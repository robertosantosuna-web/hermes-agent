# Extração de Conteúdo de Abas CDP (28/05/2026)

Técnica usada para extrair textos das 4 abas do Edge (DeepSeek, Grok, Gemini, ChatGPT)
sem depender de screenshots + OCR.

## Método: Runtime.evaluate com innerText

Conectar ao CDP endpoint (porta 9225 no Edge), listar abas, e extrair texto:

```python
import json, urllib.request

# 1. Listar abas
with urllib.request.urlopen("http://localhost:9225/json") as f:
    tabs = json.loads(f.read())

# 2. Para cada aba, extrair innerText
for tab in tabs:
    ws_url = tab['webSocketDebuggerUrl']
    # Conectar via WebSocket e enviar:
    # {"id":1,"method":"Runtime.evaluate","params":{"expression":"document.body.innerText","returnByValue":true}}
```

## Pitfalls

- **ChatGPT bloqueia CDP injection** — a interface do ChatGPT usa iframes e Shadow DOM que não expõem `innerText`. O texto não foi extraível por CDP; foi necessário colar manualmente.
- **DeepSeek, Grok, Gemini funcionam** — `document.body.innerText` retorna o texto visível.
- **WebSocket necessário** — `browser_cdp` do Hermes não suporta WebSocket persistente. Para este caso, usei Python direto com `websockets` library.

## Alternativa testada (Edge sidebar)

Edge na porta 9225 tem um tab de "sidebar" que lista as abas abertas. Usar `browser_cdp` para isso funcionou para as 3 que retornaram texto (DeepSeek, Grok, Gemini).

## Uso futuro

Sempre que precisar extrair conteúdo de abas abertas no Edge (porta 9225), usar:
1. `browser_cdp(method="Target.getTargets")` para listar
2. `browser_cdp(method="Runtime.evaluate", params={"expression": "document.body.innerText", "returnByValue": true}, target_id=id)` para extrair
3. Se falhar (ChatGPT/SPA complexas): pedir ao usuário para colar o texto
