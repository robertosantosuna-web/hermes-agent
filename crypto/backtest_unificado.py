#!/usr/bin/env python3
"""
BACKTEST UNIFICADO v10 — TradingView Feed, Multi-Agente, 90+ dias
Crypto: H1 nativo (125 dias, 4 pares)
Forex: H1 via FX_IDC (máx possível, 7 pares)
"""
import sys, json, subprocess, os
from pathlib import Path
from datetime import datetime, timedelta, timezone
import numpy as np

VENV_PYTHON = os.path.expanduser('~/.hermes/hermes-agent/venv/bin/python')

def get_tv_data(symbol, exchange, interval, n_bars):
    """Extrai dados do TradingView via tvDatafeed."""
    code = f"""
from tvDatafeed import TvDatafeed, Interval
tv = TvDatafeed()
data = tv.get_hist(symbol='{symbol}', exchange='{exchange}', interval=Interval.{interval}, n_bars={n_bars})
import json
if len(data) == 0:
    print('EMPTY')
else:
    result = {{
        'high': data['high'].values.tolist(),
        'low': data['low'].values.tolist(),
        'close': data['close'].values.tolist(),
        'open': data['open'].values.tolist(),
        'volume': data['volume'].values.tolist() if 'volume' in data.columns else [],
        'dates': [str(d) for d in data.index[:3]]
    }}
    print(json.dumps(result))
"""
    r = subprocess.run([VENV_PYTHON, '-c', code], capture_output=True, text=True, timeout=30)
    if r.returncode != 0 or r.stdout.strip() == 'EMPTY':
        return None
    try:
        data = json.loads(r.stdout.strip())
        return (np.array(data['high']), np.array(data['low']), 
                np.array(data['close']), np.array(data['open']),
                np.array(data['volume']) if data['volume'] else None)
    except:
        return None

# ═══ CONFIG ═══
RR = 3.0
MIN_CONFIDENCE = 55
N_BARS = 2500  # H1: 2500 velas = ~104 dias

CRYPTO_PAIRS = {
    'BTCUSD': ('BTCUSDT', 'BINANCE'),
    'ETHUSD': ('ETHUSDT', 'BINANCE'),
    'DOGEUSD': ('DOGEUSDT', 'BINANCE'),
    'BNBUSD': ('BNBUSDT', 'BINANCE'),
}

FOREX_PAIRS = {
    'EURUSD': ('EURUSD', 'FX_IDC'),
    'GBPUSD': ('GBPUSD', 'FX_IDC'),
    'USDJPY': ('USDJPY', 'FX_IDC'),
    'AUDUSD': ('AUDUSD', 'FX_IDC'),
    'NZDUSD': ('NZDUSD', 'FX_IDC'),
    'USDCAD': ('USDCAD', 'FX_IDC'),
    'USDCHF': ('USDCHF', 'FX_IDC'),
}

# ═══ ANÁLISE SIMPLIFICADA (sem importar módulos pesados) ═══

def ema(data, period):
    """EMA simples."""
    if len(data) < period: return data
    alpha = 2 / (period + 1)
    result = [data[0]]
    for i in range(1, len(data)):
        result.append(alpha * data[i] + (1 - alpha) * result[-1])
    return np.array(result)

def detect_ob_simple(highs, lows, closes, opens, direction):
    """Detector OB simplificado para backtest rápido."""
    n = len(closes)
    if n < 30: return None, 0
    
    atr = np.mean([max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
                    for i in range(1, min(20, n))])
    atr_pct = atr / closes[-1]
    avg_body = np.mean([abs(closes[i]-opens[i]) for i in range(max(0,n-20), n-1)])
    
    best, best_score = None, 0
    
    for i in range(n-3, max(10, n-150), -1):
        if direction == 'BUY':
            if closes[i] <= closes[i-1]: continue
            impulse = closes[i] - closes[i-1]
            if impulse < atr_pct * closes[i] * 0.3: continue
            
            ob_high = highs[i-1]
            ob_low = lows[i-1]
            
            # Fibonacci
            fib_50 = ob_low + (ob_high - ob_low) * 0.5
            fib_618 = ob_low + (ob_high - ob_low) * 0.618
            
            touched = False
            for j in range(i+1, min(i+20, n)):
                if lows[j] <= ob_high and lows[j] >= ob_low:
                    if lows[j] <= fib_618 and lows[j] >= fib_50:
                        touched = True
                        break
            
            if not touched: continue
            if any(lows[k] < ob_low for k in range(j+1, min(j+15, n))): continue
            
            score = 55
            ob_body = abs(closes[i-1] - opens[i-1])
            if ob_body > avg_body * 1.5: score += 15
            score += min(impulse / (atr_pct * closes[i]) * 15, 20)
            
            if score > best_score:
                best_score = score
                best = {'type': 'OB', 'entry': closes[i-1], 'direction': 'BUY', 'quality': score}
        
        else:  # SELL
            if closes[i] >= closes[i-1]: continue
            impulse = closes[i-1] - closes[i]
            if impulse < atr_pct * closes[i] * 0.3: continue
            
            ob_high = highs[i-1]
            ob_low = lows[i-1]
            
            fib_50 = ob_high - (ob_high - ob_low) * 0.5
            fib_618 = ob_high - (ob_high - ob_low) * 0.618
            
            touched = False
            for j in range(i+1, min(i+20, n)):
                if highs[j] <= ob_high and highs[j] >= ob_low:
                    if highs[j] >= fib_618 and highs[j] <= fib_50:
                        touched = True
                        break
            
            if not touched: continue
            if any(highs[k] > ob_high for k in range(j+1, min(j+15, n))): continue
            
            score = 55
            ob_body = abs(closes[i-1] - opens[i-1])
            if ob_body > avg_body * 1.5: score += 15
            score += min(impulse / (atr_pct * closes[i]) * 15, 20)
            
            if score > best_score:
                best_score = score
                best = {'type': 'OB', 'entry': closes[i-1], 'direction': 'SELL', 'quality': score}
    
    return best, best_score

def check_trend(closes):
    """Verifica tendência multi-TF simplificada."""
    if len(closes) < 100: return 'NEUTRAL'
    
    # M15 (50 velas H1... na verdade aqui é H1, ajustar)
    ema20 = np.mean(closes[-20:])
    ema50 = np.mean(closes[-50:])
    
    if closes[-1] > ema20 > ema50:
        return 'BUY'
    elif closes[-1] < ema20 < ema50:
        return 'SELL'
    return 'NEUTRAL'

def simulate_trade(highs, lows, closes, direction, entry, sl, tp):
    for i in range(len(closes)):
        if direction == 'BUY':
            if lows[i] <= sl: return {'result': 'LOSS', 'rr': -1, 'exit': sl}
            if highs[i] >= tp: return {'result': 'WIN', 'rr': RR, 'exit': tp}
        else:
            if highs[i] >= sl: return {'result': 'LOSS', 'rr': -1, 'exit': sl}
            if lows[i] <= tp: return {'result': 'WIN', 'rr': RR, 'exit': tp}
    return None

def run_backtest(pair, sym, exchange, label):
    """Executa backtest em um par."""
    print(f"  {pair:8s} [{label}]...", end=' ', flush=True)
    
    data = get_tv_data(sym, exchange, 'in_1_hour', N_BARS)
    if data is None:
        print("sem dados")
        return []
    
    h, l, c, o, v = data
    print(f"{len(c)} velas ", end='', flush=True)
    
    trades = []
    last_entry_idx = -100
    
    for i in range(100, len(c) - 5, 2):
        h_win, l_win = h[:i], l[:i]
        c_win, o_win = c[:i], o[:i]
        
        # Tendência
        trend = check_trend(c_win)
        if trend == 'NEUTRAL': continue
        
        # OB
        pat, score = detect_ob_simple(h_win, l_win, c_win, o_win, trend)
        if not pat or score < 55: continue
        
        idx = pat.get('idx', i)
        if abs(idx - last_entry_idx) < 10: continue
        last_entry_idx = idx
        
        entry = pat['entry']
        atr_pct = np.mean([max(h_win[j]-l_win[j], abs(h_win[j]-c_win[j-1]), abs(l_win[j]-c_win[j-1]))
                          for j in range(1, min(20, len(c_win)))]) / c_win[-1]
        sl_pct = max(atr_pct * 1.5, 0.15)
        
        if trend == 'BUY':
            sl = entry * (1 - sl_pct/100)
            tp = entry * (1 + sl_pct*RR/100)
        else:
            sl = entry * (1 + sl_pct/100)
            tp = entry * (1 - sl_pct*RR/100)
        
        result = simulate_trade(h[i:], l[i:], c[i:], trend, entry, sl, tp)
        if result:
            trades.append({
                'pair': pair, 'direction': trend, 'entry': entry,
                'result': result['result'], 'rr': result['rr'],
                'quality': score
            })
    
    print(f"{len(trades)} trades")
    return trades

# ═══ MAIN ═══
print(f"═══ BACKTEST UNIFICADO v10 — TradingView H1 ~100 dias ═══")
print(f"RR={RR}:1 N={N_BARS} velas H1")
print()

all_trades = []

# CRYPTO
print("═══ CRYPTO ═══")
for pair, (sym, ex) in CRYPTO_PAIRS.items():
    trades = run_backtest(pair, sym, ex, 'crypto')
    all_trades.extend(trades)

print()

# FOREX  
print("═══ FOREX ═══")
for pair, (sym, ex) in FOREX_PAIRS.items():
    trades = run_backtest(pair, sym, ex, 'forex')
    all_trades.extend(trades)

print()

# ═══ RESULTADOS ═══
if not all_trades:
    print("Nenhum trade encontrado")
    sys.exit(0)

wins = [t for t in all_trades if t['result'] == 'WIN']
losses = [t for t in all_trades if t['result'] == 'LOSS']
total = len(all_trades)
wr = len(wins) / total * 100
total_r = sum(t['rr'] for t in all_trades)
gross_win = sum(t['rr'] for t in wins) if wins else 0
gross_loss = abs(sum(t['rr'] for t in losses)) if losses else 1
pf = gross_win / gross_loss

print(f"═══ RESULTADO FINAL ═══")
print(f"Total: {total} | Wins: {len(wins)} | Losses: {len(losses)}")
print(f"WR: {wr:.1f}% | PF: {pf:.2f} | Total R: {total_r:+.1f}R")
print()

# Por sistema
for label, pairs_dict in [('CRYPTO', CRYPTO_PAIRS), ('FOREX', FOREX_PAIRS)]:
    sys_trades = [t for t in all_trades if t['pair'] in pairs_dict]
    if not sys_trades: continue
    sw = [t for t in sys_trades if t['result'] == 'WIN']
    swr = len(sw)/len(sys_trades)*100
    sr = sum(t['rr'] for t in sys_trades)
    print(f"{label}: {len(sys_trades)} trades, WR={swr:.1f}%, {sr:+.1f}R")

print()

# Por par
for pair in sorted(set(t['pair'] for t in all_trades)):
    pt = [t for t in all_trades if t['pair'] == pair]
    pw = [t for t in pt if t['result'] == 'WIN']
    pwr = len(pw)/len(pt)*100
    pr = sum(t['rr'] for t in pt)
    print(f"  {pair:8s}: {len(pt):4d} trades, WR={pwr:5.1f}%, {pr:+6.1f}R")

print()
print(f"✅ Aprovado" if wr >= 50 and pf >= 2.0 else "❌ Reprovado")
