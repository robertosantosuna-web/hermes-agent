#!/usr/bin/env python3
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

print('='*60)
print('BACKTEST -- ATR/DMI M15 + FVG M1')
print(datetime.now().strftime('%d/%m %H:%M'))
print('='*60)
all_trades=[]

for name, cfg in PAIRS.items():
    sym=cfg[0]; pip=cfg[1]; mtl=len(cfg)>2
    print('\n--- ' + name + ' ---')
    try:
        df_m1=yf.Ticker(sym).history(period='5d',interval='1m')
        df_m15=yf.Ticker(sym).history(period='5d',interval='15m')
        if df_m1 is None or len(df_m1)<200: continue
        if df_m15 is None or len(df_m15)<20: continue
        print('  M1:' + str(len(df_m1)) + ' M15:' + str(len(df_m15)))
        
        m1_h=df_m1['High'].values; m1_l=df_m1['Low'].values
        m1_c=df_m1['Close'].values; m1_o=df_m1['Open'].values
        m1_t=df_m1.index; m1_day=[t.date() for t in m1_t]
        days=sorted(set(m1_day))
        
        # ATR/DMI M15
        m15_h=df_m15['High'].values; m15_l=df_m15['Low'].values
        m15_c=df_m15['Close'].values
        n=15; h=m15_h[-n:]; l=m15_l[-n:]; c=m15_c[-n:]
        tr=np.maximum(h-l,np.maximum(abs(h-np.roll(c,1)),abs(l-np.roll(c,1))))
        tr[0]=h[0]-l[0]
        atr15=np.mean(tr[-14:])/pip if len(tr)>=14 else np.mean(tr)/pip
        up=h-np.roll(h,1); dn=np.roll(l,1)-l; up[0]=dn[0]=0
        pdm=np.where((up>dn)&(up>0),up,0); ndm=np.where((dn>up)&(dn>0),dn,0)
        av=np.mean(tr[-14:]) if len(tr)>=14 else np.mean(tr)
        pdi=100*np.mean(pdm[-14:])/av if av>0 else 0
        ndi=100*np.mean(ndm[-14:])/av if av>0 else 0
        
        df_d=yf.Ticker(sym).history(period='30d',interval='1d')
        cm={c.lower():c for c in df_d.columns}
        d_h=df_d[cm.get('high','High')].values
        d_l=df_d[cm.get('low','Low')].values
        d_c=df_d[cm.get('close','Close')].values
        d_t=df_d.index
        
        trades=[]; last=None
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
            trend=(b=='BUY' and pdi>ndi) or (b=='SELL' and ndi>pdi)
            if not trend: continue
            
            for off in range(8,len(dc)-1):
                i=dc[off]
                if last==day: break
                lh=m1_h[max(0,i-12):i+1]; ll=m1_l[max(0,i-12):i+1]
                lc=m1_c[max(0,i-12):i+1]; lo=m1_o[max(0,i-12):i+1]
                fvgs=det_fvg(lh,ll,lc,b,pip,mtl)
                if not fvgs: continue
                s=fvgs[-1]
                if s['idx']>=len(lc)-1: continue
                
                slp=max(MIN_SL,min(atr15*1.5,MAX_SL if not mtl else 300))
                e=s['entry']
                if s['dir']=='BUY':
                    sl_price=e-slp*pip; tp_price=e+slp*RR*pip
                else:
                    sl_price=e+slp*pip; tp_price=e-slp*RR*pip
                
                res='OPEN'; cv=0
                for j in range(i+1,min(i+3000,len(m1_h))):
                    cv+=1
                    if s['dir']=='BUY':
                        if m1_h[j]>=tp_price: res='WIN'; break
                        if m1_l[j]<=sl_price: res='LOSS'; break
                    else:
                        if m1_l[j]<=tp_price: res='WIN'; break
                        if m1_h[j]>=sl_price: res='LOSS'; break
                if res in ('WIN','LOSS'):
                    trades.append(dict(
                        pair=name,day=str(day),b=b,dir=s['dir'],
                        entry=round(e,5),sl=round(slp,1),atr=round(atr15,1),
                        r=res,cv=cv,R=RR if res=='WIN' else -1
                    ))
                    last=day; break
        
        if trades:
            w=sum(1 for t in trades if t['r']=='WIN')
            wr=w/len(trades)*100; rt=sum(t['R'] for t in trades)
            print('  ' + str(len(trades)) + 't | WR:' + str(int(wr)) + '% | R:' + ('+' if rt>=0 else '') + str(round(rt,1)) + ' | ATR15=' + str(round(atr15,1)) + 'p DMI=' + str(int(pdi)) + '/' + str(int(ndi)))
            for t in trades[-2:]:
                e='OK' if t['r']=='WIN' else 'XX'
                print('  ' + e + ' ' + t['day'] + ' ' + t['dir'] + ' SL=' + str(int(t['sl'])) + 'p ATR=' + str(t['atr']) + 'p')
            all_trades.extend(trades)
        else:
            print('  0t | ATR15=' + str(round(atr15,1)) + 'p DMI=' + str(int(pdi)) + '/' + str(int(ndi)))
    except Exception as e:
        print('  ERRO: ' + str(e))

print('\n' + '='*60)
print('CONSOLIDADO -- ATR/DMI M15 + FVG M1')
print('='*60)
if all_trades:
    w=sum(1 for t in all_trades if t['r']=='WIN')
    total=len(all_trades); wr=w/total*100; rt=sum(x['R'] for x in all_trades)
    wr2=sum(x['R'] for x in all_trades if x['R']>0)
    lr=abs(sum(x['R'] for x in all_trades if x['R']<0))
    pf=wr2/lr if lr>0 else float('inf')
    print('Total:' + str(total) + ' | WR:' + str(int(wr)) + '% | R:' + ('+' if rt>=0 else '') + str(round(rt,1)) + ' | PF:' + str(round(pf,2)) + ' | Exp:' + ('+' if (wr/100*RR-(1-wr/100))>=0 else '') + str(round(wr/100*RR-(1-wr/100),2)) + 'R')
    for p in sorted(set(x['pair'] for x in all_trades)):
        pt=[x for x in all_trades if x['pair']==p]
        pw=sum(1 for x in pt if x['r']=='WIN')
        print(p + ' ' + str(len(pt)) + 't ' + str(int(pw/len(pt)*100)) + '% ' + ('+' if sum(x['R'] for x in pt)>=0 else '') + str(round(sum(x['R'] for x in pt),1)) + 'R')
    eq=0; pk=0; dd=0
    for x in all_trades: eq+=x['R']; pk=max(pk,eq); dd=max(dd,pk-eq)
    print('DD:' + str(round(dd,1)) + 'R Eq:' + ('+' if eq>=0 else '') + str(round(eq,1)) + 'R | 0.5%: +' + str(round(rt*0.5,1)) + '% / -' + str(round(dd*0.5,1)) + '%')
else:
    print('0 trades')
print('FIM')
