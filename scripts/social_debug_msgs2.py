#!/usr/bin/env python3
"""Debug v2 - check raw HTML of WhatsApp message area."""
import asyncio, json, urllib.request, websockets

CDP = 'http://localhost:9224'

async def run_js(expression, timeout=15):
    tabs = json.loads(urllib.request.urlopen(f'{CDP}/json').read())
    ws_url = None
    for t in tabs:
        if t.get('type') == 'page' and 'whatsapp' in t.get('url', '').lower():
            ws_url = t['webSocketDebuggerUrl']
            break
    
    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        await ws.send(json.dumps({
            'id': 1, 'method': 'Runtime.evaluate',
            'params': {'expression': expression, 'returnByValue': True, 'timeout': timeout * 1000}
        }))
        
        for _ in range(5):
            msg = await asyncio.wait_for(ws.recv(), timeout=timeout + 5)
            data = json.loads(msg)
            if 'result' in data:
                result = data['result'].get('result', {})
                if isinstance(result, dict):
                    value = result.get('value', {})
                    if isinstance(value, dict):
                        return value
                    elif isinstance(value, str):
                        try: return json.loads(value)
                        except: return {"raw": value[:500]}
    return {"error": "no response"}

async def main():
    # Check if a chat is already open
    check = """
    JSON.stringify({
        header: document.querySelector('#main header') ? document.querySelector('#main header').innerText.substring(0, 80) : 'NO-HEADER',
        mainHTML: document.querySelector('#main') ? document.querySelector('#main').innerHTML.substring(0, 2000) : 'NO-MAIN',
        allDivs: document.querySelectorAll('#main div').length,
        allSpans: document.querySelectorAll('#main span').length
    })
    """
    
    print("=== Current state ===")
    r = await run_js(check)
    print(json.dumps(r, indent=2, ensure_ascii=False)[:3000])
    
    # If no header, try clicking Pai
    if 'NO-HEADER' in str(r):
        print("\n=== Clicking Pai ===")
        click = """
        (function() {
            var rows = document.querySelector('#pane-side').querySelectorAll('[role="row"]');
            for (var r of rows) {
                var spans = r.querySelectorAll('span[title]');
                for (var s of spans) {
                    var t = s.getAttribute('title').trim().replace(/[\\u200e\\u200f]/g, '');
                    if (t === 'Pai') {
                        r.click();
                        return 'clicked-pai';
                    }
                }
            }
            return 'not-found';
        })()
        """
        cr = await run_js(click)
        print(f"Click: {cr}")
        
        # Wait 4 seconds for messages to load
        await asyncio.sleep(4)
        
        # Check again
        print("\n=== After click + 4s wait ===")
        r2 = await run_js(check)
        print(json.dumps(r2, indent=2, ensure_ascii=False)[:3000])

asyncio.run(main())
