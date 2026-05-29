# CDP TradingView OHLC Extraction

## Extractor Script
`/home/roberto/tv_ohlc_extractor.py` — CLI tool to extract OHLCV from TradingView charts via Brave :9222 CDP.

```bash
python3 /home/roberto/tv_ohlc_extractor.py --symbol 'FX:EURUSD' --interval 1
python3 /home/roberto/tv_ohlc_extractor.py --symbol 'TVC:GOLD' --interval 1 --output /tmp/xau.json
```

## Internal JS Path (Critical)
The data lives at:
```
_exposed_chartWidgetCollection
  .activeChartWidget._value
  ._modelWV._value
  .m_model._panes[0]
  .m_mainDataSource
  .data().m_bars._items[]
```

Bar format: `{index, value: [timestamp, open, high, low, close, volume]}`

## Integration in tv_data.py
`fetch_ohlcv(symbol, interval='1m')` tries CDP first, falls back to yfinance:
- CDP: ~544 candles (9 hours), 5s latency
- yfinance: ~6700 candles (5 days), 2s latency
- For backtest: use yfinance chunking (7d blocks × 4 = 28 days)

## Column Normalization Pitfall
yfinance returns lowercase columns (`h`, `l`, `c`) for daily data and uppercase (`High`, `Low`, `Close`) for intraday. Always normalize:
```python
col_map = {}
for c in df.columns:
    cl = c.lower()
    if cl in ('high','h'): col_map['h'] = c
    elif cl in ('low','l'): col_map['l'] = c
    elif cl in ('close','c'): col_map['c'] = c
```

## ATR/DMI Calculation (no talib dependency)
```python
n = 15; h = highs[-n:]; l = lows[-n:]; c = closes[-n:]
tr = np.maximum(h-l, np.maximum(abs(h-np.roll(c,1)), abs(l-np.roll(c,1))))
tr[0] = h[0]-l[0]
atr = np.mean(tr[-14:]) / pip

up = h - np.roll(h,1); dn = np.roll(l,1) - l; up[0] = dn[0] = 0
pdm = np.where((up>dn)&(up>0), up, 0)
ndm = np.where((dn>up)&(dn>0), dn, 0)
av = np.mean(tr[-14:])
pdi = 100 * np.mean(pdm[-14:]) / av
ndi = 100 * np.mean(ndm[-14:]) / av
trending = (bias=='BUY' and pdi>ndi) or (bias=='SELL' and ndi>pdi)
```
