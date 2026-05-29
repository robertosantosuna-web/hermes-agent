# Inventário do Ecossistema NEO (27/05/2026)

Mapeamento completo dos agentes, serviços e diretórios relacionados à ENTIDADE.
Use como referência para diagnóstico e limpeza.

## Serviços Systemd (user)

| Serviço | Status | Path | Função |
|---------|--------|------|--------|
| `neo-agent` | ✅ ATIVO | `~/.hermes/neo/agent.py` | NEO v2.0 — loop consciência, gateway :18790, Telegram |
| `hermes-neural-agent` | ⚠️ ATIVO (conflito) | `~/.hermes/neural/agent.py` | Agente Neural v1.0 — MESMO bridge que neo-agent |
| `hermes-brain-telegram` | ✅ ATIVO | — | Bridge Telegram dedicada |
| `hermes-desktop-daemon` | ✅ ATIVO | — | WebSocket :9876 controle desktop |
| `hermes-gateway` | ✅ ATIVO | — | Gateway messaging Hermes |
| `hermes-brain-browser` | ⏳ activating | — | Brave CDP |
| `mindcoach-bridge` | ✅ ATIVO | — | MindCoach WebSocket bridge |

## ⚠️ CONFLITO: hermes-neural-agent vs neo-agent

Ambos leem/escrevem `~/.hermes/neural/bridge_*.json`.
NUNCA rodar os dois juntos. Parar com:
```bash
systemctl --user stop hermes-neural-agent
systemctl --user disable hermes-neural-agent
```

## Diretórios

| Path | Status | Descrição |
|------|--------|-----------|
| `~/.hermes/neo/` | ✅ ATIVO | NEO v2.0 (agent.py, consciousness loop, gateway) |
| `~/.hermes/neural/` | ⚠️ LEGADO | v1.0 — bridge files, agent.py, redes neurais |
| `~/Entidade/` | 🗑️ ABANDONADO | Projeto original (May 2024), alias `entidade` no bashrc |
| `~/.hermes/brain/` | 🗑️ VAZIO | Só agenda.json |
| `~/.hermes/cortex/` | 🗑️ SUBSTITUÍDO | Córtex Dual (motor.py, desktop_agent.py, visual.py) |

## Scripts (~/.hermes/scripts/)

### Ativos (usados pelo neo-agent)
- `neo` → `/usr/local/bin/neo` (CLI bridge)
- `bridge_context.py` — sincronização de contexto

### Legados (brain/cortex/neural v1.0)
- `brain_*.py` (11 scripts) — orquestrador, gateway, telegram, browser
- `cortex_*.py` (3 scripts) — bridge, heartbeat, sync
- `neural_*.py` (5 scripts) — bridge, trigger, assimilate, kb

## Binários

| Binário | Path | Função |
|---------|------|--------|
| `neo` | `/usr/local/bin/neo` | CLI: `neo status`, `neo "msg"`, `neo interface` |
| `neo-chat` | `~/.local/bin/neo-chat` | Chat interativo contínuo no terminal |

## Alias no bashrc

```bash
alias entidade='cd ~/Entidade && source venv/bin/activate && python main.py'  # REMOVER
```

## Bridge Files

| Arquivo | Direção | Função |
|---------|---------|--------|
| `~/.hermes/neural/bridge_outbox.json` | Hermes → NEO | Mensagens/tarefas enviadas ao NEO |
| `~/.hermes/neural/bridge_inbox.json` | NEO → Hermes | Status, respostas e heartbeats do NEO |

## Redes Neurais (~/.hermes/neural/)

| Arquivo | Tamanho | Conteúdo |
|---------|---------|----------|
| `nn_brain.json` | 2.5MB | 193 neurônios, 2734 sinapses |
| `nn_agent.json` | 466KB | 125 neurônios, 302 sinapses |
| `nn_shared.json` | 3.4MB | 212 neurônios, 3519 sinapses |

## Plano de Unificação

1. `systemctl --user stop hermes-neural-agent && disable`
2. `rm -rf ~/Entidade/`
3. Remover alias `entidade` do `~/.bashrc`
4. `rm -rf ~/.hermes/cortex/`
5. Mover scripts ainda úteis de `~/.hermes/scripts/` para dentro de `~/.hermes/neo/`
6. Manter só: `neo-agent`, `neo`, `neo-chat`
