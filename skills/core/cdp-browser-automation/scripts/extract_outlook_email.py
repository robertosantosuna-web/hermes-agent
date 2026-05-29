#!/usr/bin/env python3
"""Extract email content from Outlook Web using MSAL token from CDP localStorage.

Usage:
    python3 extract_outlook_email.py <search_term>
    
Example:
    python3 extract_outlook_email.py "Carta Proposta"
    
Requirements:
    pip install websocket-client  # NOT websockets
    Brave/Edge running with --remote-debugging-port=9222
    User logged into Outlook Web
"""

import json, sys, re, urllib.request, websocket

CDP_PORT = 9222
SEARCH_TERM = sys.argv[1] if len(sys.argv) > 1 else "Carta Proposta"

def get_outlook_tab():
    """Find the Outlook tab in CDP tabs."""
    tabs = json.loads(urllib.request.urlopen(f"http://localhost:{CDP_PORT}/json").read())
    for t in tabs:
        if 'outlook.live.com' in t.get('url', '') and t['type'] == 'page':
            return t
    raise RuntimeError("No Outlook tab found. Open Outlook Web first.")

def extract_token(ws):
    """Extract MSAL access token from localStorage."""
    mid = [0]
    def cdp(method, params=None):
        mid[0] += 1
        ws.send(json.dumps({'id': mid[0], 'method': method, 'params': params or {}}))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == mid[0]:
                return resp.get('result', {})
    
    # Enable Runtime
    cdp('Runtime.enable')
    
    # Get tokens from localStorage
    result = cdp('Runtime.evaluate', {
        'expression': """
        (() => {
            let tokens = [];
            for (let i = 0; i < localStorage.length; i++) {
                let k = localStorage.key(i);
                if (k.includes('accesstoken') && (k.includes('outlook') || k.includes('m365'))) {
                    let v = localStorage.getItem(k);
                    try {
                        let parsed = JSON.parse(v);
                        if (parsed.secret && parsed.target) {
                            tokens.push({key: k, secret: parsed.secret, target: parsed.target});
                        }
                    } catch(e) {}
                }
            }
            return JSON.stringify(tokens);
        })()
        """,
        'returnByValue': True
    })
    
    tokens = json.loads(result.get('result', {}).get('value', '[]'))
    
    # Prefer M365.Access token over MBI_SSL
    for t in tokens:
        if 'M365.Access' in t.get('target', ''):
            return t['secret']
    
    # Fallback to any token
    if tokens:
        return tokens[0]['secret']
    
    raise RuntimeError("No MSAL token found in localStorage")

def search_emails(token, search_term):
    """Search emails using Outlook REST API."""
    import urllib.parse
    encoded = urllib.parse.quote(f'"{search_term}"')
    url = (f"https://outlook.office.com/api/v2.0/me/messages"
           f"?$search={encoded}&$top=5"
           f"&$select=Subject,BodyPreview,Body,From,ReceivedDateTime")
    
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
    return resp.get('value', [])

def main():
    print(f"[*] Connecting to Outlook tab on port {CDP_PORT}...")
    tab = get_outlook_tab()
    print(f"[*] Found: {tab['title'][:80]}")
    
    ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=10)
    
    print("[*] Extracting MSAL token...")
    token = extract_token(ws)
    print(f"[*] Token: {token[:40]}... (redacted)")
    
    print(f"[*] Searching for: {SEARCH_TERM}")
    emails = search_emails(token, SEARCH_TERM)
    print(f"[*] Found {len(emails)} emails\n")
    
    for i, msg in enumerate(emails):
        print(f"{'='*60}")
        print(f"#{i+1} | Subject: {msg.get('Subject', '?')}")
        print(f"    | From: {msg.get('From', {}).get('EmailAddress', {}).get('Name', '?')}")
        print(f"    | Date: {msg.get('ReceivedDateTime', '?')}")
        body = msg.get('Body', {}).get('Content', msg.get('BodyPreview', ''))
        clean = re.sub(r'<[^>]+>', ' ', body[:5000])
        clean = re.sub(r'&nbsp;', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        print(f"    | Body: {clean[:2000]}")
        print()
    
    ws.close()

if __name__ == '__main__':
    main()
