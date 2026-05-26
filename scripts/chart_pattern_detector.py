#!/usr/bin/env python3
"""
Chart Pattern Detector — Reconhecimento algorítmico de padrões gráficos clássicos.
Detecta: Head & Shoulders, Double Top/Bottom, Triangles, Flags, Wedges, Channels, etc.

no_agent — zero tokens. Usado pelo cérebro para estudo e análise.

Uso:
  python3 chart_pattern_detector.py              # Analisa todos os pares
  python3 chart_pattern_detector.py --pair EURUSD # Par específico
  python3 chart_pattern_detector.py --json        # Output JSON
"""

import json, sys, argparse
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
import urllib.request
import math

HERMES = Path.home() / ".hermes"
OUTPUT_DIR = HERMES / "forex" / "chart_patterns"
PAIRS = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'NZDUSD', 'EURJPY', 'GBPJPY']
TIMEFRAMES = ['H1', 'M30', 'M15']


def fetch_candles(pair, timeframe='H1', days=60):
    """Busca candles do Yahoo Finance."""
    interval_map = {'M5': '5m', 'M15': '15m', 'M30': '30m', 'H1': '60m', 'H4': '1h'}
    interval = interval_map.get(timeframe, '60m')
    
    try:
        symbol = f"{pair}=X"
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={days}d&interval={interval}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        result = data['chart']['result'][0]
        quotes = result['indicators']['quote'][0]
        
        candles = []
        for i in range(len(result['timestamp'])):
            o, h, l, c = quotes['open'][i], quotes['high'][i], quotes['low'][i], quotes['close'][i]
            if None not in (o, h, l, c):
                candles.append({
                    'idx': len(candles),
                    'o': o, 'h': h, 'l': l, 'c': c,
                    'ts': result['timestamp'][i]
                })
        return candles
    except Exception as e:
        return []


def find_swing_points(candles, window=3):
    """Encontra swing highs e lows."""
    highs = []
    lows = []
    
    for i in range(window, len(candles) - window):
        c = candles[i]
        is_high = all(c['h'] >= candles[i-j]['h'] for j in range(1, window+1)) and \
                  all(c['h'] >= candles[i+j]['h'] for j in range(1, window+1))
        is_low = all(c['l'] <= candles[i-j]['l'] for j in range(1, window+1)) and \
                 all(c['l'] <= candles[i+j]['l'] for j in range(1, window+1))
        
        if is_high:
            highs.append({'idx': i, 'price': c['h'], 'type': 'high'})
        if is_low:
            lows.append({'idx': i, 'price': c['l'], 'type': 'low'})
    
    return highs, lows


def detect_double_top(candles, highs, tolerance=0.005):
    """Detecta Double Top: dois topos no mesmo nível, vale entre eles."""
    patterns = []
    
    for i in range(1, len(highs)):
        h1, h2 = highs[i-1], highs[i]
        diff = abs(h1['price'] - h2['price'])
        avg = (h1['price'] + h2['price']) / 2
        pct = diff / avg if avg > 0 else 0
        
        if pct <= tolerance and (h2['idx'] - h1['idx']) >= 5:
            # Precisa de um vale entre eles
            between = [c for c in candles[h1['idx']:h2['idx']]]
            if between:
                valley = min(c['l'] for c in between)
                if valley < min(h1['price'], h2['price']) * 0.99:
                    patterns.append({
                        'type': 'DOUBLE_TOP',
                        'top1': {'idx': h1['idx'], 'price': round(h1['price'], 5)},
                        'top2': {'idx': h2['idx'], 'price': round(h2['price'], 5)},
                        'valley': round(valley, 5),
                        'confidence': round((1 - pct/tolerance) * 100),
                        'bias': 'BEARISH'
                    })
    return patterns


def detect_double_bottom(candles, lows, tolerance=0.005):
    """Detecta Double Bottom: dois fundos no mesmo nível, pico entre eles."""
    patterns = []
    
    for i in range(1, len(lows)):
        l1, l2 = lows[i-1], lows[i]
        diff = abs(l1['price'] - l2['price'])
        avg = (l1['price'] + l2['price']) / 2
        pct = diff / avg if avg > 0 else 0
        
        if pct <= tolerance and (l2['idx'] - l1['idx']) >= 5:
            between = [c for c in candles[l1['idx']:l2['idx']]]
            if between:
                peak = max(c['h'] for c in between)
                if peak > max(l1['price'], l2['price']) * 1.01:
                    patterns.append({
                        'type': 'DOUBLE_BOTTOM',
                        'bottom1': {'idx': l1['idx'], 'price': round(l1['price'], 5)},
                        'bottom2': {'idx': l2['idx'], 'price': round(l2['price'], 5)},
                        'peak': round(peak, 5),
                        'confidence': round((1 - pct/tolerance) * 100),
                        'bias': 'BULLISH'
                    })
    return patterns


def detect_head_shoulders(candles, highs, lows, min_distance=8, tolerance=0.01):
    """Detecta Head & Shoulders: 3 picos, central mais alto, ombros nivelados."""
    patterns = []
    
    for i in range(2, len(highs)):
        left, head, right = highs[i-2], highs[i-1], highs[i]
        
        # Head deve ser mais alto que os ombros
        if head['price'] <= left['price'] or head['price'] <= right['price']:
            continue
        
        # Ombros devem estar nivelados
        shoulder_avg = (left['price'] + right['price']) / 2
        left_diff = abs(left['price'] - shoulder_avg) / shoulder_avg
        right_diff = abs(right['price'] - shoulder_avg) / shoulder_avg
        
        if left_diff <= tolerance and right_diff <= tolerance:
            dist_lr = right['idx'] - left['idx']
            if dist_lr >= min_distance:
                # Procurar neckline (vales entre os picos)
                valley_left = min(c['l'] for c in candles[left['idx']:head['idx']])
                valley_right = min(c['l'] for c in candles[head['idx']:right['idx']])
                neckline = (valley_left + valley_right) / 2
                
                patterns.append({
                    'type': 'HEAD_AND_SHOULDERS',
                    'left_shoulder': {'idx': left['idx'], 'price': round(left['price'], 5)},
                    'head': {'idx': head['idx'], 'price': round(head['price'], 5)},
                    'right_shoulder': {'idx': right['idx'], 'price': round(right['price'], 5)},
                    'neckline': round(neckline, 5),
                    'confidence': round(min(100, (1 - left_diff/tolerance) * 100)),
                    'bias': 'BEARISH'
                })
    
    return patterns


def detect_inverse_head_shoulders(candles, lows, min_distance=8, tolerance=0.01):
    """Detecta Inverse Head & Shoulders: 3 vales, central mais baixo."""
    patterns = []
    
    for i in range(2, len(lows)):
        left, head, right = lows[i-2], lows[i-1], lows[i]
        
        if head['price'] >= left['price'] or head['price'] >= right['price']:
            continue
        
        shoulder_avg = (left['price'] + right['price']) / 2
        left_diff = abs(left['price'] - shoulder_avg) / shoulder_avg
        right_diff = abs(right['price'] - shoulder_avg) / shoulder_avg
        
        if left_diff <= tolerance and right_diff <= tolerance:
            dist_lr = right['idx'] - left['idx']
            if dist_lr >= min_distance:
                peak_left = max(c['h'] for c in candles[left['idx']:head['idx']])
                peak_right = max(c['h'] for c in candles[head['idx']:right['idx']])
                neckline = (peak_left + peak_right) / 2
                
                patterns.append({
                    'type': 'INVERSE_HEAD_AND_SHOULDERS',
                    'left_shoulder': {'idx': left['idx'], 'price': round(left['price'], 5)},
                    'head': {'idx': head['idx'], 'price': round(head['price'], 5)},
                    'right_shoulder': {'idx': right['idx'], 'price': round(right['price'], 5)},
                    'neckline': round(neckline, 5),
                    'confidence': round(min(100, (1 - left_diff/tolerance) * 100)),
                    'bias': 'BULLISH'
                })
    
    return patterns


def detect_triangle(highs, lows, min_points=4):
    """Detecta triângulos (ascending, descending, symmetrical)."""
    patterns = []
    
    if len(highs) < min_points or len(lows) < min_points:
        return patterns
    
    # Usar últimos swing points
    recent_highs = highs[-min_points:]
    recent_lows = lows[-min_points:]
    
    if len(recent_highs) < min_points or len(recent_lows) < min_points:
        return patterns
    
    # Regressão linear nos highs
    h_idx = [h['idx'] for h in recent_highs]
    h_prices = [h['price'] for h in recent_highs]
    h_slope = linear_slope(h_idx, h_prices)
    
    # Regressão linear nos lows
    l_idx = [l['idx'] for l in recent_lows]
    l_prices = [l['price'] for l in recent_lows]
    l_slope = linear_slope(l_idx, l_prices)
    
    pip_size = 0.0001
    h_slope_pips = h_slope * 10000 if pip_size == 0.0001 else h_slope * 100
    l_slope_pips = l_slope * 10000 if pip_size == 0.0001 else l_slope * 100
    
    # Classificar triângulo
    triangle_type = None
    bias = None
    
    if abs(h_slope_pips) < 0.1 and l_slope_pips > 0.1:
        triangle_type = 'ASCENDING_TRIANGLE'
        bias = 'BULLISH'
    elif h_slope_pips < -0.1 and abs(l_slope_pips) < 0.1:
        triangle_type = 'DESCENDING_TRIANGLE'
        bias = 'BEARISH'
    elif h_slope_pips < -0.05 and l_slope_pips > 0.05:
        triangle_type = 'SYMMETRICAL_TRIANGLE'
        bias = 'NEUTRAL_BREAKOUT'
    
    if triangle_type:
        patterns.append({
            'type': triangle_type,
            'high_slope': round(h_slope_pips, 2),
            'low_slope': round(l_slope_pips, 2),
            'swing_points': len(recent_highs) + len(recent_lows),
            'confidence': round(min(100, min_points * 20)),
            'bias': bias,
            'approaching_apex': True if (recent_highs[-1]['idx'] - recent_highs[0]['idx']) > 15 else False
        })
    
    return patterns


def detect_flag(candles, highs, lows):
    """Detecta bandeiras (flag/pennant) após impulso forte."""
    patterns = []
    
    if len(candles) < 30:
        return patterns
    
    # Procurar impulso (movimento forte em uma direção)
    for i in range(10, len(candles) - 15):
        segment = candles[i-10:i]
        move = segment[-1]['c'] - segment[0]['o']
        pip_size = 0.01 if abs(move) < 1 else 0.0001
        move_pips = move / pip_size
        
        # Impulso significativo (> 30 pips)
        if abs(move_pips) >= 30:
            direction = 'BULLISH' if move > 0 else 'BEARISH'
            
            # Verificar consolidação após o impulso
            consolidation = candles[i:i+15]
            cons_high = max(c['h'] for c in consolidation)
            cons_low = min(c['l'] for c in consolidation)
            cons_range = (cons_high - cons_low) / pip_size
            
            # Consolidação deve ser menor que o impulso
            if cons_range < abs(move_pips) * 0.5:
                # Verificar se é bandeira (contra-tendência) ou pennant (simétrico)
                if direction == 'BULLISH':
                    # Flag bullish: consolidação com leve viés de baixa
                    cons_first = consolidation[0]
                    cons_last = consolidation[-1]
                    if cons_last['c'] < cons_first['c']:
                        patterns.append({
                            'type': 'BULL_FLAG',
                            'impulse_pips': round(move_pips),
                            'consolidation_pips': round(cons_range),
                            'start_idx': i,
                            'confidence': round(min(100, move_pips / 50 * 100)),
                            'bias': 'BULLISH_CONTINUATION'
                        })
                else:
                    if consolidation[-1]['c'] > consolidation[0]['c']:
                        patterns.append({
                            'type': 'BEAR_FLAG',
                            'impulse_pips': round(abs(move_pips)),
                            'consolidation_pips': round(cons_range),
                            'start_idx': i,
                            'confidence': round(min(100, abs(move_pips) / 50 * 100)),
                            'bias': 'BEARISH_CONTINUATION'
                        })
    return patterns


def detect_wedge(candles, highs, lows, window=20):
    """Detecta cunhas (rising/falling wedge)."""
    patterns = []
    
    if len(highs) < 3 or len(lows) < 3:
        return patterns
    
    recent_highs = highs[-4:]
    recent_lows = lows[-4:]
    
    if len(recent_highs) < 3 or len(recent_lows) < 3:
        return patterns
    
    h_idx = [h['idx'] for h in recent_highs]
    h_prices = [h['price'] for h in recent_highs]
    h_slope = linear_slope(h_idx, h_prices)
    
    l_idx = [l['idx'] for l in recent_lows]
    l_prices = [l['price'] for l in recent_lows]
    l_slope = linear_slope(l_idx, l_prices)
    
    pip_size = 0.0001
    h_slope_pips = h_slope * 10000
    l_slope_pips = l_slope * 10000
    
    # Rising wedge: ambos sobem, lows sobem mais rápido (bearish)
    if h_slope_pips > 0.05 and l_slope_pips > h_slope_pips * 1.2:
        patterns.append({
            'type': 'RISING_WEDGE',
            'high_slope': round(h_slope_pips, 2),
            'low_slope': round(l_slope_pips, 2),
            'confidence': round(min(100, (l_slope_pips / max(h_slope_pips, 0.01)) * 50)),
            'bias': 'BEARISH_REVERSAL'
        })
    
    # Falling wedge: ambos caem, highs caem mais rápido (bullish)
    if h_slope_pips < -0.05 and h_slope_pips < l_slope_pips * 1.2:
        patterns.append({
            'type': 'FALLING_WEDGE',
            'high_slope': round(h_slope_pips, 2),
            'low_slope': round(l_slope_pips, 2),
            'confidence': round(min(100, (abs(h_slope_pips) / max(abs(l_slope_pips), 0.01)) * 50)),
            'bias': 'BULLISH_REVERSAL'
        })
    
    return patterns


def detect_channel(candles, highs, lows, period=30):
    """Detecta canais de preço (parallel channel)."""
    if len(highs) < 3 or len(lows) < 3:
        return []
    
    recent_highs = highs[-5:]
    recent_lows = lows[-5:]
    
    h_idx = [h['idx'] for h in recent_highs]
    h_prices = [h['price'] for h in recent_highs]
    h_slope = linear_slope(h_idx, h_prices)
    
    l_idx = [l['idx'] for l in recent_lows]
    l_prices = [l['price'] for l in recent_lows]
    l_slope = linear_slope(l_idx, l_prices)
    
    pip_size = 0.0001
    h_slope_pips = h_slope * 10000
    l_slope_pips = l_slope * 10000
    
    # Canais: slopes paralelos (diferença < 20%)
    slope_ratio = abs(h_slope_pips - l_slope_pips) / max(abs(h_slope_pips), abs(l_slope_pips), 0.001)
    
    if slope_ratio < 0.3 and abs(h_slope_pips) > 0.02:
        direction = 'ASCENDING' if h_slope_pips > 0 else 'DESCENDING'
        patterns = [{
            'type': f'{direction}_CHANNEL',
            'high_slope': round(h_slope_pips, 2),
            'low_slope': round(l_slope_pips, 2),
            'channel_width_pct': round((max(h_prices) - min(l_prices)) / min(l_prices) * 100, 2),
            'confidence': round(100 - slope_ratio * 100),
            'bias': 'BULLISH' if direction == 'ASCENDING' else 'BEARISH'
        }]
        return patterns
    
    return []


def detect_support_resistance(candles, highs, lows, n_levels=5):
    """Detecta níveis de suporte e resistência mais tocados."""
    all_levels = defaultdict(int)
    pip_size = 0.0001
    
    # Arredondar preços para o pip mais próximo
    for c in candles:
        h_round = round(c['h'] / pip_size) * pip_size
        l_round = round(c['l'] / pip_size) * pip_size
        c_round = round(c['c'] / pip_size) * pip_size
        all_levels[h_round] += 1
        all_levels[l_round] += 1
        all_levels[c_round] += 0.5
    
    # Ordenar por número de toques
    sorted_levels = sorted(all_levels.items(), key=lambda x: x[1], reverse=True)
    
    # Filtrar níveis significativos (> 3 toques) e agrupar próximos
    levels = []
    for price, touches in sorted_levels:
        if touches >= 3:
            # Verificar se já tem nível próximo
            if not any(abs(price - l['price']) < pip_size * 3 for l in levels):
                levels.append({
                    'price': round(price, 5),
                    'touches': round(touches),
                    'type': 'support' if price < candles[-1]['c'] else 'resistance'
                })
        
        if len(levels) >= n_levels:
            break
    
    return levels


def linear_slope(x, y):
    """Calcula slope da regressão linear."""
    n = len(x)
    if n < 2:
        return 0
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_xx = sum(xi * xi for xi in x)
    
    denom = n * sum_xx - sum_x * sum_x
    if denom == 0:
        return 0
    return (n * sum_xy - sum_x * sum_y) / denom


def analyze_pair(pair, timeframes=None):
    """Analisa todos os padrões para um par."""
    if timeframes is None:
        timeframes = TIMEFRAMES
    
    results = {'pair': pair, 'timeframes': {}, 'timestamp': datetime.now(timezone.utc).isoformat()}
    
    for tf in timeframes:
        candles = fetch_candles(pair, tf)
        if len(candles) < 30:
            continue
        
        highs, lows = find_swing_points(candles)
        
        tf_patterns = {
            'candles': len(candles),
            'swing_highs': len(highs),
            'swing_lows': len(lows),
            'patterns': []
        }
        
        # Detectar todos os padrões
        all_p = []
        all_p.extend(detect_double_top(candles, highs))
        all_p.extend(detect_double_bottom(candles, lows))
        all_p.extend(detect_head_shoulders(candles, highs, lows))
        all_p.extend(detect_inverse_head_shoulders(candles, lows))
        all_p.extend(detect_triangle(highs, lows))
        all_p.extend(detect_flag(candles, highs, lows))
        all_p.extend(detect_wedge(candles, highs, lows))
        all_p.extend(detect_channel(candles, highs, lows))
        
        tf_patterns['patterns'] = all_p
        
        # S/R levels
        tf_patterns['support_resistance'] = detect_support_resistance(candles, highs, lows)
        
        results['timeframes'][tf] = tf_patterns
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Chart Pattern Detector")
    parser.add_argument("--pair", help="Par específico")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()
    
    pairs = [args.pair] if args.pair else PAIRS
    all_results = []
    
    for pair in pairs:
        if not args.json:
            print(f"\n📊 {pair} — Detectando padrões gráficos...")
        
        result = analyze_pair(pair)
        all_results.append(result)
        
        if not args.json:
            total = sum(len(tf['patterns']) for tf in result['timeframes'].values())
            print(f"   {total} padrões encontrados em {len(result['timeframes'])} timeframes")
            
            for tf, data in result['timeframes'].items():
                if data['patterns']:
                    print(f"   ├─ {tf}: {len(data['patterns'])} padrões")
                    for p in data['patterns'][:3]:
                        emoji = '🐻' if 'BEARISH' in p.get('bias', '') else ('🐂' if 'BULLISH' in p.get('bias', '') else '⚪')
                        print(f"   │  {emoji} {p['type']} ({p.get('confidence', '?')}%)")
    
    # Salvar
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime('%Y%m%d_%H%M')
    output_file = OUTPUT_DIR / f"chart_patterns_{date_str}.json"
    output_file.write_text(json.dumps(all_results, indent=2, default=str))
    
    if not args.json:
        total_patterns = sum(
            len(tf['patterns']) 
            for r in all_results 
            for tf in r['timeframes'].values()
        )
        print(f"\n✅ {total_patterns} padrões totais detectados")
        print(f"   Salvo em: {output_file}")
    else:
        print(json.dumps(all_results, indent=2, default=str))


if __name__ == "__main__":
    main()
