#!/usr/bin/env python3
"""
Brain Telegram Bridge — Lightweight Poller
============================================
Monitora chat dedicado do Telegram e roteta para Brain Gateway.
Compatível com o gateway principal (usa getUpdates com offset separado).

Setup:
  1. Criar grupo "🧠 Cérebro" no Telegram
  2. Adicionar o bot ao grupo
  3. Mandar uma msg qualquer no grupo
  4. Rodar: python3 brain_telegram.py --discover
     → Vai mostrar o chat_id do grupo
  5. Configurar: python3 brain_telegram.py --chat-id -100XXXXXX
  6. Todas msgs nesse chat → Cérebro (sem Agent!)

Requer: requests (ou urllib built-in)
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

HERMES = Path.home() / ".hermes"
GATEWAY_INBOX = HERMES / "brain_gateway_inbox.json"
STATE_FILE = HERMES / "brain_telegram_state.json"

# Load token
env_file = HERMES / ".env"
BOT_TOKEN = None
if env_file.exists():
    for line in env_file.read_text().split("\n"):
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            BOT_TOKEN = line.split("=", 1)[1].strip()
            break

if not BOT_TOKEN:
    print("❌ BOT_TOKEN not found")
    sys.exit(1)

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def _now():
    return datetime.now(timezone.utc).isoformat()


def api(method, data=None):
    """Call Telegram API."""
    url = f"{BASE_URL}/{method}"
    if data:
        req = urllib.request.Request(url, data=json.dumps(data).encode(),
                                     headers={"Content-Type": "application/json"})
    else:
        req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"ok": False, "error": str(e)}


def discover_chats():
    """List recent chats to find the brain group ID."""
    # Get recent updates
    result = api("getUpdates", {"limit": 20, "allowed_updates": ["message"]})
    
    if not result.get("ok"):
        print(f"❌ API error: {result.get('description', result)}")
        return
    
    chats = {}
    for update in result.get("result", []):
        msg = update.get("message", {})
        chat = msg.get("chat", {})
        cid = str(chat.get("id", ""))
        ctype = chat.get("type", "?")
        cname = chat.get("title", chat.get("first_name", "?"))
        text = msg.get("text", "")[:50]
        
        if cid not in chats:
            chats[cid] = {"type": ctype, "name": cname, "last_msg": text}
    
    print("📡 Recent chats:")
    for cid, info in chats.items():
        print(f"  {info['type']:10s} {cid:20s} {info['name'][:30]}")
        print(f"                     \"{info['last_msg']}\"")
    
    print()
    print("Use: python3 brain_telegram.py --chat-id <ID>")


def get_updates(offset=None, timeout=30):
    """Get updates with offset (non-blocking for cron mode)."""
    params = {"timeout": timeout, "allowed_updates": ["message"]}
    if offset:
        params["offset"] = offset
    return api("getUpdates", params)


def send_message(chat_id, text):
    """Send message via Telegram."""
    return api("sendMessage", {
        "chat_id": chat_id,
        "text": text[:4000],
        "parse_mode": "Markdown"
    })


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {"last_update_id": 0, "processed_ids": []}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def process_updates(chat_id=None):
    """Fetch updates, filter by chat, route to brain gateway."""
    state = load_state()
    
    result = get_updates(offset=state["last_update_id"] + 1, timeout=5)
    
    if not result.get("ok"):
        return {"status": "error", "message": result.get("description", "?")}
    
    updates = result.get("result", [])
    processed = 0
    
    for update in updates:
        update_id = update.get("update_id", 0)
        state["last_update_id"] = max(state["last_update_id"], update_id)
        
        msg = update.get("message", {})
        if not msg or not msg.get("text"):
            continue
        
        msg_chat_id = str(msg.get("chat", {}).get("id", ""))
        msg_id = msg.get("message_id")
        text = msg.get("text", "")
        user_name = msg.get("from", {}).get("first_name", "User")
        
        # Skip if already processed
        dedup_key = f"{msg_chat_id}:{msg_id}"
        if dedup_key in state["processed_ids"]:
            continue
        
        # Filter by chat_id if configured
        if chat_id and msg_chat_id != str(chat_id):
            continue
        
        # Skip commands meant for main agent
        clean_text = text
        if text.startswith("/brain"):
            clean_text = text[6:].strip()
        elif text.startswith("/"):
            continue  # Other commands go to main agent
        
        if not clean_text:
            continue
        
        # Route to brain gateway inbox
        inbox = {"messages": []}
        if GATEWAY_INBOX.exists():
            try:
                inbox = json.loads(GATEWAY_INBOX.read_text())
            except:
                pass
        
        inbox["messages"].append({
            "id": f"tg_{msg_id}",
            "from": f"telegram:{user_name}",
            "chat_id": msg_chat_id,
            "content": clean_text,
            "sent_at": _now(),
            "read": False,
        })
        
        GATEWAY_INBOX.parent.mkdir(parents=True, exist_ok=True)
        GATEWAY_INBOX.write_text(json.dumps(inbox, indent=2, ensure_ascii=False))
        
        state["processed_ids"].append(dedup_key)
        state["processed_ids"] = state["processed_ids"][-200:]  # Keep last 200
        
        processed += 1
    
    save_state(state)
    
    # Deliver pending brain responses
    delivered = deliver_responses(chat_id)
    
    return {"status": "ok", "processed": processed, "delivered": delivered}


def deliver_responses(chat_id=None):
    """Check brain outbox and deliver to Telegram."""
    outbox_file = HERMES / "brain_outbox.json"
    if not outbox_file.exists():
        return 0
    
    try:
        outbox = json.loads(outbox_file.read_text())
        messages = outbox.get("messages", [])
        delivered = 0
        
        for msg in messages:
            if msg.get("delivered_to_telegram"):
                continue
            
            target = chat_id or "845735429"
            content = msg.get("content", "")
            
            # Send response
            send_message(target, f"🧠 *Cérebro:*\n{content[:3500]}")
            
            msg["delivered_to_telegram"] = True
            msg["delivered_at"] = _now()
            delivered += 1
        
        if delivered > 0:
            outbox_file.write_text(json.dumps(outbox, indent=2, ensure_ascii=False))
        
        return delivered
    except:
        return 0


def run_daemon(chat_id, interval=10):
    """Run as persistent daemon polling every N seconds."""
    print(f"🧠 Brain Telegram Bridge — Daemon")
    print(f"   Chat ID: {chat_id or 'ALL (global)'}")
    print(f"   Interval: {interval}s")
    print(f"   Gateway: brain_gateway_inbox.json")
    print()
    
    while True:
        try:
            result = process_updates(chat_id=chat_id)
            if result.get("processed", 0) > 0:
                print(f"[{_now()[:19]}] Processed: {result['processed']} msgs, Delivered: {result.get('delivered', 0)}")
        except Exception as e:
            print(f"[{_now()[:19]}] Error: {e}")
        
        time.sleep(interval)


# ═══════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Brain Telegram Bridge")
    p.add_argument("--discover", action="store_true", help="Discover chat IDs")
    p.add_argument("--chat-id", help="Telegram chat ID for brain channel")
    p.add_argument("--interval", type=int, default=10, help="Poll interval in seconds (daemon mode)")
    p.add_argument("--once", action="store_true", help="Run once and exit (for cron)")
    args = p.parse_args()
    
    if args.discover:
        discover_chats()
    elif args.once:
        result = process_updates(chat_id=args.chat_id)
        print(json.dumps(result, indent=2))
    else:
        if not args.chat_id:
            print("⚠️  No --chat-id specified. Use --discover to find it.")
            print("   Running in discovery mode...")
            discover_chats()
            sys.exit(1)
        run_daemon(args.chat_id, args.interval)
