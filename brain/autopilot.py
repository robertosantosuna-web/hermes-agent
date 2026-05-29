#!/usr/bin/env python3
"""AutoPilot v9.0 — Gerenciamento autônomo de posições.
Sincronizado com Córtex Visual v3.0 + Conselho v4.0.
Executado a cada 3 minutos pelo cron.

Estratégia de lucro máximo:
- RR >= 3:1 → fecha 50% da posição (parcial) + ativa trailing stop no restante
- Trailing stop: SL sobe junto com o preço, mantendo distância mínima
- Parciais registradas para evitar repetir no mesmo trade
"""

import json, os, sys, time
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path.home() / '.hermes' / 'brain'))

H = Path.home() / '.hermes'
SCRIPTS = H / 'scripts'
FOREX = H / 'forex'
BRAIN = H / 'brain'
STATE_FILE = FOREX / 'autopilot_state.json'
COOLDOWN_FILE = FOREX / 'autopilot_cooldown'
PARTIALS_FILE = FOREX / 'autopilot_partials.json'
MT5_RESP = Path.home() / '.wine/drive_c/users/roberto/AppData/Roaming/MetaQuotes/Terminal/Common/Files/hermes_resp.json'
MT5_CMD = MT5_RESP.parent / 'hermes_cmd.json'

# ═══ PARÂMETROS ═══
DRAWDOWN_WARNING = 0.10
DRAWDOWN_CRITICAL = 0.15
COOLDOWN_MINUTES = 30
MAX_POSITIONS = 4
RISK_PCT_FOREX = 0.01
RISK_PCT_XAU = 0.005
RR_PARTIAL_TRIGGER = 3.0    # RR >= 3:1 → dispara parcial
PARTIAL_CLOSE_PCT = 0.50    # Fecha 50% da posição

# ═══ TRAILING STOP APRIMORADO ═══
BREAKEVEN_TRIGGER_RR = 1.0   # Move SL pro breakeven quando atinge 1R
ATR_TRAIL_MULTIPLIER = 0.5   # Multiplicador do ATR para distância do trailing (forex)
ATR_TRAIL_XAU = 1.0          # XAUUSD: 1.0 ATR (ouro precisa mais folga — Gemini)

# Filtro de spread (Gemini): pausa trailing se spread > 3x média
MAX_SPREAD_RATIO = 3.0       # Spread atual / spread médio máximo permitido
SPREAD_CHECK_ENABLED = True   # Ativar verificação de spread antes de ajustar SL
LOCK_STEPS = [                # Degraus de lock-in progressivo: (RR_atingido, %_lucro_travado)
    (1.0, 0.25),   # 1R → trava 25%
    (2.0, 0.40),   # 2R → trava 40%
    (3.0, 0.55),   # 3R → trava 55%
    (5.0, 0.70),   # 5R → trava 70%
    (8.0, 0.82),   # 8R → trava 82%
    (12.0, 0.90),  # 12R → trava 90%
]
TRAIL_ACCELERATION = 1.3     # Fator de aceleração: quanto mais longe, mais próximo o stop
TRAIL_ACCEL_CAP = 0.95       # Teto absoluto: stop NUNCA trava mais de 95% do lucro
BREAKEVEN_BUFFER_SPREAD = 1.5  # Multiplicador do spread para buffer no breakeven
BREAKEVEN_BUFFER_ATR = 0.1   # Fração do ATR como buffer mínimo no breakeven

# Aceleração por ativo (ouro = mais volátil = menos agressivo)
ACCEL_BY_ASSET = {
    'XAUUSD': 1.15,
    'EURUSD': 1.30,
    'GBPUSD': 1.30,
    'USDJPY': 1.25,
    'GBPJPY': 1.20,
    'EURJPY': 1.20,
    'USDCAD': 1.30,
    'default': 1.25,
}

# ═══ MONITOR DE CONECTIVIDADE ═══
CONNECTIVITY_CHECK_HOSTS = ["8.8.8.8", "1.1.1.1"]  # Google DNS, Cloudflare
CONNECTIVITY_TIMEOUT = 3       # Timeout por ping (segundos)
CONNECTIVITY_STABILITY_WINDOW = 5  # Número de checks para considerar "estável"
CONNECTIVITY_STATE_FILE = FOREX / 'connectivity_state.json'

# ═══ CIRCUIT BREAKERS (Gemini) ═══
MAX_DRAWDOWN_DAILY = 0.05      # 5% drawdown diário → suspensão
MAX_CONSECUTIVE_LOSSES = 5     # 5 perdas seguidas → suspensão  
MAX_BREAKEVEN_PREMATURE = 0.40 # 40% dos BE seguem após saída → recalibragem
MAX_SLIPPAGE_RATIO = 2.0       # Slippage > 2x spread → alerta
MAX_BRIDGE_FAILURES_HOUR = 3   # >3 falhas de bridge/hora → suspensão
CIRCUIT_BREAKER_FILE = FOREX / 'circuit_breakers.json'
BRIDGE_LOG_FILE = FOREX / 'bridge_errors.log'       # Log isolado de erros de bridge
GHOST_TRACKER_FILE = FOREX / 'ghost_tracker.json'   # Price ghost tracker (Gemini)
GHOST_TRACK_HOURS = 2          # Horas para rastrear preço após BE
WATCHDOG_RESTART_CMD = "pkill -f hermes_bridge && sleep 2 && wine ..."  # placeholder
KILL_SWITCH_CLOSE_ALL = True   # Fechar TODAS posições ao disparar circuit breaker

# Grupos correlacionados
CORRELATED = {
    "JPY": ["USDJPY", "GBPJPY", "EURJPY"],
    "USD": ["EURUSD", "GBPUSD", "AUDUSD"],
    "GBP": ["GBPUSD", "GBPJPY"],
    "XAU": ["XAUUSD"],
}
MAX_CORRELATED = 2  # Máximo de pares do mesmo grupo

def read_mt5():
    """Lê estado do MT5 via bridge EA."""
    if MT5_RESP.exists():
        try:
            with open(MT5_RESP) as f:
                return json.load(f)
        except:
            pass
    # Fallback: bridge antiga
    try:
        import subprocess
        r = subprocess.run(f'python3 {SCRIPTS}/hermes_mt5_bridge.py status', 
                          shell=True, capture_output=True, text=True, timeout=10)
        return json.loads(r.stdout)
    except:
        return {}

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"closed_today": 0, "last_close_all": None, "alerts": []}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, default=str)

def is_cooldown():
    if COOLDOWN_FILE.exists():
        ts = datetime.fromisoformat(COOLDOWN_FILE.read_text().strip())
        return datetime.now() < ts + timedelta(minutes=COOLDOWN_MINUTES)
    return False

def close_all_positions():
    """Fecha todas as posições via EA bridge."""
    cmd = json.dumps({"action": "close_all"})
    MT5_CMD.write_text(cmd)
    time.sleep(1)
    return read_mt5()

def close_partial_position(symbol, volume_pct):
    """Fecha parcialmente uma posição (ex: 50% do volume)."""
    cmd = json.dumps({
        "action": "close_symbol_partial",
        "symbol": symbol,
        "volume_pct": volume_pct
    })
    MT5_CMD.write_text(cmd)
    time.sleep(0.5)
    return read_mt5()

def modify_sl(symbol, new_sl):
    """Atualiza SL de posição existente (trailing stop)."""
    ticket = None
    mt5 = read_mt5()
    for pos in mt5.get('positions_data', []):
        if pos.get('symbol') == symbol:
            ticket = pos.get('ticket')
            break
    
    if not ticket:
        return None
    
    cmd = json.dumps({
        "action": "modify_position",
        "ticket": ticket,
        "sl": new_sl,
        "tp": 0  # mantém TP atual
    })
    MT5_CMD.write_text(cmd)
    time.sleep(0.5)
    return read_mt5()

def load_partials():
    """Carrega registro de parciais já executadas."""
    if PARTIALS_FILE.exists():
        return json.loads(PARTIALS_FILE.read_text())
    return {}

def save_partial(ticket, symbol, pct_closed, profit_locked):
    """Registra que uma parcial foi executada neste trade."""
    partials = load_partials()
    partials[str(ticket)] = {
        'symbol': symbol,
        'pct_closed': pct_closed,
        'profit_locked': profit_locked,
        'time': datetime.now().isoformat(),
        'trailing_activated': True
    }
    PARTIALS_FILE.write_text(json.dumps(partials, indent=2))

def check_partial_and_trail(mt5, positions):
    """Estratégia de lucro máximo: parcial no 3:1 + trailing stop.
    
    Para cada posição:
    1. Calcular RR atual = lucro_atual / risco_inicial
    2. Se RR >= 3:1 E ainda não fez parcial → fecha 50%
    3. No restante, ativa trailing stop
    4. Se já fez parcial, ajusta trailing stop no restante
    """
    partials = load_partials()
    
    for pos in positions:
        symbol = pos.get('symbol', '')
        ticket = pos.get('ticket', 0)
        pnl = pos.get('profit', 0)
        entry = pos.get('entry', 0)
        current_sl = pos.get('sl', 0)
        ptype = pos.get('type', '')
        volume = pos.get('volume', 0.01)
        
        if entry <= 0 or current_sl <= 0:
            continue
        
        # Calcular risco inicial (distância SL → entrada)
        initial_risk = abs(entry - current_sl)
        if initial_risk <= 0:
            continue
        
        # Calcular RR atual
        if pnl > 0:
            current_rr = pnl / (initial_risk * volume * _pip_value(symbol))
            current_rr = abs(current_rr) if abs(current_rr) < 100 else 0
        else:
            current_rr = 0
        
        # Preço atual (aproximado pelo lucro)
        if ptype == 'BUY':
            current_price = entry + (pnl / (volume * _pip_scale(symbol)))
        else:
            current_price = entry - (pnl / (volume * _pip_scale(symbol)))
        
        ticket_str = str(ticket)
        
        # ═══ PARCIAL 3:1 ═══
        if current_rr >= RR_PARTIAL_TRIGGER and ticket_str not in partials:
            profit_locked = pnl * PARTIAL_CLOSE_PCT
            print(f"💰 PARCIAL {symbol} {ptype}: RR={current_rr:.1f}, "
                  f"fechando {PARTIAL_CLOSE_PCT*100:.0f}% → lucro travado ${profit_locked:.2f}")
            
            result = close_partial_position(symbol, PARTIAL_CLOSE_PCT)
            save_partial(ticket, symbol, PARTIAL_CLOSE_PCT, profit_locked)
            
            try:
                import thalamus
                thalamus.broadcast_to_workspace(
                    f"AutoPilot: Parcial {symbol} {ptype} RR={current_rr:.1f}, "
                    f"lucro travado ${profit_locked:.2f}, trailing ativado",
                    priority=8, source="autopilot"
                )
            except:
                pass
            continue  # Pula trailing nesta iteração (SL será ajustado na próxima)

        # ═══ TRAILING STOP APRIMORADO v2 — com feedback dos 4 especialistas ═══
        if pnl <= 0:
            continue  # Sem lucro, sem trailing
        
        profit_distance = pnl / (volume * _pip_scale(symbol))
        
        # Obter ATR do par (com cache implícito via função)
        atr = get_atr(symbol)
        
        # Aceleração por ativo
        accel = ACCEL_BY_ASSET.get(symbol.upper(), ACCEL_BY_ASSET['default'])
        
        # 1. BREAKEVEN COM BUFFER (ChatGPT + DeepSeek)
        # SL nunca vai exatamente no entry — inclui spread + slippage
        if current_rr >= BREAKEVEN_TRIGGER_RR:
            spread_buffer = 0.00015  # Spread típico EURUSD (1.5 pip)
            if 'JPY' in symbol.upper():
                spread_buffer = 0.015  # JPY spread típico (1.5 pip)
            elif 'XAU' in symbol.upper():
                spread_buffer = 0.30  # Ouro spread típico
            
            atr_buffer = max(spread_buffer * BREAKEVEN_BUFFER_SPREAD, atr * BREAKEVEN_BUFFER_ATR)
            
            if ptype == 'BUY':
                breakeven_sl = entry + atr_buffer
                if current_sl < breakeven_sl:
                    print(f"🔒 BREAKEVEN {symbol}: SL {current_sl:.5f} → {breakeven_sl:.5f} "
                          f"(entry+{atr_buffer:.5f} buffer)")
                    modify_sl(symbol, breakeven_sl)
            else:
                breakeven_sl = entry - atr_buffer
                if current_sl > breakeven_sl:
                    print(f"🔒 BREAKEVEN {symbol}: SL {current_sl:.5f} → {breakeven_sl:.5f} "
                          f"(entry-{atr_buffer:.5f} buffer)")
                    modify_sl(symbol, breakeven_sl)
        
        # 2. LOCK-IN PROGRESSIVO com cap (todos os especialistas)
        protect_pct = 0.0
        for rr_threshold, pct in LOCK_STEPS:
            if current_rr >= rr_threshold:
                protect_pct = pct
        
        # 3. ACELERAÇÃO com cap absoluto
        if current_rr > 1.0 and protect_pct > 0:
            protect_pct = min(TRAIL_ACCEL_CAP, protect_pct * accel)
        
        if protect_pct <= 0:
            continue
        
        # 4. Calcular SL com ATR como piso (ChatGPT: corrigir direção)
        # Multiplicador ATR por classe de ativo (Gemini: XAU precisa mais folga)
        atr_mult = ATR_TRAIL_XAU if 'XAU' in symbol.upper() else ATR_TRAIL_MULTIPLIER
        
        if ptype == 'BUY':
            new_sl = entry + (profit_distance * protect_pct)
            
            # Piso ATR: stop NÃO pode ficar mais próximo que N*ATR do preço atual
            if atr > 0:
                atr_floor = current_price - (atr * atr_mult)
                new_sl = min(new_sl, atr_floor)  # Não deixa colar demais
            
            # Garantias: nunca abaixo do entry (após breakeven) + nunca desce
            if current_rr >= BREAKEVEN_TRIGGER_RR:
                new_sl = max(new_sl, entry + (atr * BREAKEVEN_BUFFER_ATR if atr > 0 else 0.0001))
            new_sl = max(new_sl, current_sl)
            
            if new_sl > current_sl:
                # Filtro de spread (Gemini): não ajusta SL se spread alargou
                if SPREAD_CHECK_ENABLED and is_spread_wide(symbol):
                    print(f"⚠️  TRAIL {symbol} SKIP: spread alargado, SL mantido em {current_sl:.5f}")
                    continue
                    
                locked_pct = (new_sl - entry) / (current_price - entry) * 100 if current_price > entry else 0
                print(f"📈 TRAIL {symbol}: SL {current_sl:.5f} → {new_sl:.5f} "
                      f"(PnL=${pnl:.2f}, RR={current_rr:.1f}, trava {locked_pct:.0f}%, accel={accel}x)")
                modify_sl(symbol, new_sl)
        
        else:  # SELL
            new_sl = entry - (profit_distance * protect_pct)
            
            if atr > 0:
                atr_floor = current_price + (atr * atr_mult)
                new_sl = max(new_sl, atr_floor)
            
            if current_rr >= BREAKEVEN_TRIGGER_RR:
                new_sl = min(new_sl, entry - (atr * BREAKEVEN_BUFFER_ATR if atr > 0 else 0.0001))
            new_sl = min(new_sl, current_sl)
            
            if new_sl < current_sl:
                # Filtro de spread (Gemini): não ajusta SL se spread alargou
                if SPREAD_CHECK_ENABLED and is_spread_wide(symbol):
                    print(f"⚠️  TRAIL {symbol} SKIP: spread alargado, SL mantido em {current_sl:.5f}")
                    continue
                    
                locked_pct = (entry - new_sl) / (entry - current_price) * 100 if current_price < entry else 0
                print(f"📉 TRAIL {symbol}: SL {current_sl:.5f} → {new_sl:.5f} "
                      f"(PnL=${pnl:.2f}, RR={current_rr:.1f}, trava {locked_pct:.0f}%, accel={accel}x)")
                modify_sl(symbol, new_sl)


def _pip_value(symbol):
    """Valor de 1 pip em USD para 0.01 lote."""
    if 'XAU' in symbol.upper():
        return 0.01
    if 'JPY' in symbol.upper():
        return 0.09
    return 0.10

def _pip_scale(symbol):
    """Escala para converter preço → USD."""
    if 'XAU' in symbol.upper():
        return 100  # XAU: 1 ponto = $1 para 0.01 lote
    if 'JPY' in symbol.upper():
        return 1000  # JPY: 0.01 = 1 pip ≈ $0.09
    return 10000  # Forex padrão: 0.0001 = 1 pip ≈ $0.10

def is_spread_wide(symbol):
    """Verifica se spread atual está alargado (>3x média). Retorna True se deve pausar trailing."""
    import subprocess, json
    try:
        # Obtém spread via MT5 bridge
        if MT5_RESP.exists():
            mt5 = json.loads(MT5_RESP.read_text())
            positions = mt5.get('positions', [])
            for p in positions:
                if p.get('symbol', '').upper() == symbol.upper():
                    spread = p.get('spread', 0)  # spread em pontos
                    # Spread médio esperado por ativo
                    avg_spreads = {
                        'EURUSD': 15, 'GBPUSD': 20, 'USDJPY': 15,
                        'GBPJPY': 25, 'EURJPY': 20, 'XAUUSD': 30,
                        'USDCAD': 20, 'default': 20
                    }
                    avg = avg_spreads.get(symbol.upper(), avg_spreads['default'])
                    if spread > avg * MAX_SPREAD_RATIO:
                        print(f"  ⚠ Spread {symbol}: {spread} pts (média: {avg}, ratio: {spread/avg:.1f}x)")
                        return True
                    return False
        return False
    except:
        return False  # Erro → não bloqueia


# ═══════════════════════════════════════════════════════════════════════════
# CIRCUIT BREAKERS — Suspensão automática de trading
# ═══════════════════════════════════════════════════════════════════════════

def load_circuit_breakers():
    """Carrega estado dos circuit breakers."""
    if CIRCUIT_BREAKER_FILE.exists():
        return json.loads(CIRCUIT_BREAKER_FILE.read_text())
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    return {
        'daily_drawdown': 0.0,
        'daily_start_balance': 0.0,
        'date': today,
        'consecutive_losses': 0,
        'breakeven_trades': [],
        'slippage_events': [],
        'bridge_failures': [],
        'suspended': False,
        'suspended_reason': None,
        'suspended_since': None,
        'last_loss_ticket': None
    }

def save_circuit_breakers(state):
    CIRCUIT_BREAKER_FILE.write_text(json.dumps(state, indent=2, default=str))

def is_circuit_breaker_active():
    """Verifica se algum circuit breaker suspendeu trading."""
    state = load_circuit_breakers()
    return state.get('suspended', False)

def check_circuit_breakers(mt5_data):
    """Executa todas as verificações. Retorna (ok, reason, kill_switch)."""
    state = load_circuit_breakers()
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    if state.get('date') != today:
        state = {
            'daily_drawdown': 0.0,
            'daily_start_balance': float(mt5_data.get('balance', 0)),
            'date': today,
            'consecutive_losses': 0,
            'breakeven_trades': [],
            'slippage_events': [],
            'bridge_failures': [],
            'suspended': False,
            'suspended_reason': None,
            'suspended_since': None,
            'last_loss_ticket': None,
            'kill_switch_triggered': False
        }
        save_circuit_breakers(state)
        return True, None, False
    
    balance = float(mt5_data.get('balance', 0))
    equity = float(mt5_data.get('equity', balance))
    start_balance = float(state.get('daily_start_balance', balance))
    
    if start_balance <= 0:
        state['daily_start_balance'] = balance
        save_circuit_breakers(state)
        return True, None, False
    
    dd = (start_balance - equity) / start_balance
    state['daily_drawdown'] = max(state.get('daily_drawdown', 0), dd)
    
    # 1. Drawdown → KILL SWITCH (fecha tudo)
    if dd >= MAX_DRAWDOWN_DAILY:
        reason = f"Drawdown diário {dd*100:.1f}% ≥ {MAX_DRAWDOWN_DAILY*100:.0f}%"
        state['suspended'] = True
        state['suspended_reason'] = reason
        state['suspended_since'] = datetime.now(timezone.utc).isoformat()
        state['kill_switch_triggered'] = True
        save_circuit_breakers(state)
        return False, reason, True  # kill_switch!
    
    # 2. Perdas consecutivas → KILL SWITCH
    if state.get('consecutive_losses', 0) >= MAX_CONSECUTIVE_LOSSES:
        reason = f"{state['consecutive_losses']} perdas consecutivas (limite: {MAX_CONSECUTIVE_LOSSES})"
        state['suspended'] = True
        state['suspended_reason'] = reason
        state['suspended_since'] = datetime.now(timezone.utc).isoformat()
        state['kill_switch_triggered'] = True
        save_circuit_breakers(state)
        return False, reason, True
    
    # 3. Falhas de bridge → KILL SWITCH (tentou watchdog, falhou)
    one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    recent_failures = [f for f in state.get('bridge_failures', [])
                       if f.get('timestamp', '') > one_hour_ago]
    if len(recent_failures) >= MAX_BRIDGE_FAILURES_HOUR:
        reason = f"{len(recent_failures)} falhas de bridge em 1h (limite: {MAX_BRIDGE_FAILURES_HOUR})"
        state['suspended'] = True
        state['suspended_reason'] = reason
        state['suspended_since'] = datetime.now(timezone.utc).isoformat()
        state['kill_switch_triggered'] = True
        save_circuit_breakers(state)
        return False, reason, True
    
    # 4. Breakeven prematuro → SUSPENDE mesmo com lucro (Gemini: "lucro com proteção descalibrada é falha")
    be_trades = state.get('breakeven_trades', [])
    if len(be_trades) >= 5:
        premature = [t for t in be_trades if t.get('max_rr_reached', 0) >= 2.0]
        if len(premature) / len(be_trades) > MAX_BREAKEVEN_PREMATURE:
            reason = (f"Breakeven prematuro: {len(premature)}/{len(be_trades)} "
                      f"({len(premature)/len(be_trades)*100:.0f}%) trades saíram antes de 2R+")
            state['suspended'] = True
            state['suspended_reason'] = reason
            state['suspended_since'] = datetime.now(timezone.utc).isoformat()
            # NÃO fecha posições existentes (kill_switch=False), só bloqueia novas
            save_circuit_breakers(state)
            return False, reason, False
    
    save_circuit_breakers(state)
    return True, None, False


def record_trade_result(ticket, symbol, pnl, max_rr_reached, exit_reason, slippage=None):
    """Registra resultado de trade fechado para circuit breakers."""
    state = load_circuit_breakers()
    
    if pnl < 0:
        if state.get('last_loss_ticket') != ticket:
            state['consecutive_losses'] = state.get('consecutive_losses', 0) + 1
            state['last_loss_ticket'] = ticket
    else:
        state['consecutive_losses'] = 0
        state['last_loss_ticket'] = None
    
    if exit_reason in ('breakeven', 'trailing_stop') and pnl >= 0:
        state.setdefault('breakeven_trades', []).append({
            'symbol': symbol,
            'pnl': pnl,
            'max_rr_reached': max_rr_reached,
            'exit_reason': exit_reason,
            'date': datetime.now(timezone.utc).isoformat()
        })
        if len(state['breakeven_trades']) > 50:
            state['breakeven_trades'] = state['breakeven_trades'][-50:]
    
    if slippage and slippage.get('ratio', 0) > MAX_SLIPPAGE_RATIO:
        state.setdefault('slippage_events', []).append({
            'symbol': symbol,
            **slippage,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        try:
            import thalamus
            thalamus.broadcast_to_workspace(
                f"⚠️ Slippage alto: {symbol} {slippage.get('ratio',0):.1f}x spread",
                priority=7, source="autopilot"
            )
        except:
            pass
    
    save_circuit_breakers(state)


def record_bridge_failure():
    """Registra falha de comunicação com bridge MT5 + log isolado."""
    state = load_circuit_breakers()
    ts = datetime.now(timezone.utc)
    entry = {'timestamp': ts.isoformat()}
    state.setdefault('bridge_failures', []).append(entry)
    
    # Log isolado de bridge (Gemini: auditoria assíncrona)
    with open(BRIDGE_LOG_FILE, 'a') as f:
        f.write(f"{ts.isoformat()} | BRIDGE_FAILURE | count_1h: {len([x for x in state['bridge_failures'] if x.get('timestamp','') > (ts - timedelta(hours=1)).isoformat()])}\n")
    
    cutoff = (ts - timedelta(hours=24)).isoformat()
    state['bridge_failures'] = [f for f in state['bridge_failures'] 
                                 if f.get('timestamp', '') > cutoff]
    
    # Watchdog: na 1ª falha, tenta reiniciar bridge silenciosamente
    recent = [f for f in state['bridge_failures'] 
              if f.get('timestamp', '') > (ts - timedelta(minutes=5)).isoformat()]
    if len(recent) == 1:
        print("🔄 Watchdog: 1ª falha de bridge — verificando...")
        # Nota: reinício real depende do ambiente Wine; logamos para auditoria
    
    save_circuit_breakers(state)


# ═══════════════════════════════════════════════════════════════════════════
# GHOST TRACKER — Monitora preço após BE para validar trailing
# ═══════════════════════════════════════════════════════════════════════════

def start_ghost_track(symbol, entry_price, exit_price, target_price, direction, max_rr, ticket):
    """Inicia rastreamento fantasma após fechamento no BE."""
    ghost = load_ghost_tracker()
    ghost.setdefault('active', []).append({
        'symbol': symbol,
        'entry': entry_price,
        'exit': exit_price,
        'target': target_price,
        'direction': direction,
        'max_rr_before_exit': max_rr,
        'ticket': ticket,
        'started': datetime.now(timezone.utc).isoformat(),
        'expires': (datetime.now(timezone.utc) + timedelta(hours=GHOST_TRACK_HOURS)).isoformat()
    })
    save_ghost_tracker(ghost)

def load_ghost_tracker():
    if GHOST_TRACKER_FILE.exists():
        return json.loads(GHOST_TRACKER_FILE.read_text())
    return {'active': [], 'completed': []}

def save_ghost_tracker(data):
    GHOST_TRACKER_FILE.write_text(json.dumps(data, indent=2, default=str))

def check_ghost_tracker():
    """Verifica se trades fantasmas atingiram o alvo após saída."""
    ghost = load_ghost_tracker()
    now = datetime.now(timezone.utc)
    completed_any = False
    
    for g in ghost.get('active', []):
        if g.get('expires', '') < now.isoformat():
            # Expirado: não atingiu alvo
            ghost.setdefault('completed', []).append({
                **g, 'hit_target': False, 'result': 'expired',
                'checked_at': now.isoformat()
            })
            completed_any = True
            continue
        
        # Verificar preço atual via MT5
        try:
            mt5 = json.loads(MT5_RESP.read_text()) if MT5_RESP.exists() else {}
            positions = mt5.get('positions_data', [])
            for p in positions:
                if p.get('symbol', '') == g['symbol']:
                    # Ainda tem posição aberta no mesmo símbolo — não é o ghost
                    continue
            
            # Obter preço atual do par (aproximado via posições)
            # Fallback: usar preço da entry como referência
            current = g.get('entry', 0)
            for p in positions:
                if p.get('symbol', '') == g['symbol']:
                    current = p.get('current_price', p.get('entry', 0))
                    break
            
            # Verificar se atingiu target
            hit = False
            if g['direction'] == 'BUY' and current >= g['target']:
                hit = True
            elif g['direction'] == 'SELL' and current <= g['target']:
                hit = True
            
            if hit:
                ghost.setdefault('completed', []).append({
                    **g, 'hit_target': True, 'result': 'would_have_won',
                    'checked_at': now.isoformat()
                })
                completed_any = True
        except:
            pass
    
    # Limpar expirados/completados da lista ativa
    if completed_any:
        ghost['active'] = [g for g in ghost.get('active', []) 
                          if g.get('expires', '') >= now.isoformat()
                          and not any(c.get('ticket') == g.get('ticket') 
                                     for c in ghost.get('completed', []))]
        save_ghost_tracker(ghost)
    
    return ghost


def get_atr(symbol, tf='M15', periods=14):
    """Obtém ATR do par usando yfinance como fallback rápido."""
    import subprocess, json
    try:
        # Mapear símbolos MT5 → Yahoo Finance
        yf_map = {
            'EURUSD': 'EURUSD=X', 'GBPUSD': 'GBPUSD=X', 'USDJPY': 'USDJPY=X',
            'GBPJPY': 'GBPJPY=X', 'EURJPY': 'EURJPY=X', 'XAUUSD': 'GC=F',
            'USDCAD': 'USDCAD=X', 'AUDUSD': 'AUDUSD=X',
        }
        yf_sym = yf_map.get(symbol.upper(), f'{symbol}=X')
        
        r = subprocess.run(
            ['python3', '-c', f'''
import yfinance as yf
import numpy as np
import pandas as pd
import json
sym = "{yf_sym}"
try:
    df = yf.download(sym, period="2d", interval="15m", progress=False, auto_adjust=False)
    if df.empty:
        print(json.dumps({{"atr": 0, "error": "no data"}}))
    else:
        # Handle MultiIndex columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            high = df[("High", sym)].values
            low = df[("Low", sym)].values
            close = df[("Close", sym)].values
        else:
            high = df["High"].values
            low = df["Low"].values
            close = df["Close"].values
        n = len(close)
        if n < 2:
            print(json.dumps({{"atr": 0, "error": "not enough bars"}}))
        else:
            tr_vals = []
            for i in range(1, min({periods}+1, n)):
                tr = max(high[-i] - low[-i], abs(high[-i] - close[-i-1]), abs(low[-i] - close[-i-1]))
                tr_vals.append(tr)
            atr = sum(tr_vals) / len(tr_vals)
            print(json.dumps({{"atr": float(atr)}}))
except Exception as e:
    print(json.dumps({{"atr": 0, "error": str(e)}}))
'''], capture_output=True, text=True, timeout=8, env={**__import__('os').environ, 'PYTHONPATH': ''})
        
        if r.returncode == 0:
            data = json.loads(r.stdout.strip())
            return data.get('atr', 0)
    except:
        pass
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# MONITOR DE CONECTIVIDADE — Pausa ordens se rede instável
# ═══════════════════════════════════════════════════════════════════════════

def check_connectivity():
    """Verifica conectividade de rede. Retorna (ok, detalhes)."""
    import subprocess
    
    results = []
    for host in CONNECTIVITY_CHECK_HOSTS:
        try:
            r = subprocess.run(
                ['ping', '-c', '1', '-W', str(CONNECTIVITY_TIMEOUT), host],
                capture_output=True, text=True, timeout=5
            )
            ok = r.returncode == 0
            latency = None
            if ok:
                for line in r.stdout.split('\n'):
                    if 'time=' in line:
                        latency = float(line.split('time=')[1].split(' ')[0])
                        break
            results.append({'host': host, 'ok': ok, 'latency': latency})
        except:
            results.append({'host': host, 'ok': False, 'latency': None})
    
    # Verificar MT5 bridge também
    mt5_ok = MT5_RESP.exists() and (time.time() - MT5_RESP.stat().st_mtime) < 30
    
    ping_ok = sum(1 for r in results if r['ok']) >= 1  # Pelo menos 1 ping ok
    overall = ping_ok and mt5_ok
    
    return overall, {
        'ping_results': results,
        'mt5_bridge': mt5_ok,
        'timestamp': time.time()
    }

def load_connectivity_state():
    """Carrega histórico de conectividade."""
    if CONNECTIVITY_STATE_FILE.exists():
        return json.loads(CONNECTIVITY_STATE_FILE.read_text())
    return {
        'status': 'unknown',
        'consecutive_failures': 0,
        'consecutive_successes': 0,
        'paused_since': None,
        'history': []
    }

def save_connectivity_state(state):
    """Salva estado de conectividade."""
    CONNECTIVITY_STATE_FILE.write_text(json.dumps(state, indent=2, default=str))

def is_trading_paused():
    """Verifica se abertura de ordens está pausada por instabilidade."""
    state = load_connectivity_state()
    return state.get('status') == 'paused'

def update_connectivity():
    """Atualiza estado de conectividade e decide se pausa/retoma."""
    state = load_connectivity_state()
    ok, details = check_connectivity()
    
    state['history'].append({
        'ok': ok,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'mt5_bridge': details['mt5_bridge'],
        'pings': sum(1 for r in details['ping_results'] if r['ok'])
    })
    
    # Manter só últimos 50 checks
    if len(state['history']) > 50:
        state['history'] = state['history'][-50:]
    
    if ok:
        state['consecutive_successes'] += 1
        state['consecutive_failures'] = 0
        
        # unknown → normal na primeira verificação OK
        if state['status'] == 'unknown':
            state['status'] = 'normal'
        
        # Retomar após janela de estabilidade
        if state['status'] == 'paused' and state['consecutive_successes'] >= CONNECTIVITY_STABILITY_WINDOW:
            state['status'] = 'normal'
            state['paused_since'] = None
            print(f"🟢 REDE ESTÁVEL — retomando abertura de ordens ({state['consecutive_successes']} checks OK)")
            
            try:
                import thalamus
                thalamus.broadcast_to_workspace(
                    "🟢 Rede estabilizada — AutoPilot retomando operação normal",
                    priority=9, source="autopilot"
                )
            except:
                pass
    else:
        state['consecutive_failures'] += 1
        state['consecutive_successes'] = 0
        
        # Pausar após 2 falhas consecutivas
        if state['status'] != 'paused' and state['consecutive_failures'] >= 2:
            state['status'] = 'paused'
            state['paused_since'] = datetime.now(timezone.utc).isoformat()
            
            ping_status = f"{sum(1 for r in details['ping_results'] if r['ok'])}/{len(details['ping_results'])} pings OK"
            print(f"🔴 REDE INSTÁVEL — pausando novas ordens! ({ping_status}, MT5: {'OK' if details['mt5_bridge'] else 'OFFLINE'})")
            
            try:
                import thalamus
                thalamus.raise_alert("critical", "connectivity_lost",
                    f"Rede instável: {ping_status}. Novas ordens PAUSADAS.", "autopilot")
                thalamus.broadcast_to_workspace(
                    "🔴 ALERTA: Rede instável detectada! AutoPilot pausou novas ordens até estabilizar.",
                    priority=10, source="autopilot"
                )
            except:
                pass
    
    save_connectivity_state(state)
    return ok, state


def close_all_positions_old():
    """Fecha todas as posições via EA bridge."""
    cmd = json.dumps({"action": "close_all"})
    cmd_path = MT5_RESP.parent / "hermes_cmd.json"
    cmd_path.write_text(cmd)
    time.sleep(1)
    result = read_mt5()
    return result

def main():
    # Cooldown check
    if is_cooldown():
        print("AutoPilot: em cooldown")
        return

    # ═══ 0. VERIFICAÇÃO DE CONECTIVIDADE ═══
    net_ok, net_state = update_connectivity()
    trading_paused = not net_ok
    
    if trading_paused:
        print(f"🔴 AutoPilot: Rede instável — novas ordens BLOQUEADAS "
              f"(falhas: {net_state['consecutive_failures']})")
        # Ainda monitora posições existentes (fechar/manejar)
        # mas NÃO permite novas entradas
    
    # Ler MT5
    mt5 = read_mt5()
    if not mt5 or mt5.get('status') != 'ok':
        print("AutoPilot: MT5 offline")
        return

    balance = mt5.get('balance', 0)
    equity = mt5.get('equity', 0)
    positions = mt5.get('positions_data', [])
    
    if balance <= 0:
        return
    
    state = load_state()
    drawdown = (balance - equity) / balance if balance > 0 else 0
    
    # ═══ 1. DRAWDOWN PROTECTION ═══
    if drawdown >= DRAWDOWN_CRITICAL:
        print(f"🛑 DRAWDOWN CRÍTICO {drawdown:.1%} — fechando tudo")
        close_all_positions()
        COOLDOWN_FILE.write_text(datetime.now().isoformat())
        state['last_close_all'] = datetime.now().isoformat()
        state['closed_today'] += 1
        save_state(state)
        
        # Notificar Tálamo
        try:
            import thalamus
            thalamus.raise_alert("critical", "autopilot_close_all", 
                                f"Drawdown {drawdown:.1%} — todas posições fechadas", "autopilot")
        except:
            pass
        return
    
    if drawdown >= DRAWDOWN_WARNING:
        print(f"⚠️ Drawdown warning: {drawdown:.1%}")
        try:
            import thalamus
            thalamus.raise_alert("warning", "autopilot_drawdown", 
                                f"Drawdown {drawdown:.1%}", "autopilot")
        except:
            pass

    # ═══ 2. CIRCUIT BREAKERS ═══
    cb_ok, cb_reason, cb_kill = check_circuit_breakers(mt5)
    if not cb_ok:
        print(f"🛑 CIRCUIT BREAKER: {cb_reason}")
        
        if cb_kill and KILL_SWITCH_CLOSE_ALL:
            print(f"💀 KILL SWITCH: fechando TODAS as posições!")
            close_all_positions()
            COOLDOWN_FILE.write_text(datetime.now().isoformat())
            try:
                import thalamus
                thalamus.raise_alert("critical", "kill_switch",
                                    f"KILL SWITCH: {cb_reason} — todas posições fechadas", "autopilot")
            except:
                pass
        
        try:
            import thalamus
            thalamus.raise_alert("critical", "circuit_breaker",
                                f"Trading suspenso: {cb_reason}", "autopilot")
        except:
            pass
    circuit_block = is_circuit_breaker_active()

    # ═══ 3. PARCIAL + TRAILING STOP (estratégia de lucro máximo) ═══
    if positions:
        check_partial_and_trail(mt5, positions)
    
    # ═══ 3.5 GHOST TRACKER ═══
    check_ghost_tracker()

    # ═══ 3. PROTEÇÃO POR POSIÇÃO ═══
    for pos in positions:
        symbol = pos.get('symbol', '')
        profit = pos.get('profit', 0)
        entry = pos.get('entry', 0)
        sl = pos.get('sl', 0)
        tp = pos.get('tp', 0)
        ticket = pos.get('ticket', 0)
        ptype = pos.get('type', '')
        
        # Threshold de perda por tipo de ativo
        if 'XAU' in symbol:
            max_loss = -10.00  # XAU: ~$10 max loss por posição
        else:
            max_loss = -2.00   # Forex: ~$2 max loss
        
        if profit < max_loss:
            print(f"🔻 {symbol} {ptype} P&L={profit:.2f} < {max_loss} — fechando")
            # Fechar posição individual via bridge
            try:
                cmd = json.dumps({"action": "close_symbol", "symbol": symbol})
                (MT5_RESP.parent / "hermes_cmd.json").write_text(cmd)
                time.sleep(0.5)
            except:
                pass

    # ═══ 4. CONCENTRAÇÃO ═══
    pos_symbols = [p.get('symbol', '') for p in positions]
    for group, pairs in CORRELATED.items():
        count = sum(1 for p in pos_symbols if p in pairs)
        if count > MAX_CORRELATED:
            print(f"⚠️ Concentração: {count} pares no grupo {group} (max {MAX_CORRELATED})")
            try:
                import thalamus
                thalamus.raise_alert("warning", "autopilot_concentration",
                                    f"{count} posições no grupo {group}", "autopilot")
            except:
                pass

    # ═══ 4. MAX POSITIONS ═══
    if len(positions) >= MAX_POSITIONS or circuit_block or trading_paused:
        block_reason = []
        if circuit_block:
            block_reason.append("circuit breaker")
        if trading_paused:
            block_reason.append("rede instável")
        if len(positions) >= MAX_POSITIONS:
            block_reason.append(f"{len(positions)}/{MAX_POSITIONS} posições")
        
        print(f"⛔ NOVAS ORDENS BLOQUEADAS: {', '.join(block_reason)}")
        try:
            import thalamus
            thalamus.broadcast_to_workspace(
                f"AutoPilot bloqueou novas ordens: {', '.join(block_reason)}",
                priority=6, source="autopilot")
        except:
            pass

    # ═══ 5. SALVAR ESTADO ═══
    state['last_run'] = datetime.now().isoformat()
    state['balance'] = balance
    state['equity'] = equity
    state['drawdown'] = round(drawdown, 4)
    state['positions'] = len(positions)
    save_state(state)

    # Resumo
    pos_str = ", ".join(f"{p.get('symbol','?')} {p.get('type','?')} ${p.get('profit',0):+.2f}" 
                        for p in positions) if positions else "nenhuma"
    cb_str = " ⛔CB" if circuit_block else ""
    net_str = " 🔴NET" if trading_paused else ""
    print(f"AutoPilot {datetime.now().strftime('%H:%M')} | "
          f"${equity:.2f} | DD {drawdown:.1%} | {len(positions)} pos | {pos_str[:80]}{cb_str}{net_str}")

if __name__ == "__main__":
    main()
