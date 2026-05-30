#!/usr/bin/env python3
"""
Trade Notifier — Envia confirmações de ordens abertas/fechadas via Telegram.
Uso:
  python3 trade_notifier.py open EURUSD BUY 1.1625 1.1615 1.1655 FVG+CRT KZ
  python3 trade_notifier.py close EURUSD BUY 1.1625 1.1640 +15.0p WIN FVG+CRT
  python3 trade_notifier.py summary "3 ordens abertas hoje, PnL: +25p"
"""

import json, os, sys, urllib.request
from datetime import datetime
from pathlib import Path

# ══════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════
CONFIG_FILE = Path.home() / '.hermes' / 'config.yaml'
ENV_FILE = Path.home() / '.hermes' / '.env'

def load_token():
    """Carrega o token do Telegram do .env ou config."""
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().split('\n'):
            if 'TELEGRAM_BOT_TOKEN' in line and '=' in line and not line.strip().startswith('#'):
                val = line.split('=', 1)[1].strip().strip('"').strip("'")
                if val and val != '***':
                    return val
    
    # Fallback: ler do config.yaml
    if CONFIG_FILE.exists():
        import yaml
        try:
            cfg = yaml.safe_load(CONFIG_FILE.read_text())
            token = cfg.get('telegram', {}).get('bot_token', '')
            if token:
                return token
        except:
            pass
    
    return None

def get_chat_id():
    """Obtém o chat_id do .env."""
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().split('\n'):
            if 'TELEGRAM_HOME_CHANNEL' in line and '=' in line and not line.strip().startswith('#'):
                val = line.split('=', 1)[1].strip().strip('"').strip("'")
                if val and val != '***' and val.isdigit():
                    return val
    return '845735429'  # Default: Home channel ID do Roberto

# ══════════════════════════════════════════
# EMOJIS POR TIPO
# ══════════════════════════════════════════
EMOJI = {
    'BUY': '🟢',
    'SELL': '🔴',
    'WIN': '✅',
    'LOSS': '❌',
    'open': '📈',
    'close': '📉',
    'FVG+CRT': '🔍',
    'SMC Fractal': '🧠',
    'S/R+FVG': '📐',
}

def send_telegram(message: str):
    """Envia mensagem via Telegram Bot API."""
    token = load_token()
    chat_id = get_chat_id()
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN não configurado")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = json.dumps({
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_notification': False,
        }).encode()
        req = urllib.request.Request(url, data=data,
            headers={'Content-Type': 'application/json'})
        resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return resp.get('ok', False)
    except Exception as e:
        print(f"❌ Erro Telegram: {e}")
        return False

# ══════════════════════════════════════════
# FORMATADORES
# ══════════════════════════════════════════

def format_open(pair, direction, entry, sl, tp, strategy, mode):
    """Formata notificação de ordem ABERTA."""
    e = EMOJI.get(direction, '')
    s = EMOJI.get(strategy, '')
    sl_pips = abs(entry - sl) / (0.01 if 'JPY' in pair else 0.0001)
    tp_pips = abs(tp - entry) / (0.01 if 'JPY' in pair else 0.0001)
    
    return f"""{e} *ORDEM ABERTA* {s}
┌ *{pair}* | {direction} | {strategy}
├ Entrada: `{entry:.5f}`
├ SL: `{sl:.5f}` ({sl_pips:.1f}p)
├ TP: `{tp:.5f}` ({tp_pips:.1f}p)
├ Modo: {mode}
└ {datetime.now().strftime('%H:%M')}"""

def format_close(pair, direction, entry, exit_price, pnl, result, strategy):
    """Formata notificação de ordem FECHADA."""
    e = EMOJI.get(result, '')
    s = EMOJI.get(strategy, '')
    r_emoji = EMOJI.get(result, '❓')
    
    return f"""{r_emoji} *ORDEM FECHADA* {s}
┌ *{pair}* | {direction} | {strategy}
├ Entrada: `{entry:.5f}`
├ Saída: `{exit_price:.5f}`
├ P&L: *{pnl}*
└ {datetime.now().strftime('%H:%M')}"""

def format_summary(text):
    """Formata resumo diário."""
    return f"""📊 *RESUMO DE TRADES*
{text}
🕐 {datetime.now().strftime('%d/%m %H:%M')}"""

# ══════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("Uso: trade_notifier.py <open|close|summary> [args...]")
        print("  open: pair direction entry sl tp strategy mode")
        print("  close: pair direction entry exit_price pnl result strategy")
        print("  summary: 'texto do resumo'")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == 'open':
        if len(sys.argv) < 8:
            print("❌ open requer: pair direction entry sl tp strategy [mode]")
            sys.exit(1)
        pair = sys.argv[2]
        direction = sys.argv[3]
        entry = float(sys.argv[4])
        sl = float(sys.argv[5])
        tp = float(sys.argv[6])
        strategy = sys.argv[7]
        mode = sys.argv[8] if len(sys.argv) > 8 else '24h'
        
        msg = format_open(pair, direction, entry, sl, tp, strategy, mode)
        send_telegram(msg)
        print(msg)
    
    elif action == 'close':
        if len(sys.argv) < 8:
            print("❌ close requer: pair direction entry exit_price pnl result strategy")
            sys.exit(1)
        pair = sys.argv[2]
        direction = sys.argv[3]
        entry = float(sys.argv[4])
        exit_price = float(sys.argv[5])
        pnl = sys.argv[6]
        result = sys.argv[7]
        strategy = sys.argv[8] if len(sys.argv) > 8 else 'FVG+CRT'
        
        msg = format_close(pair, direction, entry, exit_price, pnl, result, strategy)
        send_telegram(msg)
        print(msg)
    
    elif action == 'summary':
        text = ' '.join(sys.argv[2:])
        msg = format_summary(text)
        send_telegram(msg)
        print(msg)
    
    elif action == 'test':
        msg = f"🧪 *Trade Notifier — Teste*\n✅ Funcionando!\n🕐 {datetime.now().strftime('%H:%M')}"
        ok = send_telegram(msg)
        print(f"{'✅' if ok else '❌'} Teste {'enviado' if ok else 'FALHOU'}")

if __name__ == '__main__':
    main()
