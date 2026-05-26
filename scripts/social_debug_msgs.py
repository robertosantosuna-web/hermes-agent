#!/usr/bin/env python3
"""Debug WhatsApp message reading."""
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
    # First click on "Pai" to open the chat
    click_js = """
    (function() {
        var rows = document.querySelector('#pane-side').querySelectorAll('[role="row"]');
        for (var r of rows) {
            var spans = r.querySelectorAll('span[title]');
            for (var s of spans) {
                var t = s.getAttribute('title').trim().replace(/[\\u200e\\u200f]/g, '');
                if (t === 'Pai') {
                    r.click();
                    return 'clicked';
                }
            }
        }
        return 'not-found';
    })()
    """
    
    click_result = await run_js(click_js)
    print(f"Click result: {click_result}")
    
    await asyncio.sleep(2)
    
    # Now debug message structure
    debug_js = """
    JSON.stringify({
        // Main area
        mainExists: !!document.querySelector('#main'),
        // Message region
        region: document.querySelector('#main') ? document.querySelector('#main').querySelector('[role="region"]') !== null : false,
        // Role rows in main
        rowsInMain: document.querySelectorAll('#main [role="row"]').length,
        // Message containers - try many selectors
        msgContainers: document.querySelectorAll('[data-testid="msg-container"]').length,
        msgIn: document.querySelectorAll('.message-in').length,
        msgOut: document.querySelectorAll('.message-out').length,
        // Copyable text spans
        copyableSpans: document.querySelectorAll('#main span[class*="selectable"], #main span[class*="copyable"]').length,
        // All spans in main
        allSpansInMain: document.querySelector('#main') ? document.querySelector('#main').querySelectorAll('span').length : 0,
        // Get header to verify we're in the right chat
        headerText: document.querySelector('#main header') ? document.querySelector('#main header').innerText.substring(0, 80) : 'no-header',
        // Get a chunk of text from message area
        msgText: (function() {
            var region = document.querySelector('#main [role="region"]');
            if (region) return region.innerText.substring(0, 1000);
            var alt = document.querySelector('#main div[class*="message"]');
            if (alt) return alt.parentElement.innerText.substring(0, 1000);
            return 'no-region';
        })(),
        // Try to find message bubbles by their structure
        firstMsgHTML: (function() {
            var rows = document.querySelectorAll('#main [role="row"]');
            if (rows.length > 0) return rows[0].outerHTML.substring(0, 500);
            var containers = document.querySelectorAll('[data-testid="msg-container"]');
            if (containers.length > 0) return containers[0].outerHTML.substring(0, 500);
            return 'no-rows-or-containers';
        })()
    })
    """
    
    result = await run_js(debug_js)
    print(f"\nDebug result:")
    print(json.dumps(result, indent=2, ensure_ascii=False)[:5000])

asyncio.run(main())
