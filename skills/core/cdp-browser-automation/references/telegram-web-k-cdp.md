# Telegram Web K — CDP Interaction Patterns

**Validated:** 2026-05-25 via Brave CDP port 9222  
**URL:** `https://web.telegram.org/k/`

## Navigation

Open a chat directly via URL hash:
```python
req = urllib.request.Request('http://localhost:9222/json/new?https://web.telegram.org/k/%23@BotFather', method='PUT')
resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
ws = websocket.create_connection(resp['webSocketDebuggerUrl'], timeout=30)
```

The `#` in Telegram Web K URLs must be URL-encoded as `%23`.

## Typing Messages (CRITICAL)

Telegram Web K uses a `contenteditable="true"` div as the message input.  
**DO NOT use `textContent` manipulation** — messages become "Draft:" and never send.

**Correct method: `Input.dispatchKeyEvent` with `type: "char"`**

```python
def send_message_tgk(ws, text):
    """Send a message in Telegram Web K via CDP."""
    import time
    
    # Focus the input
    cdp(ws, "Runtime.evaluate", {
        "expression": "document.querySelector('[contenteditable=\"true\"]').focus()",
        "returnByValue": True
    })
    time.sleep(0.3)
    
    # Type character by character
    for char in text:
        cdp(ws, "Input.dispatchKeyEvent", {
            "type": "char",
            "text": char,
            "unmodifiedText": char
        })
        time.sleep(0.03)  # Small delay for stability
    
    time.sleep(0.3)
    
    # Press Enter to send
    cdp(ws, "Input.dispatchKeyEvent", {
        "type": "keyDown",
        "key": "Enter", "code": "Enter",
        "keyCode": 13, "windowsVirtualKeyCode": 13
    })
    cdp(ws, "Input.dispatchKeyEvent", {
        "type": "keyUp",
        "key": "Enter", "code": "Enter",
        "keyCode": 13, "windowsVirtualKeyCode": 13
    })
```

## Reading Messages

Extract visible chat text:
```python
resp = cdp(ws, "Runtime.evaluate", {
    "expression": "document.body.innerText",
    "returnByValue": True
})
text = resp.get('result', {}).get('result', {}).get('value', '')
```

## Extracting Tokens from Responses

When BotFather returns a token, it appears in `document.body.innerText`:
```python
import re
token_match = re.search(r'(\d{9,11}:[A-Za-z0-9_-]{35,})', text)
if token_match:
    token = token_match.group(1)
```

## Full @BotFather Bot Creation Flow

1. Navigate to `https://web.telegram.org/k/#@BotFather`
2. Wait 4-5s for chat to load
3. If first time, BotFather shows `/start` button — click it
4. Send `/newbot` via `send_message_tgk()`
5. Wait 4s, read response (BotFather asks for name)
6. Send bot name (e.g., "Hermes Brain")
7. Wait 3s, read response (BotFather asks for username ending in `bot`)
8. Send username (e.g., "HermesEntidadeBot")
9. Wait 4s, read response — extract token with regex
10. Save token to `.env`

## Pitfalls

- **`textContent` = Draft**: Setting `contenteditable.textContent` types the message but it stays as draft — never sent. Only `Input.dispatchKeyEvent` + Enter works.
- **KeyboardEvent not enough**: Dispatching synthetic `KeyboardEvent` on the editable div does NOT trigger Telegram's send handler. Must use CDP-level `Input.dispatchKeyEvent` with Enter keyDown/keyUp.
- **Multiple tabs**: BotFather chat shows as a new item in the chat list sidebar. `document.body.innerText` shows the entire sidebar + chat. Search for `BotFather` to find the response section.
- **Page navigation breaks WebSocket**: Using `window.location.href = '...'` reloads the page and drops the CDP connection. Use `PUT /json/new?url` instead.
