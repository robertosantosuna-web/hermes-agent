# Edge CDP — Extração de Conversas 99Freelas

## Técnica descoberta 20/05/2026

Quando `Runtime.evaluate` com `document.body.innerText` trunca a conversa (scroll não carregou), usar:

### Fallback 1: Click na conversa + scroll

```python
# Clicar no item da conversa
ws.send(json.dumps({
    "id": 1, "method": "Runtime.evaluate",
    "params": {"expression": """
        (() => {
            let items = document.querySelectorAll('[class*=conversation], [class*=thread], li');
            for (let el of items) {
                if (el.innerText.includes('NOME_DO_CLIENTE')) {
                    el.click(); return 'clicked';
                }
            }
            return 'not found';
        })()
    """, "returnByValue": True}
}))

time.sleep(4)

# Scroll no painel de mensagens
ws.send(json.dumps({
    "id": 2, "method": "Runtime.evaluate",
    "params": {"expression": """
        let panel = document.querySelector('[class*=chat], [class*=conversation-view]');
        if (panel) panel.scrollTop = 0; // topo = mais recente
        'scrolled'
    """, "returnByValue": True}
}))
```

### Fallback 2: Screenshot + OCR

Quando o DOM não revela o texto completo (React virtualized, lazy loading):

```python
ws.send(json.dumps({
    "id": 3, "method": "Page.captureScreenshot",
    "params": {"format": "png"}
}))

# Decodificar e salvar
import base64
resp = json.loads(ws.recv())
img_data = base64.b64decode(resp['result']['data'])
with open('/tmp/conversa.png', 'wb') as f:
    f.write(img_data)

# OCR via vision_engine
import subprocess
r = subprocess.run(
    ['~/.hermes/scripts/vision_engine.py', 'ocr_only', '--image', '/tmp/conversa.png', '--lang', 'por'],
    capture_output=True, text=True
)
text = json.loads(r.stdout)['text']
```

### Lição: Nunca pedir senha

Se o Edge CDP (:9222) está rodando com cookies ativos, SEMPRE usar CDP primeiro. Só pedir credenciais se:
1. CDP não está rodando (porta 9222 fechada)
2. Nenhuma página tem cookies válidos (session expired)
3. Cloudflare Turnstile bloqueia até com cookies

Verificar com: `curl -s http://localhost:9222/json | jq '.[] | {title, url}'`
