#!/usr/bin/python3
"""
FOREX DAILY REVIEW — Mínimo: WR + P&L + trades fechados.
Usa trade_log.json + balance_log.json.
"""
import json
from datetime import datetime
from pathlib import Path

TRADE_LOG = Path.home() / '.hermes' / 'forex' / 'trade_log.json'
BALANCE_LOG = Path.home() / '.hermes' / 'forex' / 'balance_log.json'

def main():
    if not TRADE_LOG.exists():
        return
    
    data = json.loads(TRADE_LOG.read_text())
    trades = data.get('trades', [])
    today = datetime.now().strftime('%Y-%m-%d')
    
    today_trades = [t for t in trades if t['timestamp'].startswith(today)]
    closed = [t for t in today_trades if t['status'] == 'closed']
    dups = [t for t in today_trades if t['status'] == 'duplicate']
    
    if not today_trades:
        return
    
    wins = len([t for t in closed if (t.get('pnl') or 0) > 0])
    total_pnl = sum(t.get('pnl') or 0 for t in closed)
    wr = round(wins / len(closed) * 100, 1) if closed else 0
    
    # Saldo via balance log
    balance = None
    if BALANCE_LOG.exists():
        bl = json.loads(BALANCE_LOG.read_text())
        if bl:
            balance = bl[-1].get('balance')
    
    lines = [f"📊 Forex {today}"]
    if closed:
        lines.append(f"WR={wr}% | P&L=${total_pnl:+.2f} | {wins}W/{len(closed)-wins}L")
    if dups:
        lines.append(f"⚠️ {len(dups)} duplicados (bug corrigido)")
    if balance:
        lines.append(f"Saldo: ${balance:,.2f}")
    
    print('\n'.join(lines))

if __name__ == '__main__':
    main()
