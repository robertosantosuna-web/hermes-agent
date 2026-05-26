#!/usr/bin/env python3
"""
SIMULAÇÃO RÁPIDA PÓS-KILLZONE — NY Open
Roda após 10:00 BRT, analisa dados da killzone + pré-mercado.
Foco: detectar setups CHoCH+sweep+OB/FVG nos pares principais.
Saída formatada para Telegram.
"""
import json
import urllib.request
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# ═══════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════
PAIRS = {
    'EUR/USD': 'EURUSD=X',
    'USD/JPY': 'JPY=X',
    'GBP/USD': 'GBPUSD=X',
    'EUR/JPY': 'EURJPY=X',
}

CAPITAL = 1000.0
RISCO_PCT = 1.0
RR = 2.0  # 1:2 conforme calibração

def pip_m(pair):
    return 100 if 'JPY' in pair else 10000

def fetch_m5(symbol, hours=8):
    """Busca candles M5 via Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=5m"
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
                    'time': datetime.utcfromtimestamp(ts) - timedelta(hours=3),  # BRT
                    'o': o, 'h': h, 'l': l, 'c': c
                })
        # Filtrar últimas N horas
        cutoff = candles[-1]['time'] - timedelta(hours=hours) if candles else None
        if cutoff:
            candles = [c for c in candles if c['time'] >= cutoff]
        return candles
    except Exception as e:
        print(f"  ⚠️ Erro {symbol}: {e}", file=sys.stderr)
        return []

def detect_swings(candles):
    """Detecta swing highs e lows."""
    highs, lows = [], []
    for i in range(2, len(candles) - 2):
        h = candles[i]['h']
        l = candles[i]['l']
        if h > candles[i-1]['h'] and h > candles[i-2]['h'] and h > candles[i+1]['h'] and h > candles[i+2]['h']:
            highs.append({'idx': i, 'price': h, 'time': candles[i]['time']})
        if l < candles[i-1]['l'] and l < candles[i-2]['l'] and l < candles[i+1]['l'] and l < candles[i+2]['l']:
            lows.append({'idx': i, 'price': l, 'time': candles[i]['time']})
    return highs, lows

def detect_sweeps(candles, highs, lows):
    """Detecta liquidity sweeps."""
    sweeps = []
    for i in range(3, len(candles) - 1):
        c = candles[i]
        # Sweep de low anterior
        for sl in lows:
            if sl['idx'] < i - 2 and c['l'] < sl['price'] and c['c'] > sl['price']:
                sweeps.append({
                    'idx': i, 'type': 'SWEEP_LOW', 'time': c['time'],
                    'level': round(sl['price'], 5), 'direction': 'COMPRA'
                })
                break
        # Sweep de high anterior
        for sh in highs:
            if sh['idx'] < i - 2 and c['h'] > sh['price'] and c['c'] < sh['price']:
                sweeps.append({
                    'idx': i, 'type': 'SWEEP_HIGH', 'time': c['time'],
                    'level': round(sh['price'], 5), 'direction': 'VENDA'
                })
                break
    return sweeps

def detect_fvg(candles):
    """Detecta Fair Value Gaps."""
    fvgs = []
    for i in range(1, len(candles) - 1):
        c0, c2 = candles[i-1], candles[i+1]
        if c0['h'] < c2['l']:
            fvgs.append({'idx': i, 'type': 'FVG_BULL', 'top': c2['l'], 'bottom': c0['h']})
        if c0['l'] > c2['h']:
            fvgs.append({'idx': i, 'type': 'FVG_BEAR', 'top': c0['l'], 'bottom': c2['h']})
    return fvgs

def atr(candles, idx, period=14):
    """Calcula ATR no ponto."""
    if idx < period:
        return None
    trs = []
    for i in range(idx - period + 1, idx + 1):
        tr = max(
            candles[i]['h'] - candles[i]['l'],
            abs(candles[i]['h'] - candles[i-1]['c']),
            abs(candles[i]['l'] - candles[i-1]['c'])
        )
        trs.append(tr)
    return sum(trs) / period

def simulate_pair(pair, symbol):
    """Simula estratégia SMC no par."""
    candles = fetch_m5(symbol, hours=8)
    if len(candles) < 30:
        return None

    pm = pip_m(pair)
    highs, lows = detect_swings(candles)
    sweeps = detect_sweeps(candles, highs, lows)
    fvgs = detect_fvg(candles)

    # Filtrar sweeps nas últimas 4 horas (foco na NY Open)
    ny_cutoff = candles[-1]['time'] - timedelta(hours=4)
    recent_sweeps = [s for s in sweeps if s['time'] >= ny_cutoff]

    if not recent_sweeps:
        return None

    trades = []
    for sweep in recent_sweeps[-5:]:  # Últimos 5 sweeps
        if sweep['idx'] >= len(candles) - 5:
            continue

        c = candles[sweep['idx']]
        next_c = candles[sweep['idx'] + 1]
        curr_atr = atr(candles, sweep['idx'])
        if curr_atr is None:
            continue

        # Verificar FVG próximo
        nearby_fvg = [f for f in fvgs if abs(f['idx'] - sweep['idx']) <= 3]
        has_fvg = len(nearby_fvg) > 0

        if sweep['direction'] == 'COMPRA':
            # CHoCH: fecha acima da máxima da vela de sweep
            if next_c['c'] > c['h']:
                entry = next_c['c']
                stop = entry - curr_atr * 1.5
                target = entry + (entry - stop) * RR

                # Forward test até 50 candles
                hit = None
                for j in range(sweep['idx'] + 2, min(sweep['idx'] + 50, len(candles))):
                    fc = candles[j]
                    if fc['l'] <= stop:
                        hit = ('SL', round((stop - entry) * pm, 1))
                        break
                    if fc['h'] >= target:
                        hit = ('TP', round((target - entry) * pm, 1))
                        break

                if hit:
                    trades.append({
                        'time': sweep['time'].strftime('%H:%M'),
                        'direction': '🟢 COMPRA',
                        'entry': round(entry, 5),
                        'stop': round(stop, 5),
                        'target': round(target, 5),
                        'result': hit[0],
                        'pnl_pips': hit[1],
                        'fvg': has_fvg
                    })

        elif sweep['direction'] == 'VENDA':
            if next_c['c'] < c['l']:
                entry = next_c['c']
                stop = entry + curr_atr * 1.5
                target = entry - (stop - entry) * RR

                hit = None
                for j in range(sweep['idx'] + 2, min(sweep['idx'] + 50, len(candles))):
                    fc = candles[j]
                    if fc['h'] >= stop:
                        hit = ('SL', round((entry - stop) * pm, 1))
                        break
                    if fc['l'] <= target:
                        hit = ('TP', round((entry - target) * pm, 1))
                        break

                if hit:
                    trades.append({
                        'time': sweep['time'].strftime('%H:%M'),
                        'direction': '🔴 VENDA',
                        'entry': round(entry, 5),
                        'stop': round(stop, 5),
                        'target': round(target, 5),
                        'result': hit[0],
                        'pnl_pips': hit[1],
                        'fvg': has_fvg
                    })

    if not trades:
        return None

    price = candles[-1]['c']
    wins = [t for t in trades if t['result'] == 'TP']
    losses = [t for t in trades if t['result'] == 'SL']
    wr = len(wins) / len(trades) * 100 if trades else 0
    total_pips = sum(t['pnl_pips'] for t in trades)

    return {
        'pair': pair,
        'price': round(price, 5),
        'trades': trades,
        'total_trades': len(trades),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(wr, 1),
        'total_pips': round(total_pips, 1),
        'pnl_pct': round(total_pips / (price * pm) * 100 * 30, 2),  # 30x leverage
    }


def main():
    now = datetime.now()
    print(f"┌{'─'*40}┐")
    print(f"│ 📊 SIMULAÇÃO FOREX — PÓS NY OPEN")
    print(f"│ {now.strftime('%d/%m %H:%M')} BRT | SMC: CHoCH+Sweep+FVG | RR 1:{RR:.0f}")
    print(f"├{'─'*40}┤")

    all_results = []
    total_trades = 0
    total_wins = 0
    total_pips = 0
    total_pnl = 0

    for pair, symbol in PAIRS.items():
        print(f"│ ⏳ {pair}...", end='', flush=True)
        result = simulate_pair(pair, symbol)
        if result and result['trades']:
            all_results.append(result)
            total_trades += result['total_trades']
            total_wins += result['wins']
            total_pips += result['total_pips']
            total_pnl += result['pnl_pct']
            print(f" {result['total_trades']} trades")
        else:
            print(f" sem setups")

    print(f"├{'─'*40}┤")

    if not all_results:
        print(f"│ ⚠️ Nenhum setup CHoCH+Sweep+FVG detectado")
        print(f"│ Mercado lateral ou range insuficiente")
    else:
        for r in all_results:
            wr_icon = '🟢' if r['win_rate'] >= 50 else '🟡' if r['win_rate'] >= 33 else '🔴'
            print(f"│  {r['pair']}: {r['price']} | {r['wins']}/{r['total_trades']} | WR={r['win_rate']}% | {r['total_pips']:+}p | PnL={r['pnl_pct']:+}%")
            for t in r['trades']:
                fvg_tag = ' [FVG]' if t['fvg'] else ''
                icon = '✅' if t['result'] == 'TP' else '❌'
                print(f"│    {t['time']} {t['direction']} E={t['entry']} {icon} {t['result']} {t['pnl_pips']:+}p{fvg_tag}")

        overall_wr = total_wins / total_trades * 100 if total_trades else 0
        print(f"├{'─'*40}┤")
        print(f"│ 📈 TOTAL: {total_trades} trades | WR={overall_wr:.0f}% | {total_pips:+}p | PnL={total_pnl:+.2f}%")
        print(f"│ 💰 Capital R${CAPITAL:.0f} | Ganho teórico: R${CAPITAL * total_pnl / 100:+.2f}")

    print(f"└{'─'*40}┘")
    return 0


if __name__ == '__main__':
    sys.exit(main())
