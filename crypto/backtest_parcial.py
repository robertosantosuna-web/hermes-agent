#!/usr/bin/env python3
"""
BACKTEST PARCIAL vs TOTAL — 50% @1:1 + 50% @3:1 (SL→BE) vs 100% @3:1
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
MAX_TOTAL_TRADES = 1

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
        if pair in gcfg['pairs']: return gname
    return None

def get_daily_bias(highs, lows, closes):
    if len(highs) < 3: return 'NEUTRAL'
    ph, pl = highs[-3], lows[-3]
    ch, cl, cc = highs[-2], lows[-2], closes[-2]
    if ch > ph and cc > ph: return 'BUY'
    if cl < pl and cc < pl: return 'SELL'
    if cc > closes[-3]: return 'BUY'
    if cc < closes[-3]: return 'SELL'
    return 'NEUTRAL'

def simulate_partial(highs, lows, closes, direction, entry, sl, tp):
    """Simula parcial: 50% @1:1 (TP1), 50% @3:1 com SL→BE após TP1.
    Retorna: (result, exit_price, bars, r_total, tp1_hit, tp2_hit, sl_hit)"""
    
    sl_dist = abs(entry - sl)
    if direction == 'BUY':
        tp1 = entry + sl_dist  # 1:1
        tp2 = tp  # 3:1 (original)
    else:
        tp1 = entry - sl_dist  # 1:1
        tp2 = tp  # 3:1 (original)
    
    tp1_hit = False
    sl_hit = False
    tp2_hit = False
    tp1_bar = 0
    
    for i in range(len(closes)):
        h, l = highs[i], lows[i]
        
        if direction == 'BUY':
            # Verificar SL (antes de TP1, full size)
            if not tp1_hit and l <= sl:
                sl_hit = True
                return 'LOSS', sl, i+1, -1.0, False, False, True
            
            # TP1
            if not tp1_hit and h >= tp1:
                tp1_hit = True
                tp1_bar = i
                # SL move to breakeven (entry)
                sl = entry
            
            # Após TP1: verificar SL no breakeven ou TP2
            if tp1_hit:
                if l <= sl:  # SL no BE
                    return 'PARTIAL_WIN', entry, i+1, 0.5, True, False, False
                if h >= tp2:
                    tp2_hit = True
                    return 'FULL_WIN', tp2, i+1, 2.0, True, True, False
        
        else:  # SELL
            if not tp1_hit and h >= sl:
                sl_hit = True
                return 'LOSS', sl, i+1, -1.0, False, False, True
            
            if not tp1_hit and l <= tp1:
                tp1_hit = True
                tp1_bar = i
                sl = entry  # breakeven
            
            if tp1_hit:
                if h >= sl:
                    return 'PARTIAL_WIN', entry, i+1, 0.5, True, False, False
                if l <= tp2:
                    tp2_hit = True
                    return 'FULL_WIN', tp2, i+1, 2.0, True, True, False
    
    # Open: calcular R parcial
    last = closes[-1]
    if tp1_hit:
        if direction == 'BUY':
            partial_r = 0.5 + 0.5 * (last - entry) / sl_dist
        else:
            partial_r = 0.5 + 0.5 * (entry - last) / sl_dist
        return 'PARTIAL_OPEN', last, len(closes), partial_r, True, False, False
    else:
        if direction == 'BUY':
            r = (last - entry) / sl_dist
        else:
            r = (entry - last) / sl_dist
        return 'OPEN', last, len(closes), r, False, False, False

def simulate_full(highs, lows, closes, direction, entry, sl, tp):
    """Simula 100% @3:1 (sistema antigo)."""
    for i in range(len(closes)):
        if direction == 'BUY':
            if lows[i] <= sl: return 'LOSS', max(sl, lows[i]), i+1, -1.0
            if highs[i] >= tp: return 'WIN', tp, i+1, 3.0
        else:
            if highs[i] >= sl: return 'LOSS', min(sl, highs[i]), i+1, -1.0
            if lows[i] <= tp: return 'WIN', tp, i+1, 3.0
    last = closes[-1]
    if direction == 'BUY': r = (last - entry) / (entry - sl)
    else: r = (entry - last) / (sl - entry)
    return 'OPEN', last, len(closes), r

def run_backtest(use_partial=True):
    feed = TradingViewFeed()
    agent = CryptoConfluencia()
    
    pair_data = {}
    for pair, (sym, exchange, pip) in TEST_PAIRS.items():
        try:
            h, l, c, o, v = feed.get_candles(pair, TIMEFRAME, MIN_CANDLES + 5000)
            if c is not None and len(c) >= MIN_CANDLES:
                pair_data[pair] = {'h': np.array(h), 'l': np.array(l), 'c': np.array(c),
                                  'o': np.array(o), 'sym': sym, 'pip': pip}
        except: pass

    min_len = min(len(pd['c']) for pd in pair_data.values())
    common_len = min(min_len, 6000)
    start_offset = min_len - common_len
    
    step = 5
    min_warmup = 200
    
    trades = []
    active_trade = None
    equity_curve = []
    peak_r = 0
    max_dd = 0
    current_r = 0
    
    for i in range(min_warmup, common_len - 60, step):
        abs_idx = start_offset + i
        
        if active_trade:
            start = active_trade['start_idx']
            remain_h = pair_data[active_trade['pair']]['h'][start:]
            remain_l = pair_data[active_trade['pair']]['l'][start:]
            remain_c = pair_data[active_trade['pair']]['c'][start:]
            
            if use_partial:
                result, exit_price, bars, r, tp1_hit, tp2_hit, sl_hit = simulate_partial(
                    remain_h, remain_l, remain_c,
                    active_trade['direction'], active_trade['entry'],
                    active_trade['sl'], active_trade['tp'])
            else:
                result, exit_price, bars, r = simulate_full(
                    remain_h, remain_l, remain_c,
                    active_trade['direction'], active_trade['entry'],
                    active_trade['sl'], active_trade['tp'])
                tp1_hit = False; sl_hit = False
            
            if result not in ('OPEN', 'PARTIAL_OPEN'):
                current_r += r
                trades.append({
                    'pair': active_trade['pair'],
                    'direction': active_trade['direction'],
                    'entry': active_trade['entry'],
                    'sl': active_trade['sl'],
                    'tp': active_trade['tp'],
                    'result': result,
                    'exit': exit_price,
                    'r': r,
                    'duration_bars': bars,
                    'duration_min': bars,
                    'tp1_hit': tp1_hit,
                })
                active_trade = None
                continue
        
        if active_trade:
            continue
        
        # Scan candidates (same as existing backtest)
        candidates = []
        for pair, pd in pair_data.items():
            h_win = pd['h'][abs_idx-200:abs_idx]
            l_win = pd['l'][abs_idx-200:abs_idx]
            c_win = pd['c'][abs_idx-200:abs_idx]
            o_win = pd['o'][abs_idx-200:abs_idx] if pd['o'] is not None else c_win
            if len(c_win) < 200: continue
            
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
            
            btc_chg = 0
            if pair != 'BTCUSD':
                try:
                    btc_c = pair_data['BTCUSD']['c'][abs_idx-200:abs_idx]
                    if len(btc_c) >= 60:
                        btc_chg = (btc_c[-1] / btc_c[-60] - 1) * 100
                except: pass
            
            try:
                decision, conf, signal, v_info = agent.analyze(
                    pair, h_win, l_win, c_win, o_win, bias, pd['pip'],
                    btc_chg, MIN_CONFIDENCE, None)
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
            })
        
        if not candidates: continue
        
        candidates.sort(key=lambda x: x['ir'] * 10 + x['quality']/10 + x['conf']/10, reverse=True)
        best = candidates[0]
        
        active_trade = {
            'pair': best['pair'], 'direction': best['direction'],
            'entry': best['entry'], 'sl': best['sl'], 'tp': best['tp'],
            'start_idx': abs_idx, 'sl_pct': best['sl_pct'], 'conf': best['conf'],
            'ir': best['ir'], 'quality': best['quality'],
        }
        
        # Track equity
        if i % 50 == 0:
            peak_r = max(peak_r, current_r)
            max_dd = max(max_dd, peak_r - current_r)
    
    # Close open
    if active_trade:
        p = pair_data[active_trade['pair']]['c'][-1]
        sl_dist = abs(active_trade['entry'] - active_trade['sl'])
        if active_trade['direction'] == 'BUY':
            r = (p - active_trade['entry']) / sl_dist
        else:
            r = (active_trade['entry'] - p) / sl_dist
        trades.append({**active_trade, 'result': 'OPEN', 'exit': p, 'r': r,
                      'duration_bars': common_len - active_trade['start_idx'],
                      'duration_min': common_len - active_trade['start_idx']})
    
    return trades, current_r, max_dd, common_len

def analyze(trades, total_r, max_dd, bars, label):
    closed = [t for t in trades if t['result'] not in ('OPEN', 'PARTIAL_OPEN')]
    
    full_wins = [t for t in closed if t['result'] == 'FULL_WIN']
    partial_wins = [t for t in closed if t['result'] == 'PARTIAL_WIN']
    losses = [t for t in closed if t['result'] == 'LOSS']
    
    if 'FULL_WIN' in [t['result'] for t in trades]:
        # Parcial mode
        wins = full_wins + partial_wins
        wr = len(wins) / max(len(closed), 1) * 100
        avg_r_win = sum(t['r'] for t in wins) / len(wins) if wins else 0
        
        tp1_count = len([t for t in closed if t.get('tp1_hit')])
        
        print(f"\n═══ {label} ═══")
        print(f"Total:  {len(trades)}t | Fechados: {len(closed)}")
        print(f"FULL WIN (3:1):  {len(full_wins)} ({len(full_wins)/max(len(closed),1)*100:.0f}%)")
        print(f"PARTIAL (1:1):   {len(partial_wins)} ({len(partial_wins)/max(len(closed),1)*100:.0f}%)")
        print(f"LOSS (-1R):      {len(losses)} ({len(losses)/max(len(closed),1)*100:.0f}%)")
        print(f"Win Rate:        {wr:.1f}%")
        print(f"TP1 hit rate:    {tp1_count}/{len(closed)} ({tp1_count/max(len(closed),1)*100:.0f}%)")
    else:
        wins = [t for t in closed if t['result'] == 'WIN']
        losses = [t for t in closed if t['result'] == 'LOSS']
        wr = len(wins) / max(len(closed), 1) * 100
        print(f"\n═══ {label} ═══")
        print(f"Total:  {len(trades)}t | Wins: {len(wins)} | Losses: {len(losses)}")
        print(f"Win Rate: {wr:.1f}%")
    
    days = bars / 1440
    pf = (sum(t['r'] for t in closed if t['r'] > 0)) / max(abs(sum(t['r'] for t in closed if t['r'] < 0)), 1)
    
    durations = [t.get('duration_min', 0) for t in closed]
    avg_dur = sum(durations) / len(durations) if durations else 0
    
    print(f"R Total:     {total_r:+.1f}R | R/dia: {total_r/days:+.1f}")
    print(f"Profit Factor: {pf:.2f}")
    print(f"Duração média: {avg_dur:.0f}min")
    print(f"Max Drawdown:  {max_dd:.1f}R")
    print(f"R/trade:       {total_r/max(len(trades),1):+.2f}")
    
    return {'total': len(trades), 'wr': wr, 'total_r': total_r, 'pf': pf, 
            'max_dd': max_dd, 'tp1_hit_rate': tp1_count/max(len(closed),1)*100 if 'FULL_WIN' in [t['result'] for t in trades] else 0}

# ═══ RUN ═══
print(f"Iniciando comparativo parcial {datetime.now().strftime('%d/%m %H:%M')} UTC")

t_full, r_full, dd_full, bars = run_backtest(use_partial=False)
a_full = analyze(t_full, r_full, dd_full, bars, "100% @3:1 (ANTES)")

t_partial, r_partial, dd_partial, bars = run_backtest(use_partial=True)
a_partial = analyze(t_partial, r_partial, dd_partial, bars, "50%@1:1 + 50%@3:1 SL→BE (NOVO)")

days = bars / 1440

print(f"\n═══ COMPARATIVO FINAL ═══")
print(f"{'Métrica':<25} {'100% @3:1':>14} {'Parcial 50/50':>14} {'Delta':>10}")
print(f"-" * 65)
for label, key in [
    ('Trades', 'total'), ('Win Rate', 'wr'), ('R Total', 'total_r'),
    ('R/dia', 'total_r'), ('Profit Factor', 'pf'), ('Max Drawdown', 'max_dd'),
]:
    v1 = a_full[key] / days if key == 'total_r' else a_full[key]
    v2 = a_partial[key] / days if key == 'total_r' else a_partial[key]
    delta = v2 - v1
    ds = f"{delta:+.1f}" if isinstance(delta, float) else f"{delta}"
    f = '{:.1f}' if isinstance(v1, float) else '{:.0f}'
    print(f"{label:<25} {f.format(v1):>14} {f.format(v2):>14} {ds:>10}")

# TP1 hit rate
print(f"\n📊 TP1 (1:1) preencheu em {a_partial['tp1_hit_rate']:.0f}% dos trades fechados")

# Recomendação final
print(f"\n═══ VEREDICTO ═══")
r_delta = r_partial - r_full
dd_delta = dd_partial - dd_full
if r_delta > 0 and dd_delta <= 0:
    print(f"✅ PARCIAL É SUPERIOR: +{r_delta:.1f}R com menor/igual drawdown")
elif r_delta > 0:
    print(f"✅ PARCIAL VENCE: +{r_delta:.1f}R extra (DD: {dd_full:.1f}→{dd_partial:.1f}R, +{dd_delta:.1f}R)")
else:
    print(f"🛑 MANTENHA 100% @3:1 — parcial reduz retorno em {abs(r_delta):.1f}R")

out = {
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'full': a_full,
    'partial': a_partial,
}
outfile = Path.home() / '.hermes' / 'crypto' / 'backtest_parcial.json'
with open(outfile, 'w') as f:
    json.dump(out, f, indent=2, default=str)
print(f"Salvo: {outfile}")
