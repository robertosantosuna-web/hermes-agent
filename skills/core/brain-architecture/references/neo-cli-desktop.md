# NEO CLI & Desktop Interface (27/05/2026)

Comando `neo` para interagir com a ENTIDADE via terminal e navegador.

## CLI — Comandos

```bash
neo status           # Status do NEO (ativo? últimos logs)
neo check            # Ping/pong rápido (~15s)
neo "mensagem"       # Envia pergunta, aguarda resposta (timeout 90s)
neo interface        # Abre chat web em http://localhost:18790
neo chat             # Atalho para interface
```

**Instalação:** `sudo ln -sf ~/.hermes/scripts/neo /usr/local/bin/neo`

**Funcionamento:** Escreve no `bridge_outbox.json` (Hermes→NEO). Loop de consciência lê a cada ~15s, processa via Ollama, salva resposta em `neo/data/last_response.json`. CLI faz polling a cada 2s.

**Timeout:** 90s (15s sleep + ~10s Ollama + margem). Se o NEO estiver em cold start (~90s), pode falhar.

## Gateway HTTP — Interface Web

**URL:** `http://localhost:18790`
**Iniciado:** automaticamente no boot do NEO (`neo/channels/gateway.py`)
**Endpoints:**
- `GET /` — Interface HTML (chat escuro, bolhas roxas/escuras, indicador pulsando)
- `GET /health` — `{"status":"conscious","timestamp":"..."}` 
- `POST /chat` — Body: `{"message":"..."}` → resposta JSON

**Roteamento de provider:**
- Perguntas com keywords complexas ("analise", "explique", "ecossistema", "status", "forex", "cron") → DeepSeek V4
- Perguntas simples ("oi", "ok") → Ollama (phi3:mini)
- DeepSeek sem créditos → resposta vazia (sem fallback automático)

**Pitfalls:**
- BrokenPipeError quando navegador fecha conexão cedo — tratado com `try/except (BrokenPipeError, ConnectionResetError, OSError): pass`
- Cold start Ollama ~90s após restart — gateway retorna vazio nas primeiras requisições
- phi3:mini alucina com JSON bruto — sempre resumir dados antes de injetar no prompt
- Módulos Python cacheados — após corrigir bug, precisa reiniciar NEO

## Fluxo de Mensagem (Interface Web)

```
Navegador → POST /chat {"message":"..."}
  → gateway._handle_chat()
    → detecta keywords (ecossistema/forex → injeta dados reais)
    → router.call(prompt, system, model)
      → Ollama (local, grátis) ou DeepSeek (API, fallback)
    → resposta JSON
  → Navegador renderiza bolha
```
