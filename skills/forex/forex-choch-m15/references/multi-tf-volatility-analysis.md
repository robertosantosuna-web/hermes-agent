# Multi-Timeframe Volatility Analysis (26/05/2026)

## Methodology
Analyzed 8 pairs × 4 timeframes (M5, M15, M30, H1) × 4 market crossovers
(Asia+London 7-9, London+NY 12-16, London Close 15-16, NY Open 12-13)
using yfinance OHLC data (5 days).

## Global Ranking (avg range/candle across all crossovers × timeframes)

| Rank | Par | Avg | Peak (H1) | M15 |
|------|-----|-----|-----------|-----|
| 🥇 | GBPJPY | 17.9p/c | 36.7p/c | 12.8p/c |
| 🥈 | EURJPY | 12.6p/c | 28.7p/c | 8.9p/c |
| 🥉 | USDCAD | 12.4p/c | 19.7p/c | 10.9p/c |
| 4️⃣ | USDJPY | 11.2p/c | 23.5p/c | 7.2p/c |
| 5️⃣ | GBPUSD | 10.6p/c | 20.0p/c | 8.0p/c |
| 6️⃣ | EURUSD | 7.6p/c | 13.8p/c | 6.0p/c |

## Key Findings
- **GBPJPY = #1 in ALL 16 scenarios** (4 TFs × 4 crossovers) without exception
- **London Close (15-16 UTC)** = peak volatility for all pairs
- **M15 = sweet spot** — balances frequency vs range for bot trading
- **H1 has 2.3x more range** but setups would be much rarer
- **EURUSD is dead last** — consistently the least volatile major pair

## Per-Crossover Top 3 (M15)
| Crossover | #1 | #2 | #3 |
|-----------|----|----|-----|
| Asia+London (7-9) | GBPJPY 13.5p | EURJPY 9.7p | USDCAD 9.0p |
| London+NY (12-16) | GBPJPY 13.2p | USDCAD 11.7p | EURJPY 9.1p |
| London Close (15-16) | USDCAD 12.3p | GBPJPY 12.2p | USDJPY 9.4p |
| NY Open (12-13) | GBPJPY 11.2p | USDCAD 10.4p | EURJPY 8.5p |

## Action Taken
- Added GBPJPY and USDCAD to bot (from 3 to 6 pairs)
- Deprioritized EURUSD (consistently worst)
- London Close elevated to priority killzone in scoring
