# MT5 Order via MQL5 EA Bridge (25/05/2026)

## Overview

Instead of keyboard automation (F9, Alt+B, ydotool), use a native MQL5 Expert Advisor running inside MT5 that reads JSON commands from a file and executes `OrderSend()` directly.

**Advantage:** No dependency on window focus, Wayland/Wine keyboard quirks, or screen visibility. The EA runs on MT5's internal timer and processes commands autonomously.

## Architecture

```
Python (hermes_mt5_bridge.py)
  └─ write JSON → Common/Files/hermes_cmd.json
                  ↓
MT5 EA (hermes_bridge.ex5, OnTimer 250ms)
  └─ FileOpen → parse JSON → OrderSend() → FileWrite JSON response
                  ↓
Python ← read ← Common/Files/hermes_resp.json
```

## Files

| File | Location | Purpose |
|------|----------|---------|
| `hermes_bridge.mq5` | `MQL5/Experts/` | MQL5 source code |
| `hermes_bridge.ex5` | `MQL5/Experts/` | Compiled EA (19,644 bytes) |
| `hermes_mt5_bridge.py` | `~/.hermes/scripts/` | Python client |
| `hermes_cmd.json` | `Common/Files/` | Command file (auto-deleted after read) |
| `hermes_resp.json` | `Common/Files/` | Response file |

## MT5 Paths (IC Markets Global, Wine)

```
MQL5 Experts:  ~/.wine/drive_c/Program Files/MetaTrader 5 IC Markets Global/MQL5/Experts/
Common Files:  ~/.wine/drive_c/users/roberto/AppData/Roaming/MetaQuotes/Terminal/Common/Files/
```

## EA Compilation

```bash
cd ~/.wine/drive_c/"Program Files"/"MetaTrader 5 IC Markets Global"
wine MetaEditor64.exe /compile:"MQL5\\Experts\\hermes_bridge.mq5" /log
```

Check: `cat MQL5/Experts/hermes_bridge.log` → "Result: 0 errors, 0 warnings"

## EA Commands

The EA accepts 3 commands via JSON:

### 1. Order
```json
{"action":"order","symbol":"EURUSD","direction":"BUY","volume":0.01,"sl":1.16405,"tp":1.16505}
```
Response:
```json
{"status":"ok","ticket":123456,"symbol":"EURUSD","direction":"BUY","volume":0.01,"price":1.16455,"sl":1.16405,"tp":1.16505}
```

### 2. Close All
```json
{"action":"close_all"}
```
Response:
```json
{"status":"ok","action":"close_all","closed":2,"errors":0,"total_was":2}
```

### 3. Status
```json
{"action":"status"}
```
Response:
```json
{"status":"ok","balance":10000.00,"equity":10050.00,"margin":50.00,"positions":1,"positions_data":[...]}
```

## Python Usage

```python
from hermes_mt5_bridge import send_order, get_status, close_all

# Check account
status = get_status()
print(f"Balance: ${status['balance']}, Positions: {status['positions']}")

# Place order
result = send_order('EURUSD', 'BUY', 0.01, 1.16405, 1.16505)
if result['status'] == 'ok':
    print(f"Order #{result['ticket']} opened at {result['price']}")

# Close all
result = close_all()
print(f"Closed {result['closed']} positions")
```

## Attaching EA to MT5 Chart

The EA must be running on a chart for the OnTimer to fire:
1. In MT5, open Navigator (Ctrl+N)
2. Find "hermes_bridge" under Expert Advisors
3. Drag onto any chart (e.g., EURUSD M15)
4. Click OK (default settings: Magic=20260525, Timer=250ms)

The EA will print "[HermesBridge] Started." in the Experts tab when active.

## Troubleshooting

- **EA not processing commands:** Check MT5 Experts tab for errors. Ensure EA smiley face icon is visible on chart.
- **Timeout reading response:** EA might not be attached to any chart, or MT5 is closed.
- **OrderSend failed:** Check symbol is available in Market Watch (EA calls `SymbolSelect(symbol, true)` automatically).
- **FILE_COMMON flag:** Uses Common folder (shared across all MT5 terminals on the machine), not the instance-specific Files folder.
