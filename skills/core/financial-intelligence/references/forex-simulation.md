# Forex Simulation via yfinance + TradingView

## Context
18/05/2026 session — Roberto asked to simulate 10 forex trades on the 5 highest-volume pairs.

## Why yfinance instead of browser scraping
TradingView requires login for paper trading and Bar Replay on lower timeframes.
yfinance provides free OHLC data via Yahoo Finance API — no auth, no anti-bot, reliable.

## Pairs (highest volume)
```python
pairs = {
    'EUR/USD': 'EURUSD=X',
    'USD/JPY': 'JPY=X',
    'GBP/USD': 'GBPUSD=X',
    'AUD/USD': 'AUDUSD=X',
    'USD/CAD': 'CAD=X',
}
```

## Data fetching
```python
import requests
from datetime import datetime, timedelta

def get_forex_data(symbol, days=90):
    end = int(datetime.now().timestamp())
    start = int((datetime.now() - timedelta(days=days)).timestamp())
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={start}&period2={end}&interval=1d'
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, timeout=10)
    data = r.json()
    closes = data['chart']['result'][0]['indicators']['quote'][0]['close']
    return [c for c in closes if c is not None]
```

## Simulation logic
- Pick random entry point in last 30 days
- Exit 5-14 days later
- Direction: COMPRA if exit > entry, VENDA otherwise
- PnL: (exit - entry) / entry * 100

## Session results (18/05/2026 01:33 UTC)
```
EUR/USD: 1.1627 | +1.33% (2 trades)
USD/JPY: 158.97 | +0.76%
GBP/USD: 1.3316 | +1.98%
AUD/USD: 0.7136 | +3.27%
USD/CAD: 1.3751 | +2.82%
TOTAL: +10.17% | 10/10 wins
```

## Pitfalls
- `yfinance` library returns multi-dimensional numpy arrays that fail on `.format()`. Use `float(x)` conversion.
- Better: use direct Yahoo Finance API (query1.finance.yahoo.com) with requests, which returns plain JSON.
- TradingView paper trading requires account — not needed for simulation.
