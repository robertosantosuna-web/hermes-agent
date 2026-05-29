# TvDatafeed — Dados Diretos do TradingView (27/05/2026)

## Instalação
```bash
pip install git+https://github.com/rongardF/tvdatafeed.git
```

## Uso básico
```python
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

# Forex: exchange='FX'
df = tv.get_hist(symbol='GBPJPY', exchange='FX', interval=Interval.in_15_minute, n_bars=200)

# Ouro: exchange='OANDA'  
df = tv.get_hist(symbol='XAUUSD', exchange='OANDA', interval=Interval.in_30_minute, n_bars=100)
```

## Colunas
DataFrame retornado usa colunas **minúsculas**: `open`, `high`, `low`, `close`, `volume`
NÃO usar `df['Open']` — vai dar KeyError.

## Comparação com Yahoo Finance
| Fonte | GBPJPY 15m | EURUSD 15m | GBPUSD 15m |
|-------|-----------|-----------|-----------|
| yfinance | 6 FVGs | 9 FVGs | 18 FVGs |
| **TvDatafeed** | **24 FVGs** | **42 FVGs** | **60 FVGs** |

TvDatafeed retorna 3-6x mais dados de qualidade.

## Limitações
- Modo "nologin": sem autenticação → dados podem ser limitados em volume
- Warning "you are using nologin method, data you access may be limited" é normal e inofensivo
- XAUUSD requer `exchange='OANDA'` (não 'FX')

## Integração nos scripts
- `chart_renderer.py`: TvDatafeed primário → yfinance fallback
- `terminal_chart.py`: TvDatafeed exclusivo
- `tv_data.py`: Ainda usa yfinance (legado, migrar futuramente)
