#!/usr/bin/env python3
"""
CRYPTO DAEMON FUTURES v1 — CDP executor (Edge).
Scanner TradingView + Execução via navegador Binance Futures.
Contorna bloqueio API Futures para KYC Brasil.
"""
import sys, json, time, signal
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
sys.path.insert(0, str(Path.home() / '.hermes' / 'scripts'))

from pair_selector import CryptoPairSelector
from crypto_multi_agent import CryptoConfluencia
from tradingview_feed import TradingViewFeed
from cdp_futures import CDPFuturesExecutor

TRADES_FILE = Path.home() / '.hermes' / 'crypto' / 'open_trades.json'
SIGNALS_FILE = Path.home() / '.hermes' / 'crypto' / 'signals.json'
CONFIG_PATH = Path.home() / '.hermes' / 'crypto' / 'binance_config.json'
STATE_FILE = Path.home() / '.hermes' / 'crypto' / 'daemon_state.json'

SCAN_INTERVAL = 45
MIN_CONFIDENCE = 50  # Reduzido: mais sinais
RR = 3.0
LEVERAGE = 5
RISK_PCT = 8.0  # Agressivo: Quarter-Kelly (8.3%)

ALL_PAIRS = [
    {'pair': 'BTCUSD', 'sym': 'BTC-USD', 'pip': 1.0},
    {'pair': 'ETHUSD', 'sym': 'ETH-USD', 'pip': 0.1},
    {'pair': 'DOGEUSD', 'sym': 'DOGE-USD', 'pip': 0.001},
    {'pair': 'BNBUSD', 'sym': 'BNB-USD', 'pip': 0.1},
]

feed, agent, executor = None, None, None
running = True

def get_feed():
    global feed
    if feed is None: feed = TradingViewFeed()
    return feed

def get_agent():
    global agent
    if agent is None: agent = CryptoConfluencia()
    return agent

def get_executor():
    global executor
    if executor is None: executor = CDPFuturesExecutor()
    return executor

def save_state(data):
    STATE_FILE.write_text(json.dumps(data, indent=2, default=str))

def load_open_trades():
    if TRADES_FILE.exists():
        try:
            with open(TRADES_FILE) as f: return json.load(f)
        except: pass
    return []

def has_open_trade():
    trades = load_open_trades()
    if trades: return True
    try:
        ex = get_executor()
        ex._connect('BNBUSDT')
        pos = ex.get_position()
        if pos and pos.get('size') != '?':
            return True
        bal = ex.get_balance()
        return bal < 17.5  # Se balance < 17.5, tem posição aberta
    except:
        pass
    return False

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

# ═══ SCAN (igual ao daemon margin) ═══
def scan_all_pairs():
    f = get_feed()
    ag = get_agent()
    selector = CryptoPairSelector(max_pairs=4)
    
    ranked = selector.select_best_pairs()
    if not ranked:
        ranked = [{'pair': p['pair'], 'sym': p['sym'], 'pip': p['pip'], 'direction': 'NEUTRAL', 'score': 0} for p in ALL_PAIRS]
    
    best_signal = None
    best_score = -999
    
    btc_change = None
    try:
        bh, bl, bc, bo, bv = f.get_candles('BTCUSD', '15m', 20)
        if bc is not None and len(bc) >= 16:
            btc_change = (bc[-1] / bc[-16] - 1) * 100
    except: pass
    
    for r in ranked:
        pair = r['pair']; pip = r.get('pip', 0.1)
        preferred_dir = r.get('direction', 'NEUTRAL')
        test_dirs = [preferred_dir, 'SELL' if preferred_dir == 'BUY' else 'BUY'] if preferred_dir != 'NEUTRAL' else ['BUY', 'SELL']
        
        for direction in test_dirs:
            can, reason = selector.can_open_trade(pair, direction)
            if not can: continue
            
            try:
                h, l, c, o, v = f.get_candles(pair, '1m', 1500)
                if c is None or len(c) < 30: continue
                
                import numpy as np
                if len(c) >= 1440:
                    daily_h = [max(h[i:i+1440]) for i in range(0, len(h), 1440)]
                    daily_l = [min(l[i:i+1440]) for i in range(0, len(l), 1440)]
                    daily_c = [c[i+1439] for i in range(0, len(c), 1440) if i+1439 < len(c)]
                else:
                    daily_h = [max(h[-200:])]; daily_l = [min(l[-200:])]; daily_c = [c[-1]]
                
                bias = get_daily_bias(daily_h, daily_l, daily_c)
                daily_levels = {'resistance': max(daily_h[-3:]) if len(daily_h)>=3 else max(daily_h),
                               'support': min(daily_l[-3:]) if len(daily_l)>=3 else min(daily_l)}
                
                test_dirs2 = [direction]
                if bias != 'NEUTRAL' and direction != bias: continue
                
                decision, conf, sig, info = ag.analyze(
                    pair, h, l, c, o, direction, pip,
                    btc_change if pair != 'BTCUSD' else None,
                    MIN_CONFIDENCE, v, daily_levels)
                
                if decision == 'NEUTRAL' or not sig: continue
                
                ir = sig.get('impulse_ratio', 0)
                quality = sig.get('quality', 0)
                score = ir * 50 + conf * 0.3 + quality * 0.2
                
                if score > best_score:
                    atr_pct = (info or {}).get('atr_pct', 0.3)
                    sl_rec = (info or {}).get('sl_recommend', None)
                    entry = sig['entry']
                    sl, tp, sl_pct = calculate_sl_tp(entry, atr_pct, decision, sl_rec)
                    
                    best_score = score
                    best_signal = {
                        'pair': pair, 'sym': r['sym'], 'direction': decision,
                        'entry': float(entry), 'sl': float(sl), 'tp': float(tp),
                        'sl_pct': sl_pct, 'conf': conf, 'pattern': sig.get('type','?'),
                        'quality': quality, 'ir': ir, 'atr_pct': atr_pct,
                        'score': score, 'time': datetime.now(timezone.utc).isoformat(),
                        'source': 'tv'
                    }
            except Exception as e:
                continue
    
    return best_signal

# ═══ EXECUÇÃO CDP ═══
def execute_signal_cdp(signal_data):
    """Executa ordem via CDP no navegador Binance Futures."""
    ex = get_executor()
    pair = signal_data['pair']
    direction = signal_data['direction']
    entry = signal_data['entry']
    sl = signal_data['sl']
    tp = signal_data['tp']
    
    # Navegar pro par
    symbol = pair.replace('USD', 'USDT')
    ex._connect(symbol)
    
    # Balanço
    balance = ex.get_balance()
    if balance < 5:
        print(f"   ❌ Saldo insuficiente: ${balance:.2f}")
        return False
    
    # Tamanho: RISK_PCT% do equity
    risk_usd = balance * (RISK_PCT / 100)
    position_size = min(risk_usd * LEVERAGE, balance * 0.95)
    position_size = round(position_size, 1)
    
    # SL/TP ajustado
    sl_orig = sl
    if direction == 'BUY':
        sl_dist = abs(entry - sl)
        sl = entry - sl_dist * 1.15
        tp = entry + abs(tp - entry) * 0.95
    else:
        sl_dist = abs(sl - entry)
        sl = entry + sl_dist * 1.15
        tp = entry - abs(entry - tp) * 0.95
    
    print(f"\n🚀 CDP FUTURES: {pair} {direction} ${position_size:.1f} ({LEVERAGE}x)")
    print(f"   Entry={entry:.4f} SL={sl_orig:.4f}→{sl:.4f} TP={tp:.4f}")
    
    # Slippage check via TradingView
    try:
        current = get_feed().get_price(pair)
        if current:
            slip = abs(current - entry) / entry * 100
            sl_dist_pct = abs(entry - sl_orig) / entry * 100
            if slip > sl_dist_pct * 2:
                print(f"   ❌ SLIPPAGE BLOQUEANTE: {slip:.2f}% > {sl_dist_pct*2:.2f}%")
                return False
            if slip > sl_dist_pct:
                print(f"   ⚠️ Slippage {slip:.2f}%, ajustando...")
    except: pass
    
    # Executar via CDP
    result = ex.market_order(symbol, direction, position_size)
    
    if result.get('success'):
        trade_record = {
            'pair': pair, 'direction': direction,
            'entry': entry, 'sl': sl, 'tp': tp,
            'amount': position_size, 'leverage': LEVERAGE,
            'mode': 'futures_cdp',
            'time': datetime.now(timezone.utc).isoformat(),
        }
        with open(TRADES_FILE, 'w') as f:
            json.dump([trade_record], f, indent=2, default=str)
        
        if SIGNALS_FILE.exists(): SIGNALS_FILE.unlink()
        print(f"✅ CDP EXECUTADO: {direction} ${position_size:.1f} @{symbol}")
        return True
    else:
        print(f"❌ Falha CDP: {result}")
        return False

# ═══ MAIN ═══
def main():
    global running
    print(f"🔴 CRYPTO DAEMON FUTURES (CDP) — {datetime.now().strftime('%d/%m %H:%M')}")
    print(f"   Scanner: TradingView | Executor: Edge CDP | {LEVERAGE}x | Risco {RISK_PCT}%")
    print()
    
    signal.signal(signal.SIGTERM, lambda *_: setattr(sys.modules[__name__], 'running', False))
    signal.signal(signal.SIGINT, lambda *_: setattr(sys.modules[__name__], 'running', False))
    
    scan_count = 0
    last_btc = 0
    
    while running:
        try:
            scan_count += 1
            ts = datetime.now().strftime('%H:%M:%S')
            
            if has_open_trade():
                if scan_count % 6 == 0:
                    trades = load_open_trades()
                    t = trades[0] if trades else None
                    print(f"[{ts}] 🔒 Trade ativo: {t['pair']} {t['direction']}" if t else f"[{ts}] 🔒 Trade ativo")
                time.sleep(SCAN_INTERVAL)
                continue
            
            signal_data = scan_all_pairs()
            
            if signal_data:
                print(f"[{ts}] 🎯 {signal_data['pair']} {signal_data['direction']} "
                      f"@{signal_data['entry']:.4f} IR={signal_data['ir']:.1f} Conf={signal_data['conf']:.0f}%")
                execute_signal_cdp(signal_data)
            else:
                if scan_count % 2 == 0:
                    try:
                        btc = get_feed().get_price('BTCUSD')
                        if btc and abs(btc - last_btc) > 10:
                            last_btc = btc
                            print(f"[{ts}] 📊 BTC=${btc:,.0f} | Sem sinal")
                    except: pass
            
            save_state({
                'status': 'running', 'mode': 'futures_cdp',
                'last_scan': datetime.now(timezone.utc).isoformat(),
                'scans': scan_count, 'open_trades': len(load_open_trades()),
            })
            
            time.sleep(SCAN_INTERVAL)
            
        except Exception as e:
            print(f"[{ts}] ⚠️ Erro: {e}")
            time.sleep(SCAN_INTERVAL)
    
    get_executor().close()
    print("\n👋 Daemon Futures encerrado")

if __name__ == '__main__':
    main()
