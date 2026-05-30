#!/usr/bin/env python3
"""BACKTEST 30 DIAS — Sistema Multi-Agente"""
import yfinance as yf, numpy as np, pandas as pd, sys
from datetime import datetime, timedelta
sys.path.insert(0, '/home/roberto/.hermes/scripts')
from multi_agent import ConfluenciaAgent
from fvg_quality import is_fvg_valid

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
    return adx,pdi14,ndi14,atr14

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

agent = ConfluenciaAgent()

print('='*60)
print('BACKTEST 30 DIAS — Multi-Agente')
print(datetime.now().strftime('%d/%m %H:%M'))
print('='*60)

all_A=[]; all_AG=[]

for name, cfg in PAIRS.items():
    sym=cfg[0]; pip=cfg[1]; mtl=len(cfg)>2
    print('\n--- ' + name + ' ---')
    try:
        print('  Baixando 30d M1...', end=' ', flush=True)
        df_m1 = fetch_m1_chunked(sym, 30)
        if df_m1 is None or len(df_m1) < 1000: print('falhou'); continue
        days_total = len(set(df_m1.index.date))
        print(str(len(df_m1)) + ' velas, ' + str(days_total) + ' dias')
        
        m1_h=df_m1['High'].values; m1_l=df_m1['Low'].values
        m1_c=df_m1['Close'].values; m1_o=df_m1['Open'].values
        m1_t=df_m1.index; m1_day=[t.date() for t in m1_t]
        days=sorted(set(m1_day))
        
        adx,pdi,ndi,atr14 = calc_adx_dmi(m1_h,m1_l,m1_c)
        
        df_d=yf.Ticker(sym).history(period='30d',interval='1d')
        cm={c.lower():c for c in df_d.columns}
        d_h=df_d[cm.get('high','High')].values
        d_l=df_d[cm.get('low','Low')].values
        d_c=df_d[cm.get('close','Close')].values
        d_t=df_d.index
        
        a_t=[]; ag_t=[]
        
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
                
                # Modelo A: DMI + ADX
                trend_dmi=(b=='BUY' and pdi[i]>ndi[i]) or (b=='SELL' and ndi[i]>pdi[i])
                
                lh=m1_h[max(0,i-20):i+1]; ll=m1_l[max(0,i-20):i+1]
                lc=m1_c[max(0,i-20):i+1]
                fvgs=det_fvg(lh,ll,lc,b,pip,mtl)
                if not fvgs: continue
                
                for s in fvgs:
                    if s['idx']>=len(lc)-1: continue
                    entry=s['entry']
                    slp=max(MIN_SL,min(atr14[i]/pip*2,MAX_SL if not mtl else 300))
                    if slp<MIN_SL: slp=MIN_SL
                    res=simulate(m1_h,m1_l,i,entry,slp,s['dir'],pip)
                    if res not in ('WIN','LOSS'): continue
                    R=RR if res=='WIN' else -1
                    
                    # Modelo A
                    if trend_dmi and adx[i]>ADX_MIN:
                        a_t.append(dict(pair=name,day=str(day),dir=s['dir'],res=res,R=R,sl=slp))
                    
                    # Modelo AGENT
                    decision, conf, ag_sig = agent.analyze(
                        name, m1_h[:i+1], m1_l[:i+1], m1_c[:i+1], b, pip, mtl)
                    if decision != 'NEUTRAL' and ag_sig:
                        res2=simulate(m1_h,m1_l,i,ag_sig['entry'],slp,ag_sig['direction'],pip)
                        if res2 in ('WIN','LOSS'):
                            R2=RR if res2=='WIN' else -1
                            ag_t.append(dict(pair=name,day=str(day),dir=ag_sig['direction'],
                                            res=res2,R=R2,sl=slp,conf=conf))
                
                break
        
        w_a=sum(1 for t in a_t if t['res']=='WIN')
        w_ag=sum(1 for t in ag_t if t['res']=='WIN')
        print(f'  A:{len(a_t)}t/{w_a}w ({len(a_t)/max(days_total,1):.1f}/dia) | AG:{len(ag_t)}t/{w_ag}w ({len(ag_t)/max(days_total,1):.1f}/dia)')
        all_A.extend(a_t); all_AG.extend(ag_t)
    
    except Exception as e:
        print('  ERRO: ' + str(e)[:100])

def report(trades, label):
    if not trades: return
    w=sum(1 for t in trades if t['res']=='WIN')
    total=len(trades); wr=w/total*100; rt=sum(x['R'] for x in trades)
    wr2=sum(x['R'] for x in trades if x['R']>0)
    lr=abs(sum(x['R'] for x in trades if x['R']<0))
    pf=wr2/lr if lr>0 else float('inf')
    exp=wr/100*RR - (1-wr/100)
    avg_conf=np.mean([t.get('conf',0) for t in trades]) if trades else 0
    print(f'{label:25s} {total:4d}t  {wr:4.0f}% WR  {rt:+6.1f}R  PF={pf:.2f}  Exp={exp:+.2f}R  Conf={avg_conf:.0f}%')

print('\n' + '='*60)
print('RESULTADOS')
print('='*60)
report(all_A, 'MODELO A (DMI+ADX)')
report(all_AG, 'MULTI-AGENTE')
if all_A and all_AG:
    print(f'\nMulti-Agente: {len(all_AG)} trades vs {len(all_A)} baseline')
print('FIM')
