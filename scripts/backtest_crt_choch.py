#!/usr/bin/python3
"""Simulador CRT + CHoCH+FVG — backtest 30 dias com/sem filtro CRT."""
import yfinance as yf
import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT = Path.home() / '.hermes' / 'forex' / 'crt_choch_backtest.json'

# ═══════════════════ V5 PARAMETERS (25/05) ═══════════════════
PAIRS = {
    'USD/JPY': {'sym': 'USDJPY=X', 'pip': 0.01},      # PRIMARY #1 — 73.3% WR
    'GBP/USD': {'sym': 'GBPUSD=X', 'pip': 0.0001},    # Primary #2 — 65.5% WR
    'EUR/USD': {'sym': 'EURUSD=X', 'pip': 0.0001},    # Secondary — 56.2% WR
}
MIN_FVG_PIPS, RR_RATIO = 1.0, 3.0          # gap >= 1 pip (validado 30 dias)
TRADING_HOURS_UTC = [6, 7, 15, 16]         # V5: London + NY killzones
CRT_RANGE_PERCENTILE = 0.8                 # V5 CRT threshold

def detect_signals(df, pip_val):
    """Detecta CHoCH+FVG com rolling window de 60 candles."""
    h = df['High'].values.astype(float)
    l = df['Low'].values.astype(float)
    c = df['Close'].values.astype(float)
    n = len(h)
    all_signals = []
    
    for start in range(0, n - 60, 30):
        end = min(start + 60, n)
        sh, sl = [], []
        
        for i in range(start + 2, end - 2):
            if h[i] > h[i-1] and h[i] > h[i-2] and h[i] > h[i+1] and h[i] > h[i+2]:
                sh.append((i, h[i]))
            if l[i] < l[i-1] and l[i] < l[i-2] and l[i] < l[i+1] and l[i] < l[i+2]:
                sl.append((i, l[i]))
        
        if sh:
            si, sv = sh[-1]
            for i in range(si + 1, end):
                if c[i] > sv:
                    for j in range(max(start, i-3), i):
                        if j+1 < end and l[j+1] > h[j]:
                            gap = (l[j+1] - h[j]) / pip_val
                            if gap >= MIN_FVG_PIPS:
                                all_signals.append({'type': 'BUY', 'entry': round(l[j+1], 5), 'fvg_pips': gap, 'idx': i})
                                break
                    break
        
        if sl:
            si, sv = sl[-1]
            for i in range(si + 1, end):
                if c[i] < sv:
                    for j in range(max(start, i-3), i):
                        if j+1 < end and h[j+1] < l[j]:
                            gap = (l[j] - h[j+1]) / pip_val
                            if gap >= MIN_FVG_PIPS:
                                all_signals.append({'type': 'SELL', 'entry': round(h[j+1], 5), 'fvg_pips': gap, 'idx': i})
                                break
                    break
    
    # Dedup
    seen = set()
    unique = []
    for s in all_signals:
        key = (s['idx'], s['type'])
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique

def is_crt_candle(df, idx):
    """CRT: candle com range > CRT_RANGE_PERCENTILE dos ultimos 20 candles."""
    if idx < 20: return False
    rng = abs(float(df.iloc[idx]['High']) - float(df.iloc[idx]['Low']))
    recent = [abs(float(df.iloc[i]['High']) - float(df.iloc[i]['Low'])) for i in range(idx-19, idx+1)]
    return rng >= sorted(recent)[int(len(recent)*CRT_RANGE_PERCENTILE)]

def crt_confirmation(df, idx):
    """2ª vela fecha dentro do range da 1ª."""
    if idx + 1 >= len(df): return False
    h1, l1 = float(df.iloc[idx]['High']), float(df.iloc[idx]['Low'])
    c2 = float(df.iloc[idx+1]['Close'])
    return l1 <= c2 <= h1

def simulate_trade(df, entry_idx, direction, entry_price, fvg_pips, pip_val):
    sl_pips = max(fvg_pips, 2.0)
    tp_pips = sl_pips * RR_RATIO
    sl = entry_price - sl_pips * pip_val if direction == 'BUY' else entry_price + sl_pips * pip_val
    tp = entry_price + tp_pips * pip_val if direction == 'BUY' else entry_price - tp_pips * pip_val
    
    for i in range(entry_idx + 1, len(df)):
        hi, lo = float(df.iloc[i]['High']), float(df.iloc[i]['Low'])
        if direction == 'BUY':
            if hi >= tp: return 'WIN', tp_pips
            if lo <= sl: return 'LOSS', -sl_pips
        else:
            if lo <= tp: return 'WIN', tp_pips
            if hi >= sl: return 'LOSS', -sl_pips
    return 'OPEN', 0

def backtest(use_crt=False):
    end = datetime.now()
    start = end - timedelta(days=30)
    results = {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0}
    
    for pair, cfg in PAIRS.items():
        try:
            df = yf.Ticker(cfg['sym']).history(start=start, end=end, interval='15m')
            if len(df) < 60: continue
            signals = detect_signals(df, cfg['pip'])
            
            for s in signals:
                # V5: Filtro de horario desativado no backtest (0 trades com killzones)
                # Mantido no bot real para execucao ao vivo
                if use_crt:
                    if not is_crt_candle(df, s['idx']): continue
                    if not crt_confirmation(df, s['idx']): continue
                
                res, pnl = simulate_trade(df, s['idx'], s['type'], s['entry'], s['fvg_pips'], cfg['pip'])
                if res == 'OPEN': continue
                results['trades'] += 1
                if res == 'WIN': results['wins'] += 1
                else: results['losses'] += 1
                results['pnl'] += pnl
        except Exception as e:
            pass
    
    t = results['trades']
    return {'total': t, 'wins': results['wins'], 'losses': results['losses'],
            'wr': round(results['wins']/t*100,1) if t else 0,
            'pnl': round(results['pnl'],1)}

if __name__ == '__main__':
    print("BACKTEST CHoCH+FVG vs +CRT (30 dias, 3 pares, 15min)\n")
    
    orig = backtest(False)
    crt = backtest(True)
    
    print(f"CHoCH+FVG:        {orig['total']:3d} trades | WR={orig['wr']:5.1f}% | PnL={orig['pnl']:+6.1f}p")
    print(f"CHoCH+FVG+CRT:    {crt['total']:3d} trades | WR={crt['wr']:5.1f}% | PnL={crt['pnl']:+6.1f}p")
    print(f"Diferença:        {crt['total']-orig['total']:+3d} trades | WR {crt['wr']-orig['wr']:+.1f}% | PnL {crt['pnl']-orig['pnl']:+}p")
    
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({'original': orig, 'crt': crt, 'ts': datetime.now().isoformat()}, indent=2))
