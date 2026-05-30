#!/usr/bin/env python3
"""
BACKTEST v10 FINAL — 21 dias M1 — Multi-TF Bias + CRT + RR 3:1
Usa yfinance com chunking de 7 dias para obter 21 dias de M1
"""
import sys, os, yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

sys.path.insert(0, '/home/roberto/.hermes/scripts')

RR = 3.0; MIN_SL = 10; MAX_SL = 20

PAIRS = {
    'USDJPY': {'sym': 'USDJPY=X', 'pip': 0.01},
    'GBPJPY': {'sym': 'GBPJPY=X', 'pip': 0.01},
    'USDCAD': {'sym': 'USDCAD=X', 'pip': 0.0001},
    'EURJPY': {'sym': 'EURJPY=X', 'pip': 0.01},
    'GBPUSD': {'sym': 'GBPUSD=X', 'pip': 0.0001},
    'EURUSD': {'sym': 'EURUSD=X', 'pip': 0.0001},
    'XAUUSD': {'sym': 'GC=F',     'pip': 0.01, 'metal': True},
}

def fetch_m1_21d(symbol):
    """Baixa 21 dias de M1 em chunks de 7 dias."""
    all_data = []
    for i in range(3):
        end = datetime.now() - timedelta(days=i*7)
        start = end - timedelta(days=7)
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start, end=end, interval='1m')
        if len(df) > 0:
            all_data.append(df)
    if not all_data: return None
    full = pd.concat(all_data)
    full = full[~full.index.duplicated()].sort_index()
    return full

def get_tf_bias(highs, lows, closes):
    if len(highs) < 3: return 'NEUTRAL'
    ph, pl = highs[-3], lows[-3]
    ch, cl, cc = highs[-2], lows[-2], closes[-2]
    if ch > ph and cc < ph: return 'SELL'
    if cl < pl and cc > pl: return 'BUY'
    if ch > ph and cc > ph: return 'BUY'
    if cl < pl and cc < pl: return 'SELL'
    return 'NEUTRAL'

def detect_fvg_m1(highs, lows, closes, direction, pip_size, is_metal=False):
    n = len(closes)
    if n < 10: return []
    min_gap = 100 if is_metal else 1.0
    out = []
    for i in range(6, n-1):
        if direction == 'BUY' and lows[i] > highs[i-2]:
            gap = (lows[i]-highs[i-2])/pip_size
            if gap >= min_gap:
                out.append({'dir':'BUY','entry':closes[i],'gap':gap,'sl_pips':max(gap*1.2,MIN_SL),'idx':i})
        if direction == 'SELL' and highs[i] < lows[i-2]:
            gap = (lows[i-2]-highs[i])/pip_size
            if gap >= min_gap:
                out.append({'dir':'SELL','entry':closes[i],'gap':gap,'sl_pips':max(gap*1.2,MIN_SL),'idx':i})
    return out

print("="*60)
print("BACKTEST v10 FINAL — 21 dias M1 — Multi-TF Bias + CRT + RR 3:1")
print(datetime.now().strftime('%d/%m/%Y %H:%M'))
print("="*60)

all_trades = []

for name, cfg in PAIRS.items():
    sym = cfg['sym']; pip = cfg['pip']; metal = cfg.get('metal', False)
    print(f"\n--- {name} ---")
    
    try:
        # Baixar dados com chunking
        print(f"  Baixando M1...", end=' ', flush=True)
        df_m1 = fetch_m1_21d(sym)
        if df_m1 is None or len(df_m1) < 500:
            print("sem dados"); continue
        print(f"{len(df_m1)} velas")
        
        # Dados diários para o bias
        df_d = yf.Ticker(sym).history(period='30d', interval='1d')
        if df_d is None or len(df_d) < 5:
            print("  sem dados diários"); continue
        
        m1_h = df_m1['High'].astype(float).values
        m1_l = df_m1['Low'].astype(float).values
        m1_c = df_m1['Close'].astype(float).values
        m1_t = df_m1.index
        m1_day = [t.date() for t in m1_t]
        days = sorted(set(m1_day))
        
        d_h = df_d['High'].astype(float).values
        d_l = df_d['Low'].astype(float).values
        d_c = df_d['Close'].astype(float).values
        d_t = df_d.index
        
        trades = []
        last_trade_day = None
        
        for day_idx in range(5, len(days)):
            day = days[day_idx]
            day_candles = [j for j, d in enumerate(m1_day) if d == day]
            if len(day_candles) < 60: continue
            
            d_idx = None
            for di in range(len(d_t)):
                if d_t[di].date() == day: d_idx = di; break
            if d_idx is None or d_idx < 3: continue
            
            bias_d = get_tf_bias(d_h[:d_idx+1], d_l[:d_idx+1], d_c[:d_idx+1])
            if bias_d == 'NEUTRAL': continue
            
            for offset in range(8, len(day_candles)-1):
                i = day_candles[offset]
                if last_trade_day == day: break
                
                local_h = m1_h[max(0,i-12):i+1]
                local_l = m1_l[max(0,i-12):i+1]
                local_c = m1_c[max(0,i-12):i+1]
                
                fvgs = detect_fvg_m1(local_h, local_l, local_c, bias_d, pip, metal)
                if not fvgs: continue
                
                s = fvgs[-1]
                sl_pips = max(MIN_SL, min(s['sl_pips'], MAX_SL if not metal else 300))
                entry = s['entry']
                
                if s['dir'] == 'BUY':
                    sl = entry - sl_pips * pip
                    tp = entry + sl_pips * RR * pip
                else:
                    sl = entry + sl_pips * pip
                    tp = entry - sl_pips * RR * pip
                
                result = 'OPEN'; candles_held = 0
                for j in range(i+1, min(i+2000, len(m1_h))):
                    candles_held += 1
                    if s['dir'] == 'BUY':
                        if m1_h[j] >= tp: result = 'WIN'; break
                        if m1_l[j] <= sl: result = 'LOSS'; break
                    else:
                        if m1_l[j] <= tp: result = 'WIN'; break
                        if m1_h[j] >= sl: result = 'LOSS'; break
                
                if result in ('WIN','LOSS'):
                    trades.append({
                        'pair':name,'day':str(day),'bias':bias_d,
                        'dir':s['dir'],'entry':round(entry,5),
                        'sl_pips':round(sl_pips,1),'gap':round(s['gap'],1),
                        'result':result,'candles':candles_held,
                        'r':RR if result=='WIN' else -1.0
                    })
                    last_trade_day = day
                    break
        
        if trades:
            wins = sum(1 for t in trades if t['result']=='WIN')
            wr = wins/len(trades)*100
            r_tot = sum(t['r'] for t in trades)
            print(f"  {len(trades)} trades | WR:{wr:.1f}% | R:{r_tot:+.1f}")
            for t in trades[-3:]:
                e='✅' if t['result']=='WIN' else '❌'
                print(f"  {e} {t['day']} {t['dir']:4s} {t['bias']:4s} SL={t['sl_pips']:.0f}p → {t['result']} ({t['candles']}v)")
            all_trades.extend(trades)
        else:
            print("  0 trades")
    
    except Exception as e:
        print(f"  ERRO: {e}")
        import traceback; traceback.print_exc()

# CONSOLIDADO
print("\n"+"="*60)
print("CONSOLIDADO — 21 dias M1")
print("="*60)

if all_trades:
    wins = sum(1 for t in all_trades if t['result']=='WIN')
    total = len(all_trades)
    wr = wins/total*100
    r_total = sum(t['r'] for t in all_trades)
    win_r = sum(t['r'] for t in all_trades if t['r']>0)
    loss_r = abs(sum(t['r'] for t in all_trades if t['r']<0))
    pf = win_r/loss_r if loss_r>0 else float('inf')
    
    print(f"Total:    {total} trades")
    print(f"Win Rate: {wr:.1f}%")
    print(f"Expect:   {wr/100*RR - (1-wr/100):+.2f}R/trade")
    print(f"R total:  {r_total:+.1f}R")
    print(f"Profit F: {pf:.2f}")
    
    print(f"\n{'Par':8s} {'Trades':>6s} {'WR':>6s} {'R':>6s}")
    print("-"*30)
    for p in sorted(set(t['pair'] for t in all_trades)):
        pt = [t for t in all_trades if t['pair']==p]
        pw = sum(1 for t in pt if t['result']=='WIN')
        pr = sum(t['r'] for t in pt)
        print(f"{p:8s} {len(pt):6d} {pw/len(pt)*100:5.1f}% {pr:+5.1f}R")
    
    eq=0; peak=0; max_dd=0
    for t in all_trades:
        eq+=t['r']; peak=max(peak,eq); max_dd=max(max_dd,peak-eq)
    print(f"\nMax DD:   {max_dd:.1f}R")
    print(f"Equity:   {eq:+.1f}R")
    print(f"\nRisco 0.5%: Ganho={r_total*0.5:.1f}% MaxDD={max_dd*0.5:.1f}%")
else:
    print("Nenhum trade.")

print("\n=== FIM ===")
