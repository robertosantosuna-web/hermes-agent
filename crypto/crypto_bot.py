#!/usr/bin/env python3
"""
CRYPTO BOT v9 — TradingView Feed Direto (tvDatafeed)
Multi-TF nativo: M1, M5, M15, M30, H1, H4
Dados Binance via TradingView, sem delay, sem API key
"""
import sys, json, os
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import yfinance as yf

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
from crypto_multi_agent import CryptoConfluencia
from pair_selector import CryptoPairSelector
from tradingview_feed import TradingViewFeed

# ═══ CONFIG ═══
RR = 3.0
RISK_PCT = 0.5
MIN_CONFIDENCE = 55

TRADES_FILE = Path.home() / '.hermes' / 'crypto' / 'open_trades.json'
SIGNALS_FILE = Path.home() / '.hermes' / 'crypto' / 'signals.json'

# Feed global
_feed = None

def get_feed():
    global _feed
    if _feed is None:
        _feed = TradingViewFeed()
    return _feed

def get_candles_tv(pair, feed):
    """Dados TradingView multi-TF."""
    return feed.get_multi_tf(pair, ['1m', '5m', '15m', '1h'])

def load_open_trades():
    if TRADES_FILE.exists():
        try:
            with open(TRADES_FILE) as f:
                return json.load(f)
        except: pass
    return []

def get_btc_change():
    try:
        df = yf.Ticker('BTC-USD').history(period='1d', interval='1h')
        if len(df) < 4: return None
        return (df['Close'].values[-1] / df['Close'].values[-5] - 1) * 100
    except: return None

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
print(f"═══ CRYPTO BOT v8 (Hyperliquid + Multi-TF) — {datetime.now(timezone.utc).strftime('%d/%m %H:%M')} UTC ═══")
print()

try:
    # Iniciar feed
    feed = get_feed()
    print(f"[Feed] TradingView direto (Binance)")
    
    open_trades = load_open_trades()
    print(f"[0] Trades abertos: {len(open_trades)}/1")
    for t in open_trades:
        print(f"    {t['pair']:8s} {t['direction']:4s} @{t['entry']:.4f}")
    print()
    
    # Selecionar pares
    print("[1/3] Selecionando pares (anti-corr USD)...")
    selector = CryptoPairSelector(max_pairs=3)
    selected = selector.select_best_pairs()
    
    if not selected:
        print("  ⚠️ Nenhum par disponível")
        print("═══ FIM ═══")
        sys.exit(0)
    
    selector.print_summary()
    print()
    
    # BTC referência
    print("[2/3] Obtendo dados BTC...")
    btc_change = get_btc_change()
    btc_price = feed.get_price('BTCUSD')
    print(f"       BTC: ${btc_price:,.2f}" if btc_price else "       BTC: sem dados")
    print(f"       4h change: {btc_change:+.2f}%" if btc_change else "")
    print()
    
    # Analisar pares
    print("[3/3] Analisando pares (M1 Hyperliquid + Yahoo Fallback)...")
    agent = CryptoConfluencia()
    signals_found = []
    
    for pair_info in selected:
        pair = pair_info['pair']
        sym = pair_info['sym']
        pip = pair_info['pip']
        
        can_open, reason = selector.can_open_trade(pair, pair_info['direction'])
        if not can_open:
            print(f"  {pair:8s} 🚫 {reason}")
            continue
        
        try:
            # Dados TradingView M1
            h, l, c, o, v = feed.get_candles(pair, '1m', 200)
            if c is None or len(c) < 30:
                print(f"  {pair:8s} sem dados TV")
                continue
            
            # Daily bias (yfinance diário)
            df_d = yf.Ticker(sym).history(period='30d', interval='1d')
            cm = {c.lower(): c for c in df_d.columns}
            dh = df_d[cm.get('high','High')].values
            dl = df_d[cm.get('low','Low')].values
            dc = df_d[cm.get('close','Close')].values
            bias = get_daily_bias(dh, dl, dc)
            
            if bias == 'NEUTRAL':
                print(f"  {pair:8s} BIAS NEUTRAL [tv]")
                continue
            
            # Níveis diários
            daily_levels = {
                'resistance': max(dh[-10:]) if len(dh) >= 10 else max(dh),
                'support': min(dl[-10:]) if len(dl) >= 10 else min(dl)
            }
            
            # Análise multi-agente + multi-TF completo
            decision, conf, signal, v_info = agent.analyze(
                pair, h, l, c, o, bias, pip,
                btc_change if pair != 'BTCUSD' else None,
                MIN_CONFIDENCE, v, daily_levels
            )
            
            atr_pct = (v_info or {}).get('atr_pct', 0.5)
            sl_rec = (v_info or {}).get('sl_recommend', None)
            
            if decision != 'NEUTRAL' and signal:
                entry = signal['entry']
                sl, tp, sl_pct = calculate_sl_tp(entry, atr_pct, decision, sl_rec)
                
                print(f"  ✅ {pair:8s} {decision:4s} @{entry:.4f} | "
                      f"{signal.get('type','?')} Q={signal.get('quality',0)} | "
                      f"SL={sl_pct:.2f}% TP={sl_pct*RR:.2f}% | "
                      f"Conf={conf:.0f}% [tv]")
                
                signals_found.append({
                    'pair': pair, 'sym': sym, 'direction': decision,
                    'entry': float(entry), 'sl': float(sl), 'tp': float(tp),
                    'sl_pct': sl_pct, 'conf': conf,
                    'pattern': signal.get('type', '?'),
                    'quality': signal.get('quality', 0),
                    'atr_pct': atr_pct, 'regime': (v_info or {}).get('regime'),
                    'group': pair_info.get('group', '?'),
                    'time': datetime.now(timezone.utc).isoformat(),
                    'source': 'tv'
                })
                
                open_trades.append(signals_found[-1])
                TRADES_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(TRADES_FILE, 'w') as f:
                    json.dump(open_trades, f, indent=2, default=str)
            else:
                print(f"  {pair:8s} {decision:7s} conf={conf:.0f}% [tv]")
        
        except Exception as e:
            print(f"  {pair:8s} ❌ {e}")
    
    print()
    
    if signals_found:
        print(f"═══ {len(signals_found)} SINAL(is) ═══")
        for sig in signals_found:
            print(f"  {sig['pair']} {sig['direction']} @{sig['entry']:.4f} "
                  f"SL={sig['sl_pct']:.2f}% TP={sig['sl_pct']*RR:.2f}% "
                  f"[{sig.get('source','?')}]")
        with open(SIGNALS_FILE, 'w') as f:
            json.dump(signals_found, f, indent=2, default=str)
        print(f"\n  Sinais: {SIGNALS_FILE}")
    else:
        print(f"═══ NENHUM SINAL ═══")
    
    print(f"\n═══ FIM ═══")

except Exception as e:
    print(f"\n❌ {e}")
    import traceback
    traceback.print_exc()
