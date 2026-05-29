# STOPLEVEL Forensic Analysis (26/05/2026)

## Root Cause of Zero Profit

After analyzing 7 real trades on IC Markets demo ($399 account), the #1 reason for losses is **SL silently rejected by broker**.

### The Silent Kill

```
Bot sends:  OrderSend(EURUSD BUY, SL=1.34925, TP=1.35065)  → SL = 3.5 pips
MT5 broker: STOPLEVEL minimum = 8 pips
MT5 action: Opens position WITHOUT stop loss (retcode=10009 success!)
Result:    Price drops 27.6 pips → loss = -$27.60 instead of -$3.50
```

### Trade Evidence

| Trade | SL Config | STOPLEVEL Min | Actual Loss | Violation |
|-------|-----------|---------------|-------------|-----------|
| GBP/USD BUY | 3.5p | ~8p | -27.6p | **7.9×** |
| GBP/JPY BUY | 3.0p | ~8p | -14.4p | **4.8×** |
| GBP/USD_KZ BUY | 3.5p | ~8p | -49.4p | **14.1×** |
| USD/JPY BUY | 2.6p | ~8p | -3.1p | 1.2× |
| EUR/JPY BUY | 6.6p | ~8p | -7.8p | 1.2× |

### Fix Applied (3 layers)

1. **EA Bridge (.mq5):** Validates `SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL)` before OrderSend. Rejects if SL < 1.5× minimum.
2. **Python Bot:** `MIN_SL_PIPS = 15` — all signals now require minimum 15 pip stop loss.
3. **Dynamic Volume:** `calculate_volume(balance, sl_pips, pair)` — sizes position so risk = 2% of balance regardless of SL size.

### Related: Dynamic Volume

```python
RISK_PERCENT = 2.0  # % of balance per trade
def calculate_volume(balance, sl_pips, pair):
    pip_val = PIP_VALUES.get(pair, 0.10)
    risk_dollar = balance * RISK_PERCENT / 100.0
    lots_001 = risk_dollar / (max(sl_pips, MIN_SL_PIPS) * pip_val)
    return max(0.01, round(lots_001 / 100, 2))
```

With $399 balance, SL=15p:
- EURUSD: 0.05 lots, risk $7.50
- USDCAD: 0.07 lots, risk $7.77
