# Forex Backtest — Maio 2026 (V4 calibrado)

**Data:** 18-19/05/2026
**Fonte:** Yahoo Finance 5m, 10 dias de dados
**Script:** `~/.hermes/forex/backtest_killzones.py`

## Iterações

### V1 (M1, 5 pares, regras originais)
- 0 trades — Yahoo rate limit 429

### V2 (5m, yfinance, 3 killzones)
- 0 trades — filtros restritivos demais (range >12p, momentum >5p)

### V3 (5m, per-pair params, 3 killzones)
- 6 trades, 83% WR, +2.67%
- London Close: 4 trades, 4 wins — única killzone produtiva

### V4 (5m, filtros relaxados, 3 killzones)
- 8 trades, 62% WR, +1.48%

### V5 (London Close 1h, 3 pares)
- 14 trades, 50% WR, +3.51%

### Sweet Spot Final (London Close 1h, EUR/JPY + USD/JPY)
- **12 trades, 50% WR, +6.72%**
- EUR/JPY: 4 trades, 75% TP, +3.05%
- USD/JPY: 7 trades, 43% TP, +4.56%

## Parâmetros validados

```python
KILLZONE = "London Close 12:00-13:00 BRT (15:00-16:00 GMT)"
PAIRS = ["EURJPY", "USDJPY"]
TIMEFRAME = "5m"
RR = 1.5  # mais realista que 1:2 para janela 60min
LEV = 30

# Per-pair
EURJPY: stop=5-10p, target=7.5-15p, wick_min=2.0p, range_min=6p, mom_min=3p
USDJPY: stop=5-8p, target=7.5-12p, wick_min=2.0p, range_min=5p, mom_min=2p
```

## Regras de entrada

1. Range pré-killzone >5 pips (média 5 velas)
2. Sweep: wick > body × 1.2 + fecha contra o sweep
3. Momentum >2-3 pips nas últimas 3 velas
4. Entrada na vela seguinte ao sweep confirmado
5. Stop = 50% do range da vela de sweep
6. Target = 1.5× stop
7. Timeout: fecha no fim da killzone (60 min)

## Conclusão

- London Open (04:00) e NY Open (09:30) são **negativas** no mercado atual
- Mercado está lateral — ranges médios de 2-6 pips em 5m
- JPY crosses (EUR/JPY, USD/JPY) têm ranges maiores (6.3p avg) e são os únicos viáveis
- GBP/USD e EUR/USD descartados por ranges insuficientes
- Estratégia ajustada para volatilidade real do mercado, não teoria ICT
