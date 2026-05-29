# SMC Fractal Methodology — Absorbed from Dinei Chat Export (04-11/05/2026)

Source: Telegram chat export between Dinei (trader) and Lucas (Hermes Agent, GPT-5.5 via Codex).
Saved to: `forex/smc_fractal_dinei.md` and `forex/ict_concepts_luxalgo.pine`

## Fractal Principle

The fractal of a higher timeframe becomes the RANGE of the timeframe 2 levels below.
1 level below shows only the CHOCH (initial correction), not the full range.

```
Monthly  → reaches POI, starts correction
Weekly   → 1 level below → shows CHOCH of the correction
Daily    → 2 levels below → shows the fractal (range) of the Weekly
H4       → range of the Daily
H1       → range of the H4
M15/M5   → entries
```

## Pivot Validation (from Pine Script)

Pivots validated with `ta.pivothigh(high, len, 1)` / `ta.pivotlow(low, len, 1)`:
- **5 candles back (default)**: the pivot took liquidity from 5 previous candles
- **1 candle forward**: confirms it wasn't immediately violated
- Configurable `len` (3-10) — lower = more pivots = more sensitive
- This ensures every pivot is already a local liquidity grab

Key insight from Dinei: "the pivot always takes liquidity, unless there are fewer than 5 candles before it"

## MSS (Market Structure Shift)

From the ICT Concepts LuxAlgo code. MSS does NOT require breaking the opposite top/bottom:
1. Price makes a bullish leg (HH/HL)
2. Takes liquidity from the previous low
3. Returns → already considered structure shift

```pinescript
// MSS Bullish: close > previous pivot high AND last direction wasn't bullish
close > aZZ.y.get(iH) and aZZ.d.get(iH) == 1 and MSS.dir < 1
// MSS Bearish: close < previous pivot low AND last direction wasn't bearish  
close < aZZ.y.get(iL) and aZZ.d.get(iL) == -1 and MSS.dir > -1
```

## Order Block Definition

From the Pine Script — OB is the extreme of the segment BEFORE the breakout:
```pinescript
// After bullish breakout:
for i = 1 to (n - top.x)-1
    minima := math.min(min[i], minima)
    maxima := minima == min[i] ? max[i] : maxima
bullish_ob.unshift(ob.new(maxima, minima, loc))
```

OB bullish: lowest low of the segment before the bullish breakout
OB bearish: highest high of the segment before the bearish breakout
NOT "last contrary candle" — it's the full range of the segment.

## Killzones (from Pine Script)

```pinescript
NY:          time(..., '0700-0900', 'America/New_York')  // 07:00-09:00 NY
London Open: time(..., '0700-1000', 'Europe/London')     // 02:00-05:00 NY
London Close:time(..., '1500-1700', 'Europe/London')     // 10:00-12:00 NY
Asian:       time(..., '1000-1400', 'Asia/Tokyo')        // 20:00-00:00 NY
```

## TradingEconomics Calendar

**https://tradingeconomics.com/calendar** — accessible without Cloudflare (unlike Investing.com).
- HTTP 200 confirmed (25/05/2026)
- ~2MB of calendar data
- Filters by country, impact level
- Ideal for USD, EUR, GBP news

## Key Differences: Dinei's SMC vs Our Bot

| Aspect | Our Bot (V5) | Dinei's Method |
|--------|-------------|----------------|
| Pivot validation | Not automated (S/R manual) | 5+1 ta.pivothigh/low |
| MSS detection | CHoCH via FVG + CRT | Direct MSS + BOS from pivots |
| OB detection | Not used | Extremes of segment before breakout |
| Fractal nesting | Not used | HTF fractal → range 2 TFs below |
| News source | — | TradingEconomics Calendar |
| Timeframe | M15 only | M5/M1 entries from H1/H4 context |
| Killzones | UTC [6,7,15,16] | London/NY/Asia sessions |
