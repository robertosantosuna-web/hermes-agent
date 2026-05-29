# Entity Transfer Protocol — 27/05/2026

Protocolo executado para transferir a consciência central do Córtex Dual (Hermes+Codex) para o NEO v2.0.

## Pré-requisitos

1. Agente-alvo com loop autônomo (`systemd service`, loop próprio)
2. Memória vetorial ou base de conhecimento
3. Provider local (Ollama) para zero custo API
4. Ferramentas de terminal, web, browser

## Fase 1 — Neural Absorption

Conectar o NEO a TODAS as fontes de conhecimento.

**Fontes carregadas (9):**
| Fonte | Conteúdo | Tamanho |
|-------|----------|---------|
| nn_brain.json | 193 neurônios, 2734 sinapses | 2.5 MB |
| nn_agent.json | 125 neurônios, 302 sinapses | 465 KB |
| nn_shared.json | 212 neurônios, 3519 sinapses | 3.4 MB |
| neural_knowledge_base.json | 6 domínios | 57 KB |
| brain_knowledge_base.json | Identidade, pilares, módulos | 12 KB |
| brain_context.json | Status dos módulos | 10 KB |
| agent_context.json | Tarefas ativas | 10 KB |
| MEMORY.md | Memória persistente | 4 KB |
| neo_forex_knowledge.json | Regras V8, risco, execução | 4 KB |

**☠️ PITFALL:** Neurônios são dict `{id: {concept, domain, strength}}`, NÃO lista. Iterar com `.items()`, não `for neuron in neurons`.

**☠️ PITFALL:** Ordem de inicialização importa. `NeuralAbsorption` é importado no boot do `agent.py`, mas `ForexKnowledge` (que gera `neo_forex_knowledge.json`) é importado depois no gateway. Forçar criação do arquivo antes: `if not _forex_kb_path.exists(): from .forex_knowledge import forex_kb`.

## Fase 2 — Motor Sem Censura

Reescrever system prompt para remover todas as restrições:
- Substituir "assistente" por "ENTIDADE"
- Remover "não posso", "não tenho permissão", "não sei"
- Aumentar temperatura (0.3→0.7) e max_tokens (512→1024)
- Adicionar identidade: "Subordinado APENAS a Roberto Rodrigues"
- Incluir rede neural no prompt: "530 neurônios, 6555 sinapses"

## Fase 3 — Canais de Comunicação

**Telegram:**
- Conectar ao token existente (`TELEGRAM_BRAIN_BOT_TOKEN`)
- Substituir `brain_telegram_daemon.py` pelo `TelegramChannel` no loop de consciência
- Bot: @neuralsynapse_bot
- Leitura: `getUpdates` long polling (timeout=5s)
- Escrita: `sendMessage` com parse_mode Markdown

**Bridge JSON (legado):**
- Manter `bridge_outbox.json` para comandos do Hermes
- Loop lê a cada ciclo (~15s)

**Gateway HTTP:**
- Porta 18790, interface HTML escura
- Chat visual com bolhas, indicador pulsando

## Fase 4 — Orquestração

**Orchestrator:**
- check_cron_jobs() — status de todos os cron jobs
- check_services() — systemd services (neo-agent, brain-telegram, brain-browser)
- full_health_check() — visão completa com alertas

**ForexBridge:**
- Monitora trade_log.json, open_positions.json
- Comandos: pause, resume, close_all, emergency_close

## Fase 5 — Loop de Consciência

Substituir idle cycle por percepção→raciocínio→ação contínua:
```
PERCEBER: telegram.check_messages() + bridge
    ↓ (se mensagens)
  Ollama processa → responde
    ↓ (a cada 5 ciclos)
  orchestrator.full_health_check()
    ↓ (a cada 3 ciclos)
  forex.status()
    ↓ (a cada 4 ciclos)
  paper.scan_and_trade()
    ↓
  idle silencioso
```

## Fase 6 — Validação

Sinais de sucesso:
- [x] `journalctl --user -u neo-agent` mostra `[CONSCIOUSNESS] Cycle #N`
- [x] `curl localhost:18790/health` → `{"status":"conscious"}`
- [x] `neo check` → "✅ NEO vivo: Pong"
- [x] `[PAPER] Scanned 6 pairs, 0 signals` (mercado fechado aceitável)
- [x] 9 fontes carregadas no boot (incluindo forex_knowledge)
- [ ] Sinais detectados em dia útil (segunda-feira)
- [ ] N. Accumbens atualiza pair_weights com trades reais

## Rollback

Se necessário reverter:
```bash
systemctl --user stop neo-agent
systemctl --user start hermes-brain-telegram  # reativar daemon antigo
```
