#!/usr/bin/env python3
"""
MONITOR CONSUMER — Lê alertas do monitor.py e entrega ao Roberto.
Fecha o gap: monitor.py → [Motor Central PAUSADO] → NUNCA ENTREGUE.
Agora: monitor.py → monitor_consumer.py → Telegram IMEDIATO.

Roda a cada 5 minutos (mesmo schedule do monitor.py).
Zero tokens.
"""
import json, os, sys, subprocess
from pathlib import Path
from datetime import datetime

H = Path.home() / '.hermes'
ALERTS_FILE = H / 'monitor' / 'alerts.json'
STATE_FILE = H / 'monitor' / 'consumer_state.json'

def load(path):
    if path.exists():
        try: return json.loads(path.read_text())
        except: pass
    return None

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))

def send_telegram(msg):
    """Envia mensagem para o Telegram via send_message tool (cron deliver=origin)."""
    # Como script no_agent, stdout vai para o cron output.
    # Se configurado com deliver=origin, vai pro Telegram automaticamente.
    print(msg)
    return True

def main():
    alerts = load(ALERTS_FILE)
    state = load(STATE_FILE) or {'last_notified': None, 'notified_ids': []}
    
    if not alerts:
        return  # Sem alertas novos
    # alerts pode ser list (array JSON) ou dict com chave 'alerts'
    alert_list = alerts if isinstance(alerts, list) else alerts.get('alerts', [])
    if not alert_list:
        return
    
    new_alerts = []
    for alert in alert_list:
        alert_id = alert.get('id', str(alert.get('timestamp', '')))
        if alert_id not in state['notified_ids']:
            new_alerts.append(alert)
    
    if not new_alerts:
        return
    
    # Compilar mensagem
    lines = [f"📬 **Novos alertas de freelas** ({len(new_alerts)})"]
    for a in new_alerts[:5]:  # Máx 5 por vez
        source = a.get('source', '?')
        title = a.get('title', a.get('subject', 'Sem título'))
        url = a.get('url', '')
        lines.append(f"• **{source}**: {title}")
        if url:
            lines.append(f"  {url}")
    
    msg = '\n'.join(lines)
    send_telegram(msg)
    
    # Atualizar estado
    for a in new_alerts:
        state['notified_ids'].append(a.get('id', str(a.get('timestamp', ''))))
    state['last_notified'] = datetime.now().isoformat()
    # Manter só últimos 50 IDs
    state['notified_ids'] = state['notified_ids'][-50:]
    save(STATE_FILE, state)

if __name__ == '__main__':
    main()
