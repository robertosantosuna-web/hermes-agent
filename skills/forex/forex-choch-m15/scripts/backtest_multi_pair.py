#!/usr/bin/python3
"""Backtest multi-par FVG+CRT — 30 dias M15, suporte a killzones por par.

Diferente de backtest_crt_choch.py (config fixa), este script aceita:
- killzones POR PAR (ex: GBPJPY=[6,7], EURUSD=[15])
- Toggle killzone ON/OFF para comparar impacto
- 1 ou mais pares com estratégias nomeadas
- Gap mínimo e RR configuráveis

Uso:
  python3 scripts/backtest_multi_pair.py              # 3 pares padrão
  python3 scripts/backtest_multi_pair.py --no-killzone # sem filtro de hora
  python3 scripts/backtest_multi_pair.py --gap 5       # gap >= 5 pips
"""
import yfinance as yf
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT = Path.home() / '.hermes' / 'forex' / 'backtest_multi_pair.json'

# Pares padrão — editar conforme necessário
DEFAULT_PAIRS = {
    'GBP/JPY': {'sym': 'GBPJPY=X', 'pip': 0.01,  'strategy': 'ICT H1-M5-M1',    'killzone': [6, 7]},
    'GBP/USD': {'sym': 'GBPUSD=X', 'pip': 0.0001, 'strategy': 'Killzone LC 15h', 'killzone': [15]},
    'EUR/USD': {'sym': 'EURUSD=X', 'pip': 0.0001, 'strategy': 'Killzone LC 15h', 'killzone': [15]},
}
MIN_FVG_PIPS = 3.0
RR_RATIO = 3.0
CRT_RANGE_PERCENTILE = 0.8
DAYS = 30


def detect_signals(df, pip_val, allowed_hours):
    """Detecta CHoCH+FVG com rolling window de 60 candles, filtro de killzone."""
    h = df['High'].values.astype(float)
    l = df['Low'].values.astype(float)
    c = df['Close'].values.astype(float)
    n = len(h)
    all_signals = []

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
                        if j+1 < end and l[j+1] > h[j]:
                            gap = (l[j+1] - h[j]) / pip_val
                            if gap >= MIN_FVG_PIPS:
                                candle_hour = df.index[j+1].hour
                                if candle_hour in allowed_hours:
                                    all_signals.append({
                                        'type': 'BUY', 'entry': round(l[j+1], 5),
                                        'fvg_pips': round(gap, 1), 'idx': i, 'hour': candle_hour
                                    })
                                break
                    break

        if sl:
            si, sv = sl[-1]
            for i in range(si + 1, end):
                if c[i] < sv:
                    for j in range(max(start, i-3), i):
                        if j+1 < end and h[j+1] < l[j]:
                            gap = (l[j] - h[j+1]) / pip_val
                            if gap >= MIN_FVG_PIPS:
                                candle_hour = df.index[j+1].hour
                                if candle_hour in allowed_hours:
                                    all_signals.append({
                                        'type': 'SELL', 'entry': round(h[j+1], 5),
                                        'fvg_pips': round(gap, 1), 'idx': i, 'hour': candle_hour
                                    })
                                break
                    break

    seen = set()
    unique = []
    for s in all_signals:
        key = (s['idx'], s['type'])
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique


def is_crt_candle(df, idx):
    if idx < 20:
        return False
    rng = abs(float(df.iloc[idx]['High']) - float(df.iloc[idx]['Low']))
    recent = [abs(float(df.iloc[i]['High']) - float(df.iloc[i]['Low'])) for i in range(idx-19, idx+1)]
    return rng >= sorted(recent)[int(len(recent)*CRT_RANGE_PERCENTILE)]


def crt_confirmation(df, idx):
    if idx + 1 >= len(df):
        return False
    h1, l1 = float(df.iloc[idx]['High']), float(df.iloc[idx]['Low'])
    c2 = float(df.iloc[idx+1]['Close'])
    return l1 <= c2 <= h1


def simulate_trade(df, entry_idx, direction, entry_price, fvg_pips, pip_val):
    sl_pips = max(fvg_pips, 3.0)
    tp_pips = sl_pips * RR_RATIO
    if direction == 'BUY':
        sl = entry_price - sl_pips * pip_val
        tp = entry_price + tp_pips * pip_val
    else:
        sl = entry_price + sl_pips * pip_val
        tp = entry_price - tp_pips * pip_val

    for i in range(entry_idx + 1, len(df)):
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


def backtest(pairs, use_crt=False, use_killzone=True):
    end = datetime.now()
    start = end - timedelta(days=DAYS)
    results = {}
    total = {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0}

    for pair, cfg in pairs.items():
        try:
            df = yf.Ticker(cfg['sym']).history(start=start, end=end, interval='15m')
            if len(df) < 60:
                results[pair] = {'error': f'Only {len(df)} candles'}
                continue
            allowed = cfg['killzone'] if use_killzone else list(range(24))
            signals = detect_signals(df, cfg['pip'], allowed)

            if use_crt:
                signals = [s for s in signals
                           if is_crt_candle(df, s['idx']) and crt_confirmation(df, s['idx'])]

            pr = {'pair': pair, 'strategy': cfg['strategy'],
                  'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0, 'signals': []}
            for s in signals:
                res, pnl = simulate_trade(df, s['idx'], s['type'],
                                          s['entry'], s['fvg_pips'], cfg['pip'])
                if res == 'OPEN':
                    continue
                pr['trades'] += 1
                if res == 'WIN':
                    pr['wins'] += 1
                else:
                    pr['losses'] += 1
                pr['pnl'] += pnl
                pr['signals'].append({
                    'type': s['type'], 'entry': s['entry'],
                    'fvg_pips': round(s['fvg_pips'], 1),
                    'hour': s['hour'], 'result': res, 'pnl': round(pnl, 1)
                })

            t = pr['trades']
            pr['wr'] = round(pr['wins']/t*100, 1) if t else 0
            pr['pnl'] = round(pr['pnl'], 1)
            results[pair] = pr

            total['trades'] += pr['trades']
            total['wins'] += pr['wins']
            total['losses'] += pr['losses']
            total['pnl'] += pr['pnl']
        except Exception as e:
            results[pair] = {'error': str(e)}

    t = total['trades']
    total['wr'] = round(total['wins']/t*100, 1) if t else 0
    total['pnl'] = round(total['pnl'], 1)
    return results, total


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backtest FVG+CRT multi-par')
    parser.add_argument('--no-killzone', action='store_true', help='Desativa filtro de killzone')
    parser.add_argument('--gap', type=float, default=MIN_FVG_PIPS, help='Gap mínimo em pips')
    parser.add_argument('--days', type=int, default=DAYS, help='Dias de backtest')
    parser.add_argument('--pairs', nargs='*', help='Pares específicos (ex: GBP/USD EUR/USD)')
    args = parser.parse_args()

    MIN_FVG_PIPS = args.gap
    DAYS = args.days
    pairs = DEFAULT_PAIRS
    if args.pairs:
        pairs = {k: v for k, v in DEFAULT_PAIRS.items() if k in args.pairs}

    print("=" * 70)
    print(f"BACKTEST — {len(pairs)} par(es), {DAYS}d, M15, gap≥{MIN_FVG_PIPS}p, "
          f"killzone={'OFF' if args.no_killzone else 'ON'}")
    print("=" * 70)

    r1, t1 = backtest(pairs, use_crt=False, use_killzone=not args.no_killzone)
    r2, t2 = backtest(pairs, use_crt=True, use_killzone=not args.no_killzone)

    for pair in pairs:
        cfg = pairs[pair]
        print(f"\n── {pair} ({cfg['strategy']}, killzone UTC {cfg['killzone']}) ──")
        o = r1.get(pair, {})
        c = r2.get(pair, {})
        if 'error' in o:
            print(f"  ❌ ERROR: {o['error']}")
            continue
        print(f"  FVG puro:      {o.get('trades',0):3d}T | WR={o.get('wr',0):5.1f}% | PnL={o.get('pnl',0):+7.1f}p")
        print(f"  FVG + CRT:     {c.get('trades',0):3d}T | WR={c.get('wr',0):5.1f}% | PnL={c.get('pnl',0):+7.1f}p")
        for s in c.get('signals', []):
            emoji = '✅' if s['result'] == 'WIN' else '❌'
            print(f"    {emoji} {s['type']:5s} @ {s['entry']}  gap={s['fvg_pips']}p  h={s['hour']}  {s['pnl']:+}p")

    print(f"\n{'='*70}")
    print(f"TOTAL FVG puro:      {t1['trades']:3d}T | WR={t1['wr']:5.1f}% | PnL={t1['pnl']:+7.1f}p")
    print(f"TOTAL FVG + CRT:     {t2['trades']:3d}T | WR={t2['wr']:5.1f}% | PnL={t2['pnl']:+7.1f}p")
    print(f"CRT impacto:          {t2['trades']-t1['trades']:+3d}T | "
          f"WR {t2['wr']-t1['wr']:+.1f}pp | PnL {t2['pnl']-t1['pnl']:+}p")
    print(f"{'='*70}")
    print(f"⚠️  Killzones zeram backtest histórico com intervalo M15.")
    print(f"   Use --no-killzone para ver sinais reais. No bot ao vivo,")
    print(f"   killzones capturam setups que o backtest perde.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        'original': r1, 'crt': r2, 'total_orig': t1, 'total_crt': t2,
        'ts': datetime.now().isoformat(), 'pairs': list(pairs.keys()),
        'gap': MIN_FVG_PIPS, 'killzones': not args.no_killzone
    }, indent=2, default=str))
    print(f"\n📁 Saved: {OUTPUT}")
