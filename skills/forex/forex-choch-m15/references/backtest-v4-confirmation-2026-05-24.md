# Backtest V4 — Confirmação Independente (24/05/2026)

Segundo backtest completo rodado em 24/05 com dados frescos do Yahoo Finance.
Confirma todos os rankings e thresholds da estratégia V4.

## Baseline (sem filtros) — 3225 FVGs, 5 pares, 30 dias M15

| Rank | Par | WR | PF | FVGs | Status |
|------|-----|-----|-----|------|--------|
| 🥇 | USDJPY | 60.7% | 3.04 | 356 | ✅ |
| 🥈 | GBPUSD | 53.1% | 2.95 | 761 | ✅ |
| 🥉 | EURUSD | 48.3% | 2.60 | 545 | ⚠️ |
| ❌ | AUDUSD | 45.7% | 2.29 | 793 | EVITAR |
| ❌ | NZDUSD | 44.3% | 2.11 | 770 | EVITAR |

Ranking IDÊNTICO ao backtest original de 23/05.

## V4 Filtrado (gap≥5 + horas [6,7,15,16] UTC)

Filtro muito seletivo: apenas 83 FVGs de 3225 (2.6%) passam.
~0.55 setups/pair-dia.

| Par | WR | Wins | Losses | PF |
|-----|-----|------|--------|-----|
| GBPUSD | 83.8% | 31 | 6 | 15.5 |
| USDJPY | 87.5% | 7 | 1 | 21.0 |
| EURUSD | 76.9% | 10 | 3 | 10.0 |
| NZDUSD | 88.9% | 8 | 1 | 24.0 |
| AUDUSD | 68.8% | 11 | 5 | 6.6 |

⚠️ NZDUSD e AUDUSD com amostras pequenas (9 e 16 trades) — ruidoso.
GBPUSD tem maior volume (37 trades) e WR excelente (83.8%) — mais confiável.

## Bullish vs Bearish (baseline)

| Par | BULL WR | BEAR WR | Delta |
|-----|---------|---------|-------|
| USDJPY | 61.3% | 59.9% | +1.4 |
| GBPUSD | 49.2% | 56.9% | **+7.7** |
| EURUSD | 44.6% | 51.6% | **+7.0** |
| AUDUSD | 46.0% | 45.3% | +0.7 |
| NZDUSD | 43.3% | 45.3% | +2.0 |

Confirma preferência bearish já documentada (regra #3 do cross-agent).

## Gap Threshold — USDJPY

| Gap mínimo | Wins | Losses | WR |
|-----------|------|--------|-----|
| 0 | 216 | 140 | 60.7% |
| 3 | 81 | 47 | 63.3% |
| 5 | 40 | 20 | 66.7% |
| 7 | 22 | 9 | 71.0% |
| 10 | 8 | 3 | 72.7% |

Gap≥5 é o sweet spot: WR sobe 6pp com volume ainda saudável.

## Bot State (24/05)

`forex_bot_real.py` atualizado para V4:
- Pares: USDJPY, GBPUSD, EURUSD (AUD/NZD removidos)
- MIN_FVG_PIPS: 5.0
- TRADING_HOURS_UTC: [6, 7, 15, 16]
- MAX_POSITIONS: 4
- FVG_TIMEOUT_CANDLES: 3
- DEDUP_PER_DAY: True
- Corretora: IC Markets Demo (ydotool, display:0)
