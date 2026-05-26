# Order Flow & Market Microstructure — Predicting Direction

*Discovered: 2026-05-24 — 3 agent delegation, ~45 advanced order flow resources*

The current strategy relies purely on price action (candles, swings, patterns).
Order flow analysis adds a second dimension: WHO is driving the move and whether
the move is genuine or about to exhaust.

⚠️ Current limitation: Yahoo Finance provides no volume/tick data for forex.
These techniques require futures data or CFD broker data (MT5 can provide tick
volume which is a proxy for real volume).

## Delta Divergence — The Most Actionable Signal

**Delta** = aggressive buying volume - aggressive selling volume per candle.
When price moves up but delta moves down → hidden selling → reversal imminent.

### Classic Divergence Patterns

| Price | Delta | Signal | Meaning |
|-------|-------|--------|---------|
| Higher High | Lower High | BEARISH | Buyers exhausting, sellers absorbing |
| Lower Low | Higher Low | BULLISH | Sellers exhausting, buyers absorbing |
| Double Top | Declining Delta | BEARISH | Each push up has less buying behind it |

### Key sources:
- ATAS: https://atas.net/blog/what-is-delta/
- ForexBee: https://forexbee.co/cumulative-delta-divergence/

## CVD (Cumulative Volume Delta) — Trend Confirmation

CVD = running total of delta. If price is rising but CVD is flat or falling,
the trend lacks institutional support and is likely to reverse.

### CVD Divergence Strategy (Bookmap):
1. Identify trend on price chart
2. Check CVD direction over same period
3. If CVD diverges from price → exhaustion signal
4. Enter when price breaks structure in CVD's direction
5. SL: recent swing, TP: 3× SL

Source: https://bookmap.com/blog/how-cumulative-volume-delta-transform-your-trading-strategy

## Absorption Detection (Trader Dale)

**Absorption** = large volume at a level without price advancing.
Institutions are absorbing all opposing orders. The level will hold.

### How to detect without order flow data:
- Large candle wick rejecting a level + high relative volume
- Multiple candles with long wicks at same price zone
- Price repeatedly touching a level without breaking

Source: https://www.trader-dale.com/order-flow-analysis-how-to-use-absorption-delta-to-confirm-trade-entry-13th-may-25/

## POC (Point of Control) Migration

POC = price level with the most volume traded. When POC migrates:
- Upward migration = bullish (institutions accumulating higher)
- Downward migration = bearish (institutions distributing lower)
- Stationary POC = range/consolidation

## Practical Integration with Current M15 Strategy

The bot currently uses Yahoo Finance which has NO volume data for forex.
To integrate order flow:

**Option A — MT5 Tick Volume (proxy):** MT5 provides tick count per candle.
Tick volume correlates ~70-80% with real volume in forex. Module can:
1. Read MT5 tick volume via OCR or exported CSV
2. Calculate tick delta (uptick - downtick)
3. Apply delta divergence filter to FVG signals

**Option B — Futures COT Data:** Check CME futures positioning weekly.
If commercials are net long and retail is net short → bullish bias.

**Option C — Sentiment as Proxy:** Myfxbook/Dukascopy retail positioning.
Extreme retail long (>70%) = potential short (contrarian).

## Implementation Priority
1. MT5 tick volume extraction (available now via IC Markets demo)
2. COT positioning check (weekly, free via Barchart)
3. Sentiment check (real-time, free via Myfxbook)
4. Full delta/CVD (requires futures data feed — paid)
