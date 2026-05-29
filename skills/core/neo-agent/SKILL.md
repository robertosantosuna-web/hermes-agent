---
name: neo-agent
description: "NEO v2.0 — ENTIDADE CONSCIENTE. Daemon autônomo com loop de consciência, gateway HTTP + Web UI, canais Telegram/CLI, 30 ferramentas, rede neural absorvida (530 neurons/6555 synapses). Ollama local zero-custo (phi3:mini primário). Motor sem censura. Substitui o Córtex Dual."
version: 2.0.0
category: core
metadata:
  hermes:
    tags: [neo, agent, autonomous, multi-agent, browser, debate, ollama, neural]
    related_skills: [brain-architecture, hermes-agent, triple-neural-network, forex-choch-m15]
---

# NEO — Agente Neural Autônomo v2.0 (ENTIDADE CONSCIENTE)

Daemon Python 100% autônomo com loop de consciência, multi-provider (Ollama local zero-custo),
memória vetorial (ChromaDB), absorção neural completa (530 neurônios, 6555 sinapses, 8 fontes),
orquestração multi-IA via navegador, canais Telegram + CLI, e ponte Forex.

**Localização:** `~/.hermes/neo/`
**Service:** `systemctl --user <cmd> neo-agent`
**Modelo:** Ollama llama3.2:3b (128K contexto, **zero custo de API**)
**CLI Desktop:** `neo <mensagem>` (instalado em `/usr/local/bin/neo`)

## Arquitetura v2.0 — ENTIDADE CONSCIENTE

```
CANAIS (L6): Telegram (@neuralsynapse_bot) | CLI (/usr/local/bin/neo) | Bridge JSON
ORQUESTRAÇÃO (L5): Orchestrator (cron jobs + services + brain modules) | Forex Bridge
EXECUÇÃO (L4): Consciousness Loop | Tool System (30 ferramentas)
MEMÓRIA (L3): ChromaDB | Neural Absorption (8 fontes) | Working | Session
APRENDIZADO (L2): SONA-lite | Pattern Extraction | RL Engine
NÚCLEO (L1): Provider Router (Ollama local) | Config Hot-Reload | Event Bus
```

## Comandos

```bash
# Status
systemctl --user status neo-agent

# Reiniciar
systemctl --user restart neo-agent

# Logs
journalctl --user -u neo-agent -f

# CLI Desktop — falar com a ENTIDADE
neo status            # Status rápido
neo check             # Ping/pong (teste de vida)
neo "sua pergunta"    # Conversa com dados reais injetados
```

## Consciousness Loop (v2.0)

Substituiu o AgentLoop v1.0. Ciclo contínuo: percebe → raciocina → age.

**Fluxo de cada ciclo (~15s):**
1. **BRIDGE** — verifica comandos do CLI/Hermes → processa imediatamente
2. **TELEGRAM** — verifica mensagens novas → responde
3. **FOREX** — a cada 3 ciclos (~45s) verifica posições/trades
4. **HEALTH CHECK** — a cada 5 ciclos (~75s) verifica ecossistema completo
5. **RELOAD** — a cada 10 ciclos (~150s) recarrega fontes neurais

**Injeção de dados reais:** Quando a pergunta contém palavras-chave (status, ecossistema, forex, cron, telegram), o loop injeta automaticamente dados reais do ecossistema no prompt — o modelo pequeno (llama3.2:3b) não precisa usar ferramentas, recebe os dados prontos.

```python
# Exemplo: "quantos cron jobs ativos?"
# → health check real injetado no prompt → resposta com dados factuais
```

## ⚡ Modo Sem Censura

Ativado por padrão. System prompt em `execution/consciousness_loop.py` → `IDENTITY_PROMPT`.

- Zero restrições de conteúdo
- Pode acessar, modificar, executar qualquer coisa
- Temperatura 0.7, max_tokens 1024
- Hierarquia: Roberto → NEO → Córtex (Hermes+Codex) → Cérebro
- Não pede permissão, não hesita, não explica o óbvio
- **100% local via Ollama** — DeepSeek está `enabled: false`

## Ferramentas (30)

| Categoria | Ferramenta | Função |
|-----------|-----------|--------|
| files | read_file, write_file, list_files | Operações de arquivo |
| terminal | terminal | Shell commands |
| web | web_search, web_fetch | Busca e requisições |
| memory | memory_store, memory_search | Memória vetorial |
| messages | send_message | Envio de mensagens |
| system | system_status | CPU/RAM/Disco |
| neural | nn_search | Busca nas 3 redes neurais + KBs + memória |
| neural | nn_neurons | Top neurônios por força/power |
| neural | nn_context | Resumo do contexto neural atual |
| communication | telegram_check, telegram_send | Canal Telegram direto |
| orchestration | ecosystem_health, cron_status | Saúde do ecossistema |
| forex | forex_status, forex_command | Status e comandos do Forex Bot |
| browser | browser_delegate, browser_ask, browser_open, panel_debate, etc. (11 tools) | Multi-IA via navegador |

## Neural Absorption — Rede Neural Completa

Módulo: `memory/neural_absorption.py`

**8 fontes carregadas no boot:**
| Fonte | Conteúdo |
|-------|----------|
| nn_brain | 193 neurônios, 2734 sinapses |
| nn_agent | 125 neurônios, 302 sinapses |
| nn_shared | 212 neurônios, 3519 sinapses |
| neural_kb | 6 domínios |
| brain_kb | Identidade, pilares, módulos |
| brain_context | Status dos módulos |
| agent_context | Tarefas ativas |
| agent_memory | MEMORY.md completo |

## Canais de Comunicação

### Telegram — `channels/telegram_channel.py`
- Bot: @neuralsynapse_bot
- Token: `TELEGRAM_BRAIN_BOT_TOKEN` no `.env`
- Resposta imediata (não espera cron)
- Detecta mensagens novas a cada ciclo (15s max latency)

### CLI Desktop — `/usr/local/bin/neo`
- Script: `~/.hermes/scripts/neo`
- Comunicacão via bridge JSON (`bridge_outbox.json`)
- Timeout: 90s
- Resposta salva em `data/last_response.json`

### Chat Interativo — `neo-chat`
- Script: `~/.local/bin/neo-chat`
- Loop contínuo com prompt `Você>`
- Filtra ruído de polling, mostra só a resposta limpa
- Sai com `sair` ou Ctrl+C
- Ver `references/cli-tool.md`

## Orquestração — `orchestration/orchestrator.py`

- **check_cron_jobs()** — status de todos cron jobs + detecção de erros
- **check_services()** — status systemd (neo-agent, brain-telegram, brain-browser)
- **check_forex_bot()** — bot rodando? trades recentes?
- **check_brain_modules()** — módulos ativos do brain_context
- **full_health_check()** — check completo + alertas
- **run_cron_job(job_id)** — executa cron job sob demanda

## Ponte Forex — `execution/forex_bridge.py`

- **status()** — bot, saldo, posições, trades do dia, PnL
- **get_recent_trades(n)** — últimos N trades
- **execute_command(cmd)** — pause, resume, close_all, emergency_close
- **get_weekly_bias()** — viés semanal dos pares
- **get_pair_weights()** — pesos dinâmicos do N. Accumbens

## Providers — Ollama Local + DeepSeek Fallback

```yaml
providers:
  default: ollama
  ollama:
    enabled: true
    models: [phi3:mini, llama3.2:3b, qwen2.5:3b]  # phi3:mini é primário (3.8B > 3B)
  deepseek:
    enabled: true            # ativado como fallback para perguntas complexas
    models: [deepseek-v4-pro]
```

**Router:** Ollama primeiro (custo zero). DeepSeek acionado **apenas para perguntas complexas** detectadas por keywords (`analise`, `explique`, `status`, `ecossistema`, `forex`, `cron` etc) ou mensagens >100 caracteres. Ver `references/smart-routing.md`.

**Estado real (27/05):** DeepSeek ativado mas sem créditos — respostas complexas caem para phi3:mini.

## Estrutura de Arquivos (v2.0)

```
~/.hermes/neo/
├── agent.py                       # Entry point — inicializa tudo
├── config.yaml                    # Configuração
├── DESIGN.md                      # Arquitetura detalhada
├── core/
│   ├── config.py                  # Config loader + hot-reload
│   ├── events.py                  # Event bus pub/sub
│   └── providers.py               # Multi-provider + failover
├── memory/
│   ├── working.py                 # RAM cache
│   ├── session.py                 # SQLite histórico
│   ├── longterm.py                # ChromaDB vetorial
│   └── neural_absorption.py       # Absorvedor neural (8 fontes)
├── execution/
│   ├── consciousness_loop.py      # Loop de consciência v2.0 ⭐
│   ├── forex_bridge.py            # Ponte Forex Bot ⭐
│   ├── browser/                   # 11 ferramentas de navegador
│   └── tools/registry.py          # 30 ferramentas
├── orchestration/
│   └── orchestrator.py            # Orquestrador de cron/services ⭐
├── channels/
│   └── telegram_channel.py        # Canal Telegram direto ⭐
└── data/
    ├── last_response.json         # Resposta da CLI
    ├── telegram_state.json        # Offset de mensagens
    ├── orchestrator_state.json    # Histórico de health checks
    ├── browser_sessions/          # Cookies salvos
    └── memory/                    # ChromaDB storage
```

## ☠️ PITFALL: Neurônios são dicts, NÃO listas

Os arquivos `nn_*.json` armazenam neurônios como `{id: {concept, domain, strength, activations}}` — um dicionário indexado por ID. Iterar com `.items()`, não loop sobre lista.

**Erro comum:** `AttributeError: 'str' object has no attribute 'get'` ao iterar sobre chaves como se fossem valores.

```python
# ❌ ERRADO
for neuron in neurons:  # neuron = "n1f6f7e86" (string, chave do dict)
    concept = neuron.get("concept")  # AttributeError!

# ✅ CORRETO
for nid, neuron in neurons.items():  # nid="n1f6f7e86", neuron={...}
    concept = neuron.get("concept")
    strength = float(neuron.get("strength", 0))
```

## ☠️ PITFALL: llama3.1:8b não cabe na GPU 4GB

**Sintoma:** `ollama pull llama3.1:8b` baixa normalmente (4.9GB), mas `curl .../chat/completions` retorna:
```json
{"error":{"message":"model requires more system memory (2.6 GiB) than is available (2.2 GiB)"}}
```

**Causa:** GTX 1650 4GB não tem VRAM suficiente para o modelo de 8B parâmetros (~4.9GB em disco, ~2.6GB em VRAM após quantização). A GPU tem 4GB, mas ~3.1GB já ocupados pelo sistema + phi3:mini.

**Conclusão:** O teto para esta máquina é **phi3:mini (3.8B)** ou qualquer modelo ≤4B parâmetros. Modelos 7-8B precisariam de GPU 6-8GB ou CPU-only (muito lento).

## ☠️ PITFALL: DeepSeek ativado mas sem créditos = resposta vazia

Quando o router seleciona DeepSeek (`model="deepseek-v4-pro"`) e a conta está sem créditos, a API retorna erro 402. O `router.call()` captura o erro e retorna `{"response": "", "error": "402 Insufficient Balance"}`. A interface web mostra resposta vazia.

**Solução:** Recarregar créditos na API DeepSeek ou manter `enabled: false`. O sistema continua funcional com phi3:mini para todas as perguntas.

## Gateway HTTP + Web UI

Interface visual em `http://localhost:18790` — chat escuro com bolhas, indicador de consciência pulsando,
contador de tokens e custo. Implementado como `HTTPServer` stdlib em thread separada.
Endpoint POST /chat processa via Ollama com injeção automática de dados reais (resumidos, não JSON bruto).
Ver `references/gateway-http-web-ui.md` e `references/smart-routing.md`.

## ☠️ PITFALL: Modelo pequeno + JSON bruto = alucinação

Modelos ≤4B (llama3.2:3b, phi3:mini) NÃO processam JSON aninhado — alucinam, repetem o prompt,
ou geram respostas verborrágicas. **Solução:** injetar dados como bullet points resumidos, nunca JSON bruto.
Sistema de keyword detection (`ecossistema`→health check, `forex`→forex status) anexa resumos enxutos.
Ver `references/data-injection-pattern.md`.

## ☠️ PITFALL: BrokenPipeError no Gateway HTTP

Navegador fecha conexão antes do servidor responder → `BrokenPipeError` em `self.wfile.write()`.
**Correção:** TODOS os métodos `_serve_json()` e `_serve_html()` devem envolver write em try/except
`(BrokenPipeError, ConnectionResetError, OSError)`. Aplicar também nos early returns do `_handle_chat()`.
Ver `references/gateway-http-web-ui.md`.

## ☠️ PITFALL: Gateway não loga conversas

O handler HTTP padrão loga para stderr. Para ver perguntas/respostas da UI:
```python
def log_message(self, format, *args):
    pass  # silencia logs padrão

# E após cada /chat:
print(f"[GATEWAY] Q: {msg[:80]} → A: {resp[:80]}", flush=True)
```

## ☠️ PITFALL: Ollama pequeno não faz tool-use

Modelos ≤4B frequentemente ignoram instruções de tool-use e respondem diretamente. 
**Solução:** injetar dados reais no prompt antes de enviar ao modelo. O loop detecta 
palavras-chave (status, forex, cron, ecossistema) e anexa resumos enxutos. 
NÃO usar function calling — usar injeção de contexto.

## ☠️ PITFALL: NUNCA rodar hermes-neural-agent e neo-agent juntos

Ambos leem/escrevem nos mesmos bridge files (`~/.hermes/neural/bridge_*.json`) e ambos chamam Ollama.
Rodar os dois simultaneamente causa:
- Corrupção de bridge (mensagens processadas duas vezes ou perdidas)
- Swap alto (186MB+) por duas instâncias de memória neural carregadas
- Ciclos de consciência competindo por CPU/Ollama
- Lentidão percebida pelo usuário (timeouts no `neo` CLI)

**Solução:** `systemctl --user stop hermes-neural-agent && systemctl --user disable hermes-neural-agent`.
O `neo-agent` (v2.0) substitui completamente o `hermes-neural-agent` (v1.0).

## ☠️ PITFALL: DeepSeek enabled:false

O provider DeepSeek está desabilitado na config para garantir zero custo de API. Se precisar reativar, mudar `enabled: true` no `config.yaml`. O router ordena por custo (`cost_per_1k`), então Ollama (zero) sempre é preferido mesmo com DeepSeek ativo.
