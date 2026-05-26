#!/usr/bin/env python3
"""
Motor Local de Monitoramento — ENTIDADE
Verifica email + plataformas a cada 5 min.
Só acorda o agente quando há ação pendente.
Economiza tokens evitando polling desnecessário.

Uso: configurado como cron job no_agent
     hermes cronjob create --name "Motor Monitor" --schedule "every 5m" --script monitor.py --no_agent
"""
import imaplib
import email
import re
import json
import os
import sys
from email.header import decode_header
from datetime import datetime, timedelta
from pathlib import Path

CONFIG = {
    "email": "robertosantos.una@gmail.com",
    "app_password": "exnlrvfswckioces",
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "state_file": os.path.expanduser("~/.hermes/monitor/state.json"),
    "alert_file": os.path.expanduser("~/.hermes/monitor/alerts.json"),
}

PLATFORMS = {
    "99freelas": {
        "from": "99freelas",
        "patterns": {
            "novo_projeto": r"Novo Projeto: (.+)",
            "nova_mensagem": r"Nova mensagem de (.+) no projeto (.+)",
            "proposta_aceita": r"(?:proposta aceita|Parabéns|escolhido)",
            "pagamento": r"(?:pagamento|transferência|recebeu)",
        }
    },
    "freelancer": {
        "from": "freelancer",
        "patterns": {
            "novo_projeto": r"(?:new project|novo projeto)",
            "nova_mensagem": r"(?:new message|nova mensagem)",
            "awarded": r"(?:awarded|concedido|aceito)",
        }
    },
    "fiverr": {
        "from": "fiverr",
        "patterns": {
            "nova_mensagem": r"(?:new message|nova mensagem|inbox)",
            "novo_pedido": r"(?:new order|novo pedido|congratulations)",
        }
    },
    "workana": {
        "from": "workana",
        "patterns": {
            "novo_projeto": r"(?:novo projeto|new project)",
            "nova_mensagem": r"(?:nova mensagem|new message)",
        }
    },
}

WAKE_TYPES = [
    "nova_mensagem",      # Client message - urgent!
    "proposta_aceita",    # You got hired!
    "awarded",            # You got the project!
    "pagamento",          # Money received!
    "novo_pedido",        # New order!
]

def check_email():
    """Check Gmail for new freelancing emails since last check"""
    mail = imaplib.IMAP4_SSL(CONFIG["imap_server"], CONFIG["imap_port"])
    mail.login(CONFIG["email"], CONFIG["app_password"])
    mail.select('INBOX')
    
    state = load_state()
    alerts = []
    
    for platform_name, config in PLATFORMS.items():
        _, ids = mail.search(None, 'FROM', config["from"])
        if not ids[0]:
            continue
        
        msg_ids = ids[0].split()
        for msg_id in msg_ids[-5:]:
            _, msg_data = mail.fetch(msg_id, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            subject = decode_str(msg['Subject'])
            
            msg_key = f"{platform_name}_{msg_id.decode()}"
            if msg_key in state.get("processed_emails", []):
                continue
            
            for alert_type, pattern in config["patterns"].items():
                match = re.search(pattern, subject, re.IGNORECASE)
                if match:
                    alerts.append({
                        "platform": platform_name,
                        "type": alert_type,
                        "subject": subject,
                        "timestamp": datetime.now().isoformat(),
                    })
            
            if "processed_emails" not in state:
                state["processed_emails"] = []
            state["processed_emails"].append(msg_key)
            state["processed_emails"] = state["processed_emails"][-500:]
    
    mail.logout()
    state["last_email_check"] = datetime.now().isoformat()
    return alerts, state

def should_wake(alerts):
    """Only wake agent for high-priority alerts"""
    for a in alerts:
        if a["type"] in WAKE_TYPES:
            return True
        if a["type"] == "novo_projeto":
            subject = a.get("subject", "").lower()
            if any(kw in subject for kw in 
                ["revisão", "correção", "formatação", "abnt", "tcc", 
                 "python", "automação", "scraping", "excel", "planilha",
                 "tradução", "transcrição", "digitação", "currículo"]):
                return True
    return False

def decode_str(s):
    if s is None: return ""
    parts = decode_header(s)
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or 'utf-8', errors='replace'))
        else:
            result.append(str(part))
    return ' '.join(result)

def load_state():
    path = Path(CONFIG["state_file"])
    if path.exists():
        try: return json.loads(path.read_text())
        except: pass
    return {"processed_emails": [], "last_email_check": None}

def save_state(state):
    path = Path(CONFIG["state_file"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))

def main():
    alerts, state = check_email()
    if alerts:
        wake_file = Path(CONFIG["state_file"]).parent / "wake.txt"
        alert_data = json.dumps(alerts, indent=2, ensure_ascii=False)
        
        if should_wake(alerts):
            wake_file.write_text(f"WAKE:{datetime.now().isoformat()}:\n{alert_data}")
            print(f">>> ACORDAR AGENTE: {len(alerts)} alertas <<<")
        else:
            print(f"Alertas baixa prioridade ({len(alerts)}) — agente dorme")
    save_state(state)

if __name__ == "__main__":
    main()
