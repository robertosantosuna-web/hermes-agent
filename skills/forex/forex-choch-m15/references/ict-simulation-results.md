# ICT Killzone Simulation Results — v2 (26/05/2026)

## Backtest Configuration
- **Filtros:** 2+ níveis (Asia+Daily) | Displacement 06-08h >1.4x avg | Retrace <50% | 3:1 RR
- **Período:** 7 dias úteis (2026-05-12 a 2026-05-22)
- **Dados:** yfinance H1/M5/M1 (M1 limitado a 7 dias pelo Yahoo)

## Results
| Par | Trades | WR | PnL | Veredito |
|-----|--------|-----|------|----------|
| GBPJPY | 1 | 100% | +20.7p | ✅ ÚNICO aprovado |
| EURJPY | 0 | — | — | ❌ Sem setups |
| USDJPY | 0 | — | — | ❌ Sem setups |
| GBPUSD | 0 | — | — | ❌ Sem setups |
| EURUSD | 0 | — | — | ❌ Sem setups |
| USDCAD | 0 | — | — | ❌ Sem setups |

## Key Finding
**GBPJPY is the ONLY pair with ICT-quality displacement candles at 06-08h UTC.**
All other pairs fail the displacement filter (range >1.4x average) — they don't form
the aggressive institutional moves required for the strategy.

## v1 Results (10 days, relaxed filters)
| Par | Trades | WR | PnL |
|-----|--------|-----|------|
| GBPJPY | 7 | 57.1% | +54.6p |
| EURJPY | 8 | 37.5% | +18.3p |
| USDCAD | 4 | 0% | -43.2p |
| **Total** | 19 | 36.8% | +29.7p |

## Pattern Quality Analysis (3 best GBPJPY days)
| Par | Double Breakouts | Displacement | Score |
|-----|-----------------|-------------|-------|
| GBPJPY | 67% of days | 0.40-0.42 range | ⭐⭐⭐ |
| EURJPY | 33% | 0.15-0.44 (inconsistent) | ⭐⭐ |
| USDJPY | 33% | 0.14-0.25 (weak) | ⭐ |
| GBPUSD | 33% | 0.002-0.003 | ⭐ |

## Learned Rules
1. **Displacement MUST be at 06-08h UTC** — 04h or 11h displacement = fake
2. **2+ levels broken = confluent setup** — single level = coin flip
3. **Retracement <50%** of displacement candle preserves momentum
4. **GBPJPY exclusive** for ICT — other pairs use M15 FVG+CRT instead
5. **~1 setup/week** — ICT is inherently selective, don't force entries
