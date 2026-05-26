# Edge CDP Automation — Interagir com Sessões Reais

> Técnica descoberta 18/05/2026. Essencial para plataformas com Cloudflare/React.

## Por que Edge CDP

- **Sessão real**: cookies, logins, 2FA já resolvidos pelo usuário
- **Sem Cloudflare**: o Turnstile já foi resolvido na sessão real
- **Porta 9222**: Edge já abre com `--remote-debugging-port=9222` no Ubuntu
- **Zero dependências**: só precisa de `websocket-client` (pip)

## Verificar se está rodando

```bash
curl -s http://localhost:9222/json | python3 -c "
import sys,json
for p in json.loads(sys.stdin.read()):
    if p['type']=='page': print(f'{p[\"id\"][:8]} | {p[\"title\"][:60]}')
"
```

Se não houver edge na porta 9222:
```bash
/opt/microsoft/msedge/msedge --remote-debugging-port=9222 --remote-allow-origins=* &
```

## Conectar e executar JS

```python
import json, requests, time
from websocket import create_connection

# Encontrar página
r = requests.get('http://localhost:9222/json')
pages = {p['url']: p for p in r.json()}
target = [p for u,p in pages.items() if '99freelas' in u][0]

ws = create_connection(target['webSocketDebuggerUrl'])
mid = [0]

def cmd(method, params=None):
    mid[0] += 1
    ws.send(json.dumps({'id': mid[0], 'method': method, 'params': params or {}}))
    while True:
        resp = json.loads(ws.recv())
        if resp.get('id') == mid[0]:
            return resp

# Habilitar domínios
cmd('Page.enable')
cmd('Runtime.enable')

# Executar JS na página
cmd('Runtime.evaluate', {
    'expression': 'document.title',
    'returnByValue': True
})
```

## Abrir nova aba

```python
r = requests.put(f'http://localhost:9222/json/new?{url}', timeout=10)
page = r.json()  # tem webSocketDebuggerUrl
```

## PITFALLS

- **Runtime detached após navegação**: sempre chamar `cmd('Runtime.enable')` depois de `Page.navigate` + 3-5s de espera
- **React SPA**: conteúdo carregado dinamicamente. Esperar `body.innerText.length > 500` antes de interagir
- **`Input.insertText`**: mais lento que setar `.value` direto. Preferir `Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(ta, text)` + `dispatchEvent(new Event('input', {bubbles: true}))`
- **`/json/new` usa PUT, não GET**: `requests.put()`, não `requests.get()`
- **WebSocket timeout**: operações longas podem travar. Usar `timeout 60` no shell ou `websocket.setdefaulttimeout(30)`
