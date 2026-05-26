#!/usr/bin/env python3
"""Debug WhatsApp Web DOM structure."""
import asyncio, json, urllib.request, websockets

CDP = 'http://localhost:9224'

async def main():
    tabs = json.loads(urllib.request.urlopen(f'{CDP}/json').read())
    ws_url = None
    for t in tabs:
        if t.get('type') == 'page' and 'whatsapp' in t.get('url', '').lower():
            ws_url = t['webSocketDebuggerUrl']
            break
    
    if not ws_url:
        print("WhatsApp tab not found")
        return
    
    # Simple DOM check
    js = """
    JSON.stringify({
        title: document.title,
        bodyText: document.body ? document.body.innerText.substring(0, 500) : 'no-body',
        rows: document.querySelectorAll('[role="row"]').length,
        spans: document.querySelectorAll('span[title]').length,
        divs: document.querySelectorAll('div').length,
        // Try common WhatsApp selectors
        chatList: document.querySelector('[data-testid="chat-list"]') ? 'found' : 'not-found',
        chatListAlt: document.querySelector('#pane-side') ? 'found-pane-side' : 'not-found',
        // Get first 5 span titles
        titles: (function() {
            var spans = document.querySelectorAll('span[title]');
            var titles = [];
            for (var i = 0; i < Math.min(5, spans.length); i++) {
                titles.push(spans[i].getAttribute('title'));
            }
            return titles;
        })(),
        // Check if content is loaded
        mainEl: document.querySelector('#main') ? 'found-main' : 'not-found'
    })
    """
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({
            'id': 1, 'method': 'Runtime.evaluate',
            'params': {'expression': js, 'returnByValue': True}
        }))
        
        for _ in range(5):
            msg = await asyncio.wait_for(ws.recv(), timeout=15)
            data = json.loads(msg)
            if 'result' in data:
                val = data['result'].get('result', {})
                if isinstance(val, dict):
                    val = val.get('value', '')
                print(val)
                return
            elif 'error' in data:
                print(f"Error: {data['error']}")
                return

asyncio.run(main())
