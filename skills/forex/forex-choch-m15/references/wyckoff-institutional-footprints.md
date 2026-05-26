# Wyckoff Methodology — Institutional Footprints Without Order Flow Data

*Discovered: 2026-05-24 — wyckoffanalytics.com, newtraderu.com*

Wyckoff's method detects institutional activity using ONLY price and volume —
no DOM, footprint charts, or order flow data required. This is directly applicable
to the current M15 strategy which operates on pure candlestick data.

## The Three Fundamental Laws

1. **Supply & Demand:** Price moves to balance supply and demand. Excess demand → rally.
   Excess supply → decline. Equilibrium → range.
2. **Cause & Effect:** The size of the accumulation/distribution range (cause) determines
   the size of the subsequent move (effect). Use horizontal counting.
3. **Effort vs Result:** The relationship between volume (effort) and price movement (result).
   THIS is the most actionable concept for M15.

## Effort vs Result — The Killer Signal

> "High volume + small candle = absorption. The next candle reverses."

| Effort (Volume) | Result (Price) | Signal | Next Move |
|-----------------|----------------|--------|-----------|
| HIGH | SMALL (doji/spinning top) | Absorption | REVERSAL |
| HIGH | LARGE (wide range candle) | Commitment | CONTINUATION |
| LOW | LARGE | No resistance | CONTINUATION (easy move) |
| LOW | SMALL | No interest | CONTINUE RANGE |

### Practical M15 application:
- CRT candle with HIGH volume + closes in middle = exhaustion → next candle reverses
- FVG with LOW volume = no institutional participation → low probability
- Break of structure with LOW volume = false breakout (Turtle Soup)

## Spring and Upthrust — Stop Hunt Patterns

### Spring (False Breakdown)
1. Price breaks below a well-defined support level
2. Volume spikes (stop losses triggered)
3. Price IMMEDIATELY reverses back above support
4. → BUY signal. Institutions absorbed all the sell stops.

### Upthrust (False Breakout)
1. Price breaks above a well-defined resistance level
2. Volume spikes (breakout traders enter)
3. Price IMMEDIATELY reverses back below resistance
4. → SELL signal. Institutions sold into the breakout buying.

### Integration with Turtle Soup:
Spring = Turtle Soup at support (BUY)
Upthrust = Turtle Soup at resistance (SELL)
These are essentially the same pattern described by two different methodologies.

## Accumulation/Distribution Schematics

### Accumulation Phases (bottoming before rally):
- **PS** (Preliminary Support): First buying appears after decline
- **SC** (Selling Climax): Panic selling, wide spread, high volume
- **AR** (Automatic Rally): Natural bounce after climax
- **ST** (Secondary Test): Price returns to SC zone on lower volume
- **Spring**: Shakeout below SC, traps late shorts
- **LPS** (Last Point of Support): Higher low on lower volume
- **SOS** (Sign of Strength): Rally above AR high

### Distribution Phases (topping before decline):
- **PSY** (Preliminary Supply): First selling appears after rally
- **BC** (Buying Climax): Euphoric buying, wide spread, high volume
- **AR** (Automatic Reaction): Natural decline after climax
- **ST** (Secondary Test): Price returns to BC zone on lower volume
- **UT** (Upthrust): Shakeout above BC, traps late buyers
- **UTAD** (Upthrust After Distribution): Final trap before decline
- **LPSY** (Last Point of Supply): Lower high on lower volume
- **SOW** (Sign of Weakness): Decline below AR low

## Practical M15 Detection

Current M15 strategy already detects swings (highs/lows). Adding Wyckoff:

1. **Swing quality check:** Was the swing high made on declining volume? → Distribution UT
2. **Range detection:** Is price in a 20-30 candle range? → Look for Spring/Upthrust
3. **FVG + Effort/Result:** FVG on low volume = skip. FVG on high volume = enter.

## Key Sources
- Wyckoff Analytics: https://www.wyckoffanalytics.com/wyckoff-method/
- Wyckoff Spring (detailed): https://www.newtraderu.com/2022/03/09/wyckoff-spring/
- Accumulation/Distribution phases: https://www.newtraderu.com/2020/08/18/richard-wyckoff-theory-of-accumulation-and-distribution/
- YouTube: https://www.youtube.com/@WyckoffAnalytics
