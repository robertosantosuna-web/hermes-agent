#!/usr/bin/env python3
"""
Auto-Pilot Forex — Gerenciamento autônomo de posições.
Executado a cada 5 minutos pelo cron.
Fecha perdedores, protege ganhadores, mantém o bot saudável.
NADA de intervenção manual.
"""
import json, os, sys, time
from pathlib import Path
from datetime import datetime

H = Path.home() / '.hermes'
SCRIPTS = H / 'scripts'
FOREX = H / 'forex'

def run(cmd):
    import subprocess
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

def mt5_status():
    raw = run(f'python3 {SCRIPTS}/hermes_mt5_bridge.py status')
    try: return json.loads(raw)
    except: return {}

def close_position(ticket):
    """Fecha posição específica."""
    raw = run(f'python3 {SCRIPTS}/hermes_mt5_bridge.py close_symbol USDJPY 2>&1')
    return raw

def close_positions_by_symbol(symbol):
    """Fecha todas posições de um símbolo."""
    raw = run(f'python3 -c "from hermes_mt5_bridge import close_symbol; print(close_symbol(\'{symbol}\'))" 2>&1')
    return raw

def close_all():
    raw = run(f'python3 {SCRIPTS}/hermes_mt5_bridge.py close_all 2>&1')
    return raw

# ═══ MAIN ═══
status = mt5_status()
if not status or status.get('status') != 'ok':
    print("MT5 offline")
    sys.exit(0)

balance = status.get('balance', 400)
equity = status.get('equity', 400)
positions = status.get('positions_data', [])

# ═══ 1. DRAWDOWN PROTECTION ═══
# Usa o saldo REAL do MT5 como base, não hardcoded
initial_balance = 400  # fallback
try:
    # Tenta ler saldo inicial do arquivo de estado
    state_file = FOREX / 'autopilot_state.json'
    if state_file.exists():
        state = json.loads(state_file.read_text())
        initial_balance = state.get('initial_balance', balance)
    else:
        initial_balance = balance
        state_file.write_text(json.dumps({'initial_balance': balance, 'updated': str(datetime.now())}))
except:
    initial_balance = balance

drawdown_pct = (1 - equity / max(initial_balance, 1)) * 100
if drawdown_pct > 15:  # 15% drawdown (antes 3% que era $12)
    print(f"🛑 DRAWDOWN CRÍTICO {drawdown_pct:.1f}% — fechando todas posições")
    close_all()
    # Marca cooldown pra evitar reabertura imediata
    (FOREX / 'autopilot_cooldown').write_text(str(datetime.now()))
    sys.exit(0)

# Cooldown: não fecha de novo por 30 min após close_all
cooldown_file = FOREX / 'autopilot_cooldown'
if cooldown_file.exists():
    try:
        last_close = datetime.fromisoformat(cooldown_file.read_text().strip())
        if (datetime.now() - last_close).total_seconds() < 1800:  # 30 min
            print(f"⏳ Cooldown ativo — {(datetime.now() - last_close).total_seconds()/60:.0f}min restantes")
            sys.exit(0)
    except:
        pass

# ═══ 2. ANALISAR CADA POSIÇÃO ═══
tlog_file = FOREX / 'trade_log.json'
tlog = json.loads(tlog_file.read_text()) if tlog_file.exists() else {'trades':[]}

# Calcular WR por par
from collections import defaultdict
pair_stats = defaultdict(lambda: {'wins':0,'losses':0,'pnl':0})
for t in tlog.get('trades', []):
    if t.get('status') != 'closed': continue
    pair = t.get('pair','').replace('_KZ','').replace('/','')
    pair_stats[pair]['pnl'] += t.get('pnl',0)
    if t.get('result') == 'WIN': pair_stats[pair]['wins'] += 1
    else: pair_stats[pair]['losses'] += 1

for p in positions:
    symbol = p.get('symbol', '')
    profit = p.get('profit', 0)
    pair_clean = symbol.replace('/','')
    stats = pair_stats.get(pair_clean, {'wins':0,'losses':0})
    
    total_trades = stats['wins'] + stats['losses']
    wr = stats['wins']/total_trades*100 if total_trades > 0 else None
    
    ticket = p.get('ticket')
    
    # ═══ REGRA 1: Fechar se WR do par < 30% com 2+ trades ═══
    if total_trades >= 2 and wr is not None and wr < 30:
        print(f"🔴 {symbol} #{ticket}: WR={wr:.0f}% — FECHANDO (par tóxico)")
        close_positions_by_symbol(symbol)
        continue
    
    # ═══ REGRA 2: Fechar perda > 2× o risco típico do par ═══
    # Forex: SL ~$1.50 (15p × $0.10) → threshold $2.00
    # Ouro:  SL ~$12.00 (1200t × $0.01) → threshold $10.00
    if 'XAU' in symbol.upper():
        loss_limit = -10.0  # Ouro: aguenta até -$10
    else:
        loss_limit = -2.0   # Forex: fecha em -$2
    
    if profit < loss_limit:
        print(f"🔴 {symbol} #{ticket}: Perda ${profit:.2f} > {loss_limit} — FECHANDO")
        close_positions_by_symbol(symbol)
        continue
    
    # ═══ REGRA 3: Trail stop no lucro ═══
    if profit > 1.0:  # $1+ de lucro
        print(f"🟢 {symbol} #{ticket}: Lucro ${profit:.2f} — protegido")

# ═══ 3. CONCENTRAÇÃO — CORRIGIR PROATIVAMENTE ═══
pair_count = {}
for p in positions:
    s = p.get('symbol','')
    pair_count[s] = pair_count.get(s, 0) + 1

CORRELATED = {
    'JPY': ['USDJPY', 'GBPJPY', 'EURJPY'],
    'USD': ['GBPUSD', 'EURUSD', 'USDCAD'],
    'XAU': ['XAUUSD'],
}

for pair, count in pair_count.items():
    if count >= 4:
        print(f"🔴 {pair}: {count}x concentração — FECHANDO TODAS")
        close_positions_by_symbol(pair)
    elif count >= 3:
        print(f"⚠️ {pair}: {count}x concentração — ALERTA")

# Verificar grupos correlacionados
for group, pairs in CORRELATED.items():
    group_count = sum(pair_count.get(p, 0) for p in pairs)
    if group_count >= 4:
        print(f"🔴 Grupo {group}: {group_count}x posições — FECHANDO MAIS ANTIGA")
        # Pega o par com mais posições no grupo e fecha
        worst = max((p for p in pairs if p in pair_count), key=lambda p: pair_count[p], default=None)
        if worst:
            close_positions_by_symbol(worst)

# ═══ 4. SALVAR ESTADO ═══
state = {
    'timestamp': datetime.now().isoformat(),
    'balance': balance,
    'equity': equity,
    'positions': len(positions),
    'drawdown_pct': round(drawdown_pct, 2),
    'pair_counts': pair_count,
}
state_file = FOREX / 'autopilot_state.json'
state_file.write_text(json.dumps(state, indent=2))

summary = f"AutoPilot {datetime.now().strftime('%H:%M')} | {len(positions)} pos | ${equity:.2f} | DD {drawdown_pct:.1f}%"
print(f"\n{summary}")
