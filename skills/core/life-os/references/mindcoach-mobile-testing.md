# MindCoach Mobile Testing via CDP

Como testar o app MindCoach em viewport mobile sem emulador Android.
Usa o Brave real na porta 9222 com device metrics override.

## Script de teste

```python
import json, time, urllib.request, websocket, base64

BASE = 'http://localhost:9222'

# Abrir o app (com cache-bust ?v=N)
url = 'https://mindcoach-541659260074.us-central1.run.app?v=29'
req = urllib.request.Request(f'{BASE}/json/new?{url}', method='PUT')
tab = json.loads(urllib.request.urlopen(req, timeout=15).read())
ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=15)

mid = [0]
def cdp(method, params=None):
    mid[0] += 1
    ws.send(json.dumps({'id': mid[0], 'method': method, 'params': params or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get('id') == mid[0]:
            return r.get('result', {})

# Pixel 6 viewport
cdp('Emulation.setDeviceMetricsOverride', {
    'width': 412, 'height': 915,
    'deviceScaleFactor': 2.5,
    'mobile': True,
    'screenOrientation': {'type': 'portraitPrimary', 'angle': 0}
})
cdp('Emulation.setUserAgentOverride', {
    'userAgent': 'Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
})
cdp('Page.enable')
cdp('Runtime.enable')
time.sleep(3)

# Verificar estado
info = cdp('Runtime.evaluate', {'expression': '''
(() => {
    const r = {};
    r.version = document.getElementById('app-version')?.textContent || 'MISSING';
    r.dock = !!document.getElementById('dock');
    ['dock-auth','dock-painel','dock-chat'].forEach(id => {
        const el = document.getElementById(id);
        r[id] = el ? 'present' : 'MISSING';
    });
    r.sendChatDefined = typeof sendChat === 'function';
    r.vp = `${window.innerWidth}x${window.innerHeight}`;
    return JSON.stringify(r, null, 2);
})()''', 'returnByValue': True})
print(info.get('result',{}).get('value','{}'))

# Screenshot
result = cdp('Page.captureScreenshot', {'format': 'png'})
with open('/tmp/mindcoach_test.png', 'wb') as f:
    f.write(base64.b64decode(result['data']))

ws.close()
```

## Checklist de verificação

- [ ] Versão visível no topo direito (v29+)
- [ ] Dock bar visível com 3 ícones (🔐 📊 💬)
- [ ] `sendChat` definida como função global
- [ ] `toggleChat` e `toggleAuth` definidas
- [ ] Chat abre e envia mensagens
- [ ] Auth panel lista solicitações
- [ ] Nenhum `#bubble`, `#chat-bubble`, ou `#auth-bubble` no DOM (removidos)

## Pitfalls

- Sempre usar `?v=N` na URL para bypassar cache do Brave
- Viewport 412×915 = Pixel 6 (bom meio-termo mobile)
- O CDP na porta 9222 é o Brave real do Roberto (Wayland)
- A porta 9223 é headless (offline frequentemente)
