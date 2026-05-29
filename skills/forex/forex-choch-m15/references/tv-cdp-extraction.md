# CDP TradingView OHLC Extraction

## Tool: tv_ohlc_extractor.py

Location: `/home/roberto/tv_ohlc_extractor.py`

Extracts OHLCV candles directly from TradingView charts via Brave :9222 WebSocket CDP.

### Usage
```bash
python3 /home/roberto/tv_ohlc_extractor.py --symbol 'FX:EURUSD' --interval 1
python3 /home/roberto/tv_ohlc_extractor.py --symbol 'FX:EURUSD' --interval 1 --output /tmp/eurusd.json
```

### Technical Details

- Connects to Brave CDP at `http://localhost:9222`
- Finds existing TradingView tab or creates new one
- Extracts from: `_exposed_chartWidgetCollection.activeChartWidget._value._modelWV._value.m_model._panes[0].m_mainDataSource.data().m_bars._items[]`
- Bar format: `{time: unix_ts, open, high, low, close, volume}`
- Output: JSON file with `{symbol, interval, count, bars: [...]}`
- ~544 candles M1 (9 hours of data)

### M1 Data Source Priority

```
fetch_ohlcv(symbol, interval='1m'):
  1. TradingView CDP (primary — no scale errors)
  2. yfinance (fallback — limited to 7 days)
  3. Local cache
```

### Symbol Mapping
```python
'EURUSD=X' → 'FX:EURUSD'
'GBPUSD=X' → 'FX:GBPUSD'
'USDJPY=X' → 'FX:USDJPY'
'GC=F'     → 'TVC:GOLD'
```

### Pitfalls
- Brave :9222 blocks session-based CDP (attachToTarget, Runtime.evaluate via sessionId) but WebSocket direct connection WORKS
- Must have tradingview.com tab already open and logged in
- Extraction takes ~5 seconds per symbol
- Data only covers what's visible on the chart (~544 bars for M1)
