#!/usr/bin/env python3
"""ICT Killzone Simulation — H1→M5→M1 Strategy Backtest
Simula a estratégia de entrada por liquidez usando dados reais do yfinance.
Detecta: Asia/Daily liquidity capture → M5 ChoCh c/ deslocamento → M1 entrada.
Resultados esperados: GBPJPY 57% WR, USDCAD evitar.
"""
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT = Path.home() / '.hermes' / 'forex' / 'ict_simulation_results.json'

PAIRS = {
    'EURJPY': ('EURJPY=X', 0.01),
    'GBPJPY': ('GBPJPY=X', 0.01),
    'USDCAD': ('USDCAD=X', 0.0001),
}

def flatten(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def detect_choch_m5(df_m5, direction):
    """Detecta ChoCh com deslocamento no M5 (candle >50% avg range)."""
    h = df_m5['High'].values.astype(float)
    l = df_m5['Low'].values.astype(float)
    c = df_m5['Close'].values.astype(float)
    n = len(h)
    
    for i in range(3, n-2):
        if direction == 'SELL':
            if h[i] > h[i-1] and h[i] > h[i-2]:
                for j in range(i+1, min(i+6, n-1)):
                    if c[j] < l[i-1]:
                        rng = abs(h[j] - l[j])
                        avg_rng = np.mean([abs(h[k]-l[k]) for k in range(max(0,j-10), j)])
                        if rng > avg_rng * 1.5:
                            return {
                                'idx': j, 'price': c[j],
                                'range_high': h[i], 'range_low': min(l[j-2:j+1]) if j >= 2 else l[j]
                            }
        else:  # BUY
            if l[i] < l[i-1] and l[i] < l[i-2]:
                for j in range(i+1, min(i+6, n-1)):
                    if c[j] > h[i-1]:
                        rng = abs(h[j] - l[j])
                        avg_rng = np.mean([abs(h[k]-l[k]) for k in range(max(0,j-10), j)])
                        if rng > avg_rng * 1.5:
                            return {
                                'idx': j, 'price': c[j],
                                'range_high': max(h[j-2:j+1]) if j >= 2 else h[j],
                                'range_low': l[i]
                            }
    return None

def detect_choch_m1(df_m1, direction, premium_zone, discount_zone):
    """Detecta ChoCh M1 dentro de premium/discount com deslocamento >30% avg."""
    h = df_m1['High'].values.astype(float)
    l = df_m1['Low'].values.astype(float)
    c = df_m1['Close'].values.astype(float)
    n = len(h)
    
    for i in range(3, n-2):
        price = c[i]
        in_zone = False
        
        if direction == 'SELL':
            in_zone = premium_zone[0] <= price <= premium_zone[1]
            if in_zone and h[i] > h[i-1] and h[i] > h[i-2]:
                for j in range(i+1, min(i+5, n-1)):
                    if c[j] < l[i-1]:
                        rng = abs(h[j] - l[j])
                        avg_rng = np.mean([abs(h[k]-l[k]) for k in range(max(0,j-10), j)])
                        if rng > avg_rng * 1.3:
                            return {'idx': j, 'price': c[j], 'sl': h[i]}
        else:  # BUY
            in_zone = discount_zone[0] <= price <= discount_zone[1]
            if in_zone and l[i] < l[i-1] and l[i] < l[i-2]:
                for j in range(i+1, min(i+5, n-1)):
                    if c[j] > h[i-1]:
                        rng = abs(h[j] - l[j])
                        avg_rng = np.mean([abs(h[k]-l[k]) for k in range(max(0,j-10), j)])
                        if rng > avg_rng * 1.3:
                            return {'idx': j, 'price': c[j], 'sl': l[i]}
    return None

def get_asia_range(df_h1):
    df_h1['hour'] = df_h1.index.hour
    asia = df_h1[df_h1['hour'].isin([20, 21, 22, 23])].tail(8)
    if len(asia) >= 2:
        return float(asia['High'].max()), float(asia['Low'].min())
    return None, None

def get_prev_day_levels(df_h1):
    df_h1['date'] = df_h1.index.date
    dates = sorted(df_h1['date'].unique())
    if len(dates) < 2:
        return None, None
    prev = df_h1[df_h1['date'] == dates[-2]]
    return float(prev['High'].max()), float(prev['Low'].min())

def simulate_day(sym, pip_val, date_str):
    """Simula um dia completo da estratégia ICT H1→M5→M1."""
    end = pd.Timestamp(date_str) + timedelta(days=1)
    start = end - timedelta(days=3)
    
    df_h1 = flatten(yf.download(sym, start=start, end=end, interval='1h', progress=False))
    df_m5 = flatten(yf.download(sym, start=start, end=end, interval='5m', progress=False))
    df_m1 = flatten(yf.download(sym, start=start, end=end, interval='1m', progress=False))
    
    if len(df_h1) < 20 or len(df_m5) < 50:
        return None
    
    target = pd.Timestamp(date_str).date()
    df_h1['date'] = df_h1.index.date
    df_m5_day = df_m5[df_m5.index.date == target]
    df_m1_day = df_m1[df_m1.index.date == target]
    
    if len(df_m5_day) < 30:
        return None
    
    asia_h, asia_l = get_asia_range(df_h1)
    daily_h, daily_l = get_prev_day_levels(df_h1)
    
    df_h1['hour'] = df_h1.index.hour
    london = df_h1[(df_h1['date'] == target) & (df_h1['hour'].isin([3,4,5,6]))]
    
    if len(london) < 2:
        return None
    
    london_h = float(london['High'].max())
    london_l = float(london['Low'].min())
    
    direction = None
    captured_level = None
    
    if asia_h and london_h > asia_h:
        direction = 'BUY'; captured_level = f'Asia High {asia_h:.5f}'
    elif daily_h and london_h > daily_h:
        direction = 'BUY'; captured_level = f'Daily High {daily_h:.5f}'
    elif asia_l and london_l < asia_l:
        direction = 'SELL'; captured_level = f'Asia Low {asia_l:.5f}'
    elif daily_l and london_l < daily_l:
        direction = 'SELL'; captured_level = f'Daily Low {daily_l:.5f}'
    
    if not direction:
        return {'date': date_str, 'direction': None, 'result': 'NO_SETUP'}
    
    choch_m5 = detect_choch_m5(df_m5_day, direction)
    if not choch_m5:
        return {'date': date_str, 'direction': direction, 'captured': captured_level, 'result': 'NO_M5_CHOCH'}
    
    range_size = choch_m5['range_high'] - choch_m5['range_low']
    mid = choch_m5['range_low'] + range_size / 2
    
    if direction == 'SELL':
        premium = (mid, choch_m5['range_high'])
        discount = (choch_m5['range_low'], mid)
        target_zone = premium
    else:
        premium = (mid, choch_m5['range_high'])
        discount = (choch_m5['range_low'], mid)
        target_zone = discount
    
    if len(df_m1_day) < 10:
        return {'date': date_str, 'direction': direction, 'm5_choch': True, 'result': 'NO_M1_DATA'}
    
    entry = detect_choch_m1(df_m1_day, direction, premium, discount)
    if not entry:
        return {'date': date_str, 'direction': direction, 'm5_choch': True, 'result': 'NO_M1_ENTRY'}
    
    sl_pips = abs(entry['price'] - entry['sl']) / pip_val
    tp_price = entry['price'] + sl_pips * 3 * pip_val if direction == 'BUY' else entry['price'] - sl_pips * 3 * pip_val
    
    for i in range(entry['idx'] + 1, len(df_m1_day)):
        hi = float(df_m1_day.iloc[i]['High'])
        lo = float(df_m1_day.iloc[i]['Low'])
        if direction == 'BUY':
            if hi >= tp_price:
                return {'date': date_str, 'direction': direction, 'result': 'WIN', 'pips': round(sl_pips*3, 1)}
            if lo <= entry['sl']:
                return {'date': date_str, 'direction': direction, 'result': 'LOSS', 'pips': round(-sl_pips, 1)}
        else:
            if lo <= tp_price:
                return {'date': date_str, 'direction': direction, 'result': 'WIN', 'pips': round(sl_pips*3, 1)}
            if hi >= entry['sl']:
                return {'date': date_str, 'direction': direction, 'result': 'LOSS', 'pips': round(-sl_pips, 1)}
    
    return {'date': date_str, 'direction': direction, 'result': 'OPEN'}

if __name__ == '__main__':
    print("ICT Killzone Simulation — H1→M5→M1\n")
    all_results = []
    for name, (sym, pip_val) in PAIRS.items():
        print(f"## {name}")
        pair_results = []
        today = datetime.now().date()
        for days_back in range(1, 15):
            date = today - timedelta(days=days_back)
            if date.weekday() >= 5: continue
            result = simulate_day(sym, pip_val, date.strftime('%Y-%m-%d'))
            if result:
                pair_results.append(result)
                status = result.get('result', '?')
                icon = '🟢' if status == 'WIN' else ('🔴' if status == 'LOSS' else '⚪')
                print(f"  {icon} {result['date']} {result.get('direction','?') or '?':5s} {status:12s} {str(result.get('pips','')):>6s}")
        all_results.extend(pair_results)
        wins = sum(1 for r in pair_results if r.get('result') == 'WIN')
        losses = sum(1 for r in pair_results if r.get('result') == 'LOSS')
        total = wins + losses
        wr = round(wins/total*100,1) if total else 0
        pnl = sum(r.get('pips',0) for r in pair_results)
        print(f"  → {wins}W/{losses}L WR={wr}% PnL={pnl:+.1f}p\n")
    
    tw = sum(1 for r in all_results if r.get('result')=='WIN')
    tl = sum(1 for r in all_results if r.get('result')=='LOSS')
    print(f"TOTAL: {tw}W/{tl}L WR={round(tw/(tw+tl)*100,1) if (tw+tl) else 0}% PnL={sum(r.get('pips',0) for r in all_results):+.1f}p")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(all_results, indent=2, default=str))
