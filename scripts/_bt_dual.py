#!/usr/bin/env python3
"""BACKTEST: 2 modelos simultâneos — M1 + M5"""
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

print('='*60)
print('BACKTEST DUPLO — Modelo A (M1) + Modelo B (M5)')
print(datetime.now().strftime('%d/%m %H:%M'))
print('='*60)

all_A=[]; all_B=[]

for name, cfg in PAIRS.items():
    sym=cfg[0]; pip=cfg[1]; mtl=len(cfg)>2
    print('\n--- ' + name + ' ---')
    try:
        df_m1=yf.Ticker(sym).history(period='5d',interval='1m')
        df_m5=yf.Ticker(sym).history(period='5d',interval='5m')
        if df_m1 is None or len(df_m1)<200: continue
        if df_m5 is None or len(df_m5)<20: continue
        
        m1_h=df_m1['High'].values; m1_l=df_m1['Low'].values
        m1_c=df_m1['Close'].values; m1_o=df_m1['Open'].values
        m1_t=df_m1.index; m1_day=[t.date() for t in m1_t]
        days=sorted(set(m1_day))
        
        m5_h=df_m5['High'].values; m5_l=df_m5['Low'].values
        m5_c=df_m5['Close'].values
        
        atr_A,pdi_A,ndi_A = calc_atr_dmi(m1_h,m1_l,m1_c,pip)
        atr_B,pdi_B,ndi_B = calc_atr_dmi(m5_h,m5_l,m5_c,pip)
        
        df_d=yf.Ticker(sym).history(period='30d',interval='1d')
        cm={c.lower():c for c in df_d.columns}
        d_h=df_d[cm.get('high','High')].values
        d_l=df_d[cm.get('low','Low')].values
        d_c=df_d[cm.get('close','Close')].values
        d_t=df_d.index
        
        trades_A=[]; trades_B=[]; last_A=None; last_B=None
        
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
            trend_B=(b=='BUY' and pdi_B>ndi_B) or (b=='SELL' and ndi_B>pdi_B)
            
            for off in range(8,len(dc)-1):
                i=dc[off]
                
                lh=m1_h[max(0,i-12):i+1]; ll=m1_l[max(0,i-12):i+1]
                lc=m1_c[max(0,i-12):i+1]; lo=m1_o[max(0,i-12):i+1]
                fvgs=det_fvg(lh,ll,lc,b,pip,mtl)
                if not fvgs: continue
                s=fvgs[-1]
                if s['idx']>=len(lc)-1: continue
                
                # MODELO A: DMI M1 + ATR M1
                if trend_A and last_A!=day:
                    slp_A=max(MIN_SL,min(atr_A*2.0,MAX_SL if not mtl else 300))
                    e=s['entry']
                    if s['dir']=='BUY': sl_A=e-slp_A*pip; tp_A=e+slp_A*RR*pip
                    else: sl_A=e+slp_A*pip; tp_A=e-slp_A*RR*pip
                    res_A='OPEN'; cv_A=0
                    for j in range(i+1,min(i+3000,len(m1_h))):
                        cv_A+=1
                        if s['dir']=='BUY':
                            if m1_h[j]>=tp_A: res_A='WIN'; break
                            if m1_l[j]<=sl_A: res_A='LOSS'; break
                        else:
                            if m1_l[j]<=tp_A: res_A='WIN'; break
                            if m1_h[j]>=sl_A: res_A='LOSS'; break
                    if res_A in ('WIN','LOSS'):
                        trades_A.append(dict(pair=name,day=str(day),b=b,dir=s['dir'],
                            entry=round(e,5),sl=round(slp_A,1),atr=round(atr_A,1),
                            res=res_A,cv=cv_A,R=RR if res_A=='WIN' else -1,model='A'))
                        last_A=day
                
                # MODELO B: DMI M5 + ATR M5
                if trend_B and last_B!=day:
                    slp_B=max(MIN_SL,min(atr_B*1.5,MAX_SL if not mtl else 300))
                    e=s['entry']
                    if s['dir']=='BUY': sl_B=e-slp_B*pip; tp_B=e+slp_B*RR*pip
                    else: sl_B=e+slp_B*pip; tp_B=e-slp_B*RR*pip
                    res_B='OPEN'; cv_B=0
                    for j in range(i+1,min(i+3000,len(m1_h))):
                        cv_B+=1
                        if s['dir']=='BUY':
                            if m1_h[j]>=tp_B: res_B='WIN'; break
                            if m1_l[j]<=sl_B: res_B='LOSS'; break
                        else:
                            if m1_l[j]<=tp_B: res_B='WIN'; break
                            if m1_h[j]>=sl_B: res_B='LOSS'; break
                    if res_B in ('WIN','LOSS'):
                        trades_B.append(dict(pair=name,day=str(day),b=b,dir=s['dir'],
                            entry=round(e,5),sl=round(slp_B,1),atr=round(atr_B,1),
                            res=res_B,cv=cv_B,R=RR if res_B=='WIN' else -1,model='B'))
                        last_B=day
        
        if trades_A or trades_B:
            wa=sum(1 for t in trades_A if t['res']=='WIN'); ta=len(trades_A)
            wb=sum(1 for t in trades_B if t['res']=='WIN'); tb=len(trades_B)
            wra=wa/ta*100 if ta else 0; wrb=wb/tb*100 if tb else 0
            rta=sum(t['R'] for t in trades_A); rtb=sum(t['R'] for t in trades_B)
            print('  A(M1):' + str(ta) + 't WR:' + str(int(wra)) + '% R:' + ('+' if rta>=0 else '') + str(round(rta,1)) + ' | B(M5):' + str(tb) + 't WR:' + str(int(wrb)) + '% R:' + ('+' if rtb>=0 else '') + str(round(rtb,1)))
            print('    ATR A=' + str(round(atr_A,1)) + 'p DMI=' + str(int(pdi_A)) + '/' + str(int(ndi_A)) + ' | ATR B=' + str(round(atr_B,1)) + 'p DMI=' + str(int(pdi_B)) + '/' + str(int(ndi_B)))
            all_A.extend(trades_A); all_B.extend(trades_B)
        else:
            print('  0 trades')
    except Exception as e:
        print('  ERRO: ' + str(e))

def report(trades, label):
    if not trades: return
    w=sum(1 for t in trades if t['res']=='WIN')
    total=len(trades); wr=w/total*100; rt=sum(x['R'] for x in trades)
    wr2=sum(x['R'] for x in trades if x['R']>0)
    lr=abs(sum(x['R'] for x in trades if x['R']<0))
    pf=wr2/lr if lr>0 else float('inf')
    print(label + ': ' + str(total) + 't | WR:' + str(int(wr)) + '% | R:' + ('+' if rt>=0 else '') + str(round(rt,1)) + ' | PF:' + str(round(pf,2)) + ' | Exp:' + ('+' if (wr/100*RR-(1-wr/100))>=0 else '') + str(round(wr/100*RR-(1-wr/100),2)) + 'R')
    eq=0; pk=0; dd=0
    for x in trades: eq+=x['R']; pk=max(pk,eq); dd=max(dd,pk-eq)
    print('  DD:' + str(round(dd,1)) + 'R Eq:' + ('+' if eq>=0 else '') + str(round(eq,1)) + 'R | 0.5%: +' + str(round(rt*0.5,1)) + '% / -' + str(round(dd*0.5,1)) + '%')

print('\n' + '='*60)
print('CONSOLIDADO')
print('='*60)
report(all_A, 'MODELO A (DMI M1 + ATR M1)')
report(all_B, 'MODELO B (DMI M5 + ATR M5)')

# Combinado
combined = all_A + all_B
if combined:
    w=sum(1 for t in combined if t['res']=='WIN')
    total=len(combined); wr=w/total*100; rt=sum(x['R'] for x in combined)
    print('\nCOMBINADO A+B: ' + str(total) + 't | WR:' + str(int(wr)) + '% | R:' + ('+' if rt>=0 else '') + str(round(rt,1)))

print('FIM')
