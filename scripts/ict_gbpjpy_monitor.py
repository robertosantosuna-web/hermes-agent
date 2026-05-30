#!/usr/bin/env python3
"""GBPJPY ICT Live Monitor — London Session
Monitora em tempo real: Asia range, London breakout, displacement, M5/M1 entry setup.
"""
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path
import time

SYM = 'GBPJPY=X'
PIP = 0.01
OUTPUT = Path.home() / '.hermes' / 'forex' / 'ict_gbpjpy_live.json'

def flatten(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def check_setup():
    """Verifica se há setup ICT ativo agora."""
    now = datetime.now()
    
    # Baixar dados recentes
    df_h1 = flatten(yf.download(SYM, period='3d', interval='1h', progress=False))
    df_m5 = flatten(yf.download(SYM, period='1d', interval='5m', progress=False))
    
    if len(df_h1) < 20:
        return {'status': 'NO_DATA'}
    
    df_h1['date'] = df_h1.index.date
    df_h1['hour'] = df_h1.index.hour
    
    # Hoje
    today = now.date()
    day = df_h1[df_h1['date'] == today]
    prev = df_h1[df_h1['date'] < today]
    
    if len(day) < 3 or len(prev) < 5:
        return {'status': 'INSUFFICIENT_DATA'}
    
    # Asia range
    asia = prev[prev['hour'].isin([20,21,22,23])].tail(8)
    ah, al = None, None
    if len(asia) >= 2:
        ah, al = float(asia['High'].max()), float(asia['Low'].min())
    
    # Daily levels
    dh, dl = float(prev['High'].max()), float(prev['Low'].min())
    
    # London session
    london = day[day['hour'].isin([3,4,5,6,7,8])]
    if len(london) < 2:
        return {'status': 'PRE_LONDON', 'asia_h': ah, 'asia_l': al, 'daily_h': dh, 'daily_l': dl}
    
    lh = float(london['High'].max())
    ll = float(london['Low'].min())
    
    # Count breaks
    breaks_up = 0
    breaks_down = 0
    if ah and lh > ah: breaks_up += 1
    if lh > dh: breaks_up += 1
    if al and ll < al: breaks_down += 1
    if ll < dl: breaks_down += 1
    
    total_breaks = max(breaks_up, breaks_down)
    direction = 'BUY' if breaks_up > breaks_down else 'SELL'
    
    # Displacement check
    avg_rng = np.mean([float(row['High'])-float(row['Low']) for _, row in day.iterrows()])
    
    displacement = None
    for idx, row in day[day['hour'].isin([6,7,8])].iterrows():
        rng = float(row['High']) - float(row['Low'])
        o, c = float(row['Open']), float(row['Close'])
        if direction == 'BUY' and c <= o: continue
        if direction == 'SELL' and c >= o: continue
        if rng >= avg_rng * 1.4:
            displacement = {
                'hour': idx.hour, 'rng': round(rng, 4),
                'avg_rng': round(avg_rng, 4),
                'close': round(c, 5),
            }
    
    # Current M5 price
    m5_price = float(df_m5.iloc[-1]['Close']) if len(df_m5) > 0 else None
    
    result = {
        'status': 'LIVE',
        'timestamp': now.isoformat(),
        'pair': 'GBPJPY',
        'price': m5_price,
        'asia': {'high': round(ah, 2) if ah else None, 'low': round(al, 2) if al else None},
        'daily': {'high': round(dh, 2), 'low': round(dl, 2)},
        'london': {'high': round(lh, 2), 'low': round(ll, 2)},
        'breaks': total_breaks,
        'direction': direction if total_breaks >= 1 else None,
        'displacement': displacement,
        'ready': total_breaks >= 2 and displacement is not None,
    }
    
    return result

if __name__ == '__main__':
    result = check_setup()
    print(json.dumps(result, indent=2))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2))
