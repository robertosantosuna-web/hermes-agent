# Telegram Web K — CDP Automation

Automation of Telegram Web K (`web.telegram.org/k/`) via Chrome DevTools Protocol (CDP).
Used when Telethon/Python API is unavailable or when browser-based interaction is needed
(e.g., @BotFather bot creation, reading chats via CDP screenshot fallback).

## Connection

```python
# Brave real (desktop, port 9222) — Telegram Web K precisa estar aberto
tabs = json.loads(urllib.request.urlopen('http://localhost:9222/json/list').read())
tg_tab = [t for t in tabs if 'web.telegram.org/k/' in t.get('url','') and 'Telegram Web' in t.get('title','')][0]
ws_url = tg_tab['webSocketDebuggerUrl']
```

## Reading Screen Content

```python
# Telegram Web K renders content in virtual DOM — use innerText
cdp("Runtime.evaluate", {
    "expression": "document.body.innerText",
    "returnByValue": True
})
```

## Navigating to a Chat

```python
# Direct URL navigation
cdp("Runtime.evaluate", {
    "expression": "window.location.href = 'https://web.telegram.org/k/#@BotFather'",
    "returnByValue": True
})
# OR open new tab
urllib.request.Request('http://localhost:9222/json/new?https://web.telegram.org/k/%23@BotFather', method='PUT')
```

## Sending Messages (the CORRECT way)

### ❌ DOES NOT WORK: DOM manipulation
```python
# contentEditable textContent + InputEvent — typed but NOT sent
editable.textContent = '/newbot'
editable.dispatchEvent(new InputEvent('input', ...))
# → Message stays as draft, never delivered
```

### ✅ WORKS: CDP Input.dispatchKeyEvent (char mode)
```python
# Type each character via CDP char events
for char in "Hermes Brain":
    cdp("Input.dispatchKeyEvent", {
        "type": "char",
        "text": char,
        "unmodifiedText": char
    })
    time.sleep(0.05)

# Press Enter to send
cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Enter", "code": "Enter", "keyCode": 13})
cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Enter", "code": "Enter", "keyCode": 13})
```

**Why this works:** `Input.dispatchKeyEvent` with `type: "char"` injects characters at the OS input level inside the browser. Telegram Web K's React handler sees them as genuine keyboard input. The Enter keyDown/keyUp triggers the send action.

**PITFALL:** DOM-level events (InputEvent, KeyboardEvent, textContent manipulation) are ignored by Telegram Web K's React reconciliation. Only CDP-level input dispatch works.

## Creating a Bot via @BotFather

Full pipeline tested and working:

1. Open `https://web.telegram.org/k/#@BotFather`
2. Send `/newbot` via `Input.dispatchKeyEvent` chars + Enter
3. Wait for response, read via `document.body.innerText`
4. Send bot name (e.g., "Hermes Brain")
5. Send bot username (must end in "bot", e.g., "HermesEntidadeBot")
6. Extract token from response: `re.search(r'(\d{9,11}:[A-Za-z0-9_-]{35,})', text)`
7. Save token to `.env`

## Reading Bot Responses

```python
# After sending, wait and extract the BotFather response
time.sleep(4)
text = cdp("Runtime.evaluate", {
    "expression": "document.body.innerText", 
    "returnByValue": True
})
# Parse token: re.search(r'(\d{9,11}:[A-Za-z0-9_-]{35,})', text)
```

## @HermesEntidadeBot — Brain Telegram Bot

- Token: `TELEGRAM_BRAIN_BOT_TOKEN` in `~/.hermes/.env`
- Daemon: `hermes-brain-telegram.service` (systemd user)
- Response: IMMEDIATE (processes via `_brain_process()` inline, not cron-based)
- Chat with Roberto: ID `845735429`
