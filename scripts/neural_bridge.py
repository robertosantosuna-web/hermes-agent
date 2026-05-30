#!/usr/bin/env python3
"""
BRIDGE — Comunicação entre Hermes Agent e Agente Neural.
Usado pelo Hermes para enviar/receber mensagens do agente neural.
"""
import json, sys, os
from pathlib import Path
from datetime import datetime, timezone

NEURAL_HOME = Path.home() / '.hermes' / 'neural'
BRIDGE_INBOX = NEURAL_HOME / 'bridge_inbox.json'   # Hermes lê daqui (neural→hermes)
BRIDGE_OUTBOX = NEURAL_HOME / 'bridge_outbox.json'  # Hermes escreve aqui (hermes→neural)

def load(path):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except:
        pass
    return []

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))

def cmd_send(task_desc: str, priority: str = 'medium', context: dict = None):
    """Envia tarefa para o agente neural."""
    outbox = load(BRIDGE_OUTBOX)
    outbox.append({
        'type': 'task',
        'content': task_desc,
        'priority': priority,
        'context': context or {},
        'ts': datetime.now(timezone.utc).isoformat(),
        'direction': 'hermes->neural'
    })
    save(BRIDGE_OUTBOX, outbox[-50:])
    print(f"✓ Task sent to Neural Agent: {task_desc[:80]}")

def cmd_read():
    """Lê mensagens do agente neural."""
    inbox = load(BRIDGE_INBOX)
    unread = [m for m in inbox if m.get('direction') == 'neural->hermes']
    if unread:
        for msg in unread:
            print(f"[{msg.get('type')}] {msg.get('content', '')[:200]}")
        # Marca como lidas
        remaining = [m for m in inbox if m.get('direction') != 'neural->hermes']
        save(BRIDGE_INBOX, remaining)
    else:
        print("📭 Nenhuma mensagem do Agente Neural")

def cmd_status():
    """Status rápido."""
    inbox = load(BRIDGE_INBOX)
    outbox = load(BRIDGE_OUTBOX)
    neural_msgs = [m for m in inbox if m.get('direction') == 'neural->hermes']
    hermes_msgs = [m for m in outbox if m.get('direction') == 'hermes->neural']
    print(f"🧠 Agente Neural Bridge")
    print(f"   Mensagens Neural→Hermes: {len(neural_msgs)}")
    print(f"   Mensagens Hermes→Neural: {len(hermes_msgs)}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: bridge.py send <descricao> [priority] | read | status")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == 'send':
        desc = sys.argv[2] if len(sys.argv) > 2 else ''
        pri = sys.argv[3] if len(sys.argv) > 3 else 'medium'
        cmd_send(desc, pri)
    elif cmd == 'read':
        cmd_read()
    elif cmd == 'status':
        cmd_status()
    else:
        print(f"Comando desconhecido: {cmd}")
