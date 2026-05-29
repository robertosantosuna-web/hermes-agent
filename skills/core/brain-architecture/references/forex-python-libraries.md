# Python Libraries for Forex — ENTIDADE v3.0 (28/05/2026)

## Installed & Tested

| Library | Version | Import | Function |
|---------|---------|--------|----------|
| **smart-money-concepts** | 0.0.27 | `from smartmoneyconcepts import smc` | SMC/ICT: fvg(), ob(), liquidity(), bos_choch(), swing_highs_lows(), retracements(), previous_high_low() |
| **backtesting.py** | 0.6.5 | `from backtesting import Backtest, Strategy` | Interactive backtesting with HTML output |
| **quantstats** | 0.0.81 | `import quantstats as qs` | Sharpe, VaR, drawdown, tearsheet |
| **mplfinance** | 0.12.10 | `import mplfinance as mpf` | Candlestick charts |
| **forex-python** | 1.9.2 | `from forex_python.converter import CurrencyRates` | Currency conversion |
| **yfinance** | 1.3.0 | `import yfinance as yf` | Yahoo Finance OHLC data |

## smart-money-concepts Usage

```python
import pandas as pd
from smartmoneyconcepts import smc

# Load OHLC data
df = pd.DataFrame({'open': [...], 'high': [...], 'low': [...], 'close': [...], 'volume': [...]})

# 1. Detect swing highs/lows (required first)
swings = smc.swing_highs_lows(df)

# 2. Fair Value Gaps
fvg = smc.fvg(df)  # Returns DataFrame with FVG levels

# 3. Order Blocks
ob = smc.ob(df, swings)  # Requires swings

# 4. Liquidity Sweeps
liquidity = smc.liquidity(df, swings)  # Requires swings

# 5. Break of Structure / Change of Character
bos_choch = smc.bos_choch(df, swings)  # Requires swings

# 6. Retracements
fibs = smc.retracements(df, swings)  # Fibonacci levels

# 7. Previous High/Low
prev_hl = smc.previous_high_low(df)

# 8. Trading Sessions
# sessions = smc.sessions(df, session='London')  # Needs session name
```

## backtesting.py Usage

```python
from backtesting import Backtest, Strategy

class SMCStrategy(Strategy):
    def init(self):
        # Pre-compute indicators
        self.swings = self.I(lambda x: smc.swing_highs_lows(x), self.data.df)
    
    def next(self):
        # Trading logic per candle
        if self.data.Close[-1] > self.data.Open[-1]:
            self.buy(sl=self.data.Low[-1], tp=self.data.Close[-1] * 1.02)

bt = Backtest(data, SMCStrategy, cash=10000)
stats = bt.run()
bt.plot()
```

## quantstats Usage

```python
import quantstats as qs

# Generate HTML report
qs.reports.html(returns, output='report.html')

# Key metrics
qs.stats.sharpe(returns)
qs.stats.max_drawdown(returns)
qs.stats.win_rate(returns)
```

## Not Installed (Python 3.14 incompatibility)

- **pandas-ta** — Only supports Python 3.10-3.13
- Alternative: use `finta` or calculate indicators manually with pandas/numpy
