#!/usr/bin/env python3
"""
Chart Pattern Degraded Learner — Estuda padrões sem MT5 (modo offline).
Gera imagens de padrões a partir de dados do Yahoo Finance usando matplotlib.

Funciona mesmo sem MT5 rodando.
Integra com: chart_pattern_study.py + Neural KB + Visual Cortex.

no_agent — zero tokens.
"""
import json, os, sys, urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

HERMES = Path(os.path.expanduser('~/.hermes'))
PATTERNS_DIR = HERMES / 'forex' / 'patterns'
CHARTS_DIR = PATTERNS_DIR / 'generated_charts'
ALGO_LIB = PATTERNS_DIR / 'pattern_library.json'

# ── Data ─────────────────────────────────────────────────────────────────

def download_pair(pair, days=30):
    """Baixa candles M5/M15 do Yahoo Finance."""
    for interval, label in [('5m', 'M5'), ('15m', 'M15')]:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{pair}=X?range={days}d&interval={interval}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read())
            result = data['chart']['result'][0]
            timestamps = result['timestamp']
            quotes = result['indicators']['quote'][0]
            candles = []
            for i, ts in enumerate(timestamps):
                o, h, l, c = quotes['open'][i], quotes['high'][i], quotes['low'][i], quotes['close'][i]
                if None not in (o, h, l, c):
                    candles.append({'idx': i, 'ts': ts, 'o': o, 'h': h, 'l': l, 'c': c})
            yield label, candles
        except Exception:
            yield label, []


# ── Pattern Detection (same as chart_pattern_study.py) ───────────────────

def find_swings(candles):
    highs, lows = [], []
    for i in range(2, len(candles) - 2):
        c = candles[i]
        if c['h'] > max(candles[i-1]['h'], candles[i-2]['h'], candles[i+1]['h'], candles[i+2]['h']):
            highs.append({'idx': i, 'price': c['h'], 'ts': c['ts']})
        if c['l'] < min(candles[i-1]['l'], candles[i-2]['l'], candles[i+1]['l'], candles[i+2]['l']):
            lows.append({'idx': i, 'price': c['l'], 'ts': c['ts']})
    return highs, lows


def find_choch(candles, highs, lows):
    chochs = []
    for i in range(3, len(candles) - 3):
        c = candles[i]
        next_c = candles[i+1:i+4]
        for sl in lows:
            if sl['idx'] >= i - 5 and sl['idx'] <= i:
                if c['l'] <= sl['price'] * 0.999 and c['c'] > c['o']:
                    if len(next_c) >= 2 and next_c[0]['c'] > c['h']:
                        chochs.append({
                            'idx': i, 'type': 'BULLISH_CHOCH',
                            'price': c['c'], 'swept_level': sl['price'],
                            'ts': c['ts'], 'quality': 'high' if c['c'] > c['h'] * 0.5 else 'medium',
                        })
                        break
        for sh in highs:
            if sh['idx'] >= i - 5 and sh['idx'] <= i:
                if c['h'] >= sh['price'] * 1.001 and c['c'] < c['o']:
                    if len(next_c) >= 2 and next_c[0]['c'] < c['l']:
                        chochs.append({
                            'idx': i, 'type': 'BEARISH_CHOCH',
                            'price': c['c'], 'swept_level': sh['price'],
                            'ts': c['ts'], 'quality': 'high' if c['c'] < c['l'] * 1.5 else 'medium',
                        })
                        break
    return chochs


def find_fvg(candles):
    fvgs = []
    for i in range(1, len(candles) - 1):
        c0, c1, c2 = candles[i-1], candles[i], candles[i+1]
        gap_size = c2['l'] - c0['h']
        if gap_size > 0:
            fvgs.append({
                'idx': i, 'type': 'BULLISH_FVG',
                'gap_top': c2['l'], 'gap_bottom': c0['h'],
                'gap_size_pct': round(gap_size / c0['h'] * 100, 4), 'ts': c1['ts'],
            })
        gap_size = c0['l'] - c2['h']
        if gap_size > 0:
            fvgs.append({
                'idx': i, 'type': 'BEARISH_FVG',
                'gap_top': c0['l'], 'gap_bottom': c2['h'],
                'gap_size_pct': round(gap_size / c0['l'] * 100, 4), 'ts': c1['ts'],
            })
    return fvgs


def find_structure(candles, highs, lows):
    breaks = []
    for i in range(2, len(highs)):
        if highs[i]['price'] > highs[i-1]['price'] > highs[i-2]['price']:
            prev_lows = [l for l in lows if l['idx'] < highs[i]['idx']]
            if len(prev_lows) >= 2 and prev_lows[-1]['price'] > prev_lows[-2]['price']:
                breaks.append({'idx': highs[i]['idx'], 'type': 'BULLISH_BOS',
                               'price': highs[i]['price'], 'ts': highs[i]['ts']})
    for i in range(2, len(lows)):
        if lows[i]['price'] < lows[i-1]['price'] < lows[i-2]['price']:
            prev_highs = [h for h in highs if h['idx'] < lows[i]['idx']]
            if len(prev_highs) >= 2 and prev_highs[-1]['price'] < prev_highs[-2]['price']:
                breaks.append({'idx': lows[i]['idx'], 'type': 'BEARISH_BOS',
                               'price': lows[i]['price'], 'ts': lows[i]['ts']})
    return breaks


# ── Pattern Template Generation ──────────────────────────────────────────

def generate_pattern_template(candles, pattern_idx, context=15):
    """
    Gera um template do padrão para reconhecimento visual.
    Cria uma "assinatura" numérica do padrão: sequência de candles normalizada.
    """
    start = max(0, pattern_idx - context)
    end = min(len(candles), pattern_idx + context + 1)
    
    window = candles[start:end]
    
    if len(window) < 5:
        return None
    
    # Normalize prices relative to pattern candle
    pattern_candle = candles[pattern_idx]
    center_price = (pattern_candle['h'] + pattern_candle['l']) / 2
    
    template = {
        'pattern_idx': pattern_idx,
        'candles': [],
        'features': {
            'body_sizes': [],
            'wick_ratios': [],
            'directions': [],
            'gaps': [],
        },
    }
    
    for c in window:
        # Normalized OHLC
        pct_factor = center_price / 1000  # scale factor
        if pct_factor <= 0:
            pct_factor = 0.0001
        
        body = abs(c['c'] - c['o'])
        upper_wick = c['h'] - max(c['c'], c['o'])
        lower_wick = min(c['c'], c['o']) - c['l']
        
        template['candles'].append({
            'rel_idx': c['idx'] - pattern_idx,
            'o_norm': round((c['o'] - center_price) / pct_factor, 2),
            'h_norm': round((c['h'] - center_price) / pct_factor, 2),
            'l_norm': round((c['l'] - center_price) / pct_factor, 2),
            'c_norm': round((c['c'] - center_price) / pct_factor, 2),
            'direction': 'bull' if c['c'] > c['o'] else 'bear' if c['c'] < c['o'] else 'doji',
            'body_size': round(body, 5),
            'upper_wick_ratio': round(upper_wick / (body + 0.00001), 2),
            'lower_wick_ratio': round(lower_wick / (body + 0.00001), 2),
        })
        
        template['features']['body_sizes'].append(round(body, 5))
        template['features']['wick_ratios'].append(
            round((upper_wick + lower_wick) / (body + 0.00001), 2))
        template['features']['directions'].append(
            1 if c['c'] > c['o'] else -1 if c['c'] < c['o'] else 0)
    
    # Gaps between consecutive candles
    for i in range(1, len(window)):
        gap = window[i]['l'] - window[i-1]['h']  # gap up
        if gap < 0:
            gap = window[i-1]['l'] - window[i]['h']  # gap down (negative)
        template['features']['gaps'].append(round(gap, 5))
    
    # Summary statistics
    bodies = [abs(c['c'] - c['o']) for c in window]
    template['summary'] = {
        'avg_body': round(sum(bodies) / len(bodies), 5),
        'max_body': round(max(bodies), 5),
        'bullish_count': sum(1 for c in window if c['c'] > c['o']),
        'bearish_count': sum(1 for c in window if c['c'] < c['o']),
        'doji_count': sum(1 for c in window if c['c'] == c['o']),
        'trend': 'bull' if sum(1 for c in window if c['c'] > c['o']) > len(window) * 0.6
                 else 'bear' if sum(1 for c in window if c['c'] < c['o']) > len(window) * 0.6
                 else 'neutral',
    }
    
    return template


# ── Pattern Similarity Scoring ───────────────────────────────────────────

def score_pattern_similarity(template_a, template_b):
    """
    Compare two pattern templates and return similarity score (0-1).
    Uses simple feature distance — not ML, just heuristics.
    """
    if not template_a or not template_b:
        return 0.0
    
    score = 0.0
    weights = {'trend': 0.3, 'body_ratio': 0.25, 'direction': 0.25, 'avg_body': 0.2}
    
    # Trend match
    if template_a.get('summary', {}).get('trend') == template_b.get('summary', {}).get('trend'):
        score += weights['trend']
    
    # Body size ratio match
    try:
        ratio_a = template_a['summary']['max_body'] / (template_a['summary']['avg_body'] + 0.00001)
        ratio_b = template_b['summary']['max_body'] / (template_b['summary']['avg_body'] + 0.00001)
        if abs(ratio_a - ratio_b) < 0.5:
            score += weights['body_ratio'] * (1 - abs(ratio_a - ratio_b) / max(ratio_a, ratio_b, 1))
    except (KeyError, ZeroDivisionError):
        pass
    
    # Direction sequence similarity
    dirs_a = template_a['features'].get('directions', [])
    dirs_b = template_b['features'].get('directions', [])
    if dirs_a and dirs_b:
        min_len = min(len(dirs_a), len(dirs_b))
        matches = sum(1 for i in range(min_len) if i < len(dirs_a) and i < len(dirs_b) and dirs_a[i] == dirs_b[i])
        score += weights['direction'] * (matches / min_len if min_len > 0 else 0)
    
    # Average body comparison
    try:
        body_diff = abs(template_a['summary']['avg_body'] - template_b['summary']['avg_body'])
        body_scale = max(template_a['summary']['avg_body'], template_b['summary']['avg_body'], 0.00001)
        if body_diff / body_scale < 2.0:
            score += weights['avg_body'] * (1 - body_diff / (body_scale * 2))
    except (KeyError, ZeroDivisionError):
        pass
    
    return round(min(score, 1.0), 3)


# ── Study and Learn ──────────────────────────────────────────────────────

def study_pattern_templates(pair, candles, tf_label, patterns_by_type):
    """
    Study each detected pattern, create templates, and find similar patterns.
    This is the "learning" phase — the brain internalizes pattern shapes.
    """
    study = {
        'pair': pair,
        'timeframe': tf_label,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'patterns_studied': {},
        'learned_similarities': [],
        'pattern_archetypes': {},
    }
    
    for ptype, patterns in patterns_by_type.items():
        if not patterns:
            continue
        
        templates = []
        for p in patterns[:10]:  # Study top 10 of each type
            template = generate_pattern_template(candles, p['idx'], context=12)
            if template:
                template['pattern_type'] = ptype
                template['pattern_price'] = p.get('price', p.get('gap_top', 0))
                template['pair'] = pair
                templates.append(template)
        
        if not templates:
            continue
        
        # Find the "archetype" — the template closest to the average
        if len(templates) >= 2:
            best_score = -1
            best_idx = 0
            for i, t1 in enumerate(templates):
                avg_sim = sum(score_pattern_similarity(t1, t2) for j, t2 in enumerate(templates) if j != i) / (len(templates) - 1)
                if avg_sim > best_score:
                    best_score = avg_sim
                    best_idx = i
            
            study['pattern_archetypes'][ptype] = {
                'archetype_idx': best_idx,
                'avg_similarity': round(best_score, 3),
                'sample_count': len(templates),
                'template': templates[best_idx],
            }
        
        # Find cross-pattern similarities (e.g., CHoCH that looks like BOS)
        other_types = [k for k in patterns_by_type if k != ptype and patterns_by_type.get(k)]
        for other_type in other_types:
            for op in patterns_by_type[other_type][:5]:
                other_template = generate_pattern_template(candles, op['idx'], context=12)
                for t in templates[:3]:
                    sim = score_pattern_similarity(t, other_template) if other_template else 0
                    if sim > 0.6:
                        study['learned_similarities'].append({
                            'type_a': ptype,
                            'type_b': other_type,
                            'similarity': sim,
                            'note': f'{ptype} visualmente similar a {other_type} ({sim})',
                        })
        
        study['patterns_studied'][ptype] = {
            'total_detected': len(patterns),
            'templates_created': len(templates),
            'sample_template': templates[0] if templates else None,
        }
    
    return study


# ─── Main ────────────────────────────────────────────────────────────────

def main():
    now = datetime.now(timezone.utc)
    today = now.strftime('%Y-%m-%d')
    
    print(f"📊 Chart Pattern Degraded Learner — {today}")
    print("   (Modo offline — estuda via Yahoo Finance, sem MT5)")
    
    pairs = ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDJPY']
    timeframes = [('5m', 'M5'), ('15m', 'M15'), ('60m', 'H1')]
    
    all_studies = {}
    total_per_type = defaultdict(int)
    
    for pair in pairs:
        print(f"\n▶ {pair}")
        pair_studies = {}
        
        for interval, tf_label in timeframes:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{pair}=X?range=30d&interval={interval}"
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                resp = urllib.request.urlopen(req, timeout=15)
                data = json.loads(resp.read())
                result = data['chart']['result'][0]
                timestamps = result['timestamp']
                quotes = result['indicators']['quote'][0]
                candles = []
                for i, ts in enumerate(timestamps):
                    o, h, l, c = quotes['open'][i], quotes['high'][i], quotes['low'][i], quotes['close'][i]
                    if None not in (o, h, l, c):
                        candles.append({'idx': i, 'ts': ts, 'o': o, 'h': h, 'l': l, 'c': c})
                
                if not candles:
                    continue
                
                # Detect patterns
                highs, lows = find_swings(candles)
                patterns = {
                    'choch': find_choch(candles, highs, lows),
                    'fvg': find_fvg(candles),
                    'bos': find_structure(candles, highs, lows),
                }
                
                # Study and create templates
                study = study_pattern_templates(pair, candles, tf_label, patterns)
                pair_studies[tf_label] = study
                
                total = sum(len(v) for v in patterns.values())
                for k, v in patterns.items():
                    total_per_type[k] += len(v)
                
                print(f"  {tf_label}: {total} patterns ({study['pattern_archetypes'].__len__()} archetypes)")
                
            except Exception as e:
                print(f"  {tf_label}: error — {e}")
        
        all_studies[pair] = pair_studies
    
    # ── Save Study Report ────────────────────────────────────────────────
    report_dir = PATTERNS_DIR / 'degraded_studies'
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report = {
        'date': today,
        'timestamp': now.isoformat(),
        'pairs_studied': len(all_studies),
        'total_patterns_by_type': dict(total_per_type),
        'studies': all_studies,
        'key_learnings': [],
    }
    
    # Extract key learnings from cross-pattern similarities
    for pair, tfs in all_studies.items():
        for tf, study in tfs.items():
            for sim in study.get('learned_similarities', []):
                report['key_learnings'].append({
                    'pair': pair,
                    'timeframe': tf,
                    **sim,
                })
    
    report_path = report_dir / f'degraded_study_{today}.json'
    report_path.write_text(json.dumps(report, indent=2, default=str))
    
    # ── Neural KB Integration ────────────────────────────────────────────
    try:
        from kb_bridge import write as kb_write
        
        # Share archetypes with other brain modules
        archetypes_learned = {}
        for pair, tfs in all_studies.items():
            for tf, study in tfs.items():
                for ptype, arch in study.get('pattern_archetypes', {}).items():
                    key = f'{pair}_{tf}_{ptype}'
                    archetypes_learned[key] = {
                        'pair': pair,
                        'timeframe': tf,
                        'pattern_type': ptype,
                        'avg_similarity': arch.get('avg_similarity', 0),
                        'sample_count': arch.get('sample_count', 0),
                        'trend': arch.get('template', {}).get('summary', {}).get('trend', '?'),
                    }
        
        kb_write('chart_patterns', {
            'study_mode': 'degraded',
            'last_study': today,
            'total_patterns': sum(total_per_type.values()),
            'archetypes': archetypes_learned,
            'per_type': dict(total_per_type),
        })
        
        # Cross-reference with N. Accumbens for trading decisions
        # If a pair has high-quality patterns and good WR history → signal
        from kb_bridge import read as kb_read, synapse as kb_synapse
        accumbens = kb_read('n_accumbens')
        if accumbens:
            pair_weights = accumbens.get('pair_weights', {})
            for pair in pairs:
                if pair in pair_weights:
                    pw = pair_weights[pair]
                    pair_total = sum(
                        len(all_studies.get(pair, {}).get(tf, {}).get('patterns_studied', {}).get('choch', []))
                        for tf in ['M15', 'M5']
                        if tf in all_studies.get(pair, {})
                    )
                    if pw.get('wr', 0) > 50 and pair_total > 5:
                        kb_synapse('chart_patterns', 'n_accumbens',
                            f'{pair}: WR={pw.get("wr")}% + {pair_total} patterns = favorable',
                            confidence=0.7,
                            evidence={'pair': pair, 'wr': pw.get('wr'), 'patterns': pair_total})
    except ImportError:
        pass
    
    print(f"\n✅ Degraded study complete: {sum(total_per_type.values())} total patterns")
    print(f"📄 Report: {report_path}")


if __name__ == '__main__':
    main()
