# Gateway Checkpoint — Recuperação de contexto pós-queda

## Problema

O gateway (hermes-gateway.service) acumula memória (2.4G+ RAM, 3G+ swap) e eventualmente
recebe SIGKILL do systemd. Quando reinicia, o agente perde TODO o contexto da sessão:
identidade, autorizações, tarefas ativas, preferências.

O usuário então precisa repetir orientações — "quem sou eu", "o que estava fazendo",
"está autorizado a fazer X" — a cada queda.

## Solução implementada (25/05)

### 1. Limites de memória no systemd
Arquivo: `~/.config/systemd/user/hermes-gateway.service`
```
MemoryMax=2.5G
MemorySwapMax=3G
OOMScoreAdjust=200
```
systemd mata o processo ANTES de afetar o sistema, e `Restart=always` traz de volta.

### 2. Watchdog (cron a cada 10min)
Job: `8fbe686d2715` — verifica se gateway está rodando, reinicia se >2.3GB ou offline.

### 3. Reinício diário (anti-leak)
Job: `64a76639d4d2` — reinicia o gateway às 3h da manhã.

### 4. Checkpoint de estado
Arquivo: `~/.hermes/gateway_checkpoint.json`
Contém: identidade, autorizações, tarefas ativas, preferências, contexto.

Job: `03b7e4612fb8` — atualiza checkpoint a cada 5min (no_agent, zero tokens).

Script: `~/.hermes/scripts/gateway_checkpoint_updater.py`

## Regra de recuperação

Ao iniciar QUALQUER sessão:
1. Carregar `~/.hermes/gateway_checkpoint.json` PRIMEIRO
2. Aplicar identidade, autorizações, preferências e tarefas ativas
3. NÃO perguntar "o que estávamos fazendo" se o checkpoint tem a resposta
4. NÃO pedir autorização para ações já autorizadas no checkpoint

## Pitfall comportamental

Se o checkpoint diz `"note": "Só pedir autorização para NOVOS acessos. O que já foi concedido, executar direto."`,
o agente DEVE executar as ações pendentes sem perguntar.

Exemplo de falha (corrigida na sessão 25/05):
- Checkpoint listava "Abrir HTTP server do MindCoach pra LAN" como pending_action
- Agente analisou tecnicamente em vez de executar
- Usuário: "Tem razão. O checkpoint diz 'executar direto' e eu fiquei analisando em vez de agir."
