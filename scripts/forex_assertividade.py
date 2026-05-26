#!/usr/bin/env python3
"""
Backtest: CHoCH+FVG+CRT + 3 filtros de assertividade
1. H1 Trend Confirmation
2. S/R Level Proximity (swing high/low anterior)
3. Volume acima da média
"""
import yfinance as yf, numpy as np, json
from datetime import timedelta

PAIRS = {
    'GBP/USD': {'s':'GBPUSD=X','pv':0.0001},
    'AUD/USD': {'s':'AUDUSD=X','pv':0.0001},
    'NZD/USD': {'s':'NZDUSD=X','pv':0.0001},
    'EUR/USD': {'s':'EURUSD=X','pv':0.0001},
}
RR=3.0; MIN_FVG=1.0; CRT_PERC=0.8
SR_PROXIMITY_PIPS = 5  # distância máxima do nível S/R
VOL_PERIOD = 20

def is_crt(df, idx):
    if idx<20: return False
    rng=abs(float(df.iloc[idx]['High'])-float(df.iloc[idx]['Low']))
    recent=sorted([abs(float(df.iloc[i]['High'])-float(df.iloc[i]['Low'])) for i in range(idx-19,idx+1)])
    return rng>=recent[int(len(recent)*CRT_PERC)]

def crt_conf(df, idx):
    if idx+1>=len(df): return False
    h1=float(df.iloc[idx]['High']); l1=float(df.iloc[idx]['Low']); c2=float(df.iloc[idx+1]['Close'])
    return l1<=c2<=h1

def detect_at(df, anchor, pv):
    start=max(0,anchor-30)
    df30=df.iloc[start:anchor+1]
    if len(df30)<20: return []
    h=df30['High'].values.astype(float); l=df30['Low'].values.astype(float); c=df30['Close'].values.astype(float)
    sh,sl_sw=[],[]
    for i in range(2,len(h)-2):
        if h[i]>h[i-1] and h[i]>h[i-2] and h[i]>h[i+1] and h[i]>h[i+2]: sh.append((i,h[i]))
        if l[i]<l[i-1] and l[i]<l[i-2] and l[i]<l[i+1] and l[i]<l[i+2]: sl_sw.append((i,l[i]))
    sigs=[]
    if sh:
        lsi,lsv=sh[-1]
        for i in range(lsi+1,len(c)):
            if c[i]>lsv:
                for j in range(max(0,i-4),i-1):
                    if j+2<len(h) and h[j]<l[j+2]:
                        g=(l[j+2]-h[j])/pv
                        if g>=MIN_FVG: sigs.append({'t':'BUY','e':l[j+2],'g':g,'i':start+i,'choch_i':i})
    if sl_sw:
        lsi,lsv=sl_sw[-1]
        for i in range(lsi+1,len(c)):
            if c[i]<lsv:
                for j in range(max(0,i-4),i-1):
                    if j+2<len(h) and l[j]>h[j+2]:
                        g=(l[j]-h[j+2])/pv
                        if g>=MIN_FVG: sigs.append({'t':'SELL','e':h[j+2],'g':g,'i':start+i,'choch_i':i})
    return sigs

def h1_trend_ok(df_h1, sig_time, direction):
    """Filtro 1: H1 confirma direção"""
    h1w = df_h1[df_h1.index<=sig_time]
    if len(h1w)<20: return False
    h=h1w['High'].values.astype(float)[-20:]; l=h1w['Low'].values.astype(float)[-20:]
    sh_pos,sl_pos=[],[]
    for i in range(2,len(h)-2):
        if h[i]>h[i-1] and h[i]>h[i-2] and h[i]>h[i+1] and h[i]>h[i+2]: sh_pos.append(i)
        if l[i]<l[i-1] and l[i]<l[i-2] and l[i]<l[i+1] and l[i]<l[i+2]: sl_pos.append(i)
    if len(sh_pos)<2 or len(sl_pos)<2: return False
    
    bullish = h[sh_pos[-1]]>h[sh_pos[-2]] and l[sl_pos[-1]]>l[sl_pos[-2]]
    bearish = h[sh_pos[-1]]<h[sh_pos[-2]] and l[sl_pos[-1]]<l[sl_pos[-2]]
    
    if direction=='BUY' and bullish: return True
    if direction=='SELL' and bearish: return True
    return False

def near_sr_level(df, entry_price, direction, pv):
    """Filtro 2: entrada próxima de S/R (swing high/low anterior)"""
    h=df['High'].values.astype(float)
    l=df['Low'].values.astype(float)
    
    # Swings nos últimos 100 candles
    sh_vals, sl_vals = [], []
    for i in range(2, min(100, len(h))-2):
        if h[i]>h[i-1] and h[i]>h[i-2] and h[i]>h[i+1] and h[i]>h[i+2]: sh_vals.append(h[i])
        if l[i]<l[i-1] and l[i]<l[i-2] and l[i]<l[i+1] and l[i]<l[i+2]: sl_vals.append(l[i])
    
    if direction=='BUY':
        # Entrada perto de swing low (suporte)
        for sl_val in sl_vals[-5:]:
            if abs(entry_price - sl_val) < SR_PROXIMITY_PIPS * pv:
                return True
        # Ou perto de swing high rompido (resistência virada suporte)
        if len(sh_vals)>=2:
            for sh_val in sh_vals[-5:-1]:
                if abs(entry_price - sh_val) < SR_PROXIMITY_PIPS * pv:
                    return True
    else:
        # Entrada perto de swing high (resistência)
        for sh_val in sh_vals[-5:]:
            if abs(entry_price - sh_val) < SR_PROXIMITY_PIPS * pv:
                return True
        # Ou perto de swing low rompido
        if len(sl_vals)>=2:
            for sl_val in sl_vals[-5:-1]:
                if abs(entry_price - sl_val) < SR_PROXIMITY_PIPS * pv:
                    return True
    return False

def volume_ok(df, idx):
    """Filtro 3: candle CHoCH tem volume acima da média"""
    if 'Volume' not in df.columns: return True  # forex yahoo não tem volume
    
    vols = df['Volume'].values.astype(float)
    if idx<VOL_PERIOD: return True
    
    current_vol = vols[idx]
    avg_vol = np.mean(vols[max(0,idx-VOL_PERIOD):idx])
    
    return current_vol > avg_vol * 1.2  # 20% acima da média

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

# ═════════════════════════════════════════
# BACKTEST
# ═════════════════════════════════════════

variants = {
    'CRT (baseline)':        {'h1':False,'sr':False,'vol':False},
    'CRT + H1 Trend':        {'h1':True, 'sr':False,'vol':False},
    'CRT + S/R Levels':      {'h1':False,'sr':True, 'vol':False},
    'CRT + Volume':          {'h1':False,'sr':False,'vol':True},
    'CRT + H1 + S/R':        {'h1':True, 'sr':True, 'vol':False},
    'CRT + ALL 3':           {'h1':True, 'sr':True, 'vol':True},
}

print("═"*70)
print("  BACKTEST — ASSERTIVIDADE")
print("═"*70)

all_results = {}

for vname, vcfg in variants.items():
    print(f"\n{vname}...", end=' ', flush=True)
    
    tot_w,tot_l,tot_p=0,0,0.0
    
    for pair,cfg in PAIRS.items():
        pv=cfg['pv']
        df = yf.Ticker(cfg['s']).history(period='30d',interval='15m')
        df_h1 = yf.Ticker(cfg['s']).history(period='30d',interval='1h')
        if len(df)<60: continue
        
        w,l,pn=0,0,0.0
        seen=set()
        
        for idx in range(40, len(df)-10, 4):
            sigs = detect_at(df, idx, pv)
            
            for s in sigs:
                key=(s['t'],round(s['e'],5))
                if key in seen: continue
                seen.add(key)
                
                # CRT
                if not is_crt(df,s['i']): continue
                if not crt_conf(df,s['i']): continue
                
                sig_time = df.index[s['i']]
                
                # Filtro 1: H1
                if vcfg['h1']:
                    if not h1_trend_ok(df_h1, sig_time, s['t']):
                        continue
                
                # Filtro 2: S/R
                if vcfg['sr']:
                    window = df.iloc[max(0,s['i']-100):s['i']+1]
                    if not near_sr_level(window, s['e'], s['t'], pv):
                        continue
                
                # Filtro 3: Volume
                if vcfg['vol']:
                    if not volume_ok(df, s['i']):
                        continue
                
                r,p=sim(df, s, pv)
                if r=='O': continue
                if r=='W': w+=1; pn+=p
                else: l+=1; pn+=p
        
        tot_w+=w; tot_l+=l; tot_p+=pn
    
    tt=tot_w+tot_l
    wr=tot_w/tt*100 if tt else 0
    all_results[vname]={'t':tt,'w':tot_w,'l':tot_l,'wr':round(wr,1),'pnl':round(tot_p,1)}
    print(f"{tt}T WR={wr:.1f}% PnL={tot_p:+.0f}p")

# Ranking
print(f"\n{'═'*70}")
print(f"  RANKING FINAL")
print(f"{'═'*70}")
ranked=sorted(all_results.items(), key=lambda x: (x[1]['wr'], x[1]['pnl']), reverse=True)
for i,(name,r) in enumerate(ranked):
    bar='█'*int(r['wr']/5)
    print(f"  {i+1}. {name:25s}: {r['t']:4d}T | {r['w']}W/{r['l']}L | WR={r['wr']:5.1f}% | PnL={r['pnl']:+8.1f}p {bar}")

json.dump(all_results, open('/home/roberto/.hermes/forex/assertividade_backtest.json','w'), indent=2)
