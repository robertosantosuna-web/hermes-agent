#!/usr/bin/env python3
"""Backtest XAU/USD — FVG+CRT nos 3 timeframes principais.
Requer: yfinance, pandas, numpy.
Uso: python3 backtest_xau.py
"""
import yfinance as yf
import pandas as pd
import numpy as np

MIN_GAP = 1.0     # Gap mínimo em dólares
RR = 3.0
CRT_LOOKBACK = 20
CRT_PERCENTILE = 70
MIN_SL = 2.0      # SL mínimo em dólares (backtest)

def pull_xau(tf):
    intervals = {'5m': '5m', '15m': '15m', '30m': '30m'}
    xau = yf.Ticker('GC=F')
    df = xau.history(period='59d', interval=intervals[tf])
    df = df.reset_index()
    df.columns = ['dt', 'open', 'high', 'low', 'close', 'volume', 'divs', 'splits']
    return df

def detect_fvg(df, i):
    """FVG sem filtro de pavio (ouro quebra wick_pct)."""
    if i < 2:
        return None
    c0, c1, c2 = df.iloc[i], df.iloc[i-1], df.iloc[i-2]
    if c2['low'] > c0['high']:
        return {'type': 'BEARISH', 'gap': c2['low'] - c0['high'], 'entry': c0['high'], 'sl': c2['low']}
    if c2['high'] < c0['low']:
        return {'type': 'BULLISH', 'gap': c0['low'] - c2['high'], 'entry': c0['low'], 'sl': c2['high']}
    return None

def is_crt(df, i, lookback=20, pct=70):
    if i < lookback:
        return False
    rng = abs(df.iloc[i]['high'] - df.iloc[i]['low'])
    recent = [abs(df.iloc[j]['high'] - df.iloc[j]['low']) for j in range(i-lookback, i+1)]
    return rng >= sorted(recent)[int(len(recent) * pct / 100)]

# ... (see full script at /tmp/backtest_xau_v2.py)
