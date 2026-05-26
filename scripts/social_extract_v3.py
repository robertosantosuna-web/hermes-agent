#!/usr/bin/env python3
"""Extract WhatsApp chat data v3 - working selectors."""
import asyncio, json, urllib.request, websockets, sys, os, re
from datetime import datetime
from collections import Counter

CDP = 'http://localhost:9224'
OUTPUT_DIR = os.path.expanduser('~/.hermes/data/social')
OUTPUT = os.path.join(OUTPUT_DIR, 'whatsapp_chats.json')

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
                        try:
                            return json.loads(value)
                        except:
                            return {"raw_value": value[:500]}
                return {"unknown": str(result)[:500]}
            elif 'error' in data:
                return {"error": str(data['error'])[:500]}
    return {"error": "no response"}

async def main():
    print("🔍 Extraindo metadados das conversas WhatsApp...")
    
    # Extract using working selectors
    js = """
    (function() {
        var pane = document.querySelector('#pane-side');
        if (!pane) return JSON.stringify({error: 'pane not found'});
        
        var rows = pane.querySelectorAll('[role="row"]');
        var chats = [];
        
        rows.forEach(function(row) {
            var text = row.innerText;
            
            // Get name from span[title] (first one)
            var titleSpans = row.querySelectorAll('span[title]');
            var name = '';
            for (var i = 0; i < titleSpans.length; i++) {
                var t = titleSpans[i].getAttribute('title').trim();
                // Skip LTR marks and empty
                t = t.replace(/[\\u200e\\u200f]/g, '').trim();
                if (t.length > 1 && t.length < 60) {
                    name = t;
                    break;
                }
            }
            
            if (!name) return;
            
            // Extract unread count
            var unread = 0;
            var unreadMatch = text.match(/(\\d+)\\s*mensagens?\\s*n[aã]o\\s*lidas?/i);
            if (unreadMatch) unread = parseInt(unreadMatch[1]);
            
            // Extract time (HH:MM pattern)
            var time = '';
            var timeMatch = text.match(/(\\d{1,2}:\\d{2})\\s*$/m);
            if (timeMatch) time = timeMatch[1];
            
            // Extract last message (between time and name, roughly)
            var lines = text.split('\\n').filter(function(l) { return l.trim(); });
            var lastMsg = '';
            // Find the line that's not the name, not the time, not unread count
            for (var j = lines.length - 1; j >= 0; j--) {
                var line = lines[j].trim();
                if (line === name) continue;
                if (line === time) continue;
                if (line.match(/^\\d+\\s*mensagens?\\s*n[aã]o\\s*lidas?/i)) continue;
                if (line.match(/^~\\w/)) continue; // author prefix
                if (line.match(/^\\d{1,2}:\\d{2}$/)) continue;
                if (line === ':' || line === ' ') continue;
                if (line.match(/^Ligação/)) { lastMsg = line; break; }
                lastMsg = line;
                break;
            }
            
            // Detect group
            var isGroup = row.querySelector('span[data-icon="group"]') !== null;
            
            // Detect archived
            var isArchived = false;
            // Check if parent has archived-related class
            
            chats.push({
                name: name,
                unread: unread,
                time: time,
                last_msg: lastMsg.substring(0, 200),
                group: isGroup
            });
        });
        
        return JSON.stringify({count: chats.length, chats: chats});
    })()
    """
    
    result = await run_js(js)
    
    if 'error' in result:
        print(f"❌ ERRO: {result['error']}")
        return
    
    chats = result.get('chats', [])
    count = result.get('count', len(chats))
    
    print(f"\n📊 {count} conversas extraídas\n")
    
    # === CLASSIFICATION ===
    groups = [c for c in chats if c.get('group')]
    individuals = [c for c in chats if not c.get('group')]
    
    # Match known categories
    family_names = ['pai', 'mãe', 'mae', 'tia', 'tio', 'vó', 'vo', 'vô', 'primo', 'prima', 
                    'irmã', 'irma', 'irmão', 'irmao', 'sobrinho', 'sobrinha', 'filho', 'filha',
                    'tamires', 'thais', 'janaína', 'janaina', 'pati']
    
    work_names = ['oficina', 'freela', 'cliente', 'trabalho', 'projeto', 'serviço', 'servico',
                  '99', 'workana', 'fiverr']
    
    for c in chats:
        name_lower = c['name'].lower()
        c['category'] = 'social'
        if c.get('group'):
            c['category'] = 'grupo'
        if any(fn in name_lower for fn in family_names):
            c['category'] = 'familia'
        if any(wn in name_lower for wn in work_names):
            c['category'] = 'trabalho'
        if any(kw in name_lower for kw in ['promo', 'venda', 'loja', 'oferta', 'cupom', 'desconto']):
            c['category'] = 'comercial'
        if any(kw in name_lower for kw in ['igreja', 'cura', 'church', 'jesus', 'deus', 'fe']):
            c['category'] = 'religiao'
    
    cat_counts = Counter(c['category'] for c in chats)
    
    print("=== DISTRIBUICAO POR CATEGORIA ===")
    for cat, n in cat_counts.most_common():
        bar = '█' * (n // 2)
        print(f"  {cat:15s} {n:3d} {bar}")
    
    print(f"\n=== TOP 15 POR NAO LIDAS ===")
    top_unread = sorted(chats, key=lambda c: c.get('unread', 0), reverse=True)[:15]
    for c in top_unread:
        tag = "👥" if c.get('group') else "👤"
        cat = c.get('category', '?')
        print(f"  {tag} [{cat:10s}] {c['name'][:40]:40s} {c.get('unread',0):>5} | {c.get('time','?'):>5s} | {c.get('last_msg','')[:55]}")
    
    print(f"\n=== TODAS AS CONVERSAS (ordenado por nao lidas) ===")
    sorted_chats = sorted(chats, key=lambda c: c.get('unread', 0), reverse=True)
    for i, c in enumerate(sorted_chats):
        tag = "👥" if c.get('group') else "👤"
        cat = c.get('category', '?')
        unread_str = f"[{c.get('unread')}]" if c.get('unread') else ""
        print(f"  {i+1:3d}. {tag} [{cat:10s}] {c['name'][:42]:42s} {unread_str:>7s} {c.get('time','?'):>6s} | {c.get('last_msg','')[:50]}")
    
    # === FINANCIAL ANALYSIS ===
    print(f"\n=== METRICAS DE ENGAJAMENTO ===")
    total_unread = sum(c.get('unread', 0) for c in chats)
    chats_with_unread = [c for c in chats if c.get('unread', 0) > 0]
    
    print(f"  Total mensagens nao lidas: {total_unread}")
    print(f"  Conversas com pendencia: {len(chats_with_unread)}/{len(chats)}")
    print(f"  Media nao lidas/chat: {total_unread/max(len(chats),1):.1f}")
    
    # Conversation neglect score (chats with high unread that aren't groups)
    neglected = [c for c in chats_with_unread if not c.get('group') and c.get('unread', 0) > 10]
    if neglected:
        print(f"\n  ⚠️ CONVERSAS INDIVIDUAIS NEGLIGENCIADAS (>10 nao lidas):")
        for c in sorted(neglected, key=lambda c: c['unread'], reverse=True):
            print(f"     {c['name'][:40]:40s} {c['unread']} msgs")
    
    # Save data
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    export = {
        'extracted_at': datetime.now().isoformat(),
        'total_chats': count,
        'categories': dict(cat_counts),
        'total_unread': total_unread,
        'chats_with_unread': len(chats_with_unread),
        'chats': sorted_chats
    }
    
    with open(OUTPUT, 'w') as f:
        json.dump(export, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Dados salvos: {OUTPUT}")

asyncio.run(main())
