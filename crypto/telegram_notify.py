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
    """Notifica trade aberto."""
    emoji = '🟢' if direction == 'BUY' else '🔴'
    msg = f"{emoji} {pair} {direction} @{entry:.4f}\nSL={sl:.4f} TP={tp:.4f}\n💰 ${amount:.2f}"
    send_telegram(msg)

def notify_close(pair, result, pnl, balance):
    """Notifica trade fechado."""
    if result == 'WIN':
        emoji = '✅'
        msg = f"{emoji} {pair} +${pnl:.2f} | 💰 ${balance:.2f}"
    else:
        emoji = '❌'
        msg = f"{emoji} {pair} -${abs(pnl):.2f} | 💰 ${balance:.2f}"
    send_telegram(msg)
