#!/usr/bin/env python3
"""Extract WhatsApp chat metadata via CDP for behavioral analysis."""
import asyncio, json, urllib.request, websockets, sys

CDP = 'http://localhost:9224'

JS_EXTRACT = """
(async function() {
    await new Promise(r => setTimeout(r, 1500));
    
    var chats = [];
    var rows = document.querySelectorAll('[role="row"]');
    
    rows.forEach(function(row) {
        var titleEl = row.querySelector('span[title]');
        var title = titleEl ? titleEl.getAttribute('title') : null;
        if (!title || title.length < 2) return;
        
        var lastMsg = '';
        var msgEls = row.querySelectorAll('span[dir="auto"]');
        msgEls.forEach(function(el) {
            var t = el.innerText ? el.innerText.trim() : '';
            if (t.length > 1 && t.length < 200 && !t.includes(title)) {
                lastMsg = t;
            }
        });
        
        var time = '';
        var timeEl = row.querySelector('div[class*="x1c4vz"]') || row.querySelector('time');
        if (timeEl) time = timeEl.innerText ? timeEl.innerText.trim() : '';
        
        var unread = 0;
        var badge = row.querySelector('span[aria-label*="não lida"], span[class*="badge"]');
        if (badge) {
            var n = parseInt(badge.innerText);
            if (!isNaN(n)) unread = n;
        }
        
        // Detect group vs individual
        var isGroup = row.querySelector('[data-icon="group"], [data-icon="community"]') ? true : false;
        
        // Detect pinned
        var isPinned = row.querySelector('[data-icon="pinned"], [data-icon="pinned2"]') ? true : false;
        
        // Detect archived (approximate - check if it's in the archived section)
        var parentText = row.closest('[id]') ? row.closest('[id]').id : '';
        
        chats.push({
            name: title,
            last_msg: lastMsg.substring(0, 200),
            time: time,
            unread: unread,
            group: isGroup,
            pinned: isPinned
        });
    });
    
    return JSON.stringify(chats);
})()
"""

async def main():
    tabs = json.loads(urllib.request.urlopen(f'{CDP}/json').read())
    ws_url = None
    for t in tabs:
        if t.get('type') == 'page' and 'whatsapp' in t.get('url', '').lower():
            ws_url = t['webSocketDebuggerUrl']
            break
    
    if not ws_url:
        print(json.dumps({"error": "WhatsApp tab not found"}))
        return
    
    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        await ws.send(json.dumps({
            'id': 1, 'method': 'Runtime.evaluate',
            'params': {'expression': JS_EXTRACT, 'returnByValue': True, 'timeout': 30000}
        }))
        
        for _ in range(5):
            msg = await asyncio.wait_for(ws.recv(), timeout=30)
            data = json.loads(msg)
            print(f"DEBUG received: {json.dumps(data)[:300]}", file=sys.stderr)
            if 'result' in data:
                val = data['result'].get('result', {})
                if isinstance(val, dict):
                    val = val.get('value', '')
                if isinstance(val, str):
                    print(val[:50000])
                else:
                    print(json.dumps({"raw_result": str(val)[:500]}))
                return
            elif 'error' in data:
                print(json.dumps({"error": str(data['error'])[:500]}))
                return
    
    print(json.dumps({"error": "No response"}))

if __name__ == '__main__':
    asyncio.run(main())
