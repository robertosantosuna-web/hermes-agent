#!/usr/bin/python3
"""
Forex Trade Tracker — registra trades e calcula WR/P&L via visão (MT5).
Zero tokens. Roda como script watchdog.
"""
import json, subprocess, os, sys
from datetime import datetime
from pathlib import Path

FOREX_DIR = Path.home() / '.hermes' / 'forex'
TRADE_LOG = FOREX_DIR / 'trade_log.json'
STATE_FILE = FOREX_DIR / 'real_state.json'

VISION_ENGINE = Path.home() / '.hermes' / 'scripts' / 'vision_engine.py'

def load_log():
    if TRADE_LOG.exists():
        return json.loads(TRADE_LOG.read_text())
    return {'trades': [], 'daily': {}}

def save_log(data):
    TRADE_LOG.parent.mkdir(parents=True, exist_ok=True)
    TRADE_LOG.write_text(json.dumps(data, indent=2))

def record_trade(direction, pair, entry, sl, tp, volume=0.01):
    """Registra trade enviado ao MT5."""
    data = load_log()
    trade = {
        'id': f"T{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'timestamp': datetime.now().isoformat(),
        'pair': pair,
        'direction': direction,
        'entry': entry,
        'sl': sl,
        'tp': tp,
        'volume': volume,
        'status': 'open',
        'exit_price': None,
        'pnl': None
    }
    data['trades'].append(trade)
    save_log(data)
    return trade['id']

def get_mt5_balance():
    """Lê saldo MT5 via OCR do Xvfb."""
    try:
        result = subprocess.run(
            [str(VISION_ENGINE), 'mt5_account'],
            capture_output=True, text=True, timeout=15,
            env={**os.environ, 'DISPLAY': ':99'}
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            ocr_text = data.get('ocr', {}).get('text', '')
            # Extrair números do texto OCR (saldo, equity, etc)
            import re
            numbers = re.findall(r'[\d,]+\\.?\\d*', ocr_text)
            return {'ocr_text': ocr_text, 'numbers': numbers}
    except Exception as e:
        return {'error': str(e)}
    return {'error': 'ocr failed'}

def daily_summary():
    """Resumo diário: WR e P&L."""
    data = load_log()
    today = datetime.now().strftime('%Y-%m-%d')
    
    today_trades = [t for t in data['trades'] 
                    if t['timestamp'].startswith(today) and t['status'] == 'closed']
    
    if not today_trades:
        return None
    
    wins = [t for t in today_trades if t.get('pnl', 0) > 0]
    losses = [t for t in today_trades if t.get('pnl', 0) <= 0]
    
    total_pnl = sum(t.get('pnl', 0) for t in today_trades)
    wr = (len(wins) / len(today_trades) * 100) if today_trades else 0
    
    return {
        'date': today,
        'total_trades': len(today_trades),
        'wins': len(wins),
        'losses': len(losses),
        'wr': round(wr, 1),
        'pnl': round(total_pnl, 2),
        'pairs': list(set(t['pair'] for t in today_trades))
    }

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'summary'
    
    if cmd == 'record':
        # Uso: trade_tracker.py record BUY GBP/USD 1.26250 1.26200 1.26400
        direction = sys.argv[2]
        pair = sys.argv[3]
        entry = float(sys.argv[4])
        sl = float(sys.argv[5])
        tp = float(sys.argv[6])
        tid = record_trade(direction, pair, entry, sl, tp)
        print(json.dumps({'trade_id': tid, 'status': 'recorded'}))
    
    elif cmd == 'balance':
        print(json.dumps(get_mt5_balance()))
    
    elif cmd == 'summary':
        s = daily_summary()
        if s:
            print(f"📊 {s['date']} | WR={s['wr']}% | P&L=${s['pnl']} | {s['wins']}W/{s['losses']}L")
        else:
            print("")
    
    elif cmd == 'list_open':
        data = load_log()
        open_trades = [t for t in data['trades'] if t['status'] == 'open']
        for t in open_trades:
            print(f"  {t['id']} {t['pair']} {t['direction']} entry={t['entry']:.5f}")
