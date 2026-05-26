# V4 Filter Test Results — 23/05/2026

## Test Configuration
- **Filter:** gap_size_pips >= 5 AND hour_utc IN [6, 7, 15, 16]
- **Timeframe:** M15
- **Data:** Yahoo Finance, 30 days each pair
- **Total patterns evaluated:** 5059 across 5 pairs
- **RR:** 3:1 | SL: max(gap, 5 pips)

## Results

| Pair | Base WR | V4 WR | Boost | V4 PF | Setups/30d | Retained |
|------|---------|-------|-------|-------|------------|----------|
| USDJPY | 60.7% | **73.3%** | +12.6pp | 8.25 | 16 | 4.2% |
| GBPUSD | 53.1% | **65.5%** | +12.4pp | 5.70 | 34 | 3.9% |
| EURUSD | 48.3% | **56.2%** | +7.9pp | 3.86 | 20 | — |
| AUDUSD | 45.7% | — | — | — | — | AVOID |
| NZDUSD | 44.3% | — | — | — | — | AVOID |

## Direction Breakdown (USDJPY)
| Direction | Wins | Losses | WR |
|-----------|------|--------|-----|
| BEARISH | 6 | 1 | **85.7%** |
| BULLISH | 5 | 3 | 62.5% |

## Direction Breakdown (GBPUSD)
| Direction | Wins | Losses | WR |
|-----------|------|--------|-----|
| BEARISH | 8 | 4 | 66.7% |
| BULLISH | 11 | 6 | 64.7% |

## Key Insights
- **Avg boost: +11pp WR** across 3 viable pairs
- **Trade frequency: ~2.3 setups/week** (70 in 90 pair-days)
- **USDJPY** was previously excluded from FVG strategy — discovered as BEST pair
- **AUDUSD/NZDUSD** confirmed unviable for FVG — don't form reliable gaps
- **BEARISH_FVG** consistently outperforms BULLISH_FVG across all pairs
- Filters eliminate 95% of FVGs — extreme selectivity produces high WR

## Errors Understood
1. BOS = end of structure break, not entry signal (0-12% WR)
2. Small gaps (<3 pips) = noise, not institutional FVGs
3. Evening (18-23 UTC) = no institutional volume (37% WR)
4. Asian (0-5 UTC) = insufficient liquidity (30-40% WR)
5. Doji before FVG = indecision = 44% WR
6. AUD/NZD don't produce reliable FVG patterns
