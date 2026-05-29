# TradingView OHLC Extraction via CDP (29/05/2026)

## Discovery
Brave :9222 WebSocket CDP **works** for TradingView data extraction even though HTTP session-based CDP commands are blocked. The key is using `websockets.connect(ws_url)` directly to the `webSocketDebuggerUrl`.

## Internal Data Path
```
window._exposed_chartWidgetCollection
  .activeChartWidget._value
  ._modelWV._value
  .m_model._panes[0]
  .m_mainDataSource
  .data().m_bars._items[]
```

Each bar: `{index, value: [timestamp, open, high, low, close, volume]}`

## Working Script
`/home/roberto/tv_ohlc_extractor.py` — CLI tool:
```bash
python3 tv_ohlc_extractor.py --symbol 'FX:EURUSD' --interval 1
python3 tv_ohlc_extractor.py --output /tmp/data.json
```

## Integration
`/home/roberto/.hermes/scripts/tv_data.py` → `_tv_cdp_fetch()` calls extractor via subprocess. `fetch_ohlcv(symbol, interval='1m')` uses CDP as primary source, yfinance as fallback.

## Pitfalls
- Brave MUST be running with `--remote-debugging-port=9222`
- `PUT /json/new?url` works for navigation but Runtime.evaluate via sessionId is BLOCKED
- WebSocket `websockets.connect(ws_url)` bypasses the block
- Tab reuse is critical — each new tab = ~200MB RAM
- Output JSON format: `{bars: [{time, open, high, low, close, volume}]}`
- ~544 candles available in chart memory (varies by zoom level)
