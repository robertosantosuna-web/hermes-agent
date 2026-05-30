#!/usr/bin/env python3
"""CRYPTO BOT v9 — TradingView + IR gate + Telegram notify"""
import sys, json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import yfinance as yf

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
from crypto_multi_agent import CryptoConfluencia
from pair_selector import CryptoPairSelector
from tradingview_feed import TradingViewFeed

RR = 3.0; MIN_CONFIDENCE = 55
TRADES_FILE = Path.home() / '.hermes' / 'crypto' / 'open_trades.json'
SIGNALS_FILE = Path.home() / '.hermes' / 'crypto' / 'signals.json'

_feed = None
def get_feed():
    global _feed
    if _feed is None: _feed = TradingViewFeed()
    return _feed

def load_open_trades():
    if TRADES_FILE.exists():
        try:
            with open(TRADES_FILE) as f: return json.load(f)
        except: pass
    return []

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
    if sl_recommend is None: sl_recommend = max(atr_pct * 1.5, 0.15)
    sl_pct = min(sl_recommend, 1.5)
    sp = entry * sl_pct / 100
    if direction == 'BUY': return entry - sp, entry + sp * RR, sl_pct
    return entry + sp, entry - sp * RR, sl_pct

# ═══ MAIN ═══
now = datetime.now(timezone.utc)
print(f"═══ CRYPTO BOT v9 — {now.strftime('%d/%m %H:%M')} UTC ═══")
print()

try:
    feed = get_feed()
    print("[Feed] TradingView direto (Binance)")
    
    open_trades = load_open_trades()
    print(f"[0] Trades: {len(open_trades)}/1")
    for t in open_trades:
        print(f"    {t['pair']} {t['direction']} @{t['entry']:.4f}")
    print()
    
    print("[1/3] Selecionando pares...")
    selector = CryptoPairSelector(max_pairs=3)
    selected = selector.select_best_pairs()
    if not selected:
        print("  Nenhum par disponível"); print("═══ FIM ═══"); sys.exit(0)
    selector.print_summary()
    print()
    
    print("[2/3] BTC...")
    btc_price = feed.get_price('BTCUSD')
    btc_change = None
    try:
        df = yf.Ticker('BTC-USD').history(period='1d', interval='1h')
        if len(df) >= 5:
            btc_change = (df['Close'].values[-1] / df['Close'].values[-5] - 1) * 100
    except: pass
    print(f"  BTC: ${btc_price:,.2f}" + (f" 4h: {btc_change:+.2f}%" if btc_change else ""))
    print()
    
    print("[3/3] Analisando...")
    agent = CryptoConfluencia()
    signals_found = []
    
    for pi in selected:
        pair, sym, pip = pi['pair'], pi['sym'], pi['pip']
        
        can, reason = selector.can_open_trade(pair, pi['direction'])
        if not can:
            print(f"  {pair:8s} 🚫 {reason}")
            continue
        
        try:
            h, l, c, o, v = feed.get_candles(pair, '1m', 1000)  # ~16h de dados
            if c is None or len(c) < 30:
                print(f"  {pair:8s} sem dados"); continue
            
            df_d = yf.Ticker(sym).history(period='30d', interval='1d')
            cm = {k.lower(): k for k in df_d.columns}
            dh = df_d[cm.get('high','High')].values
            dl = df_d[cm.get('low','Low')].values
            dc = df_d[cm.get('close','Close')].values
            
            bias = get_daily_bias(dh, dl, dc)
            daily_levels = {
                'resistance': max(dh[-10:]) if len(dh) >= 10 else max(dh),
                'support': min(dl[-10:]) if len(dl) >= 10 else min(dl)
            }
            
            # Testar direções
            test_dirs = [bias] if bias != 'NEUTRAL' else ['BUY', 'SELL']
            decision = 'NEUTRAL'; conf = 0; sig = None; info = {}
            
            for tb in test_dirs:
                if tb == 'NEUTRAL': continue
                decision, conf, sig, info = agent.analyze(
                    pair, h, l, c, o, tb, pip,
                    btc_change if pair != 'BTCUSD' else None,
                    MIN_CONFIDENCE, v, daily_levels
                )
                if decision != 'NEUTRAL' and sig: break
            
            if decision == 'NEUTRAL' or not sig:
                print(f"  {pair:8s} NEUTRAL [tv]"); continue
            
            atr_pct = (info or {}).get('atr_pct', 0.3)
            sl_rec = (info or {}).get('sl_recommend', None)
            entry = sig['entry']
            sl, tp, sl_pct = calculate_sl_tp(entry, atr_pct, decision, sl_rec)
            
            print(f"  ✅ {pair:8s} {decision:4s} @{entry:.4f} | {sig.get('type','?')} "
                  f"Q={sig.get('quality',0)} IR={sig.get('impulse_ratio',0):.1f} | "
                  f"SL={sl_pct:.2f}% TP={sl_pct*RR:.2f}% | Conf={conf:.0f}%")
            
            trade = {
                'pair': pair, 'sym': sym, 'direction': decision,
                'entry': float(entry), 'sl': float(sl), 'tp': float(tp),
                'sl_pct': sl_pct, 'conf': conf,
                'pattern': sig.get('type','?'), 'quality': sig.get('quality',0),
                'atr_pct': atr_pct, 'regime': (info or {}).get('regime'),
                'group': pi.get('group','?'),
                'time': now.isoformat(), 'source': 'tv'
            }
            signals_found.append(trade)
            # NÃO salvar em open_trades.json — executor que faz isso após confirmar
        
        except Exception as e:
            print(f"  {pair:8s} ❌ {e}")
    
    print()
    if signals_found:
        print(f"═══ {len(signals_found)} SINAL(is) ═══")
        for s in signals_found:
            print(f"  {s['pair']} {s['direction']} @{s['entry']:.4f} "
                  f"SL={s['sl_pct']:.2f}% TP={s['sl_pct']*RR:.2f}%")
        with open(SIGNALS_FILE, 'w') as f:
            json.dump(signals_found, f, indent=2, default=str)
    else:
        print("═══ NENHUM SINAL ═══")
    print("═══ FIM ═══")

except Exception as e:
    print(f"\n❌ {e}")
    import traceback; traceback.print_exc()
