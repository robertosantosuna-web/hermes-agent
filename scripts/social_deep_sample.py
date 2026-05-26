#!/usr/bin/env python3
"""Deep-dive: extract message samples from key WhatsApp chats for tone analysis."""
import asyncio, json, urllib.request, websockets, sys, os
from datetime import datetime
from pathlib import Path

CDP = 'http://localhost:9224'
OUTPUT = Path.home() / '.hermes' / 'data' / 'social' / 'whatsapp_deep_samples.json'

async def run_js(expression, timeout=30):
    tabs = json.loads(urllib.request.urlopen(f'{CDP}/json').read())
    ws_url = None
    for t in tabs:
        if t.get('type') == 'page' and 'whatsapp' in t.get('url', '').lower():
            ws_url = t['webSocketDebuggerUrl']
            break
    
    if not ws_url:
        return {"error": "WhatsApp tab not found"}
    
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

async def click_chat(name):
    """Click on a chat by name and wait for messages to load."""
    escaped = name.replace('\\', '\\\\').replace("'", "\\'")
    js = f"""
    (function() {{
        var pane = document.querySelector('#pane-side');
        if (!pane) return 'no-pane';
        var rows = pane.querySelectorAll('[role="row"]');
        for (var r of rows) {{
            var spans = r.querySelectorAll('span[title]');
            for (var s of spans) {{
                var t = s.getAttribute('title') || '';
                t = t.replace(/[\\u200e\\u200f]/g, '').trim();
                if (t.includes('{escaped}')) {{
                    r.click();
                    return 'clicked:' + t.substring(0, 30);
                }}
            }}
        }}
        return 'not-found';
    }})()
    """
    result = await run_js(js)
    # Wait for messages to load
    await asyncio.sleep(2)
    return result

async def read_sample_messages():
    """Read last 30 messages from currently open chat."""
    js = """
    (function() {
        var mainPanel = document.querySelector('#main');
        if (!mainPanel) return JSON.stringify({error: 'main panel not found'});
        
        // WhatsApp message containers - try multiple selectors
        var containers = mainPanel.querySelectorAll('[data-testid="msg-container"], div.message-in, div.message-out, div[class*="message"]');
        
        var msgs = [];
        containers.forEach(function(c) {
            var text = c.innerText.trim();
            if (text.length < 3) return;
            
            // Detect if outgoing (your message) vs incoming
            var isOutgoing = c.querySelector('[data-testid="msg-check"], [data-testid="msg-dblcheck"], [data-icon="msg-check"]') !== null;
            if (!isOutgoing) {
                // WhatsApp Web: outgoing messages have specific classes
                isOutgoing = c.classList.contains('message-out') || 
                            c.querySelector('div[class*="out"]') !== null ||
                            c.closest('[class*="out"]') !== null;
            }
            
            // Try to get timestamp
            var time = '';
            var timeEl = c.querySelector('span[class*="time"], time, div[class*="time"]');
            if (timeEl) time = timeEl.innerText.trim();
            
            msgs.push({
                text: text.replace(/\\n+/g, ' ').substring(0, 300),
                time: time,
                outgoing: isOutgoing
            });
        });
        
        // Return last 30 messages
        var sample = msgs.slice(-30);
        return JSON.stringify({count: msgs.length, sample: sample});
    })()
    """
    return await run_js(read_sample_messages.__code__.co_consts[1] if False else js)

# Actually the closure above might not work, let me inline
JS_READ_MSGS = """
(function() {
    var mainPanel = document.querySelector('#main');
    if (!mainPanel) return JSON.stringify({error: 'main panel not found'});
    
    var allDivs = mainPanel.querySelectorAll('div[role="row"], div[data-testid="msg-container"]');
    if (allDivs.length === 0) {
        // Fallback: get all text content from message area
        var msgArea = mainPanel.querySelector('[role="region"]') || mainPanel;
        var text = msgArea.innerText.substring(0, 5000);
        return JSON.stringify({raw: text, count: 0});
    }
    
    var msgs = [];
    allDivs.forEach(function(c) {
        var text = c.innerText.trim();
        if (text.length < 2) return;
        
        // Detect outgoing: check for checkmarks
        var isOutgoing = c.querySelector('span[data-icon="msg-check"], span[data-icon="msg-dblcheck"]') !== null;
        
        // Get timestamp
        var timeEl = c.querySelector('span[class*="x1rg5ohu"]') || c.querySelector('div[class*="x1rg5ohu"]');
        var time = timeEl ? timeEl.innerText.trim() : '';
        
        msgs.push({
            text: text.replace(/\\n+/g, ' | ').substring(0, 300),
            time: time,
            outgoing: isOutgoing
        });
    });
    
    // Return last 30
    var sample = msgs.slice(-30);
    return JSON.stringify({count: msgs.length, sample: sample});
})()
"""

async def main():
    # Key contacts to analyze - start with family and most active
    targets = [
        "Pai", "Mãe", "Thais", "Pati",
        "Dinei cleia", "Maria Sogra", "CLEIDE🥰"
    ]
    
    results = {}
    
    for name in targets:
        try:
            print(f"  📱 {name}...", file=sys.stderr)
            
            # Click on chat
            escaped = name.replace('\\', '\\\\').replace("'", "\\'")
            click_js = f"""
            (function() {{
                var pane = document.querySelector('#pane-side');
                if (!pane) return 'no-pane';
                var rows = pane.querySelectorAll('[role="row"]');
                for (var r of rows) {{
                    var spans = r.querySelectorAll('span[title]');
                    for (var s of spans) {{
                        var t = s.getAttribute('title') || '';
                        t = t.replace(/[\\u200e\\u200f]/g, '').trim();
                        if (t === '{escaped}' || t.includes('{escaped[:20]}')) {{
                            r.click();
                            return 'clicked:' + t.substring(0, 30);
                        }}
                    }}
                }}
                return 'not-found';
            }})()
            """
            
            click_result = await run_js(click_js)
            await asyncio.sleep(2)
            
            if 'not-found' in str(click_result):
                results[name] = {"error": "not found"}
                print(f"    NAO ENCONTRADO", file=sys.stderr)
                continue
            
            # Read messages
            msgs = await run_js(JS_READ_MSGS)
            results[name] = msgs
            count = msgs.get('count', 0)
            print(f"    {count} mensagens", file=sys.stderr)
            
        except Exception as e:
            results[name] = {"error": str(e)}
            print(f"    ERRO: {e}", file=sys.stderr)
    
    # Save
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    export = {
        'extracted_at': datetime.now().isoformat(),
        'contacts_analyzed': len(results),
        'samples': results
    }
    
    with open(OUTPUT, 'w') as f:
        json.dump(export, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Salvo: {OUTPUT}", file=sys.stderr)
    print(json.dumps(export, ensure_ascii=False))
    
    # Save
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    export = {
        'extracted_at': datetime.now().isoformat(),
        'contacts_analyzed': len(results),
        'samples': results
    }
    
    with open(OUTPUT, 'w') as f:
        json.dump(export, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Salvo: {OUTPUT}", file=sys.stderr)
    print(json.dumps(export, ensure_ascii=False))

asyncio.run(main())
