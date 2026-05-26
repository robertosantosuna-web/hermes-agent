#!/usr/bin/env python3
"""
Canal Direto — Agent ↔ Brain Communication
===========================================
Inbox/outbox assíncrono entre Hermes Agent e Cérebro Autônomo.

Arquivos:
  ~/.hermes/brain_inbox.json   → Agent escreve, Brain lê (próximo ciclo)
  ~/.hermes/brain_outbox.json  → Brain escreve, Agent lê
  ~/.hermes/brain_channel.log  → Histórico completo da conversa

Fluxo:
  Agent:  brain send "pergunta"     → inbox.json
  Brain:  (cron lê inbox, processa) → outbox.json  
  Agent:  brain read                → lê resposta

Comandos:
  brain send "mensagem"      → envia para o cérebro
  brain read                 → lê respostas pendentes
  brain log [N]              → últimas N mensagens do histórico
  brain status               → status do canal
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERMES = Path.home() / ".hermes"
INBOX = HERMES / "brain_inbox.json"
OUTBOX = HERMES / "brain_outbox.json"
LOG = HERMES / "brain_channel.log"


def _now():
    return datetime.now(timezone.utc).isoformat()


def _load(path):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            pass
    return {"messages": []}


def _save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _log(direction, content):
    """Append to channel log."""
    entry = f"[{_now()}] {direction}: {content[:500]}\n"
    with open(LOG, "a") as f:
        f.write(entry)


def send(message):
    """Agent → Brain: write message to inbox."""
    inbox = _load(INBOX)
    
    msg = {
        "id": f"agent_{int(datetime.now().timestamp())}",
        "from": "agent",
        "to": "brain",
        "content": message,
        "sent_at": _now(),
        "read": False,
    }
    
    inbox["messages"].append(msg)
    _save(INBOX, inbox)
    _log("AGENT→BRAIN", message)
    
    return {
        "status": "sent",
        "id": msg["id"],
        "pending_total": len([m for m in inbox["messages"] if not m["read"]]),
        "note": "Brain will read on next cycle (1-15 min)"
    }


def read(unread_only=True):
    """Agent ← Brain: read messages from outbox."""
    outbox = _load(OUTBOX)
    
    messages = outbox.get("messages", [])
    if unread_only:
        messages = [m for m in messages if not m.get("read_by_agent", False)]
    
    # Mark as read
    for m in messages:
        m["read_by_agent"] = True
        m["read_at"] = _now()
    _save(OUTBOX, outbox)
    
    return {
        "status": "ok",
        "unread": len(messages),
        "messages": messages,
    }


def mark_processed(msg_ids):
    """Brain marks inbox messages as processed."""
    inbox = _load(INBOX)
    for msg in inbox["messages"]:
        if msg["id"] in msg_ids:
            msg["read"] = True
            msg["processed_at"] = _now()
    _save(INBOX, inbox)
    return {"status": "ok", "processed": len(msg_ids)}


def brain_respond(message, in_reply_to=None):
    """Brain → Agent: write response to outbox. Called by brain scripts."""
    outbox = _load(OUTBOX)
    
    msg = {
        "id": f"brain_{int(datetime.now().timestamp())}",
        "from": "brain",
        "to": "agent",
        "content": message,
        "sent_at": _now(),
        "in_reply_to": in_reply_to,
        "read_by_agent": False,
    }
    
    outbox["messages"].append(msg)
    _save(OUTBOX, outbox)
    _log("BRAIN→AGENT", message)
    
    return {"status": "sent", "id": msg["id"]}


def show_log(n=20):
    """Show last N channel log entries."""
    if not LOG.exists():
        print("📭 No messages yet.")
        return
    
    lines = LOG.read_text().strip().split("\n")
    for line in lines[-n:]:
        print(line)


def status():
    """Show channel status."""
    inbox = _load(INBOX)
    outbox = _load(OUTBOX)
    
    inbox_unread = len([m for m in inbox["messages"] if not m["read"]])
    outbox_unread = len([m for m in outbox["messages"] if not m.get("read_by_agent", False)])
    
    print(f"📡 Canal Direto Agent ↔ Brain")
    print(f"   Inbox:  {len(inbox['messages'])} total, {inbox_unread} não lidos pelo Brain")
    print(f"   Outbox: {len(outbox['messages'])} total, {outbox_unread} não lidos pelo Agent")
    print(f"   Log:    {LOG.stat().st_size if LOG.exists() else 0} bytes")
    
    if outbox_unread > 0:
        print(f"\n   🔔 {outbox_unread} mensagens do Cérebro aguardando!")


# ═══════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        status()
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "send":
        message = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else sys.stdin.read().strip()
        if not message:
            print("❌ No message")
            sys.exit(1)
        result = send(message)
        print(json.dumps(result, indent=2))
    
    elif cmd == "read":
        result = read()
        if result["messages"]:
            for m in result["messages"]:
                print(f"\n🧠 Cérebro [{m['sent_at'][:19]}]:")
                print(f"   {m['content']}")
                if m.get("in_reply_to"):
                    print(f"   (em resposta a: {m['in_reply_to']})")
        else:
            print("📭 Nenhuma mensagem nova do Cérebro.")
    
    elif cmd == "respond":
        # brain_respond: usado pelo cérebro para responder
        # Uso: brain respond "mensagem" [--reply-to ID]
        args = sys.argv[2:]
        reply_to = None
        message_parts = []
        for i, a in enumerate(args):
            if a == "--reply-to" and i + 1 < len(args):
                reply_to = args[i + 1]
                break
            message_parts.append(a)
        message = " ".join(message_parts)
        result = brain_respond(message, reply_to)
        print(json.dumps(result, indent=2))
    
    elif cmd == "mark-read":
        # mark_processed: brain marca mensagens como lidas
        ids = sys.argv[2:]
        result = mark_processed(ids)
        print(json.dumps(result, indent=2))
    
    elif cmd == "log":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        show_log(n)
    
    elif cmd == "status":
        status()
    
    else:
        print(f"Unknown: {cmd}")
        print("Commands: send, read, log, status")
