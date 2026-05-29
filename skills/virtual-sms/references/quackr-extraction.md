# Quackr.io SMS Number Extraction — Confirmed Pattern (29/05/2026)

## Confirmed Working Numbers (Brazil +55)

- `+55 (61) 98173-7725` — Active, auto-refreshing SMS page
- `+55 (11) 98765-4321` — Listed but may be placeholder (sequential digits)

## Extraction via CDP

The numbers are rendered in an Angular SPA. Raw HTTP/curl returns HTML without numbers — JavaScript rendering required.

### Pattern: Regex on `body.innerHTML`

```python
import re
html = await page.evaluate('() => document.body.innerHTML')
numbers = set(re.findall(r'55\d{9,11}', html))
```

Numbers appear as plain digit sequences within the rendered Angular DOM.

### Individual SMS Monitoring Page

URL pattern: `https://quackr.io/temporary-numbers/brazil/<FULL_NUMBER>`

Example: `https://quackr.io/temporary-numbers/brazil/5561981737725`

The page displays "Waiting on incoming messages..." and auto-refreshes when SMS arrives.

### Page Structure

- Title: `+556****7725 — Brazil Temporary Number | Receive SMS Online • Quackr`
- Warning banner: "Everyone on this page sees your verification codes."
- "Get a private number" CTA (links to /rent-sms-numbers)
- Messages appear in a list when received

## Opening via CDP

### Via HTTP (persists after script exits)
```bash
# PUT required, not GET
curl -s -X PUT "http://localhost:9225/json/new?$(python3 -c "import urllib.parse; print(urllib.parse.quote('https://quackr.io/temporary-numbers/brazil/5561981737725', safe=''))")"
```

### Via WebSocket (for programmatic extraction)
```python
from websocket import create_connection
import json, urllib.request

resp = urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=5)
ws_url = json.loads(resp.read())['webSocketDebuggerUrl']
ws = create_connection(ws_url, timeout=10)

# Create new target
ws.send(json.dumps({"id": 1, "method": "Target.createTarget", 
    "params": {"url": "https://quackr.io/temporary-numbers/brazil/5561981737725"}}))
r = json.loads(ws.recv())
new_tid = r['result']['targetId']

# Attach
ws.send(json.dumps({"id": 2, "method": "Target.attachToTarget", "params": {"targetId": new_tid}}))
r = json.loads(ws.recv())
sid = r['params']['sessionId']  # sessionId is in params, not result

# Check for messages
ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {
    "expression": "document.body.innerText.includes('Waiting on incoming') ? 'WAITING' : document.body.innerText.substring(0, 500)",
    "returnByValue": True
}, "sessionId": sid}))
```

## Pitfalls

- Numbers are SHARED — everyone sees your verification codes
- Numbers may already be blocked on target platforms
- The Angular SPA can be slow to render — wait 4-6s after navigation
- quackr.io pushes "Get a private number" upsells — ignore, free numbers work
- Phone number format: 11 digits starting with 55 (Brazil country code)
