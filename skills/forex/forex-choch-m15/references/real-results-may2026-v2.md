# Resultados Reais — Bot Forex CHoCH+FVG M15 (20-22 Mai 2026)

## Período: 20-22 de Maio de 2026
## Conta: OANDA Demo #1715539800

### Trades Fechados (12 trades com P&L)

| ID | Data | Par | Direção | Entry | Exit | P&L (pips) | Result |
|----|------|-----|---------|-------|------|------------|--------|
| T20260521_040102 | 21/05 | AUD/USD | SELL | 0.71266 | 0.71169 | +9.7 | WIN |
| T20260521_040111 | 21/05 | NZD/USD | SELL | 0.58613 | 0.58524 | +8.9 | WIN |
| T20260521_053030 | 21/05 | GBP/USD | BUY | 1.34396 | 1.34315 | -8.1 | LOSS |
| T20260521_053040 | 21/05 | EUR/USD | BUY | 1.16279 | 1.16090 | -18.9 | LOSS |
| T20260521_054527 | 21/05 | AUD/USD | BUY | 0.71301 | 0.71200 | -10.1 | LOSS |
| T20260521_110107 | 21/05 | GBP/USD | SELL | 1.34113 | 1.34219 | -10.6 | LOSS |
| T20260522_034556 | 22/05 | GBP/USD | SELL | 1.34261 | 1.34181 | +8.0 | WIN |
| T20260522_043052 | 22/05 | AUD/USD | SELL | 0.71388 | 0.71413 | -2.5 | LOSS |
| T20260522_043101 | 22/05 | NZD/USD | SELL | 0.58658 | 0.58569 | +8.9 | WIN |
| T20260522_101530 | 22/05 | GBP/USD | BUY | 1.34363 | 1.34216 | -14.7 | LOSS |
| T20260522_101540 | 22/05 | EUR/USD | BUY | 1.16077 | 1.16050 | -2.7 | LOSS |
| T20260522_101549 | 22/05 | AUD/USD | BUY | 0.71347 | 0.71271 | -7.6 | LOSS |

### Resumo

| Métrica | Valor |
|---------|-------|
| Total trades | 12 |
| Wins | 4 |
| Losses | 8 |
| **WR** | **33.3%** ⚠️ |
| P&L total | -39.7 pips |
| P&L 21/05 | -10.2 pips |
| P&L 22/05 | -29.5 pips |

### Por Par

| Par | Trades | W/L | WR | P&L |
|-----|--------|-----|-----|------|
| NZD/USD | 2 | 2W/0L | 100% | +17.8 |
| AUD/USD | 4 | 1W/3L | 25% | -10.5 |
| GBP/USD | 4 | 1W/3L | 25% | -25.4 |
| EUR/USD | 2 | 0W/2L | 0% | -21.6 |

### Conclusão

- **WR real (33.3%) está ABAIXO do backtest (72.6%)** — gap de 39pp
- **NZD/USD é o único par positivo** — restringir bot a este par até recuperar
- **WR<40% = bot DEVERIA estar bloqueado** pela regra, mas self-learning não aplicou
- **Correção urgente:** implementar verificação de WR dos últimos 20 trades ANTES de cada ciclo. Se <40%, pular ciclo.

### Causas Prováveis do Gap Backtest→Real

1. Backtest usou Yahoo Finance (dados de fechamento), execução real usa MT5 (spread + slippage)
2. SL muito apertado (2 pips) — ajustar para no mínimo 5 pips ou ATR-based
3. Horário: trades em horários de baixa liquidez (madrugada BRT) têm spread maior
4. CRT confirmation pode estar atrasando entrada (2ª vela fecha dentro do range)
