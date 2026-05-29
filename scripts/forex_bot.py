#!/usr/bin/env python3
"""FOREX BOT — Multi-Agente v1.0"""
import sys, json, os, numpy as np
from pathlib import Path
from datetime import datetime
import yfinance as yf

sys.path.insert(0, str(Path.home() / '.hermes' / 'scripts'))
from multi_agent import ConfluenciaAgent

RR = 3.0; MIN_SL = 10; MAX_SL = 30; RISK_PCT = 0.5
PAIRS = {
    'EURUSD': ('EURUSD=X', 0.0001), 'GBPUSD': ('GBPUSD=X', 0.0001),
    'USDJPY': ('USDJPY=X', 0.01), 'XAUUSD': ('GC=F', 0.01, True),
}

def get_bias(highs, lows, closes):
    if len(highs) < 3: return 'NEUTRAL'
    ph, pl = highs[-3], lows[-3]; ch, cl, cc = highs[-2], lows[-2], closes[-2]
    if ch > ph and cc < ph: return 'SELL'
    if cl < pl and cc > pl: return 'BUY'
    if ch > ph and cc > ph: return 'BUY'
    if cl < pl and cc < pl: return 'SELL'
    return 'NEUTRAL'

agent = ConfluenciaAgent()

print(f"Forex Bot Multi-Agente — {datetime.now().strftime('%H:%M')}")

for name, cfg in PAIRS.items():
    sym, pip = cfg[0], cfg[1]
    is_metal = len(cfg) > 2
    
    try:
        # Daily bias
        df_d = yf.Ticker(sym).history(period='30d', interval='1d')
        cm = {c.lower(): c for c in df_d.columns}
        dh = df_d[cm.get('high','High')].values
        dl = df_d[cm.get('low','Low')].values
        dc = df_d[cm.get('close','Close')].values
        bias = get_bias(dh, dl, dc)
        if bias == 'NEUTRAL': continue
        
        # M1 data
        df_m1 = yf.Ticker(sym).history(period='5d', interval='1m')
        if df_m1 is None or len(df_m1) < 100: continue
        h = df_m1['High'].values; l = df_m1['Low'].values
        c = df_m1['Close'].values
        
        # Multi-Agent analysis
        decision, conf, signal = agent.analyze(name, h, l, c, bias, pip, is_metal)
        
        if decision != 'NEUTRAL' and signal:
            slp = max(MIN_SL, min(abs(signal['entry'] - l[-1]) / pip * 2, MAX_SL if not is_metal else 300))
            print(f"  {name}: {decision} @{signal['entry']:.5f} SL={slp:.0f}p Conf={conf:.0f}%")
    
    except Exception as e:
        pass

print("FIM")
