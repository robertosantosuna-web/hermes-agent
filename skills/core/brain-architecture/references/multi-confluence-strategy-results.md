# Estratégia Multi-Confluência SMC/ICT — Resultados Validados
## 28/05/2026

### Backtest 59d M15 + 90d H1 (5 pares forex)

| Métrica | Multi-Confluência | Silver Bullet puro |
|---------|-------------------|-------------------|
| Trades | 25 | 64 |
| Win Rate | **60.0%** | 23.4% |
| Profit Factor | **3.25** | 0.67 |
| Expectancy | +0.184R | -0.36R |
| Max Drawdown | 31.3 pips | 171.1 pips |

### Confluências (6, filtro >= 4):

1. HTF Alignment (MANDATORY) — H1 trend via swing structure
2. Killzone (MANDATORY) — London/NY Open/Close
3. Liquidity Sweep (MANDATORY) — M15 sweep + reversal
4. Fresh FVG — directional FVG no M15
5. Order Block — OB próximo válido
6. SMT Divergence — EURUSD↔GBPUSD, USDJPY↔EURJPY

### Melhores pares:
- GBPJPY: 71.4% WR, +129.4 pips
- USDJPY: 73-100% WR (dados reais)
- EURJPY: 65-67% WR

### Conclusão:
Filtros multi-confluência transformam Silver Bullet de -0.36R para +3.25 profit factor.
A diferença entre 23% e 60% WR são os filtros de qualidade. SEMPRE exigir >= 4 confluências.

### XAUUSD (ouro):
- Multi-confluência: 44.8% WR, PF 1.08, +3.50R
- Marginalmente lucrativo. Ouro reverte mais — usar TP 1.5:1 e risk 0.5%.
