#!/usr/bin/env python3
"""
Gera link do TradingView no timestamp exato dos sinais do bot.
Uso: python3 tradingview_signals.py [data YYYY-MM-DD]
Sem argumentos = hoje.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

LOG_DIR = Path.home() / '.hermes' / 'forex' / 'paper_logs'

date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime('%Y-%m-%d')
log_file = LOG_DIR / f"daily_{date_str}.json"

if not log_file.exists():
    print(f"❌ Log não encontrado: {log_file}")
    sys.exit(1)

data = json.loads(log_file.read_text())

PAIR_SYMBOLS = {
    'GBP/USD': 'OANDA%3AGBPUSD',
    'AUD/USD': 'OANDA%3AAUDUSD', 
    'EUR/USD': 'OANDA%3AEURUSD',
    'NZD/USD': 'OANDA%3ANZDUSD',
}

print(f"📊 Sinais do bot — {date_str}")
print(f"   Abra cada link e verifique o candle no timestamp")
print()

# Closed trades
if data.get('closed_trades'):
    print("── TRADES FECHADOS ──")
    for t in data['closed_trades']:
        icon = '✅' if t['result'] == 'WIN' else '❌'
        pair = t['pair']
        symbol = PAIR_SYMBOLS.get(pair, '')
        opened = t.get('opened_at', '')[:16]
        # Generate TradingView link at entry time
        tv_url = f"https://www.tradingview.com/chart/?symbol={symbol}&interval=15"
        print(f"{icon} {pair:<10} {t['direction']:>5s} {opened}")
        print(f"   Entry={t['entry']} SL={t['sl_pips']}p TP={t['tp_pips']}p → {t['result']} {t['pnl_pips']:+.1f}p")
        print(f"   🔗 {tv_url}")
        print()

# Open positions
if data.get('open_positions'):
    print("── POSIÇÕES ABERTAS ──")
    for p in data['open_positions']:
        pair = p['pair']
        symbol = PAIR_SYMBOLS.get(pair, '')
        tv_url = f"https://www.tradingview.com/chart/?symbol={symbol}&interval=15"
        print(f"🔓 {pair:<10} {p['direction']:>5s} @ {p['entry']}")
        print(f"   SL={p['sl_pips']}p TP={p['tp_pips']}p | Aberto desde {p.get('opened_at','?')[:16]}")
        print(f"   🔗 {tv_url}")
        print()

# Stats
stats = data.get('stats', {})
if stats.get('trades', 0) > 0:
    print(f"── RESUMO ──")
    print(f"Trades: {stats['trades']} | WR: {stats['wr']}% | PnL: {stats['pnl_pips']:+.1f} pips")
