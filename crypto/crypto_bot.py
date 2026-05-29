#!/usr/bin/env python3
"""
CRYPTO BOT v2 — Multi-Agente + Pair Selector dinâmico
Opera 24/7 com seleção adaptativa dos melhores pares
"""
import sys, json, os
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import yfinance as yf

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
from crypto_multi_agent import CryptoConfluencia
from pair_selector import CryptoPairSelector

# ═══ CONFIG ═══
RR = 3.0                    # RR fixo
RISK_PCT = 0.5              # 0.5% risco por trade
MAX_PAIRS = 5               # Máximo de pares simultâneos
MIN_CONFIDENCE = 40         # Confiança mínima para entrada
DATA_PERIOD = '5d'          # Período de dados

# Horários de scan (UTC)
SCAN_HOURS = list(range(24))  # 24/7, mas com peso menor fora de pico

def get_btc_change():
    """Variação % do BTC nas últimas 4 horas."""
    try:
        df = yf.Ticker('BTC-USD').history(period='1d', interval='1h')
        if len(df) < 4: return None
        return (df['Close'].values[-1] / df['Close'].values[-5] - 1) * 100
    except:
        return None

def get_daily_bias(highs, lows, closes):
    """Viés diário baseado em estrutura de preço."""
    if len(highs) < 3: return 'NEUTRAL'
    ph, pl = highs[-3], lows[-3]    # dia anterior
    ch, cl, cc = highs[-2], lows[-2], closes[-2]  # ontem
    
    if ch > ph and cc > ph: return 'BUY'
    if cl < pl and cc < pl: return 'SELL'
    if ch > ph and cc < ph: return 'SELL'  # manipulação
    if cl < pl and cc > pl: return 'BUY'   # manipulação
    if cc > closes[-3]: return 'BUY'
    if cc < closes[-3]: return 'SELL'
    return 'NEUTRAL'

def calculate_sl_tp(entry, atr_pct, direction, sl_recommend=None):
    """Calcula SL e TP baseados em ATR."""
    if sl_recommend is None:
        sl_recommend = max(atr_pct * 1.5, 0.15)  # mínimo 0.15%
    
    sl_pct = min(sl_recommend, 1.5)  # cap em 1.5%
    sl_price = entry * sl_pct / 100
    
    if direction == 'BUY':
        sl = entry - sl_price
        tp = entry + sl_price * RR
    else:
        sl = entry + sl_price
        tp = entry - sl_price * RR
    
    return sl, tp, sl_pct


# ═══ MAIN ═══
print(f"═══ CRYPTO BOT v2 — {datetime.now(timezone.utc).strftime('%d/%m %H:%M')} UTC ═══")
print()

try:
    # 1. Selecionar melhores pares
    print("[1/3] Selecionando pares...")
    selector = CryptoPairSelector(max_pairs=MAX_PAIRS)
    selected = selector.select_best_pairs()
    
    if not selected:
        print("⚠️ Nenhum par com volatilidade suficiente. Abortando.")
        sys.exit(0)
    
    print(f"       {len(selected)} pares selecionados:")
    for s in selected:
        print(f"       {s['pair']:8s} vol={s['vol']:.1f}% mom={s['mom']:+.1f}% score={s['score']:.0f}")
    print()
    
    # 2. Dados BTC (referência)
    print("[2/3] Obtendo dados BTC...")
    btc_change = get_btc_change()
    print(f"       BTC 4h: {btc_change:+.2f}%" if btc_change else "       BTC: sem dados")
    print()
    
    # 3. Analisar cada par
    print("[3/3] Analisando pares...")
    agent = CryptoConfluencia()
    signals_found = []
    
    for pair_info in selected:
        pair = pair_info['pair']
        sym = pair_info['sym']
        pip = pair_info['pip']
        
        try:
            # Daily bias
            df_d = yf.Ticker(sym).history(period='30d', interval='1d')
            cm = {c.lower(): c for c in df_d.columns}
            dh = df_d[cm.get('high','High')].values
            dl = df_d[cm.get('low','Low')].values
            dc = df_d[cm.get('close','Close')].values
            bias = get_daily_bias(dh, dl, dc)
            
            if bias == 'NEUTRAL':
                print(f"  {pair:8s} BIAS NEUTRAL — pulado")
                continue
            
            # Dados M1
            df_m1 = yf.Ticker(sym).history(period=DATA_PERIOD, interval='1m')
            if df_m1 is None or len(df_m1) < 100:
                print(f"  {pair:8s} sem dados M1 suficientes")
                continue
            
            h = df_m1['High'].values
            l = df_m1['Low'].values
            c = df_m1['Close'].values
            o = df_m1['Open'].values
            
            # Análise completa (retorna info de volatilidade também)
            decision, conf, signal, v_info = agent.analyze(
                pair, h, l, c, o, bias, pip,
                btc_change if pair != 'BTCUSD' else None,
                MIN_CONFIDENCE
            )
            
            # Calcular SL/TP
            atr_pct = v_info.get('atr_pct', 0.5)
            sl_rec = v_info.get('sl_recommend', None)
            
            if decision != 'NEUTRAL' and signal:
                entry = signal['entry']
                sl, tp, sl_pct = calculate_sl_tp(entry, atr_pct, decision, sl_rec)
                
                pattern_type = signal.get('type', '?')
                quality = signal.get('quality', 0)
                
                print(f"  ✅ {pair:8s} {decision:4s} @{entry:.4f} | {pattern_type} Q={quality} | "
                      f"SL={sl_pct:.2f}% | TP={sl_pct*RR:.2f}% | Conf={conf:.0f}% | "
                      f"Regime={v_info.get('regime','?')}")
                
                signals_found.append({
                    'pair': pair, 'sym': sym, 'direction': decision,
                    'entry': entry, 'sl': sl, 'tp': tp,
                    'sl_pct': sl_pct, 'conf': conf,
                    'pattern': pattern_type, 'quality': quality,
                    'atr_pct': atr_pct, 'regime': v_info.get('regime'),
                    'time': datetime.now(timezone.utc).isoformat()
                })
            else:
                print(f"  {pair:8s} {decision:7s} conf={conf:.0f}% — {v_info.get('regime','?')}")
        
        except Exception as e:
            print(f"  {pair:8s} ❌ ERRO: {e}")
    
    print()
    
    # 4. Resumo
    if signals_found:
        print(f"═══ {len(signals_found)} SINAL(is) ENCONTRADO(s) ═══")
        for sig in signals_found:
            print(f"  {sig['pair']} {sig['direction']} @{sig['entry']:.4f} "
                  f"SL={sig['sl_pct']:.2f}% TP={sig['sl_pct']*RR:.2f}% "
                  f"Conf={sig['conf']:.0f}% [{sig['pattern']}]")
        
        # Salvar sinais para possível execução
        signals_file = Path.home() / '.hermes' / 'crypto' / 'signals.json'
        with open(signals_file, 'w') as f:
            json.dump(signals_found, f, indent=2, default=str)
        print(f"\n  Sinais salvos: {signals_file}")
    else:
        print("═══ NENHUM SINAL ENCONTRADO ═══")
    
    print(f"\nBTC 4h: {btc_change:+.2f}%" if btc_change else "\nBTC: sem dados")
    print("═══ FIM ═══")

except Exception as e:
    print(f"\n❌ ERRO FATAL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
