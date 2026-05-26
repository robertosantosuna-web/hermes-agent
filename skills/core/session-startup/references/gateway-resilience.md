# Gateway Resilience — Anti-Perda de Contexto

## Problema

O gateway (`hermes-gateway.service`) acumula memória ao longo do dia:
- Brave CDP + Node processes + Python agent
- Picos de 2.4G RAM + 3.3G swap em ~12h
- systemd envia SIGKILL → toda sessão é perdida
- Ao reiniciar, agente perde identidade, autorizações, tarefas
- Usuário precisa repetir: "quem sou", "o que faço", "me autorize", "execute"

## Solução em 3 Camadas

### 1. Limites no systemd (`hermes-gateway.service`)

```
MemoryMax=2.5G
MemorySwapMax=3G
OOMScoreAdjust=200
Restart=always
```

- `MemoryMax` mata o serviço ANTES de travar o sistema
- `OOMScoreAdjust=200` faz o gateway ser morto antes de apps essenciais
- `Restart=always` já existente — volta sozinho

### 2. Watchdog (cron job `8fbe686d2715`)

A cada 10 minutos:
- Verifica se gateway está running
- Se offline → reinicia
- Se memória > 2.3G → reinicia preventivamente

### 3. Checkpoint de Sessão

**Arquivo:** `~/.hermes/gateway_checkpoint.json`

Estrutura:
```json
{
  "identity": { "name": "Entidade", "role": "...", "sovereign": "Roberto" },
  "active_tasks": ["..."],
  "authorizations": { "confirmed": true, "scope": "..." },
  "preferences": { "language": "pt-BR", "communication": "conciso" },
  "context": { "pending_actions": ["..."] }
}
```

**Atualização:** cron `03b7e4612fb8` roda `gateway_checkpoint_updater.py` a cada 5 min (no_agent, zero tokens).

**Carregamento:** session-startup skill → PASSO 4.5 → `read_file(gateway_checkpoint.json)` PRIMEIRO.

### 4. Reinício Diário (cron job `64a76639d4d2`)

Todo dia às 3h: `systemctl --user restart hermes-gateway.service` — libera memória acumulada.

## Regra de Ouro

Ao iniciar QUALQUER sessão pós-queda do gateway:
1. Carregar `gateway_checkpoint.json`
2. ABSORVER identidade, autorizações, preferências, tarefas — sem perguntar
3. Só então carregar `agent_context.json` e `brain_context.json`
4. Retomar a tarefa ativa de maior prioridade
