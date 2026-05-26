#!/usr/bin/env python3
"""Debug WhatsApp chat extraction with multiple selector attempts."""
import asyncio, json, urllib.request, websockets

CDP = 'http://localhost:9224'

async def run_js(js, timeout=15):
    tabs = json.loads(urllib.request.urlopen(f'{CDP}/json').read())
    ws_url = None
    for t in tabs:
        if t.get('type') == 'page' and 'whatsapp' in t.get('url', '').lower():
            ws_url = t['webSocketDebuggerUrl']
            break
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({
            'id': 1, 'method': 'Runtime.evaluate',
            'params': {'expression': js, 'returnByValue': True}
        }))
        
        for _ in range(5):
            msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
            data = json.loads(msg)
            if 'result' in data:
                result = data['result'].get('result', {})
                if isinstance(result, dict):
                    value = result.get('value', {})
                    if isinstance(value, dict):
                        return value
                    return {"value": value}
            elif 'error' in data:
                return {"error": str(data['error'])[:300]}
    return {"error": "no response"}


async def main():
    # Test 1: pane-side structure
    js1 = """
    JSON.stringify({
        paneExists: !!document.querySelector('#pane-side'),
        listItems: document.querySelector('#pane-side') ? document.querySelector('#pane-side').querySelectorAll('[role="listitem"]').length : -1,
        rows: document.querySelector('#pane-side') ? document.querySelector('#pane-side').querySelectorAll('[role="row"]').length : -1,
        // Try to get any element that looks like a chat item
        firstItemHTML: document.querySelector('#pane-side') ? document.querySelector('#pane-side').children[0]?.children[0]?.children[0]?.outerHTML?.substring(0,500) : 'no-pane',
        // Direct selector
        chatItems: document.querySelectorAll('div[aria-label]').length,
        // Get some aria labels
        sampleLabels: (function() {
            var items = document.querySelectorAll('[aria-label]');
            var labels = [];
            for (var i = 0; i < Math.min(5, items.length); i++) {
                labels.push(items[i].getAttribute('aria-label').substring(0,60));
            }
            return labels;
        })()
    })
    """
    
    print("=== Test 1: DOM Structure ===")
    r = await run_js(js1)
    print(json.dumps(r, indent=2, ensure_ascii=False)[:2000])
    
    # Test 2: Try getting chats directly
    js2 = """
    JSON.stringify((function() {
        var pane = document.querySelector('#pane-side');
        if (!pane) return {error: 'no pane'};
        
        // WhatsApp Web stores chat data in React fiber
        // Let's try to get all visible text content grouped by row
        var rows = pane.querySelectorAll('[role="row"]');
        var result = [];
        
        rows.forEach(function(row, idx) {
            var text = row.innerText.replace(/\\n+/g, ' | ').substring(0, 200);
            var spans = row.querySelectorAll('span');
            var titles = [];
            spans.forEach(function(s) {
                var t = s.getAttribute('title');
                if (t && t.length > 1) titles.push(t.substring(0, 50));
            });
            result.push({
                idx: idx,
                text: text.substring(0, 150),
                titleCount: titles.length,
                firstTitles: titles.slice(0, 3)
            });
        });
        
        return {rowCount: rows.length, sample: result.slice(0, 10)};
    })())
    """
    
    print("\n=== Test 2: Row extraction ===")
    r2 = await run_js(js2)
    print(json.dumps(r2, indent=2, ensure_ascii=False)[:3000])

asyncio.run(main())
