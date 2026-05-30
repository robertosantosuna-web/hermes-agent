#!/usr/bin/env python3
"""ICT Killzone Detector v2 — Multi-level Liquidity (Asia + Daily + Weekly + Monthly)
Detecta rompimentos de liquidez no H1 e indica direção.
"""
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path

PAIRS = {
    'GBPJPY': ('GBPJPY=X', 0.01),
    'EURJPY': ('EURJPY=X', 0.01),
    'USDJPY': ('USDJPY=X', 0.01),
    'GBPUSD': ('GBPUSD=X', 0.0001),
    'EURUSD': ('EURUSD=X', 0.0001),
    'USDCAD': ('USDCAD=X', 0.0001),
}

OUTPUT = Path.home() / '.hermes' / 'forex' / 'ict_liquidity_state.json'

def get_liquidity_levels(sym, pip_val):
    """Coleta níveis de liquidez: Asia, Daily, Weekly, Monthly."""
    
    # H1 data for Asia/London
    df_h1 = yf.download(sym, period='2d', interval='1h', progress=False)
    if isinstance(df_h1.columns, pd.MultiIndex):
        df_h1.columns = df_h1.columns.get_level_values(0)
    df_h1['hour'] = df_h1.index.hour
    
    levels = {}
    
    # Asia range (last 20-23 UTC session)
    asia = df_h1[df_h1['hour'].isin([20, 21, 22, 23])].tail(8)
    if len(asia) >= 2:
        levels['asia_high'] = round(float(asia['High'].max()), 5)
        levels['asia_low'] = round(float(asia['Low'].min()), 5)
    
    # London session (last 3-6 UTC)
    london = df_h1[df_h1['hour'].isin([3, 4, 5, 6])].tail(8)
    if len(london) >= 2:
        levels['london_high'] = round(float(london['High'].max()), 5)
        levels['london_low'] = round(float(london['Low'].min()), 5)
    
    # Daily levels (previous day H1)
    df_d1 = yf.download(sym, period='5d', interval='1d', progress=False)
    if isinstance(df_d1.columns, pd.MultiIndex):
        df_d1.columns = df_d1.columns.get_level_values(0)
    if len(df_d1) >= 2:
        prev_day = df_d1.iloc[-2]
        levels['daily_high'] = round(float(prev_day['High']), 5)
        levels['daily_low'] = round(float(prev_day['Low']), 5)
    
    # Weekly levels
    df_w1 = yf.download(sym, period='1mo', interval='1wk', progress=False)
    if isinstance(df_w1.columns, pd.MultiIndex):
        df_w1.columns = df_w1.columns.get_level_values(0)
    if len(df_w1) >= 2:
        prev_week = df_w1.iloc[-2]
        levels['weekly_high'] = round(float(prev_week['High']), 5)
        levels['weekly_low'] = round(float(prev_week['Low']), 5)
    
    # Monthly levels
    df_m1 = yf.download(sym, period='3mo', interval='1mo', progress=False)
    if isinstance(df_m1.columns, pd.MultiIndex):
        df_m1.columns = df_m1.columns.get_level_values(0)
    if len(df_m1) >= 2:
        prev_month = df_m1.iloc[-2]
        levels['monthly_high'] = round(float(prev_month['High']), 5)
        levels['monthly_low'] = round(float(prev_month['Low']), 5)
    
    return levels

def check_breakouts(levels, pip_val):
    """Verifica quais níveis foram rompidos por Londres."""
    breaks = {'up': [], 'down': []}
    
    london_h = levels.get('london_high')
    london_l = levels.get('london_low')
    
    if london_h is None or london_l is None:
        return breaks
    
    # Check upside breakouts
    for key, label in [
        ('asia_high', '🌙 Asia High'),
        ('daily_high', '📅 Daily High'),
        ('weekly_high', '📅📅 Weekly High'),
        ('monthly_high', '📅📅📅 Monthly High'),
    ]:
        level = levels.get(key)
        if level and london_h > level:
            pips = round((london_h - level) / pip_val, 1)
            breaks['up'].append(f"{label} ({level}) +{pips}p")
    
    # Check downside breakouts
    for key, label in [
        ('asia_low', '🌙 Asia Low'),
        ('daily_low', '📅 Daily Low'),
        ('weekly_low', '📅📅 Weekly Low'),
        ('monthly_low', '📅📅📅 Monthly Low'),
    ]:
        level = levels.get(key)
        if level and london_l < level:
            pips = round((level - london_l) / pip_val, 1)
            breaks['down'].append(f"{label} ({level}) -{pips}p")
    
    return breaks

if __name__ == '__main__':
    print("🔍 ICT Liquidity Detector v2 — Multi-Level\n")
    
    results = []
    for name, (sym, pip_val) in PAIRS.items():
        try:
            levels = get_liquidity_levels(sym, pip_val)
            breaks = check_breakouts(levels, pip_val)
            
            up_count = len(breaks['up'])
            down_count = len(breaks['down'])
            
            # Direction and strength
            if up_count > 0 and down_count == 0:
                direction = 'BUY'
                icon = '🟢'
            elif down_count > 0 and up_count == 0:
                direction = 'SELL'
                icon = '🔴'
            elif up_count > 0 and down_count > 0:
                direction = 'CHOP'
                icon = '🟡'
            else:
                direction = 'WAIT'
                icon = '⚪'
            
            # Confluence score
            max_breaks = max(up_count, down_count)
            strength = '🔥🔥🔥' if max_breaks >= 3 else ('🔥🔥' if max_breaks >= 2 else ('🔥' if max_breaks >= 1 else ''))
            
            result = {
                'pair': name,
                'direction': direction,
                'strength': max_breaks,
                'breaks_up': breaks['up'],
                'breaks_down': breaks['down'],
                'levels': levels,
                'timestamp': datetime.now().isoformat(),
            }
            results.append(result)
            
            print(f"{icon} {name:8s} {direction:5s} {strength}")
            for b in breaks['up']:
                print(f"   ▲ {b}")
            for b in breaks['down']:
                print(f"   ▼ {b}")
            if not breaks['up'] and not breaks['down']:
                print(f"   — Nenhum nível rompido")
            print()
            
        except Exception as e:
            print(f"❌ {name}: {e}\n")
    
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(results, indent=2, default=str))
    print(f"✅ Salvo em {OUTPUT}")
