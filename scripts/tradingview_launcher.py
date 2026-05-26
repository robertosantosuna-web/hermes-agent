#!/usr/bin/env python3
"""
Abre TradingView com os 4 pares + Pine Script carregado.
Uso: python3 tradingview_launcher.py
"""
import webbrowser
import time

PAIRS = [
    ('GBP/USD', 'OANDA%3AGBPUSD'),
    ('AUD/USD', 'OANDA%3AAUDUSD'),
    ('EUR/USD', 'OANDA%3AEURUSD'),
    ('NZD/USD', 'OANDA%3ANZDUSD'),
]

print("📊 Abrindo TradingView com 4 pares + M15...")

for name, symbol in PAIRS:
    url = f"https://www.tradingview.com/chart/?symbol={symbol}&interval=15"
    print(f"  {name}: {url}")
    webbrowser.open(url)
    time.sleep(0.5)

print("\n✅ 4 abas abertas. Para cada aba:")
print("  1. Clicar 'Pine Editor' (painel inferior)")
print("  2. Colar o conteúdo de ~/.hermes/forex/choch_fvg_m15.pine")
print("  3. Clicar 'Add to chart'")
print("  4. Aba 'Strategy Tester' → ver resultado do backtest")
print(f"\n📁 Pine Script: ~/.hermes/forex/choch_fvg_m15.pine")
