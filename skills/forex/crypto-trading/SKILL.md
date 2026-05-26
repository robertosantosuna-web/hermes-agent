---
name: crypto-trading
description: "Estratégia de trading de criptomoedas. Backtest BTC/USDT iniciado. Mesma base ICT (CHoCH+FVG+S/R) adaptada para crypto 24/7."
version: 1.0.0
---

# Crypto Trading — Bitcoin & Criptomoedas

## Status

Backtest BTC/USDT iniciado em 19/05/2026. Estratégia baseada na mesma lógica do forex (CHoCH+FVG ICT + CRT + S/R), adaptada para mercado 24/7.

## Diferenças Forex vs Crypto

| Característica | Forex | Crypto |
|---------------|-------|--------|
| Horário | Seg-Sex, sessões | 24/7 contínuo |
| Sessões de pico | London, NY, Asia | Sobreposição US/EU, Asia |
| Volatilidade | Moderada | Alta (2-5x forex) |
| Pares | 4-6 principais | BTC/USDT (foco) |

## Pares Prioritários

1. **BTC/USDT** — Maior liquidez, mais dados
2. ETH/USDT — Segundo par (testar depois)
3. SOL/USDT — Alta volatilidade (testar depois)

## Estratégia Base

Mesma do forex: CHoCH + FVG + CRT + S/R @ M15.
WR≥40%→RR 3:1, WR≥80%→RR livre, WR<40%→NÃO abrir.

## Horários de Pico (Crypto, BRT)

| Sessão | Horário | Característica |
|--------|---------|---------------|
| Asia | 20:00-05:00 | Abertura semanal (dom 20h) |
| London/US | 09:00-13:00 | Maior volume |
| US | 10:30-17:00 | Notícias macro |

## Dados

```python
# Yahoo Finance (gratuito)
import yfinance as yf
btc = yf.download("BTC-USD", period="30d", interval="15m")

# Binance API (mais preciso, sem auth)
import requests
klines = requests.get(
    "https://api.binance.com/api/v3/klines",
    params={"symbol": "BTCUSDT", "interval": "15m", "limit": 500}
).json()
```

## Corretoras

| Corretora | Depósito Mínimo | Pix |
|-----------|----------------|-----|
| Binance | $10 | ✅ |
| Bybit | $10 | ✅ |
| KuCoin | $1 | ❌ |

**Recomendação: Binance** — maior liquidez, Pix, API robusta.

## Integração com Bot

Quando parâmetros validados:
1. Criar `~/.hermes/scripts/crypto_bot.py`
2. Usar Binance API para ordens
3. Mesmo self-learning do forex
4. Cronjob 24/7 (sem pausa fim de semana)

## Gestão de Risco (Crypto)

- Máximo 1-2% capital por trade (mais conservador que forex)
- Stop Loss OBRIGATÓRIO
- Máximo 2 posições simultâneas (vs 3 forex)
- Reserva 50% do lucro em USDT
- Fechar antes de CPI, FOMC

## Plano

1. [ ] Backtest BTC/USDT 30 dias com parâmetros forex
2. [ ] Ajustar para volatilidade crypto
3. [ ] Validar em demo Binance Testnet
4. [ ] Depositar $10-50
5. [ ] Ativar após 20 trades positivos
