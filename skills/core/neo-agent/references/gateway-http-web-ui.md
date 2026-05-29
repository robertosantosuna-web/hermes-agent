# Gateway HTTP + Web UI

## Smart Routing

O gateway decide qual provider usar por keyword detection. Ver `references/smart-routing.md`.

## Arquitetura

O gateway é um `HTTPServer` Python stdlib rodando em thread separada na porta 18790.
Serve uma SPA HTML com chat visual e processa POST /chat via Ollama.

```
Navegador → GET / → CHAT_HTML (SPA)
Navegador → POST /chat {"message":"..."} → router.call() → Ollama → JSON response
```

## Endpoints

| Método | Path | Função |
|--------|------|--------|
| GET | / | Chat UI HTML |
| GET | /health | `{"status":"conscious"}` |
| POST | /chat | `{"message":"..."}` → `{"response":"...", "tokens":N}` |

## Fluxo do POST /chat

1. Parser JSON do body
2. Detecta keywords na pergunta (ecossistema, forex, cron, telegram)
3. Se relevante → injeta dados reais RESUMIDOS (bullets, não JSON)
4. System prompt enxuto (~200 chars) com identidade
5. router.call() → Ollama (phi3:mini ou llama3.2:3b)
6. Retorna JSON com resposta + metadados

## Pitfalls

### BrokenPipeError
**Causa:** Navegador fecha conexão durante processamento (refresh, pre-flight, timeout).
**Sintoma:** `BrokenPipeError: [Errno 32] Broken pipe` em `self.wfile.write()`.
**Correção:** TODOS os `_serve_json()` e `_serve_html()` devem ter try/except:

```python
def _serve_json(self, data):
    try:
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass  # Cliente já fechou, ignora
```

### Gateway não loga
O handler padrão do Python `BaseHTTPRequestHandler` loga para stderr. Para silenciar:
```python
def log_message(self, format, *args):
    pass
```

Para debugar conversas da UI, adicionar print após cada /chat:
```python
print(f"[GATEWAY] Q: {msg[:80]} → A: {resp[:80]}", flush=True)
```
