#!/usr/bin/env python3
"""
CRYPTO BOT v6 + BINANCE — Execução real
Lê signals.json, executa na Binance via binance_trader.py
"""
import sys, json, os
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
from binance_trader import BinanceTrader

CONFIG_PATH = Path.home() / '.hermes' / 'crypto' / 'binance_config.json'
SIGNALS_PATH = Path.home() / '.hermes' / 'crypto' / 'signals.json'

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def main():
    cfg = load_config()
    
    if not cfg.get('api_key') or 'COLE_SUA' in cfg.get('api_key', ''):
        print("❌ API keys não configuradas em binance_config.json")
        sys.exit(1)
    
    trader = BinanceTrader(testnet=cfg.get('testnet', False))
    
    # Verificar conexão
    if not trader.check_connection():
        print("❌ Falha na conexão")
        sys.exit(1)
    
    # Ver saldo
    balance = trader.get_balance('USDT')
    print(f"\n💰 Saldo: {balance:.2f} USDT")
    
    if balance < 10:
        print("⚠️ Saldo abaixo do mínimo (10 USDT). Deposite via Pix na Binance.")
        print("   Binance → Buy Crypto → PIX → USDT")
        sys.exit(0)
    
    # Ver sinais pendentes
    if not SIGNALS_PATH.exists():
        print("Nenhum sinal pendente.")
        sys.exit(0)
    
    with open(SIGNALS_PATH) as f:
        signals = json.load(f)
    
    if not signals:
        print("Nenhum sinal pendente.")
        sys.exit(0)
    
    print(f"\n📊 {len(signals)} sinal(is) encontrado(s):")
    
    auto_execute = cfg.get('auto_execute', False)
    
    for i, sig in enumerate(signals):
        pair = sig['pair']
        direction = sig['direction']
        entry = sig['entry']
        sl = sig['sl']
        tp = sig['tp']
        sl_pct = sig.get('sl_pct', 0.3)
        conf = sig.get('conf', 0)
        
        print(f"\n  [{i+1}] {pair} {direction} @{entry:.4f}")
        print(f"      SL={sl:.4f} ({sl_pct:.2f}%) TP={tp:.4f} ({sl_pct*3:.2f}%) Conf={conf:.0f}%")
        
        if auto_execute:
            # Usar saldo disponível (mín $10, máx $19 por enquanto)
            position_size = min(balance, cfg.get('max_position_usdt', 19))
            position_size = max(position_size, 10)  # mínimo Binance
            
            print(f"      💰 Posição: {position_size:.2f} USDT (saldo total)")
            
            try:
                result = trader.execute_signal(
                    pair, direction, entry, sl, tp, 
                    usdt_amount=position_size
                )
                print(f"      ✅ Executado!")
            except Exception as e:
                print(f"      ❌ Erro: {e}")
        else:
            print(f"      ⏸️ Auto-execute desligado. Para ativar: auto_execute: true no config")
    
    if not auto_execute:
        print(f"\n🔒 Modo: somente análise. Para executar ordens reais:")
        print(f"   Edite binance_config.json → \"auto_execute\": true")


if __name__ == '__main__':
    main()
