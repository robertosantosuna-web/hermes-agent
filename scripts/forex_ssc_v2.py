#!/usr/bin/env python3
"""SSC Backtest v2 — filtros relaxados + debug"""
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import sys, json

PAIRS = {
    'GBP/USD': {'sym': 'GBPUSD=X', 'pip': 0.0001},
    'AUD/USD': {'sym': 'AUDUSD=X', 'pip': 0.0001},
    'NZD/USD': {'sym': 'NZDUSD=X', 'pip': 0.0001},
    'EUR/USD': {'sym': 'EURUSD=X', 'pip': 0.0001},
}

RR = 3.0
KILLZONES_BRT = [(4, 12)]  # 4h-12h BRT (Asia+London)

def get_h1_trend(df_h1):
    if len(df_h1) < 25: return None
    c = df_h1['Close'].values.astype(float)
    ema = np.zeros(len(c)); alpha=2.0/21
    ema[0]=c[0]
    for i in range(1,len(c)): ema[i]=alpha*c[i]+(1-alpha)*ema[i-1]
    
    h=df_h1['High'].values.astype(float)[-20:]; l=df_h1['Low'].values.astype(float)[-20:]
    sh,sl_sw=[],[]
    for i in range(2,len(h)-2):
        if h[i]>h[i-1] and h[i]>h[i-2] and h[i]>h[i+1] and h[i]>h[i+2]: sh.append(i)
        if l[i]<l[i-1] and l[i]<l[i-2] and l[i]<l[i+1] and l[i]<l[i+2]: sl_sw.append(i)
    
    cur=c[-1]; ema_cur=ema[-1]
    if cur>ema_cur: return 'BULLISH'
    if cur<ema_cur: return 'BEARISH'
    return None

def detect_sweep(df20, trend):
    """Sweep relaxado: qualquer candle que testa extremo e reverte"""
    h=df20['High'].values.astype(float); l=df20['Low'].values.astype(float)
    c=df20['Close'].values.astype(float); o=df20['Open'].values.astype(float)
    
    range_h = max(h[:-3]); range_l = min(l[:-3])
    
    for i in range(len(df20)-5, len(df20)):
        ch, cl, cc, co = h[i], l[i], c[i], o[i]
        body = abs(cc-co)
        
        if trend == 'BULLISH':
            if cl < range_l and cc > range_l:
                wick = min(co,cc) - cl
                if wick > body * 0.5:  # Relaxado de 1.5x pra 0.5x
                    return 'BUY'
        elif trend == 'BEARISH':
            if ch > range_h and cc < range_h:
                wick = ch - max(co,cc)
                if wick > body * 0.5:
                    return 'SELL'
    return None

def detect_fvg(df_after, pip_v):
    """FVG ICT após sweep"""
    if len(df_after) < 5: return None
    h=df_after['High'].values.astype(float); l=df_after['Low'].values.astype(float)
    
    for j in range(len(h)-2):
        if h[j] < l[j+2]:  # Bullish
            g=(l[j+2]-h[j])/pip_v
            if g>=1.0: return {'t':'BUY','e':l[j+2],'g':g}
        if l[j] > h[j+2]:  # Bearish
            g=(l[j]-h[j+2])/pip_v
            if g>=1.0: return {'t':'SELL','e':h[j+2],'g':g}
    return None

def sim(df, sig_idx, sig, pip_v):
    sl_p=max(sig['g'],2.0); tp_p=sl_p*RR
    if sig['t']=='BUY': sl=sig['e']-sl_p*pip_v; tp=sig['e']+tp_p*pip_v
    else: sl=sig['e']+sl_p*pip_v; tp=sig['e']-tp_p*pip_v
    
    for i in range(sig_idx+1, len(df)):
        lo=float(df.iloc[i]['Low']); hi=float(df.iloc[i]['High'])
        if sig['t']=='BUY':
            if lo<=sl: return 'L',-sl_p
            if hi>=tp: return 'W',tp_p
        else:
            if hi>=sl: return 'L',-sl_p
            if lo<=tp: return 'W',tp_p
    return 'O',0

print("═"*60)
print("  BACKTEST SSC v2 (relaxado)")
print("═"*60)

total={'w':0,'l':0,'p':0}
for pair,cfg in PAIRS.items():
    pv=cfg['pip']
    print(f"\n{pair}...")
    
    df=yf.Ticker(cfg['sym']).history(period='30d',interval='15m')
    df_h1=yf.Ticker(cfg['sym']).history(period='30d',interval='1h')
    
    w,l,pn=0,0,0
    step=4
    skipped={'trend':0,'killzone':0,'sweep':0,'fvg':0,'total':0}
    
    for si in range(100, len(df)-30, step):
        skipped['total']+=1
        win=df.iloc[:si+30]
        ct=win.index[-1]; dt_brt=ct-timedelta(hours=3)
        
        # Killzone
        h=dt_brt.hour; ok=False
        for s,e in KILLZONES_BRT:
            if s<=h<e: ok=True; break
        if not ok: skipped['killzone']+=1; continue
        
        # Trend
        h1w=df_h1[df_h1.index<=ct]
        trend=get_h1_trend(h1w)
        if not trend: skipped['trend']+=1; continue
        
        # Sweep
        sw=detect_sweep(win.iloc[-20:], trend)
        if not sw: skipped['sweep']+=1; continue
        
        # FVG após sweep
        fvg=detect_fvg(win.iloc[-20:], pv)
        if not fvg: skipped['fvg']+=1; continue
        if fvg['t']!=sw: continue
        
        r,p=sim(df, si+10, fvg, pv)
        if r=='W': w+=1; pn+=p
        elif r=='L': l+=1; pn+=p
    
    t=w+l
    wr=w/t*100 if t else 0
    print(f"  {t}T | {w}W/{l}L | WR={wr:.0f}% | PnL={pn:+.1f}p")
    print(f"  Debug: {skipped}")
    total['w']+=w; total['l']+=l; total['p']+=pn

tt=total['w']+total['l']
wr=total['w']/tt*100 if tt else 0
print(f"\n{'═'*60}")
print(f"  TOTAL: {tt}T | {total['w']}W/{total['l']}L | WR={wr:.0f}% | PnL={total['p']:+.1f}p")
print(f"{'═'*60}")
