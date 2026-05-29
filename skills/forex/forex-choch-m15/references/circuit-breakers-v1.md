# Circuit Breakers v1 — AutoPilot (28/05/2026)

Implementado por demanda do Roberto: "quero que o sistema de autopilot detecte quando a rede corretora estiver instável e pause a abertura de ordens até normalizar."

Revisado por 4 IAs (Gemini, DeepSeek, ChatGPT, Grok). Gemini forneceu as métricas de suspensão.

## Circuit Breakers Ativos

| # | Breaker | Gatilho | Ação | Reset |
|---|---------|---------|------|-------|
| 1 | Drawdown diário | equity -5% vs saldo inicial do dia | ⛔ Suspende novas ordens | 00:00 UTC |
| 2 | Perdas consecutivas | 5 trades negativos seguidos | ⛔ Suspende novas ordens | Vitória reseta |
| 3 | Falhas de bridge | >3 falhas em 1 hora | ⛔ Suspende novas ordens | Janela 1h |
| 4 | Breakeven prematuro | >40% dos BE saem antes de 2R | ⚠️ Alerta (não suspende) | — |
| 5 | Slippage alto | >2x spread normal | ⚠️ Alerta (não suspende) | — |

## Implementação

Arquivo: `~/.hermes/brain/autopilot.py`
Estado: `~/.hermes/forex/circuit_breakers.json`

### Funções principais

```python
check_circuit_breakers(mt5_data)  # Executa todas as verificações. Retorna (ok, reason)
is_circuit_breaker_active()       # True se trading suspenso
record_trade_result(ticket, symbol, pnl, max_rr, exit_reason, slippage)
record_bridge_failure()           # Registra falha de comunicação
```

### Integração no main()

Antes de abrir novas ordens:
```python
cb_ok, cb_reason = check_circuit_breakers(mt5)
if not cb_ok:
    # Suspende novas ordens, mas continua gerenciando posições existentes
    # Alerta crítico no Tálamo
```

Resumo mostra indicador `⛔CB` quando ativo.

## Gemini: Pergunta de validação

> "Qual será a métrica matemática exata de rebaixamento (drawdown) ou taxa de falha de execução nesses testes práticos que forçará a suspensão imediata e a recalibragem das variáveis do algoritmo?"

Resposta implementada: drawdown diário 5%, 5 perdas consecutivas, 3 falhas de bridge/hora.

## Parâmetros configuráveis

```python
MAX_DRAWDOWN_DAILY = 0.05       # 5%
MAX_CONSECUTIVE_LOSSES = 5      # 5 trades
MAX_BREAKEVEN_PREMATURE = 0.40  # 40%
MAX_SLIPPAGE_RATIO = 2.0        # 2x spread
MAX_BRIDGE_FAILURES_HOUR = 3    # 3 falhas/hora
```

## ⚠️ Pitfall: INITIAL_BALANCE Fixo (29/05/2026)

**Sintoma:** Bot inicia e imediatamente para com `🛑 DAILY STOP: $334.89 (-16.3%). BOT HALTED.`

**Causa:** `forex_bot_multi.py` usava `INITIAL_BALANCE = 400.0` (hardcoded) como referência para o circuit breaker de drawdown. Quando o saldo real caiu para $334.89 (-16.3%), o breaker disparava falsamente.

**Correção:** Substituir `INITIAL_BALANCE` fixo por `daily_state.json`:
```python
daily_state_file = Path.home() / '.hermes' / 'forex' / 'daily_state.json'
# Salva {"date": "2026-05-29", "start_balance": 334.89} no início de cada dia
# Circuit breaker compara balance com daily_start, não com INITIAL_BALANCE
```
`INITIAL_BALANCE` agora é apenas fallback quando MT5 não responde.
