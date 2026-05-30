#!/usr/bin/env python3
"""
Flow + Trend Analyzer — Ordem de fluxo e força de tendência.
Complementa o Range Detector e FVG Analyzer.

Fluxo:
  - Bull/Bear pressure ratio (velas verdes vs vermelhas)
  - Volume-weighted momentum (candle size × volume)
  - Delta acumulado (CVD simulado)
  - Absorption detection (vela grande + reversão)

Tendência:
  - HH/HL structure (uptrend) vs LH/LL (downtrend)
  - ADX-based strength scoring
  - Multi-TF alignment (M15→M30→H1→H4)
  - Trend maturity (há quanto tempo está ativa)

Uso:
  python3 flow_trend.py GBPJPY         # Análise completa
  python3 flow_trend.py --all           # Todos os pares
"""

import json, sys, os
from pathlib import Path
from datetime import datetime
import numpy as np

HERMES = Path.home() / ".hermes"
FOREX_DIR = HERMES / "forex"

PAIRS = ['GBPJPY', 'USDJPY', 'EURUSD', 'GBPUSD', 'EURJPY', 'USDCAD']

TIMEFRAMES = {
    'M15': ('15m', 200),
    'M30': ('30m', 150),
    'H1': ('1h', 100),
    'H4': ('4h', 80),
}


def fetch_data(pair, interval, n_bars):
    from tvDatafeed import TvDatafeed, Interval as TVInterval
    tv = TvDatafeed()
    tf_map = {'15m': TVInterval.in_15_minute, '30m': TVInterval.in_30_minute,
              '1h': TVInterval.in_1_hour, '4h': TVInterval.in_4_hour}
    df = tv.get_hist(symbol=pair, exchange='FX', interval=tf_map.get(interval, TVInterval.in_1_hour), n_bars=n_bars)
    if df is None or len(df) < 20:
        return None
    return {
        'open': np.array(df['open']).flatten().astype(float),
        'high': np.array(df['high']).flatten().astype(float),
        'low': np.array(df['low']).flatten().astype(float),
        'close': np.array(df['close']).flatten().astype(float),
    }


# ══════════════════════════════════════════════
# ORDER FLOW METRICS
# ══════════════════════════════════════════════

def bull_bear_ratio(opens, closes):
    """Razão de velas bullish vs bearish nas últimas N candles."""
    n = len(closes)
    window = min(n, 50)
    o = opens[-window:]
    c = closes[-window:]
    bullish = sum(1 for i in range(len(o)) if c[i] > o[i])
    bearish = sum(1 for i in range(len(o)) if c[i] < o[i])
    total = bullish + bearish
    if total == 0:
        return 0.5, 0
    ratio = bullish / total
    return round(ratio, 2), total


def momentum_score(opens, closes, window=20):
    """Score de momentum: candle size ponderado pela direção."""
    n = len(closes)
    w = min(n, window)
    o = opens[-w:]
    c = closes[-w:]
    score = 0.0
    for i in range(len(o)):
        change_pct = (c[i] - o[i]) / o[i] if o[i] > 0 else 0
        score += change_pct
    return round(float(score * 100), 2)  # Percentual acumulado


def volume_weighted_momentum(opens, closes, window=20):
    """Momentum ponderado pelo tamanho da vela (proxy de volume)."""
    n = len(closes)
    w = min(n, window)
    o = opens[-w:]
    c = closes[-w:]
    total_weight = 0
    weighted_sum = 0
    for i in range(len(o)):
        body_pct = abs(c[i] - o[i]) / o[i] if o[i] > 0 else 0
        direction = 1 if c[i] > o[i] else -1 if c[i] < o[i] else 0
        weight = body_pct * 100  # Peso = tamanho do corpo %
        weighted_sum += direction * weight
        total_weight += weight
    if total_weight == 0:
        return 0.0
    return round(weighted_sum / total_weight, 2)


def cv_delta(opens, highs, lows, closes, window=20):
    """CVD simulado: diferença entre pressão compradora e vendedora."""
    n = len(closes)
    w = min(n, window)
    h = highs[-w:]
    l = lows[-w:]
    o = opens[-w:]
    c = closes[-w:]
    
    bull_pressure = 0.0
    bear_pressure = 0.0
    
    for i in range(len(o)):
        body = abs(c[i] - o[i])
        upper_wick = h[i] - max(c[i], o[i])
        lower_wick = min(c[i], o[i]) - l[i]
        total_range = h[i] - l[i]
        if total_range == 0:
            continue
        
        # Pressão compradora: corpo bullish + wick inferior
        if c[i] > o[i]:
            bull_pressure += (body + lower_wick) / total_range
        else:
            bear_pressure += (body + upper_wick) / total_range
    
    total = bull_pressure + bear_pressure
    if total == 0:
        return 0.0
    return round((bull_pressure - bear_pressure) / total, 2)


def absorption_check(opens, highs, lows, closes, window=10):
    """Detecta absorção: vela grande com rejeição + reversão no candle seguinte."""
    n = len(closes)
    w = min(n, window + 1)
    h = highs[-w:]
    l = lows[-w:]
    o = opens[-w:]
    c = closes[-w:]
    
    absorptions = []
    for i in range(1, len(o)):
        body_prev = abs(c[i-1] - o[i-1])
        range_prev = h[i-1] - l[i-1]
        body_curr = abs(c[i] - o[i])
        
        if range_prev == 0:
            continue
        
        # Vela grande (>70% do range)
        if body_prev / range_prev > 0.6:
            prev_bullish = c[i-1] > o[i-1]
            curr_bullish = c[i] > o[i]
            
            # Absorção: reversão no candle seguinte
            if prev_bullish and not curr_bullish and c[i] < o[i-1]:
                absorptions.append({'type': 'bearish_absorption', 'index': n - w + i})
            elif not prev_bullish and curr_bullish and c[i] > o[i-1]:
                absorptions.append({'type': 'bullish_absorption', 'index': n - w + i})
    
    return absorptions


# ══════════════════════════════════════════════
# TREND STRUCTURE
# ══════════════════════════════════════════════

def ema(data, period):
    alpha = 2 / (period + 1)
    result = np.zeros_like(data)
    result[0] = data[0]
    for i in range(1, len(data)):
        result[i] = alpha * data[i] + (1 - alpha) * result[i-1]
    return result


def find_swings(highs, lows, window=5):
    """Encontra swing highs e lows."""
    swings_h = []
    swings_l = []
    n = len(highs)
    for i in range(window, n - window):
        is_high = all(highs[i] >= highs[i-j] for j in range(1, window+1)) and \
                  all(highs[i] >= highs[i+j] for j in range(1, window+1))
        is_low = all(lows[i] <= lows[i-j] for j in range(1, window+1)) and \
                 all(lows[i] <= lows[i+j] for j in range(1, window+1))
        if is_high:
            swings_h.append({'index': i, 'price': float(highs[i])})
        if is_low:
            swings_l.append({'index': i, 'price': float(lows[i])})
    return swings_h, swings_l


def trend_structure(highs, lows):
    """Analisa estrutura HH/HL (uptrend) vs LH/LL (downtrend)."""
    sh, sl = find_swings(highs, lows)
    
    if len(sh) < 2 or len(sl) < 2:
        return 'UNDEFINED', 0
    
    recent_h = sh[-3:] if len(sh) >= 3 else sh
    recent_l = sl[-3:] if len(sl) >= 3 else sl
    
    # Verificar HH/HL (uptrend)
    hh = sum(1 for i in range(1, len(recent_h)) if recent_h[i]['price'] > recent_h[i-1]['price'])
    hl = sum(1 for i in range(1, len(recent_l)) if recent_l[i]['price'] > recent_l[i-1]['price'])
    uptrend_score = hh + hl
    
    # Verificar LH/LL (downtrend)
    lh = sum(1 for i in range(1, len(recent_h)) if recent_h[i]['price'] < recent_h[i-1]['price'])
    ll = sum(1 for i in range(1, len(recent_l)) if recent_l[i]['price'] < recent_l[i-1]['price'])
    downtrend_score = lh + ll
    
    max_possible = (len(recent_h)-1) + (len(recent_l)-1)
    if max_possible == 0:
        return 'UNDEFINED', 0
    
    if uptrend_score > downtrend_score:
        return 'UPTREND', round(uptrend_score / max_possible, 2)
    elif downtrend_score > uptrend_score:
        return 'DOWNTREND', round(downtrend_score / max_possible, 2)
    return 'SIDEWAYS', 0.0


def adx_simple(highs, lows, closes, period=14):
    n = len(closes)
    if n < period * 2:
        return 20.0
    tr_arr = np.zeros(n)
    p_dm = np.zeros(n)
    m_dm = np.zeros(n)
    for i in range(1, n):
        tr_arr[i] = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
        up = highs[i] - highs[i-1]
        dn = lows[i-1] - lows[i]
        p_dm[i] = up if up > dn and up > 0 else 0
        m_dm[i] = dn if dn > up and dn > 0 else 0
    atr = np.mean(tr_arr[-period:])
    if atr == 0:
        return 20.0
    smooth_p = ema(p_dm, period)[-1]
    smooth_m = ema(m_dm, period)[-1]
    pdi = (smooth_p / atr) * 100 if atr > 0 else 0
    mdi = (smooth_m / atr) * 100 if atr > 0 else 0
    denom = pdi + mdi
    dx = abs(pdi - mdi) / denom * 100 if denom > 0.001 else 0
    return float(dx)


def trend_maturity(highs, lows):
    """Estima há quantos candles a tendência está ativa."""
    sh, sl = find_swings(highs, lows)
    if len(sh) < 2 or len(sl) < 2:
        return 0
    
    # Contar candles desde a última quebra de estrutura
    last_h = sh[-1]['index'] if sh else 0
    last_l = sl[-1]['index'] if sl else 0
    n = len(highs)
    
    # Tendência ativa desde o último swing relevante
    maturity = n - max(last_h, last_l)
    return maturity


# ══════════════════════════════════════════════
# UNIFIED ANALYSIS
# ══════════════════════════════════════════════

def analyze_flow_trend(pair):
    """Análise completa de fluxo + tendência em todos os TFs."""
    results = {}
    
    for tf_name, (interval, n_bars) in TIMEFRAMES.items():
        data = fetch_data(pair, interval, n_bars)
        if data is None:
            continue
        
        o, h, l, c = data['open'], data['high'], data['low'], data['close']
        
        # Flow metrics
        bb_ratio, bb_total = bull_bear_ratio(o, c)
        mom = momentum_score(o, c)
        vwm = volume_weighted_momentum(o, c)
        cvd = cv_delta(o, h, l, c)
        absorptions = absorption_check(o, h, l, c)
        
        # Trend metrics
        structure, struct_conf = trend_structure(h, l)
        adx_val = adx_simple(h, l, c)
        maturity = trend_maturity(h, l)
        ema20 = ema(c, 20)[-1] if len(c) >= 20 else c[-1]
        ema50 = ema(c, 50)[-1] if len(c) >= 50 else c[-1]
        ema_dir = 'UP' if ema20 > ema50 else 'DOWN'
        
        # ═══ UNIFIED SCORE ═══
        # Flow score: -1 (forte venda) a +1 (forte compra)
        flow_score = (bb_ratio - 0.5) * 2 * 0.3   # Bull/Bear ratio
        flow_score += cvd * 0.4                      # CVD delta
        flow_score += vwm * 0.3                      # Volume-weighted momentum
        flow_score = round(max(-1.0, min(1.0, flow_score)), 2)
        
        # Trend score: 0 a 1
        trend_score = struct_conf * 0.4               # Estrutura HH/HL
        trend_score += (adx_val / 100) * 0.3          # ADX normalizado
        trend_score += min(maturity / 50, 1.0) * 0.3  # Maturidade
        trend_score = round(min(1.0, trend_score), 2)
        
        # Direção do fluxo
        if flow_score > 0.15:
            flow_dir = 'BULLISH'
        elif flow_score < -0.15:
            flow_dir = 'BEARISH'
        else:
            flow_dir = 'NEUTRAL'
        
        # Força da tendência
        if trend_score > 0.6:
            trend_strength = 'FORTE'
        elif trend_score > 0.35:
            trend_strength = 'MODERADA'
        else:
            trend_strength = 'FRACA'
        
        results[tf_name] = {
            'flow': {
                'score': flow_score,
                'direction': flow_dir,
                'bull_bear_ratio': bb_ratio,
                'cvd_delta': cvd,
                'vw_momentum': vwm,
                'momentum': mom,
                'absorptions': len(absorptions),
                'absorption_type': absorptions[0]['type'] if absorptions else None,
            },
            'trend': {
                'score': trend_score,
                'strength': trend_strength,
                'structure': structure,
                'struct_confidence': struct_conf,
                'adx': round(adx_val, 1),
                'maturity': maturity,
                'ema_dir': ema_dir,
                'ema20': round(float(ema20), 5),
                'ema50': round(float(ema50), 5),
            },
            'price': round(float(c[-1]), 5),
            'range_pips': round(float((max(h[-20:]) - min(l[-20:]))) / (0.01 if 'JPY' in pair else 0.0001), 1),
            'range_20': round(float((max(h[-20:]) - min(l[-20:]))) / (0.01 if 'JPY' in pair else 0.0001), 1),
        }
    
    return results


def multi_tf_alignment(results):
    """Verifica alinhamento multi-timeframe."""
    tf_list = list(results.keys())
    if len(tf_list) < 2:
        return 'INSUFICIENTE', 0
    
    # Contar TFs com mesma direção de fluxo
    flow_dirs = [r['flow']['direction'] for r in results.values()]
    trend_dirs = [r['trend']['structure'] for r in results.values()]
    
    flow_consensus = max(set(flow_dirs), key=flow_dirs.count) if flow_dirs else 'NEUTRAL'
    trend_consensus = max(set(trend_dirs), key=trend_dirs.count) if trend_dirs else 'UNDEFINED'
    
    flow_align = flow_dirs.count(flow_consensus) / len(flow_dirs)
    trend_align = trend_dirs.count(trend_consensus) / len(trend_dirs)
    
    # Combined alignment score
    combined = (flow_align + trend_align) / 2
    
    if combined > 0.75:
        alignment = 'FORTE'
    elif combined > 0.5:
        alignment = 'MODERADO'
    else:
        alignment = 'FRACO'
    
    return f'{flow_consensus}/{trend_consensus}', round(combined, 2), alignment


def render_flow_bar(value, width=12):
    """Renderiza barra de fluxo visual."""
    if value > 0:
        filled = int(value * width)
        return f"[{'█' * filled}{' ' * (width - filled)}] 🟢"
    elif value < 0:
        filled = int(abs(value) * width)
        return f"[{' ' * (width - filled)}{'█' * filled}] 🔴"
    else:
        return f"[{' ' * width}] ⚪"


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('pair', nargs='?', default='GBPJPY')
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()
    
    targets = PAIRS if args.all else [args.pair.upper()]
    
    for pair in targets:
        print(f"\n{'='*65}")
        print(f"  {pair} — Flow + Trend Multi-TF Analysis")
        print(f"{'='*65}")
        
        results = analyze_flow_trend(pair)
        if not results:
            print("  ⚠️ Sem dados")
            continue
        
        consensus, align_score, align_strength = multi_tf_alignment(results)
        
        for tf_name in ['M15', 'M30', 'H1', 'H4']:
            if tf_name not in results:
                continue
            r = results[tf_name]
            f = r['flow']
            t = r['trend']
            
            flow_bar = render_flow_bar((f['score'] + 1) / 2)
            emoji = '📈' if t['ema_dir'] == 'UP' else '📉'
            abs_text = f"Abs:{f['absorption_type']}" if f['absorptions'] > 0 else ""
            
            print(f"\n  {tf_name}: {flow_bar} {f['direction']:8s} | {emoji} {t['strength']:8s} | {t['structure']:10s}")
            print(f"    Flow:  BB={f['bull_bear_ratio']:.2f}  CVD={f['cvd_delta']:+.2f}  VWM={f['vw_momentum']:+.2f}  Mom={f['momentum']:+.1f}%  {abs_text}")
            print(f"    Trend: ADX={t['adx']:.0f}  Struct={t['struct_confidence']:.0%}  Mat={t['maturity']}c  EMA={t['ema_dir']}")
            print(f"    Price: {r['price']:.5f}  Range20: {r['range_20']}p")
        
        # Resumo
        flow_scores = [r['flow']['score'] for r in results.values()]
        trend_scores = [r['trend']['score'] for r in results.values()]
        avg_flow = round(sum(flow_scores) / len(flow_scores), 2) if flow_scores else 0
        avg_trend = round(sum(trend_scores) / len(trend_scores), 2) if trend_scores else 0
        
        h1 = results.get('H1', {})
        
        print(f"\n  ── RESUMO ──")
        print(f"  Consenso Multi-TF: {consensus} ({align_strength}, {align_score:.0%})")
        print(f"  Flow médio: {avg_flow:+.2f} | Trend médio: {avg_trend:.2f}")
        
        # Decisão
        if align_score > 0.7 and abs(avg_flow) > 0.1:
            # Alinhamento forte multi-TF + fluxo na mesma direção
            direction = 'COMPRA' if avg_flow > 0 else 'VENDA'
            print(f"  🟢 SETUP CONVICTIVO: {direction} — Alinhamento {align_score:.0%} + Fluxo {avg_flow:+.2f}")
        elif avg_trend > 0.5 and abs(avg_flow) > 0.3:
            direction = 'COMPRA' if avg_flow > 0 else 'VENDA'
            print(f"  🟢 SETUP: Tendência forte + Fluxo alinhado ({direction})")
        elif align_score > 0.5 and avg_trend > 0.4:
            direction = 'COMPRA' if avg_flow > 0 else 'VENDA'
            print(f"  🟡 SETUP MODERADO: Alinhamento {align_score:.0%} — viés {direction}")
        elif avg_trend < 0.3 and abs(avg_flow) < 0.15:
            print(f"  ⚪ LATERAL: Sem fluxo ou tendência — aguardar")
        else:
            print(f"  🟡 CAUTELA: Fluxo e tendência divergentes entre timeframes")
    
    print(f"\n{'='*65}")


if __name__ == '__main__':
    main()
