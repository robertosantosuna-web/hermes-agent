# Backtest Results — 29/05/2026

## Evolution

| Version | Dias | Trades | WR | R | PF | Config |
|---------|------|--------|-----|-----|-----|--------|
| v9.5 | 30 | 144 | 27% | -11R | 0.77 | Multi-TF M15, sem filtros |
| v10 | 21 | 59 | 20% | -11R | 0.77 | M1 FVG, sem filtros |
| v10 | 7 | 12 | 42% | +8R | 2.00 | M1 FVG, candle fechado |
| v11 | 5 | 10 | 60% | +14R | 4.50 | DMI M1 + ATR M1 |
| v11 dual | 5 | 9 | 55% | +11R | 2.50 | Modelo A+B |
| v11 30d | 30 | 65 | 22% | -9R | 0.82 | DMI+ADX estrito |
| v11 relaxed | 30 | 83 | 22% | -11R | 0.83 | ADX only |
| v12 scored | 30 | 10 | 40% | +6R | 2.00 | FVG Score >55 |
| v12 5d base | 5 | 9 | 56% | +11R | 3.75 | DMI+ADX, sem score |

## Key Findings
1. 5 dias bons (25-29/05): Tendencia USD caindo = 56-60% WR
2. 30 dias: Regime misto expoe fraqueza, WR cai para 22%
3. FVG Quality Score > 55: Elimina 92% dos trades, sobe WR para 40%
4. XAUUSD: Melhor par consistente (50-100% WR em todos os testes)
5. Premium/Discount e o filtro mais impactante (30pts no score)
