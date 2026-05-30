#!/usr/bin/env python3
"""
Chart Analyzer — Gera análise ESTRUTURADA (JSON) para o agente consumir.
Multi-timeframe, FVG scoring, CRT, swing structure, bias detection.

Uso:
  python3 chart_analyzer.py GBPJPY          # Análise completa M15+M30+H1
  python3 chart_analyzer.py EURUSD --json    # JSON puro
  python3 chart_analyzer.py --all            # Todos os 6 pares
"""

import json, sys
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
import numpy as np

HERMES = Path.home() / ".hermes"
OUTPUT_DIR = HERMES / "forex" / "analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

from tvDatafeed import TvDatafeed, Interval as TVInterval

TIMEFRAMES = {
    'M5':  TVInterval.in_5_minute,
    'M15': TVInterval.in_15_minute,
    'M30': TVInterval.in_30_minute,
    'H1':  TVInterval.in_1_hour,
    'H4':  TVInterval.in_4_hour,
}

PIP_SIZES = {
    'GBPJPY': 0.01, 'USDJPY': 0.01, 'EURJPY': 0.01,
    'EURUSD': 0.0001, 'GBPUSD': 0.0001, 'USDCAD': 0.0001,
    'XAUUSD': 0.01,
}

PAIRS = ['GBPJPY', 'USDJPY', 'EURUSD', 'GBPUSD', 'EURJPY', 'USDCAD']


def fetch_tv(symbol, interval, n_bars=200):
    """TradingView data feed."""
    tv = TvDatafeed()
    exchange = 'OANDA' if symbol == 'XAUUSD' else 'FX'
    tv_interval = TIMEFRAMES.get(interval, TVInterval.in_15_minute)
    df = tv.get_hist(symbol=symbol, exchange=exchange, interval=tv_interval, n_bars=n_bars)
    if df is None or len(df) < 20:
        return None
    return df


def detect_fvgs(df, pip_size, min_gap=2.0):
    """FVG detection with scoring."""
    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    n = len(closes)
    fvgs = []
    
    for i in range(2, n):
        gap_up = lows[i] - highs[i-2]
        gap_down = lows[i-2] - highs[i]
        gap_up_pips = gap_up / pip_size
        gap_down_pips = gap_down / pip_size
        
        if gap_up_pips >= min_gap:
            age_penalty = (n - i) / n * 0.3
            gap_bonus = min(gap_up_pips / 10, 0.5)
            score = 1.0 - age_penalty + gap_bonus
            
            fvgs.append({
                'index': int(i), 'type': 'bullish',
                'top': float(highs[i-2]), 'bottom': float(lows[i]),
                'gap_pips': round(float(gap_up_pips), 1),
                'score': round(min(float(score), 1.0), 2),
                'age_bars': int(n - i),
            })
        
        if gap_down_pips >= min_gap:
            age_penalty = (n - i) / n * 0.3
            gap_bonus = min(gap_down_pips / 10, 0.5)
            score = 1.0 - age_penalty + gap_bonus
            
            fvgs.append({
                'index': int(i), 'type': 'bearish',
                'top': float(highs[i]), 'bottom': float(lows[i-2]),
                'gap_pips': round(float(gap_down_pips), 1),
                'score': round(min(float(score), 1.0), 2),
                'age_bars': int(n - i),
            })
    
    return sorted(fvgs, key=lambda f: f['score'], reverse=True)


def detect_swings(df):
    """Swing highs/lows with structure analysis."""
    highs = df['high'].values
    lows = df['low'].values
    n = len(highs)
    swings = []
    
    for i in range(3, n - 3):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            swings.append({'index': int(i), 'type': 'high', 'price': float(highs[i])})
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            swings.append({'index': int(i), 'type': 'low', 'price': float(lows[i])})
    
    # Analyze structure (last 10 swings)
    recent = swings[-10:]
    high_prices = [s['price'] for s in recent if s['type'] == 'high']
    low_prices = [s['price'] for s in recent if s['type'] == 'low']
    
    structure = 'RANGING'
    if len(high_prices) >= 2 and len(low_prices) >= 2:
        hh = high_prices[-1] > high_prices[-2]  # Higher high
        hl = low_prices[-1] > low_prices[-2]     # Higher low
        lh = high_prices[-1] < high_prices[-2]   # Lower high
        ll = low_prices[-1] < low_prices[-2]     # Lower low
        
        if hh and hl:
            structure = 'BULLISH_TREND'
        elif lh and ll:
            structure = 'BEARISH_TREND'
        elif hh and ll:
            structure = 'EXPANDING'
        elif lh and hl:
            structure = 'CONTRACTING'
    
    return swings, structure


def check_crt(df, index, window=10):
    """CRT (Candle Range Theory): check if candle range is in top percentile."""
    ranges = (df['high'] - df['low']).values
    start = max(0, index - window)
    current_range = ranges[index]
    pct_rank = np.sum(ranges[start:index+1] <= current_range) / (index - start + 1)
    return round(pct_rank, 2)


def analyze_timeframe(symbol, interval, n_bars=200):
    """Full analysis for one timeframe."""
    df = fetch_tv(symbol, interval, n_bars)
    if df is None:
        return None
    
    pip = PIP_SIZES.get(symbol, 0.0001)
    fvgs = detect_fvgs(df, pip)
    swings, structure = detect_swings(df)
    
    # Current price
    current = float(df['close'].iloc[-1])
    
    # FVG bias: count bullish vs bearish in recent window
    recent_fvgs = [f for f in fvgs if f['age_bars'] <= 50]
    bullish_fvgs = [f for f in recent_fvgs if f['type'] == 'bullish']
    bearish_fvgs = [f for f in recent_fvgs if f['type'] == 'bearish']
    
    fvg_bias = 'NEUTRAL'
    if len(bullish_fvgs) > len(bearish_fvgs) * 1.5:
        fvg_bias = 'BULLISH'
    elif len(bearish_fvgs) > len(bullish_fvgs) * 1.5:
        fvg_bias = 'BEARISH'
    
    # Best FVGs (top 5 by score)
    best_fvgs = fvgs[:5]
    
    # Support/Resistance from recent swings
    recent_swings = swings[-10:]
    supports = sorted([s for s in recent_swings if s['type'] == 'low'], 
                      key=lambda s: s['price'])[-3:]
    resistances = sorted([s for s in recent_swings if s['type'] == 'high'],
                         key=lambda s: s['price'], reverse=True)[-3:]
    
    # CRT check for most recent candle
    crt_value = check_crt(df, len(df) - 3)  # -3 because FVG needs 3 candles
    
    # Generate signal if conditions met
    signals = []
    for f in best_fvgs:
        if f['score'] < 0.5 or f['age_bars'] > 20:
            continue
        
        crt = check_crt(df, f['index'])
        crt_ok = crt >= 0.70
        
        if not crt_ok:
            continue
        
        direction = 'BUY' if f['type'] == 'bullish' else 'SELL'
        entry = current
        sl_pips = max(f['gap_pips'], 15)
        tp_pips = sl_pips * 3.0  # RR 3:1
        
        if direction == 'BUY':
            sl = entry - sl_pips * pip
            tp = entry + tp_pips * pip
        else:
            sl = entry + sl_pips * pip
            tp = entry - tp_pips * pip
        
        score = round(f['score'] * crt * 100)
        
        signals.append({
            'type': 'FVG+CRT',
            'direction': direction,
            'entry': round(entry, 5),
            'sl': round(sl, 5),
            'tp': round(tp, 5),
            'sl_pips': round(sl_pips, 1),
            'tp_pips': round(tp_pips, 1),
            'score': score,
            'gap_pips': f['gap_pips'],
            'crt': crt,
            'fvg_age': f['age_bars'],
        })
    
    # Sort signals by score
    signals = sorted(signals, key=lambda s: s['score'], reverse=True)[:3]
    
    return {
        'symbol': symbol,
        'timeframe': interval,
        'current_price': round(current, 5),
        'candles': len(df),
        'range_pips': round((float(df['high'].max()) - float(df['low'].min())) / pip, 1),
        'swing_structure': structure,
        'fvg_count': len(fvgs),
        'fvg_bias': fvg_bias,
        'bullish_fvgs': len(bullish_fvgs),
        'bearish_fvgs': len(bearish_fvgs),
        'crt_latest': crt_value,
        'levels': {
            'support': [{'price': round(s['price'], 5), 'age': n_bars - s['index']} for s in supports],
            'resistance': [{'price': round(s['price'], 5), 'age': n_bars - s['index']} for s in resistances],
        },
        'signals': signals,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }


def analyze_mtf(symbol):
    """Multi-timeframe analysis: M15 + M30 + H1."""
    results = {}
    for tf in ['M15', 'M30', 'H1']:
        r = analyze_timeframe(symbol, tf)
        if r:
            results[tf] = r
    
    if not results:
        return None
    
    # MTF consensus
    biases = [r['fvg_bias'] for r in results.values()]
    structures = [r['swing_structure'] for r in results.values()]
    
    bias_votes = defaultdict(int)
    for b in biases:
        bias_votes[b] += 1
    
    consensus_bias = max(bias_votes, key=bias_votes.get) if bias_votes else 'NEUTRAL'
    
    # Confidence based on alignment
    alignment = sum(1 for b in biases if b == consensus_bias)
    confidence = round(alignment / len(biases) * 100)
    
    # Best signals across timeframes
    all_signals = []
    for tf, r in results.items():
        for s in r.get('signals', []):
            s['timeframe'] = tf
            all_signals.append(s)
    all_signals = sorted(all_signals, key=lambda s: s['score'], reverse=True)[:5]
    
    return {
        'symbol': symbol,
        'consensus': consensus_bias,
        'confidence': confidence,
        'alignment': f"{alignment}/{len(biases)} timeframes",
        'timeframes': results,
        'combined_signals': all_signals,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }


def format_report(analysis):
    """Formata análise MTF para leitura do agente."""
    if not analysis:
        return "Sem dados."
    
    lines = []
    lines.append(f"\n{'═'*60}")
    lines.append(f"  {analysis['symbol']} — Análise Multi-Timeframe")
    lines.append(f"  Viés: {analysis['consensus']} | Confiança: {analysis['confidence']}% | Alinhamento: {analysis['alignment']}")
    lines.append(f"{'═'*60}")
    
    for tf, r in analysis['timeframes'].items():
        bias_emoji = '🟢' if r['fvg_bias'] == 'BULLISH' else '🔴' if r['fvg_bias'] == 'BEARISH' else '⚪'
        struct_emoji = '📈' if 'BULL' in r['swing_structure'] else '📉' if 'BEAR' in r['swing_structure'] else '↔'
        
        lines.append(f"\n  {tf}: {bias_emoji} {r['fvg_bias']:8s} {struct_emoji} {r['swing_structure']:15s} | "
                     f"{r['fvg_count']} FVGs ({r['bullish_fvgs']}🟢/{r['bearish_fvgs']}🔴) | "
                     f"CRT: {r['crt_latest']:.0%} | Range: {r['range_pips']:.0f}p")
        
        for lvl in r['levels']['support'][:2]:
            lines.append(f"      Suporte: {lvl['price']:.5f} (há {lvl['age']} velas)")
        for lvl in r['levels']['resistance'][:2]:
            lines.append(f"      Resistência: {lvl['price']:.5f} (há {lvl['age']} velas)")
        
        for s in r.get('signals', [])[:2]:
            emoji = '🟢' if s['direction'] == 'BUY' else '🔴'
            lines.append(f"      {emoji} SINAL: {s['direction']} @ {s['entry']:.5f} | "
                         f"SL: {s['sl_pips']:.0f}p | TP: {s['tp_pips']:.0f}p | "
                         f"Score: {s['score']}/100 | CRT: {s['crt']:.0%}")
    
    lines.append(f"\n  Sinais combinados (top 3):")
    for s in analysis['combined_signals'][:3]:
        emoji = '🟢' if s['direction'] == 'BUY' else '🔴'
        lines.append(f"    {emoji} [{s['timeframe']}] {s['direction']} @ {s['entry']:.5f} | "
                     f"Score: {s['score']}/100 | SL: {s['sl_pips']:.0f}p | TP: {s['tp_pips']:.0f}p")
    
    lines.append(f"{'═'*60}\n")
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('symbol', nargs='?', default=None, help='Par (GBPJPY, EURUSD...) ou --all')
    parser.add_argument('--json', action='store_true', help='Output JSON puro')
    parser.add_argument('--all', action='store_true', help='Todos os 6 pares')
    parser.add_argument('--tf', default=None, help='Timeframe único (M15, H1...) ao invés de MTF')
    parser.add_argument('--out', action='store_true', help='Salvar JSON em arquivo')
    args = parser.parse_args()
    
    symbols = PAIRS if args.all else [args.symbol.upper()] if args.symbol else PAIRS
    
    for sym in symbols:
        if args.tf:
            # Single timeframe
            result = analyze_timeframe(sym, args.tf)
        else:
            # Multi-timeframe
            result = analyze_mtf(sym)
        
        if result is None:
            print(f"⚠️ {sym}: sem dados", file=sys.stderr)
            continue
        
        if args.out:
            ts = datetime.now().strftime('%Y%m%d_%H%M')
            out = OUTPUT_DIR / f'{sym}_{args.tf or "MTF"}_{ts}.json'
            out.write_text(json.dumps(result, indent=2, default=str))
            print(f"📁 {out}")
        
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            if args.tf:
                # Single TF: show key info
                r = result
                print(f"\n{sym} {args.tf}: {r['fvg_bias']} | {r['swing_structure']} | "
                      f"{r['fvg_count']} FVGs | CRT:{r['crt_latest']:.0%}")
                for s in r.get('signals', [])[:3]:
                    print(f"  {'🟢' if s['direction']=='BUY' else '🔴'} {s['direction']} | "
                          f"Score:{s['score']}/100 | SL:{s['sl_pips']:.0f}p TP:{s['tp_pips']:.0f}p")
            else:
                print(format_report(result))


if __name__ == '__main__':
    main()
