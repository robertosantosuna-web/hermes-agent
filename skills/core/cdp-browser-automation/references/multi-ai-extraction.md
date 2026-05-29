# Multi-AI CDP Extraction Pattern (28/05/2026)

## Use Case
Consultar múltiplas IAs (Gemini, DeepSeek, ChatGPT, Grok) em paralelo sobre o mesmo prompt, extrair respostas via CDP, e encontrar convergência entre elas para code review ou decisões.

## Setup
1. Abrir cada IA em uma aba separada no Edge (:9225)
2. Colar o mesmo prompt em cada aba
3. Aguardar respostas
4. Extrair via CDP WebSocket

## Extração

```python
import json, asyncio
from websockets import connect  # pip install websockets

TABS = {
    "Gemini":   "TARGET_ID_FROM_/json",
    "DeepSeek": "TARGET_ID_FROM_/json", 
    "ChatGPT":  "TARGET_ID_FROM_/json",
    "Grok":     "TARGET_ID_FROM_/json",
}

async def extract_one(ws_url):
    async with connect(ws_url, close_timeout=5) as ws:
        msg = json.dumps({
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": "document.body.innerText",
                "returnByValue": True
            }
        })
        await ws.send(msg)
        resp = await asyncio.wait_for(ws.recv(), timeout=8)
        data = json.loads(resp)
        return data.get("result", {}).get("result", {}).get("value", "")

async def main():
    for name, tid in TABS.items():
        ws_url = f"ws://localhost:9225/devtools/page/{tid}"
        text = await extract_one(ws_url)
        print(f"\n{'='*60}\n{name} ({len(text)} chars)\n{'='*60}")
        print(text[:3000])

asyncio.run(main())
```

## Listar abas primeiro
```bash
curl -s http://localhost:9225/json | python3 -c "
import sys, json
for t in json.load(sys.stdin):
    if t['type'] == 'page':
        print(f\"{t['id']} | {t['title'][:80]} | {t['url'][:100]}\")
"
```

## Análise de Convergência
Após extrair todas as respostas:
1. Identificar pontos onde TODAS as IAs concordam → **aplicar imediatamente**
2. Pontos onde 3/4 concordam → **aplicar com cautela**
3. Pontos onde só 1 menciona → considerar contexto

## Pitfalls
- `browser_cdp` usa porta configurada (9223) — para Edge (9225), usar WebSocket direto
- `document.body.innerText` inclui sidebar/navegação — filtrar pelo conteúdo relevante
- Algumas IAs têm limite de resposta — prompt muito longo pode truncar
- `websockets` precisa ser instalado: `pip install websockets`
