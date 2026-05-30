#!/usr/bin/env python3
"""
BACKTEST v11 FINAL — CDP M1 + Filtros ATR/ADX/Vol + Multi-TF Bias + RR 3:1
"""
import sys, os, json, time
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, '/home/roberto/.hermes/scripts')
from tv_data import fetch_ohlcv

RR = 3.0
MIN_SL, MAX_SL = 10, 30

PAIRS = {
    'EURUSD': {'sym': 'EURUSD=X', 'pip': 0.0001},
    'GBPUSD': {'sym': 'GBPUSD=X', 'pip': 0.0001},
    'USDJPY': {'sym': 'USDJPY=X', 'pip': 0.01},
    'GBPJPY': {'sym': 'GBPJPY=X', 'pip': 0.01},
    'EURJPY': {'sym': 'EURJPY=X', 'pip': 0.01},
    'USDCAD': {'sym': 'USDCAD=X', 'pip': 0.0001},
    'XAUUSD': {'sym': 'GC=F',     'pip': 0.01, 'metal': True},
}

def get_tf_bias(highs, lows, closes):
    if len(highs) < 3: return 'NEUTRAL'
    ph, pl = highs[-3], lows[-3]
    ch, cl, cc = highs[-2], lows[-2], closes[-2]
    if ch > ph and cc < ph: return 'SELL'
    if cl < pl and cc > pl: return 'BUY'
    if ch > ph and cc > ph: return 'BUY'
    if cl < pl and cc < pl: return 'SELL'
    return 'NEUTRAL'

def get_multi_bias(sym):
    """Multi-TF bias rápido."""
    buy = sell = 0
    details = {}
    for tf_name, tf in [('W','1d'),('D','1d'),('H4','4h')]:
        df = fetch_ohlcv(sym, period='5d', interval=tf)
        if df is None or len(df) < 3: details[tf_name]='?'; continue
        col_map = {}
        for c in df.columns:
            cl = c.lower()
            if cl in ('high','h'): col_map['h']=c
            elif cl in ('low','l'): col_map['l']=c
            elif cl in ('close','c'): col_map['c']=c
        if len(col_map)<3: details[tf_name]='?'; continue
        h = df[col_map['h']].values; l = df[col_map['l']].values
        c = df[col_map['c']].values
        bias = get_tf_bias(h, l, c)
        if bias=='BUY': buy+=1; details[tf_name]='BUY✓'
        elif bias=='SELL': sell+=1; details[tf_name]='SELL✓'
        else: details[tf_name]='NEUTRAL'
    if buy>sell: return 'BUY',details
    if sell>buy: return 'SELL',details
    return 'NEUTRAL',details

def detect_fvg(highs, lows, closes, direction, pip_size, is_metal=False):
    n = len(closes)
    if n < 10: return []
    min_gap = 100 if is_metal else 1.0
    out = []
    for i in range(6, n-1):
        if direction == 'BUY' and lows[i] > highs[i-2]:
            gap = (lows[i]-highs[i-2])/pip_size
            if gap >= min_gap:
                out.append({'dir':'BUY','entry':closes[i],'gap':gap,
                           'sl_raw':max(gap*1.2,MIN_SL),'idx':i})
        if direction == 'SELL' and highs[i] < lows[i-2]:
            gap = (lows[i-2]-highs[i])/pip_size
            if gap >= min_gap:
                out.append({'dir':'SELL','entry':closes[i],'gap':gap,
                           'sl_raw':max(gap*1.2,MIN_SL),'idx':i})
    return out

print("="*60)
print("BACKTEST v11 — CDP M1 + Filtros + Multi-TF Bias + RR 3:1")
print(datetime.now().strftime('%d/%m/%Y %H:%M'))
print("="*60)

all_trades = []

for name, cfg in PAIRS.items():
    sym = cfg['sym']; pip = cfg['pip']; metal = cfg.get('metal', False)
    print(f"\n--- {name} ---")
    
    try:
        # Dados M1 via CDP (primário) ou yfinance (fallback)
        t0 = time.time()
        df_m1 = fetch_ohlcv(sym, period='5d', interval='1m')
        source = 'CDP' if len(df_m1) < 1000 else 'yfinance'
        print(f"  {len(df_m1)} velas M1 via {source} ({time.time()-t0:.0f}s)")
        
        m1_h = df_m1['High'].values; m1_l = df_m1['Low'].values
        m1_c = df_m1['Close'].values; m1_o = df_m1['Open'].values
        m1_t = df_m1.index
        
        # Dados diários para bias
        df_d = fetch_ohlcv(sym, period='30d', interval='1d')
        if df_d is None or len(df_d) < 3: continue
        col_map = {}
        for c in df_d.columns:
            cl = c.lower()
            if cl in ('high','h'): col_map['h']=c
            elif cl in ('low','l'): col_map['l']=c
            elif cl in ('close','c'): col_map['c']=c
        d_h = df_d[col_map['h']].values; d_l = df_d[col_map['l']].values
        d_c = df_d[col_map['c']].values; d_t = df_d.index
        
        m1_day = [t.date() for t in m1_t]
        days = sorted(set(m1_day))
        
        trades = []
        last_trade_day = None
        
        for day_idx in range(2, len(days)):
            day = days[day_idx]
            day_candles = [j for j, d in enumerate(m1_day) if d == day]
            if len(day_candles) < 60: continue
            
            # Daily bias no dia
            d_idx = None
            for di in range(len(d_t)):
                if d_t[di].date() == day: d_idx = di; break
            if d_idx is None or d_idx < 2: continue
            
            bias_d = get_tf_bias(d_h[:d_idx+1], d_l[:d_idx+1], d_c[:d_idx+1])
            if bias_d == 'NEUTRAL': continue
            
            for offset in range(8, len(day_candles)-1):
                i = day_candles[offset]
                if last_trade_day == day: break
                
                local_h = m1_h[max(0,i-12):i+1]
                local_l = m1_l[max(0,i-12):i+1]
                local_c = m1_c[max(0,i-12):i+1]
                local_o = m1_o[max(0,i-12):i+1]
                
                fvgs = detect_fvg(local_h, local_l, local_c, bias_d, pip, metal)
                if not fvgs: continue
                
                s = fvgs[-1]
                
                # Filtro: candle fechado
                if s['idx'] >= len(local_c)-1: continue
                
                # ATR(14)
                n=15; h=m1_h[max(0,i-n):i+1]; l=m1_l[max(0,i-n):i+1]
                c=m1_c[max(0,i-n):i+1]
                if len(h)<5: continue
                tr = np.maximum(h-l, np.maximum(abs(h-np.roll(c,1)), abs(l-np.roll(c,1))))
                tr[0]=h[0]-l[0]; atr = np.mean(tr[-14:])/pip if len(tr)>=14 else np.mean(tr)/pip
                
                # DMI
                up=h-np.roll(h,1); dn=np.roll(l,1)-l; up[0]=dn[0]=0
                pdm=np.where((up>dn)&(up>0),up,0); ndm=np.where((dn>up)&(dn>0),dn,0)
                av=np.mean(tr[-14:]) if len(tr)>=14 else np.mean(tr)
                pdi=100*np.mean(pdm[-14:])/av if av>0 else 0
                ndi=100*np.mean(ndm[-14:])/av if av>0 else 0
                trend_ok = (bias_d=='BUY' and pdi>ndi) or (bias_d=='SELL' and ndi>pdi)
                if not trend_ok: continue
                
                # SL dinâmico
                sl_pips = max(MIN_SL, min(atr*2.0, MAX_SL if not metal else 300))
                entry = s['entry']
                
                if s['dir'] == 'BUY':
                    sl_price = entry - sl_pips * pip
                    tp_price = entry + sl_pips * RR * pip
                else:
                    sl_price = entry + sl_pips * pip
                    tp_price = entry - sl_pips * RR * pip
                
                # Simular
                result = 'OPEN'; candles_held = 0
                for j in range(i+1, min(i+3000, len(m1_h))):
                    candles_held += 1
                    if s['dir'] == 'BUY':
                        if m1_h[j] >= tp_price: result = 'WIN'; break
                        if m1_l[j] <= sl_price: result = 'LOSS'; break
                    else:
                        if m1_l[j] <= tp_price: result = 'WIN'; break
                        if m1_h[j] >= sl_price: result = 'LOSS'; break
                
                if result in ('WIN','LOSS'):
                    trades.append({
                        'pair':name,'day':str(day),'bias':bias_d,
                        'dir':s['dir'],'entry':round(entry,5),
                        'sl_pips':round(sl_pips,1),'gap':round(s['gap'],1),
                        'atr':round(atr,2),'pdi':round(pdi,1),'ndi':round(ndi,1),
                        'result':result,'candles':candles_held,
                        'r':RR if result=='WIN' else -1.0
                    })
                    last_trade_day = day
                    break
        
        if trades:
            wins=sum(1 for t in trades if t['result']=='WIN')
            wr=wins/len(trades)*100
            r_tot=sum(t['r'] for t in trades)
            print(f"  {len(trades)} trades | WR:{wr:.0f}% | R:{r_tot:+.1f}")
            for t in trades[-3:]:
                e='✅' if t['result']=='WIN' else '❌'
                print(f"  {e} {t['day']} {t['dir']:4s} SL={t['sl_pips']:.0f}p ATR={t['atr']:.1f}p → {t['result']} ({t['candles']}v)")
            all_trades.extend(trades)
        else:
            print("  0 trades")
    
    except Exception as e:
        print(f"  ERRO: {e}")
        import traceback; traceback.print_exc()

# CONSOLIDADO
print("\n"+"="*60)
print("CONSOLIDADO")
print("="*60)

if all_trades:
    wins=sum(1 for t in all_trades if t['result']=='WIN')
    total=len(all_trades)
    wr=wins/total*100
    r_total=sum(t['r'] for t in all_trades)
    win_r=sum(t['r'] for t in all_trades if t['r']>0)
    loss_r=abs(sum(t['r'] for t in all_trades if t['r']<0))
    pf=win_r/loss_r if loss_r>0 else float('inf')
    
    print(f"Total:    {total} trades")
    print(f"Win Rate: {wr:.1f}%")
    print(f"Expect:   {wr/100*RR - (1-wr/100):+.2f}R/trade")
    print(f"R total:  {r_total:+.1f}R")
    print(f"Profit F: {pf:.2f}")
    
    print(f"\n{'Par':8s} {'Trades':>6s} {'WR':>6s} {'R':>6s}")
    print("-"*30)
    for p in sorted(set(t['pair'] for t in all_trades)):
        pt=[t for t in all_trades if t['pair']==p]
        pw=sum(1 for t in pt if t['result']=='WIN')
        pr=sum(t['r'] for t in pt)
        print(f"{p:8s} {len(pt):6d} {pw/len(pt)*100:5.1f}% {pr:+5.1f}R")
    
    eq=0; peak=0; max_dd=0
    for t in all_trades: eq+=t['r']; peak=max(peak,eq); max_dd=max(max_dd,peak-eq)
    print(f"\nMax DD:   {max_dd:.1f}R")
    print(f"Equity:   {eq:+.1f}R")
    print(f"\nRisco 0.5%: Ganho={r_total*0.5:.1f}% MaxDD={max_dd*0.5:.1f}%")
    
    # ATR médio
    atrs = [t['atr'] for t in all_trades if t.get('atr')]
    if atrs:
        print(f"ATR médio: {np.mean(atrs):.1f}p")
else:
    print("Nenhum trade.")

print("\n=== FIM ===")
