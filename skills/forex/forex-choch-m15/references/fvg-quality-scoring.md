# FVG Quality Scoring System (29/05/2026)

Script: `/home/roberto/.hermes/scripts/fvg_quality.py`

## Score Criteria (0-100)

| Criterio | Peso | Condicao |
|----------|------|----------|
| Tamanho minimo | OBRIGATORIO | Gap > 2 pips forex / >50 ticks metal |
| Premium/Discount | 30pts | Compra em discount, venda em premium |
| Alinhamento tendencia | 25pts | FVG na direcao do momentum recente |
| First touch | 20pts | FVG nunca foi revisitado |
| Vela qualidade | 10pts | Corpo da vela > 1.3x media |
| Consecutive FVGs | -15pts | Penalidade se >3 FVGs mesma direcao |

## Thresholds testados (30 dias, 7 pares)

| Score | Trades | WR | R | Efeito |
|-------|--------|-----|-----|--------|
| 0 (sem filtro) | 120 | 24% | -4R | Baseline |
| 55 | 10 | 40% | +6R | Elimina 92% trades |
| 35-40 | ~25-30 | ~35% | ~+5R | Equilibrio (estimado) |

## Uso

```python
from fvg_quality import is_fvg_valid
valid, details = is_fvg_valid(highs, lows, closes, fvg_idx, direction, pip_size, is_metal, min_score=40)
```
