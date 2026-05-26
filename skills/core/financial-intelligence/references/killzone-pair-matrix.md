# Forex SMC/ICT Strategy — Killzone + Pair Matrix
# Updated: 2026-05-19

## Killzone Windows (BRT, UTC-3)

| Killzone | Horário | Pares | Análise T-5 |
|----------|---------|-------|-------------|
| London Open | 05:00-07:00 | EURUSD, GBPUSD, EURGBP | 04:55 |
| NY Open | 09:00-12:00 | EURUSD, GBPUSD, USDJPY | 09:55 |
| London Close | 12:00-14:00 | EURUSD, EURJPY, USDJPY | 11:55 |

## Pair Restrictions (DO NOT VIOLATE)

- London Open: ONLY EURUSD, GBPUSD, EURGBP
- NY Open: ONLY EURUSD, GBPUSD, USDJPY
- London Close: ONLY EURUSD, EURJPY, USDJPY
- NEVER: AUD/USD, NZD/USD, USD/CAD, or any other pair
- NEVER: Asian session (21:00-23:00 BRT)
- NEVER: Weekends

## Entry Rules (5 Steps)

1. M15 trend confirmation (HH+HL for LONG, LH+LL for SHORT)
2. M5 liquidity sweep (takes out previous high/low)
3. CHoCH confirmation (candle closes beyond sweep candle)
4. Return to Order Block or fresh FVG
5. Entry at OB/FVG touch + SL at sweep extreme + TP 3:1

## Filters

- NO entry without CHoCH confirmation
- NO entry if OB/FVG tested 2x already
- NO entry against M15 trend
- YES when OB coincides with Fib 0.62-0.79
- YES on fresh (untested) FVG
- SHORT priority during London Close (44.4% WR vs LONG 21.1%)

## Risk Management

- Risk: 1% capital per trade
- Max 1 trade per pair per session
- Max 3 trades per day (1 per killzone)
- Stop after 2 consecutive losses
- Friday: close all by 13:00 BRT
- Breakeven at 1.5R

## Best Parameters (from backtest)

- Best killzone: London Close (28.6% WR, +54.5 pips)
- Best type: SHORT (44.4% WR)
- Best pairs: EURUSD (36.4%), EURJPY (33.3%)
- Avoid: GBPUSD (15.4% WR)
