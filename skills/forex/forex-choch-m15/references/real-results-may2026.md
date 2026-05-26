# Trading Results — May 2026

⚠️ **ATUALIZADO 22/05:** Todos os resultados abaixo são PAPER TRADING. O MT5 nunca esteve conectado à OANDA (0/0Kb tráfego). Os preços vêm do Yahoo Finance, não do MT5. As ordens do `mt5_direct.py` eram enviadas via xdotool mas nunca executadas no servidor real. Considerar como simulação backtest, NÃO como trading real.

## May 20
| Time | Pair | Dir | Result | PnL |
|------|------|-----|--------|-----|
| 15:45 | NZD/USD | BUY | CLOSE_ALL | 0 |
| 16:00+ | NZD/USD | BUY | DUPLICATE x5 | dedup bug |

## May 21
| Time | Pair | Dir | Entry | SL | TP | Exit | PnL | Result |
|------|------|-----|-------|----|----|------|-----|--------|
| 04:01 | AUD/USD | SELL | 0.71266 | 0.71286 | 0.71206 | 0.71169 | +9.7 | WIN |
| 04:01 | NZD/USD | SELL | 0.58613 | 0.58633 | 0.58553 | 0.58524 | +8.9 | WIN |
| 05:30 | GBP/USD | BUY | 1.34396 | 1.34318 | 1.34629 | 1.34315 | -8.1 | LOSS |
| 05:30 | EUR/USD | BUY | 1.16279 | 1.16117 | 1.16765 | — | — | OPEN |
| 05:45 | AUD/USD | BUY | 0.71301 | 0.71225 | 0.71530 | 0.71200 | -10.1 | LOSS |
| 11:01 | GBP/USD | SELL | 1.34113 | 1.34160 | 1.33973 | 1.34219 | -10.6 | LOSS |

**Daily: 2W/3L, WR=40%, PnL=-$10.20**

## Backtest Reference
CRT+S/R: 113 trades, 72.6% WR, +733 pips (30 days, 4 pairs)
Real sample: 5 trades — too small to evaluate statistically.
