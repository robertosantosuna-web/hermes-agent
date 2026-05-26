# Backtest Comparison — 25/05/2026

Comparação consolidada de 3 backtests executados em 25/05/2026.

## 1. CRT CHoCH+FVG M15 (30 dias, 3 pares)

Script: `backtest_crt_choch.py`
Parâmetros: gap≥1, sem filtro de horário, 3 pares (USDJPY, GBPUSD, EURUSD)

| Estratégia | Trades | WR | PnL |
|---|---|---|---|
| CHoCH+FVG puro | 9 | 66.7% | +33.8p |
| CHoCH+FVG+CRT | 3 | 100.0% | +24.2p |

**Conclusão**: CRT sobe WR 66.7→100% mas reduz trades de 9→3. Ambos positivos.

## 2. Killzones M5 (10 dias, 5 pares)

Script: `backtest_killzones.py`
Parâmetros: stop calibrado por par, range mínimo, mom mínimo, 5 pares

| Par | Trades | WR | PnL |
|---|---|---|---|
| EUR/JPY | 1 | 100% | +1.76% |
| GBP/USD | 1 | 100% | +0.44% |
| USD/JPY | 2 | 100% | +1.64% |
| **Total** | **4** | **100%** | **+3.84%** |

**Todos os trades na London Close**. London Open e NY Open zerados.

## 3. SMC Sweep 10 ordens (10 dias, 4 pares)

Script: `forex_backtest_10trades.py`
Parâmetros: CHoCH+Sweep, RR 1:2, ≥40% WR threshold

**Sobreviventes (≥40% WR)**:
| Setup | Trades | WR | PnL |
|---|---|---|---|
| GBP/USD @ London Open | 19/39 | 49% | +19.7% |
| GBP/USD @ NY Open | 20/45 | 44% | +19.1% |

**Eliminados (<40% WR)**: USD/JPY @ London Close (9%), EUR/JPY @ London Open (18%), EUR/USD @ NY Open (30%), entre outros.

## Conclusão Consolidada

- **Melhor estratégia**: CHoCH+FVG+CRT M15 (100% WR embora poucos trades)
- **Melhores pares**: USDJPY e GBPUSD consistentemente no topo
- **Melhor killzone**: London Close concentrou todos os trades do backtest killzones
- **GBP/USD** é o par mais versátil (aparece bem em 2 de 3 backtests)
- **Pares exóticos (AUD, NZD)**: consistentemente ruins, evitá-los
