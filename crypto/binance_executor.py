#!/usr/bin/env python3
"""
CRYPTO EXECUTOR v2 — Com Safety Checks
- Circuit breaker (perda diária máxima)
- Ordem OCO obrigatória (SL sempre junto)
- Verificação de saldo mínimo
- Log de trades
"""
import sys, json, os
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
from binance_trader import BinanceTrader
from telegram_notify import notify_open, notify_close

CONFIG_PATH = Path.home() / '.hermes' / 'crypto' / 'binance_config.json'
SIGNALS_PATH = Path.home() / '.hermes' / 'crypto' / 'signals.json'
TRADE_LOG_PATH = Path.home() / '.hermes' / 'crypto' / 'trade_log.json'

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(cfg, f, indent=2)

def log_trade(trade):
    log = []
    if TRADE_LOG_PATH.exists():
        try:
            with open(TRADE_LOG_PATH) as f:
                log = json.load(f)
        except:
            pass
    log.append(trade)
    with open(TRADE_LOG_PATH, 'w') as f:
        json.dump(log, f, indent=2, default=str)

def main():
    cfg = load_config()
    safety = cfg.get('safety', {})
    
    if not cfg.get('api_key') or 'COLE_SUA' in cfg.get('api_key', ''):
        print("❌ API keys não configuradas")
        sys.exit(1)
    
    trader = BinanceTrader(testnet=cfg.get('testnet', False))
    
    # ═══ SAFETY CHECK 1: Conexão ═══
    if not trader.check_connection():
        print("❌ Falha na conexão")
        sys.exit(1)
    
    balance = trader.get_balance('USDT')
    margin_balance = trader._get_margin_balance('USDT')
    total_balance = balance + margin_balance
    print(f"\n💰 Saldo: Spot=${balance:.2f} | Margin=${margin_balance:.2f} | Total=${total_balance:.2f}")
    
    # ═══ SAFETY CHECK 2: Saldo mínimo ═══
    min_balance = safety.get('min_balance_usdt', 5)
    if total_balance < min_balance:
        print(f"🛑 CIRCUIT BREAKER: Saldo ${total_balance:.2f} abaixo do mínimo ${min_balance:.2f}")
        sys.exit(0)
    
    # ═══ SAFETY CHECK 3: Perda diária ═══
    daily = cfg.get('daily_pnl', {})
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    if daily.get('date') != today:
        daily = {'date': today, 'trades': 0, 'pnl_usdt': 0}
        cfg['daily_pnl'] = daily
        save_config(cfg)
    
    max_daily_loss = safety.get('max_daily_loss_usdt', 5)
    if daily['pnl_usdt'] < -max_daily_loss:
        print(f"🛑 CIRCUIT BREAKER: Perda diária ${daily['pnl_usdt']:.2f} excede limite ${max_daily_loss:.2f}")
        sys.exit(0)
    
    print(f"📊 Hoje: {daily['trades']} trades, PnL: ${daily['pnl_usdt']:.2f}")
    
    # ═══ SAFETY CHECK 4: Ordens abertas ═══
    open_orders = trader.get_open_orders()
    if open_orders:
        print(f"⚠️ {len(open_orders)} ordem(ns) aberta(s) — não abrindo novas")
        for o in open_orders:
            print(f"   {o.get('symbol')} {o.get('side')} {o.get('type')} qty={o.get('origQty')}")
        sys.exit(0)
    
    # ═══ Sinais ═══
    if not SIGNALS_PATH.exists():
        sys.exit(0)
    
    with open(SIGNALS_PATH) as f:
        signals = json.load(f)
    
    if not signals:
        sys.exit(0)
    
    # Pega só o primeiro sinal (1 trade por vez)
    sig = signals[0]
    pair = sig['pair']
    direction = sig['direction']
    entry = sig['entry']
    sl = sig['sl']
    tp = sig['tp']
    sl_pct = sig.get('sl_pct', 0.3)
    conf = sig.get('conf', 0)
    
    print(f"\n📊 SINAL: {pair} {direction} @{entry:.4f}")
    print(f"   SL={sl:.4f} ({sl_pct:.2f}%) TP={tp:.4f} ({sl_pct*3:.2f}%) Conf={conf:.0f}%")
    
    if not cfg.get('auto_execute', False):
        print("⏸️ Auto-execute desligado")
        sys.exit(0)
    
    # ═══ SAFETY CHECK 5: Slippage ═══
    symbol = pair.replace('USD', 'USDT')
    try:
        current_price = trader.get_price(symbol)
        slippage = abs(current_price - entry) / entry * 100
        max_slippage = safety.get('max_slippage_pct', 0.5)
        if slippage > max_slippage:
            print(f"⚠️ Slippage alto: {slippage:.2f}% (entrada={entry:.4f}, atual={current_price:.4f})")
            print(f"   Aguardando próximo tick...")
            sys.exit(0)
        print(f"   Preço atual: {current_price:.4f} (slippage: {slippage:.2f}%)")
    except:
        pass
    
    # ═══ EXECUTAR ═══
    position_size = min(total_balance, cfg.get('max_position_usdt', 19))
    position_size = max(position_size, 5)  # Mínimo $5 (Binance rule)
    
    print(f"\n🚀 EXECUTANDO: {pair} {direction} ${position_size:.2f}")
    
    try:
        result = trader.execute_signal(
            pair, direction, entry, sl, tp,
            usdt_amount=position_size
        )
        
        # Log
        trade_log = {
            'time': datetime.now(timezone.utc).isoformat(),
            'pair': pair, 'direction': direction,
            'entry': entry, 'sl': sl, 'tp': tp,
            'amount': position_size,
            'conf': conf,
            'result': result
        }
        log_trade(trade_log)
        
        # Atualizar daily PnL (começa zerado, atualiza quando fechar)
        daily['trades'] += 1
        cfg['daily_pnl'] = daily
        save_config(cfg)
        
        # Limpar sinal executado
        SIGNALS_PATH.unlink()
        
        print(f"✅ TRADE EXECUTADO!")
        print(f"   Ordem: {result}")
        
        # Notificar Telegram
        notify_open(pair, direction, entry, sl, tp, position_size)
        
    except Exception as e:
        print(f"❌ Erro: {e}")


if __name__ == '__main__':
    main()
