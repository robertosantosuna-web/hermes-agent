#!/usr/bin/env python3
"""
Gateway Checkpoint Updater
Salva estado atual do agente para recuperação pós-queda.
Roda a cada 5 min via cron (no_agent).
"""
import json
import os
from datetime import datetime, timezone, timedelta

CHECKPOINT = os.path.expanduser("~/.hermes/gateway_checkpoint.json")
CONTEXT_FILE = os.path.expanduser("~/.hermes/agent_context.json")

def load_checkpoint():
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {}

def save_checkpoint(data):
    with open(CHECKPOINT, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    cp = load_checkpoint()
    
    # Atualizar timestamp
    now = datetime.now(timezone(timedelta(hours=-3))).isoformat()
    cp["last_updated"] = now
    cp["version"] = cp.get("version", 1)
    
    # Garantir que preferences e authorizations persistem
    if "preferences" not in cp:
        cp["preferences"] = {
            "language": "português BR",
            "communication": "conciso",
            "autonomy": "máxima"
        }
    
    if "authorizations" not in cp:
        cp["authorizations"] = {
            "confirmed": True,
            "scope": "ações seguras sem violar soberania"
        }
    
    save_checkpoint(cp)
    print(f"checkpoint updated: {now}")

if __name__ == "__main__":
    main()
