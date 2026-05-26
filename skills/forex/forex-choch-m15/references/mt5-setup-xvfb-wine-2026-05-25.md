# MT5 Setup — Xvfb :99 + Wine (25/05/2026)

## Current Working State

| Component | Value |
|-----------|-------|
| Wine prefix | `~/.wine_mt5/` |
| MT5 exe | `C:\Program Files\MetaTrader 5\terminal64.exe` |
| Display | `:99` (Xvfb, 1280x900x24) |
| Account | IC Markets Demo, **Netting** (Raw Trading Ltd) |
| Window title | `MetaTrader 5 - Netting - EURUSD,H1` |

## Startup Sequence

```bash
# 1. Start Xvfb if not running
Xvfb :99 -screen 0 1280x900x24 &

# 2. Verify display
xdpyinfo -display :99 | head -3

# 3. Start MT5
DISPLAY=:99 WINEPREFIX=~/.wine_mt5 wine "C:\\Program Files\\MetaTrader 5\\terminal64.exe" &

# 4. Wait and verify
sleep 10
DISPLAY=:99 xdotool search --name "MetaTrader"
DISPLAY=:99 xdotool getwindowname <WID>
```

## Execution (xdotool :99)

All order executors use `xdotool` with `DISPLAY=:99`:
- `mt5_order_executor.py` — primary (F9 + Alt+B/S)
- `mt5_executor.py` — same approach
- `mt5_direct.py` — used by forex_bot_real.py

```bash
python3 mt5_order_executor.py --status
python3 mt5_order_executor.py BUY USDJPY 0.01 --sl 159.00 --tp 159.45
```

## Pitfalls

- Xvfb does NOT persist across reboots
- No window manager on Xvfb — `windowactivate` fails, use `windowfocus`
- `MetaTrader5` pip package is Windows-only — do NOT attempt install on Linux
- Old scripts used `DISPLAY=:0` (wrong) and `ydotool` (works but less reliable than xdotool on Xvfb)
- Wine prefix was `~/.mt5` in old scripts — actual is `~/.wine_mt5`
- Account is **Netting** not Hedge (verified from window title 25/05)
