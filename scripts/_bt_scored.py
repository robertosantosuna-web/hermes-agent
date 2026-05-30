#!/usr/bin/env python3
"""BACKTEST 30 DIAS — FVG Quality Scoring"""
import yfinance as yf, numpy as np, pandas as pd, sys
from datetime import datetime, timedelta
sys.path.insert(0, '/home/roberto/.hermes/scripts')
from fvg_quality import is_fvg_valid, find_swing_levels

RR=3.0; MIN_SL=10; MAX_SL=30; ADX_MIN=20
PAIRS = {
    'EURUSD':('EURUSD=X',0.0001),'GBPUSD':('GBPUSD=X',0.0001),
    'USDJPY':('USDJPY=X',0.01),'GBPJPY':('GBPJPY=X',0.01),
    'EURJPY':('EURJPY=X',0.01),'USDCAD':('USDCAD=X',0.0001),
    'XAUUSD':('GC=F',0.01,True),
}

def tf_bias(h,l,c):
    if len(h)<3: return 'NEUTRAL'
    ph,pl=h[-3],l[-3]; ch,cl,cc=h[-2],l[-2],c[-2]
    if ch>ph and cc<ph: return 'SELL'
    if cl<pl and cc>pl: return 'BUY'
    if ch>ph and cc>ph: return 'BUY'
    if cl<pl and cc<pl: return 'SELL'
    return 'NEUTRAL'

def det_fvg(h,l,c,d,pip,mtl=False):
    n=len(c); mg=100 if mtl else 1.0; out=[]
    for i in range(6,n-1):
        if d=='BUY' and l[i]>h[i-2]:
            g=(l[i]-h[i-2])/pip
            if g>=mg: out.append(dict(dir='BUY',entry=c[i],gap=g,idx=i))
        if d=='SELL' and h[i]<l[i-2]:
            g=(l[i-2]-h[i])/pip
            if g>=mg: out.append(dict(dir='SELL',entry=c[i],gap=g,idx=i))
    return out

def calc_adx_dmi(h,l,c):
    n=len(h); tr=np.zeros(n); pdm=np.zeros(n); ndm=np.zeros(n)
    for i in range(1,n):
        tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
        up=h[i]-h[i-1]; dn=l[i-1]-l[i]
        if up>dn and up>0: pdm[i]=up
        if dn>up and dn>0: ndm[i]=dn
    atr14=np.zeros(n); pdi14=np.zeros(n); ndi14=np.zeros(n); dx=np.zeros(n); adx=np.zeros(n)
    for i in range(14,n):
        atr14[i]=np.mean(tr[i-13:i+1])
        pdi14[i]=100*np.mean(pdm[i-13:i+1])/atr14[i] if atr14[i]>0 else 0
        ndi14[i]=100*np.mean(ndm[i-13:i+1])/atr14[i] if atr14[i]>0 else 0
    for i in range(14,n):
        denom=pdi14[i]+ndi14[i]
        dx[i]=100*abs(pdi14[i]-ndi14[i])/denom if denom>0 else 0
    for i in range(28,n): adx[i]=np.mean(dx[i-13:i+1])
    return adx,pdi14,ndi14

def simulate(m1_h,m1_l,i,entry,slp,direction,pip):
    if direction=='BUY': sl=entry-slp*pip; tp=entry+slp*RR*pip
    else: sl=entry+slp*pip; tp=entry-slp*RR*pip
    for j in range(i+1,min(i+3000,len(m1_h))):
        if direction=='BUY':
            if m1_h[j]>=tp: return 'WIN'
            if m1_l[j]<=sl: return 'LOSS'
        else:
            if m1_l[j]<=tp: return 'WIN'
            if m1_h[j]>=sl: return 'LOSS'
    return 'OPEN'

def fetch_m1_chunked(sym, days=30):
    all_data = []
    for i in range(5):
        end = datetime.now() - timedelta(days=i*7)
        start = end - timedelta(days=7)
        df = yf.Ticker(sym).history(start=start, end=end, interval='1m')
        if len(df) > 0: all_data.append(df)
    if not all_data: return None
    full = pd.concat(all_data)
    return full[~full.index.duplicated()].sort_index()

print('='*60)
print('BACKTEST 30 DIAS — FVG Quality Scoring (min_score=55)')
print(datetime.now().strftime('%d/%m %H:%M'))
print('='*60)

all_baseline=[]; all_scored=[]

for name, cfg in PAIRS.items():
    sym=cfg[0]; pip=cfg[1]; mtl=len(cfg)>2
    print('\n--- ' + name + ' ---')
    try:
        print('  Baixando 30d M1...', end=' ', flush=True)
        df_m1 = fetch_m1_chunked(sym, 30)
        if df_m1 is None or len(df_m1) < 1000: print('falhou'); continue
        print(str(len(df_m1)) + ' velas')
        
        m1_h=df_m1['High'].values; m1_l=df_m1['Low'].values
        m1_c=df_m1['Close'].values; m1_o=df_m1['Open'].values
        m1_t=df_m1.index; m1_day=[t.date() for t in m1_t]
        days=sorted(set(m1_day))
        
        adx,pdi,ndi = calc_adx_dmi(m1_h,m1_l,m1_c)
        
        df_d=yf.Ticker(sym).history(period='30d',interval='1d')
        cm={c.lower():c for c in df_d.columns}
        d_h=df_d[cm.get('high','High')].values
        d_l=df_d[cm.get('low','Low')].values
        d_c=df_d[cm.get('close','Close')].values
        d_t=df_d.index
        
        bl=[]; sc=[]
        
        for di in range(5,len(days)):
            day=days[di]
            dc=[j for j,d in enumerate(m1_day) if d==day]
            if len(dc)<60: continue
            dd=None
            for ddi in range(len(d_t)):
                if d_t[ddi].date()==day: dd=ddi; break
            if dd is None or dd<3: continue
            b=tf_bias(d_h[:dd+1],d_l[:dd+1],d_c[:dd+1])
            if b=='NEUTRAL': continue
            
            for off in range(8,len(dc)-1):
                i=dc[off]
                if i<28: continue
                adx_i=adx[i]; pdi_i=pdi[i]; ndi_i=ndi[i]
                trend_adx=adx_i>ADX_MIN
                trend_dmi=(b=='BUY' and pdi_i>ndi_i) or (b=='SELL' and ndi_i>pdi_i)
                if not trend_dmi or not trend_adx: continue
                
                lh=m1_h[max(0,i-20):i+1]; ll=m1_l[max(0,i-20):i+1]
                lc=m1_c[max(0,i-20):i+1]; lo=m1_o[max(0,i-20):i+1]
                
                fvgs=det_fvg(lh,ll,lc,b,pip,mtl)
                if not fvgs: continue
                
                for s in fvgs:
                    if s['idx']>=len(lc)-1: continue
                    
                    # FVG Quality Score
                    valid, det = is_fvg_valid(lh, ll, lc, s['idx'], s['dir'], pip, mtl, 55)
                    
                    entry=s['entry']
                    slp=max(MIN_SL,min(adx_i/10*2,MAX_SL if not mtl else 300))
                    if slp<MIN_SL: slp=MIN_SL
                    
                    res=simulate(m1_h,m1_l,i,entry,slp,s['dir'],pip)
                    if res not in ('WIN','LOSS'): continue
                    
                    R=RR if res=='WIN' else -1
                    t=dict(pair=name,day=str(day),dir=s['dir'],res=res,R=R,sl=slp,
                           score=det.get('score',0),zone=det.get('zone','?'),
                           trend=det.get('trend','?'),touch=det.get('touch','?'))
                    
                    bl.append(t)  # baseline (sem score)
                    if valid: sc.append(t)  # com score
                
                break
        
        w_bl=sum(1 for t in bl if t['res']=='WIN')
        w_sc=sum(1 for t in sc if t['res']=='WIN')
        print(f'  Baseline:{len(bl)}t/{w_bl}w | Scored:{len(sc)}t/{w_sc}w')
        all_baseline.extend(bl); all_scored.extend(sc)
    
    except Exception as e:
        print('  ERRO: ' + str(e)[:80])

def report(trades, label):
    if not trades: return
    w=sum(1 for t in trades if t['res']=='WIN')
    total=len(trades); wr=w/total*100; rt=sum(x['R'] for x in trades)
    wr2=sum(x['R'] for x in trades if x['R']>0)
    lr=abs(sum(x['R'] for x in trades if x['R']<0))
    pf=wr2/lr if lr>0 else float('inf')
    exp=wr/100*RR - (1-wr/100)
    avg_score=np.mean([t.get('score',0) for t in trades])
    print(f'{label:22s} {total:4d}t  {wr:4.0f}% WR  {rt:+6.1f}R  PF={pf:.2f}  Exp={exp:+.2f}R  Score={avg_score:.0f}')

print('\n' + '='*60)
print('RESULTADOS 30 DIAS — FVG Quality Score')
print('='*60)
report(all_baseline, 'BASELINE (todos FVG)')
report(all_scored, 'SCORED (min 55pts)')

if all_baseline and all_scored:
    reduc = (1-len(all_scored)/len(all_baseline))*100
    print(f'\nScoring eliminou {reduc:.0f}% dos trades')

print('\nFIM')
