# Advanced ICT Concepts — Beyond FVG

*Discovered: 2026-05-24 — 3 agent delegation, ~135 resources audited*

The current strategy (CHoCH+FVG M15) covers only entry-level ICT. Three advanced concepts
build on top of FVG/OB to filter false signals and improve direction prediction.

## 1. Breaker Blocks (Failed Order Block Reversal)

**What:** An Order Block that failed to hold → becomes support/resistance for the reversal.
When price breaks through an OB and then returns to it, the OB flips role (support→resistance
or resistance→support).

**Why it matters:** OBs near FVGs can be misleading — if the OB already failed once,
the FVG is likely to fail too. Breaker Blocks tell you which OBs are still valid.

**Entry logic:**
1. Identify an OB that was broken (price closed beyond it)
2. Wait for price to return to that broken OB zone
3. Enter in the opposite direction of the original break
4. SL: beyond the breaker block + buffer

**Source:** https://innercircletrader.net/tutorials/ict-breaker-block-trading/ (free PDF)

## 2. Turtle Soup Pattern (False Breakout Fade)

**What:** Price breaks a previous swing high/low, traps breakout traders, then reverses.
The name comes from the "Turtle Traders" who traded breakouts — the pattern fades them.

**Why it matters for FVG:** A Turtle Soup often creates the liquidity sweep that
precedes a CHoCH+FVG setup. Detecting Turtle Soup = detecting the moment retail gets trapped.

**Entry logic:**
1. Price breaks swing high/low by a few pips
2. Candle immediately reverses and closes back inside the range
3. Enter in the reversal direction
4. SL: beyond the false breakout extreme

**Source:** https://innercircletrader.net/tutorials/ict-turtle-soup-pattern/ (free PDF)

## 3. Mitigation Blocks (Liquidity Grab Continuation)

**What:** A short-term counter-trend move that grabs liquidity (stops, breakout orders)
before continuing in the original direction. Different from Breaker Blocks — Breakers
signal reversal, Mitigation signals continuation.

**Why it matters:** Distinguishes between a genuine reversal and a liquidity grab.
Prevents entering against the trend on what looks like a CHoCH but is actually mitigation.

**Key difference Breaker vs Mitigation:**
- Breaker: OB broken → price returns → reversal
- Mitigation: OB broken briefly → liquidity grabbed → trend continues

**Source:** https://innercircletrader.net/tutorials/ict-mitigation-block-explained/ (free PDF)

## Integration with Current Strategy

```
FVG detected → Check if FVG is near a Breaker Block (OB that already failed)
             → Check for Turtle Soup (false breakout just occurred)
             → Check if this is a Mitigation Block (liquidity grab, not CHoCH)
             → Only then enter with FVG + CRT + S/R confirmation
```

Priority order for study: Turtle Soup → Breaker Blocks → Mitigation Blocks.

## Key Sources
- innercircletrader.net (free PDFs for all 3 concepts)
- ICTPDF.com (downloadable course materials)
- YouTube: Breaker Block (6u7kpCEVROc), Turtle Soup (XC6AL1mEZIQ), Mitigation (UqW5hxFx62Y)
