#!/usr/bin/env python3
"""
Motor Local de Monitoramento — ENTIDADE
Verifica email + plataformas a cada 5 min.
Só acorda o agente quando há ação pendente.
Economiza tokens evitando polling desnecessário.
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
    "check_interval_minutes": 5,
    "state_file": os.path.expanduser("~/.hermes/monitor/state.json"),
    "alert_file": os.path.expanduser("~/.hermes/monitor/alerts.json"),
}

# Plataformas monitoradas via email
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

def decode_str(s):
    """Decode email header string"""
    if s is None:
        return ""
    parts = decode_header(s)
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or 'utf-8', errors='replace'))
        else:
            result.append(str(part))
    return ' '.join(result)

def check_email():
    """Check Gmail for new freelancing emails since last check"""
    try:
        mail = imaplib.IMAP4_SSL(CONFIG["imap_server"], CONFIG["imap_port"])
        mail.login(CONFIG["email"], CONFIG["app_password"])
        mail.select('INBOX')
        
        # Load last check time
        state = load_state()
        last_check = state.get("last_email_check", 
                               (datetime.now() - timedelta(minutes=10)).isoformat())
        
        alerts = []
        
        # Search for emails from platforms since last check
        for platform_name, config in PLATFORMS.items():
            _, ids = mail.search(None, 'FROM', config["from"])
            if not ids[0]:
                continue
            
            msg_ids = ids[0].split()
            # Only check the last 5 emails per platform
            for msg_id in msg_ids[-5:]:
                _, msg_data = mail.fetch(msg_id, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])
                
                date_str = msg.get('Date', '')
                subject = decode_str(msg['Subject'])
                
                # Parse email date
                try:
                    from email.utils import parsedate_to_datetime
                    email_date = parsedate_to_datetime(date_str)
                    email_date_str = email_date.isoformat()
                except:
                    email_date_str = date_str
                
                # Skip if already processed
                msg_key = f"{platform_name}_{msg_id.decode()}"
                if msg_key in state.get("processed_emails", []):
                    continue
                
                # Check patterns
                for alert_type, pattern in config["patterns"].items():
                    match = re.search(pattern, subject, re.IGNORECASE)
                    if match:
                        alert = {
                            "platform": platform_name,
                            "type": alert_type,
                            "subject": subject,
                            "date": email_date_str,
                            "match": match.group(0) if match.groups() else subject,
                            "timestamp": datetime.now().isoformat(),
                        }
                        alerts.append(alert)
                
                # Mark as processed
                if "processed_emails" not in state:
                    state["processed_emails"] = []
                state["processed_emails"].append(msg_key)
                # Keep only last 500
                state["processed_emails"] = state["processed_emails"][-500:]
        
        mail.logout()
        
        # Update state
        state["last_email_check"] = datetime.now().isoformat()
        
        return alerts, state
        
    except Exception as e:
        print(f"Email check error: {e}", file=sys.stderr)
        return [], load_state()

def load_state():
    """Load monitor state"""
    path = Path(CONFIG["state_file"])
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            pass
    return {"processed_emails": [], "last_email_check": None}

def save_state(state):
    """Save monitor state"""
    path = Path(CONFIG["state_file"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))

def save_alerts(alerts):
    """Save alerts to trigger agent"""
    if not alerts:
        return
    
    path = Path(CONFIG["alert_file"])
    path.parent.mkdir(parents=True, exist_ok=True)
    
    existing = []
    if path.exists():
        try:
            existing = json.loads(path.read_text())
        except:
            pass
    
    existing.extend(alerts)
    # Keep only last 50
    existing = existing[-50:]
    path.write_text(json.dumps(existing, indent=2, ensure_ascii=False))

def should_wake_agent(alerts):
    """Determine if agent should be woken up"""
    if not alerts:
        return False
    
    wake_types = [
        "nova_mensagem",      # Client message - urgent!
        "proposta_aceita",    # You got hired!
        "awarded",            # You got the project!
        "pagamento",          # Money received!
        "novo_pedido",        # New order!
    ]
    
    for alert in alerts:
        if alert["type"] in wake_types:
            return True
        # Also wake for new projects with specific keywords
        if alert["type"] == "novo_projeto":
            subject = alert.get("subject", "").lower()
            high_value = any(kw in subject for kw in 
                ["revisão", "correção", "formatação", "abnt", "tcc", 
                 "python", "automação", "scraping", "excel", "planilha",
                 "tradução", "transcrição", "digitação", "currículo"])
            if high_value:
                return True
    
    return False

def main():
    alerts, state = check_email()
    
    if alerts:
        save_alerts(alerts)
        print(f"ALERTAS: {len(alerts)} novos")
        for a in alerts:
            print(f"  [{a['platform']}] {a['type']}: {a['subject'][:80]}")
        
        if should_wake_agent(alerts):
            # Write wake signal
            wake_file = Path(CONFIG["state_file"]).parent / "wake.txt"
            wake_file.write_text(f"WAKE:{datetime.now().isoformat()}:{len(alerts)} alerts")
            print(">>> ACORDAR AGENTE <<<")
        else:
            print("Alertas baixa prioridade — agente continua dormindo")
    else:
        print("Nada novo")
    
    save_state(state)

if __name__ == "__main__":
    main()
