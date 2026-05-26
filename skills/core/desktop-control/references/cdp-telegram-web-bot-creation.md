# CDP Visibility for Web Apps — Telegram Web K Pattern

**Validated: 25/05/2026** — Creating @HermesEntidadeBot via @BotFather entirely through CDP.

## When to Use

Any desktop app that has a web version AND renders on Wayland (GNOME 50.1). The web version
is visible via CDP; the native desktop app is 100% invisible (mss screenshots = black).

## Telegram Web K Specifics

| Aspect | Detail |
|--------|--------|
| URL | `https://web.telegram.org/k/` |
| Framework | React (Telegram Web K / "K" version) |
| CDP Port | 9222 (Brave real, user's logged-in session) |
| Read DOM | `document.body.innerText` → full chat list, messages, headers as plain text |
| Screenshot | `Page.captureScreenshot` → works, but DeepSeek can't process images |

## Typing in Telegram Web K

**DO NOT use DOM manipulation** — React ignores `textContent` + `InputEvent` on contenteditable divs.
Messages will appear as "Draft" but never send.

**USE CDP `Input.dispatchKeyEvent` with `type: "char"`:**

```python
import json, websocket, time, urllib.request

# Connect to Telegram Web K tab
tabs = json.loads(urllib.request.urlopen('http://localhost:9222/json/list').read())
tg_ws = next(t for t in tabs if 'web.telegram.org/k/' in t['url'])
ws = websocket.create_connection(tg_ws['webSocketDebuggerUrl'], timeout=30)

msg_id = [0]
def cdp(method, params=None):
    msg_id[0] += 1
    ws.send(json.dumps({"id": msg_id[0], "method": method, "params": params or {}}))
    return json.loads(ws.recv())

# Focus the input field
cdp("Runtime.evaluate", {
    "expression": "document.querySelector('[contenteditable=\"true\"]').focus()",
    "returnByValue": True
})

# Type character by character
for char in "/newbot":
    cdp("Input.dispatchKeyEvent", {
        "type": "char",
        "text": char,
        "unmodifiedText": char
    })
    time.sleep(0.05)

# Press Enter to send
cdp("Input.dispatchKeyEvent", {
    "type": "keyDown", "key": "Enter", "code": "Enter",
    "keyCode": 13, "windowsVirtualKeyCode": 13
})
cdp("Input.dispatchKeyEvent", {
    "type": "keyUp", "key": "Enter", "code": "Enter",
    "keyCode": 13, "windowsVirtualKeyCode": 13
})
```

## Verifying BotFather Responses

After sending `/newbot`, read the DOM to verify BotFather's response:

```python
# Get visible text (includes chat history + BotFather response)
text = cdp("Runtime.evaluate", {
    "expression": "document.body.innerText",
    "returnByValue": True
})['result']['result']['value']

# Search for token in response
import re
token_match = re.search(r'(\d{9,11}:[A-Za-z0-9_-]{35,})', text)
if token_match:
    token = token_match.group(1)
    print(f"Token: {token}")
```

## Bot Creation Flow

1. Navigate to `https://web.telegram.org/k/#@BotFather` (or open new tab via CDP)
2. Send `/newbot` → BotFather: "How are we going to call it?"
3. Send bot name (e.g., "Hermes Brain") → BotFather: "Choose a username ending in bot"
4. Send username (e.g., "HermesEntidadeBot") → BotFather: "Done! Here's your token"
5. Extract token with regex from `document.body.innerText`
6. Save token to `~/.hermes/.env` as `TELEGRAM_BRAIN_BOT_TOKEN=<token>`
7. Start daemon: `systemctl --user enable --now hermes-brain-telegram`

## Pitfalls

- **Character timing matters**: too fast (< 30ms between chars) and Telegram drops characters.
  Use 30-50ms delays.
- **`type: "char"` is mandatory**: `keyDown`/`keyUp` without `char` won't insert text.
- **Don't reuse WebSocket**: after `Page.navigate`, the WS connection breaks. Always reconnect.
- **React reconciliation**: DOM changes without CDP-level events are silently reverted by React.
- **Contenteditable vs input**: Telegram Web K uses contenteditable divs, NOT `<input>` elements.
  `element.value = 'text'` has no effect. Must use CDP keyboard events.
