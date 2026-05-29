# GitHub Libraries para Forex — 28/05/2026

## Instaladas e testadas

| Biblioteca | Versão | Função |
|-----------|--------|--------|
| smartmoneyconcepts | 0.0.27 | FVG, OB, Liquidity, BOS/CHoCH, Swings, Retracements |
| backtesting | 0.6.5 | Backtest interativo com HTML |
| quantstats | 0.0.81 | Sharpe, VaR, drawdown, tearsheets |
| mplfinance | 0.12.10 | Gráficos de candles |
| forex-python | 1.9.2 | Câmbio e conversão forex |
| yfinance | 1.3.0 | Yahoo Finance dados |

## SMC/ICT API (smartmoneyconcepts.smc)

```python
from smartmoneyconcepts import smc
swings = smc.swing_highs_lows(df)
fvgs = smc.fvg(df)
obs = smc.ob(df, swings)
liquidity = smc.liquidity(df, swings)
bos_choch = smc.bos_choch(df, swings)
retracements = smc.retracements(df, swings)
prev_hl = smc.previous_high_low(df)
sessions = smc.sessions(df, session='London')
```

Substitui ~200 linhas de código manual de detecção FVG/OB.

## Pendentes (Python 3.14 incompatível)

- pandas-ta: limite Python 3.13
- finta: alternativa para indicadores técnicos

## Stack recomendado para instalação futura

- vectorbt: backtesting vetorizado
- gym-anytrading + FinRL: RL para trading
- mt5linux: MT5 no Linux via Wine
- openbb: 100+ fontes de dados unificadas