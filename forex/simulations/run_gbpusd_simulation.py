#!/usr/bin/env python3
"""GBPUSD M15 Pattern Simulation — CHoCH, FVG, BOS with WIN/LOSS analysis."""

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Add scripts dir to path for chart_pattern_study imports
HERMES = Path(os.path.expanduser('~/.hermes'))
sys.path.insert(0, str(HERMES / 'scripts'))

from chart_pattern_study import (
    find_swings, find_choch, find_fvg, find_structure
)

PIP = 0.0001  # 1 pip for GBPUSD
MIN_SL_PIPS = 5  # minimum SL in pips
MIN_SL = MIN_SL_PIPS * PIP  # 0.0005
TP_MULTIPLIER = 3  # TP = 3x SL
LOOKAHEAD = 20  # candles to check after pattern


def download_pair_m15(pair, days=30):
    """Download M15 candles from Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{pair}=X?range={days}d&interval=15m"
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
        print(f"Download error: {e}")
        return []


def get_pattern_entry(pattern, candles, highs, lows):
    """
    Determine entry price, direction, and gap_size for a pattern.
    Returns dict with: entry, direction, gap_size, sl, tp
    """
    ptype = pattern['type']
    entry = None
    direction = None
    gap_size = 0.0  # in price units

    if ptype == 'BULLISH_BOS':
        entry = pattern['price']
        direction = 'LONG'
        # Gap = distance to nearest prior swing low
        prior_lows = [l for l in lows if l['idx'] < pattern['idx']]
        if prior_lows:
            gap_size = abs(entry - prior_lows[-1]['price'])
        else:
            gap_size = 0

    elif ptype == 'BEARISH_BOS':
        entry = pattern['price']
        direction = 'SHORT'
        prior_highs = [h for h in highs if h['idx'] < pattern['idx']]
        if prior_highs:
            gap_size = abs(prior_highs[-1]['price'] - entry)
        else:
            gap_size = 0

    elif ptype == 'BULLISH_CHOCH':
        entry = pattern['price']
        direction = 'LONG'
        gap_size = abs(entry - pattern.get('swept_level', entry))

    elif ptype == 'BEARISH_CHOCH':
        entry = pattern['price']
        direction = 'SHORT'
        gap_size = abs(pattern.get('swept_level', entry) - entry)

    elif ptype == 'BULLISH_FVG':
        entry = pattern['gap_bottom']  # enter at bottom of gap
        direction = 'LONG'
        gap_size = pattern['gap_top'] - pattern['gap_bottom']

    elif ptype == 'BEARISH_FVG':
        entry = pattern['gap_top']  # enter at top of gap
        direction = 'SHORT'
        gap_size = pattern['gap_top'] - pattern['gap_bottom']

    if entry is None:
        return None

    # SL = max(gap_size, MIN_SL)
    sl_distance = max(gap_size, MIN_SL)
    tp_distance = sl_distance * TP_MULTIPLIER

    if direction == 'LONG':
        sl_price = entry - sl_distance
        tp_price = entry + tp_distance
    else:
        sl_price = entry + sl_distance
        tp_price = entry - tp_distance

    return {
        'entry': round(entry, 5),
        'direction': direction,
        'gap_size': round(gap_size, 5),
        'sl_distance': round(sl_distance, 5),
        'tp_distance': round(tp_distance, 5),
        'sl_price': round(sl_price, 5),
        'tp_price': round(tp_price, 5),
        'sl_pips': round(sl_distance / PIP, 1),
        'tp_pips': round(tp_distance / PIP, 1),
    }


def evaluate_outcome(candles, pattern_idx, entry_info):
    """
    Check if TP or SL is hit first within LOOKAHEAD candles after pattern_idx.
    Returns 'WIN', 'LOSS', or 'NO_DECISION'.
    """
    sl_price = entry_info['sl_price']
    tp_price = entry_info['tp_price']
    direction = entry_info['direction']

    end_idx = min(pattern_idx + LOOKAHEAD + 1, len(candles))
    if pattern_idx + 1 >= end_idx:
        return 'NO_DECISION'

    for i in range(pattern_idx + 1, end_idx):
        c = candles[i]
        if direction == 'LONG':
            if c['h'] >= tp_price:
                return 'WIN'
            if c['l'] <= sl_price:
                return 'LOSS'
        else:
            if c['l'] <= tp_price:
                return 'WIN'
            if c['h'] >= sl_price:
                return 'LOSS'

    return 'NO_DECISION'


def compute_rr_achieved(outcome, entry_info):
    """Return the RR ratio achieved (3 for full WIN, -1 for LOSS, 0 for no decision)."""
    if outcome == 'WIN':
        return TP_MULTIPLIER  # 3.0
    elif outcome == 'LOSS':
        return -1.0
    else:
        return 0.0


def main():
    print("=" * 60)
    print("GBPUSD M15 Pattern Simulation")
    print("=" * 60)

    # Download data
    print("\n[1/4] Downloading GBPUSD M15 data (30 days)...")
    candles = download_pair_m15('GBPUSD', 30)
    print(f"  Downloaded {len(candles)} candles")
    if not candles:
        print("  ERROR: No data downloaded")
        return

    # Detect swings
    print("\n[2/4] Detecting swings...")
    highs, lows = find_swings(candles)
    print(f"  Swing highs: {len(highs)}, Swing lows: {len(lows)}")

    # Detect patterns
    print("\n[3/4] Detecting patterns...")
    bos_patterns = find_structure(candles, highs, lows)
    choch_patterns = find_choch(candles, highs, lows)
    fvg_patterns = find_fvg(candles)

    print(f"  BOS:    {len(bos_patterns)}")
    print(f"  CHoCH:  {len(choch_patterns)}")
    print(f"  FVG:    {len(fvg_patterns)}")

    all_patterns = []
    all_patterns.extend(bos_patterns)
    all_patterns.extend(choch_patterns)
    all_patterns.extend(fvg_patterns)

    print(f"  Total patterns detected: {len(all_patterns)}")

    # Evaluate each pattern
    print(f"\n[4/4] Evaluating {len(all_patterns)} patterns...")
    results = []
    wins = 0
    losses = 0
    no_decision = 0

    for p in all_patterns:
        entry_info = get_pattern_entry(p, candles, highs, lows)
        if entry_info is None:
            continue

        outcome = evaluate_outcome(candles, p['idx'], entry_info)
        rr = compute_rr_achieved(outcome, entry_info)

        if outcome == 'WIN':
            wins += 1
        elif outcome == 'LOSS':
            losses += 1
        else:
            no_decision += 1

        ts_str = datetime.fromtimestamp(p['ts'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M')

        result = {
            'pattern_type': p['type'],
            'timestamp': ts_str,
            'candle_index': p['idx'],
            'entry_price': entry_info['entry'],
            'direction': entry_info['direction'],
            'sl_price': entry_info['sl_price'],
            'tp_price': entry_info['tp_price'],
            'sl_pips': entry_info['sl_pips'],
            'tp_pips': entry_info['tp_pips'],
            'gap_size_pips': round(entry_info['gap_size'] / PIP, 1),
            'outcome': outcome,
            'rr_achieved': rr,
        }

        # Add pattern-specific fields
        if 'swept_level' in p:
            result['swept_level'] = p['swept_level']
        if 'quality' in p:
            result['quality'] = p['quality']
        if 'strength' in p:
            result['strength'] = p['strength']
        if 'gap_size_pct' in p:
            result['gap_size_pct'] = p['gap_size_pct']

        results.append(result)

    # Compute metrics
    total_evaluated = wins + losses + no_decision
    wr = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    profit_factor = (wins * TP_MULTIPLIER) / losses if losses > 0 else float('inf')

    # Find best and worst patterns
    decided = [r for r in results if r['outcome'] != 'NO_DECISION']
    best = max(decided, key=lambda r: r['rr_achieved']) if decided else None
    worst = min(decided, key=lambda r: r['rr_achieved']) if decided else None

    # Summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"  Total patterns detected:  {len(all_patterns)}")
    print(f"  Total patterns evaluated: {total_evaluated}")
    print(f"  WINs:                     {wins}")
    print(f"  LOSSes:                   {losses}")
    print(f"  No Decision (flat):       {no_decision}")
    print(f"  Win Rate (WR%):           {wr:.1f}%")
    print(f"  Profit Factor:            {profit_factor:.2f}")
    print()

    # Breakdown by type
    by_type = {}
    for r in results:
        t = r['pattern_type']
        if t not in by_type:
            by_type[t] = {'total': 0, 'wins': 0, 'losses': 0, 'no_decision': 0}
        by_type[t]['total'] += 1
        if r['outcome'] == 'WIN':
            by_type[t]['wins'] += 1
        elif r['outcome'] == 'LOSS':
            by_type[t]['losses'] += 1
        else:
            by_type[t]['no_decision'] += 1

    print("  By Pattern Type:")
    for t, stats in sorted(by_type.items()):
        wr_t = (stats['wins'] / (stats['wins'] + stats['losses']) * 100) if (stats['wins'] + stats['losses']) > 0 else 0
        pf_t = (stats['wins'] * TP_MULTIPLIER) / stats['losses'] if stats['losses'] > 0 else float('inf')
        print(f"    {t:20s}  total={stats['total']:3d}  W={stats['wins']:3d}  L={stats['losses']:3d}  ND={stats['no_decision']:3d}  WR={wr_t:5.1f}%  PF={pf_t:.2f}")

    if best:
        print(f"\n  Best pattern:  {best['pattern_type']} @ {best['entry_price']} ({best['timestamp']}) -> {best['outcome']} RR={best['rr_achieved']:.1f}")
    if worst:
        print(f"  Worst pattern: {worst['pattern_type']} @ {worst['entry_price']} ({worst['timestamp']}) -> {worst['outcome']} RR={worst['rr_achieved']:.1f}")

    # Build final output
    output = {
        'simulation_metadata': {
            'pair': 'GBPUSD',
            'timeframe': 'M15',
            'data_period': '30d',
            'total_candles': len(candles),
            'min_sl_pips': MIN_SL_PIPS,
            'tp_multiplier': TP_MULTIPLIER,
            'lookahead_candles': LOOKAHEAD,
            'simulation_ts': datetime.now(timezone.utc).isoformat(),
        },
        'summary': {
            'total_patterns_detected': len(all_patterns),
            'total_evaluated': total_evaluated,
            'wins': wins,
            'losses': losses,
            'no_decision': no_decision,
            'win_rate_pct': round(wr, 2),
            'profit_factor': round(profit_factor, 4) if profit_factor != float('inf') else 'inf',
        },
        'by_pattern_type': {
            t: {
                'total': stats['total'],
                'wins': stats['wins'],
                'losses': stats['losses'],
                'no_decision': stats['no_decision'],
                'win_rate_pct': round(
                    (stats['wins'] / (stats['wins'] + stats['losses']) * 100)
                    if (stats['wins'] + stats['losses']) > 0 else 0, 2
                ),
                'profit_factor': round(
                    (stats['wins'] * TP_MULTIPLIER) / stats['losses']
                    if stats['losses'] > 0 else float('inf'), 4
                ),
            }
            for t, stats in by_type.items()
        },
        'best_pattern': {
            'type': best['pattern_type'],
            'entry': best['entry_price'],
            'direction': best['direction'],
            'timestamp': best['timestamp'],
            'outcome': best['outcome'],
            'rr_achieved': best['rr_achieved'],
        } if best else None,
        'worst_pattern': {
            'type': worst['pattern_type'],
            'entry': worst['entry_price'],
            'direction': worst['direction'],
            'timestamp': worst['timestamp'],
            'outcome': worst['outcome'],
            'rr_achieved': worst['rr_achieved'],
        } if worst else None,
        'all_results': results,
    }

    # Save
    output_path = HERMES / 'forex' / 'simulations' / 'brain_gbpusd_analysis.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\n  Results saved to: {output_path}")
    print("=" * 60)


if __name__ == '__main__':
    main()
