#!/usr/bin/env python3
"""
NOTIFICADOR TELEGRAM — Envia mensagens enxutas
Usa token do bot configurado no Hermes
"""
import json, requests
from pathlib import Path

# Config do Hermes para pegar token do Telegram
CONFIG_PATH = Path.home() / '.hermes' / 'config.yaml'

def get_telegram_token():
    """Extrai token do Telegram do config.yaml."""
    try:
        import yaml
        with open(CONFIG_PATH) as f:
            cfg = yaml.safe_load(f)
        telegram = cfg.get('gateway', {}).get('messaging', {}).get('telegram', {})
        return telegram.get('bot_token'), telegram.get('chat_id')
    except:
        return None, None

def send_telegram(message):
    """Envia mensagem via API do Telegram."""
    token, chat_id = get_telegram_token()
    if not token or not chat_id:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        r = requests.post(url, data=data, timeout=10)
        return r.status_code == 200
    except:
        return False

def notify_open(pair, direction, entry, sl, tp, amount):
    """Silencioso durante trade — só resultado final."""
    pass

def notify_close(pair, result, pnl, balance):
    """Notifica resultado final do trade."""
    if result == 'WIN':
        emoji = '✅'
        msg = f"{emoji} {pair} +${pnl:.2f} | 💰 ${balance:.2f}"
    else:
        emoji = '❌'
        msg = f"{emoji} {pair} -${abs(pnl):.2f} | 💰 ${balance:.2f}"
    send_telegram(msg)

def notify_status():
    """P&L + margin — sob demanda."""
    import sys
    sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
    from binance_trader import BinanceTrader
    
    try:
        trader = BinanceTrader(testnet=False)
        acct = trader._request('GET', '/sapi/v1/margin/account', signed=True)
        margin_level = float(acct.get('marginLevel', 999))
        spot = trader.get_balance('USDT')
        margin = trader._get_margin_balance('USDT')
        total = spot + margin
        
        trades_file = Path.home() / '.hermes' / 'crypto' / 'open_trades.json'
        trades = []
        if trades_file.exists():
            with open(trades_file) as f:
                trades = json.load(f)
        
        lines = [f"📊 CRYPTO STATUS"]
        if not trades:
            lines.append("😴 Sem posições abertas")
        else:
            for t in trades:
                pair = t['pair']
                symbol = pair.replace('USD', 'USDT')
                direction = t['direction']
                entry = t['entry']
                try:
                    current = trader.get_price(symbol)
                except:
                    current = entry
                if direction == 'BUY':
                    pnl = current - entry
                    pnl_pct = (current / entry - 1) * 100
                else:
                    pnl = entry - current
                    pnl_pct = (1 - current / entry) * 100
                emoji = '🟢' if pnl >= 0 else '🔴'
                lines.append(f"{emoji} {pair} {direction} | P&L: {pnl:+.2f} ({pnl_pct:+.2f}%) | ${current:,.2f}")
        lines.append(f"💰 ${total:.2f} | ML: {margin_level:.1f}x")
        send_telegram('\n'.join(lines))
        return True
    except Exception as e:
        return False
