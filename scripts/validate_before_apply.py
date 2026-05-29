#!/usr/bin/env python3
"""
SISTEMA DE VALIDAÇÃO PRÉ-APLICAÇÃO
Testa qualquer mudança em backtest antes de ir ao vivo.
Regra: só aplica se PF > 2.0 e WR > 50% nos últimos 5 dias.
"""
import sys, os, json, subprocess
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

HERMES = Path.home() / '.hermes'
SCRIPTS = HERMES / 'scripts'
VALIDATION_FILE = HERMES / 'forex' / 'validation_log.json'

def run_backtest(days=5):
    """Roda backtest rápido e retorna métricas."""
    script = SCRIPTS / '_bt_agent.py'
    if not script.exists():
        # Usar teste inline
        result = subprocess.run([
            sys.executable, '-c', '''
import sys; sys.path.insert(0, "''' + str(SCRIPTS) + '''")
from multi_agent import ConfluenciaAgent
import yfinance as yf, numpy as np, pandas as pd
from datetime import datetime, timedelta

RR=3.0; MIN_SL=10; MAX_SL=30
PAIRS = {
    "EURUSD":("EURUSD=X",0.0001),"GBPUSD":("GBPUSD=X",0.0001),
    "USDJPY":("USDJPY=X",0.01),"GBPJPY":("GBPJPY=X",0.01),
    "EURJPY":("EURJPY=X",0.01),"USDCAD":("USDCAD=X",0.0001),
    "XAUUSD":("GC=F",0.01,True),
}

def tf_bias(h,l,c):
    if len(h)<3: return "NEUTRAL"
    ph,pl=h[-3],l[-3]; ch,cl,cc=h[-2],l[-2],c[-2]
    if ch>ph and cc<ph: return "SELL"
    if cl<pl and cc>pl: return "BUY"
    return "NEUTRAL"

def simulate(m1_h,m1_l,i,entry,slp,d,pip):
    if d=="BUY": sl=entry-slp*pip; tp=entry+slp*RR*pip
    else: sl=entry+slp*pip; tp=entry-slp*RR*pip
    for j in range(i+1,min(i+3000,len(m1_h))):
        if d=="BUY":
            if m1_h[j]>=tp: return "WIN"
            if m1_l[j]<=sl: return "LOSS"
        else:
            if m1_l[j]<=tp: return "WIN"
            if m1_h[j]>=sl: return "LOSS"
    return "OPEN"

agent = ConfluenciaAgent()
results = []
for name, cfg in PAIRS.items():
    sym=cfg[0]; pip=cfg[1]; mtl=len(cfg)>2
    try:
        df=yf.Ticker(sym).history(period="5d",interval="1m")
        if df is None or len(df)<500: continue
        h=df["High"].values; l=df["Low"].values; c=df["Close"].values
        t=df.index; md=[x.date() for x in t]; days=sorted(set(md))
        df_d=yf.Ticker(sym).history(period="30d",interval="1d")
        cm={x.lower():x for x in df_d.columns}
        dh=df_d[cm.get("high","High")].values
        dl=df_d[cm.get("low","Low")].values
        dc=df_d[cm.get("close","Close")].values
        dt=df_d.index
        
        for di in range(3,len(days)):
            day=days[di]; dc_idx=[j for j,d in enumerate(md) if d==day]
            if len(dc_idx)<60: continue
            dd=None
            for ddi in range(len(dt)):
                if dt[ddi].date()==day: dd=ddi; break
            if dd is None or dd<2: continue
            b=tf_bias(dh[:dd+1],dl[:dd+1],dc[:dd+1])
            if b=="NEUTRAL": continue
            for off in range(8,len(dc_idx)-1):
                i=dc_idx[off]
                dec, conf, sig = agent.analyze(name, h[:i+1], l[:i+1], c[:i+1], b, pip, mtl)
                if dec=="NEUTRAL" or not sig: continue
                slp=max(10,min(abs(sig["entry"]-l[i])/pip*2,30))
                res=simulate(h,l,i,sig["entry"],slp,sig["direction"],pip)
                if res in ("WIN","LOSS"):
                    results.append({"pair":name,"res":res,"R":3 if res=="WIN" else -1})
                break
        
        wins=sum(1 for r in results if r["res"]=="WIN")
        total=len(results)
        wr=wins/total*100 if total>0 else 0
        rt=sum(r["R"] for r in results)
        wr2=sum(r["R"] for r in results if r["R"]>0)
        lr=abs(sum(r["R"] for r in results if r["R"]<0))
        pf=wr2/lr if lr>0 else 0
        print(f'VALIDATION:{total}|{wr:.0f}|{rt:.0f}|{pf:.2f}')
    except Exception as e:
        print(f'VALIDATION:0|0|0|0|err={e}')
'''], capture_output=True, text=True, timeout=120)
        
        for line in result.stdout.strip().split('\n'):
            if line.startswith('VALIDATION:'):
                parts = line.split('|')
                if len(parts) >= 5:
                    return {
                        'trades': int(parts[1]),
                        'wr': float(parts[2]),
                        'r_total': float(parts[3]),
                        'pf': float(parts[4]),
                    }
    return None


def validate_and_apply(force=False):
    """
    Valida estratégia em backtest antes de aplicar.
    Critérios: PF > 2.0, WR > 45%, mínimo 5 trades.
    """
    print(f'🔍 Validando estratégia... ({datetime.now().strftime("%H:%M")})')
    
    metrics = run_backtest(days=5)
    
    if metrics is None:
        print('❌ Falha ao rodar validação')
        if not force:
            return False
    else:
        print(f'   Trades: {metrics["trades"]} | WR: {metrics["wr"]:.0f}% | R: {metrics["r_total"]:+.0f} | PF: {metrics["pf"]:.2f}')
        
        # Salvar log
        log = {
            'time': datetime.now().isoformat(),
            **metrics,
            'passed': False,
        }
        
        if metrics['trades'] < 5:
            print(f'❌ Poucos trades ({metrics["trades"]} < 5). Amostra insuficiente.')
        elif metrics['wr'] < 45:
            print(f'❌ WR baixo ({metrics["wr"]:.0f}% < 45%)')
        elif metrics['pf'] < 2.0:
            print(f'❌ PF baixo ({metrics["pf"]:.2f} < 2.0)')
        else:
            print(f'✅ VALIDADO! PF {metrics["pf"]:.2f} > 2.0, WR {metrics["wr"]:.0f}% > 45%')
            log['passed'] = True
        
        # Salvar
        history = []
        if VALIDATION_FILE.exists():
            try:
                history = json.loads(VALIDATION_FILE.read_text())
            except:
                pass
        history.append(log)
        VALIDATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        VALIDATION_FILE.write_text(json.dumps(history[-50:], indent=2))
        
        return log['passed'] or force
    
    return False


if __name__ == '__main__':
    force = '--force' in sys.argv
    ok = validate_and_apply(force)
    ok_msg = 'APROVADO' if ok else 'REPROVADO'
    print(f'\nResultado: {ok_msg}')
    sys.exit(0 if ok else 1)
