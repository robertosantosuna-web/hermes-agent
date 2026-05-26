#!/usr/bin/env python3
"""
Chart Pattern Study — Biblioteca de Reconhecimento de Padrões de Gráfico.
Extrai padrões ICT (CHoCH, FVG, OB, Sweeps, Structure) de dados reais
e salva como "exemplos" para treinar reconhecimento visual.

no_agent — zero tokens.
Roda diariamente às 08:00 BRT (após daily study).
"""
import json, os, sys, urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

HERMES = Path(os.path.expanduser('~/.hermes'))
PATTERNS_DIR = HERMES / 'forex' / 'patterns'
PATTERN_LIB = PATTERNS_DIR / 'pattern_library.json'

# ─── Data Fetching ──────────────────────────────────────────────────────

def download_pair(pair, days=60):
    """Baixa candles M5 do Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{pair}=X?range={days}d&interval=5m"
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
                candles.append({
                    'idx': i, 'ts': ts,
                    'o': round(o, 5), 'h': round(h, 5),
                    'l': round(l, 5), 'c': round(c, 5)
                })
        return candles
    except Exception as e:
        return []

# ─── Structure Detection ────────────────────────────────────────────────

def find_swings(candles):
    """Detect swing highs and lows with fractal method (5-candle window)."""
    highs, lows = [], []
    for i in range(2, len(candles) - 2):
        c = candles[i]
        # Swing high
        if c['h'] > max(candles[i-1]['h'], candles[i-2]['h'], candles[i+1]['h'], candles[i+2]['h']):
            highs.append({'idx': i, 'price': c['h'], 'ts': c['ts']})
        # Swing low
        if c['l'] < min(candles[i-1]['l'], candles[i-2]['l'], candles[i+1]['l'], candles[i+2]['l']):
            lows.append({'idx': i, 'price': c['l'], 'ts': c['ts']})
    return highs, lows

def find_structure(candles, highs, lows):
    """Find HH/HL (bullish) and LH/LL (bearish) structure breaks."""
    breaks = []
    
    # Bullish BOS (Break of Structure): higher high after higher low
    for i in range(2, len(highs)):
        if highs[i]['price'] > highs[i-1]['price'] > highs[i-2]['price']:
            # Check if preceded by higher low
            prev_lows = [l for l in lows if l['idx'] < highs[i]['idx']]
            if len(prev_lows) >= 2:
                if prev_lows[-1]['price'] > prev_lows[-2]['price']:
                    breaks.append({
                        'idx': highs[i]['idx'],
                        'type': 'BULLISH_BOS',
                        'price': highs[i]['price'],
                        'ts': highs[i]['ts'],
                        'strength': _calc_strength(i, highs),
                    })
    
    # Bearish BOS
    for i in range(2, len(lows)):
        if lows[i]['price'] < lows[i-1]['price'] < lows[i-2]['price']:
            prev_highs = [h for h in highs if h['idx'] < lows[i]['idx']]
            if len(prev_highs) >= 2:
                if prev_highs[-1]['price'] < prev_highs[-2]['price']:
                    breaks.append({
                        'idx': lows[i]['idx'],
                        'type': 'BEARISH_BOS',
                        'price': lows[i]['price'],
                        'ts': lows[i]['ts'],
                        'strength': _calc_strength(i, lows),
                    })
    
    return breaks

def _calc_strength(i, swings):
    """Calculate swing strength based on distance from prior swings."""
    if i < 3:
        return 0.5
    dist = abs(swings[i]['price'] - swings[i-3]['price'])
    avg_price = swings[i]['price']
    return min(1.0, dist / (avg_price * 0.01)) if avg_price > 0 else 0.5

def find_choch(candles, highs, lows):
    """Detect Change of Character (CHoCH) — reversal signal."""
    chochs = []
    
    for i in range(3, len(candles) - 3):
        c = candles[i]
        prev = candles[i-3:i]
        next_c = candles[i+1:i+4]
        
        # Look for sweep + reversal
        # Sweep of swing low followed by bullish close
        for sl in lows:
            if sl['idx'] >= i - 5 and sl['idx'] <= i:
                if c['l'] <= sl['price'] * 0.999 and c['c'] > c['o']:
                    if len(next_c) >= 2 and next_c[0]['c'] > c['h']:
                        chochs.append({
                            'idx': i,
                            'type': 'BULLISH_CHOCH',
                            'price': c['c'],
                            'swept_level': sl['price'],
                            'ts': c['ts'],
                            'quality': 'high' if c['c'] > c['h'] * 0.5 else 'medium',
                        })
                        break
        
        # Sweep of swing high followed by bearish close
        for sh in highs:
            if sh['idx'] >= i - 5 and sh['idx'] <= i:
                if c['h'] >= sh['price'] * 1.001 and c['c'] < c['o']:
                    if len(next_c) >= 2 and next_c[0]['c'] < c['l']:
                        chochs.append({
                            'idx': i,
                            'type': 'BEARISH_CHOCH',
                            'price': c['c'],
                            'swept_level': sh['price'],
                            'ts': c['ts'],
                            'quality': 'high' if c['c'] < c['l'] * 1.5 else 'medium',
                        })
                        break
    
    return chochs

def find_fvg(candles):
    """Detect Fair Value Gaps (FVG) — ICT concept."""
    fvgs = []
    
    for i in range(1, len(candles) - 1):
        c0, c1, c2 = candles[i-1], candles[i], candles[i+1]
        
        # Bullish FVG: c0.high < c2.low
        gap_size = c2['l'] - c0['h']
        if gap_size > 0:
            fvgs.append({
                'idx': i,
                'type': 'BULLISH_FVG',
                'gap_top': c2['l'],
                'gap_bottom': c0['h'],
                'gap_size_pct': round(gap_size / c0['h'] * 100, 4),
                'ts': c1['ts'],
            })
        
        # Bearish FVG: c0.low > c2.high
        gap_size = c0['l'] - c2['h']
        if gap_size > 0:
            fvgs.append({
                'idx': i,
                'type': 'BEARISH_FVG',
                'gap_top': c0['l'],
                'gap_bottom': c2['h'],
                'gap_size_pct': round(gap_size / c0['l'] * 100, 4),
                'ts': c1['ts'],
            })
    
    return fvgs

def find_order_blocks(candles, highs, lows):
    """Detect Order Blocks (OB) — last opposite candle before impulse."""
    obs = []
    
    for i in range(2, len(candles) - 2):
        c = candles[i]
        
        # Bullish OB: last bearish candle before strong bullish move
        if candles[i-1]['c'] < candles[i-1]['o']:  # prior bearish
            if c['h'] > candles[i-1]['h'] and c['c'] > c['o']:  # bullish breakout
                look_forward = candles[i+1:min(i+6, len(candles))]
                if len(look_forward) >= 2:
                    avg_forward = sum(x['c'] for x in look_forward) / len(look_forward)
                    if avg_forward > c['h']:  # continuation confirmed
                        obs.append({
                            'idx': i,
                            'type': 'BULLISH_OB',
                            'ob_high': candles[i-1]['h'],
                            'ob_low': candles[i-1]['l'],
                            'ts': c['ts'],
                            'quality': 'high' if c['c'] - candles[i-1]['h'] > 0 else 'medium',
                        })
        
        # Bearish OB
        if candles[i-1]['c'] > candles[i-1]['o']:  # prior bullish
            if c['l'] < candles[i-1]['l'] and c['c'] < c['o']:  # bearish breakout
                look_forward = candles[i+1:min(i+6, len(candles))]
                if len(look_forward) >= 2:
                    avg_forward = sum(x['c'] for x in look_forward) / len(look_forward)
                    if avg_forward < c['l']:  # continuation
                        obs.append({
                            'idx': i,
                            'type': 'BEARISH_OB',
                            'ob_high': candles[i-1]['h'],
                            'ob_low': candles[i-1]['l'],
                            'ts': c['ts'],
                            'quality': 'high' if candles[i-1]['l'] - c['c'] > 0 else 'medium',
                        })
    
    return obs

def find_liquidity_levels(highs, lows):
    """Find key liquidity levels (EQH/EQL, double tops/bottoms)."""
    levels = []
    
    # Equal highs (sell-side liquidity)
    high_prices = defaultdict(list)
    for h in highs:
        high_prices[round(h['price'], 5)].append(h)
    for price, swings in high_prices.items():
        if len(swings) >= 2:
            levels.append({
                'price': price,
                'type': 'EQUAL_HIGHS',
                'touches': len(swings),
                'first_ts': swings[0]['ts'],
                'last_ts': swings[-1]['ts'],
            })
    
    # Equal lows (buy-side liquidity)
    low_prices = defaultdict(list)
    for l in lows:
        low_prices[round(l['price'], 5)].append(l)
    for price, swings in low_prices.items():
        if len(swings) >= 2:
            levels.append({
                'price': price,
                'type': 'EQUAL_LOWS',
                'touches': len(swings),
                'first_ts': swings[0]['ts'],
                'last_ts': swings[-1]['ts'],
            })
    
    return levels[:20]  # Top 20 levels

# ─── Pattern Snapshot ──────────────────────────────────────────────────

def extract_snapshot(candles, idx, context_before=10, context_after=5):
    """Extract price context around a pattern for visual recognition."""
    start = max(0, idx - context_before)
    end = min(len(candles), idx + context_after + 1)
    
    snapshot = []
    for c in candles[start:end]:
        snapshot.append({
            'idx': c['idx'],
            'o': c['o'], 'h': c['h'], 'l': c['l'], 'c': c['c'],
            'relative_idx': c['idx'] - idx,  # 0 = pattern candle
            'body': abs(c['c'] - c['o']),
            'direction': 'bull' if c['c'] > c['o'] else 'bear' if c['c'] < c['o'] else 'doji',
            'upper_wick': c['h'] - max(c['c'], c['o']),
            'lower_wick': min(c['c'], c['o']) - c['l'],
        })
    
    return snapshot

# ─── ASCII Chart Rendering ─────────────────────────────────────────────

def render_ascii_chart(snapshot, width=40, height=15):
    """Render a simple ASCII chart of the pattern for visual inspection."""
    prices = []
    for s in snapshot:
        prices.extend([s['h'], s['l']])
    
    if not prices:
        return ""
    
    pmin, pmax = min(prices), max(prices)
    prange = pmax - pmin
    if prange == 0:
        prange = 0.0001
    
    chart = []
    chart.append(f"  {'─' * width}")
    
    for row in range(height - 1, -1, -1):
        line = "  │"
        price_level = pmin + (prange * row / (height - 1))
        
        for s in snapshot:
            x_pos = int((s['relative_idx'] + 10) / max(len(snapshot) + 10, 1) * width)
            if x_pos >= width:
                continue
            
            if price_level <= s['h'] and price_level >= s['l']:
                # Inside body
                body_min = min(s['o'], s['c'])
                body_max = max(s['o'], s['c'])
                if price_level >= body_min and price_level <= body_max:
                    line = line[:x_pos] + ('█' if s['direction'] == 'bull' else '▓') + line[x_pos+1:]
                else:
                    line = line[:x_pos] + '│' + line[x_pos+1:]
        
        chart.append(line)
    
    chart.append(f"  {'─' * width}")
    return '\n'.join(chart)

# ─── Pattern Library Management ─────────────────────────────────────────

def update_library(pair, patterns_by_type):
    """Update the pattern library with new examples."""
    library = {}
    if PATTERN_LIB.exists():
        try:
            library = json.loads(PATTERN_LIB.read_text())
        except:
            pass
    
    now = datetime.now(timezone.utc).isoformat()
    
    for ptype, patterns in patterns_by_type.items():
        if ptype not in library:
            library[ptype] = {
                'total_collected': 0,
                'examples': [],
                'last_updated': now,
            }
        
        # Add new examples (keep max 50 per type)
        for p in patterns:
            # Avoid duplicates
            existing_ts = {e.get('ts') for e in library[ptype]['examples']}
            if p.get('ts') not in existing_ts:
                p['pair'] = pair
                p['collected_at'] = now
                library[ptype]['examples'].append(p)
                library[ptype]['total_collected'] += 1
        
        # Keep last 50
        library[ptype]['examples'] = library[ptype]['examples'][-50:]
        library[ptype]['last_updated'] = now
    
    PATTERN_LIB.parent.mkdir(parents=True, exist_ok=True)
    PATTERN_LIB.write_text(json.dumps(library, indent=2, default=str))

# ─── Main ───────────────────────────────────────────────────────────────

def main():
    now = datetime.now(timezone.utc)
    today = now.strftime('%Y-%m-%d')
    
    print(f"📊 Chart Pattern Study — {today}")
    
    pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'NZDUSD']
    
    all_patterns_by_type = defaultdict(list)
    total_patterns = 0
    
    for pair in pairs:
        print(f"\n▶ {pair}")
        candles = download_pair(pair, 30)
        if not candles:
            print(f"  Sem dados")
            continue
        
        print(f"  {len(candles)} candles")
        
        # Detect patterns
        highs, lows = find_swings(candles)
        print(f"  Swings: {len(highs)}H/{len(lows)}L")
        
        # BOS
        bos = find_structure(candles, highs, lows)
        print(f"  BOS: {len(bos)}")
        all_patterns_by_type['structure_breaks'].extend(bos)
        
        # CHoCH
        chochs = find_choch(candles, highs, lows)
        high_quality = [c for c in chochs if c.get('quality') == 'high']
        print(f"  CHoCH: {len(chochs)} ({len(high_quality)} high quality)")
        all_patterns_by_type['choch'].extend(chochs)
        
        # FVG
        fvgs = find_fvg(candles)
        significant_fvgs = [f for f in fvgs if f['gap_size_pct'] > 0.02]
        print(f"  FVG: {len(fvgs)} ({len(significant_fvgs)} significant)")
        all_patterns_by_type['fvg'].extend(fvgs[:20])
        
        # Order Blocks
        obs = find_order_blocks(candles, highs, lows)
        print(f"  Order Blocks: {len(obs)}")
        all_patterns_by_type['order_blocks'].extend(obs)
        
        # Liquidity Levels
        levels = find_liquidity_levels(highs, lows)
        print(f"  Liquidity Levels: {len(levels)}")
        all_patterns_by_type['liquidity_levels'].extend(levels)
        
        # Save pattern examples with snapshots (only high-quality CHoCHs)
        for choch in high_quality[:3]:  # Top 3 per pair
            snapshot = extract_snapshot(candles, choch['idx'])
            choch['snapshot'] = snapshot
            choch['ascii_chart'] = render_ascii_chart(snapshot)
        
        total_patterns += len(bos) + len(chochs) + len(fvgs) + len(obs) + len(levels)
    
    # Update library
    update_library('all_pairs', all_patterns_by_type)
    
    # Save daily report
    report_dir = PATTERNS_DIR / today
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report = {
        'date': today,
        'pairs_analyzed': len(pairs),
        'total_patterns': total_patterns,
        'by_type': {k: len(v) for k, v in all_patterns_by_type.items()},
        'high_quality_chochs': [
            {
                'pair': c.get('pair', '?'),
                'type': c['type'],
                'price': c['price'],
                'quality': c.get('quality'),
                'ascii': c.get('ascii_chart', ''),
            }
            for c in all_patterns_by_type.get('choch', [])
            if c.get('quality') == 'high'
        ][:5],  # Top 5 high-quality for visual review
    }
    
    report_path = report_dir / 'pattern_report.json'
    report_path.write_text(json.dumps(report, indent=2, default=str))
    
    # ── Neural KB Integration ──
    try:
        from kb_bridge import write as kb_write, read as kb_read, query as kb_query
        # Write patterns to shared KB
        kb_write('chart_patterns', {
            'dominant_patterns': [
                {'type': k, 'count': v}
                for k, v in report['by_type'].items()
            ],
            'pattern_quality_by_pair': {
                pair: len([c for c in all_patterns_by_type.get('choch', [])
                          if c.get('quality') == 'high' and c.get('pair') == pair])
                for pair in pairs
            },
            'high_quality_setups': [
                {'pair': c.get('pair', '?'), 'type': c['type'], 'price': c['price']}
                for c in all_patterns_by_type.get('choch', [])
                if c.get('quality') == 'high'
            ],
            'last_scan': today,
            'total_patterns_detected': total_patterns,
        })
        # Check if N. Accumbens has flagged any pairs
        accumbens_data = kb_read('n_accumbens')
        if accumbens_data:
            pair_weights = accumbens_data.get('pair_weights', {})
            for pair, pw in pair_weights.items():
                if pw.get('recommendation') == 'PAUSE':
                    # Check if this pair has high-quality patterns (divergence)
                    hq = [c for c in all_patterns_by_type.get('choch', [])
                          if c.get('quality') == 'high' and c.get('pair') == pair]
                    if len(hq) >= 3:
                        from kb_bridge import synapse
                        synapse('chart_patterns', 'n_accumbens',
                            f'{pair}: {len(hq)} high-quality setups despite PAUSE recommendation — potential opportunity',
                            confidence=0.65,
                            evidence={'pair': pair, 'setups': len(hq), 'recommendation': 'PAUSE'})
    except ImportError:
        pass  # KB not available yet
    
    print(f"\n✅ Total: {total_patterns} padrões detectados")
    for ptype, count in report['by_type'].items():
        print(f"  {ptype}: {count}")
    
    print(f"\n📚 Pattern Library: {PATTERN_LIB}")
    print(f"📄 Report: {report_path}")

if __name__ == '__main__':
    main()
