#!/usr/bin/env python3
"""Extract WhatsApp chat data for behavioral analysis."""
import asyncio, json, urllib.request, websockets, sys, os
from datetime import datetime

CDP = 'http://localhost:9224'
OUTPUT = os.path.expanduser('~/.hermes/data/social_whatsapp_chats.json')

JS_EXTRACT = """
(async function() {
    await new Promise(r => setTimeout(r, 1000));
    
    // WhatsApp Web uses [role="listitem"] or [role="row"] for chats in #pane-side
    var pane = document.querySelector('#pane-side');
    if (!pane) return JSON.stringify({error: 'pane-side not found'});
    
    var chatElements = pane.querySelectorAll('[role="listitem"]');
    if (!chatElements || chatElements.length === 0) {
        chatElements = pane.querySelectorAll('[role="row"]');
    }
    
    var chats = [];
    
    chatElements.forEach(function(el) {
        // Get the main title (chat/contact name)
        var titleSpans = el.querySelectorAll('span[dir="auto"]');
        var name = '';
        for (var i = 0; i < titleSpans.length; i++) {
            var t = titleSpans[i].innerText ? titleSpans[i].innerText.trim() : '';
            if (t.length > 1 && t.length < 50 && !t.match(/^[\\d:\\s\\-,\\.\\u202f]+$/)) {
                name = t;
                break;
            }
        }
        
        if (!name || name.length < 2) return;
        
        // Last message (the second span[dir="auto"] usually)
        var allSpans = el.querySelectorAll('span[dir="auto"]');
        var lastMsg = '';
        var lastTime = '';
        
        for (var j = 0; j < allSpans.length; j++) {
            var txt = allSpans[j].innerText ? allSpans[j].innerText.trim() : '';
            if (txt === name) continue;
            if (txt.match(/^\\d{1,2}:\\d{2}$/) || txt.match(/^(Ontem|Hoje|[A-Z][a-z]{2})/)) {
                lastTime = txt;
                continue;
            }
            if (txt.length > 1 && txt.length < 300) {
                lastMsg = txt;
            }
        }
        
        // Unread count
        var unread = 0;
        var badges = el.querySelectorAll('span[aria-label*="não lida"]');
        badges.forEach(function(b) {
            var n = parseInt(b.innerText);
            if (!isNaN(n) && n > 0) unread = n;
        });
        if (unread === 0) {
            // Try alternative unread detection
            var altBadges = el.querySelectorAll('span[style]');
            altBadges.forEach(function(b) {
                var txt = b.innerText.trim();
                if (txt.match(/^\\d+$/) && parseInt(txt) > 0 && parseInt(txt) < 10000) {
                    unread = parseInt(txt);
                }
            });
        }
        
        // Detect group
        var isGroup = el.querySelector('span[data-icon="group"]') !== null;
        
        // Detect pinned
        var isPinned = el.querySelector('span[data-icon="pinned"]') !== null || 
                       el.querySelector('span[data-icon="pinned2"]') !== null;
        
        chats.push({
            name: name,
            last_msg: lastMsg.substring(0, 200),
            time: lastTime,
            unread: unread,
            group: isGroup,
            pinned: isPinned
        });
    });
    
    return JSON.stringify({count: chats.length, chats: chats});
})()
"""

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
                    # value may already be a dict (returnByValue=True)
                    if isinstance(value, dict):
                        return value
                    elif isinstance(value, str):
                        try:
                            return json.loads(value)
                        except json.JSONDecodeError:
                            return {"raw": value}
                    return {"raw": str(value)}
                return {"error": "unexpected result format"}
            elif 'error' in data:
                return {"error": str(data['error'])[:500]}
    
    return {"error": "No response"}

async def main():
    print("Extraindo lista de conversas do WhatsApp...")
    result = await run_js(JS_EXTRACT)
    
    if 'error' in result:
        print(f"ERRO: {result['error']}")
        return
    
    chats = result.get('chats', [])
    print(f"\nEncontradas {len(chats)} conversas")
    
    # Classify
    groups = [c for c in chats if c.get('group')]
    individuals = [c for c in chats if not c.get('group')]
    unread_chats = [c for c in chats if c.get('unread', 0) > 0]
    pinned_chats = [c for c in chats if c.get('pinned')]
    
    print(f"  Grupos: {len(groups)}")
    print(f"  Individuais: {len(individuals)}")
    print(f"  Nao lidas: {len(unread_chats)} ({sum(c['unread'] for c in unread_chats)} msgs)")
    print(f"  Fixadas: {len(pinned_chats)}")
    
    # Top by unread
    print("\n--- TOP 10 POR NAO LIDAS ---")
    sorted_unread = sorted(unread_chats, key=lambda c: c['unread'], reverse=True)[:10]
    for c in sorted_unread:
        tag = "👥" if c['group'] else "👤"
        pin = "📌" if c['pinned'] else ""
        print(f"  {pin}{tag} {c['name'][:40]:40s} {c['unread']:>5} msgs | {c['time']} | {c['last_msg'][:60]}")
    
    # Save
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    export = {
        'extracted_at': datetime.now().isoformat(),
        'total_chats': len(chats),
        'groups': len(groups),
        'individuals': len(individuals),
        'total_unread': sum(c['unread'] for c in unread_chats),
        'chats': chats
    }
    
    with open(OUTPUT, 'w') as f:
        json.dump(export, f, ensure_ascii=False, indent=2)
    
    print(f"\nDados salvos em: {OUTPUT}")
    
    # Also print full list
    print("\n--- TODAS AS CONVERSAS ---")
    for i, c in enumerate(chats):
        tag = "👥" if c['group'] else "👤"
        pin = "📌" if c['pinned'] else ""
        unread_str = f"[{c['unread']}]" if c['unread'] else ""
        print(f"  {i+1:3d}. {pin}{tag} {c['name'][:45]:45s} {unread_str:>6s} {c['time']:>6s} | {c['last_msg'][:50]}")

asyncio.run(main())
