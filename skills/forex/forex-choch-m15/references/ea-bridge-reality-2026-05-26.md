# EA Bridge Reality Check — 26/05/2026

## What works
- `hermes_mt5_bridge.py status` — ALWAYS works. Returns balance, equity, positions.
- `send_order` WITHOUT SL/TP — works when EA is fresh (before first crash).
- EA compiles with `MetaEditor64.exe` (case-sensitive!) on Xvfb :99.

## What doesn't work
- `send_order` WITH SL/TP → retcode 10016 (Invalid stops) OR timeout (EA crash).
- `close_all` → ALWAYS timeout (EA reads cmd, deletes file, never writes response).
- After first `send_order` failure, EA stops responding to ANY command (including status).
- Recovery: Remove EA from chart → Ctrl+N → drag back → OK.

## Why orders fail
1. **EA crashes on OrderSend()** — the MQL5 code looks correct but the .ex5 crashes inside DoOrder(). Print() debug added 26/05 but .ex5 not tested (EA needs re-deploy).
2. **Account is HEDGE** (not Netting as previously documented). SELL does not close BUY — it opens separate position.
3. **Possible cause:** SymbolInfoDouble returning 0 for ASK/BID → OrderSend with price=0 → crash.

## Bot fixes applied (26/05)
- `place_choch_order()`: returns None instead of raising RuntimeError on failure.
- `run_analysis()`: skips signals when `result is None`.
- Fallback: if bridge fails → `mt5_direct.py` (ydotool) via Desktop Daemon.
- `calculate_max_risk_sl`: `pip_dollar = volume * 10.0` (was `100000 * pip_val`, 100x off for JPY).

## Diagnostic commands
```bash
# Is MT5 running?
pgrep -a terminal64

# Is EA alive?
python3 scripts/hermes_mt5_bridge.py status

# Stuck command file?
ls -la ~/.wine/.../Common/Files/hermes_cmd.json
# If exists → EA not reading → remove & redeploy EA

# Clean slate
rm -f ~/.wine/.../Common/Files/hermes_*.json
```

## When server dies
- MT5 log shows: "connection lost" → "scanning network" → "authorized on ICMarketsSC-Demo"
- Bot cron `21f7caf29606` should be PAUSED during server issues.
- Resume: `hermes cron resume 21f7caf29606`
