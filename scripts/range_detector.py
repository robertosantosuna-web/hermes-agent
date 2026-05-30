#!/usr/bin/env python3
"""
Range Detector Multi-TF — Detecta lateralização (range) vs tendência em múltiplos timeframes.
Usa 3 métodos complementares:
  1. ADX normalizado — <25 = range, >25 = tendência
  2. BB Squeeze — Bollinger Bands dentro de Keltner Channel = squeeze/range
  3. ATR relativo — ATR atual vs média móvel do ATR

Output: JSON com score de ranging (0-1) por par/timeframe.
"""

import json, sys
from pathlib import Path
from datetime import datetime
import numpy as np

HERMES = Path.home() / ".hermes"
FOREX_DIR = HERMES / "forex"

PAIRS = ['GBPJPY', 'USDJPY', 'EURUSD', 'GBPUSD', 'EURJPY', 'USDCAD', 'XAUUSD']
TIMEFRAMES = ['15m', '30m', '1h', '4h']
PIP_SIZES = {
    'GBPJPY': 0.01, 'USDJPY': 0.01, 'EURJPY': 0.01,
    'EURUSD': 0.0001, 'GBPUSD': 0.0001, 'USDCAD': 0.0001,
    'XAUUSD': 0.01,
}


def ema(data, period):
    alpha = 2 / (period + 1)
    result = np.zeros_like(data)
    result[0] = data[0]
    for i in range(1, len(data)):
        result[i] = alpha * data[i] + (1 - alpha) * result[i-1]
    return result


def sma(data, period):
    return np.convolve(data, np.ones(period)/period, mode='valid')


def adx(highs, lows, closes, period=14):
    """Average Directional Index — <25 = range, 25-50 = tendência, >50 = forte."""
    n = len(closes)
    if n < period + 1:
        return np.zeros(n)
    
    tr = np.zeros(n)
    plus_dm = np.zeros(n)
    minus_dm = np.zeros(n)
    
    for i in range(1, n):
        tr[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        up_move = highs[i] - highs[i-1]
        down_move = lows[i-1] - lows[i]
        
        if up_move > down_move and up_move > 0:
            plus_dm[i] = up_move
        if down_move > up_move and down_move > 0:
            minus_dm[i] = down_move
    
    atr = np.zeros(n)
    atr[period] = np.mean(tr[1:period+1])
    for i in range(period+1, n):
        atr[i] = (atr[i-1] * (period-1) + tr[i]) / period
    
    plus_di = np.zeros(n)
    minus_di = np.zeros(n)
    for i in range(period, n):
        if atr[i] > 0:
            plus_di[i] = (ema(plus_dm[:i+1], period)[-1] / atr[i]) * 100
            minus_di[i] = (ema(minus_dm[:i+1], period)[-1] / atr[i]) * 100
    
    adx_vals = np.zeros(n)
    for i in range(period*2, n):
        dx_sum = sum(abs(plus_di[j] - minus_di[j]) / max(plus_di[j] + minus_di[j], 0.001) * 100
                     for j in range(i-period+1, i+1))
        adx_vals[i] = dx_sum / period
    
    return adx_vals


def bollinger_bands(closes, period=20, stddev=2.0):
    """Bollinger Bands — squeeze quando bandwidth < 5% do preço."""
    n = len(closes)
    if n < period:
        return np.zeros(n), np.zeros(n), np.zeros(n)
    
    sma_arr = np.zeros(n)
    upper = np.zeros(n)
    lower = np.zeros(n)
    
    for i in range(period-1, n):
        window = closes[i-period+1:i+1]
        sma_arr[i] = np.mean(window)
        std = np.std(window)
        upper[i] = sma_arr[i] + stddev * std
        lower[i] = sma_arr[i] - stddev * std
    
    return upper, sma_arr, lower


def keltner_channel(highs, lows, closes, period=20, atr_period=10, multiplier=1.5):
    """Keltner Channel — usado com BB pra detectar squeeze."""
    n = len(closes)
    if n < period:
        return np.zeros(n), np.zeros(n), np.zeros(n)
    
    typical = (highs + lows + closes) / 3
    ema_line = ema(typical, period)
    
    # ATR
    tr = np.zeros(n)
    for i in range(1, n):
        tr[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
    
    atr = np.zeros(n)
    atr[atr_period] = np.mean(tr[1:atr_period+1])
    for i in range(atr_period+1, n):
        atr[i] = (atr[i-1] * (atr_period-1) + tr[i]) / atr_period
    
    upper_kc = ema_line + multiplier * atr
    lower_kc = ema_line - multiplier * atr
    
    return upper_kc, ema_line, lower_kc


def detect_range(highs, lows, closes, pip_size, tf='15m'):
    """Score de range 0-1: 0 = tendência pura, 1 = range puro."""
    n = len(closes)
    if n < 40:
        return {'range_score': 0.5, 'confidence': 'low', 'verdict': 'INSUFICIENTE'}
    
    # 1. ADX: <22 = strong range, 22-28 = weak trend, >28 = trend
    adx_vals = adx(highs, lows, closes, 14)
    adx_current = adx_vals[-1] if adx_vals[-1] > 0 else 25
    
    # ADX → range score: lower ADX = more range
    if adx_current < 20:
        adx_score = 1.0  # Strong range
    elif adx_current < 25:
        adx_score = 0.7  # Mild range
    elif adx_current < 30:
        adx_score = 0.3  # Mild trend
    else:
        adx_score = 0.0  # Strong trend
    
    # 2. BB Squeeze: BB inside KC = squeeze (range comprimido antes de expansão)
    bb_upper, bb_mid, bb_lower = bollinger_bands(closes)
    kc_upper, kc_mid, kc_lower = keltner_channel(highs, lows, closes)
    
    bb_inside_kc = (bb_lower[-1] >= kc_lower[-1]) and (bb_upper[-1] <= kc_upper[-1])
    bb_width = (bb_upper[-1] - bb_lower[-1]) / bb_mid[-1] if bb_mid[-1] > 0 else 0
    bb_squeeze = bb_width < 0.03  # < 3% do preço = squeeze
    
    squeeze_score = 0.8 if bb_inside_kc and bb_squeeze else 0.4 if bb_inside_kc else 0.0
    
    # 3. ATR relativo: ATR atual vs média
    tr = np.zeros(n)
    for i in range(1, n):
        tr[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
    
    atr14 = np.zeros(n)
    atr14[14] = np.mean(tr[1:15])
    for i in range(15, n):
        atr14[i] = (atr14[i-1] * 13 + tr[i]) / 14
    
    atr_sma50 = np.mean(atr14[-50:]) if n >= 50 else atr14[-1]
    atr_ratio = atr14[-1] / atr_sma50 if atr_sma50 > 0 else 1.0
    
    if atr_ratio < 0.7:
        atr_score = 0.9   # Volatilidade muito baixa = range
    elif atr_ratio < 0.9:
        atr_score = 0.6   # Abaixo da média = comprimindo
    elif atr_ratio > 1.5:
        atr_score = 0.1   # Alta volatilidade = breakout/trend
    else:
        atr_score = 0.4   # Normal
    
    # 4. Verificar consolidação de preço (máximo-mínimo do período)
    lookback = min(30, n)
    recent_high = max(highs[-lookback:])
    recent_low = min(lows[-lookback:])
    price_range_pct = (recent_high - recent_low) / closes[-1] * 100 if closes[-1] > 0 else 0
    
    if price_range_pct < 1.0:
        consolidation_score = 1.0  # < 1% range = forte consolidação
    elif price_range_pct < 2.0:
        consolidation_score = 0.6
    elif price_range_pct > 5.0:
        consolidation_score = 0.0  # > 5% = expandindo
    else:
        consolidation_score = 0.3
    
    # Weighted composite
    range_score = (adx_score * 0.35 + squeeze_score * 0.20 + atr_score * 0.25 + consolidation_score * 0.20)
    
    # Veredito
    if range_score >= 0.70:
        verdict = 'RANGE'
        action = 'NÃO OPERAR — aguardar breakout'
    elif range_score >= 0.50:
        verdict = 'LATERAL'
        action = 'CAUTELA — reduzir tamanho, SL mais largo'
    elif range_score >= 0.30:
        verdict = 'TENDÊNCIA FRACA'
        action = 'OPERAR — confirmar com CRT + multi-TF'
    else:
        verdict = 'TENDÊNCIA'
        action = 'OPERAR — setup padrão'
    
    return {
        'range_score': round(range_score, 2),
        'verdict': verdict,
        'action': action,
        'components': {
            'adx': round(float(adx_current), 1),
            'adx_score': round(adx_score, 2),
            'bb_squeeze': bb_squeeze,
            'bb_width_pct': round(float(bb_width * 100), 1),
            'squeeze_score': round(squeeze_score, 2),
            'atr_ratio': round(float(atr_ratio), 2),
            'atr_score': round(atr_score, 2),
            'price_range_pct': round(float(price_range_pct), 1),
            'consolidation_score': round(consolidation_score, 2),
        },
        'confidence': 'high' if n >= 50 else 'medium',
    }


def analyze_pair(pair, pip_size):
    from tvDatafeed import TvDatafeed, Interval as TVInterval
    
    tf_map = {
        '15m': TVInterval.in_15_minute,
        '30m': TVInterval.in_30_minute,
        '1h': TVInterval.in_1_hour,
        '4h': TVInterval.in_4_hour,
    }
    
    exchange = 'OANDA' if pair == 'XAUUSD' else 'FX'
    tv = TvDatafeed()
    
    results = {}
    for tf_name, tv_int in tf_map.items():
        df = tv.get_hist(symbol=pair, exchange=exchange, interval=tv_int, n_bars=100)
        if df is None or len(df) < 30:
            results[tf_name] = {'error': 'insufficient data'}
            continue
        
        highs = np.array(df['high']).flatten().astype(float)
        lows = np.array(df['low']).flatten().astype(float)
        closes = np.array(df['close']).flatten().astype(float)
        
        results[tf_name] = detect_range(highs, lows, closes, pip_size, tf_name)
    
    return results


def main():
    print(f"📊 Range Detector Multi-TF — {datetime.now().strftime('%d/%m %H:%M')}")
    print(f"   Método: ADX + BB Squeeze + ATR relativo + Consolidação\n")
    
    all_data = {
        'timestamp': datetime.now().isoformat(),
        'pairs': {},
        'summary': {'ranging': [], 'trending': [], 'mixed': []},
    }
    
    for pair in PAIRS:
        print(f"  {pair}...", end=" ", flush=True)
        pip = PIP_SIZES[pair]
        results = analyze_pair(pair, pip)
        all_data['pairs'][pair] = results
        
        # Resumo por par
        avg_score = sum(r.get('range_score', 0.5) for r in results.values() if 'range_score' in r) / max(len(results), 1)
        
        best_tf = max(
            (r for r in results.items() if 'range_score' in r[1]),
            key=lambda x: x[1]['range_score'] if x[1]['verdict'] == 'TENDÊNCIA' else 1-x[1]['range_score'],
            default=(None, {})
        )
        
        print(f"avg={avg_score:.2f}")
        
        if avg_score >= 0.6:
            all_data['summary']['ranging'].append(pair)
        elif avg_score <= 0.35:
            all_data['summary']['trending'].append(pair)
        else:
            all_data['summary']['mixed'].append(pair)
        
        for tf_name, r in results.items():
            if 'range_score' not in r:
                continue
            symbol = '🔒' if r['range_score'] >= 0.6 else '🔓' if r['range_score'] <= 0.35 else '⚠️'
            print(f"     {symbol} {tf_name}: {r['verdict']} (score={r['range_score']}, ADX={r['components']['adx']})")
    
    print(f"\n{'='*55}")
    print(f"  📊 RESUMO MULTI-TF")
    print(f"  🔒 RANGING ({len(all_data['summary']['ranging'])}): {', '.join(all_data['summary']['ranging']) or 'nenhum'}")
    print(f"  🔓 TRENDING ({len(all_data['summary']['trending'])}): {', '.join(all_data['summary']['trending']) or 'nenhum'}")
    print(f"  ⚠️ MIXED ({len(all_data['summary']['mixed'])}): {', '.join(all_data['summary']['mixed']) or 'nenhum'}")
    
    output_file = FOREX_DIR / 'range_detector.json'
    output_file.write_text(json.dumps(all_data, indent=2, default=str))
    print(f"\n📁 {output_file}")
    
    return all_data


if __name__ == '__main__':
    main()
