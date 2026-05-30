#!/usr/bin/env python3
"""Multi-Strategy Backtest — All Pairs, All Knowledge
Testa FVG+CRT, Killzones, SMC Fractal, ICT, S/R em todos os pares.
Output: ~/.hermes/forex/multi_backtest_results.json
"""
import yfinance as yf, pandas as pd, numpy as np, json
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT = Path.home() / '.hermes' / 'forex' / 'multi_backtest_results.json'

PAIRS = {
    'EURJPY': ('EURJPY=X', 0.01),
    'USDJPY': ('USDJPY=X', 0.01),
    'GBPUSD': ('GBPUSD=X', 0.0001),
    'EURUSD': ('EURUSD=X', 0.0001),
    'USDCAD': ('USDCAD=X', 0.0001),
}

def flatten(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

# ══════════════════════════════════════
# STRATEGY 1: FVG + CRT (M15)
# ══════════════════════════════════════
def test_fvg_crt(sym, pip, days=14):
    """FVG + CRT no M15."""
    end = datetime.now()
    start = end - timedelta(days=days)
    df = flatten(yf.download(sym, start=start, end=end, interval='15m', progress=False))
    if len(df) < 60: return None
    
    h, l, c = df['High'].values.astype(float), df['Low'].values.astype(float), df['Close'].values.astype(float)
    n = len(h)
    results = []
    
    for i in range(20, n-4):
        # FVG detection
        for gap_dir, gap_idx in [(1, 2), (-1, 2)]:
            j = i - gap_idx
            if gap_dir > 0:  # Bullish FVG
                if j+1 < n and l[j+1] > h[j]:
                    gap = (l[j+1] - h[j]) / pip
                    if gap < 3: continue  # min 3 pips
                    
                    # CRT filter
                    rng = abs(h[i] - l[i])
                    recent = [abs(h[k]-l[k]) for k in range(max(0,i-20), i)]
                    is_crt = rng >= sorted(recent)[int(len(recent)*0.8)] if recent else False
                    
                    if is_crt:
                        sl_pips = min(max(gap, 3), 10)
                        entry = l[j+1]
                        tp = entry + sl_pips * 3 * pip
                        sl = entry - sl_pips * pip
                        
                        for k in range(i+1, min(i+12, n)):
                            hk, lk = float(df.iloc[k]['High']), float(df.iloc[k]['Low'])
                            if hk >= tp: results.append(('WIN', sl_pips*3)); break
                            if lk <= sl: results.append(('LOSS', -sl_pips)); break
                        else:
                            results.append(('OPEN', 0))
    
    return results

# ══════════════════════════════════════
# STRATEGY 2: Killzones (London Close)
# ══════════════════════════════════════
def test_killzone(sym, pip, days=14):
    """FVG durante London Close (15-16 UTC)."""
    end = datetime.now()
    start = end - timedelta(days=days)
    df = flatten(yf.download(sym, start=start, end=end, interval='15m', progress=False))
    if len(df) < 60: return None
    
    df['hour'] = df.index.hour
    df_lc = df[df['hour'].isin([15,16])]
    if len(df_lc) < 10: return None
    
    h, l, c = df_lc['High'].values.astype(float), df_lc['Low'].values.astype(float), df_lc['Close'].values.astype(float)
    n = len(h)
    results = []
    
    for i in range(2, n-4):
        for gap_dir in [1, -1]:
            j = i - 2
            if gap_dir > 0:
                if j+1 < n and l[j+1] > h[j]:
                    gap = (l[j+1] - h[j]) / pip
                    if gap < 2: continue
                    tp = l[j+1] + gap * 3 * pip
                    sl = l[j+1] - gap * pip
                    for k in range(i+1, min(i+8, n)):
                        hk, lk = float(df_lc.iloc[k]['High']), float(df_lc.iloc[k]['Low'])
                        if hk >= tp: results.append(('WIN', gap*3)); break
                        if lk <= sl: results.append(('LOSS', -gap)); break
                    else:
                        results.append(('OPEN', 0))
    
    return results

# ══════════════════════════════════════
# STRATEGY 3: SMC Fractal (Pivôs 5+1)
# ══════════════════════════════════════
def test_smc_fractal(sym, pip, days=14):
    """MSS + OB no H1."""
    end = datetime.now()
    start = end - timedelta(days=days)
    df = flatten(yf.download(sym, start=start, end=end, interval='1h', progress=False))
    if len(df) < 30: return None
    
    h, l, c = df['High'].values.astype(float), df['Low'].values.astype(float), df['Close'].values.astype(float)
    n = len(h)
    results = []
    
    for i in range(10, n-4):
        # Bullish MSS
        if l[i] < l[i-1] and l[i] < l[i-2] and l[i] < l[i-3]:
            for j in range(i+1, min(i+8, n-1)):
                if c[j] > h[i-1]:
                    entry = c[j]
                    sl = l[i]
                    sl_pips = (entry - sl) / pip
                    if sl_pips <= 0 or sl_pips > 15: break
                    tp = entry + sl_pips * 2 * pip
                    for k in range(j+1, min(j+12, n)):
                        hk, lk = float(df.iloc[k]['High']), float(df.iloc[k]['Low'])
                        if hk >= tp: results.append(('WIN', sl_pips*2)); break
                        if lk <= sl: results.append(('LOSS', -sl_pips)); break
                    else:
                        results.append(('OPEN', 0))
                    break
    
    return results

# ══════════════════════════════════════
# STRATEGY 4: S/R + FVG (Support/Resistance)
# ══════════════════════════════════════
def test_sr_fvg(sym, pip, days=14):
    """FVG próximo a swing high/low anterior."""
    end = datetime.now()
    start = end - timedelta(days=days)
    df = flatten(yf.download(sym, start=start, end=end, interval='15m', progress=False))
    if len(df) < 60: return None
    
    h, l, c = df['High'].values.astype(float), df['Low'].values.astype(float), df['Close'].values.astype(float)
    n = len(h)
    results = []
    
    # Find swing highs/lows
    swings_h, swings_l = [], []
    for i in range(3, n-3):
        if h[i] > h[i-1] and h[i] > h[i-2] and h[i] > h[i+1] and h[i] > h[i+2]:
            swings_h.append((i, h[i]))
        if l[i] < l[i-1] and l[i] < l[i-2] and l[i] < l[i+1] and l[i] < l[i+2]:
            swings_l.append((i, l[i]))
    
    for i in range(5, n-4):
        for gap_dir in [1, -1]:
            j = i - 2
            if gap_dir > 0:
                if j+1 < n and l[j+1] > h[j]:
                    gap = (l[j+1] - h[j]) / pip
                    if gap < 3: continue
                    # Check proximity to swing low
                    near_swing = any(abs(l[j+1] - sw) / pip <= 5 for _, sw in swings_l[-5:])
                    if not near_swing: continue
                    
                    sl_pips = gap
                    entry = l[j+1]
                    tp = entry + sl_pips * 3 * pip
                    sl = entry - sl_pips * pip
                    for k in range(i+1, min(i+12, n)):
                        hk, lk = float(df.iloc[k]['High']), float(df.iloc[k]['Low'])
                        if hk >= tp: results.append(('WIN', sl_pips*3)); break
                        if lk <= sl: results.append(('LOSS', -sl_pips)); break
                    else:
                        results.append(('OPEN', 0))
    
    return results


if __name__ == '__main__':
    print("🔬 Multi-Strategy Backtest — 5 Pares, 4 Estratégias\n")
    
    strategies = {
        'FVG+CRT M15': test_fvg_crt,
        'Killzone LC': test_killzone,
        'SMC Fractal H1': test_smc_fractal,
        'S/R+FVG M15': test_sr_fvg,
    }
    
    all_data = {}
    
    for name, (sym, pip) in PAIRS.items():
        print(f"## {name}")
        pair_data = {}
        
        for strat_name, strat_fn in strategies.items():
            try:
                results = strat_fn(sym, pip)
                if not results:
                    print(f"  {strat_name:20s}: NO DATA")
                    continue
                
                wins = sum(1 for r in results if r[0] == 'WIN')
                losses = sum(1 for r in results if r[0] == 'LOSS')
                opens = sum(1 for r in results if r[0] == 'OPEN')
                total = wins + losses
                wr = round(wins/total*100, 1) if total > 0 else 0
                pnl = sum(r[1] for r in results if r[0] in ('WIN','LOSS'))
                
                status = '✅' if wr >= 40 else '❌'
                
                pair_data[strat_name] = {
                    'trades': total, 'wins': wins, 'losses': losses, 'wr': wr, 'pnl': round(pnl, 1)
                }
                
                print(f"  {status} {strat_name:20s}: {wins}W/{losses}L WR={wr}% PnL={pnl:+.1f}p (open={opens})")
            except Exception as e:
                print(f"  ❌ {strat_name:20s}: ERROR {e}")
        
        all_data[name] = pair_data
        print()
    
    # Best strategy per pair
    print("═══ MELHOR ESTRATÉGIA POR PAR ═══")
    for name in PAIRS:
        if name not in all_data or not all_data[name]: continue
        best = max(all_data[name].items(), key=lambda x: x[1]['pnl'])
        print(f"  {name:8s}: {best[0]:20s} WR={best[1]['wr']}% PnL={best[1]['pnl']:+.1f}p")
    
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(all_data, indent=2))
    print(f"\n✅ {OUTPUT}")
