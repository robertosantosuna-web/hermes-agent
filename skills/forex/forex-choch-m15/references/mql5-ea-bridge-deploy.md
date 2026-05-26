# MQL5 EA Bridge — Deployment Checklist (25/05/2026)

## Architecture

```
Python (hermes_mt5_bridge.py)
  → write JSON → Common/Files/hermes_cmd.json
  → EA (hermes_bridge.ex5) OnTimer() lê a cada 250ms
  → OrderSend() nativo MQL5
  → write JSON → Common/Files/hermes_resp.json
  → Python lê resposta
```

## Paths

| Resource | Path |
|----------|------|
| MT5 install | `~/.wine/drive_c/Program Files/MetaTrader 5 IC Markets Global/` |
| EA source | `MQL5/Experts/hermes_bridge.mq5` |
| EA compiled | `MQL5/Experts/hermes_bridge.ex5` |
| MetaEditor | `metaeditor64.exe` (Wine) |
| Common/Files | `~/.wine/drive_c/users/roberto/AppData/Roaming/MetaQuotes/Terminal/Common/Files/` |
| Cmd JSON | `Common/Files/hermes_cmd.json` |
| Resp JSON | `Common/Files/hermes_resp.json` |

## Compilation

```bash
# ⚠️ CRITICAL: Delete old .ex5 first — metaeditor does NOT overwrite
rm -f "/home/roberto/.wine/drive_c/Program Files/MetaTrader 5 IC Markets Global/MQL5/Experts/hermes_bridge.ex5"

cd "/home/roberto/.wine/drive_c/Program Files/MetaTrader 5 IC Markets Global"
DISPLAY=:99 WINEPREFIX="/home/roberto/.wine" \
  wine metaeditor64.exe /compile:"MQL5\Experts\hermes_bridge.mq5" /log
```

## IC Markets Netting — Filling Mode

`ORDER_FILLING_FOK` = **retcode 10030** (Unsupported filling mode).  
Use `ORDER_FILLING_IOC` (Immediate or Cancel) for Netting accounts.

In `hermes_bridge.mq5`:
```c
request.type_filling = ORDER_FILLING_IOC;  // NOT ORDER_FILLING_FOK
```

## Deploy on MT5

1. **Enable AutoTrading** — green gear icon on MT5 toolbar (disabled = retcode 10027)
2. Ctrl+N → Navigator → Expert Advisors → `hermes_bridge`
3. Drag onto any chart (e.g., USDJPY M15)
4. Click OK on config dialog
5. **After recompilation:** Right-click chart → Expert Advisors → Remove, then drag again. MT5 does NOT hot-reload EAs.

## Test

```bash
# Order
python3 ~/.hermes/scripts/hermes_mt5_bridge.py order EURUSD BUY 0.01

# Close all
python3 ~/.hermes/scripts/hermes_mt5_bridge.py close_all

# Account status
python3 ~/.hermes/scripts/hermes_mt5_bridge.py status
```

## Error Codes

| Retcode | Meaning | Fix |
|---------|---------|-----|
| 10027 | AutoTrading disabled | Click AutoTrading button on MT5 toolbar |
| 10030 | Unsupported filling mode | Change to `ORDER_FILLING_IOC` |
| timeout | EA not running | Check EA is attached to chart and AutoTrading enabled |

## Bot Integration

`forex_bot_real.py` (v5, 25/05) imports from `hermes_mt5_bridge`:
```python
from hermes_mt5_bridge import send_order
# place_choch_order() wrapper converts EUR/USD → EURUSD,
# calculates SL/TP (FVG gap × RR 3:1), calls send_order()
```

## Verified (25/05)

✅ BUY EURUSD 0.01 @ 1.16409 — ticket 1666320197  
✅ close_all — 1 position closed, 0 errors  
