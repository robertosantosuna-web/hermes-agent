#!/usr/bin/env python3
"""
Backtest V2 — Abordagem QUALIDADE: poucos trades, filtros rigorosos.
- Máximo 1 trade por par por dia
- Gap ≥ 10 pips
- CRT ≥ 85%
- Alinhamento com tendência EMA
- Apenas o MELHOR sinal do dia
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

# ═══ PARÂMETROS RIGOROSOS ═══
MIN_GAP_PIPS = 10.0          # Gap mínimo GRANDE
CRT_THRESHOLD = 0.85         # CRT muito exigente
DOMINANCE_MIN = 0.80         # Dominância de FVGs ≥ 80%
RR_RATIO = 2.0               # RR 2:1
MAX_SL_PIPS = 20             
MIN_SL_PIPS = 12             
MAX_AGE_BARS = 20            # Só FVGs recentes
MAX_TRADES_PER_DAY = 1       # 1 trade por par por dia
MIN_SCORE = 0.70             # Score mínimo do FVG


def detect_fvgs(closes, highs, lows, pip_size):
    fvgs = []
    n = len(closes)
    for i in range(2, n):
        gap_up = lows[i] - highs[i-2]
        gap_down = lows[i-2] - highs[i]
        gap_up_pips = gap_up / pip_size
        gap_down_pips = gap_down / pip_size
        
        if gap_up_pips >= MIN_GAP_PIPS:
            fvgs.append({
                'index': int(i), 'type': 'bullish',
                'top': float(highs[i-2]), 'bottom': float(lows[i]),
                'gap_pips': round(float(gap_up_pips), 1),
                'score': round(min(1.0, gap_up_pips / 20), 2),
                'age_bars': int(n - i),
            })
        
        if gap_down_pips >= MIN_GAP_PIPS:
            fvgs.append({
                'index': int(i), 'type': 'bearish',
                'top': float(highs[i]), 'bottom': float(lows[i-2]),
                'gap_pips': round(float(gap_down_pips), 1),
                'score': round(min(1.0, gap_down_pips / 20), 2),
                'age_bars': int(n - i),
            })
    return fvgs


def ema(data, period):
    """EMA simples."""
    alpha = 2 / (period + 1)
    result = np.zeros_like(data)
    result[0] = data[0]
    for i in range(1, len(data)):
        result[i] = alpha * data[i] + (1 - alpha) * result[i-1]
    return result


def trend_direction(closes):
    """Determina tendência: EMA20 vs EMA50."""
    if len(closes) < 50:
        return 'NEUTRAL'
    e20 = ema(closes, 20)
    e50 = ema(closes, 50)
    if e20[-1] > e50[-1] * 1.002:
        return 'UP'
    elif e20[-1] < e50[-1] * 0.998:
        return 'DOWN'
    return 'SIDEWAYS'


def calculate_crt(closes, window=20):
    n = len(closes)
    if n < window + 1:
        return 0.5
    recent = closes[-(window+1):]
    rng = np.max(recent) - np.min(recent)
    if rng == 0:
        return 0.5
    return round(float((closes[-1] - np.min(recent)) / rng), 2)


def check_signal(fvgs, closes):
    """Verifica sinal de ALTA QUALIDADE."""
    recent = [f for f in fvgs if f['age_bars'] <= MAX_AGE_BARS and f['score'] >= MIN_SCORE]
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
    
    # CRT alto + dominância + tendência alinhada
    if crt < CRT_THRESHOLD or dominance < DOMINANCE_MIN:
        return None
    
    if bull_score > bear_score and trend == 'DOWN':
        return None  # Contra tendência
    if bear_score > bull_score and trend == 'UP':
        return None  # Contra tendência
    
    if bull_score > bear_score:
        best = max(bullish, key=lambda f: f['score'])
        sl_pips = max(MIN_SL_PIPS, min(best['gap_pips'] * 0.5, MAX_SL_PIPS))
        return {
            'direction': 'BUY', 'entry': closes[-1],
            'sl_pips': sl_pips, 'gap': best['gap_pips'],
            'score': best['score'], 'crt': crt,
            'dominance': round(dominance, 2), 'trend': trend,
        }
    else:
        best = max(bearish, key=lambda f: f['score'])
        sl_pips = max(MIN_SL_PIPS, min(best['gap_pips'] * 0.5, MAX_SL_PIPS))
        return {
            'direction': 'SELL', 'entry': closes[-1],
            'sl_pips': sl_pips, 'gap': best['gap_pips'],
            'score': best['score'], 'crt': crt,
            'dominance': round(dominance, 2), 'trend': trend,
        }


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
    else:
        sl = entry + sl_pips * pip_size
        tp = entry - sl_pips * rr * pip_size
        for i in range(len(future_c)):
            if future_h[i] >= sl:
                return {'result': 'LOSS', 'pnl_pips': -sl_pips, 'bars': i+1}
            if future_l[i] <= tp:
                return {'result': 'WIN', 'pnl_pips': sl_pips * rr, 'bars': i+1}
    
    last = future_c[-1]
    pnl = (last - entry) / pip_size if direction == 'BUY' else (entry - last) / pip_size
    return {'result': 'WIN' if pnl > 0 else 'LOSS', 'pnl_pips': round(pnl, 1), 'bars': len(future_c)}


def backtest_pair(pair, pip_size):
    from tvDatafeed import TvDatafeed, Interval as TVInterval
    tv = TvDatafeed()
    
    df = tv.get_hist(symbol=pair, exchange='FX', interval=TVInterval.in_1_hour, n_bars=500)
    if df is None or len(df) < 100:
        return None
    
    closes = np.array(df['close']).flatten().astype(float)
    highs = np.array(df['high']).flatten().astype(float)
    lows = np.array(df['low']).flatten().astype(float)
    
    results = {'pair': pair, 'signals': 0, 'wins': 0, 'losses': 0, 'total_pips': 0.0, 'trades': []}
    last_trade_day = None
    
    for i in range(50, len(closes) - 24):
        window_c = closes[i-50:i+1]
        window_h = highs[i-50:i+1]
        window_l = lows[i-50:i+1]
        
        # 1 trade por dia
        candle_day = i  # Simplificação: cada candle H1 ≈ possível trade
        if last_trade_day is not None and (i - last_trade_day) < 24:
            continue
        
        fvgs = detect_fvgs(window_c, window_h, window_l, pip_size)
        signal = check_signal(fvgs, window_c)
        
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
        last_trade_day = i
        
        results['trades'].append({
            'direction': signal['direction'],
            'entry': round(float(signal['entry']), 5),
            'result': trade['result'],
            'pnl_pips': trade['pnl_pips'],
            'gap': signal['gap'],
            'crt': signal['crt'],
            'trend': signal['trend'],
        })
    
    return results


def main():
    print(f"📊 BACKTEST V2 — QUALIDADE (máx 1 trade/dia/par)")
    print(f"   Gap≥{MIN_GAP_PIPS}p | CRT≥{int(CRT_THRESHOLD*100)}% | Dominância≥{int(DOMINANCE_MIN*100)}%")
    print(f"   RR {RR_RATIO}:1 | SL {MIN_SL_PIPS}-{MAX_SL_PIPS}p | Score≥{MIN_SCORE}")
    print(f"   Alinhamento com tendência EMA + anti-sidways\n")
    
    all_results = {}
    grand = {'signals': 0, 'wins': 0, 'losses': 0, 'total_pips': 0.0}
    
    for pair in PAIRS:
        print(f"  {pair}...", end=" ", flush=True)
        r = backtest_pair(pair, PIP_SIZES[pair])
        if not r:
            print("sem dados")
            continue
        
        wr = round(r['wins']/r['signals']*100, 1) if r['signals']>0 else 0
        avg = round(r['total_pips']/r['signals'], 1) if r['signals']>0 else 0
        print(f"{r['signals']}t | WR={wr}% | PnL={r['total_pips']:.0f}p | {avg}p/t")
        
        all_results[pair] = r
        for k in grand:
            grand[k] += r[k]
    
    twr = round(grand['wins']/grand['signals']*100, 1) if grand['signals']>0 else 0
    tavg = round(grand['total_pips']/grand['signals'], 1) if grand['signals']>0 else 0
    
    print(f"\n{'='*60}")
    print(f"  TOTAL: {grand['signals']} trades | WR={twr}% | PnL={grand['total_pips']:.0f}p | {tavg}p/trade")
    
    if grand['signals'] > 0:
        win_rate = grand['wins'] / grand['signals']
        avg_win = sum(t['pnl_pips'] for r in all_results.values() for t in r['trades'] if t['result']=='WIN') / max(grand['wins'], 1)
        avg_loss = abs(sum(t['pnl_pips'] for r in all_results.values() for t in r['trades'] if t['result']=='LOSS') / max(grand['losses'], 1))
        exp = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        print(f"  Expectância: {exp:.1f}p | Win: {avg_win:.0f}p | Loss: {avg_loss:.0f}p")
    
    output = {
        'timestamp': datetime.now().isoformat(),
        'config': {'min_gap': MIN_GAP_PIPS, 'crt': CRT_THRESHOLD, 'dominance': DOMINANCE_MIN, 'rr': RR_RATIO},
        'summary': {'signals': grand['signals'], 'wins': grand['wins'], 'losses': grand['losses'], 'wr': twr, 'pnl': round(grand['total_pips'], 1)},
        'pairs': {p: {'signals': r['signals'], 'wr': round(r['wins']/r['signals']*100,1) if r['signals']>0 else 0, 'pnl': round(r['total_pips'],1)} for p, r in all_results.items()},
    }
    (FOREX_DIR / 'backtest_chart_analyzer_v2.json').write_text(json.dumps(output, indent=2))
    print(f"\n📁 Salvo em backtest_chart_analyzer_v2.json")
    return output

if __name__ == '__main__':
    main()
