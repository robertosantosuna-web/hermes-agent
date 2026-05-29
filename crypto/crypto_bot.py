#!/usr/bin/env python3
"""
CRYPTO BOT — Multi-Agente para Criptomoedas
Mercado 24/7, sem sessões, pares BTC e ETH
"""
import sys, json, os, numpy as np
from pathlib import Path
from datetime import datetime
import yfinance as yf

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
from crypto_multi_agent import CryptoConfluencia

# ═══ CONFIG ═══
RR = 3.0
MIN_SL_PCT = 0.1   # 0.1% SL mínimo
MAX_SL_PCT = 1.0   # 1.0% SL máximo
RISK_PCT = 0.5     # 0.5% risco por trade

PAIRS = {
    'BTCUSD': ('BTC-USD', 1.0),
    'ETHUSD': ('ETH-USD', 0.1),
}

def get_daily_bias(highs, lows, closes):
    """Viés diário baseado em fechamento vs abertura."""
    if len(highs) < 3: return 'NEUTRAL'
    ph, pl = highs[-3], lows[-3]
    ch, cl, cc = highs[-2], lows[-2], closes[-2]
    # Rompimento + fechamento
    if ch > ph and cc < ph: return 'SELL'
    if cl < pl and cc > pl: return 'BUY'
    if ch > ph and cc > ph: return 'BUY'
    if cl < pl and cc < pl: return 'SELL'
    # Tendência simples
    if cc > closes[-3]: return 'BUY'
    if cc < closes[-3]: return 'SELL'
    return 'NEUTRAL'

def get_btc_change():
    """Variação % do BTC nas últimas 4 horas."""
    try:
        df = yf.Ticker('BTC-USD').history(period='1d', interval='1h')
        if len(df) < 4: return None
        return (df['Close'].values[-1] / df['Close'].values[-5] - 1) * 100
    except:
        return None

agent = CryptoConfluencia()

print(f"═══ CRYPTO BOT Multi-Agente — {datetime.now().strftime('%d/%m %H:%M')} ═══")
print()

btc_change = get_btc_change()

for name, cfg in PAIRS.items():
    sym, pip = cfg
    
    try:
        # Daily bias
        df_d = yf.Ticker(sym).history(period='30d', interval='1d')
        cm = {c.lower(): c for c in df_d.columns}
        dh = df_d[cm.get('high','High')].values
        dl = df_d[cm.get('low','Low')].values
        dc = df_d[cm.get('close','Close')].values
        bias = get_daily_bias(dh, dl, dc)
        
        if bias == 'NEUTRAL':
            print(f"{name:8s} BIAS NEUTRAL — pulado")
            continue
        
        # Dados M1
        df_m1 = yf.Ticker(sym).history(period='5d', interval='1m')
        if df_m1 is None or len(df_m1) < 100:
            print(f"{name:8s} sem dados M1")
            continue
        
        h = df_m1['High'].values
        l = df_m1['Low'].values
        c = df_m1['Close'].values
        o = df_m1['Open'].values
        
        # Multi-Agent analysis
        decision, conf, signal = agent.analyze(
            name, h, l, c, o, bias, pip, 
            btc_change if name != 'BTCUSD' else None
        )
        
        if decision != 'NEUTRAL' and signal:
            entry = signal['entry']
            # SL baseado em % do preço
            sl_pct = max(MIN_SL_PCT, min(abs(entry - l[-1]) / entry * 100 * 2, MAX_SL_PCT))
            sl_pips = sl_pct / 100 * entry  # converter % para preço
            
            tp = entry + sl_pips * RR if decision == 'BUY' else entry - sl_pips * RR
            
            print(f"{name:8s} {decision:4s} @{entry:.2f} SL={sl_pct:.2f}% TP={RR*sl_pct:.2f}% Conf={conf:.0f}%")
            print(f"         ATR={abs(entry-l[-1])/entry*100:.2f}% BTC={'+' if btc_change and btc_change>0 else ''}{btc_change:.1f}%" if btc_change else "")
        else:
            print(f"{name:8s} {decision:7s} conf={conf:.0f}% — sem sinal")
    
    except Exception as e:
        print(f"{name:8s} ERRO: {e}")

print()
print(f"BTC 4h change: {btc_change:+.1f}%" if btc_change else "BTC: sem dados")
print("═══ FIM ═══")
