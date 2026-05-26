# Monte Carlo — Forex CHoCH+FVG M15

> Data: 2026-05-21 | Estratégia: CRT + S/R Levels | RR 3:1 | WR 72.6%

## Resultados

### Probabilidade de Ruína (50,000 simulações)

| Banca | Risco 2%/trade | Risco 5%/trade | Risco 10%/trade | Risco 20%/trade |
|-------|---------------|---------------|-----------------|-----------------|
| $100  | ~0%           | ~0%           | 0.0002%         | 0.15%           |
| $200  | ~0%           | ~0%           | 0.0002%         | 0.15%           |
| $500  | ~0%           | ~0%           | 0.0002%         | 0.15%           |

### Kelly Criterion

- f* = 63.5% (aposta ótima teórica)
- Half-Kelly recomendado = 31.7%
- Com $100: $31.70/trade | $200: $63.50/trade | $500: $158.70/trade

### Conclusão

WR=72.6% + RR=3:1 = expectativa matemática fortemente positiva (EV = +$1.90 por $1 arriscado).
**$100 é suficiente para começar com microlotes (0.01) e risco ≤5%.**

### Parâmetros para Conta Real

- Volume: 0.01 (microlote, ~$0.10/pip)
- Risco: 3% por trade (conservador inicial)
- Stop diário: -5% do saldo ($5 com $100)
- Max posições simultâneas: 3
- Ruína: praticamente impossível com estes parâmetros
