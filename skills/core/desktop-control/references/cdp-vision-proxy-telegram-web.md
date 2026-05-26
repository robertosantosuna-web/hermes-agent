# CDP Vision Proxy — Telegram Web K (25/05/2026)

## Problema

GNOME 50.1 Wayland bloqueia TODA captura programática de tela:
- mss (XWayland): tela 100% preta
- grim: wlr-screencopy não suportado
- GNOME D-Bus: AccessDenied
- gnome-screenshot: crash

## Solução: CDP Vision Proxy

Abrir o app como versão WEB no Brave (porta 9222) e usar CDP para "ver" a tela:

```python
# "Ver" a tela sem screenshot
cdp("Runtime.evaluate", {
    "expression": "document.body.innerText",
    "returnByValue": True
})
# → retorna TODO o texto visível na página
```

## Apps validadas com esta técnica

| App | URL | Funciona? |
|-----|-----|-----------|
| Telegram Web K | `web.telegram.org/k/` | ✅ |
| Telegram Web A | `web.telegram.org/a/` | ✅ |
| WhatsApp Web | `web.whatsapp.com` | ✅ (Edge :9224) |
| Gmail | `mail.google.com` | ✅ |
| Google Calendar | `calendar.google.com` | ✅ |

## Digitação em campos contenteditable (Telegram Web K)

### ❌ NÃO FUNCIONA
```javascript
editable.textContent = '/newbot'
editable.dispatchEvent(new InputEvent('input', {...}))
// → Mensagem fica como "Draft", nunca é enviada
```

### ✅ FUNCIONA — Input.dispatchKeyEvent do CDP
```python
# Digitar caractere por caractere via CDP (kernel-level)
for char in "Hermes Brain":
    cdp("Input.dispatchKeyEvent", {
        "type": "char",
        "text": char,
        "unmodifiedText": char
    })
    time.sleep(0.03)  # delay mínimo entre chars

# Enter
cdp("Input.dispatchKeyEvent", {
    "type": "keyDown", "key": "Enter", "code": "Enter",
    "keyCode": 13, "windowsVirtualKeyCode": 13
})
cdp("Input.dispatchKeyEvent", {
    "type": "keyUp", "key": "Enter", "code": "Enter",
    "keyCode": 13, "windowsVirtualKeyCode": 13
})
```

## WebSocket CDP helper (port 9222 = Brave real)

```python
import json, urllib.request, websocket

def cdp(method, params=None):
    # Pegar aba desejada
    tabs = json.loads(urllib.request.urlopen('http://localhost:9222/json/list').read())
    tab = next(t for t in tabs if 'web.telegram.org' in t.get('url',''))
    
    ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=15)
    ws.send(json.dumps({"id": 1, "method": method, "params": params or {}}))
    resp = json.loads(ws.recv())
    ws.close()
    return resp
```

## Navegação direta (sem passar pela UI)

```python
# Abrir nova aba direto no @BotFather
req = urllib.request.Request(
    'http://localhost:9222/json/new?https://web.telegram.org/k/%23@BotFather',
    method='PUT'
)
tab = json.loads(urllib.request.urlopen(req).read())
```

## Caso de uso real

Criação do @HermesEntidadeBot via @BotFather no Telegram Web K:
1. Abrir `web.telegram.org/k/#@BotFather` no Brave :9222
2. Enviar `/newbot` via Input.dispatchKeyEvent
3. Digitar nome "Hermes Brain" char por char
4. Digitar username "HermesEntidadeBot" char por char
5. Capturar token da resposta via `document.body.innerText`
6. Salvar em `~/.hermes/.env` como `TELEGRAM_BRAIN_BOT_TOKEN`
