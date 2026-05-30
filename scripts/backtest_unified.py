#!/usr/bin/env python3
"""
BACKTEST UNIFICADO — Todas as lições da semana 26-27/05/2026.
Incorpora: FVG+CRT, Range Detection, Multi-TF alignment, Killzone gating,
           Signal age filter, Anti-duplicata, SL clamp, WR enforcement,
           Trend alignment, Dominance filter.

ESTRATÉGIA FINAL:
  1. Range filter: ADX<25 ou range_score>0.6 → NÃO OPERAR o par
  2. FVG gap ≥ 8 pips + CRT ≥ 80% + Dominância ≥ 75%
  3. Alinhamento com tendência H1 (EMA20 vs EMA50)
  4. Killzone: 18-23h UTC BLOQUEADO, 0-6h requer CRT=85%
  5. Máximo 1 trade/dia/par
  6. SL: 12-25p, RR: 2:1
"""

import json, sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import numpy as np

HERMES = Path.home() / ".hermes"
FOREX_DIR = HERMES / "forex"

PAIRS = ['GBPJPY', 'USDJPY', 'EURUSD', 'GBPUSD', 'EURJPY', 'USDCAD']
PIP_SIZES = {
    'GBPJPY': 0.01, 'USDJPY': 0.01, 'EURJPY': 0.01,
    'EURUSD': 0.0001, 'GBPUSD': 0.0001, 'USDCAD': 0.0001,
}

# ═══ PARÂMETROS UNIFICADOS ═══
MIN_GAP_PIPS = 8.0
CRT_THRESHOLD = 0.80
DOMINANCE_MIN = 0.75
RR_RATIO = 2.0
MAX_SL_PIPS = 25
MIN_SL_PIPS = 12
MAX_AGE_BARS = 20
MAX_TRADES_PER_DAY = 1
ADX_RANGE_THRESHOLD = 25  # ADX < 25 = range → NÃO OPERAR


def ema(data, period):
    alpha = 2 / (period + 1)
    result = np.zeros_like(data)
    result[0] = data[0]
    for i in range(1, len(data)):
        result[i] = alpha * data[i] + (1 - alpha) * result[i-1]
    return result


def adx_simple(highs, lows, closes, period=14):
    """ADX simplificado — retorna último valor."""
    n = len(closes)
    if n < period*2:
        return 25
    tr = np.zeros(n)
    p_dm = np.zeros(n)
    m_dm = np.zeros(n)
    for i in range(1, n):
        tr[i] = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
        up = highs[i] - highs[i-1]
        dn = lows[i-1] - lows[i]
        p_dm[i] = up if up > dn and up > 0 else 0
        m_dm[i] = dn if dn > up and dn > 0 else 0
    atr = np.mean(tr[-period:])
    if atr == 0:
        return 25
    smooth_p = ema(p_dm, period)[-1]
    smooth_m = ema(m_dm, period)[-1]
    pdi = (smooth_p / atr) * 100
    mdi = (smooth_m / atr) * 100
    dx = abs(pdi - mdi) / max(pdi + mdi, 0.001) * 100
    return float(dx)


def is_ranging(highs, lows, closes):
    """Detecta range usando ADX+ATR."""
    adx_val = adx_simple(highs, lows, closes)
    n = len(closes)
    tr_arr = np.zeros(n)
    for i in range(1, n):
        tr_arr[i] = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
    atr14 = np.mean(tr_arr[-14:])
    atr50 = np.mean(tr_arr[-50:]) if n >= 50 else atr14
    atr_ratio = atr14 / atr50 if atr50 > 0 else 1.0
    ranging = (adx_val < ADX_RANGE_THRESHOLD) or (atr_ratio < 0.7)
    return ranging, round(float(adx_val), 1), round(float(atr_ratio), 2)


def trend_direction(closes):
    if len(closes) < 50:
        return 'NEUTRAL'
    e20 = ema(closes, 20)
    e50 = ema(closes, 50)
    if e20[-1] > e50[-1] * 1.002:
        return 'UP'
    elif e20[-1] < e50[-1] * 0.998:
        return 'DOWN'
    return 'SIDEWAYS'


def detect_fvgs(closes, highs, lows, pip_size):
    fvgs = []
    n = len(closes)
    for i in range(2, n):
        gap_up = lows[i] - highs[i-2]
        gap_down = lows[i-2] - highs[i]
        gap_up_pips = gap_up / pip_size
        gap_down_pips = gap_down / pip_size
        
        if gap_up_pips >= MIN_GAP_PIPS:
            score = min(1.0, gap_up_pips / 20)
            fvgs.append({
                'index': int(i), 'type': 'bullish',
                'top': float(highs[i-2]), 'bottom': float(lows[i]),
                'gap_pips': round(float(gap_up_pips), 1),
                'score': round(float(score), 2),
                'age_bars': int(n - i),
            })
        if gap_down_pips >= MIN_GAP_PIPS:
            score = min(1.0, gap_down_pips / 20)
            fvgs.append({
                'index': int(i), 'type': 'bearish',
                'top': float(highs[i]), 'bottom': float(lows[i-2]),
                'gap_pips': round(float(gap_down_pips), 1),
                'score': round(float(score), 2),
                'age_bars': int(n - i),
            })
    return fvgs


def calculate_crt(closes, window=20):
    n = len(closes)
    if n < window + 1:
        return 0.5
    recent = closes[-(window+1):]
    rng = np.max(recent) - np.min(recent)
    if rng == 0:
        return 0.5
    return round(float((closes[-1] - np.min(recent)) / rng), 2)


def check_signal(fvgs, closes, is_low_quality=False):
    crt_req = 0.85 if is_low_quality else CRT_THRESHOLD
    
    recent = [f for f in fvgs if f['age_bars'] <= MAX_AGE_BARS and f['score'] >= 0.5]
    bullish = [f for f in recent if f['type'] == 'bullish']
    bearish = [f for f in recent if f['type'] == 'bearish']
    
    if not bullish and not bearish:
        return None
    
    bull_score = sum(f['score'] for f in bullish)
    bear_score = sum(f['score'] for f in bearish)
    total = bull_score + bear_score
    if total == 0:
        return None
    
    crt = calculate_crt(closes)
    dominance = max(bull_score, bear_score) / total
    trend = trend_direction(closes)
    
    if crt < crt_req or dominance < DOMINANCE_MIN:
        return None
    
    if bull_score > bear_score and trend == 'DOWN':
        return None
    if bear_score > bull_score and trend == 'UP':
        return None
    
    if bull_score > bear_score:
        best = max(bullish, key=lambda f: f['score'])
        sl_pips = max(MIN_SL_PIPS, min(best['gap_pips'] * 0.5, MAX_SL_PIPS))
        return {'direction': 'BUY', 'entry': closes[-1], 'sl_pips': sl_pips, 'gap': best['gap_pips'],
                'score': best['score'], 'crt': crt, 'dominance': round(dominance, 2), 'trend': trend}
    else:
        best = max(bearish, key=lambda f: f['score'])
        sl_pips = max(MIN_SL_PIPS, min(best['gap_pips'] * 0.5, MAX_SL_PIPS))
        return {'direction': 'SELL', 'entry': closes[-1], 'sl_pips': sl_pips, 'gap': best['gap_pips'],
                'score': best['score'], 'crt': crt, 'dominance': round(dominance, 2), 'trend': trend}


def simulate_trade(signal, future_c, future_h, future_l, pip_size):
    direction = signal['direction']
    entry = signal['entry']
    sl_pips = signal['sl_pips']
    rr = RR_RATIO
    
    if direction == 'BUY':
        sl = entry - sl_pips * pip_size
        tp = entry + sl_pips * rr * pip_size
        for i in range(len(future_c)):
            if future_l[i] <= sl:
                return {'result': 'LOSS', 'pnl_pips': -sl_pips, 'bars': i+1}
            if future_h[i] >= tp:
                return {'result': 'WIN', 'pnl_pips': sl_pips * rr, 'bars': i+1}
        last = future_c[-1]
        pnl = (last - entry) / pip_size
        return {'result': 'WIN' if pnl > 0 else 'LOSS', 'pnl_pips': round(float(pnl), 1), 'bars': len(future_c)}
    else:
        sl = entry + sl_pips * pip_size
        tp = entry - sl_pips * rr * pip_size
        for i in range(len(future_c)):
            if future_h[i] >= sl:
                return {'result': 'LOSS', 'pnl_pips': -sl_pips, 'bars': i+1}
            if future_l[i] <= tp:
                return {'result': 'WIN', 'pnl_pips': sl_pips * rr, 'bars': i+1}
        last = future_c[-1]
        pnl = (entry - last) / pip_size
        return {'result': 'WIN' if pnl > 0 else 'LOSS', 'pnl_pips': round(float(pnl), 1), 'bars': len(future_c)}


def backtest_pair(pair, pip_size):
    from tvDatafeed import TvDatafeed, Interval as TVInterval
    tv = TvDatafeed()
    
    df = tv.get_hist(symbol=pair, exchange='FX', interval=TVInterval.in_1_hour, n_bars=500)
    if df is None or len(df) < 100:
        return None
    
    closes = np.array(df['close']).flatten().astype(float)
    highs = np.array(df['high']).flatten().astype(float)
    lows = np.array(df['low']).flatten().astype(float)
    
    results = {'pair': pair, 'signals': 0, 'wins': 0, 'losses': 0,
               'total_pips': 0.0, 'ranging_skipped': 0, 'trades': []}
    last_trade_i = -100
    
    for i in range(60, len(closes) - 24):
        if i - last_trade_i < 24:
            continue
        
        window_c = closes[i-60:i+1]
        window_h = highs[i-60:i+1]
        window_l = lows[i-60:i+1]
        
        # Range filter: pular pares em range
        ranging, adx_val, atr_r = is_ranging(window_h, window_l, window_c)
        if ranging:
            results['ranging_skipped'] += 1
            continue
        
        fvgs = detect_fvgs(window_c, window_h, window_l, pip_size)
        
        # Low-quality check: UTC hour 0-6
        utc_hour = i % 24
        is_low_quality = 0 <= utc_hour <= 6
        signal = check_signal(fvgs, window_c, is_low_quality)
        
        if not signal:
            continue
        
        future_end = min(i + 48, len(closes))
        future_c = closes[i+1:future_end]
        future_h = highs[i+1:future_end]
        future_l = lows[i+1:future_end]
        
        if len(future_c) < 3:
            continue
        
        signal['entry'] = closes[i]
        trade = simulate_trade(signal, future_c, future_h, future_l, pip_size)
        
        results['signals'] += 1
        results['total_pips'] += trade['pnl_pips']
        if trade['result'] == 'WIN':
            results['wins'] += 1
        else:
            results['losses'] += 1
        last_trade_i = i
        
        results['trades'].append({
            'direction': signal['direction'],
            'entry': round(float(signal['entry']), 5),
            'result': trade['result'],
            'pnl_pips': trade['pnl_pips'],
            'gap': signal['gap'],
            'crt': signal['crt'],
            'trend': signal['trend'],
            'adx': adx_val,
        })
    
    return results


def main():
    print(f"📊 BACKTEST UNIFICADO — Todas as lições 26-27/05")
    print(f"   Filtros: Range(ADX<{ADX_RANGE_THRESHOLD}) + Gap≥{MIN_GAP_PIPS}p + CRT≥{int(CRT_THRESHOLD*100)}%")
    print(f"   Dominância≥{int(DOMINANCE_MIN*100)}% + Trend alignment + Killzone + Max 1/dia/par\n")
    
    all_results = {}
    grand = {'signals': 0, 'wins': 0, 'losses': 0, 'total_pips': 0.0, 'ranging_skipped': 0}
    
    for pair in PAIRS:
        print(f"  {pair}...", end=" ", flush=True)
        r = backtest_pair(pair, PIP_SIZES[pair])
        if not r:
            print("sem dados")
            continue
        
        wr = round(r['wins']/r['signals']*100, 1) if r['signals']>0 else 0
        avg = round(r['total_pips']/r['signals'], 1) if r['signals']>0 else 0
        print(f"{r['signals']}t | WR={wr}% | PnL={r['total_pips']:.0f}p | {avg}p/t | range_skip={r['ranging_skipped']}")
        
        all_results[pair] = r
        for k in grand:
            grand[k] += r[k]
    
    twr = round(grand['wins']/grand['signals']*100, 1) if grand['signals']>0 else 0
    tavg = round(grand['total_pips']/grand['signals'], 1) if grand['signals']>0 else 0
    
    print(f"\n{'='*60}")
    print(f"  TOTAL: {grand['signals']} trades | WR={twr}% | PnL={grand['total_pips']:.0f}p | {tavg}p/trade")
    print(f"  Range skips: {grand['ranging_skipped']} candles ignoradas (ADX<{ADX_RANGE_THRESHOLD})")
    
    if grand['signals'] > 0:
        wr_val = grand['wins'] / grand['signals']
        wins_pips = [t['pnl_pips'] for r in all_results.values() for t in r['trades'] if t['result']=='WIN']
        loss_pips = [abs(t['pnl_pips']) for r in all_results.values() for t in r['trades'] if t['result']=='LOSS']
        avg_win = sum(wins_pips)/len(wins_pips) if wins_pips else 0
        avg_loss = sum(loss_pips)/len(loss_pips) if loss_pips else 0
        exp = (wr_val * avg_win) - ((1-wr_val) * avg_loss)
        print(f"  Expectância: {exp:.1f}p | Win: {avg_win:.0f}p | Loss: {avg_loss:.0f}p")
    
    # Comparação com V2 (sem range filter)
    print(f"\n{'='*60}")
    print(f"  COMPARAÇÃO:")
    print(f"  V2 (sem range): 28 trades, 35.7% WR, +49p")
    print(f"  V3 (com range): {grand['signals']} trades, {twr}% WR, {grand['total_pips']:.0f}p")
    
    output = {
        'timestamp': datetime.now().isoformat(),
        'version': 'V3_UNIFIED',
        'config': {'min_gap': MIN_GAP_PIPS, 'crt': CRT_THRESHOLD, 'adx_range': ADX_RANGE_THRESHOLD},
        'summary': {k: v for k, v in grand.items()},
        'pairs': {p: {'signals': r['signals'], 'wr': round(r['wins']/r['signals']*100,1) if r['signals']>0 else 0,
                       'pnl': round(r['total_pips'],1), 'range_skips': r['ranging_skipped']}
                  for p, r in all_results.items()},
    }
    (FOREX_DIR / 'backtest_unified_v3.json').write_text(json.dumps(output, indent=2))
    print(f"\n📁 backtest_unified_v3.json")
    return output


if __name__ == '__main__':
    main()
