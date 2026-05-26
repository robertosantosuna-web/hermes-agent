#!/usr/bin/env python3
"""
FOREX PAPER TRADING BOT — Local, zero tokens
Estratégia: CHoCH+FVG @ M15, RR 3:1
Pares: GBP/USD, AUD/USD, EUR/USD, NZD/USD
Horários: Ter-Qui, golden hours (07, 10, 14, 16 BRT)

Modo: SIMULAÇÃO (paper trading) — NÃO abre ordens reais.
Log diário em ~/.hermes/forex/paper_logs/

Uso:
  python3 forex_bot.py          # executa 1 tick (p/ cron)
  python3 forex_bot.py --force  # força mesmo fora de golden hour
"""
import json
import urllib.request
import sys
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# ═══════════════════════════════════════
# CONFIGURAÇÃO
# ═══════════════════════════════════════
SCRIPTS_DIR = Path(__file__).parent
PAIRS = {
    'GBP/USD': 'GBPUSD',
    'AUD/USD': 'AUDUSD',
    'EUR/USD': 'EURUSD',
    'NZD/USD': 'NZDUSD',
}

RR = 3.0
FVG_MIN_PIPS = 1.0
ATR_MIN_PIPS = 1.0
GOLDEN_HOURS = {7, 10, 14, 16}
FOREX_DIR = Path.home() / '.hermes' / 'forex'
LOG_DIR = FOREX_DIR / 'paper_logs'
STATE_FILE = FOREX_DIR / 'paper_state.json'
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════
# UTILITÁRIOS
# ═══════════════════════════════════════
def pip_val(pair):
    return 0.01 if 'JPY' in pair else 0.0001

def log(msg, level='INFO'):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] [{level}] {msg}")

def fetch_m15(symbol):
    """Busca candles M15 via TradingView CDP (brain browser).
    NOTA: Para paper trading, usamos o preço atual + dados do cérebro.
    Retorna pelo menos o último candle com o preço atual."""
    try:
        # Get current quote from TradingView
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / 'forex_quote.py'), symbol],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode == 0 and result.stdout.strip():
            quote = json.loads(result.stdout)
            if 'bid' in quote:
                # Create synthetic recent candle from current price
                now = datetime.now()
                price = quote['bid']
                return [{
                    'time': now,
                    'o': price, 'h': price, 'l': price, 'c': price
                }]
        log(f"TradingView sem dados para {symbol}", 'WARN')
    except Exception as e:
        log(f"Erro TradingView {symbol}: {e}", 'ERROR')
    return []

def atr(candles, period=14):
    if len(candles) < 2: return 0
    trs = []
    for i in range(1, len(candles)):
        h, l, pc = candles[i]['h'], candles[i]['l'], candles[i-1]['c']
        trs.append(max(h-l, abs(h-pc), abs(l-pc)))
    n = min(period, len(trs))
    return sum(trs[-n:])/n if n > 0 else 0

def detect_swings(candles):
    highs, lows = [], []
    for i in range(3, len(candles)-3):
        h, l = candles[i]['h'], candles[i]['l']
        left_h = max(c['h'] for c in candles[i-3:i])
        right_h = max(c['h'] for c in candles[i+1:i+4])
        left_l = min(c['l'] for c in candles[i-3:i])
        right_l = min(c['l'] for c in candles[i+1:i+4])
        if h > left_h and h > right_h:
            highs.append({'idx': i, 'price': h, 'time': candles[i]['time']})
        if l < left_l and l < right_l:
            lows.append({'idx': i, 'price': l, 'time': candles[i]['time']})
    return highs, lows

def find_fvgs(candles):
    fvgs = []
    for i in range(1, len(candles)-1):
        prev, curr = candles[i-1], candles[i]
        if curr['l'] > prev['h']:
            fvgs.append({'type': 'BULLISH', 'top': curr['l'], 'bottom': prev['h'], 'time': curr['time']})
        elif curr['h'] < prev['l']:
            fvgs.append({'type': 'BEARISH', 'top': prev['l'], 'bottom': curr['h'], 'time': curr['time']})
    return fvgs

def is_crt_candle(candles, idx, lookback=20, percentile=80):
    """CRT: candle com range > percentile% dos últimos lookback candles."""
    if idx < lookback:
        return False
    rng = abs(candles[idx]['h'] - candles[idx]['l'])
    recent = [abs(candles[i]['h'] - candles[i]['l']) for i in range(idx-lookback, idx+1)]
    return rng >= sorted(recent)[int(len(recent) * percentile / 100)]

# ═══════════════════════════════════════
# STATE MANAGEMENT
# ═══════════════════════════════════════
def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {'open_positions': [], 'closed_trades': [], 'daily_stats': {}}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))

# ═══════════════════════════════════════
# DETECÇÃO DE SINAL
# ═══════════════════════════════════════
def detect_signal(pair_name, symbol):
    """Detecta CHoCH+FVG signal. Retorna dict ou None."""
    pv = pip_val(pair_name)
    candles = fetch_m15(symbol)
    if not candles or len(candles) < 20:
        return None
    
    atr_val = atr(candles, 14)
    atr_pips = atr_val / pv
    if atr_pips < ATR_MIN_PIPS:
        return None
    
    swings_h, swings_l = detect_swings(candles)
    if len(swings_h) < 2 or len(swings_l) < 2:
        return None
    
    last = candles[-1]
    direction = None
    
    # CHoCH
    if last['c'] > swings_h[-2]['price']:
        direction = 'LONG'
    elif last['c'] < swings_l[-2]['price']:
        direction = 'SHORT'
    
    if not direction:
        return None
    
    # FVG
    fvgs = find_fvgs(candles[-8:])
    valid_fvg = None
    if direction == 'SHORT':
        for f in reversed(fvgs):
            if f['type'] == 'BEARISH':
                valid_fvg = f; break
    else:
        for f in reversed(fvgs):
            if f['type'] == 'BULLISH':
                valid_fvg = f; break
    
    if not valid_fvg:
        return None
    
    # ── CRT Filter (obrigatório: backtest 87.5% WR vs 61.1% sem) ──
    crt = is_crt_candle(candles, len(candles)-1)
    if not crt:
        return None  # Sem CRT = sem trade
    
    # Entry + SL
    if direction == 'SHORT':
        entry = valid_fvg['bottom']
        fvg_sl = valid_fvg['top']
    else:
        entry = valid_fvg['top']
        fvg_sl = valid_fvg['bottom']
    
    fvg_width = abs(entry - fvg_sl) / pv
    if fvg_width < FVG_MIN_PIPS:
        return None
    
    sl_pips = fvg_width
    tp_pips = sl_pips * RR
    
    if direction == 'SHORT':
        sl_price = entry + sl_pips * pv
        tp_price = entry - tp_pips * pv
    else:
        sl_price = entry - sl_pips * pv
        tp_price = entry + tp_pips * pv
    
    # Score (com CRT boost)
    golden = last['time'].hour in GOLDEN_HOURS
    crt_boost = 1.0
    if is_crt_candle(candles, len(candles)-1):
        crt_boost = 1.5  # CRT confirmado → +50% score
    score = (fvg_width / max(atr_pips, 0.01)) * (1.3 if golden else 0.8) * crt_boost
    
    return {
        'pair': pair_name,
        'direction': direction,
        'entry': round(entry, 5),
        'sl': round(sl_price, 5),
        'tp': round(tp_price, 5),
        'sl_pips': round(sl_pips, 1),
        'tp_pips': round(tp_pips, 1),
        'atr_pips': round(atr_pips, 1),
        'fvg_pips': round(fvg_width, 1),
        'score': round(score, 2),
        'golden': golden,
        'crt': is_crt_candle(candles, len(candles)-1),
        'time': last['time'].strftime('%H:%M'),
        'price': round(last['c'], 5),
    }

# ═══════════════════════════════════════
# GERENCIAMENTO DE POSIÇÕES
# ═══════════════════════════════════════
def check_positions(state, current_prices):
    """Verifica SL/TP das posições abertas. Retorna lista de trades fechados."""
    closed = []
    still_open = []
    
    for pos in state['open_positions']:
        pair = pos['pair']
        price = current_prices.get(pair)
        
        if not price:
            still_open.append(pos)
            continue
        
        hit_sl = False
        hit_tp = False
        
        if pos['direction'] == 'LONG':
            if price <= pos['sl']:
                hit_sl = True
            elif price >= pos['tp']:
                hit_tp = True
        else:  # SHORT
            if price >= pos['sl']:
                hit_sl = True
            elif price <= pos['tp']:
                hit_tp = True
        
        if hit_sl or hit_tp:
            result = 'WIN' if hit_tp else 'LOSS'
            pnl = pos['tp_pips'] if hit_tp else -pos['sl_pips']
            
            closed_trade = {
                **pos,
                'closed_at': datetime.now().isoformat(),
                'close_price': price,
                'result': result,
                'pnl_pips': pnl,
                'duration_min': round((datetime.now() - datetime.fromisoformat(pos['opened_at'])).total_seconds() / 60, 1),
            }
            closed.append(closed_trade)
            state['closed_trades'].append(closed_trade)
            log(f"FECHOU {pair} {pos['direction']} → {result} {pnl:+.1f}p", 'TRADE')
        else:
            still_open.append(pos)
    
    state['open_positions'] = still_open
    return closed

def open_position(state, signal):
    """Abre nova posição se não houver conflito."""
    # Já tem posição nesse par?
    for pos in state['open_positions']:
        if pos['pair'] == signal['pair']:
            log(f"Já tem posição em {signal['pair']} — ignorando novo sinal", 'SKIP')
            return None
    
    # Já tem posição na mesma direção em outro par? (dedup)
    same_dir = [p for p in state['open_positions'] if p['direction'] == signal['direction']]
    if same_dir:
        existing = same_dir[0]['pair']
        log(f"Já tem {signal['direction']} em {existing} — ignorando {signal['pair']}", 'SKIP')
        return None
    
    # Máximo 3 posições abertas
    if len(state['open_positions']) >= 3:
        log(f"Máximo de 3 posições abertas — ignorando {signal['pair']}", 'SKIP')
        return None
    
    position = {
        'pair': signal['pair'],
        'direction': signal['direction'],
        'entry': signal['entry'],
        'sl': signal['sl'],
        'tp': signal['tp'],
        'sl_pips': signal['sl_pips'],
        'tp_pips': signal['tp_pips'],
        'entry_price': signal['price'],
        'opened_at': datetime.now().isoformat(),
        'atr_pips': signal['atr_pips'],
        'fvg_pips': signal['fvg_pips'],
        'score': signal['score'],
        'golden': signal['golden'],
    }
    
    state['open_positions'].append(position)
    log(f"ABRIU {signal['pair']} {signal['direction']} @ {signal['entry']} "
        f"SL={signal['sl_pips']}p TP={signal['tp_pips']}p Score={signal['score']}", 'TRADE')
    return position

# ═══════════════════════════════════════
# DAILY LOG + STATS
# ═══════════════════════════════════════
def update_daily_stats(state):
    today = datetime.now().strftime('%Y-%m-%d')
    
    if today not in state['daily_stats']:
        state['daily_stats'] = {}  # reset — only keep today
    
    today_trades = [t for t in state['closed_trades'] 
                    if t.get('closed_at', '').startswith(today)]
    
    wins = sum(1 for t in today_trades if t['result'] == 'WIN')
    total = len(today_trades)
    pnl = sum(t['pnl_pips'] for t in today_trades)
    
    state['daily_stats'][today] = {
        'trades': total,
        'wins': wins,
        'losses': total - wins,
        'wr': round(wins/max(total,1)*100, 1),
        'pnl_pips': round(pnl, 1),
        'open_positions': len(state['open_positions']),
        'pairs_traded': list(set(t['pair'] for t in today_trades)),
        'last_updated': datetime.now().isoformat(),
    }
    
    # Write daily log file
    log_file = LOG_DIR / f"daily_{today}.json"
    daily_data = {
        'date': today,
        'stats': state['daily_stats'][today],
        'closed_trades': today_trades,
        'open_positions': state['open_positions'],
    }
    log_file.write_text(json.dumps(daily_data, indent=2, default=str))
    
    return daily_data

# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════
def main():
    now = datetime.now()
    hour = now.hour
    dow = now.weekday()  # 0=Seg, 6=Dom
    
    force = '--force' in sys.argv
    
    # Verificar se deve rodar
    if not force:
        if dow in (0, 4, 5, 6):  # Seg, Sex, Sab, Dom
            log(f"Fora de dia útil (dow={dow}) — [SILENT]")
            return
        
        if hour < 4 or hour > 17:
            log(f"Fora de horário ({hour}h) — [SILENT]")
            return
        
        if hour not in GOLDEN_HOURS:
            log(f"Fora de golden hour ({hour}h) — só verificando posições")
    
    log(f"🤖 BOT INICIADO — {now.strftime('%d/%m %H:%M')} BRT")
    
    # Load state
    state = load_state()
    
    # ── Fase 1: Buscar preços atuais ──
    current_prices = {}
    for pair_name, symbol in PAIRS.items():
        candles = fetch_m15(symbol)
        if candles:
            current_prices[pair_name] = candles[-1]['c']
    
    # ── Fase 2: Verificar SL/TP das posições abertas ──
    check_positions(state, current_prices)
    
    # ── Fase 3: Detectar novos sinais (só em golden hours) ──
    if force or hour in GOLDEN_HOURS:
        long_signals = []
        short_signals = []
        
        for pair_name, symbol in PAIRS.items():
            signal = detect_signal(pair_name, symbol)
            if signal:
                if signal['direction'] == 'LONG':
                    long_signals.append(signal)
                else:
                    short_signals.append(signal)
                log(f"SINAL {signal['pair']} {signal['direction']} "
                    f"E={signal['entry']} SL={signal['sl_pips']}p TP={signal['tp_pips']}p "
                    f"Score={signal['score']} {'⭐' if signal['golden'] else ''}")
        
        # Dedup: melhor score por direção
        best_long = max(long_signals, key=lambda s: s['score']) if long_signals else None
        best_short = max(short_signals, key=lambda s: s['score']) if short_signals else None
        
        if best_long:
            open_position(state, best_long)
        if best_short:
            open_position(state, best_short)
        
        if not long_signals and not short_signals:
            log("Nenhum sinal detectado")
    
    # ── Fase 4: Atualizar stats e log ──
    daily = update_daily_stats(state)
    save_state(state)
    
    # ── Resumo ──
    stats = daily['stats']
    open_pos = len(state['open_positions'])
    log(f"📊 HOJE: {stats['trades']} trades | {stats['wins']}W/{stats['losses']}L | "
        f"WR={stats['wr']}% | PnL={stats['pnl_pips']:+.1f}p | Aberto={open_pos}")
    
    # Print open positions
    for pos in state['open_positions']:
        current = current_prices.get(pos['pair'], 0)
        if current and pos['entry_price']:
            if pos['direction'] == 'LONG':
                floating = (current - pos['entry_price']) / pip_val(pos['pair'])
            else:
                floating = (pos['entry_price'] - current) / pip_val(pos['pair'])
            log(f"  ABERTO {pos['pair']} {pos['direction']} "
                f"E={pos['entry']} SL={pos['sl_pips']}p | Floating={floating:+.1f}p", 'POS')

if __name__ == '__main__':
    main()
