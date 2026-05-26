# Corretoras Forex com API para Trading Automatizado

**Data:** 18/05/2026 | **Pesquisa:** 6 corretoras analisadas

## 🥇 OANDA — Melhor para API Trading

- **API:** REST v20 — biblioteca Python `oandapyV20` ✅ testada e funcional
- **Conta Demo:** Gratuita, dados reais, endpoint `api-fxpractice.oanda.com` ✅ ativo
- **Regulação:** FCA (UK), CFTC (US), MAS (Singapura)
- **Spreads EUR/USD:** ~1.0 pip (Standard)
- **Alavancagem:** 50:1 (US) / 30:1 (UK)
- **Comando:** `pip install oandapyV20`

## 🥈 Interactive Brokers — Melhor para Produção Profissional

- **API:** REST + TWS API — biblioteca `ib_insync` ✅ instalada
- **Regulação:** SEC, FINRA, CFTC (US) + FCA (UK) — Tier-1 máximo
- **Spreads:** **0.1 pip** (interbancário de 17 dealers)
- **Comissão:** 0.20-0.08 bp, mín $2-1
- **Mercados:** 170 em 40 países

## 🥉 IC Markets — Melhores Spreads Raw

- **API:** MT5 Python (`mt5linux` ✅ instalado)
- **Spreads Raw EUR/USD:** 0.01 pip avg (mín 0.0)
- **Alavancagem:** Até 500:1
- **Regulação:** FSA Seychelles ⚠️ (offshore)

## Outras analisadas

| Corretora | API | Regulação | Destaque |
|-----------|-----|-----------|----------|
| Pepperstone | FIX API (institucional) | ASIC, FCA | MT5 via `mt5` library |
| FXCM | REST + Python (`fxcmpy`) | FCA, ASIC | Wrapper dedicado |
| XM | MT4/MT5 apenas | CySEC, FCA | Sem REST API própria |

## Estratégia Recomendada

```
Desenvolvimento: OANDA demo (REST mais simples, oandapyV20)
Produção:       Interactive Brokers (segurança máxima)
Spread baixo:   IC Markets (MT5, 0.01 pip, 500:1 alavancagem)
```

## Setup

```bash
pip install oandapyV20 ib_insync mt5linux
```
