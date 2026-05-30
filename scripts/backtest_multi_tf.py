#!/usr/bin/env python3
"""Backtest multi-TF: M5 + M15 para 5 pares com CRT + gap>=2p + RR 3:1"""
import yfinance as yf
from datetime import datetime, timedelta

PAIRS = {
    'GBP/USD': ('GBPUSD=X', 0.0001, [15, 16]),
    'USD/JPY': ('USDJPY=X', 0.01, [15, 16]),
    'EUR/JPY': ('EURJPY=X', 0.01, [11, 15]),
    'USD/CAD': ('USDCAD=X', 0.0001, [15, 16]),
    'GBP/JPY': ('GBPJPY=X', 0.01, [6, 7]),
}
MIN_FVG_PIPS = 2.0
RR = 3.0
CRT_PCT = 0.7
DAYS = 59


def detect_signals(df, pip_val):
    h = df['High'].values.astype(float)
    l = df['Low'].values.astype(float)
    c = df['Close'].values.astype(float)
    n = len(h)
    signals = []
    for start in range(0, n - 60, 30):
        end = min(start + 60, n)
        sh, sl = [], []
        for i in range(start + 2, end - 2):
            if h[i] > h[i-1] and h[i] > h[i-2] and h[i] > h[i+1] and h[i] > h[i+2]:
                sh.append((i, h[i]))
            if l[i] < l[i-1] and l[i] < l[i-2] and l[i] < l[i+1] and l[i] < l[i+2]:
                sl.append((i, l[i]))
        if sh:
            si, sv = sh[-1]
            for i in range(si + 1, end):
                if c[i] > sv:
                    for j in range(max(start, i-3), i):
                        if j + 1 < end and l[j+1] > h[j]:
                            gap = (l[j+1] - h[j]) / pip_val
                            if gap >= MIN_FVG_PIPS:
                                signals.append({
                                    'type': 'BUY', 'entry': round(l[j+1], 5),
                                    'fvg_pips': round(gap, 1), 'idx': i,
                                    'hour': df.index[j+1].hour
                                })
                                break
                    break
        if sl:
            si, sv = sl[-1]
            for i in range(si + 1, end):
                if c[i] < sv:
                    for j in range(max(start, i-3), i):
                        if j + 1 < end and h[j+1] < l[j]:
                            gap = (l[j] - h[j+1]) / pip_val
                            if gap >= MIN_FVG_PIPS:
                                signals.append({
                                    'type': 'SELL', 'entry': round(h[j+1], 5),
                                    'fvg_pips': round(gap, 1), 'idx': i,
                                    'hour': df.index[j+1].hour
                                })
                                break
                    break
    seen = set()
    uniq = []
    for s in signals:
        k = (s['idx'], s['type'])
        if k not in seen:
            seen.add(k)
            uniq.append(s)
    return uniq


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
    c2 = float(df.iloc[idx+1]['Close'])
    return l1 <= c2 <= h1


def simulate(df, idx, direction, entry, fvg_pips, pip_val):
    sl_pips = max(fvg_pips, 2.0)
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


end = datetime.now()
start = end - timedelta(days=DAYS)

print(f"BACKTEST {DAYS}D — 5 pares — gap>={MIN_FVG_PIPS}p — CRT>={int(CRT_PCT*100)}% — RR 3:1")
print("=" * 75)
print(f"{'Par':10s} {'M5 Trades':>10s} {'M5 WR':>7s} {'M5 PnL':>9s} | {'M15 Trades':>10s} {'M15 WR':>7s} {'M15 PnL':>9s}")
print("-" * 75)

grand_m5 = {'t': 0, 'w': 0, 'l': 0, 'pnl': 0}
grand_m15 = {'t': 0, 'w': 0, 'l': 0, 'pnl': 0}

for pair, (sym, pip, kz) in PAIRS.items():
    row = [pair]
    for tf in ['5m', '15m']:
        df = yf.Ticker(sym).history(start=start, end=end, interval=tf)
        if len(df) < 60:
            row.extend(['ERR', 'ERR', 'ERR'])
            continue
        signals = detect_signals(df, pip)
        signals = [s for s in signals if is_crt(df, s['idx']) and crt_ok(df, s['idx'])]
        t = len(signals)
        w = l = pnl = 0
        for s in signals:
            res, pp = simulate(df, s['idx'], s['type'], s['entry'], s['fvg_pips'], pip)
            if res == 'OPEN':
                t -= 1
                continue
            if res == 'WIN':
                w += 1
            else:
                l += 1
            pnl += pp
        wr = round(w / t * 100, 1) if t else 0
        pnl = round(pnl, 1)
        row.append(f"{t}T")
        row.append(f"{wr}%")
        row.append(f"{pnl:+}p")
        if tf == '5m':
            grand_m5['t'] += t; grand_m5['w'] += w; grand_m5['l'] += l; grand_m5['pnl'] += pnl
        else:
            grand_m15['t'] += t; grand_m15['w'] += w; grand_m15['l'] += l; grand_m15['pnl'] += pnl

    print(f"{row[0]:10s} {row[1]:>10s} {row[2]:>7s} {row[3]:>9s} | {row[4]:>10s} {row[5]:>7s} {row[6]:>9s}")

# Totals
t5 = grand_m5['t']; wr5 = round(grand_m5['w']/t5*100,1) if t5 else 0
t15 = grand_m15['t']; wr15 = round(grand_m15['w']/t15*100,1) if t15 else 0
print("-" * 75)
print(f"{'TOTAL':10s} {t5:>10d}T {wr5:>6.1f}% {grand_m5['pnl']:+9.1f}p | {t15:>10d}T {wr15:>6.1f}% {grand_m15['pnl']:+9.1f}p")

monthly_m5 = round(t5 / DAYS * 22)
monthly_m15 = round(t15 / DAYS * 22)
print(f"{'~mensal':10s} {monthly_m5:>10d}T {'':>7s} {'':>9s} | {monthly_m15:>10d}T")

print()
print("=" * 75)
print("CONCLUSÃO:")
exp_m5 = wr5/100 * 3 - (1-wr5/100) * 1 if t5 else 0
exp_m15 = wr15/100 * 3 - (1-wr15/100) * 1 if t15 else 0
print(f"  M5:  {t5}T em {DAYS}d = ~{monthly_m5}T/mês | expectância = {exp_m5:+.2f}R/trade")
print(f"  M15: {t15}T em {DAYS}d = ~{monthly_m15}T/mês | expectância = {exp_m15:+.2f}R/trade")
print(f"  Combinado: ~{monthly_m5+monthly_m15}T/mês")
print(f"  Regra: WR>{40}% + RR 3:1 = lucro sempre ✅" if (wr5>40 or wr15>40) else "")
print("=" * 75)
