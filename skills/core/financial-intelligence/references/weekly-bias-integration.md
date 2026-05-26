# Weekly Bias Integration — V5 Macro Validation

## weekly_bias.json

Location: `~/.hermes/forex/weekly_bias.json`  
Updated: via Knowledge Bridge (agent → brain → validate → write)  
Consumed by: `forex_bot_real.py` → `load_weekly_bias()` → `apply_bias()` + `macro_validation_score()`

### Format

```json
{
  "week_start": "2026-05-25",
  "week_end": "2026-05-29",
  "updated": "2026-05-24T23:00:00+00:00",
  "summary": "Iran nuclear deal close → risk-on week. JPY weakness, commodity FX strength.",
  "macro_drivers": [
    "IRAN NUCLEAR DEAL: ...",
    "FED: Kevin Warsh new Chair. UMich 44.8 vs 48.2 = USD bearish.",
    "OIL: Iran deal = supply increase. Crude bearish."
  ],
  "pairs": {
    "USD/JPY": "BUY",
    "GBP/USD": "BUY",
    "EUR/USD": "NEUTRAL"
  },
  "pair_rationale": { ... },
  "risk_events": [
    {"date": "2026-05-25", "event": "Iran deal headlines / Sunday gap risk"},
    {"date": "2026-05-28", "event": "US GDP Q1 2nd estimate"},
    {"date": "2026-05-29", "event": "US PCE Inflation"}
  ],
  "source": "agent_knowledge_bridge_v2",
  "based_on": ["ForexLive Americas FX wrap", "Sky News Arabia Iran nuclear report", ...]
}
```

### How bias flows into the bot

```
weekly_bias.json
       ↓ load_weekly_bias()
       ↓
  apply_bias(signal, bias)        → score × 1.10 (aligned) / × 0.80 (contra)
  macro_validation_score(signal)  → 0-1 score (reject if < 0.3)
       ↓
  signal score = WR × 0.70 + macro_score × 30
```

### Macro validation keywords

The `macro_validation_score()` function in `forex_bot_real.py` scans `bias.summary` for these keywords:

| Keyword | Effect |
|---------|--------|
| `iran` or `risk-on` | USDJPY BUY +0.35, GBP/EUR BUY +0.20, SELL +0.05 |
| `fed` or `hawkish` | USDJPY BUY +0.10, GBP/EUR SELL +0.10 |
| `umich` or `bearish usd` | USDJPY SELL +0.10, GBP/EUR BUY +0.10 |

### FVG Trend Monitor

`~/.hermes/forex/fvg_trend.json` — updated by brain FVG analyzer:

```json
{
  "EURUSD": {"fvg_count": 93, "gap_avg_pips": 4.2, "prev_gap_avg": 3.3, "trend": "rising"},
  "GBPUSD": {"fvg_count": 104, "gap_avg_pips": 4.4, "prev_gap_avg": 3.5, "trend": "rising"}
}
```

Rising gap avg = increasing volatility = more reliable setups near killzones.

### Updating the bias (weekly workflow)

1. Agent reads brain discoveries: `knowledge_bridge.py read`
2. Extract macro insights (Iran, Fed, economic calendar, TradingView ideas)
3. Write `weekly_bias.json` with pair directions and rationale
4. Brain absorbs: `knowledge_bridge.py absorb brain`
5. Bot picks it up on next run — no config changes needed
