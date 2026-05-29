# Forex Bot Operations — Critical Fixes & Pitfalls (May 2026)

## AutoPilot Drawdown Logic (Fixed 27/05/2026)

### Problem
AutoPilot was closing ALL positions on tiny drawdowns, creating a cycle:
1. Bot opens 5 orders → equity drops $12 → AutoPilot sees drawdown > 3% → closes everything
2. Next tick: Bot opens 5 more orders → repeat
3. **Result:** 154 trades in one morning, none reaching take profit

### Root Cause
```python
# BEFORE (broken):
drawdown_pct = (1 - equity / 400) * 100  # $400 HARDCODED
if drawdown_pct > 3:  # $12 loss triggers close_all
```

The hardcoded $400 initial balance meant any loss over $12 triggered full position closure.

### Fix Applied
```python
# AFTER (fixed):
initial_balance = read_from_state_file() or balance  # Real MT5 balance
drawdown_pct = (1 - equity / max(initial_balance, 1)) * 100
if drawdown_pct > 15:  # 15% drawdown (was 3%)
    close_all()
    write_cooldown_file()  # 30min cooldown
```

### Additional Safeguards Added
- **Daily trade limit:** `MAX_DAILY_TRADES = 20` (prevents overtrading)
- **Cooldown period:** 30 minutes after mass close (prevents immediate re-entry)
- **State file:** `~/.hermes/forex/autopilot_state.json` stores initial balance

## Multi-Strategy Bot Config

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| MAX_POSITIONS | 8 | Per Neural Link approval (26/05) |
| MAX_DAILY_TRADES | 20 | Prevents overtrading |
| RISK_PERCENT | 1.0 | Per trade risk |
| DAILY_STOP_PERCENT | 5.0 | Max daily loss |
| DRAWDOWN_ALERT_PERCENT | 3.0 | Alert only (no close) |
| MIN_SL_PIPS | 15 | IC Markets STOPLEVEL minimum |

## Related Files
- Bot: `~/.hermes/scripts/forex_bot_multi.py` (cron `ca8d82dc9fa5`, */15 min)
- AutoPilot: `~/.hermes/scripts/forex_autopilot.py` (cron `cdbae3c13baa`, */5 min)
- Bridge: `~/.hermes/scripts/hermes_mt5_bridge.py`
- Trade log: `~/.hermes/forex/trade_log.json`

## Data Source Preference

- **TradingView** para análise de sinais e preços (via CDP browser :9222)
- **Yahoo Finance** apenas para replay/backtest
- **Brain browser** usa porta :9222 (Brave real), não :9223 (headless frequentemente offline)
