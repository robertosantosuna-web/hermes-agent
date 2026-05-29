#!/usr/bin/env python3
"""
CRYPTO BOT v4 — Data-Driven Multi-Agent + Anti-Correlação USD
Regras: max 2 trades simultâneos, 1 por grupo de correlação
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
RR = 3.0
RISK_PCT = 0.5
MIN_CONFIDENCE = 55
DATA_PERIOD = '5d'

TRADES_FILE = Path.home() / '.hermes' / 'crypto' / 'open_trades.json'
SIGNALS_FILE = Path.home() / '.hermes' / 'crypto' / 'signals.json'

def load_open_trades():
    if TRADES_FILE.exists():
        try:
            with open(TRADES_FILE) as f:
                return json.load(f)
        except:
            pass
    return []

def save_open_trades(trades):
    TRADES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRADES_FILE, 'w') as f:
        json.dump(trades, f, indent=2, default=str)

def get_btc_change():
    try:
        df = yf.Ticker('BTC-USD').history(period='1d', interval='1h')
        if len(df) < 4: return None
        return (df['Close'].values[-1] / df['Close'].values[-5] - 1) * 100
    except:
        return None

def get_daily_bias(highs, lows, closes):
    if len(highs) < 3: return 'NEUTRAL'
    ph, pl = highs[-3], lows[-3]
    ch, cl, cc = highs[-2], lows[-2], closes[-2]
    if ch > ph and cc > ph: return 'BUY'
    if cl < pl and cc < pl: return 'SELL'
    if ch > ph and cc < ph: return 'SELL'
    if cl < pl and cc > pl: return 'BUY'
    if cc > closes[-3]: return 'BUY'
    if cc < closes[-3]: return 'SELL'
    return 'NEUTRAL'

def calculate_sl_tp(entry, atr_pct, direction, sl_recommend=None):
    if sl_recommend is None:
        sl_recommend = max(atr_pct * 1.5, 0.15)
    sl_pct = min(sl_recommend, 1.5)
    sl_price = entry * sl_pct / 100
    if direction == 'BUY':
        return entry - sl_price, entry + sl_price * RR, sl_pct
    else:
        return entry + sl_price, entry - sl_price * RR, sl_pct


# ═══ MAIN ═══
print(f"═══ CRYPTO BOT v4 — {datetime.now(timezone.utc).strftime('%d/%m %H:%M')} UTC ═══")
print()

try:
    # Carregar trades abertos
    open_trades = load_open_trades()
    print(f"[0] Trades abertos: {len(open_trades)}/1 (máx 1 — 85% correlação USD)")
    for t in open_trades:
        print(f"    {t['pair']:8s} {t['direction']:4s} @{t['entry']:.4f} SL={t['sl_pct']:.2f}%")
    print()
    
    # 1. Selecionar pares (respeita anti-correlação)
    print("[1/3] Selecionando pares (anti-corr USD)...")
    selector = CryptoPairSelector(max_pairs=3)
    selected = selector.select_best_pairs()
    
    if not selected:
        print("  ⚠️ Nenhum par disponível (limite de trades ou baixo volume)")
        print("═══ FIM ═══")
        sys.exit(0)
    
    selector.print_summary()
    print()
    
    # 2. BTC referência
    print("[2/3] Obtendo dados BTC...")
    btc_change = get_btc_change()
    print(f"       BTC 4h: {btc_change:+.2f}%" if btc_change else "       BTC: sem dados")
    print()
    
    # 3. Analisar pares
    print("[3/3] Analisando pares...")
    agent = CryptoConfluencia()
    signals_found = []
    
    for pair_info in selected:
        pair = pair_info['pair']
        sym = pair_info['sym']
        pip = pair_info['pip']
        
        # ⚡ Anti-correlação USD: verificar se pode abrir
        can_open, reason = selector.can_open_trade(pair, pair_info['direction'])
        if not can_open:
            print(f"  {pair:8s} 🚫 {reason}")
            continue
        
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
            v = df_m1['Volume'].values if 'Volume' in df_m1.columns else None
            
            # Níveis diários (S/R longo prazo)
            daily_levels = {
                'resistance': max(dh[-10:]) if len(dh) >= 10 else max(dh),
                'support': min(dl[-10:]) if len(dl) >= 10 else min(dl)
            }
            
            # Análise completa (retorna info de volatilidade também)
            decision, conf, signal, v_info = agent.analyze(
                pair, h, l, c, o, bias, pip,
                btc_change if pair != 'BTCUSD' else None,
                MIN_CONFIDENCE, v, daily_levels
            )
            
            atr_pct = v_info.get('atr_pct', 0.5)
            sl_rec = v_info.get('sl_recommend', None)
            
            if decision != 'NEUTRAL' and signal:
                entry = signal['entry']
                sl, tp, sl_pct = calculate_sl_tp(entry, atr_pct, decision, sl_rec)
                
                pattern_type = signal.get('type', '?')
                quality = signal.get('quality', 0)
                group = pair_info.get('group', '?')
                
                print(f"  ✅ {pair:8s} {decision:4s} @{entry:.4f} | {pattern_type} Q={quality} | "
                      f"SL={sl_pct:.2f}% | TP={sl_pct*RR:.2f}% | Conf={conf:.0f}% | "
                      f"[{group}]")
                
                trade = {
                    'pair': pair, 'sym': sym, 'direction': decision,
                    'entry': float(entry), 'sl': float(sl), 'tp': float(tp),
                    'sl_pct': sl_pct, 'conf': conf,
                    'pattern': pattern_type, 'quality': quality,
                    'atr_pct': atr_pct, 'regime': v_info.get('regime'),
                    'group': group,
                    'time': datetime.now(timezone.utc).isoformat(),
                    'status': 'open'
                }
                
                signals_found.append(trade)
                
                # ⚡ Adicionar aos trades abertos
                open_trades.append(trade)
                save_open_trades(open_trades)
                
            else:
                print(f"  {pair:8s} {decision:7s} conf={conf:.0f}% — {v_info.get('regime','?')}")
        
        except Exception as e:
            print(f"  {pair:8s} ❌ ERRO: {e}")
    
    print()
    
    # 4. Resumo
    if signals_found:
        print(f"═══ {len(signals_found)} NOVO(s) SINAL(is) ═══")
        for sig in signals_found:
            print(f"  {sig['pair']} {sig['direction']} @{sig['entry']:.4f} "
                  f"SL={sig['sl_pct']:.2f}% TP={sig['sl_pct']*RR:.2f}% "
                  f"Conf={sig['conf']:.0f}% [{sig.get('group','?')}]")
        
        with open(SIGNALS_FILE, 'w') as f:
            json.dump(signals_found, f, indent=2, default=str)
        print(f"\n  Sinais salvos: {SIGNALS_FILE}")
        print(f"  Trades abertos: {len(open_trades)}/1")
    else:
        print("═══ NENHUM SINAL NOVO ═══")
        print(f"  Trades abertos: {len(open_trades)}/1")
    
    print(f"\nBTC 4h: {btc_change:+.2f}%" if btc_change else "\nBTC: sem dados")
    print("═══ FIM ═══")

except Exception as e:
    print(f"\n❌ ERRO FATAL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
