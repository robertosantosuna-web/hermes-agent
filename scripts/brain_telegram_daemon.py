#!/usr/bin/env python3
"""
Brain Telegram Daemon — Bot dedicado ao Cérebro
=================================================
Bot Telegram separado (sem conflito com gateway principal).
Mensagens recebidas → processamento IMEDIATO → resposta no Telegram.

Setup:
  1. Criar bot no @BotFather
  2. Adicionar TELEGRAM_BRAIN_BOT_TOKEN no ~/.hermes/.env
  3. systemctl --user enable --now hermes-brain-telegram
"""

import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

HERMES = Path.home() / ".hermes"
GATEWAY_INBOX = HERMES / "brain_gateway_inbox.json"
OUTBOX_FILE = HERMES / "brain_outbox.json"
STATE_FILE = HERMES / "brain_telegram_state.json"

# Import brain processing logic DIRECTLY (immediate, no cron wait)
sys.path.insert(0, str(HERMES / "scripts"))
from brain_gateway import _brain_process, _load_knowledge

# ═══════════════ CONFIG ═══════════════

env_file = HERMES / ".env"
BOT_TOKEN = os.environ.get("TELEGRAM_BRAIN_BOT_TOKEN")

if not BOT_TOKEN and env_file.exists():
    for line in env_file.read_text().split("\n"):
        if line.startswith("TELEGRAM_BRAIN_BOT_TOKEN="):
            BOT_TOKEN = line.split("=", 1)[1].strip()
            break

if not BOT_TOKEN:
    print("❌ TELEGRAM_BRAIN_BOT_TOKEN not set.")
    print("   1. Create bot at @BotFather")
    print("   2. Add token to ~/.hermes/.env: TELEGRAM_BRAIN_BOT_TOKEN=xxx")
    sys.exit(1)

BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


def _now():
    return datetime.now(timezone.utc).isoformat()


def api(method, data=None):
    url = f"{BASE}/{method}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode() if data else None,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"ok": False, "error": str(e)}


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {"last_update_id": 0}


def save_state(s):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(s))


def route_to_brain(msg_id, chat_id, user_name, text):
    """Write message to brain gateway inbox."""
    inbox = {"messages": []}
    if GATEWAY_INBOX.exists():
        try:
            inbox = json.loads(GATEWAY_INBOX.read_text())
        except:
            pass
    
    inbox["messages"].append({
        "id": f"tg_{msg_id}",
        "from": f"telegram:{user_name}",
        "chat_id": str(chat_id),
        "content": text,
        "sent_at": _now(),
        "read": False,
    })
    
    GATEWAY_INBOX.parent.mkdir(parents=True, exist_ok=True)
    GATEWAY_INBOX.write_text(json.dumps(inbox, indent=2, ensure_ascii=False))


def deliver_responses(bot_username="HermesBrainBot"):
    """Check brain outbox and send responses via Telegram."""
    if not OUTBOX_FILE.exists():
        return 0
    
    try:
        outbox = json.loads(OUTBOX_FILE.read_text())
        delivered = 0
        
        for msg in outbox.get("messages", []):
            if msg.get("delivered_to_telegram"):
                continue
            
            # Get chat_id from original message
            chat_id = None
            inbox = json.loads(GATEWAY_INBOX.read_text()) if GATEWAY_INBOX.exists() else {}
            for m in inbox.get("messages", []):
                if m.get("id") == msg.get("in_reply_to", ""):
                    chat_id = m.get("chat_id")
                    break
            
            if not chat_id:
                chat_id = os.environ.get("BRAIN_CHAT_ID", None)
            
            if chat_id:
                text = f"🧠 {msg['content'][:3500]}"
                api("sendMessage", {"chat_id": chat_id, "text": text})
                msg["delivered_to_telegram"] = True
                msg["delivered_at"] = _now()
                delivered += 1
        
        if delivered:
            OUTBOX_FILE.write_text(json.dumps(outbox, indent=2, ensure_ascii=False))
        
        return delivered
    except:
        return 0


def main():
    print("🧠 Brain Telegram Daemon starting...")
    
    # Verify bot
    me = api("getMe")
    if me.get("ok"):
        bot_name = me["result"]["username"]
        print(f"   Bot: @{bot_name}")
    else:
        print(f"   ❌ Invalid token: {me}")
    
    state = load_state()
    print(f"   Offset: {state['last_update_id']}")
    print()
    
    while True:
        try:
            # Get updates
            result = api("getUpdates", {
                "offset": state["last_update_id"] + 1,
                "timeout": 30,
                "allowed_updates": ["message"]
            })
            
            if result.get("ok"):
                for update in result.get("result", []):
                    uid = update["update_id"]
                    state["last_update_id"] = max(state["last_update_id"], uid)
                    
                    msg = update.get("message", {})
                    if not msg or not msg.get("text"):
                        continue
                    
                    chat_id = msg["chat"]["id"]
                    text = msg["text"]
                    user = msg.get("from", {}).get("first_name", "User")
                    
                    # /start → welcome
                    if text == "/start":
                        api("sendMessage", {
                            "chat_id": chat_id,
                            "text": (
                                "🧠 *Cérebro da ENTIDADE*\n\n"
                                "Camada operacional digital de Roberto. "
                                "Subordinado ao Agente (Córtex).\n\n"
                                "📊 HIERARQUIA: Roberto → Agente → Cérebro\n\n"
                                "*Comandos:*\n"
                                "• `status` — saúde dos 7 módulos\n"
                                "• `forex` / `viés` — análise semanal\n"
                                "• `pilares` — todos os pilares\n"
                                "• `skills` — habilidades (113)\n"
                                "• `auto desenvolvimento` — meus ciclos\n"
                                "• `identidade` / `hierarquia` — quem sou\n"
                                "• `saúde` / `mental` — check-ins\n"
                                "• `financeiro` — renda e freelas\n"
                                "• `memória` — contexto e regras\n\n"
                                "_Resposta imediata. Sempre à disposição._"
                            ),
                            "parse_mode": "Markdown"
                        })
                        continue
                    
                    # Route to brain gateway inbox (for logging/assimilation)
                    route_to_brain(msg["message_id"], chat_id, user, text)
                    
                    # ⚡ PROCESSAR IMEDIATAMENTE
                    response, topics = _brain_process(text)
                    
                    # Enviar resposta direto no Telegram
                    api("sendMessage", {
                        "chat_id": chat_id,
                        "text": f"🧠 {response}"
                    })
                    
                    # 🧠 APRENDER com esta conversa
                    try:
                        from brain_gateway import _brain_learn
                        _brain_learn(text, response, topics)
                    except:
                        pass
                    
                    # Registrar no neural_sync para Agent assimilar depois
                    try:
                        sync_file = HERMES / "neural_sync.json"
                        sync = json.loads(sync_file.read_text()) if sync_file.exists() else {}
                        if "interactions" not in sync:
                            sync["interactions"] = []
                        sync["interactions"].append({
                            "timestamp": _now(),
                            "user_message": text[:300],
                            "brain_response": response[:300],
                            "topics": topics,
                            "message_id": f"tg_{msg['message_id']}",
                        })
                        sync["interactions"] = sync["interactions"][-200:]
                        sync["last_updated"] = _now()
                        sync_file.write_text(json.dumps(sync, indent=2, ensure_ascii=False))
                    except:
                        pass
                    
                    print(f"[{_now()[:19]}] {user}: {text[:50]} → {topics}")
                
                save_state(state)
            
            # Deliver pending brain responses
            delivered = deliver_responses()
            if delivered:
                print(f"[{_now()[:19]}] Delivered {delivered} responses")
            
        except Exception as e:
            print(f"[{_now()[:19]}] Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
