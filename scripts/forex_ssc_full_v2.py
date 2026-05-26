#!/usr/bin/env python3
"""
SSC Full Strategy Backtest
Combina: H1 Trend → Wyckoff Range → Sweep → CHoCH → FVG
"""
import yfinance as yf, numpy as np, json
from datetime import timedelta
from collections import defaultdict

PAIRS = {
    'GBP/USD': {'s':'GBPUSD=X','pv':0.0001},
    'AUD/USD': {'s':'AUDUSD=X','pv':0.0001},
    'NZD/USD': {'s':'NZDUSD=X','pv':0.0001},
    'EUR/USD': {'s':'EURUSD=X','pv':0.0001},
}
RR=3.0; MIN_FVG=1.0

def h1_structure(df_h1):
    """H1: identifica estrutura (BULLISH, BEARISH, RANGE)"""
    if len(df_h1)<20: return None
    h=df_h1['High'].values.astype(float)[-20:]
    l=df_h1['Low'].values.astype(float)[-20:]
    
    # Encontrar swings
    sh,sl=[],[]
    for i in range(2,len(h)-2):
        if h[i]>h[i-1] and h[i]>h[i-2] and h[i]>h[i+1] and h[i]>h[i+2]: sh.append(h[i])
        if l[i]<l[i-1] and l[i]<l[i-2] and l[i]<l[i+1] and l[i]<l[i+2]: sl.append(l[i])
    
    if len(sh)<2 or len(sl)<2: return None
    
    # Higher highs + higher lows = bullish
    if sh[-1]>sh[-2] and sl[-1]>sl[-2]: return 'BULLISH'
    # Lower highs + lower lows = bearish  
    if sh[-1]<sh[-2] and sl[-1]<sl[-2]: return 'BEARISH'
    return 'RANGE'

def wyckoff_phase(df_m15, trend):
    """Detecta fase Wyckoff: range + manipulação (sweep)"""
    if len(df_m15)<30: return None
    
    # Últimas 20 velas para range
    df20 = df_m15.iloc[-20:]
    h=df20['High'].values.astype(float)
    l=df20['Low'].values.astype(float)
    c=df20['Close'].values.astype(float)
    o=df20['Open'].values.astype(float)
    
    # Range (excluindo últimas 3 velas pra evitar viés)
    range_h = max(h[:-3]); range_l = min(l[:-3])
    range_size = (range_h - range_l) / 0.0001  # pips
    
    if range_size < 5: return None  # Range muito pequeno
    
    # Procurar sweep (manipulação) nas últimas 5 velas
    for i in range(len(df20)-5, len(df20)):
        ch, cl, cc, co = h[i], l[i], c[i], o[i]
        body = abs(cc-co)
        wick_low = min(co,cc)-cl
        wick_high = ch-max(co,cc)
        
        if trend == 'BULLISH':
            # Sweep de baixa: rompe range low e fecha de volta
            if cl < range_l and cc > range_l and wick_low > body*0.8:
                return {'phase':'MANIPULATION','type':'BUY',
                       'range_h':range_h,'range_l':range_l,'sweep_idx':i}
        
        elif trend == 'BEARISH':
            # Sweep de alta: rompe range high e fecha de volta
            if ch > range_h and cc < range_h and wick_high > body*0.8:
                return {'phase':'MANIPULATION','type':'SELL',
                       'range_h':range_h,'range_l':range_l,'sweep_idx':i}
    
    return None

def detect_choch_fvg(df_m15, sweep_info, pv):
    """CHoCH + FVG após sweep confirmado"""
    df30 = df_m15.iloc[-30:]
    bi = len(df_m15)-30
    h=df30['High'].values.astype(float); l=df30['Low'].values.astype(float)
    c=df30['Close'].values.astype(float)
    
    sh,sl_sw=[],[]
    for i in range(2,len(h)-2):
        if h[i]>h[i-1] and h[i]>h[i-2] and h[i]>h[i+1] and h[i]>h[i+2]: sh.append((i,h[i]))
        if l[i]<l[i-1] and l[i]<l[i-2] and l[i]<l[i+1] and l[i]<l[i+2]: sl_sw.append((i,l[i]))
    
    sigs=[]
    direction = sweep_info['type']
    
    if direction=='BUY' and sh:
        lsi,lsv=sh[-1]
        for i in range(lsi+1,len(c)):
            if c[i]>lsv:
                for j in range(max(0,i-4),i-1):
                    if j+2<len(h) and h[j]<l[j+2]:
                        g=(l[j+2]-h[j])/pv
                        if g>=MIN_FVG:
                            sigs.append({'t':'BUY','e':l[j+2],'g':g,'i':bi+i})
    elif direction=='SELL' and sl_sw:
        lsi,lsv=sl_sw[-1]
        for i in range(lsi+1,len(c)):
            if c[i]<lsv:
                for j in range(max(0,i-4),i-1):
                    if j+2<len(h) and l[j]>h[j+2]:
                        g=(l[j]-h[j+2])/pv
                        if g>=MIN_FVG:
                            sigs.append({'t':'SELL','e':h[j+2],'g':g,'i':bi+i})
    return sigs

def sim(df, sig, pv):
    sp=max(sig['g'],2.0); tp=sp*RR
    if sig['t']=='BUY': sl=sig['e']-sp*pv; tpr=sig['e']+tp*pv
    else: sl=sig['e']+sp*pv; tpr=sig['e']-tp*pv
    for i in range(sig['i']+1,len(df)):
        lo=float(df.iloc[i]['Low']); hi=float(df.iloc[i]['High'])
        if sig['t']=='BUY':
            if lo<=sl: return 'L',-sp
            if hi>=tpr: return 'W',tp
        else:
            if hi>=sl: return 'L',-sp
            if lo<=tpr: return 'W',tp
    return 'O',0

print("═"*65)
print("  BACKTEST SSC COMPLETO")
print("  H1 Structure → Wyckoff → Sweep → CHoCH → FVG")
print("═"*65)

# Versões pra comparar
variants = {
    'CHoCH+FVG (baseline)': {'use_h1':False,'use_wyckoff':False},
    '+ H1 Trend': {'use_h1':True,'use_wyckoff':False},
    '+ H1 + Wyckoff/Sweep': {'use_h1':True,'use_wyckoff':True},
}

def trend_to_dir(t):
    return {'BULLISH':'BUY','BEARISH':'SELL'}.get(t,'BUY')

all_results = {}

for vname, vcfg in variants.items():
    print(f"\n{'─'*50}")
    print(f"  {vname}")
    print(f"{'─'*50}")
    
    total_w,total_l,total_p=0,0,0.0
    
    for pair,cfg in PAIRS.items():
        pv=cfg['pv']
        df_m15 = yf.Ticker(cfg['s']).history(period='30d',interval='15m')
        df_h1 = yf.Ticker(cfg['s']).history(period='30d',interval='1h')
        
        if len(df_m15)<60: continue
        
        w,l,pn=0,0,0.0
        seen=set()
        
        for idx in range(40, len(df_m15)-10, 4):
            window = df_m15.iloc[:idx+30]
            sig_time = window.index[-1]
            
            # H1 trend filter
            if vcfg['use_h1']:
                h1w = df_h1[df_h1.index<=sig_time]
                trend = h1_structure(h1w)
                if not trend or trend=='RANGE': continue
            else:
                trend = 'BULLISH'  # fallback: accept both
            
            # Wyckoff/Sweep filter
            if vcfg['use_wyckoff']:
                wyckoff = wyckoff_phase(window, trend)
                if not wyckoff: continue
            else:
                wyckoff = {'type':'BUY'}  # fallback
            
            # CHoCH + FVG
            sigs = detect_choch_fvg(window, wyckoff, pv)
            
            for s in sigs:
                key=(s['t'],round(s['e'],5))
                if key in seen: continue
                seen.add(key)
                
                # Se H1 ativo, filtrar direção
                if vcfg['use_h1'] and trend and s['t']!=trend_to_dir(trend):
                    continue
                
                r,p=sim(df_m15, s, pv)
                if r=='O': continue
                if r=='W': w+=1; pn+=p
                else: l+=1; pn+=p
        
        t=w+l
        wr=w/t*100 if t else 0
        if t>0:
            print(f"  {pair:10s}: {t:3d}T WR={wr:5.1f}% PnL={pn:+7.1f}p")
        
        total_w+=w; total_l+=l; total_p+=pn
    
    tt=total_w+total_l
    wr=total_w/tt*100 if tt else 0
    all_results[vname]={'t':tt,'w':total_w,'l':total_l,'wr':round(wr,1),'pnl':round(total_p,1)}
    print(f"  {'─'*40}")
    print(f"  TOTAL: {tt}T | {total_w}W/{total_l}L | WR={wr:.1f}% | PnL={total_p:+.0f}p")

# Ranking
print(f"\n{'═'*65}")
print(f"  COMPARATIVO FINAL")
print(f"{'═'*65}")
ranked=sorted(all_results.items(), key=lambda x: (x[1]['wr'], x[1]['pnl']), reverse=True)
for i,(name,r) in enumerate(ranked):
    print(f"  {i+1}. {name:25s}: {r['t']:4d}T WR={r['wr']:5.1f}% PnL={r['pnl']:+8.1f}p")

json.dump(all_results, open('/home/roberto/.hermes/forex/ssc_full_backtest.json','w'), indent=2)
