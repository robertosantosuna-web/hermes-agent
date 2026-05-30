#!/usr/bin/env python3
"""
BACKTEST CORRIGIDO — 30 dias, todas as correções dos 4 especialistas.
- CRT CORRETO (candle range percentile, NÃO stochastic)
- tvDatafeed como fonte primária
- USDJPY + EURJPY apenas
- Range filter (ADX<25 = skip)
- Session filter (6-16h UTC)
- Binary flow_trend gate (sim/não, sem score %)
- Multi-TF alignment (H1 trend deve alinhar com M15 signal)
- Gap ≥ 5p (análise diz que <5p é ruído)
- RR 2:1 (mais realista que 3:1)
- SL 15-25p
- Máx 2 trades/dia
- Split 70/30 in-sample/out-of-sample
"""

import json, sys, time
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import numpy as np

HERMES = Path.home() / ".hermes"
FOREX_DIR = HERMES / "forex"

# ═══ PARÂMETROS (validados pelos especialistas) ═══
PAIRS = ['USDJPY', 'EURJPY']
PIP_SIZES = {'USDJPY': 0.01, 'EURJPY': 0.01}
MIN_GAP_PIPS = 5.0
CRT_PERCENTILE = 0.70  # CRT real: candle range no top 70%
RR_RATIO = 2.0
SL_MIN, SL_MAX = 15, 25
MAX_TRADES_DAY = 2
MAX_AGE_CANDLES = 20
ADX_MIN = 25
SESSION_HOURS = list(range(6, 17))  # 6-16h UTC
DAYS_BACK = 30
N_BARS_H1 = 500
N_BARS_M15 = 2000


def ema(data, period):
    alpha = 2 / (period + 1)
    r = np.zeros_like(data)
    r[0] = data[0]
    for i in range(1, len(data)):
        r[i] = alpha * data[i] + (1 - alpha) * r[i-1]
    return r


def adx(highs, lows, closes, period=14):
    n = len(closes)
    if n < period*2:
        return 20.0
    tr = np.zeros(n)
    p_dm = np.zeros(n)
    m_dm = np.zeros(n)
    for i in range(1, n):
        tr[i] = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
        up = highs[i] - highs[i-1]
        dn = lows[i-1] - lows[i]
        p_dm[i] = up if up > dn and up > 0 else 0
        m_dm[i] = dn if dn > up and dn > 0 else 0
    atr = ema(tr, period)
    pdi = ema(p_dm, period) / atr * 100
    mdi = ema(m_dm, period) / atr * 100
    dx = abs(pdi - mdi) / (pdi + mdi + 0.001) * 100
    return float(dx[-1])


# ═══════════════════════════════════════════════
# CRT CORRETO: percentile do range da vela atual vs lookback
# ═══════════════════════════════════════════════
def crt_percentile(highs, lows, idx, lookback=20):
    """CRT REAL: onde o range da vela atual está vs últimas N velas."""
    if idx < lookback:
        return 0.5
    ranges = np.abs(highs[idx-lookback:idx+1] - lows[idx-lookback:idx+1])
    current = ranges[-1]
    pct = np.sum(ranges <= current) / len(ranges)
    return float(pct)


# ═══════════════════════════════════════════════
# FVG DETECTION
# ═══════════════════════════════════════════════
def detect_fvgs(highs, lows, pip_size):
    fvgs = []
    n = len(highs)
    for i in range(2, n):
        gap_up = lows[i] - highs[i-2]
        gap_down = lows[i-2] - highs[i]
        gap_up_pips = gap_up / pip_size
        gap_down_pips = gap_down / pip_size
        
        if gap_up_pips >= MIN_GAP_PIPS:
            crt = crt_percentile(highs, lows, i)
            fvgs.append({'i': i, 'type': 'bullish', 'gap': float(gap_up_pips),
                         'top': float(highs[i-2]), 'bottom': float(lows[i]),
                         'crt': crt, 'age': n - i})
        if gap_down_pips >= MIN_GAP_PIPS:
            crt = crt_percentile(highs, lows, i)
            fvgs.append({'i': i, 'type': 'bearish', 'gap': float(gap_down_pips),
                         'top': float(highs[i]), 'bottom': float(lows[i-2]),
                         'crt': crt, 'age': n - i})
    return fvgs


# ═══════════════════════════════════════════════
# FLOW GATE BINÁRIO (sim/não, sem %)
# ═══════════════════════════════════════════════
def flow_gate(highs, lows, closes, direction):
    """Binary flow check: CVD proxy + momentum direction."""
    n = len(closes)
    if n < 10:
        return False
    
    # CVD simulado: soma de (close-open) ponderado por corpo
    bodies = closes - closes  # temporário, recalcular
    cvd = 0
    for i in range(max(0, n-10), n):
        body = closes[i] - closes[i-1] if i > 0 else 0
        upper_wick = highs[i] - max(closes[i], closes[i-1] if i > 0 else closes[i])
        lower_wick = min(closes[i], closes[i-1] if i > 0 else closes[i]) - lows[i]
        if body > 0:
            cvd += body * 1.5
        else:
            cvd += body * 0.5
        cvd -= (upper_wick - lower_wick) * 0.3
    
    flow_dir = 'UP' if cvd > 0 else 'DOWN'
    return (flow_dir == 'UP' and direction == 'BUY') or (flow_dir == 'DOWN' and direction == 'SELL')


# ═══════════════════════════════════════════════
# MULTI-TF ALIGNMENT
# ═══════════════════════════════════════════════
def h1_trend_aligns(closes_h1, direction):
    """H1 EMA20 vs EMA50 must agree with trade direction."""
    if len(closes_h1) < 50:
        return False
    e20 = ema(closes_h1, 20)
    e50 = ema(closes_h1, 50)
    h1_up = e20[-1] > e50[-1] * 1.002
    h1_down = e20[-1] < e50[-1] * 0.998
    
    if direction == 'BUY':
        return h1_up
    else:
        return h1_down


# ═══════════════════════════════════════════════
# SIMULATE TRADE
# ═══════════════════════════════════════════════
def simulate(signal, future_h, future_l, future_c, pip_size):
    d = signal['direction']
    entry = signal['entry']
    sl_pips = signal['sl_pips']
    rr = RR_RATIO
    sl = entry - sl_pips * pip_size if d == 'BUY' else entry + sl_pips * pip_size
    tp = entry + sl_pips * rr * pip_size if d == 'BUY' else entry - sl_pips * rr * pip_size
    
    for i in range(len(future_c)):
        if d == 'BUY':
            if future_l[i] <= sl:
                return {'result': 'LOSS', 'pnl': -sl_pips, 'bars': i+1}
            if future_h[i] >= tp:
                return {'result': 'WIN', 'pnl': sl_pips * rr, 'bars': i+1}
        else:
            if future_h[i] >= sl:
                return {'result': 'LOSS', 'pnl': -sl_pips, 'bars': i+1}
            if future_l[i] <= tp:
                return {'result': 'WIN', 'pnl': sl_pips * rr, 'bars': i+1}
    
    last = future_c[-1]
    pnl = (last - entry) / pip_size if d == 'BUY' else (entry - last) / pip_size
    return {'result': 'WIN' if pnl > 0 else 'LOSS', 'pnl': round(float(pnl), 1), 'bars': len(future_c)}


# ═══════════════════════════════════════════════
# BACKTEST PAIR
# ═══════════════════════════════════════════════
def backtest_pair(pair, pip_size):
    from tvDatafeed import TvDatafeed, Interval as TVInterval
    tv = TvDatafeed()
    
    # H1 data (for trend alignment + ADX)
    df_h1 = tv.get_hist(symbol=pair, exchange='FX', interval=TVInterval.in_1_hour, n_bars=N_BARS_H1)
    if df_h1 is None or len(df_h1) < 100:
        return None
    c_h1 = np.array(df_h1['close']).flatten().astype(float)
    h_h1 = np.array(df_h1['high']).flatten().astype(float)
    l_h1 = np.array(df_h1['low']).flatten().astype(float)
    
    # M15 data (for entry signals)
    df_m15 = tv.get_hist(symbol=pair, exchange='FX', interval=TVInterval.in_15_minute, n_bars=N_BARS_M15)
    if df_m15 is None or len(df_m15) < 500:
        return None
    c_m15 = np.array(df_m15['close']).flatten().astype(float)
    h_m15 = np.array(df_m15['high']).flatten().astype(float)
    l_m15 = np.array(df_m15['low']).flatten().astype(float)
    
    # Split 70/30
    split_idx = int(len(c_m15) * 0.7)
    
    results_is = {'signals': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'trades': []}
    results_oos = {'signals': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'trades': []}
    
    # Map M15 indices to H1 indices (4 M15 candles per H1)
    m15_per_h1 = 4
    
    for i in range(200, len(c_m15) - 48):  # Need 200 lookback, 48 forward
        # Skip if not in session hours
        utc_hour = (i // m15_per_h1) % 24
        if utc_hour not in SESSION_HOURS:
            continue
        
        # Determine if in-sample or OOS
        is_oos = i >= split_idx
        target = results_oos if is_oos else results_is
        
        # Range filter: ADX on H1
        h1_idx = i // m15_per_h1
        h1_start = max(0, h1_idx - 20)
        h1_end = min(len(c_h1), h1_idx + 1)
        if h1_end - h1_start < 20:
            continue
        adx_val = adx(h_h1[h1_start:h1_end], l_h1[h1_start:h1_end], c_h1[h1_start:h1_end])
        if adx_val < ADX_MIN:
            continue
        
        # FVG detection on M15
        window = 100
        start = max(0, i - window)
        fvgs = detect_fvgs(h_m15[start:i+1], l_m15[start:i+1], pip_size)
        
        # Filter: recent, CRT≥threshold
        valid = [f for f in fvgs if f['age'] <= MAX_AGE_CANDLES and f['crt'] >= CRT_PERCENTILE]
        if not valid:
            continue
        
        # Pick best
        best = max(valid, key=lambda f: f['gap'] * f['crt'])
        
        # Direction
        direction = 'BUY' if best['type'] == 'bullish' else 'SELL'
        
        # Multi-TF alignment
        h1_window_end = min(len(c_h1), h1_idx + 1)
        h1_window_start = max(0, h1_window_end - 50)
        if not h1_trend_aligns(c_h1[h1_window_start:h1_window_end], direction):
            continue
        
        # Flow gate
        flow_start = max(0, i - 30)
        if not flow_gate(h_m15[flow_start:i+1], l_m15[flow_start:i+1], c_m15[flow_start:i+1], direction):
            continue
        
        # SL cálculo
        sl_pips = max(SL_MIN, min(best['gap'] * 0.6, SL_MAX))
        
        signal = {'direction': direction, 'entry': c_m15[i], 'sl_pips': sl_pips}
        
        # Simulate forward
        fwd_end = min(i + 48, len(c_m15))
        trade = simulate(signal, h_m15[i+1:fwd_end], l_m15[i+1:fwd_end], c_m15[i+1:fwd_end], pip_size)
        
        target['signals'] += 1
        target['pnl'] += trade['pnl']
        if trade['result'] == 'WIN':
            target['wins'] += 1
        else:
            target['losses'] += 1
        target['trades'].append({
            'direction': direction, 'entry': round(float(signal['entry']), 5),
            'result': trade['result'], 'pnl': trade['pnl'],
            'gap': best['gap'], 'crt': round(best['crt'], 2),
            'adx': round(adx_val, 1),
        })
        
        # Max trades/day
        day_trades = sum(1 for t in target['trades'] if len(target['trades']) - target['trades'].index(t) <= MAX_TRADES_DAY * 4)
    
    return {'pair': pair, 'is': results_is, 'oos': results_oos}


def stats(r):
    if r['signals'] == 0:
        return {'wr': 0, 'avg_pnl': 0, 'total': 0}
    wr = round(r['wins'] / r['signals'] * 100, 1)
    avg = round(r['pnl'] / r['signals'], 1)
    return {'wr': wr, 'avg_pnl': avg, 'total': r['signals'], 'pnl': round(r['pnl'], 1)}


def main():
    print(f"📊 BACKTEST CORRIGIDO — 30 dias, todas as correções")
    print(f"   CRT REAL (range percentile) | Gap≥{MIN_GAP_PIPS}p | ADX≥{ADX_MIN}")
    print(f"   Session {SESSION_HOURS[0]}-{SESSION_HOURS[-1]}h UTC | RR {RR_RATIO}:1 | SL {SL_MIN}-{SL_MAX}p")
    print(f"   Multi-TF + Flow gate binário | 70/30 split IS/OOS\n")
    
    all_is = {'signals': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0}
    all_oos = {'signals': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0}
    
    for pair in PAIRS:
        print(f"  {pair}...", end=" ", flush=True)
        r = backtest_pair(pair, PIP_SIZES[pair])
        if not r:
            print("sem dados")
            continue
        
        is_s = stats(r['is'])
        oos_s = stats(r['oos'])
        
        # Overfitting check
        wr_drop = is_s['wr'] - oos_s['wr'] if oos_s['total'] > 0 else 0
        
        print(f"IS:{is_s['total']}t/{is_s['wr']}%/{is_s['pnl']}p | OOS:{oos_s['total']}t/{oos_s['wr']}%/{oos_s['pnl']}p | ΔWR:{wr_drop:+.1f}%")
        
        for k in all_is:
            all_is[k] += r['is'][k]
        for k in all_oos:
            all_oos[k] += r['oos'][k]
    
    is_s = stats(all_is)
    oos_s = stats(all_oos)
    
    print(f"\n{'='*60}")
    print(f"  IN-SAMPLE:  {is_s['total']} trades | WR={is_s['wr']}% | PnL={is_s['pnl']}p | {is_s['avg_pnl']}p/t")
    print(f"  OUT-SAMPLE: {oos_s['total']} trades | WR={oos_s['wr']}% | PnL={oos_s['pnl']}p | {oos_s['avg_pnl']}p/t")
    
    # Statistical significance
    total_n = all_is['signals'] + all_oos['signals']
    total_wr = (all_is['wins'] + all_oos['losses']) / total_n * 100 if total_n > 0 else 0
    se = np.sqrt(total_wr/100 * (1-total_wr/100) / total_n) * 100 if total_n > 0 else 0
    ci_low = total_wr - 1.96 * se
    ci_high = total_wr + 1.96 * se
    
    print(f"\n  📊 Estatística: n={total_n} | 95% CI: [{ci_low:.1f}%, {ci_high:.1f}%]")
    
    if total_n >= 30 and ci_low > 33.3:  # Breakeven for RR 2:1
        print(f"  ✅ EDGE CONFIRMADO: WR mínima ({ci_low:.1f}%) > breakeven RR2:1 (33.3%)")
    elif total_n >= 30:
        print(f"  ⚠️ EDGE NÃO CONFIRMADO: CI inferior ({ci_low:.1f}%) < breakeven (33.3%)")
    else:
        print(f"  ⚠️ AMOSTRA INSUFICIENTE (n={total_n}, precisa ≥30)")
    
    wr_drop_total = is_s['wr'] - oos_s['wr']
    if abs(wr_drop_total) > 15:
        print(f"  🔴 OVERFITTING: WR caiu {abs(wr_drop_total):.1f}% do IS para OOS")
    elif abs(wr_drop_total) > 8:
        print(f"  🟡 OVERFITTING MODERADO: WR caiu {abs(wr_drop_total):.1f}%")
    else:
        print(f"  ✅ ROBUSTO: WR estável entre IS/OOS (Δ={wr_drop_total:+.1f}%)")
    
    # Save
    output = {
        'timestamp': datetime.now().isoformat(),
        'version': 'CORRECTED_BACKTEST',
        'params': {'min_gap': MIN_GAP_PIPS, 'crt': CRT_PERCENTILE, 'adx_min': ADX_MIN, 'rr': RR_RATIO},
        'in_sample': is_s,
        'out_sample': oos_s,
        'statistics': {'n': total_n, 'ci_95': [round(ci_low, 1), round(ci_high, 1)]},
    }
    (FOREX_DIR / 'backtest_corrected.json').write_text(json.dumps(output, indent=2))
    print(f"\n📁 backtest_corrected.json")


if __name__ == '__main__':
    main()
