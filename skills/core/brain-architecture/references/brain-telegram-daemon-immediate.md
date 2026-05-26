# Brain Telegram Daemon — Immediate Response Pattern

**Validated:** 25/05/2026
**Bot:** @HermesEntidadeBot (criado via @BotFather usando CDP Input.dispatchKeyEvent)

## The Problem (v2.2)

The daemon wrote messages to `brain_gateway_inbox.json` and waited for the cron job
(`brain_gateway.py process`, every 2 min) to process and respond. User received
"🧠 Processando..." and waited up to 2 minutes.

## The Fix (v2.3)

Import `_brain_process()` and `_load_knowledge()` DIRECTLY from `brain_gateway.py`
in the daemon, bypassing the file-based pipeline:

```python
# In brain_telegram_daemon.py
sys.path.insert(0, str(HERMES / "scripts"))
from brain_gateway import _brain_process, _load_knowledge

# Message handler — IMMEDIATE response
response, topics = _brain_process(text)
api("sendMessage", {
    "chat_id": chat_id,
    "text": f"🧠 {response}"
})
```

## Required Setup

1. Create bot via @BotFather using CDP (see desktop-control skill)
2. Add `TELEGRAM_BRAIN_BOT_TOKEN=<token>` to `~/.hermes/.env`
3. Enable service: `systemctl --user enable --now hermes-brain-telegram`

## Hierarchy Awareness

The daemon identifies as **Cérebro da ENTIDADE**, NOT "Hermes Brain".
Hierarchy: Roberto → Agente (Córtex) → Cérebro.
Welcome message explicitly states subordination to the Agent.

## Pitfalls

- Bot cannot initiate conversation — user must send `/start` first
- Daemon uses Telegram long polling (30s timeout) — not webhooks
- If daemon crashes, cron-based gateway (`c34bd14a25a9`) provides fallback (2 min delay)
