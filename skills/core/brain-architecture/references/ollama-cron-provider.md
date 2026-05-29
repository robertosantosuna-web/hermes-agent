# Ollama como Provider para Cron Jobs

## Setup

```bash
# Adicionar provider Ollama no config.yaml
hermes config set providers.ollama.base_url "http://localhost:11434/v1"
hermes config set providers.ollama.api_key "ollama"

# Verificar modelos disponíveis
ollama list
```

## Context Length mínimo: 64K

Hermes Agent exige no mínimo 64.000 tokens de contexto. Modelos Ollama:

| Modelo | Contexto | Cron jobs |
|--------|----------|-----------|
| `llama3.2:3b` | 128K ✅ | Recomendado |
| `phi3:mini` | 128K ✅ | Alternativo |
| `qwen2.5:3b` | 32K ❌ | *ValueError: context window 32,768 below minimum 64,000* |
| `deepseek-r1:1.5b` | 32K ❌ | Mesmo erro |

## Migrar um cron job de API paga → Ollama

```bash
# Sempre use cronjob tool, NÃO edite config manualmente

# Para cada job com erro 402:
cronjob(action='update', job_id='...', model={'model': 'ollama/llama3.2:3b', 'provider': 'ollama'})
```

## Jobs que usam LLM (precisam de provider)

Esses jobs fazem chamadas ao modelo e quebram com `402 Insufficient Balance`:
- System Health Check (6ad2436b8997)
- MindCoach Checkpoint (79e9907ebf8c)
- Gateway health watchdog (8fbe686d2715)
- Mental Pillar Morning (b0001247db35)
- Motor Central Escalação (d8d0e9c72a99)
- Codex Forex Monitor (48425c92b336)

## Jobs no_agent (NÃO precisam de provider)

Estes usam `script` + `no_agent: true` — não consomem API:
- Amygdala, Cerebellum, N. Accumbens, Hippocampus, Brain Research
- Synapse Engine, NN Engine, Meta-Observer
- Brain Gateway, Neural Triggers, Monitor Consumer
- Forex Bot, AutoPilot, Trade Closer
