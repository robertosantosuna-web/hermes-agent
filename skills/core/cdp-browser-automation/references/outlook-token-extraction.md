# Outlook Token Extraction via CDP → REST API

When Outlook Web (`outlook.live.com` or `outlook.cloud.microsoft.com`) renders email content inside sandboxed iframes that are inaccessible via DOM/CDP evaluation, the workaround is to extract the MSAL access token from the browser's localStorage and use the Outlook REST API directly.

## Problem

- `document.body.innerText` returns only the sidebar/email list, not the actual email body
- The reading pane content is in a sandboxed iframe with `display: none`
- `document.querySelectorAll('iframe')` finds the iframe but `contentDocument` is null (cross-origin sandbox)
- Frame tree shows `about:blank` for the iframe — content loaded dynamically after click

## Solution: Three-Step Flow

### Step 1: Find the MSAL token keys

```python
import json, urllib.request, asyncio, websockets

# Connect to the Outlook tab
tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read())
tab = [t for t in tabs if 'outlook.live.com' in t.get('url','')][0]
ws_url = tab['webSocketDebuggerUrl']

async with websockets.connect(ws_url, max_size=10_000_000) as ws:
    # Enable Runtime
    await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
    while True:
        r = json.loads(await ws.recv())
        if r.get('id') == 1: break
    
    # Find all localStorage keys containing MSAL tokens
    await ws.send(json.dumps({
        "id": 2,
        "method": "Runtime.evaluate",
        "params": {
            "expression": """
            (() => {
                let keys = [];
                for (let i = 0; i < localStorage.length; i++) {
                    let k = localStorage.key(i);
                    if (k.includes('accesstoken') && k.includes('outlook')) {
                        keys.push({key: k, value: localStorage.getItem(k)});
                    }
                }
                return JSON.stringify(keys);
            })()
            """,
            "returnByValue": True
        }
    }))
```

### Step 2: Extract the bearer token

The token is stored as a JSON object in localStorage under a key like:
```
msal.2|00000000-0000-0000-f72f-c345d31cf369.9188040d-6c67-4c5b-b112-36a304b66dad|login.windows.net|accesstoken|9199bf20-a13f-4107-85dc-02114787ef48|9188040d-6c67-4c5b-b112-36a304b66dad|https://outlook.office.com/m365.access||
```

The value is JSON: `{"secret": "EwA4BOl3BAAU...", "target": "https://outlook.office.com/M365.Access", ...}`

**IMPORTANT**: There are usually TWO tokens:
1. `service::outlook.office.com::MBI_SSL` — for the web client (may not work for REST API)
2. `https://outlook.office.com/M365.Access` — **this is the one to use for REST API calls**

### Step 3: Call the Outlook REST API

Use `https://outlook.office.com/api/v2.0/me/messages` (NOT Microsoft Graph — the token scope doesn't cover Graph):

```python
import urllib.request, json, re

token = "EwA4BOl3BAAU..."  # The secret from the MSAL token
url = f"https://outlook.office.com/api/v2.0/me/messages?$search=%22{search_term}%22&$top=3&$select=Subject,BodyPreview,Body,From,ReceivedDateTime"

req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Accept", "application/json")

resp = json.loads(urllib.request.urlopen(req).read())
for msg in resp.get('value', []):
    body = msg.get('Body', {}).get('Content', '')
    clean = re.sub(r'<[^>]+>', ' ', body)
    clean = re.sub(r'\s+', ' ', clean)
    print(clean)
```

## API Comparison

| API | URL Base | Token Scope | Status |
|-----|----------|-------------|--------|
| Outlook REST v2 | `outlook.office.com/api/v2.0` | `outlook.office.com/M365.Access` | ✅ Works |
| Microsoft Graph v1 | `graph.microsoft.com/v1.0` | `graph.microsoft.com` | ❌ Scope mismatch |

The token extracted from Outlook Web's localStorage is scoped to `outlook.office.com`, NOT `graph.microsoft.com`. Using it with Graph API returns `401 InvalidAuthenticationToken: JWT is not well formed`.

## Token Lifetime

MSAL tokens have:
- `cachedAt` — when captured (epoch seconds)
- `expiresOn` — when it expires (~24h from issuance)
- `extendedExpiresOn` — extended expiration with refresh

The extracted token is valid for the current session. For persistent access, set up proper OAuth with `offline_access` scope instead of relying on extracted tokens.

## Full Working Script

See `scripts/extract_outlook_email.py` for a complete standalone script.

## Related

- **cdp-browser-automation** — CDP connection patterns
- **email-autonomy** — email monitoring and triage
- **credential-vault** — secure token storage
