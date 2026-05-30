#!/usr/bin/env python3
"""FOREX BOT v2 — TradingView (zero yfinance)."""
import sys, json, os, numpy as np
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
from tradingview_feed import TradingViewFeed

sys.path.insert(0, str(Path.home() / '.hermes' / 'scripts'))
from multi_agent import ConfluenciaAgent

RR = 3.0; MIN_SL = 10; MAX_SL = 30; RISK_PCT = 0.5
PAIRS = {
    'EURUSD': 0.0001, 'GBPUSD': 0.0001,
    'USDJPY': 0.01, 'EURJPY': 0.01, 'GBPJPY': 0.01,
}

def get_bias(highs, lows, closes):
    if len(highs) < 3: return 'NEUTRAL'
    ph, pl = highs[-3], lows[-3]; ch, cl, cc = highs[-2], lows[-2], closes[-2]
    if ch > ph and cc < ph: return 'SELL'
    if cl < pl and cc > pl: return 'BUY'
    if ch > ph and cc > ph: return 'BUY'
    if cl < pl and cc < pl: return 'SELL'
    return 'NEUTRAL'

def resample_daily(h, l, c, bars_per_day=288):
    """M5 → diário."""
    dh, dl, dc = [], [], []
    for i in range(0, len(c), bars_per_day):
        e = min(i+bars_per_day, len(c))
        if e-i < 10: continue
        dh.append(max(h[i:e])); dl.append(min(l[i:e])); dc.append(c[e-1])
    return np.array(dh), np.array(dl), np.array(dc)

feed = TradingViewFeed()
agent = ConfluenciaAgent()

print(f"Forex Bot v2 (TV) — {datetime.now().strftime('%H:%M')}")

for name, pip in PAIRS.items():
    try:
        # M5 para daily bias (288 velas/dia × 5 dias)
        h5, l5, c5, o5, v5 = feed.get_candles(name, '5m', 1440)
        if c5 is None or len(c5) < 200:
            continue
        dh, dl, dc = resample_daily(h5, l5, c5)
        if len(dc) < 3:
            continue
        bias = get_bias(dh, dl, dc)
        if bias == 'NEUTRAL':
            continue
        
        # M1 para sinais
        h, l, c, o, v = feed.get_candles(name, '1m', 500)
        if c is None or len(c) < 100:
            continue
        
        # Multi-Agent analysis
        decision, conf, signal = agent.analyze(name, h, l, c, bias, pip, is_metal=False)
        
        if decision != 'NEUTRAL' and signal:
            slp = max(MIN_SL, min(abs(signal['entry'] - l[-1]) / pip * 2, MAX_SL))
            print(f"  {name}: {decision} @{signal['entry']:.5f} SL={slp:.0f}p Conf={conf:.0f}%")
    
    except Exception as e:
        print(f"  {name}: {e}")

print("FIM")
