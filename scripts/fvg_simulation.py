#!/usr/bin/env python3
"""
FVG Pattern Simulation — Run WIN/LOSS evaluation on FVG patterns.
Methodology: detect FVG, evaluate WIN/LOSS with RR 3:1, SL=max(gap,5 pips).
Runs on all 5 pairs: EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY.
"""
import json, os, sys, urllib.request
from pathlib import Path
from datetime import datetime, timezone

HERMES = Path(os.path.expanduser('~/.hermes'))
SIM_DIR = HERMES / 'forex' / 'simulations'
SIM_DIR.mkdir(parents=True, exist_ok=True)

PIP_VALUES = {
    'EURUSD': 0.0001,
    'GBPUSD': 0.0001,
    'AUDUSD': 0.0001,
    'NZDUSD': 0.0001,
    'USDJPY': 0.01,
}

# ─── Data Fetching ──────────────────────────────────────────────────────

def download_pair(pair, days=30, interval='15m'):
    """Download candles from Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{pair}=X?range={days}d&interval={interval}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=30)
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
        print(f"  ERROR fetching {pair}: {e}")
        return []

# ─── Pattern Detection (from chart_pattern_study.py) ───────────────────

def find_swings(candles):
    highs, lows = [], []
    for i in range(2, len(candles) - 2):
        c = candles[i]
        if c['h'] > max(candles[i-1]['h'], candles[i-2]['h'], candles[i+1]['h'], candles[i+2]['h']):
            highs.append({'idx': i, 'price': c['h'], 'ts': c['ts']})
        if c['l'] < min(candles[i-1]['l'], candles[i-2]['l'], candles[i+1]['l'], candles[i+2]['l']):
            lows.append({'idx': i, 'price': c['l'], 'ts': c['ts']})
    return highs, lows

def _calc_strength(i, swings):
    if i < 3:
        return 0.5
    dist = abs(swings[i]['price'] - swings[i-3]['price'])
    avg_price = swings[i]['price']
    return min(1.0, dist / (avg_price * 0.01)) if avg_price > 0 else 0.5

def find_structure(candles, highs, lows):
    breaks = []
    for i in range(2, len(highs)):
        if highs[i]['price'] > highs[i-1]['price'] > highs[i-2]['price']:
            prev_lows = [l for l in lows if l['idx'] < highs[i]['idx']]
            if len(prev_lows) >= 2:
                if prev_lows[-1]['price'] > prev_lows[-2]['price']:
                    breaks.append({
                        'idx': highs[i]['idx'], 'type': 'BULLISH_BOS',
                        'price': highs[i]['price'], 'ts': highs[i]['ts'],
                        'strength': _calc_strength(i, highs),
                    })
    for i in range(2, len(lows)):
        if lows[i]['price'] < lows[i-1]['price'] < lows[i-2]['price']:
            prev_highs = [h for h in highs if h['idx'] < lows[i]['idx']]
            if len(prev_highs) >= 2:
                if prev_highs[-1]['price'] < prev_highs[-2]['price']:
                    breaks.append({
                        'idx': lows[i]['idx'], 'type': 'BEARISH_BOS',
                        'price': lows[i]['price'], 'ts': lows[i]['ts'],
                        'strength': _calc_strength(i, lows),
                    })
    return breaks

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
                            'ts': c['ts'],
                            'quality': 'high' if c['c'] > c['h'] * 0.5 else 'medium',
                        })
                        break
        for sh in highs:
            if sh['idx'] >= i - 5 and sh['idx'] <= i:
                if c['h'] >= sh['price'] * 1.001 and c['c'] < c['o']:
                    if len(next_c) >= 2 and next_c[0]['c'] < c['l']:
                        chochs.append({
                            'idx': i, 'type': 'BEARISH_CHOCH',
                            'price': c['c'], 'swept_level': sh['price'],
                            'ts': c['ts'],
                            'quality': 'high' if c['c'] < c['l'] * 1.5 else 'medium',
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
                'gap_size_pct': round(gap_size / c0['h'] * 100, 4),
                'ts': c1['ts'],
            })
        gap_size = c0['l'] - c2['h']
        if gap_size > 0:
            fvgs.append({
                'idx': i, 'type': 'BEARISH_FVG',
                'gap_top': c0['l'], 'gap_bottom': c2['h'],
                'gap_size_pct': round(gap_size / c0['l'] * 100, 4),
                'ts': c1['ts'],
            })
    return fvgs

# ─── Simulation Engine ─────────────────────────────────────────────────

def to_pips(price, pair):
    """Convert price to pips based on pair convention."""
    pip_val = PIP_VALUES.get(pair, 0.0001)
    return round(price / pip_val, 1)

def evaluate_pattern(pattern, candles, pair, min_sl_pips=5, tp_multiplier=3, lookahead=20):
    """
    Evaluate a single pattern: determine entry, SL, TP, and check outcome.
    Returns dict with WIN/LOSS/NO_DECISION.
    """
    pip_val = PIP_VALUES.get(pair, 0.0001)
    idx = pattern['idx']
    
    # Determine direction and entry
    ptype = pattern['type']
    if 'BULLISH' in ptype or 'BULL' in ptype.upper():
        direction = 'LONG'
    else:
        direction = 'SHORT'
    
    # Calculate gap size in pips for SL determination
    if 'FVG' in ptype:
        gap = abs(pattern['gap_top'] - pattern['gap_bottom'])
        # For FVG, entry is at gap close
        if direction == 'LONG':
            entry_price = pattern['gap_bottom']  # Buy at bottom of gap
        else:
            entry_price = pattern['gap_top']  # Sell at top of gap
    else:
        # BOS/CHoCH: find nearest swing low/high for gap
        entry_price = pattern.get('price', candles[idx]['c'])
        if direction == 'LONG':
            # Find nearest swing low within last 5 candles as gap proxy
            recent_lows = []
            for j in range(max(0, idx-5), idx+1):
                if j < len(candles):
                    recent_lows.append(candles[j]['l'])
            if recent_lows:
                gap = entry_price - min(recent_lows)
            else:
                gap = pip_val * 10
        else:
            recent_highs = []
            for j in range(max(0, idx-5), idx+1):
                if j < len(candles):
                    recent_highs.append(candles[j]['h'])
            if recent_highs:
                gap = max(recent_highs) - entry_price
            else:
                gap = pip_val * 10
    
    gap_pips = to_pips(gap, pair)
    sl_pips = max(gap_pips, min_sl_pips)
    tp_pips = sl_pips * tp_multiplier
    
    if direction == 'LONG':
        sl_price = entry_price - (sl_pips * pip_val)
        tp_price = entry_price + (tp_pips * pip_val)
    else:
        sl_price = entry_price + (sl_pips * pip_val)
        tp_price = entry_price - (tp_pips * pip_val)
    
    # Check outcome: look ahead up to lookahead candles
    outcome = 'NO_DECISION'
    rr_achieved = 0.0
    
    end_idx = min(idx + lookahead + 1, len(candles))
    for j in range(idx + 1, end_idx):
        c = candles[j]
        if direction == 'LONG':
            if c['l'] <= sl_price:
                outcome = 'LOSS'
                rr_achieved = -1.0
                break
            if c['h'] >= tp_price:
                outcome = 'WIN'
                rr_achieved = float(tp_multiplier)
                break
        else:  # SHORT
            if c['h'] >= sl_price:
                outcome = 'LOSS'
                rr_achieved = -1.0
                break
            if c['l'] <= tp_price:
                outcome = 'WIN'
                rr_achieved = float(tp_multiplier)
                break
    
    # Format timestamp
    from datetime import datetime as dt, timezone as tz
    ts_str = dt.fromtimestamp(candles[idx]['ts'], tz=tz.utc).strftime('%Y-%m-%d %H:%M')
    
    return {
        'pattern_type': ptype,
        'timestamp': ts_str,
        'candle_index': idx,
        'entry_price': round(entry_price, 5),
        'direction': direction,
        'sl_price': round(sl_price, 5),
        'tp_price': round(tp_price, 5),
        'sl_pips': sl_pips,
        'tp_pips': tp_pips,
        'gap_size_pips': gap_pips,
        'outcome': outcome,
        'rr_achieved': rr_achieved,
        'strength': pattern.get('strength', 0.5),
    }

def run_simulation(pair):
    """Run full simulation on a pair and return results dict."""
    print(f"\n{'='*60}")
    print(f"  Running FVG simulation on {pair} M15...")
    print(f"{'='*60}")
    
    candles = download_pair(pair, days=30, interval='15m')
    if not candles:
        print(f"  No data for {pair}")
        return None
    
    print(f"  Downloaded {len(candles)} candles")
    
    # Detect patterns
    highs, lows = find_swings(candles)
    print(f"  Swings: {len(highs)}H / {len(lows)}L")
    
    bos = find_structure(candles, highs, lows)
    chochs = find_choch(candles, highs, lows)
    fvgs = find_fvg(candles)
    
    all_patterns = bos + chochs + fvgs
    print(f"  Patterns: {len(bos)} BOS + {len(chochs)} CHoCH + {len(fvgs)} FVG = {len(all_patterns)} total")
    
    # Evaluate each pattern
    results = []
    for p in all_patterns:
        r = evaluate_pattern(p, candles, pair)
        results.append(r)
    
    # Summarize
    wins = [r for r in results if r['outcome'] == 'WIN']
    losses = [r for r in results if r['outcome'] == 'LOSS']
    no_dec = [r for r in results if r['outcome'] == 'NO_DECISION']
    
    total_evaluable = len(wins) + len(losses)
    win_rate = round(len(wins) / total_evaluable * 100, 2) if total_evaluable > 0 else 0
    profit_factor = round(len(wins) * 3 / len(losses), 4) if len(losses) > 0 else float('inf')
    
    # By pattern type
    by_type = {}
    for r in results:
        pt = r['pattern_type']
        if pt not in by_type:
            by_type[pt] = {'total': 0, 'wins': 0, 'losses': 0, 'no_decision': 0}
        by_type[pt]['total'] += 1
        if r['outcome'] == 'WIN':
            by_type[pt]['wins'] += 1
        elif r['outcome'] == 'LOSS':
            by_type[pt]['losses'] += 1
        else:
            by_type[pt]['no_decision'] += 1
    
    for pt, stats in by_type.items():
        ev = stats['wins'] + stats['losses']
        stats['win_rate_pct'] = round(stats['wins'] / ev * 100, 2) if ev > 0 else 0.0
        stats['profit_factor'] = round(stats['wins'] * 3 / stats['losses'], 4) if stats['losses'] > 0 else float('inf')
    
    # Best/worst
    best = max([r for r in results if r['outcome'] != 'NO_DECISION'], 
               key=lambda x: x['rr_achieved'], default=None)
    worst = min([r for r in results if r['outcome'] != 'NO_DECISION'], 
                key=lambda x: x['rr_achieved'], default=None)
    
    summary = {
        'simulation_metadata': {
            'pair': pair,
            'timeframe': 'M15',
            'data_period': '30d',
            'total_candles': len(candles),
            'min_sl_pips': 5,
            'tp_multiplier': 3,
            'lookahead_candles': 20,
            'simulation_ts': datetime.now(timezone.utc).isoformat(),
        },
        'summary': {
            'total_patterns_detected': len(all_patterns),
            'total_evaluated': len(results),
            'wins': len(wins),
            'losses': len(losses),
            'no_decision': len(no_dec),
            'win_rate_pct': win_rate,
            'profit_factor': profit_factor,
        },
        'by_pattern_type': by_type,
        'best_pattern': {
            'type': best['pattern_type'] if best else 'N/A',
            'entry': best['entry_price'] if best else 0,
            'direction': best['direction'] if best else 'N/A',
            'timestamp': best['timestamp'] if best else 'N/A',
            'outcome': best['outcome'] if best else 'N/A',
            'rr_achieved': best['rr_achieved'] if best else 0,
        },
        'worst_pattern': {
            'type': worst['pattern_type'] if worst else 'N/A',
            'entry': worst['entry_price'] if worst else 0,
            'direction': worst['direction'] if worst else 'N/A',
            'timestamp': worst['timestamp'] if worst else 'N/A',
            'outcome': worst['outcome'] if worst else 'N/A',
            'rr_achieved': worst['rr_achieved'] if worst else 0,
        },
        'all_results': results,
    }
    
    return summary

# ─── Main ───────────────────────────────────────────────────────────────

def main():
    pairs_to_run = ['AUDUSD', 'NZDUSD', 'USDJPY']
    
    # Load existing results
    existing = {}
    for pair in ['EURUSD', 'GBPUSD']:
        fname = f"hermes_{pair.lower()}_analysis.json" if pair == 'EURUSD' else f"brain_{pair.lower()}_analysis.json"
        fpath = SIM_DIR / fname
        if fpath.exists():
            try:
                existing[pair] = json.loads(fpath.read_text())
                s = existing[pair]['summary']
                print(f"Loaded existing {pair}: WR={s['win_rate_pct']}%, PF={s['profit_factor']}")
            except Exception as e:
                print(f"Failed to load {pair}: {e}")
    
    # Run simulations for new pairs
    new_results = {}
    for pair in pairs_to_run:
        result = run_simulation(pair)
        if result:
            new_results[pair] = result
            # Save individual result
            out_path = SIM_DIR / f"{pair.lower()}_analysis.json"
            out_path.write_text(json.dumps(result, indent=2, default=str))
            print(f"\n  Saved: {out_path}")
    
    # ─── Cross-Pair Comparison ────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  CROSS-PAIR COMPARISON (FVG Trading)")
    print(f"{'='*60}")
    
    all_pairs = {**existing, **new_results}
    
    print(f"\n{'Pair':<10} {'Total':>6} {'Wins':>6} {'Loss':>6} {'NoDec':>6} {'WR%':>8} {'PF':>8} {'Candles':>8}")
    print(f"{'-'*10} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*8} {'-'*8} {'-'*8}")
    
    for pair in ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDJPY']:
        if pair not in all_pairs:
            print(f"{pair:<10} {'N/A':>6}")
            continue
        r = all_pairs[pair]
        s = r['summary']
        candles = r['simulation_metadata']['total_candles']
        print(f"{pair:<10} {s['total_patterns_detected']:>6} {s['wins']:>6} {s['losses']:>6} {s['no_decision']:>6} {s['win_rate_pct']:>8.2f} {s['profit_factor']:>8.4f} {candles:>8}")
    
    # ─── FVG-Specific Comparison ─────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  FVG-ONLY COMPARISON")
    print(f"{'='*60}")
    
    print(f"\n{'Pair':<10} {'BULL FVG':>10} {'WR%':>8} {'PF':>8}  | {'BEAR FVG':>10} {'WR%':>8} {'PF':>8}  | {'Combined WR%':>12}")
    print(f"{'-'*10} {'-'*10} {'-'*8} {'-'*8}  | {'-'*10} {'-'*8} {'-'*8}  | {'-'*12}")
    
    ranking = []
    for pair in ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDJPY']:
        if pair not in all_pairs:
            continue
        r = all_pairs[pair]
        by_type = r.get('by_pattern_type', {})
        bull = by_type.get('BULLISH_FVG', {})
        bear = by_type.get('BEARISH_FVG', {})
        
        bull_total = bull.get('total', 0)
        bear_total = bear.get('total', 0)
        bull_wr = bull.get('win_rate_pct', 0)
        bear_wr = bear.get('win_rate_pct', 0)
        bull_pf = bull.get('profit_factor', 0)
        bear_pf = bear.get('profit_factor', 0)
        
        fvg_wins = bull.get('wins', 0) + bear.get('wins', 0)
        fvg_losses = bull.get('losses', 0) + bear.get('losses', 0)
        fvg_total_ev = fvg_wins + fvg_losses
        combined_wr = round(fvg_wins / fvg_total_ev * 100, 2) if fvg_total_ev > 0 else 0
        
        print(f"{pair:<10} {bull_total:>10} {bull_wr:>8.2f} {bull_pf:>8.4f}  | {bear_total:>10} {bear_wr:>8.2f} {bear_pf:>8.4f}  | {combined_wr:>12.2f}")
        
        ranking.append((pair, combined_wr, fvg_total_ev, fvg_wins, fvg_losses))
    
    # ─── Ranking ─────────────────────────────────────────────────────
    ranking.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n{'='*60}")
    print(f"  FVG TRADING RANKING (Best to Worst)")
    print(f"{'='*60}")
    print(f"\n{'Rank':<6} {'Pair':<10} {'Combined WR%':>14} {'Evaluable':>10} {'Wins':>6} {'Losses':>8}")
    print(f"{'-'*6} {'-'*10} {'-'*14} {'-'*10} {'-'*6} {'-'*8}")
    
    for i, (pair, wr, ev, wins, losses) in enumerate(ranking, 1):
        star = " ★" if i == 1 else ""
        print(f"{i:<6} {pair:<10} {wr:>14.2f}{star:<2} {ev:>10} {wins:>6} {losses:>8}")
    
    # Save comparison
    comparison = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'methodology': 'FVG pattern detection, RR 3:1, SL=max(gap,5 pips), 20-candle lookahead',
        'ranking': [{'rank': i, 'pair': p, 'combined_wr': wr, 'evaluable': ev, 'wins': w, 'losses': l}
                    for i, (p, wr, ev, w, l) in enumerate(ranking, 1)],
        'all_pairs_summary': {
            pair: all_pairs[pair]['summary'] for pair in all_pairs
        }
    }
    
    comp_path = SIM_DIR / 'fvg_comparison_all_5_pairs.json'
    comp_path.write_text(json.dumps(comparison, indent=2, default=str))
    print(f"\n  Comparison saved: {comp_path}")
    
    # Print final recommendation
    if ranking:
        best_pair = ranking[0][0]
        print(f"\n{'='*60}")
        print(f"  RECOMMENDATION: {best_pair} is the best pair for FVG trading")
        print(f"  on M15 timeframe with combined WR of {ranking[0][1]:.2f}%")
        print(f"{'='*60}")

if __name__ == '__main__':
    main()
