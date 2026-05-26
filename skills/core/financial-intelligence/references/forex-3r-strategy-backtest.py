# Estratégia 3:1 RR — Backtest CRT London Close
# Calibrado em 19/05/2026 com dados reais Yahoo Finance (15 dias, 5 pares)
# Resultado: 28.6% WR, +54.5 pips, Profit Factor 2.1
# 
# Uso: python3 backtest_3r_strategy.py

import json, urllib.request
from datetime import datetime
from collections import defaultdict

def download_forex(pair, period="5m", days=15):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{pair}=X?range={days}d&interval={period}"
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
                candles.append({'time': datetime.utcfromtimestamp(ts), 'open': o, 'high': h, 'low': l, 'close': c})
        return candles
    except:
        return []

def pip_m(pair):
    return 100 if 'JPY' in pair else 10000

def in_london_close(dt):
    brt = (dt.hour - 3) % 24
    return 12 <= brt < 14

def calc_ema(values, period):
    if len(values) < period:
        return [values[-1]] * len(values)
    result = [values[0]] * (period - 1)
    mult = 2 / (period + 1)
    ema = sum(values[:period]) / period
    result.append(ema)
    for v in values[period:]:
        ema = (v - ema) * mult + ema
        result.append(ema)
    return result

def backtest_london_close(candles, pair):
    trades = []
    pip = pip_m(pair)
    if len(candles) < 60:
        return trades
    
    c = [x['close'] for x in candles]
    h = [x['high'] for x in candles]
    l = [x['low'] for x in candles]
    o = [x['open'] for x in candles]
    ema20 = calc_ema(c, 20)
    
    atr = []
    for i in range(14, len(candles)):
        tr_sum = sum(max(h[j]-l[j], abs(h[j]-c[j-1]), abs(l[j]-c[j-1])) for j in range(i-13, i+1))
        atr.append(tr_sum/14)
    
    for i in range(30, len(candles) - 1):
        dt = candles[i]['time']
        if not in_london_close(dt):
            continue
        atr_i = i - 14
        if atr_i < 0 or atr_i >= len(atr):
            continue
        curr_atr = atr[atr_i]
        body = c[i] - o[i]
        prev_range = h[i-1] - l[i-1]
        if prev_range < curr_atr * 0.35 or abs(body) < curr_atr * 0.15:
            continue
        
        sweep_low_amt = l[i-1] - l[i]
        sweep_high_amt = h[i] - h[i-1]
        
        # LONG setup
        if (l[i] < l[i-1] and sweep_low_amt > curr_atr * 0.1 and
            c[i] > l[i-1] and body > 0 and c[i] > ema20[i]):
            entry = c[i]
            sl = l[i] - curr_atr * 0.08
            sl_pips = (entry - sl) * pip
            tp = entry + (entry - sl) * 3.0
            if sl_pips >= 2.5:
                trade = {'type':'LONG','pair':pair,'entry':round(entry,6),'sl':round(sl,6),'tp':round(tp,6)}
                hit = sim_trade(candles, i, trade, pip)
                if hit: trades.append(hit)
        
        # SHORT setup
        elif (h[i] > h[i-1] and sweep_high_amt > curr_atr * 0.1 and
              c[i] < h[i-1] and body < 0 and c[i] < ema20[i]):
            entry = c[i]
            sl = h[i] + curr_atr * 0.08
            sl_pips = (sl - entry) * pip
            tp = entry - (sl - entry) * 3.0
            if sl_pips >= 2.5:
                trade = {'type':'SHORT','pair':pair,'entry':round(entry,6),'sl':round(sl,6),'tp':round(tp,6)}
                hit = sim_trade(candles, i, trade, pip)
                if hit: trades.append(hit)
    return trades

def sim_trade(candles, entry_idx, trade, pip):
    max_bars = 50
    for j in range(entry_idx + 1, min(entry_idx + max_bars, len(candles))):
        c = candles[j]
        if trade['type'] == 'LONG':
            if c['low'] <= trade['sl']:
                trade['result']='SL'; trade['pnl_pips']=round((trade['sl']-trade['entry'])*pip,1); return trade
            if c['high'] >= trade['tp']:
                trade['result']='TP'; trade['pnl_pips']=round((trade['tp']-trade['entry'])*pip,1); return trade
        else:
            if c['high'] >= trade['sl']:
                trade['result']='SL'; trade['pnl_pips']=round((trade['entry']-trade['sl'])*pip,1); return trade
            if c['low'] <= trade['tp']:
                trade['result']='TP'; trade['pnl_pips']=round((trade['entry']-trade['tp'])*pip,1); return trade
    last = candles[min(entry_idx + max_bars - 1, len(candles) - 1)]
    trade['result'] = 'TIME'
    trade['pnl_pips'] = round((last['close']-trade['entry'])*pip,1) if trade['type']=='LONG' else round((trade['entry']-last['close'])*pip,1)
    return trade

if __name__ == '__main__':
    pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'EURJPY', 'AUDUSD']
    all_trades = []
    for pair in pairs:
        candles = download_forex(pair, "5m", 15)
        if not candles: continue
        trades = backtest_london_close(candles, pair)
        all_trades.extend(trades)
        if trades:
            tps = [t for t in trades if t['result']=='TP']
            sls = [t for t in trades if t['result']=='SL']
            pnl = sum(t['pnl_pips'] for t in trades)
            wr = round(len(tps)/len(trades)*100,1)
            print(f"  {pair:8s} | {len(trades):2d}T | {len(tps)}W/{len(sls)}L | {wr}% WR | PnL: {pnl:+.1f}")
    total_tp = len([t for t in all_trades if t['result']=='TP'])
    total_pnl = sum(t['pnl_pips'] for t in all_trades)
    print(f"\n  TOTAL: {len(all_trades)} trades | {round(total_tp/len(all_trades)*100,1)}% WR | PnL: {total_pnl:+.1f} pips")
