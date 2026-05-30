#!/usr/bin/env python3
"""
BACKTEST COMPARATIVO: 1 trade total vs 1 por grupo (até 3 simultâneos)
Mede: WR, PF, drawdown, R total, trades simultâneos
"""
import sys, json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
from crypto_multi_agent import CryptoConfluencia
from tradingview_feed import TradingViewFeed

RR = 3.0
DATA_DAYS = 7
TIMEFRAME = '1m'
MIN_CONFIDENCE = 55
MIN_CANDLES = 1000

TEST_PAIRS = {
    'BTCUSD': ('BTC-USD', 'BINANCE', 1.0),
    'ETHUSD': ('ETH-USD', 'BINANCE', 0.1),
    'DOGEUSD': ('DOGE-USD', 'BINANCE', 0.001),
    'BNBUSD': ('BNB-USD', 'BINANCE', 0.1),
}

CORREL_GROUPS = {
    'BTC_LARGE_CAP': {'pairs': {'BTCUSD', 'ETHUSD'}, 'max_trades': 1},
    'MEME': {'pairs': {'DOGEUSD'}, 'max_trades': 1},
    'EXCHANGE': {'pairs': {'BNBUSD'}, 'max_trades': 1},
}

def get_pair_group(pair):
    for gname, gcfg in CORREL_GROUPS.items():
        if pair in gcfg['pairs']:
            return gname
    return None

def simulate_trade(highs, lows, closes, direction, entry, sl, tp):
    for i in range(len(closes)):
        if direction == 'BUY':
            if lows[i] <= sl: return 'LOSS', max(sl, lows[i]), i + 1
            if highs[i] >= tp: return 'WIN', tp, i + 1
        else:
            if highs[i] >= sl: return 'LOSS', min(sl, highs[i]), i + 1
            if lows[i] <= tp: return 'WIN', tp, i + 1
    last = closes[-1]
    return 'OPEN', last, len(closes)

def get_daily_bias(highs, lows, closes):
    if len(highs) < 3: return 'NEUTRAL'
    ph, pl = highs[-3], lows[-3]
    ch, cl, cc = highs[-2], lows[-2], closes[-2]
    if ch > ph and cc > ph: return 'BUY'
    if cl < pl and cc < pl: return 'SELL'
    if cc > closes[-3]: return 'BUY'
    if cc < closes[-3]: return 'SELL'
    return 'NEUTRAL'

def run_backtest(max_total=1):
    """max_total: 1 = 1 trade total, 3 = 1 por grupo (até 3 simultâneos)"""
    feed = TradingViewFeed()
    agent = CryptoConfluencia()
    
    # Load data
    pair_data = {}
    for pair, (sym, exchange, pip) in TEST_PAIRS.items():
        try:
            h, l, c, o, v = feed.get_candles(pair, TIMEFRAME, MIN_CANDLES + 5000)
            if c is not None and len(c) >= MIN_CANDLES:
                pair_data[pair] = {'h': np.array(h), 'l': np.array(l), 'c': np.array(c), 
                                  'o': np.array(o), 'v': np.array(v) if v is not None else None,
                                  'sym': sym, 'pip': pip}
        except: pass

    min_len = min(len(pd['c']) for pd in pair_data.values())
    common_len = min(min_len, 6000)
    start_offset = min_len - common_len
    
    step = 5
    min_warmup = 200
    
    trades = []
    active_trades = {}  # {trade_id: {pair, direction, entry, sl, tp, start_idx, group}}
    next_id = 0
    
    equity_curve = []  # (bar, equity_r)
    peak_equity = 0
    max_drawdown = 0
    
    for i in range(min_warmup, common_len - 60, step):
        abs_idx = start_offset + i
        
        # ═══ Verificar trades ativos ═══
        closed_now = []
        for tid, at in list(active_trades.items()):
            start = at['start_idx']
            remain_h = pair_data[at['pair']]['h'][start:]
            remain_l = pair_data[at['pair']]['l'][start:]
            remain_c = pair_data[at['pair']]['c'][start:]
            
            result, exit_price, bars = simulate_trade(
                remain_h, remain_l, remain_c, at['direction'], at['entry'], at['sl'], at['tp'])
            
            if result != 'OPEN':
                trades.append({**at, 'result': result, 'exit': exit_price, 
                              'duration_bars': bars, 'duration_min': bars})
                closed_now.append(tid)
        
        for tid in closed_now:
            del active_trades[tid]
        
        # ═══ Verificar se pode abrir novo trade ═══
        active_groups = set()
        for at in active_trades.values():
            g = get_pair_group(at['pair'])
            if g: active_groups.add(g)
        
        if max_total == 1:
            can_open = len(active_trades) == 0
        else:
            can_open = len(active_groups) < max_total  # até 3 grupos
        
        if not can_open:
            continue
        
        # ═══ Escanear candidatos ═══
        candidates = []
        for pair, pd in pair_data.items():
            h_win = pd['h'][abs_idx-200:abs_idx]
            l_win = pd['l'][abs_idx-200:abs_idx]
            c_win = pd['c'][abs_idx-200:abs_idx]
            o_win = pd['o'][abs_idx-200:abs_idx] if pd['o'] is not None else c_win
            if len(c_win) < 200: continue
            
            # Daily bias (TradingView agg)
            day_bars = 1440
            bias = 'NEUTRAL'
            if abs_idx >= day_bars * 3:
                day_h, day_l, day_c = [], [], []
                for d in range(3, 0, -1):
                    sd = abs_idx - d * day_bars
                    ed = abs_idx - (d-1) * day_bars
                    if sd >= 0 and ed <= len(pd['h']):
                        day_h.append(float(np.max(pd['h'][sd:ed])))
                        day_l.append(float(np.min(pd['l'][sd:ed])))
                        day_c.append(float(pd['c'][ed-1]))
                if len(day_h) >= 3:
                    bias = get_daily_bias(np.array(day_h), np.array(day_l), np.array(day_c))
            if bias == 'NEUTRAL': continue
            
            # Grupo já ocupado?
            gname = get_pair_group(pair)
            if gname and gname in active_groups:
                continue
            
            # BTC change
            btc_chg = 0
            if pair != 'BTCUSD':
                try:
                    btc_c = pair_data['BTCUSD']['c'][abs_idx-200:abs_idx]
                    if len(btc_c) >= 60:
                        btc_chg = (btc_c[-1] / btc_c[-60] - 1) * 100
                except: pass
            
            try:
                decision, conf, signal, v_info = agent.analyze(
                    pair, h_win, l_win, c_win, o_win, bias, pd['pip'], btc_chg, 
                    MIN_CONFIDENCE, None)
            except: continue
            
            if decision == 'NEUTRAL' or not signal: continue
            
            entry = signal['entry']
            atr_pct = (v_info or {}).get('atr_pct', 0.3)
            sl_rec = (v_info or {}).get('sl_recommend', None)
            sl_pct = sl_rec or max(atr_pct * 1.5, 0.12)
            
            if decision == 'BUY':
                sl = entry * (1 - sl_pct/100)
                tp = entry * (1 + sl_pct*RR/100)
            else:
                sl = entry * (1 + sl_pct/100)
                tp = entry * (1 - sl_pct*RR/100)
            
            candidates.append({
                'pair': pair, 'direction': decision, 'entry': entry,
                'sl': sl, 'tp': tp, 'sl_pct': sl_pct, 'conf': conf,
                'ir': signal.get('impulse_ratio', 0),
                'quality': signal.get('quality', 0),
                'group': gname,
            })
        
        if not candidates: continue
        
        # ═══ Selecionar melhor ═══
        candidates.sort(key=lambda x: x['ir'] * 10 + x['quality']/10 + x['conf']/10, reverse=True)
        best = candidates[0]
        
        # Abrir trade
        active_trades[next_id] = {
            'pair': best['pair'], 'direction': best['direction'],
            'entry': best['entry'], 'sl': best['sl'], 'tp': best['tp'],
            'start_idx': abs_idx, 'group': best['group'],
            'sl_pct': best['sl_pct'], 'conf': best['conf'],
            'ir': best['ir'], 'quality': best['quality'],
        }
        next_id += 1
        
        # Track equity
        if i % 50 == 0:
            current_r = sum(t.get('rr', (RR if t['result']=='WIN' else -1)) for t in trades)
            for at in active_trades.values():
                p = pair_data[at['pair']]['c'][abs_idx]
                if at['direction'] == 'BUY': r = (p - at['entry']) / (at['entry'] - at['sl'])
                else: r = (at['entry'] - p) / (at['sl'] - at['entry'])
                current_r += r
            equity_curve.append((i, current_r))
            peak_equity = max(peak_equity, current_r)
            dd = peak_equity - current_r
            max_drawdown = max(max_drawdown, dd)
    
    # Close open trades
    for at in active_trades.values():
        p = pair_data[at['pair']]['c'][-1]
        if at['direction'] == 'BUY': rr = (p - at['entry']) / (at['entry'] - at['sl'])
        else: rr = (at['entry'] - p) / (at['sl'] - at['entry'])
        trades.append({**at, 'result': 'OPEN', 'exit': p, 'rr': rr, 
                      'duration_bars': common_len - at['start_idx'],
                      'duration_min': common_len - at['start_idx']})
    
    return trades, equity_curve, max_drawdown, common_len

def analyze(trades, eq, dd, total_bars, label):
    closed = [t for t in trades if t['result'] != 'OPEN']
    wins = [t for t in closed if t['result'] == 'WIN']
    losses = [t for t in closed if t['result'] == 'LOSS']
    
    total = len(trades)
    wr = len(wins) / max(len(closed), 1) * 100
    total_r = sum(t.get('rr', RR if t['result']=='WIN' else -1) for t in trades)
    pf = (len(wins)*RR) / max(len(losses), 1)
    
    durations = [t.get('duration_min', 0) for t in closed if t.get('duration_min')]
    avg_dur = sum(durations) / len(durations) if durations else 0
    
    # Dias simulados
    days = total_bars / 1440
    
    print(f"\n═══ {label} ═══")
    print(f"Total trades:  {total} ({total/days:.0f}/dia)")
    print(f"Wins:          {len(wins)} ({wr:.1f}%)")
    print(f"Losses:        {len(losses)}")
    print(f"Open:          {len(trades) - len(closed)}")
    print(f"Total R:       {total_r:+.1f}R ({total_r/days:+.1f}R/dia)")
    print(f"Profit Factor: {pf:.2f}")
    print(f"Duração média: {avg_dur:.0f}min")
    print(f"Max Drawdown:  {dd:.1f}R")
    print(f"R/trade:       {total_r/max(total,1):+.2f}")
    
    # Por par
    for pair in sorted(set(t['pair'] for t in trades)):
        pt = [t for t in trades if t['pair'] == pair]
        pw = [t for t in pt if t['result'] == 'WIN']
        pr = sum(t.get('rr', RR if t['result']=='WIN' else -1) for t in pt)
        if pt: print(f"  {pair}: {len(pt)}t WR={len(pw)/len(pt)*100:.0f}% {pr:+.1f}R")
    
    return {'total': total, 'wr': wr, 'pf': pf, 'total_r': total_r, 
            'avg_dur': avg_dur, 'max_dd': dd, 'r_per_trade': total_r/max(total,1)}

# ═══ RUN ═══
print(f"Iniciando comparativo {datetime.now().strftime('%d/%m %H:%M')} UTC")
print(f"RR={RR}:1 {DATA_DAYS}d {TIMEFRAME}")

t1, eq1, dd1, bars1 = run_backtest(max_total=1)
r1 = analyze(t1, eq1, dd1, bars1, "CENÁRIO 1: 1 trade total (atual)")

t2, eq2, dd2, bars2 = run_backtest(max_total=3)  
r2 = analyze(t2, eq2, dd2, bars2, "CENÁRIO 2: 1 por grupo (até 3 simultâneos)")

print(f"\n═══ COMPARATIVO ═══")
print(f"{'Métrica':<22} {'1 Trade Total':>15} {'Até 3 (grupos)':>15}")
print(f"-" * 52)
for metric, key, fmt in [
    ('Trades', 'total', '{:.0f}'),
    ('Trades/dia', 'total', '{:.0f}'),
    ('Win Rate', 'wr', '{:.1f}%'),
    ('Profit Factor', 'pf', '{:.2f}'),
    ('R Total', 'total_r', '{:+.1f}'),
    ('R/dia', 'total_r', '{:+.1f}'),
    ('Max Drawdown', 'max_dd', '{:.1f}R'),
    ('R por trade', 'r_per_trade', '{:+.2f}'),
]:
    v1 = r1[key] / (bars1/1440) if key == 'total' and 'dia' in metric else r1[key]
    v2 = r2[key] / (bars2/1440) if key == 'total' and 'dia' in metric else r2[key]
    print(f"{metric:<22} {fmt.format(v1):>15} {fmt.format(v2):>15}")

# Recomendação
if r2['total_r'] > r1['total_r'] * 1.2 and r2['max_dd'] < r1['max_dd'] * 1.5:
    print(f"\n✅ RECOMENDAÇÃO: Até 3 grupos — +{r2['total_r']-r1['total_r']:.0f}R extra com drawdown aceitável")
elif r2['total_r'] > r1['total_r']:
    print(f"\n⚠️ Mais rentável mas avalie o drawdown extra: +{r2['total_r']-r1['total_r']:.0f}R vs +{r2['max_dd']-r1['max_dd']:.1f}R DD")
else:
    print(f"\n🛑 Mantenha 1 trade total — mais grupos não compensam o risco")

# Save
out = {
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'parametros': {'rr': RR, 'days': DATA_DAYS, 'timeframe': TIMEFRAME},
    'cenario_1': {'label': '1 trade total', 'results': r1, 'trades': len(t1)},
    'cenario_2': {'label': '1 por grupo', 'results': r2, 'trades': len(t2)},
}
outfile = Path.home() / '.hermes' / 'crypto' / 'backtest_comparativo.json'
with open(outfile, 'w') as f:
    json.dump(out, f, indent=2, default=str)
print(f"\nSalvo: {outfile}")
