#!/usr/bin/env python3
"""
Backtest do Chart Analyzer — Multi-Timeframe FVG+CRT.
Testa a estratégia em 30 dias de dados históricos do TradingView.

Uso: python3 backtest_chart_analyzer.py
"""

import json, sys, os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

HERMES = Path.home() / ".hermes"
FOREX_DIR = HERMES / "forex"

# ═══ CONFIG ═══
PAIRS = ['GBPJPY', 'USDJPY', 'EURUSD', 'GBPUSD', 'EURJPY', 'USDCAD']
TIMEFRAMES = ['15m', '30m', '1h']
TF_MAP = {'15m': 'M15', '30m': 'M30', '1h': 'H1'}
PIP_SIZES = {
    'GBPJPY': 0.01, 'USDJPY': 0.01, 'EURJPY': 0.01,
    'EURUSD': 0.0001, 'GBPUSD': 0.0001, 'USDCAD': 0.0001,
}
MIN_GAP_PIPS = 5.0              # Gap mínimo mais restrito (era 2.0)
CRT_THRESHOLD = 0.80           # CRT mais exigente (era 0.70)
RR_RATIO = 1.5                 # RR mais conservador (era 2.0)
MAX_SL_PIPS = 25               # SL máximo menor (era 30)
MIN_SL_PIPS = 12               # SL mínimo (era 15)
DAYS_BACK = 30
DOMINANCE_MIN = 0.75           # Dominância mínima de FVGs (era 0.65)
MAX_AGE_BARS = 30              # FVGs com mais de 30 velas = ignorar


def detect_fvgs(closes, highs, lows, pip_size, min_gap=MIN_GAP_PIPS):
    """Detecta Fair Value Gaps com scoring."""
    fvgs = []
    n = len(closes)
    for i in range(2, n):
        gap_up = lows[i] - highs[i-2]
        gap_down = lows[i-2] - highs[i]
        gap_up_pips = gap_up / pip_size
        gap_down_pips = gap_down / pip_size
        
        if gap_up_pips >= min_gap:
            age_penalty = (n - i) / n * 0.3
            gap_bonus = min(gap_up_pips / 10, 0.5)
            score = min(1.0 - age_penalty + gap_bonus, 1.0)
            fvgs.append({'index': int(i), 'type': 'bullish',
                        'top': float(highs[i-2]), 'bottom': float(lows[i]),
                        'gap_pips': round(float(gap_up_pips), 1),
                        'score': round(score, 2), 'age_bars': int(n - i)})
        
        if gap_down_pips >= min_gap:
            age_penalty = (n - i) / n * 0.3
            gap_bonus = min(gap_down_pips / 10, 0.5)
            score = min(1.0 - age_penalty + gap_bonus, 1.0)
            fvgs.append({'index': int(i), 'type': 'bearish',
                        'top': float(highs[i]), 'bottom': float(lows[i-2]),
                        'gap_pips': round(float(gap_down_pips), 1),
                        'score': round(score, 2), 'age_bars': int(n - i)})
    return fvgs


def calculate_crt(closes, window=20):
    """CRT: posição atual no percentil do range recente."""
    n = len(closes)
    if n < window + 1:
        return 0.5
    recent = closes[-(window+1):]
    current_range = np.max(recent) - np.min(recent)
    if current_range == 0:
        return 0.5
    position = (closes[-1] - np.min(recent)) / current_range
    return round(float(position), 2)


def check_signal(fvgs, closes, tf='M15'):
    """Verifica se há sinal de entrada baseado nos FVGs + CRT."""
    recent = [f for f in fvgs if f['age_bars'] <= MAX_AGE_BARS]
    bullish = [f for f in recent if f['type'] == 'bullish']
    bearish = [f for f in recent if f['type'] == 'bearish']
    
    if not bullish and not bearish:
        return None
    
    bullish_score = sum(f['score'] for f in bullish)
    bearish_score = sum(f['score'] for f in bearish)
    total = bullish_score + bearish_score
    
    if total == 0:
        return None
    
    crt = calculate_crt(closes)
    dominance = max(bullish_score, bearish_score) / total
    
    # Só sinaliza se CRT ≥ threshold e dominância clara
    if crt < CRT_THRESHOLD or dominance < DOMINANCE_MIN:
        return None
    
    if bullish_score > bearish_score:
        # Bullish: comprar no pullback ao bottom do FVG mais recente
        best = max(bullish, key=lambda f: f['score'])
        sl_pips = max(MIN_SL_PIPS, min(best['gap_pips'], MAX_SL_PIPS))
        return {
            'direction': 'BUY',
            'entry': closes[-1],
            'sl_pips': sl_pips,
            'gap': best['gap_pips'],
            'score': best['score'],
            'crt': crt,
            'dominance': round(dominance, 2),
            'tf': tf,
        }
    else:
        best = max(bearish, key=lambda f: f['score'])
        sl_pips = max(MIN_SL_PIPS, min(best['gap_pips'], MAX_SL_PIPS))
        return {
            'direction': 'SELL',
            'entry': closes[-1],
            'sl_pips': sl_pips,
            'gap': best['gap_pips'],
            'score': best['score'],
            'crt': crt,
            'dominance': round(dominance, 2),
            'tf': tf,
        }


def simulate_trade(signal, future_closes, future_highs, future_lows, pip_size, rr=RR_RATIO):
    """Simula o resultado de um trade nos candles futuros."""
    direction = signal['direction']
    entry = signal['entry']
    sl_pips = signal['sl_pips']
    
    if direction == 'BUY':
        sl = entry - sl_pips * pip_size
        tp = entry + sl_pips * rr * pip_size
        for i in range(len(future_closes)):
            if future_lows[i] <= sl:
                return {'result': 'LOSS', 'pnl_pips': -sl_pips, 'bars_held': i+1}
            if future_highs[i] >= tp:
                return {'result': 'WIN', 'pnl_pips': sl_pips * rr, 'bars_held': i+1}
    else:
        sl = entry + sl_pips * pip_size
        tp = entry - sl_pips * rr * pip_size
        for i in range(len(future_closes)):
            if future_highs[i] >= sl:
                return {'result': 'LOSS', 'pnl_pips': -sl_pips, 'bars_held': i+1}
            if future_lows[i] <= tp:
                return {'result': 'WIN', 'pnl_pips': sl_pips * rr, 'bars_held': i+1}
    
    # Expirou sem hit — fecha no último close
    last = future_closes[-1]
    if direction == 'BUY':
        pnl = (last - entry) / pip_size
    else:
        pnl = (entry - last) / pip_size
    return {'result': 'WIN' if pnl > 0 else 'LOSS', 'pnl_pips': round(pnl, 1), 'bars_held': len(future_closes)}


def backtest_pair(pair, pip_size, days=DAYS_BACK):
    """Backtest de 30 dias para um par."""
    from tvDatafeed import TvDatafeed, Interval as TVInterval
    
    tv = TvDatafeed()
    exchange = 'FX'
    
    results = {'pair': pair, 'signals': 0, 'wins': 0, 'losses': 0, 'total_pips': 0.0, 'trades': []}
    
    # Pegar dados H1 (maior timeframe) como base
    df_h1 = tv.get_hist(symbol=pair, exchange=exchange, interval=TVInterval.in_1_hour, n_bars=500)
    if df_h1 is None or len(df_h1) < 100:
        return results
    
    # Converter pra arrays
    closes_h1 = np.array(df_h1['close']).flatten().astype(float)
    highs_h1 = np.array(df_h1['high']).flatten().astype(float)
    lows_h1 = np.array(df_h1['low']).flatten().astype(float)
    
    # Simular trade a cada candle H1
    min_lookback = 30
    max_bars_forward = 24  # Máximo 24h de duração
    
    for i in range(min_lookback, len(closes_h1) - max_bars_forward):
        # Janela de lookback
        lookback = min(200, i)
        window_closes = closes_h1[i-lookback:i+1]
        window_highs = highs_h1[i-lookback:i+1]
        window_lows = lows_h1[i-lookback:i+1]
        
        fvgs = detect_fvgs(window_closes, window_highs, window_lows, pip_size)
        signal = check_signal(fvgs, window_closes, 'H1')
        
        if not signal:
            continue
        
        # Dados futuros
        future_end = min(i + max_bars_forward, len(closes_h1))
        future_c = closes_h1[i+1:future_end]
        future_h = highs_h1[i+1:future_end]
        future_l = lows_h1[i+1:future_end]
        
        if len(future_c) < 3:
            continue
        
        # Atualizar entry pro preço real do candle
        signal['entry'] = closes_h1[i]
        
        trade_result = simulate_trade(signal, future_c, future_h, future_l, pip_size)
        
        results['signals'] += 1
        results['total_pips'] += trade_result['pnl_pips']
        if trade_result['result'] == 'WIN':
            results['wins'] += 1
        else:
            results['losses'] += 1
        
        results['trades'].append({
            'time': str(datetime.now()),  # Placeholder — o índice real viria do DataFrame
            'direction': signal['direction'],
            'entry': round(float(signal['entry']), 5),
            'result': trade_result['result'],
            'pnl_pips': trade_result['pnl_pips'],
            'bars_held': trade_result['bars_held'],
            'crt': signal['crt'],
            'score': signal['score'],
        })
    
    return results


def main():
    print(f"📊 BACKTEST Chart Analyzer — {DAYS_BACK} dias (H1)")
    print(f"   Estratégia: FVG multi-TF + CRT≥{int(CRT_THRESHOLD*100)}% + RR {RR_RATIO}:1")
    print(f"   SL: {MIN_SL_PIPS}-{MAX_SL_PIPS}p | Gap mín: {MIN_GAP_PIPS}p")
    print()
    
    all_results = {}
    grand_total = {'signals': 0, 'wins': 0, 'losses': 0, 'total_pips': 0.0}
    
    for pair in PAIRS:
        pip = PIP_SIZES[pair]
        print(f"  {pair}...", end=" ", flush=True)
        
        r = backtest_pair(pair, pip)
        wr = round(r['wins'] / r['signals'] * 100, 1) if r['signals'] > 0 else 0
        avg_pips = round(r['total_pips'] / r['signals'], 1) if r['signals'] > 0 else 0
        
        print(f"{r['signals']} trades | WR={wr}% | PnL={r['total_pips']:.0f}p | Avg={avg_pips}p/trade")
        
        all_results[pair] = r
        for k in grand_total:
            grand_total[k] += r[k]
    
    total_wr = round(grand_total['wins'] / grand_total['signals'] * 100, 1) if grand_total['signals'] > 0 else 0
    avg_total = round(grand_total['total_pips'] / grand_total['signals'], 1) if grand_total['signals'] > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"  TOTAL: {grand_total['signals']} trades | WR={total_wr}% | PnL={grand_total['total_pips']:.0f}p | {avg_total}p/trade")
    
    # Expectância
    if grand_total['signals'] > 0:
        win_rate = grand_total['wins'] / grand_total['signals']
        avg_win = sum(t['pnl_pips'] for r in all_results.values() for t in r['trades'] if t['result'] == 'WIN') / max(grand_total['wins'], 1)
        avg_loss = abs(sum(t['pnl_pips'] for r in all_results.values() for t in r['trades'] if t['result'] == 'LOSS') / max(grand_total['losses'], 1))
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        print(f"  Expectância: {expectancy:.1f}p/trade | Avg Win: {avg_win:.0f}p | Avg Loss: {avg_loss:.0f}p")
    
    # Salvar resultados
    output = {
        'timestamp': datetime.now().isoformat(),
        'config': {
            'days': DAYS_BACK,
            'crt_threshold': CRT_THRESHOLD,
            'rr_ratio': RR_RATIO,
            'min_sl': MIN_SL_PIPS,
            'max_sl': MAX_SL_PIPS,
            'min_gap': MIN_GAP_PIPS,
        },
        'summary': {
            'total_signals': grand_total['signals'],
            'wins': grand_total['wins'],
            'losses': grand_total['losses'],
            'win_rate': total_wr,
            'total_pips': round(grand_total['total_pips'], 1),
            'avg_pips_per_trade': avg_total,
        },
        'pairs': {p: {
            'signals': r['signals'],
            'wins': r['wins'],
            'losses': r['losses'],
            'wr': round(r['wins']/r['signals']*100,1) if r['signals']>0 else 0,
            'total_pips': round(r['total_pips'], 1),
        } for p, r in all_results.items()},
    }
    
    out_path = FOREX_DIR / 'backtest_chart_analyzer.json'
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\n📁 Salvo em: {out_path}")
    
    return output


if __name__ == '__main__':
    main()
