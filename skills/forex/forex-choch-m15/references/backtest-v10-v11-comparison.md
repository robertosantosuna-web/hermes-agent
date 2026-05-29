# Backtest Results — V10 vs V11 vs V12 (29/05/2026)

## Evolution

| Version | Filters | Timeframe | Trades | WR | R | PF | MaxDD |
|---------|---------|-----------|--------|-----|------|------|-------|
| v10 | None | M15 FVG | 59 | 20.3% | -11R | 0.77 | 21R |
| v11 | DMI M1 + candle fechado | M1 FVG | 10 | 60.0% | +14R | 4.50 | 2R |
| v11.1 | DMI M5 | M1 FVG | 1 | 100% | +3R | inf | 0R |

## Key Insight

- **Filtros cortaram 83% dos trades ruins** (59 → 10) mas mantiveram os bons
- **DMI no M1** é o sweet spot: responsivo o suficiente para filtrar, sem ser lento demais
- **ATR no M5/M15** para SL é essencial: ATR do M1 é 0.1-3p (sempre cai no mínimo de 10p)
- **Candle fechado** obrigatório elimina entradas em wicks
- **Volume > 1.3x** adiciona confirmação extra

## Per-Pair (v11, 5 days)

```
USDJPY   100% WR  +3R
XAUUSD   100% WR  +3R
USDCAD   100% WR  +3R
EURUSD    50% WR  +2R
GBPUSD    50% WR  +2R
EURJPY    50% WR  +2R
GBPJPY     0% WR  -1R
```

## Expectancy

v11: (0.60 × 3) + (0.40 × -1) = +1.40R per trade
v10: (0.20 × 3) + (0.80 × -1) = -0.20R per trade

**Net improvement: +1.60R per trade.**
