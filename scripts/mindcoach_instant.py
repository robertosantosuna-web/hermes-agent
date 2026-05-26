#!/usr/bin/env python3
"""
MindCoach Instant Chat Responder — Monitora inbox e responde IMEDIATAMENTE.
Usa inotify para detectar novas mensagens no inbox local.
"""
import json, os, sys, time, subprocess
from pathlib import Path

INBOX_FILE = Path.home() / '.hermes' / 'mindcoach_chat_inbox.json'
STATE_FILE = Path.home() / '.hermes' / 'mc_instant_state.json'
REST_URL = 'https://mindcoach-541659260074.us-central1.run.app/api/chat'
LAST_SIZE = 0

def get_state():
    try:
        return json.loads(STATE_FILE.read_text())
    except:
        return {"processed_timestamps": []}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state))

def call_agent(msg_text):
    """Chama o agent para responder — via arquivo de trigger."""
    trigger = Path.home() / '.hermes' / 'mc_instant_trigger.json'
    trigger.write_text(json.dumps({
        "texto": msg_text,
        "timestamp": time.time(),
        "pending": True
    }))

def post_rest(text):
    """Posta resposta na REST API."""
    try:
        import urllib.request
        data = json.dumps({"from": "assistant", "text": text}).encode()
        req = urllib.request.Request(REST_URL, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
        return True
    except:
        return False

def send_bridge(text):
    """Envia resposta via WebSocket bridge."""
    try:
        sys.path.insert(0, str(Path.home() / '.hermes' / 'scripts'))
        from mindcoach_bridge import send_command
        send_command({'type': 'chat', 'mensagens': [{'role': 'hermes', 'texto': text}]})
        return True
    except:
        return False

def process_inbox():
    """Processa mensagens não lidas."""
    if not INBOX_FILE.exists():
        return
    
    msgs = json.loads(INBOX_FILE.read_text())
    state = get_state()
    processed = set(state.get("processed_timestamps", []))
    
    for m in msgs:
        ts = m.get("timestamp")
        if ts not in processed and not m.get("lido"):
            texto = m.get("texto", "")
            print(f"[INSTANT] Nova mensagem: {texto[:60]}")
            
            # Trigger agent
            call_agent(texto)
            
            # Marcar como processado
            processed.add(ts)
            m["lido"] = True
    
    INBOX_FILE.write_text(json.dumps(msgs))
    save_state({"processed_timestamps": list(processed)[-100:]})

def watch():
    """Monitora o arquivo inbox por mudanças (polling 500ms)."""
    global LAST_SIZE
    print("[INSTANT] Watcher iniciado — monitorando inbox...", flush=True)
    
    while True:
        try:
            if INBOX_FILE.exists():
                size = INBOX_FILE.stat().st_size
                if size != LAST_SIZE:
                    LAST_SIZE = size
                    process_inbox()
        except Exception as e:
            print(f"[INSTANT] Erro: {e}", flush=True)
        time.sleep(0.5)

if __name__ == '__main__':
    watch()
