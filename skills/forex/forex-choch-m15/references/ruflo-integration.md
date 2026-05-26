# Arquitetura RUFLo — Integração com Hermes

## Visão Geral

RUFLo (github.com/ruvnet/ruflo) é uma plataforma de orquestração multi-agente com 53k+ estrelas.
33 plugins, incluindo `ruflo-neural-trader` (112+ ferramentas MCP, LSTM/Transformer/N-BEATS).

## Pipeline de Dados

```
TradingView (Pine Script) ──→ Webhook (:8888) ──→ mt5_direct.py (F9)
                                │
neural-trader (Rust) ──→ Backtest + Risco + LSTM
                                │
AgentDB ──→ Memória entre sessões
```

## Componentes

| Componente | Local | Função |
|-----------|-------|--------|
| neural-trader | ~/ruflo/node_modules/neural-trader | Backtest, risco, regime |
| webhook_receiver | ~/.hermes/scripts/webhook_receiver.py | Recebe alertas TV → MT5 |
| mt5_direct | ~/.hermes/scripts/mt5_direct.py | Executa ordens F9 no MT5 |
| forex_bot_real | ~/.hermes/scripts/forex_bot_real.py | Bot autônomo 15min |
| Pine Script | ~/.hermes/forex/choch_fvg_m15.pine | CHoCH+FVG no TradingView |

## Comandos neural-trader

```bash
cd ~/ruflo
npx neural-trader --backtest momentum --symbol EURUSD=X --live --json
npx neural-trader --signal scan --symbols GBPUSD=X,AUDUSD=X
npx neural-trader --risk assess --symbol EURUSD=X
npx neural-trader --regime --symbol EURUSD=X
```

## Credenciais

- MT5 OANDA: login 1715539800 / senha wc0ZO6#p / server OANDA_Global-Demo-1
- Portal OANDA: robertosantos.una@gmail.com / wc0ZO6#p2026 (pendente captcha)
- Brokers: ~/.hermes/forex/brokers.json
