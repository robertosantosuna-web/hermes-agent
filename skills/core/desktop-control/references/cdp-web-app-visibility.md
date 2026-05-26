# CDP Web App Visibility Pattern

**Problema:** GNOME 50.1 Wayland bloqueia screenshots de apps nativos. mss captura tela 100% preta.

**Solução:** Usar a versão WEB do app no Brave + CDP na porta 9222 (Brave real do usuário).

## Padrão

```
App Desktop (invisível) → App Web no Brave → CDP (porta 9222)
                                                   ├─ Runtime.evaluate → ler DOM
                                                   ├─ Page.captureScreenshot → ver tela
                                                   └─ document.body.innerText → extrair texto
```

## Como usar

```python
import json, urllib.request, websocket, base64

# 1. Listar abas
tabs = json.loads(urllib.request.urlopen('http://localhost:9222/json/list').read())

# 2. Encontrar aba do app web
tab = [t for t in tabs if 'web.telegram.org' in t.get('url','')][0]
ws_url = tab['webSocketDebuggerUrl']

# 3. Conectar e extrair texto
ws = websocket.create_connection(ws_url, timeout=15)
ws.send(json.dumps({"id":1, "method":"Runtime.evaluate",
    "params": {"expression": "document.body.innerText", "returnByValue": True}}))
resp = json.loads(ws.recv())
text = resp['result']['result']['value']

# 4. Screenshot (se modelo tiver visão)
ws.send(json.dumps({"id":2, "method":"Page.captureScreenshot", "params":{"format":"png"}}))
resp = json.loads(ws.recv())
png = base64.b64decode(resp['result']['data'])
```

## Apps mapeados

| App Desktop | Versão Web | Porta CDP |
|------------|-----------|-----------|
| Telegram | web.telegram.org/k/ | 9222 (Brave real) |
| WhatsApp | web.whatsapp.com | 9222 |
| Gmail | mail.google.com | 9222 ou 9224 (Edge) |
| TradingView | tradingview.com/chart | 9223 (Brain Browser) |

## Interação mista

Para apps com anti-bot (Cloudflare Turnstile, PerimeterX):
- **LER:** CDP na versão web (Runtime.evaluate, DOM)
- **DIGITAR/CLICAR:** Desktop Daemon + ydotool no app real (kernel-level input)

NUNCA tentar input via CDP em React SPAs — o React rejeita valores programáticos.
