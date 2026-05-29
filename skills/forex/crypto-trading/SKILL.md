---
name: crypto-trading
description: "Sistema Multi-Agente Crypto v2 — 5 agentes + Pair Selector dinâmico. Backtest 7 dias: 477 trades, 45.7% WR, +395R, PF 2.53."
version: 2.0.0
---

# Crypto Trading v2 — Multi-Agente + Pair Selector

## Status: ATIVO 24/7

Backtest 7 dias (5 pares): **477 trades, 45.7% WR, +395R, PF 2.53**.
Cron job `Crypto AutoPilot 24/7` rodando a cada 3 min.

## Arquitetura

```
crypto/
├── crypto_multi_agent.py   # 5 agentes (Volatilidade, Tendência, Padrão, Sessão, Fluxo)
├── crypto_bot.py           # Bot principal com pair selector dinâmico
├── pair_selector.py        # Seleção dinâmica dos melhores pares
└── validate_crypto.py      # Backtest + validação pré-deploy
```

## 5 Agentes

| Agente | Função | Peso |
|--------|--------|------|
| Volatilidade | ATR, regime, SL recomendado | 1.0 |
| Tendência | Multi-TF (M15→M5→M1) hierárquico | 2.0 |
| Padrão | FVG + Order Block, quality scoring | 1.8 |
| Sessão | Horários de pico (NY/Asia/London) | 0.7 |
| Fluxo | Correlação BTC/Altcoins | 1.2 |

## Pares

8 pares disponíveis, seleção dinâmica dos 5 melhores por volatilidade + momentum:
- S Tier: BTCUSD, ETHUSD
- A Tier: SOLUSD, DOGEUSD, BNBUSD
- B Tier: XRPUSD, ADAUSD, AVAXUSD

## Parâmetros

- RR: 3:1 fixo
- Risco: 0.5% por trade
- SL: baseado em ATR (0.12% a 0.6%)
- Confiança mínima: 40%
- Anti-correlação: max 2 pares do mesmo grupo

## Horários de Pico (UTC)

| Sessão | Horário | Bônus |
|--------|---------|-------|
| NY Open | 13-20h | 1.0x |
| Asia Open | 0-7h | 0.85x |
| London | 8-12h | 0.7x |
| Off-peak | 21-23h | 0.5x |

## Backtest Results (7 dias, 5 pares)

| Par | Trades | WR | R |
|-----|--------|----|---|
| BNBUSD | 91 | 56% | +113 |
| BTCUSD | 91 | 46% | +77 |
| DOGEUSD | 95 | 45% | +77 |
| ETHUSD | 96 | 44% | +72 |
| SOLUSD | 104 | 38% | +56 |

## Comandos

```bash
# Rodar bot manualmente
cd ~/.hermes/crypto && python3 crypto_bot.py

# Backtest
cd ~/.hermes/crypto && python3 validate_crypto.py

# Sinais salvos
cat ~/.hermes/crypto/signals.json

# Cron job
cronjob action=list  # procurar "Crypto AutoPilot 24/7"
```
