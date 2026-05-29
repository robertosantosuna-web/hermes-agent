# CDP Prompt Submission to AI Services (ChatGPT, Gemini, DeepSeek, Grok)

Técnica validada 28/05/2026 para enviar prompts longos para IAs via CDP sem interação manual.

## Pitfall: json/new?url= NÃO funciona

`curl -X PUT 'http://localhost:9225/json/new?url=https://chatgpt.com'` cria a aba mas IGNORA a URL — abre `about:blank`.
Solução: criar aba vazia + navegar via `Page.navigate` no WebSocket.

## Fluxo correto (validado 28/05)

```python
import json, asyncio
from websockets import connect

async def send_prompt_to_ia(name, url, prompt_text):
    # 1. Criar aba vazia
    r = subprocess.run(['curl', '-s', '-X', 'PUT', f'http://localhost:{PORT}/json/new'],
        capture_output=True, text=True)
    tab = json.loads(r.stdout)
    
    async with connect(tab['webSocketDebuggerUrl']) as ws:
        # 2. Navegar
        await ws.send(json.dumps({"id":1,"method":"Page.enable"}))
        await asyncio.sleep(0.3)
        await ws.send(json.dumps({"id":2,"method":"Page.navigate","params":{"url":url}}))
        
        # 3. Aguardar Page.loadEventFired
        for _ in range(40):
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            if json.loads(resp).get("method") == "Page.loadEventFired":
                break
        
        await asyncio.sleep(3)  # Tempo extra para SPA renderizar
        
        # 4. Preencher textarea com native value setter
        js = f"""
        (function() {{
            var el = document.querySelector('textarea, #prompt-textarea, div[contenteditable="true"]');
            if (!el) return 'NO ELEMENT';
            var msg = {json.dumps(prompt_text)};
            if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {{
                var ns = Object.getOwnPropertyDescriptor(
                    window.HTMLTextAreaElement.prototype, 'value'
                )?.set;
                if (ns) ns.call(el, msg);
                else el.value = msg;
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
            }} else {{
                el.innerText = msg;
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
            }}
            return 'OK:' + el.tagName;
        }})()
        """
        
        await ws.send(json.dumps({"id":1,"method":"Runtime.evaluate",
            "params":{"expression":js,"returnByValue":True}}))
        
        # 5. Enter para enviar
        await ws.send(json.dumps({"id":2,"method":"Input.dispatchKeyEvent",
            "params":{"type":"keyDown","key":"Enter","code":"Enter","windowsVirtualKeyCode":13}}))
        await ws.send(json.dumps({"id":3,"method":"Input.dispatchKeyEvent",
            "params":{"type":"keyUp","key":"Enter","code":"Enter","windowsVirtualKeyCode":13}}))
```

## Seletor por plataforma

| Plataforma | Seletor | Notas |
|-----------|---------|-------|
| ChatGPT | `#prompt-textarea` ou `textarea` | SPA React |
| Gemini | `div[contenteditable="true"]` | Rich text editor |
| DeepSeek | `textarea` | Simples |
| Grok | `textarea[placeholder*="Ask"]` | Pode resetar após envio |

## Extrair resposta (após aguardar 30-90s)

```python
await ws.send(json.dumps({"id":1,"method":"Runtime.evaluate",
    "params":{"expression":"""
        (function() {
            var articles = document.querySelectorAll('article');
            if (articles.length > 0) {
                return articles[articles.length - 1].innerText.substring(0, 6000);
            }
            return document.body ? document.body.innerText.substring(0, 4000) : '';
        })()
    ""","returnByValue":True}}))
```

## Pitfalls

- **Grok reseta a página após envio** — o prompt some e volta pra tela inicial. Usar aba de conversa existente (com `/c/...` na URL) em vez de nova conversa.
- **Timing**: Aguardar 3-5s após load para SPAs React renderizarem o textarea.
- **Headless vs real**: Chromium headless (:9226) pode não renderizar SPAs corretamente. Edge/Brave reais (:9222/:9225) são mais confiáveis.
- **Múltiplos envios**: Se houver múltiplas abas da mesma IA, o seletor sem filtro pode pegar a aba errada. Filtrar por URL/título.
