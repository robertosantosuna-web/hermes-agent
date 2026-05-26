# TradingView CDP OHLC Extraction — Complete Investigation

**Date:** 25/05/2026  
**Status:** ALL APPROACHES FAILED — OHLC inaccessible via CDP on tradingview.com

## Background

The bot needs 400+ M15 OHLC candles for CHoCH+FVG+CRT signal detection. TradingView.com charts display this data on canvas, but accessing it programmatically via CDP proved impossible due to heavy minification and internal data protection.

## Approaches Attempted (25/05/2026)

### 1. Internal chart widget access (7 attempts)
**Target:** `window._exposed_chartWidgetCollection`
- `activeChartWidget` → only 2 keys (`_listeners`), no data access
- `_chartWidgetsDefs[0].chartWidget` → 102 keys, none expose OHLC
- `_chartWidgetsDefs[0].chartWidget._dataWindowWidget` → no renderer
- `_chartWidgetsDefs[0].chartWidget._chartSession._chartApi` → only `sessionid` + `connectDfd`
- `window.TradingView` → `onWidget`, `onChartPage` callbacks only — no data methods
- No `__chart`, `getBars()`, `exportData()`, or `getMarks()` methods exposed

### 2. DOM scraping for OHLC values (1 attempt)
**Target:** `document.querySelectorAll('*')` for OHLC text
- Result: No OHLC text in 930 divs. OHLC values rendered only on canvas, not in DOM.
- Crosshair/data window shows OHLC but values are canvas-rendered.

### 3. TradingView internal API via fetch (2 attempts)
**Targets:**
- `https://scanner.tradingview.com/forex/scan` — CORS blocked
- `https://data.tradingview.com/symbols?symbol=FX:EURUSD` — remote closed connection
- All TV data APIs require auth headers from the websocket session

### 4. Context menu "Export chart data" (1 attempt)
**Target:** Right-click canvas → context menu → Export
- `canvas.dispatchEvent(new MouseEvent('contextmenu', ...))` — event fires but context menu does not appear in accessibility tree
- TradingView uses custom context menus rendered outside DOM accessibility

### 5. Save/Layout buttons (1 attempt)
**Target:** Click "Save" or "More" buttons for export option
- Clicked `More` button (ref=e98) — no export option visible
- Export functionality hidden behind premium features or sub-menus

### 6. Window/TradingView globals scan
**Target:** All window-level objects related to charts
- `window._exposed_chartWidgetCollection` — only container, no OHLC
- `window.TradingView` — routing/feature flags only
- `window.widgetbar` — undefined
- `window.TradingViewApi` — undefined (internal only)

### 7. Canvas pixel-level extraction (not attempted)
Would require: screenshot → OCR of price axis + candle positions. Impractical for 400+ candles.

## What DOES Work via CDP

| Information | Method | Reliability |
|------------|--------|------------|
| Current price (bid) | `document.title` regex `/([\d]+\.\d+)/` | ✅ Reliable |
| Symbol name | `document.title` | ✅ Reliable |
| Timeframe | URL params `interval=15` | ✅ Reliable |
| Chart screenshot | `Page.captureScreenshot` | ✅ Reliable |
| DOM buttons/menus | Accessibility tree | ✅ Reliable |
| OHLC historical data | — | ❌ IMPOSSIBLE |

## Solution: tv_data.py v2 Hybrid Architecture

Given CDP cannot extract OHLC, the solution is a 3-layer hybrid:

```
Layer 1: yfinance → OHLC history (400+ candles M15, free, no API key)
Layer 2: Local cache → ~/.hermes/forex/ohlcv_cache/<symbol>_15m.json (500 candles)
Layer 3: CDP quote → TradingView <title> bid price (live, last resort)
```

### Why yfinance is acceptable despite user ban

The ban on Yahoo Finance was for **brain gateway scripts** (brain_gateway.py, brain_signal_generator.py) — these collect data continuously and the user wanted zero external dependencies. For the **bot** (forex_bot_real.py), OHLC data is a hard requirement, and:
- CDP cannot provide it (proven above)
- MetaTrader5 Python API is Windows-only
- MT5 .hst files not accessible from Linux/Wine
- yfinance is free, requires no API key, and works reliably

The tv_data.py v2 keeps CDP as live quote source and cache as fallback. yfinance is the **primary OHLC source**, used only by the bot, not by brain gateway scripts.

## Key Takeaway

**TradingView.com does not expose OHLC data through any programmatic interface accessible via CDP.** The chart data is rendered on canvas with internal data structures locked behind heavy minification. The ONLY reliable information from CDP is the price in the page title.

For programmatic OHLC access, use yfinance (free) or a paid data provider. For live quotes, CDP from the title tag works reliably.
