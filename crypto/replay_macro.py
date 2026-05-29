#!/usr/bin/env python3
"""
REPLAY CRYPTO COM FATORES MACRO — Testa impacto do Fear & Greed
Compara: com viés de sentimento vs sem viés
"""
import sys, json, requests
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
from tradingview_feed import TradingViewFeed
from crypto_multi_agent import CryptoConfluencia, PadraoAgent, TendenciaAgent

RR = 3.0
MIN_CONFIDENCE = 55
DAYS = 2
PAIRS = ['BTCUSD', 'ETHUSD', 'DOGEUSD', 'BNBUSD']

def get_fear_greed_history(days=30):
    try:
        r = requests.get(f'https://api.alternative.me/fng/?limit={days}', timeout=10)
        return [{'date': d['timestamp'], 'value': int(d['value'])} for d in r.json()['data']]
    except:
        return []

def simulate_trade(h, l, c, direction, entry, sl_pct, idx):
    if direction == 'BUY':
        sl = entry * (1 - sl_pct/100); tp = entry * (1 + sl_pct*RR/100)
    else:
        sl = entry * (1 + sl_pct/100); tp = entry * (1 - sl_pct*RR/100)
    
    for j in range(idx, min(idx + 500, len(c))):
        if direction == 'BUY':
            if l[j] <= sl: return {'result': 'LOSS', 'rr': -1}
            if h[j] >= tp: return {'result': 'WIN', 'rr': RR}
        else:
            if h[j] >= sl: return {'result': 'LOSS', 'rr': -1}
            if l[j] <= tp: return {'result': 'WIN', 'rr': RR}
    return None


def run_replay(pair, fear_greed_bias=None):
    """Roda replay com e sem viés de sentimento."""
    feed = TradingViewFeed()
    agent = CryptoConfluencia()
    
    h, l, c, o, v = feed.get_candles(pair, '1m', min(DAYS * 1440, 4000))
    if c is None or len(c) < 200: return [], []
    
    trades_normal = []
    trades_bias = []
    last_idx = -100
    
    for idx in range(200, len(c) - 200, 30):
        hw, lw, cw, ow = h[:idx], l[:idx], c[:idx], o[:idx]
        vw = v[:idx] if v is not None else None
        
        if len(cw) < 200: continue
        
        # Análise normal
        daily_levels = {'resistance': max(hw[-200:]), 'support': min(lw[-200:])}
        btc_chg = (cw[-1] / cw[-60] - 1) * 100 if len(cw) >= 60 else 0
        
        # Testar BUY e SELL
        for test_bias in ['BUY', 'SELL']:
            dec, conf, sig, info = agent.analyze(
                pair, hw, lw, cw, ow, test_bias, 1.0, btc_chg, MIN_CONFIDENCE, vw, daily_levels
            )
            
            if dec == 'NEUTRAL' or not sig: continue
            
            sig_idx = sig.get('idx', idx)
            if abs(sig_idx - last_idx) < 20: continue
            last_idx = sig_idx
            
            entry = sig['entry']
            atr_pct = (info or {}).get('atr_pct', 0.3)
            sl_pct = max(atr_pct * 1.5, 0.15)
            
            result = simulate_trade(h, l, c, dec, entry, sl_pct, idx)
            if not result: continue
            
            # Sem viés
            trades_normal.append({'direction': dec, 'result': result['result'], 'rr': result['rr']})
            
            # Com viés de sentimento
            if fear_greed_bias:
                if dec == fear_greed_bias:
                    trades_bias.append({'direction': dec, 'result': result['result'], 'rr': result['rr']})
            else:
                trades_bias.append({'direction': dec, 'result': result['result'], 'rr': result['rr']})
    
    return trades_normal, trades_bias


# ═══ MAIN ═══
print(f"═══ REPLAY CRYPTO COM FATORES MACRO ═══")
print()

# Fear & Greed
fng = get_fear_greed_history(7)
if fng:
    current_fng = fng[0]['value']
    print(f"Fear & Greed: {current_fng} ({'Extreme Fear' if current_fng < 25 else 'Fear' if current_fng < 50 else 'Greed'})")
    if current_fng < 30:
        fng_bias = 'BUY'
        print(f"Viés: BUY (medo extremo → fundo potencial)")
    elif current_fng > 70:
        fng_bias = 'SELL'
        print(f"Viés: SELL (ganância → topo potencial)")
    else:
        fng_bias = None
        print(f"Viés: NEUTRO")
else:
    fng_bias = None
    print("Fear & Greed: indisponível")
print()

print(f"{'Par':<10s} {'Normal T':>9s} {'Normal WR':>10s} {'Normal R':>9s} | {'Bias T':>7s} {'Bias WR':>8s} {'Bias R':>7s} {'Impacto':>8s}")
print(f"{'─'*78}")

all_normal = []
all_bias = []

for pair in PAIRS:
    print(f"{pair:<10s}", end=' ', flush=True)
    normal, bias = run_replay(pair, fng_bias)
    
    nw = sum(1 for t in normal if t['result']=='WIN')
    nr = sum(t['rr'] for t in normal)
    
    bw = sum(1 for t in bias if t['result']=='WIN')
    br = sum(t['rr'] for t in bias)
    
    nwr = nw/len(normal)*100 if normal else 0
    bwr = bw/len(bias)*100 if bias else 0
    
    impacto = bwr - nwr
    
    print(f"{len(normal):9d} {nwr:9.1f}% {nr:+9.1f}R | {len(bias):7d} {bwr:8.1f}% {br:+7.1f}R {impacto:+8.1f}pp")
    
    all_normal.extend(normal)
    all_bias.extend(bias)

print(f"{'─'*78}")

nw = sum(1 for t in all_normal if t['result']=='WIN')
bw = sum(1 for t in all_bias if t['result']=='WIN')
nwr = nw/len(all_normal)*100 if all_normal else 0
bwr = bw/len(all_bias)*100 if all_bias else 0

print(f"{'TOTAL':<10s} {len(all_normal):9d} {nwr:9.1f}% {sum(t['rr'] for t in all_normal):+9.1f}R | {len(all_bias):7d} {bwr:8.1f}% {sum(t['rr'] for t in all_bias):+7.1f}R {bwr-nwr:+8.1f}pp")
print()
print(f"Impacto do Fear & Greed: {bwr-nwr:+.1f}pp WR, {len(all_normal)-len(all_bias):+d} trades filtrados")
