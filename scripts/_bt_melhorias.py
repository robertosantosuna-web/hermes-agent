#!/usr/bin/env python3
"""Testa cada melhoria — cada FVG testado contra cada filtro"""
import yfinance as yf, numpy as np
from datetime import datetime

RR=3.0; MIN_SL=10; MAX_SL=30
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

def calc_atr_dmi(h,l,c,pip):
    n=15; hh=h[-n:]; ll=l[-n:]; cc=c[-n:]
    tr=np.maximum(hh-ll,np.maximum(abs(hh-np.roll(cc,1)),abs(ll-np.roll(cc,1))))
    tr[0]=hh[0]-ll[0]
    atr=np.mean(tr[-14:])/pip if len(tr)>=14 else np.mean(tr)/pip
    up=hh-np.roll(hh,1); dn=np.roll(ll,1)-ll; up[0]=dn[0]=0
    pdm=np.where((up>dn)&(up>0),up,0); ndm=np.where((dn>up)&(dn>0),dn,0)
    av=np.mean(tr[-14:]) if len(tr)>=14 else np.mean(tr)
    pdi=100*np.mean(pdm[-14:])/av if av>0 else 0
    ndi=100*np.mean(ndm[-14:])/av if av>0 else 0
    return atr,pdi,ndi

def rsi_val(c):
    dc=np.diff(c); gain=np.where(dc>0,dc,0); loss=np.where(dc<0,-dc,0)
    avg_gain=np.mean(gain[-14:]); avg_loss=np.mean(loss[-14:])
    if avg_loss==0: return 100
    return 100-(100/(1+avg_gain/avg_loss))

def is_engulf(o,h,l,c, direction):
    if len(o)<2: return False
    pb=abs(c[-2]-o[-2]); cb=abs(c[-1]-o[-1])
    if cb<pb*1.2: return False
    if direction=='BUY':
        return c[-2]<o[-2] and c[-1]>o[-1] and c[-1]>c[-2] and o[-1]<o[-2]
    else:
        return c[-2]>o[-2] and c[-1]<o[-1] and c[-1]<c[-2] and o[-1]>o[-2]

def simulate(m1_h,m1_l,i,entry,slp,tp_price,direction,pip,mtl):
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

print('='*60)
print('TESTE DE MELHORIAS — cada FVG testado isoladamente')
print(datetime.now().strftime('%d/%m %H:%M'))
print('='*60)

results = {
    '0_BASELINE': [],
    '1_RSI': [],
    '2_ENGOLFO': [],
    '3_2CANDLES': [],
    '4_RSI+ENG+2C': [],
}

for name, cfg in PAIRS.items():
    sym=cfg[0]; pip=cfg[1]; mtl=len(cfg)>2
    try:
        df_m1=yf.Ticker(sym).history(period='5d',interval='1m')
        if df_m1 is None or len(df_m1)<200: continue
        m1_h=df_m1['High'].values; m1_l=df_m1['Low'].values
        m1_c=df_m1['Close'].values; m1_o=df_m1['Open'].values
        m1_t=df_m1.index; m1_day=[t.date() for t in m1_t]
        days=sorted(set(m1_day))
        
        atr_A,pdi_A,ndi_A = calc_atr_dmi(m1_h,m1_l,m1_c,pip)
        
        df_d=yf.Ticker(sym).history(period='30d',interval='1d')
        cm={c.lower():c for c in df_d.columns}
        d_h=df_d[cm.get('high','High')].values
        d_l=df_d[cm.get('low','Low')].values
        d_c=df_d[cm.get('close','Close')].values
        d_t=df_d.index
        
        for di in range(3,len(days)):
            day=days[di]
            dc=[j for j,d in enumerate(m1_day) if d==day]
            if len(dc)<60: continue
            dd=None
            for ddi in range(len(d_t)):
                if d_t[ddi].date()==day: dd=ddi; break
            if dd is None or dd<2: continue
            b=tf_bias(d_h[:dd+1],d_l[:dd+1],d_c[:dd+1])
            if b=='NEUTRAL': continue
            trend_A=(b=='BUY' and pdi_A>ndi_A) or (b=='SELL' and ndi_A>pdi_A)
            if not trend_A: continue
            
            for off in range(8,len(dc)-1):
                i=dc[off]
                lh=m1_h[max(0,i-14):i+1]; ll=m1_l[max(0,i-14):i+1]
                lc=m1_c[max(0,i-14):i+1]; lo=m1_o[max(0,i-14):i+1]
                
                fvgs=det_fvg(lh,ll,lc,b,pip,mtl)
                if not fvgs: continue
                
                rsi_v=rsi_val(lc)
                eng_ok=is_engulf(lo,lh,ll,lc,b)
                
                for s in fvgs:
                    if s['idx']>=len(lc)-1: continue
                    c2_ok=(s['idx']<=len(lc)-3)
                    entry=s['entry']
                    slp=max(MIN_SL,min(atr_A*2.0,MAX_SL if not mtl else 300))
                    
                    res=simulate(m1_h,m1_l,i,entry,slp,0,s['dir'],pip,mtl)
                    if res not in ('WIN','LOSS'): continue
                    
                    R=RR if res=='WIN' else -1
                    t=dict(pair=name,day=str(day),dir=s['dir'],res=res,R=R,sl=slp)
                    
                    results['0_BASELINE'].append(t)
                    if (b=='BUY' and rsi_v>45) or (b=='SELL' and rsi_v<55):
                        results['1_RSI'].append(t)
                    if eng_ok:
                        results['2_ENGOLFO'].append(t)
                    if c2_ok:
                        results['3_2CANDLES'].append(t)
                    if ((b=='BUY' and rsi_v>45) or (b=='SELL' and rsi_v<55)) and eng_ok and c2_ok:
                        results['4_RSI+ENG+2C'].append(t)
                
                break  # 1 iteração por dia
    
    except Exception as e:
        pass

print('\nRESULTADOS:')
print('-'*55)
print('Filtro                  Trades  WR     R     PF')
print('-'*55)
for label, trades in sorted(results.items()):
    if not trades: continue
    w=sum(1 for t in trades if t['res']=='WIN')
    t=len(trades); wr=w/t*100; rt=sum(x['R'] for x in trades)
    wr2=sum(x['R'] for x in trades if x['R']>0)
    lr=abs(sum(x['R'] for x in trades if x['R']<0))
    pf=wr2/lr if lr>0 else float('inf')
    short=label[2:]
    print(f'{short:25s} {t:4d}   {wr:4.0f}%  {rt:+5.1f}R  {pf:5.2f}')

print('-'*55)
print('FIM')
