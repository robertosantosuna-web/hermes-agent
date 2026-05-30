#!/usr/bin/env python3
"""
CRYPTO DAEMON v1 — Monitoramento contínuo 24/7.
- Scan dos 4 pares (BTC, ETH, DOGE, BNB) a cada 30s
- Sempre escolhe o MELHOR sinal entre todos os pares
- Execução IMEDIATA quando sinal qualifica
- Substitui o cron autopilot (scanner + executor separados)
"""
import sys, json, time, signal
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
from pair_selector import CryptoPairSelector
from crypto_multi_agent import CryptoConfluencia
from tradingview_feed import TradingViewFeed
from binance_trader import BinanceTrader
from binance_executor import log_trade

TRADES_FILE = Path.home() / '.hermes' / 'crypto' / 'open_trades.json'
SIGNALS_FILE = Path.home() / '.hermes' / 'crypto' / 'signals.json'
CONFIG_PATH = Path.home() / '.hermes' / 'crypto' / 'binance_config.json'
STATE_FILE = Path.home() / '.hermes' / 'crypto' / 'daemon_state.json'

SCAN_INTERVAL = 30  # segundos entre scans
MIN_CONFIDENCE = 55
RR = 3.0

# Pares monitorados (todos, sem exceção)
ALL_PAIRS = [
    {'pair': 'BTCUSD', 'sym': 'BTC-USD', 'pip': 1.0},
    {'pair': 'ETHUSD', 'sym': 'ETH-USD', 'pip': 0.1},
    {'pair': 'DOGEUSD', 'sym': 'DOGE-USD', 'pip': 0.001},
    {'pair': 'BNBUSD', 'sym': 'BNB-USD', 'pip': 0.1},
]

feed = None
agent = None
trader = None
running = True

def get_feed():
    global feed
    if feed is None:
        feed = TradingViewFeed()
    return feed

def get_agent():
    global agent
    if agent is None:
        agent = CryptoConfluencia()
    return agent

def get_trader():
    global trader
    if trader is None:
        trader = BinanceTrader(testnet=False)
    return trader

def save_state(data):
    STATE_FILE.write_text(json.dumps(data, indent=2, default=str))

def load_open_trades():
    if TRADES_FILE.exists():
        try:
            with open(TRADES_FILE) as f:
                return json.load(f)
        except:
            pass
    return []

def has_open_trade():
    """Verifica se há trade ativo: arquivo, ordens Binance, OU empréstimos margin."""
    trades = load_open_trades()
    if trades:
        return True
    # Double-check na Binance
    try:
        t = get_trader()
        orders = t._request('GET', '/sapi/v1/margin/openOrders', signed=True)
        if orders:
            return True
        # Verificar empréstimos ativos (short não fechado)
        acct = t._request('GET', '/sapi/v1/margin/account', signed=True)
        for a in acct.get('userAssets', []):
            if float(a.get('borrowed', 0)) > 0.0001:
                return True  # Tem empréstimo = posição aberta
    except:
        pass
    return False

def get_daily_bias(highs, lows, closes):
    if len(highs) < 3:
        return 'NEUTRAL'
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
    sp = entry * sl_pct / 100
    if direction == 'BUY':
        return entry - sp, entry + sp * RR, sl_pct
    return entry + sp, entry - sp * RR, sl_pct

def scan_all_pairs():
    """Scanner completo: analisa TODOS os pares na ordem de favorabilidade, retorna o melhor sinal."""
    f = get_feed()
    ag = get_agent()
    selector = CryptoPairSelector(max_pairs=4)
    
    # ═══ PASSO 1: Pair selector ranqueia pares por favorabilidade ═══
    ranked = selector.select_best_pairs()
    
    if not ranked:
        # Seletor não encontrou pares viáveis, testar todos como fallback
        ranked = [{'pair': p['pair'], 'sym': p['sym'], 'pip': p['pip'], 
                    'direction': 'NEUTRAL', 'score': 0} for p in ALL_PAIRS]
    
    best_signal = None
    best_score = -999
    
    # ═══ PASSO 2: Scannear na ORDEM do ranking (melhor primeiro) ═══
    for r in ranked:
        pair = r['pair']
        pip = r.get('pip', 0.1)
        preferred_dir = r.get('direction', 'NEUTRAL')
        
        # Direções a testar: preferida do seletor primeiro, depois a outra
        if preferred_dir != 'NEUTRAL':
            test_dirs = [preferred_dir, 'SELL' if preferred_dir == 'BUY' else 'BUY']
        else:
            test_dirs = ['BUY', 'SELL']
        
        for direction in test_dirs:
            can, reason = selector.can_open_trade(pair, direction)
            if not can:
                continue  # Bloqueado por IR gate
            
            try:
                h, l, c, o, v = f.get_candles(pair, '1m', 1500)  # ~25h de dados
                if c is None or len(c) < 30:
                    continue
                
                # Daily bias via M1 candles (resample pra diário)
                import numpy as np
                if len(c) >= 1440:  # 24h de M1
                    # Resample: pegar high/low/close diário
                    daily_h = [max(h[i:i+1440]) for i in range(0, len(h), 1440)]
                    daily_l = [min(l[i:i+1440]) for i in range(0, len(l), 1440)]
                    daily_c = [c[i+1439] for i in range(0, len(c), 1440) if i+1439 < len(c)]
                else:
                    # Dados insuficientes, usar últimas velas
                    daily_h = [max(h[-200:])]
                    daily_l = [min(l[-200:])]
                    daily_c = [c[-1]]
                
                bias = get_daily_bias(daily_h, daily_l, daily_c)
                daily_levels = {
                    'resistance': max(daily_h[-3:]) if len(daily_h) >= 3 else max(daily_h),
                    'support': min(daily_l[-3:]) if len(daily_l) >= 3 else min(daily_l)
                }
                
                # Só testa a direção alinhada com o bias (ou ambas se NEUTRAL)
                test_dirs = [direction]
                if bias != 'NEUTRAL' and direction != bias:
                    continue  # Direção contra bias, pula
                
                decision, conf, sig, info = ag.analyze(
                    pair, h, l, c, o, direction, pip,
                    None, MIN_CONFIDENCE, v, daily_levels
                )
                
                if decision == 'NEUTRAL' or not sig:
                    continue
                
                # Score composto: qualidade do sinal (IR + confiança)
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
                        'pair': pair,
                        'sym': r['sym'],
                        'direction': decision,
                        'entry': float(entry),
                        'sl': float(sl),
                        'tp': float(tp),
                        'sl_pct': sl_pct,
                        'conf': conf,
                        'pattern': sig.get('type', '?'),
                        'quality': quality,
                        'ir': ir,
                        'atr_pct': atr_pct,
                        'score': score,
                        'time': datetime.now(timezone.utc).isoformat(),
                        'source': 'tv'
                    }
                    
            except Exception as e:
                continue
    
    return best_signal

def execute_signal(signal_data):
    """Executa o melhor sinal imediatamente."""
    t = get_trader()
    pair = signal_data['pair']
    direction = signal_data['direction']
    entry = signal_data['entry']
    sl = signal_data['sl']
    tp = signal_data['tp']
    
    # Calcular tamanho
    spot = t.get_balance('USDT')
    margin = t._get_margin_balance('USDT')
    total_balance = spot + margin
    
    # Carregar config para max_position
    cfg = {}
    if CONFIG_PATH.exists():
        cfg = json.loads(CONFIG_PATH.read_text())
    
    max_pos = cfg.get('max_position_usdt', 19)
    position_size = min(total_balance, max_pos)
    position_size = max(position_size, 5)
    
    print(f"\n🚀 EXECUTANDO: {pair} {direction} ${position_size:.2f}")
    print(f"   Entry={entry:.4f} SL={sl:.4f} TP={tp:.4f} IR={signal_data['ir']:.1f} Conf={signal_data['conf']:.0f}%")
    
    try:
        result = t.execute_signal(pair, direction, entry, sl, tp, usdt_amount=position_size)
        
        # Registrar em open_trades.json
        trade_record = {
            'pair': pair,
            'direction': direction,
            'entry': entry,
            'sl': sl,
            'tp': tp,
            'oco_id': result.get('oco', {}).get('orderListId') if result.get('oco') else None,
            'time': datetime.now(timezone.utc).isoformat(),
        }
        
        if result.get('partial'):
            trade_record['partial'] = True
            trade_record['tp1_order_id'] = result['tp1'].get('orderId') if result.get('tp1') else None
            trade_record['sl_moved'] = False
        
        with open(TRADES_FILE, 'w') as f:
            json.dump([trade_record], f, indent=2, default=str)
        
        # Limpar signals
        if SIGNALS_FILE.exists():
            SIGNALS_FILE.unlink()
        
        print(f"✅ EXECUTADO: OCO={trade_record.get('oco_id')} partial={result.get('partial')}")
        return True
        
    except Exception as e:
        print(f"❌ Erro execução: {e}")
        return False

def main():
    global running
    
    print(f"🔴 CRYPTO DAEMON v1 — {datetime.now().strftime('%d/%m %H:%M')}")
    print(f"   Monitorando: BTC, ETH, DOGE, BNB (scan a cada {SCAN_INTERVAL}s)")
    print(f"   Modo: execução IMEDIATA no melhor sinal")
    print()
    
    signal.signal(signal.SIGTERM, lambda *_: setattr(sys.modules[__name__], 'running', False))
    signal.signal(signal.SIGINT, lambda *_: setattr(sys.modules[__name__], 'running', False))
    
    scan_count = 0
    last_btc = 0
    
    while running:
        try:
            scan_count += 1
            ts = datetime.now().strftime('%H:%M:%S')
            
            # Verificar trade aberto
            if has_open_trade():
                if scan_count % 6 == 0:  # A cada ~3min
                    trades = load_open_trades()
                    t = trades[0] if trades else None
                    pair_info = f"{t['pair']} {t['direction']}" if t else "?"
                    print(f"[{ts}] 🔒 Trade ativo: {pair_info}")
                time.sleep(SCAN_INTERVAL)
                continue
            
            # Scan completo
            signal_data = scan_all_pairs()
            
            if signal_data:
                score = signal_data['score']
                ir = signal_data['ir']
                pair = signal_data['pair']
                direction = signal_data['direction']
                
                print(f"[{ts}] 🎯 {pair} {direction} @{signal_data['entry']:.4f} "
                      f"IR={ir:.1f} Conf={signal_data['conf']:.0f}% Score={score:.1f}")
                
                # Executar IMEDIATAMENTE
                execute_signal(signal_data)
            else:
                if scan_count % 2 == 0:  # Log a cada ~60s
                    # Mostrar preço BTC como heartbeat
                    try:
                        btc = get_feed().get_price('BTCUSD')
                        if btc and abs(btc - last_btc) > 10:
                            last_btc = btc
                            print(f"[{ts}] 📊 BTC=${btc:,.0f} | Sem sinal qualificado")
                    except:
                        pass
            
            # Salvar estado
            save_state({
                'status': 'running',
                'last_scan': datetime.now(timezone.utc).isoformat(),
                'scans': scan_count,
                'open_trades': len(load_open_trades()),
            })
            
            time.sleep(SCAN_INTERVAL)
            
        except Exception as e:
            print(f"[{ts}] ⚠️ Erro: {e}")
            time.sleep(SCAN_INTERVAL)
    
    print("\n👋 Daemon encerrado")

if __name__ == '__main__':
    main()
