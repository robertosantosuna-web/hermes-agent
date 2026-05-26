# Edge CDP — Messaging Automation (99Freelas)

## Abordagem: WebSocket CDP + JavaScript Evaluation

Usado com sucesso em 20/05/2026 para ler e enviar mensagens no 99Freelas sem Cloudflare.

## Setup

```bash
# Edge já deve estar rodando com --remote-debugging-port=9222
curl http://localhost:9222/json  # confirmar abas
```

## Leitura de Mensagens

```python
import json, websocket, ssl, time

PAGE_ID = "E1E95A2682429C2537C4DDC8145B8FE9"  # da listagem de abas
ws = websocket.create_connection(f"ws://localhost:9222/devtools/page/{PAGE_ID}", timeout=10)

# Extrair DOM
ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {
    "expression": "document.body.innerText.substring(0, 5000)", "returnByValue": True}}))
time.sleep(3)
print(ws.recv())
```

## Envio de Mensagem

```python
# Navegar para conversa específica
ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {
    "url": "https://www.99freelas.com.br/messages/inbox/16525119"}}))
time.sleep(5)

# Digitar no textarea
msg = "Mensagem aqui"
ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {
    "expression": f"var ta=document.querySelector('textarea'); if(ta){{ta.value={json.dumps(msg)};ta.dispatchEvent(new Event('input',{{bubbles:true}}));'ok'}}else{{'no'}}",
    "returnByValue": True}}))
time.sleep(1)

# Enviar (Enter)
ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {
    "expression": "var ta=document.querySelector('textarea'); if(ta){{ta.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',code:'Enter',keyCode:13,bubbles:true}));'sent'}}else{{'no'}}",
    "returnByValue": True}}))
```

## PITFALLS

- A conversa precisa estar ATIVA (clicada) antes de digitar. Usar `Page.navigate` para a URL específica da conversa.
- `websocket-client` library (import `websocket`, minúsculo) — NÃO `websockets` (com 's').
- Upload de arquivo (`DOM.setFileInputFiles`) não funciona no 99Freelas (input dinâmico). Anexar requer clique humano.
- Screenshots via `Page.captureScreenshot` funcionam no Wayland.

## Alternativa: playwright connect_over_cdp

```python
from playwright.async_api import async_playwright

async def read_messages():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        for page in browser.contexts[0].pages:
            if "99freelas" in page.url:
                text = await page.inner_text("body")
                print(text[:3000])
        await browser.close()
```

Playwright é mais ergonômico mas tem timeout em SPAs pesadas (>5000 nós DOM).
