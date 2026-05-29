# Risco Exponencial Dinâmico

## Objetivo
Crescimento não-linear da conta. Quanto maior o saldo e melhor o WR,
mais agressivo o risco por trade.

## Implementação
Função `calculate_dynamic_risk(balance, wr_real)` em `forex_bot_multi.py`.

## Tiers de Risco Base
| Saldo | Risco Base |
|-------|-----------|
| < $600 | 2% |
| $600-1000 | 3% |
| $1000-2000 | 5% |
| $2000-5000 | 7% |
| > $5000 | 10% |

## Bônus/Penalidade por WR
- WR > 80%: +3%
- WR > 70%: +2%
- WR > 60%: +1%
- WR < 40%: -1%
- WR < 30%: -2% (mínimo 1%)

## Volume
```python
volume, risk_pct = calculate_volume(balance, sl_pips, pair, wr_real)
```
Calcula lotes baseado no risco % do saldo, SL em pips, e pip value do par.
Mínimo 0.01, máximo 0.50 (conta pequena).

## Curva de exemplo
- $400 (WR 50%): 0.05 lot, risco $8
- $600 (WR 65%): 0.16 lot, risco $24
- $1000 (WR 65%): 0.40 lot, risco $60
- $2000 (WR 70%): 1.20 lot, risco $180
- $5000 (WR 75%): 4.00 lot, risco $600
