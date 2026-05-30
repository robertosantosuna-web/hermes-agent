#!/usr/bin/env python3
"""
TRADE MONITOR UNIFICADO — Detecta fechamento + move SL→BE no parcial.
Substitui trade_close_monitor.py e partial_tp_monitor.py.
Roda a cada 1min via cron.
"""
import sys, json
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
from binance_trader import BinanceTrader
from telegram_notify import notify_close, send_telegram

TRADES_FILE = Path.home() / '.hermes' / 'crypto' / 'open_trades.json'
TRADE_LOG = Path.home() / '.hermes' / 'crypto' / 'trade_log.json'

def monitor():
    if not TRADES_FILE.exists():
        return
    
    with open(TRADES_FILE) as f:
        trades = json.load(f)
    
    if not trades:
        return
    
    trader = BinanceTrader(testnet=False)
    updated = False
    
    for t in list(trades):
        pair = t['pair']
        symbol = pair.replace('USD', 'USDT')
        direction = t['direction']
        entry = t['entry']
        is_partial = t.get('partial', False)
        
        try:
            orders = trader._request('GET', '/sapi/v1/margin/openOrders', signed=True)
            pair_orders = [o for o in orders if o.get('symbol') == symbol]
        except:
            continue
        
        # ═══ CASO 1: Trade fechou (sem ordens) ═══
        if not pair_orders and (t.get('oco_id') or t.get('tp1_order_id')):
            _handle_close(trader, t, symbol, direction, entry, trades)
            updated = True
            continue
        
        # ═══ CASO 2: Parcial — TP1 encheu? ═══
        if is_partial and not t.get('sl_moved') and t.get('tp1_order_id'):
            try:
                tp1_status = trader._request('GET', '/sapi/v1/margin/order', signed=True,
                                            symbol=symbol, orderId=t['tp1_order_id'])
                if tp1_status.get('status') == 'FILLED':
                    _move_sl_to_be(trader, t, symbol, entry, pair_orders)
                    updated = True
            except:
                pass
    
    if updated:
        with open(TRADES_FILE, 'w') as f:
            json.dump(trades, f, indent=2, default=str)

def _handle_close(trader, t, symbol, direction, entry, trades):
    """Trade fechou — registra e notifica."""
    try:
        my_trades = trader._request('GET', '/sapi/v1/margin/myTrades', 
                                   signed=True, symbol=symbol, limit=10)
        close_is_buyer = (direction == 'SELL')
        close_trades = [tr for tr in my_trades if tr.get('isBuyer') == close_is_buyer]
        
        if close_trades:
            latest = close_trades[-1]
            exit_price = float(latest['price'])
            qty = float(latest['qty'])
            pnl = (exit_price - entry) * qty if direction == 'BUY' else (entry - exit_price) * qty
        else:
            # Não achou trade de fechamento, usa preço atual
            exit_price = trader.get_price(symbol)
            pnl = 0
        
        result = 'WIN' if pnl > 0 else 'LOSS'
        balance = trader.get_balance('USDT') + trader._get_margin_balance('USDT')
        
        # Log
        log = []
        if TRADE_LOG.exists():
            with open(TRADE_LOG) as f:
                log = json.load(f)
        log.append({
            'time': datetime.now(timezone.utc).isoformat(),
            'pair': t['pair'], 'direction': direction,
            'entry': entry, 'exit': exit_price,
            'pnl': round(pnl, 2), 'result': result,
        })
        with open(TRADE_LOG, 'w') as f:
            json.dump(log, f, indent=2, default=str)
        
        # Notificar
        notify_close(t['pair'], result, pnl, balance)
        trades.remove(t)
        print(f"Trade fechado: {t['pair']} {result} ${pnl:.2f}")
        
    except Exception as e:
        print(f"Erro close {t['pair']}: {e}")
        trades.remove(t)  # Remove mesmo com erro

def _move_sl_to_be(trader, t, symbol, entry, pair_orders):
    """TP1 encheu — move SL pro breakeven."""
    try:
        tick_size = 0.01
        try:
            info = trader.get_symbol_info(symbol)
            tick_size = info.get('tick_size', 0.01)
            step = info.get('step_size', 0.0001)
        except:
            step = 0.0001
        
        sl_be = trader.round_to_tick(entry, tick_size)
        
        # Cancelar OCO antiga
        oco_id = t.get('oco_id')
        if oco_id:
            try:
                trader._request('DELETE', '/sapi/v1/margin/orderList', signed=True,
                              symbol=symbol, orderListId=oco_id)
            except:
                pass
        
        # Quantidade restante
        acct = trader._request('GET', '/sapi/v1/margin/account', signed=True)
        base = symbol.replace('USDT', '')
        free = 0
        for a in acct.get('userAssets', []):
            if a['asset'] == base:
                free = float(a['free'])
        
        rem_qty = trader.round_to_step(free * 0.98, step, use_floor=True)
        if rem_qty < 0.0001:
            return
        
        tp2 = trader.round_to_tick(t.get('tp', entry), tick_size)
        side = 'BUY' if t['direction'] == 'SELL' else 'SELL'
        
        new_oco = trader._request('POST', '/sapi/v1/margin/order/oco', signed=True,
                                symbol=symbol, side=side,
                                quantity=str(rem_qty),
                                price=str(tp2), stopPrice=str(sl_be),
                                stopLimitPrice=str(sl_be),
                                stopLimitTimeInForce='GTC',
                                sideEffectType='AUTO_REPAY')
        
        t['sl_moved'] = True
        t['sl_be'] = sl_be
        t['new_oco_id'] = new_oco.get('orderListId')
        
        msg = f"🔒 {t['pair']} {t['direction']} | TP1 ok → SL@{sl_be} | TP2@{tp2}"
        send_telegram(msg)
        print(msg)
        
    except Exception as e:
        print(f"Erro move SL {t['pair']}: {e}")

if __name__ == '__main__':
    monitor()
