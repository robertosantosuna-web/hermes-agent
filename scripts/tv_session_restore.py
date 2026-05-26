#!/usr/bin/env python3
"""
TradingView Session Restorer — Injeta cookies de sessão no navegador CDP.
Roda ao iniciar o hermes-brain-browser para manter login persistente.

Usa cookies salvos de ~/.hermes/browser/tradingview_cookies.json.
"""
import asyncio, json, sys, urllib.request
from pathlib import Path

CDP_URL = 'http://localhost:9223'
COOKIE_FILE = Path('/home/roberto/.hermes/browser/tradingview_cookies.json')

async def restore():
    if not COOKIE_FILE.exists():
        print("No cookie backup found")
        return False
    
    cookies_data = json.loads(COOKIE_FILE.read_text())
    cookies = cookies_data.get('cookies', [])
    
    if not cookies:
        print("No cookies in backup")
        return False
    
    # Wait for CDP to be ready
    import time
    for _ in range(10):
        try:
            urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=2)
            break
        except:
            time.sleep(1)
    else:
        print("CDP not ready after 10s")
        return False
    
    # Get or create a tab
    tabs = json.loads(urllib.request.urlopen(f"{CDP_URL}/json/list").read())
    tab = next((t for t in tabs if t.get('type') == 'page'), None)
    if not tab:
        req = urllib.request.Request(f"{CDP_URL}/json/new", method='PUT')
        resp = urllib.request.urlopen(req, timeout=5)
        tab = json.loads(resp.read())
    
    import websockets
    ws_url = tab['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        imported = 0
        for c in cookies:
            try:
                params = {
                    'name': c['name'],
                    'value': c['value'],
                    'domain': c['domain'].lstrip('.'),
                    'path': c.get('path', '/'),
                    'secure': c.get('secure', False),
                    'httpOnly': c.get('httpOnly', False),
                }
                if c.get('expires'):
                    params['expires'] = c['expires']
                
                await ws.send(json.dumps({
                    'id': 1, 'method': 'Network.setCookie', 'params': params
                }))
                resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
                if resp.get('result', {}).get('success'):
                    imported += 1
            except:
                pass
    
    print(f"TradingView session restored: {imported}/{len(cookies)} cookies")
    return imported > 0

if __name__ == '__main__':
    asyncio.run(restore())
