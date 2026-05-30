#!/usr/bin/env python3
"""ICT Killzone Backtest v2 — Refined Filters
Regras:
  1. 2+ níveis de liquidez rompidos (Asia + Daily/Weekly/Monthly)
  2. Displacement candle 06-08h UTC com range > 1.4x média
  3. Retracement < 50% do displacement
  4. M1 ChoCh com deslocamento
  5. 3:1 RR | WR < 40% → descartar par
"""
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT = Path.home() / '.hermes' / 'forex' / 'ict_backtest_v2.json'

PAIRS = {
    'GBPJPY': ('GBPJPY=X', 0.01),
    'EURJPY': ('EURJPY=X', 0.01),
    'USDJPY': ('USDJPY=X', 0.01),
    'GBPUSD': ('GBPUSD=X', 0.0001),
    'EURUSD': ('EURUSD=X', 0.0001),
    'USDCAD': ('USDCAD=X', 0.0001),
}

MIN_WR = 40.0  # Abaixo disso → descartar par
RR = 3.0
MIN_BREAKS = 2  # 2+ níveis (Asia + Daily/Weekly)
DISP_HOURS = [6, 7, 8]  # UTC — London killzone
DISP_MULTIPLIER = 1.4  # Range > 1.4x média
MAX_RETRACEMENT = 0.5  # < 50% do displacement

def flatten(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def get_levels(df_h1, target_date):
    """Coleta níveis: Asia, Daily, Weekly, Monthly."""
    df_h1['date'] = df_h1.index.date
    df_h1['hour'] = df_h1.index.hour
    
    prev_all = df_h1[df_h1['date'] < target_date]
    levels = {}
    
    # Asia (20-23 UTC previous day)
    asia = prev_all[prev_all['hour'].isin([20,21,22,23])].tail(8)
    if len(asia) >= 2:
        levels['asia_high'] = float(asia['High'].max())
        levels['asia_low'] = float(asia['Low'].min())
    
    # Daily
    if len(prev_all) > 0:
        levels['daily_high'] = float(prev_all['High'].max())
        levels['daily_low'] = float(prev_all['Low'].min())
    
    return levels

def count_breaks(levels, london_high, london_low):
    """Conta níveis rompidos por Londres."""
    breaks_up = 0
    breaks_down = 0
    
    for key, val in levels.items():
        if 'high' in key and london_high > val:
            breaks_up += 1
        if 'low' in key and london_low < val:
            breaks_down += 1
    
    return max(breaks_up, breaks_down), 'BUY' if breaks_up > breaks_down else 'SELL'

def find_displacement(day_h1, direction, disp_hours, multiplier):
    """Encontra candle de displacement no H1."""
    day_h1_h = day_h1[day_h1.index.hour.isin(disp_hours)]
    if len(day_h1_h) < 2:
        return None
    
    avg_rng = np.mean([float(row['High'])-float(row['Low']) for _, row in day_h1.iterrows()])
    
    best = None
    for idx, row in day_h1_h.iterrows():
        rng = float(row['High']) - float(row['Low'])
        o, c = float(row['Open']), float(row['Close'])
        
        # Direction check
        if direction == 'BUY' and c <= o:
            continue
        if direction == 'SELL' and c >= o:
            continue
        
        if rng >= avg_rng * multiplier:
            if best is None or rng > best['rng']:
                best = {
                    'hour': idx.hour,
                    'rng': rng,
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': c,
                    'avg_rng': avg_rng,
                }
    
    return best

def check_retracement(day_h1, displacement, direction, max_ret):
    """Verifica se a retração é < 50% do displacement."""
    if not displacement:
        return False
    
    disp_rng = displacement['high'] - displacement['low']
    disp_hour = displacement['hour']
    
    # Check candles after displacement (up to 4 candles)
    day_sorted = day_h1.sort_index()
    after = day_sorted[day_sorted.index.hour > disp_hour].head(4)
    
    if len(after) < 1:
        return False
    
    if direction == 'BUY':
        # After displacement up, price should not drop below 50% of disp low
        ret_level = displacement['low'] + disp_rng * max_ret
        lowest = float(after['Low'].min())
        return lowest >= ret_level
    else:
        # After displacement down, price should not rally above 50%
        ret_level = displacement['high'] - disp_rng * max_ret
        highest = float(after['High'].max())
        return highest <= ret_level

def detect_choch_m5(df_m5_day, direction):
    """Detecta ChoCh com deslocamento no M5."""
    if len(df_m5_day) < 10:
        return None
    
    h = df_m5_day['High'].values.astype(float)
    l = df_m5_day['Low'].values.astype(float)
    c = df_m5_day['Close'].values.astype(float)
    n = len(h)
    
    avg_rng = np.mean([abs(h[i]-l[i]) for i in range(n)])
    
    for i in range(3, n-2):
        if direction == 'SELL':
            if h[i] > h[i-1] and h[i] > h[i-2]:
                for j in range(i+1, min(i+6, n-1)):
                    if c[j] < l[i-1]:
                        rng = abs(h[j] - l[j])
                        if rng > avg_rng * 1.3:
                            return {
                                'idx': j, 'price': c[j],
                                'range_high': h[i], 'range_low': min(l[j-2:j+1]) if j >= 2 else l[j]
                            }
        else:
            if l[i] < l[i-1] and l[i] < l[i-2]:
                for j in range(i+1, min(i+6, n-1)):
                    if c[j] > h[i-1]:
                        rng = abs(h[j] - l[j])
                        if rng > avg_rng * 1.3:
                            return {
                                'idx': j, 'price': c[j],
                                'range_high': max(h[j-2:j+1]) if j >= 2 else h[j],
                                'range_low': l[i]
                            }
    return None

def detect_entry_m1(df_m1_day, direction, premium_zone, discount_zone):
    """Detecta entrada M1 no premium/discount."""
    if len(df_m1_day) < 10:
        return None
    
    h = df_m1_day['High'].values.astype(float)
    l = df_m1_day['Low'].values.astype(float)
    c = df_m1_day['Close'].values.astype(float)
    n = len(h)
    
    target = discount_zone if direction == 'BUY' else premium_zone
    avg_rng = np.mean([abs(h[i]-l[i]) for i in range(n)])
    
    for i in range(3, n-2):
        price = c[i]
        if not (target[0] <= price <= target[1]):
            continue
        
        if direction == 'SELL':
            if h[i] > h[i-1] and h[i] > h[i-2]:
                for j in range(i+1, min(i+5, n-1)):
                    if c[j] < l[i-1]:
                        rng = abs(h[j] - l[j])
                        if rng > avg_rng * 1.2:
                            return {'idx': j, 'entry': c[j], 'sl': h[i]}
        else:
            if l[i] < l[i-1] and l[i] < l[i-2]:
                for j in range(i+1, min(i+5, n-1)):
                    if c[j] > h[i-1]:
                        rng = abs(h[j] - l[j])
                        if rng > avg_rng * 1.2:
                            return {'idx': j, 'entry': c[j], 'sl': l[i]}
    return None

def simulate_trade(df_m1_day, entry, direction, pip_val):
    """Simula resultado do trade."""
    sl_pips = abs(entry['entry'] - entry['sl']) / pip_val
    if sl_pips <= 0 or sl_pips > 15:
        return 'SKIP', 0
    
    tp_price = entry['entry'] + sl_pips * RR * pip_val if direction == 'BUY' else entry['entry'] - sl_pips * RR * pip_val
    
    for i in range(entry['idx'] + 1, len(df_m1_day)):
        hi = float(df_m1_day.iloc[i]['High'])
        lo = float(df_m1_day.iloc[i]['Low'])
        
        if direction == 'BUY':
            if hi >= tp_price:
                return 'WIN', round(sl_pips * RR, 1)
            if lo <= entry['sl']:
                return 'LOSS', round(-sl_pips, 1)
        else:
            if lo <= tp_price:
                return 'WIN', round(sl_pips * RR, 1)
            if hi >= entry['sl']:
                return 'LOSS', round(-sl_pips, 1)
    
    return 'OPEN', 0


def backtest_pair(sym, pip_val, name, days=30):
    """Backtest completo para um par."""
    results = []
    today = datetime.now().date()
    
    for days_back in range(1, days+1):
        date = today - timedelta(days=days_back)
        if date.weekday() >= 5:
            continue
        
        date_str = date.strftime('%Y-%m-%d')
        end = pd.Timestamp(date_str) + timedelta(days=1)
        start = end - timedelta(days=4)
        
        try:
            df_h1 = flatten(yf.download(sym, start=start, end=end, interval='1h', progress=False))
            df_m5 = flatten(yf.download(sym, start=start, end=end, interval='5m', progress=False))
            df_m1 = flatten(yf.download(sym, start=start, end=end, interval='1m', progress=False))
        except:
            continue
        
        if len(df_h1) < 20:
            continue
        
        target = pd.Timestamp(date_str).date()
        day_h1 = df_h1[df_h1.index.date == target]
        df_m5_day = df_m5[df_m5.index.date == target]
        df_m1_day = df_m1[df_m1.index.date == target]
        
        if len(day_h1) < 5 or len(df_m5_day) < 30:
            results.append({'date': date_str, 'result': 'NO_DATA'})
            continue
        
        # Step 1: Get levels
        levels = get_levels(df_h1, target)
        if not levels:
            results.append({'date': date_str, 'result': 'NO_LEVELS'})
            continue
        
        # Step 2: London breakout
        london = day_h1[day_h1.index.hour.isin([3,4,5,6,7,8])]
        if len(london) < 2:
            results.append({'date': date_str, 'result': 'NO_LONDON'})
            continue
        
        lh, ll = float(london['High'].max()), float(london['Low'].min())
        num_breaks, direction = count_breaks(levels, lh, ll)
        
        if num_breaks < MIN_BREAKS:
            results.append({'date': date_str, 'result': 'NO_BREAKS', 'breaks': num_breaks})
            continue
        
        # Step 3: Displacement
        displ = find_displacement(day_h1, direction, DISP_HOURS, DISP_MULTIPLIER)
        if not displ:
            results.append({'date': date_str, 'result': 'NO_DISPLACEMENT', 'direction': direction, 'breaks': num_breaks})
            continue
        
        # Step 4: Retracement check
        ret_ok = check_retracement(day_h1, displ, direction, MAX_RETRACEMENT)
        if not ret_ok:
            results.append({'date': date_str, 'result': 'DEEP_RETRACE', 'direction': direction, 'breaks': num_breaks})
            continue
        
        # Step 5: M5 ChoCh
        choch_m5 = detect_choch_m5(df_m5_day, direction)
        if not choch_m5:
            results.append({'date': date_str, 'result': 'NO_M5_CHOCH', 'direction': direction, 'breaks': num_breaks})
            continue
        
        # Step 6: Premium/Discount
        rng_size = choch_m5['range_high'] - choch_m5['range_low']
        mid = choch_m5['range_low'] + rng_size / 2
        premium = (mid, choch_m5['range_high'])
        discount = (choch_m5['range_low'], mid)
        
        # Step 7: M1 Entry
        entry = detect_entry_m1(df_m1_day, direction, premium, discount)
        if not entry:
            results.append({'date': date_str, 'result': 'NO_ENTRY', 'direction': direction, 'breaks': num_breaks})
            continue
        
        # Step 8: Simulate
        result, pips = simulate_trade(df_m1_day, entry, direction, pip_val)
        results.append({
            'date': date_str, 'result': result, 'pips': pips,
            'direction': direction, 'breaks': num_breaks,
            'disp_hour': displ['hour'], 'disp_rng': round(displ['rng'], 4),
            'avg_rng': round(displ['avg_rng'], 4),
        })
    
    return results


if __name__ == '__main__':
    print("🔬 ICT Killzone Backtest v2 — Filtros Refinados\n")
    print(f"Regras: {MIN_BREAKS}+ níveis | Displacement {DISP_HOURS}h | Range >{DISP_MULTIPLIER}x | Retrace <{MAX_RETRACEMENT*100}%\n")
    
    all_results = {}
    
    for name, (sym, pip_val) in PAIRS.items():
        print(f"## {name}")
        results = backtest_pair(sym, pip_val, name, days=7)
        all_results[name] = results
        
        trades = [r for r in results if r['result'] in ('WIN', 'LOSS')]
        wins = sum(1 for r in trades if r['result'] == 'WIN')
        losses = len(trades) - wins
        total = len(trades)
        wr = round(wins / total * 100, 1) if total > 0 else 0
        pnl = sum(r.get('pips', 0) for r in trades)
        
        # Filter reasons
        no_breaks = sum(1 for r in results if r['result'] == 'NO_BREAKS')
        no_disp = sum(1 for r in results if r['result'] == 'NO_DISPLACEMENT')
        deep_ret = sum(1 for r in results if r['result'] == 'DEEP_RETRACE')
        no_m5 = sum(1 for r in results if r['result'] == 'NO_M5_CHOCH')
        no_entry = sum(1 for r in results if r['result'] == 'NO_ENTRY')
        
        status = '✅' if wr >= MIN_WR else '❌ DESCARTAR'
        
        print(f"  Trades: {wins}W/{losses}L WR={wr}% PnL={pnl:+.1f}p {status}")
        print(f"  Filtrados: NoBreak={no_breaks} NoDisp={no_disp} DeepRet={deep_ret} NoM5={no_m5} NoEntry={no_entry}")
        
        if trades:
            for t in trades:
                icon = '🟢' if t['result'] == 'WIN' else '🔴'
                print(f"    {icon} {t['date']} {t['direction']:5s} {t['pips']:+6.1f}p | disp={t['disp_hour']}h rng={t['disp_rng']:.3f}/{t['avg_rng']:.3f} | breaks={t['breaks']}")
        print()
    
    # Summary
    print("═══ RANKING FINAL ═══")
    valid = {}
    for name in all_results:
        trades = [r for r in all_results[name] if r['result'] in ('WIN', 'LOSS')]
        if not trades:
            continue
        wr = round(sum(1 for r in trades if r['result'] == 'WIN') / len(trades) * 100, 1)
        pnl = sum(r.get('pips', 0) for r in trades)
        valid[name] = (wr, pnl, len(trades), '✅' if wr >= MIN_WR else '❌')
    
    for name, (wr, pnl, t, status) in sorted(valid.items(), key=lambda x: x[1][0], reverse=True):
        print(f"  {status} {name:8s} WR={wr}% PnL={pnl:+.1f}p Trades={t}")
    
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(all_results, indent=2, default=str))
    print(f"\n✅ Salvo em {OUTPUT}")
