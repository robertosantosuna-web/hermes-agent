# Forex Self-Learning System

> Sistema automático de ajuste de pesos dos pares baseado em resultado REAL.
> Zero tokens — Python puro. Roda via Módulo Executivo.

## Como funciona

1. **Coleta:** Lê `~/.hermes/forex/trade_log.json`
2. **Agrupa:** Por par, calcula WR real e P&L
3. **Recomenda:** ACTIVE (WR≥60%), WATCH (50-59%), PAUSE (<50%)
4. **Salva:** `~/.hermes/forex/pair_weights_live.json`

## Comando

```bash
/usr/bin/python3 ~/.hermes/executive/brain.py --learn
```

## Output exemplo

```json
{
  "AUD/USD": {"wr": 50.0, "trades": 2, "pnl": -0.4, "recommendation": "WATCH"},
  "NZD/USD": {"wr": 100.0, "trades": 1, "pnl": 8.9, "recommendation": "ACTIVE"},
  "GBP/USD": {"wr": 0.0, "trades": 2, "pnl": -18.7, "recommendation": "PAUSE"}
}
```

## Integração com o bot

O bot `forex_bot_real.py` pode carregar este arquivo e ajustar `PAIRS[par]['wr']` dinamicamente, substituindo os scores de backtest por dados reais.

## Ollama Pattern Detection (futuro)

Com `llama3.2:3b` local: analisar histórico de trades e responder:
- "Existe padrão nos horários de loss?"
- "Qual par está mais consistente?"
- "Setup específico falhando repetidamente?"
