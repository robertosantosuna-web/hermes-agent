#!/usr/bin/env python3
"""Backtest FVG+CRT multi-TF: M5 + M15 + M30 para 6 pares.
Uso: python3 scripts/backtest_multi_tf.py
     python3 scripts/backtest_multi_tf.py --days 30 --pairs GBP/USD EUR/USD
"""
import yfinance as yf
import argparse
from datetime import datetime, timedelta
from collections import Counter

PAIRS = {
    'GBP/JPY': ('GBPJPY=X', 0.01, [6, 7]),
    'USD/JPY': ('USDJPY=X', 0.01, [15, 16]),
    'EUR/JPY': ('EURJPY=X', 0.01, [11, 15]),
    'GBP/USD': ('GBPUSD=X', 0.0001, [15, 16]),
    'EUR/USD': ('EURUSD=X', 0.0001, [15, 16]),
    'USD/CAD': ('USDCAD=X', 0.0001, [15, 16]),
}
MIN_GAP = 2.0
RR = 3.0
CRT_PCT = 0.7
TIMEFRAMES = ['5m', '15m', '30m']


def detect_fvg(df, pip_val):
    h = df['High'].values.astype(float)
    l = df['Low'].values.astype(float)
    n = len(h)
    signals = []
    for i in range(2, n):
        if l[i] > h[i-2]:
            gap = (l[i] - h[i-2]) / pip_val
            if gap >= MIN_GAP:
                signals.append({
                    'type': 'BUY', 'entry': round(l[i], 5),
                    'gap': round(gap, 1), 'idx': i,
                    'hour': df.index[i].hour, 'date': df.index[i].date()
                })
        if h[i] < l[i-2]:
            gap = (l[i-2] - h[i]) / pip_val
            if gap >= MIN_GAP:
                signals.append({
                    'type': 'SELL', 'entry': round(h[i], 5),
                    'gap': round(gap, 1), 'idx': i,
                    'hour': df.index[i].hour, 'date': df.index[i].date()
                })
    return signals


def is_crt(df, idx):
    if idx < 20:
        return False
    rng = abs(float(df.iloc[idx]['High']) - float(df.iloc[idx]['Low']))
    recent = [abs(float(df.iloc[i]['High']) - float(df.iloc[i]['Low']))
              for i in range(idx - 19, idx + 1)]
    return rng >= sorted(recent)[int(len(recent) * CRT_PCT)]


def crt_ok(df, idx):
    if idx + 1 >= len(df):
        return False
    h1, l1 = float(df.iloc[idx]['High']), float(df.iloc[idx]['Low'])
    c2 = float(df.iloc[idx + 1]['Close'])
    return l1 <= c2 <= h1


def simulate(df, idx, direction, entry, gap, pip_val):
    sl_pips = max(gap, 2.0)
    tp_pips = sl_pips * RR
    if direction == 'BUY':
        sl = entry - sl_pips * pip_val
        tp = entry + tp_pips * pip_val
    else:
        sl = entry + sl_pips * pip_val
        tp = entry - tp_pips * pip_val
    for i in range(idx + 1, len(df)):
        hi, lo = float(df.iloc[i]['High']), float(df.iloc[i]['Low'])
        if direction == 'BUY':
            if hi >= tp:
                return 'WIN', tp_pips
            if lo <= sl:
                return 'LOSS', -sl_pips
        else:
            if lo <= tp:
                return 'WIN', tp_pips
            if hi >= sl:
                return 'LOSS', -sl_pips
    return 'OPEN', 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=59)
    parser.add_argument('--pairs', nargs='*')
    parser.add_argument('--gap', type=float, default=MIN_GAP)
    parser.add_argument('--no-killzone', action='store_true')
    args = parser.parse_args()

    active_pairs = {k: v for k, v in PAIRS.items()
                    if not args.pairs or k in args.pairs}
    end = datetime.now()
    start = end - timedelta(days=args.days)

    print(f"BACKTEST {args.days}D — FVG+CRT — gap>={args.gap}p — CRT>{int(CRT_PCT*100)}% — RR 3:1")
    print("=" * 90)
    header = f"{'Par':10s}"
    for tf in TIMEFRAMES:
        header += f" {'T ' + tf:>8s} {'WR':>6s} {'PnL':>8s}"
    print(header)
    print("-" * 90)

    grand = {tf: {'t': 0, 'w': 0, 'l': 0, 'pnl': 0} for tf in TIMEFRAMES}

    for pair, (sym, pip, kz) in active_pairs.items():
        row = [pair]
        for tf in TIMEFRAMES:
            df = yf.Ticker(sym).history(start=start, end=end, interval=tf)
            if len(df) < 60:
                row.extend(['ERR', 'ERR', 'ERR'])
                continue
            sigs = detect_fvg(df, pip)
            sigs = [s for s in sigs if is_crt(df, s['idx']) and crt_ok(df, s['idx'])]
            t = len(sigs)
            w = l = pnl = 0
            for s in sigs:
                res, pp = simulate(df, s['idx'], s['type'], s['entry'], s['gap'], pip)
                if res == 'OPEN':
                    t -= 1
                    continue
                if res == 'WIN':
                    w += 1
                else:
                    l += 1
                pnl += pp
            wr = round(w / t * 100, 1) if t else 0
            row.extend([f"{t}T", f"{wr}%", f"{pnl:+}p"])
            grand[tf]['t'] += t
            grand[tf]['w'] += w
            grand[tf]['l'] += l
            grand[tf]['pnl'] += pnl
        print(f"{row[0]:10s} {'  '.join(row[1:])}")

    print("-" * 90)
    total_row = ["TOTAL"]
    for tf in TIMEFRAMES:
        g = grand[tf]
        wr = round(g['w'] / g['t'] * 100, 1) if g['t'] else 0
        monthly = round(g['t'] / args.days * 22)
        total_row.extend([f"{g['t']}T", f"{wr}%", f"{g['pnl']:+}p"])
    print(f"{total_row[0]:10s} {'  '.join(total_row[1:])}")

    print()
    for tf in TIMEFRAMES:
        g = grand[tf]
        wr = round(g['w'] / g['t'] * 100, 1) if g['t'] else 0
        exp = round(wr / 100 * 3 - (1 - wr / 100), 2) if g['t'] else 0
        monthly = round(g['t'] / args.days * 22)
        print(f"  {tf}: {g['t']}T WR={wr}% PnL={g['pnl']:+}p Exp={exp:+.2f}R ~{monthly}T/mês")
    print("=" * 90)
