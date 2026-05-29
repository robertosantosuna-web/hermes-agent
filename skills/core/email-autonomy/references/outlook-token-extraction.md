# Outlook Token Extraction via Browser CDP

When Outlook Web blocks DOM extraction (sandboxed iframes, dynamic rendering),
extract the MSAL access token from the browser's localStorage and use the
Outlook REST API directly.

## Why this works

Outlook Web (outlook.live.com / outlook.cloud.microsoft) renders email bodies
in sandboxed iframes with `display:none` initially. The email content is simply
not in the accessible DOM. CDP `Runtime.evaluate` on `document.body.innerText`
returns only the sidebar and email list — never the reading pane content.

The MSAL library stores access tokens in localStorage. These tokens can be
extracted via CDP and used with the Outlook REST API, which returns clean JSON.

## Step 1: Find the right CDP port

The browser with the Outlook session may not be on the expected port:

```bash
# Scan all likely CDP ports
for port in 9222 9223 9224 9225 9226; do
  echo "=== Porta $port ==="
  curl -s http://localhost:$port/json | python3 -c "
import sys, json
tabs = json.load(sys.stdin)
for t in tabs:
    if t['type'] == 'page':
        print(f\"  {t['id'][:20]}... | {t.get('title','?')[:80]}\")
        print(f\"    {t.get('url','?')[:120]}\")
  " 2>/dev/null
done
```

## Step 2: Connect via WebSocket and extract token

```python
import json, urllib.request, asyncio, websockets

async def extract_msal_token():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read())
    outlook_tab = [t for t in tabs if 'outlook' in t.get('url','').lower() and t['type'] == 'page'][0]
    ws_url = outlook_tab['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10_000_000) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        while True:
            r = json.loads(await ws.recv())
            if r.get('id') == 1: break
        
        # Extract MSAL access tokens for Outlook/M365
        await ws.send(json.dumps({
            "id": 2,
            "method": "Runtime.evaluate",
            "params": {
                "expression": """
                (() => {
                    let tokens = [];
                    for (let i = 0; i < localStorage.length; i++) {
                        let k = localStorage.key(i);
                        if (k.includes('accesstoken') && (k.includes('outlook') || k.includes('M365'))) {
                            let raw = localStorage.getItem(k);
                            try {
                                let parsed = JSON.parse(raw);
                                tokens.push({
                                    key: k,
                                    secret: parsed.secret,
                                    target: parsed.target,
                                    expiresOn: parsed.expiresOn,
                                    cachedAt: parsed.cachedAt
                                });
                            } catch(e) {
                                tokens.push({key: k, raw: raw.substring(0, 100)});
                            }
                        }
                    }
                    return JSON.stringify(tokens);
                })()
                """,
                "returnByValue": True
            }
        }))
        
        while True:
            r = json.loads(await ws.recv())
            if r.get('id') == 2:
                return json.loads(r.get('result', {}).get('result', {}).get('value', '[]'))
```

## Step 3: Use the token with Outlook REST API

The token with `target: "https://outlook.office.com/M365.Access"` works with the
Outlook REST API (not Microsoft Graph — that needs a different scope).

```python
import urllib.request, json, re

token = "<extracted_secret>"

# Search for emails
url = "https://outlook.office.com/api/v2.0/me/messages?$search=%22Carta%20Proposta%22&$top=5&$select=Subject,BodyPreview,Body,From,ReceivedDateTime"

req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Accept", "application/json")

resp = urllib.request.urlopen(req)
data = json.loads(resp.read())

for msg in data.get('value', []):
    subject = msg.get('Subject', '')
    sender = msg.get('From', {}).get('EmailAddress', {}).get('Name', '')
    date = msg.get('ReceivedDateTime', '')
    body_html = msg.get('Body', {}).get('Content', '')
    
    # Clean HTML
    body = re.sub(r'<[^>]+>', ' ', body_html)
    body = re.sub(r'\s+', ' ', body)
    
    print(f"Subject: {subject}")
    print(f"From: {sender}")
    print(f"Date: {date}")
    print(f"Body: {body[:2000]}")
    print("---")
```

## Token details

The MSAL tokens found in localStorage have this structure (inside a JSON string):

```json
{
  "homeAccountId": "00000000-0000-0000-...",
  "credentialType": "AccessToken",
  "secret": "EwA4BOl3BAAU...",
  "cachedAt": "1779813423",
  "expiresOn": "1779899822",
  "environment": "login.windows.net",
  "clientId": "9199bf20-...",
  "realm": "9188040d-...",
  "target": "https://outlook.office.com/M365.Access",
  "tokenType": "Bearer"
}
```

Key fields:
- `secret`: The actual access token (Bearer)
- `target`: What API this token is for (M365.Access covers Outlook REST API)
- `expiresOn`: Unix timestamp when token expires
- `cachedAt`: Unix timestamp when token was cached

The localStorage key pattern is:
`msal.2|<tenant>.<user>|<env>|<token_type>|<client_id>|<realm>|<target>||`

## Important notes

- **Token freshness**: MSAL auto-refreshes tokens. The cached token is valid for ~24h from `cachedAt`.
- **Token scope**: `M365.Access` works for Outlook REST API (`outlook.office.com`). It does NOT work for Microsoft Graph (`graph.microsoft.com`) — that needs a different scope.
- **API response format**: Outlook REST API returns PascalCase (`Subject`, `ReceivedDateTime`). Microsoft Graph returns camelCase. Don't mix them up.
- **Rate limiting**: The REST API has standard throttling. Don't make more than a few requests per second.
- **CDP vs REST choice**: Use REST API when you need email body content. Use CDP only for actions that require browser interaction (clicking links, navigating OAuth flows).
