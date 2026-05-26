#!/usr/bin/env python3
"""
Backtest rápido: 10 ordens por setup, elimina <40% WR.
Testa todos os pares nas 3 killzones. SMC: CHoCH+sweep+FVG.
"""
import json
import urllib.request
import sys
from datetime import datetime, timedelta
from collections import defaultdict

PAIRS = {
    'EUR/USD': 'EURUSD=X',
    'USD/JPY': 'JPY=X',
    'GBP/USD': 'GBPUSD=X',
    'EUR/JPY': 'EURJPY=X',
}

KILLZONES = {
    'London Open': ('04:00', '05:00', ['EUR/USD', 'GBP/USD', 'EUR/JPY']),
    'NY Open': ('09:30', '10:30', ['EUR/USD', 'GBP/USD', 'USD/JPY']),
    'London Close': ('12:00', '13:00', ['EUR/USD', 'USD/JPY', 'EUR/JPY', 'GBP/USD']),
}

RR = 2.0
MIN_TRADES = 10
MIN_WR = 40.0
CAPITAL = 1000.0

def pip_m(pair):
    return 100 if 'JPY' in pair else 10000

def fetch_m5(symbol, days=10):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={days}d&interval=5m"
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
                dt = datetime.utcfromtimestamp(ts) - timedelta(hours=3)
                candles.append({'time': dt, 'o': o, 'h': h, 'l': l, 'c': c})
        return candles
    except Exception as e:
        print(f"  ⚠️ {symbol}: {e}", file=sys.stderr)
        return []

def detect_sweeps(candles):
    sweeps = []
    for i in range(3, len(candles) - 1):
        c = candles[i]
        # Sweep de low anterior
        for j in range(max(0, i-50), i-2):
            if j + 2 >= len(candles):
                continue
            prev_low = min(candles[k]['l'] for k in range(j, j+3))
            if c['l'] < prev_low and c['c'] > prev_low:
                sweeps.append({'idx': i, 'type': 'SWEEP_LOW', 'time': c['time'], 'level': prev_low, 'direction': 'COMPRA'})
                break
        # Sweep de high anterior
        for j in range(max(0, i-50), i-2):
            if j + 2 >= len(candles):
                continue
            prev_high = max(candles[k]['h'] for k in range(j, j+3))
            if c['h'] > prev_high and c['c'] < prev_high:
                sweeps.append({'idx': i, 'type': 'SWEEP_HIGH', 'time': c['time'], 'level': prev_high, 'direction': 'VENDA'})
                break
    return sweeps

def atr(candles, idx, period=14):
    if idx < period:
        return None
    trs = []
    for i in range(idx - period + 1, idx + 1):
        tr = max(candles[i]['h'] - candles[i]['l'],
                 abs(candles[i]['h'] - candles[i-1]['c']),
                 abs(candles[i]['l'] - candles[i-1]['c']))
        trs.append(tr)
    return sum(trs) / period

def simulate_setup(candles, sweeps, pair, killzone_name, killzone_hours):
    """Simula trades num setup especifico, filtra por killzone."""
    pm = pip_m(pair)
    trades = []
    
    for sweep in sweeps:
        if sweep['idx'] >= len(candles) - 5:
            continue
        
        # Filtrar por killzone
        sweep_hour = sweep['time'].hour + sweep['time'].minute / 60.0
        kz_start, kz_end = killzone_hours
        if not (kz_start <= sweep_hour < kz_end):
            continue
        
        c = candles[sweep['idx']]
        next_c = candles[sweep['idx'] + 1]
        curr_atr = atr(candles, sweep['idx'])
        if curr_atr is None or curr_atr == 0:
            continue
        
        if sweep['direction'] == 'COMPRA':
            if next_c['c'] > c['h']:
                entry = next_c['c']
                stop = entry - curr_atr * 1.5
                target = entry + (entry - stop) * RR
                
                for j in range(sweep['idx'] + 2, min(sweep['idx'] + 50, len(candles))):
                    fc = candles[j]
                    if fc['l'] <= stop:
                        trades.append({'result': 'SL', 'pnl': round((stop - entry) * pm, 1)})
                        break
                    if fc['h'] >= target:
                        trades.append({'result': 'TP', 'pnl': round((target - entry) * pm, 1)})
                        break
                else:
                    last = candles[min(sweep['idx'] + 49, len(candles) - 1)]
                    trades.append({'result': 'TIME', 'pnl': round((last['c'] - entry) * pm, 1)})
        
        elif sweep['direction'] == 'VENDA':
            if next_c['c'] < c['l']:
                entry = next_c['c']
                stop = entry + curr_atr * 1.5
                target = entry - (stop - entry) * RR
                
                for j in range(sweep['idx'] + 2, min(sweep['idx'] + 50, len(candles))):
                    fc = candles[j]
                    if fc['h'] >= stop:
                        trades.append({'result': 'SL', 'pnl': round((entry - stop) * pm, 1)})
                        break
                    if fc['l'] <= target:
                        trades.append({'result': 'TP', 'pnl': round((entry - target) * pm, 1)})
                        break
                else:
                    last = candles[min(sweep['idx'] + 49, len(candles) - 1)]
                    trades.append({'result': 'TIME', 'pnl': round((entry - last['c']) * pm, 1)})
    
    return trades

def main():
    now = datetime.now()
    print(f"┌{'─'*50}┐")
    print(f"│ BACKTEST 10 ORDENS POR SETUP — Elimina <{MIN_WR:.0f}% WR")
    print(f"│ {now.strftime('%d/%m %H:%M')} BRT | SMC: CHoCH+Sweep | RR 1:{RR:.0f} | 10 dias")
    print(f"├{'─'*50}┤")
    
    all_results = {}
    surviving = []
    eliminated = []
    
    for pair, symbol in PAIRS.items():
        print(f"│ 📥 {pair}...", end='', flush=True)
        candles = fetch_m5(symbol, 10)
        if len(candles) < 200:
            print(f" dados insuficientes ({len(candles)} candles)")
            continue
        
        sweeps = detect_sweeps(candles)
        print(f" {len(sweeps)} sweeps")
        
        for kz_name, (start_str, end_str, kz_pairs) in KILLZONES.items():
            if pair not in kz_pairs:
                continue
            
            start_h = int(start_str.split(':')[0]) + int(start_str.split(':')[1]) / 60.0
            end_h = int(end_str.split(':')[0]) + int(end_str.split(':')[1]) / 60.0
            
            trades = simulate_setup(candles, sweeps, pair, kz_name, (start_h, end_h))
            
            if len(trades) >= MIN_TRADES:
                wins = sum(1 for t in trades if t['result'] == 'TP')
                losses = sum(1 for t in trades if t['result'] == 'SL')
                wr = wins / len(trades) * 100
                total_pips = sum(t['pnl'] for t in trades)
                price = candles[-1]['c']
                pnl_pct = total_pips / (price * pip_m(pair)) * 100 * 30
                
                key = f"{pair}@{kz_name}"
                all_results[key] = {
                    'pair': pair, 'killzone': kz_name,
                    'trades': len(trades), 'wins': wins, 'losses': losses,
                    'wr': wr, 'pips': total_pips, 'pnl_pct': pnl_pct
                }
                
                if wr >= MIN_WR:
                    surviving.append(all_results[key])
                else:
                    eliminated.append(all_results[key])
    
    print(f"├{'─'*50}┤")
    
    if surviving:
        print(f"│ ✅ SOBREVIVENTES (≥{MIN_WR:.0f}% WR):")
        for r in sorted(surviving, key=lambda x: -x['wr']):
            icon = '🟢' if r['wr'] >= 50 else '🟡'
            print(f"│  {icon} {r['pair']} @ {r['killzone']}: {r['wins']}/{r['trades']} WR={r['wr']:.0f}% PnL={r['pips']:+.0f}p ({r['pnl_pct']:+.1f}%)")
    else:
        print(f"│ ⚠️ NENHUM setup sobreviveu ao filtro de {MIN_WR:.0f}%")
    
    if eliminated:
        print(f"│")
        print(f"│ ❌ ELIMINADOS (<{MIN_WR:.0f}% WR):")
        for r in sorted(eliminated, key=lambda x: x['wr']):
            print(f"│  🔴 {r['pair']} @ {r['killzone']}: {r['wins']}/{r['trades']} WR={r['wr']:.0f}%")
    
    # Resumo
    if surviving:
        total_trades = sum(r['trades'] for r in surviving)
        total_wins = sum(r['wins'] for r in surviving)
        avg_wr = total_wins / total_trades * 100
        avg_pnl = sum(r['pnl_pct'] for r in surviving) / len(surviving)
        print(f"├{'─'*50}┤")
        print(f"│ 📊 SOBREVIVENTES: {len(surviving)} setups | WR médio={avg_wr:.0f}% | PnL médio={avg_pnl:+.1f}%")
    
    print(f"└{'─'*50}┘")
    return 0

if __name__ == '__main__':
    sys.exit(main())
