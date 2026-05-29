# Agente Neural Independente — Arquitetura v1.0

Criado em 27/05/2026. O Agente Neural é a evolução do cérebro bi-neural:
sai de scripts passivos (cron jobs no_agent) para um **processo autônomo contínuo**
com loop próprio, memória própria e raciocínio via Ollama local.

## Motivação

- **Custo**: DeepSeek API quebrou com 402 (sem créditos) — 6+ cron jobs parados
- **Dependência**: Cérebro dependia de cron jobs do Hermes pra funcionar
- **Autonomia**: Roberto quer o cérebro verdadeiramente independente

## Arquitetura

```
┌────────────────────┐     bridge JSON      ┌─────────────────────┐
│   Hermes Agent     │ ←── inbox/outbox ──→ │   Neural Agent      │
│  (DeepSeek V4)     │                      │  (llama3.2:3b)      │
│                    │                      │                      │
│  Decisões          │                      │  Loop autônomo       │
│  Estratégia        │                      │  Memória própria      │
│  Orquestração      │                      │  Pipeline tarefas    │
│  Comunicação       │                      │  Ollama local        │
└────────────────────┘                      └─────────────────────┘
                                                    │
                                              systemd daemon
                                              restart automático
                                              zero API cost
```

## Componentes

| Arquivo | Função |
|---------|--------|
| `~/.hermes/neural/agent.py` | Core do agente: loop, Ollama, tools, memória |
| `~/.hermes/neural/memory.json` | Memória persistente (identidade, estado, histórico) |
| `~/.hermes/neural/tasks.json` | Fila de tarefas com prioridade |
| `~/.hermes/neural/bridge_inbox.json` | Mensagens Neural → Hermes |
| `~/.hermes/neural/bridge_outbox.json` | Mensagens Hermes → Neural |
| `~/.hermes/scripts/neural_bridge.py` | CLI da bridge (send/read/status) |
| `~/.config/systemd/user/hermes-neural-agent.service` | Serviço systemd |

## Comandos

```bash
# Gestão do agente
systemctl --user status hermes-neural-agent
systemctl --user restart hermes-neural-agent
journalctl --user -u hermes-neural-agent -f

# Bridge
python3 ~/.hermes/scripts/neural_bridge.py send "descrição da tarefa" high
python3 ~/.hermes/scripts/neural_bridge.py read
python3 ~/.hermes/scripts/neural_bridge.py status
```

## Ciclo de Execução

1. A cada 15s: verifica bridge (mensagens do Hermes)
2. Auto-seed: gera tarefas internas se fila vazia
3. Processa próxima tarefa pendente (prioridade + ordem)
4. Cada tarefa: chama Ollama → recebe JSON com ação → executa tool → registra
5. A cada 10 ciclos: reporta status ao Hermes

## Tools Disponíveis

- `terminal(cmd)` — executa shell
- `read_file(path)` — lê arquivo
- `write_file(path, content)` — escreve arquivo
- `web_fetch(url)` — HTTP GET

## Modelo

- **llama3.2:3b** (128K contexto, 2.0 GB)
- Alternativa: **phi3:mini** (128K contexto, 2.2 GB)
- **NUNCA usar qwen2.5:3b** (32K contexto — Hermes rejeita)

## Migração Planejada

Tarefas a migrar do cérebro (scripts cron) para o Agente Neural:

| Tarefa | Cron Job | Status |
|--------|----------|--------|
| Health check sistema | System Health Check | → Neural |
| Monitoramento processos | Gateway Watchdog | → Neural |
| Verificação forex | Brain Signal Scanner | → Neural |
| Alertas freelas | Monitor Consumer | → Neural |
| Consolidação padrões | Hippocampus | → Neural |
