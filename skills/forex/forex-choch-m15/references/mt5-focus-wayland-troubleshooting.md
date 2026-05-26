# MT5 Window Focus on Wayland/GNOME — Troubleshooting (25/05/2026)

## Problem

`mt5_direct.py` v4 runs from a cron job (`no_agent: true`). It needs to focus the MT5 window
before sending order keys (F9 → symbol → etc.). On Wayland/GNOME, standard X11 window
management tools (`xdotool`, `wmctrl`) cannot see or manipulate native Wayland windows.

## Methods Tested

### 1. Alt+Tab cycling (FAILED)
```python
for _ in range(3):
    ydotool key alt+tab
    time.sleep(0.15)
```
**Result:** Keys went to wrong window. Alt+Tab cycling order is unpredictable from cron context.

### 2. GNOME Overview search — Super + type + Enter (FAILED)
```python
ydotool key super ; sleep 0.8
ydotool type "metatrader" ; sleep 0.8
ydotool key enter ; sleep 1.0
```
**Result:** User reported shortcuts "não estão ativos ou estão incorretos." Overview may not open,
search text may not enter correctly, or Wine window may not match search terms.

### 3. GNOME Overview with "icmarkets" (UNTESTED — user confirmed previous didn't work)
```python
ydotool key super ; sleep 0.8
ydotool type "icmarkets" ; sleep 0.8
ydotool key enter ; sleep 1.0
```
**Current state:** Updated in `mt5_direct.py` but user hasn't confirmed if this specific variant works.

## Root Cause Hypotheses

1. **ydotool Super key not reaching GNOME Shell** — depends on keymap and compositor
2. **ydotool type() not working correctly** — Brazilian ABNT2 layout may interfere
3. **Wine window title not indexed** — GNOME Shell search may not include Wine windows
4. **Cron context limitation** — ydotool may behave differently from cron vs terminal

## Verification Steps

```bash
# 1. Verify ydotoold is running
pgrep ydotoold

# 2. Test basic ydotool keystrokes
ydotool type "TEST"  # Should type where focus currently is

# 3. Test Super key specifically
ydotool key super  # Should open GNOME overview

# 4. Check if MT5 window exists
pgrep -a -f terminal64  # Shows: MetaTrader 5 IC Markets Global
```

## Alternative Approaches (Not Yet Tried)

### A. GNOME Window API via gdbus
```bash
gdbus call --session --dest org.gnome.Shell \
  --object-path /org/gnome/Shell \
  --method org.gnome.Shell.Eval \
  "global.get_window_actors().map(...)"
```
Note: Shell.Eval returned `(false, '')` on our setup — may require extension/unsafe mode.

### B. Mouse click on known position
Use `ydotool mousemove x y` and `ydotool click 1` to click the MT5 "New Order" toolbar button directly.
Requires knowing window position — fragile across screen sizes/resolutions.

### C. MT5 Expert Advisor (MQL5)
Write an EA that listens on a local socket/pipe and receives trade commands.
Dropped into MT5 Experts folder. Most robust long-term but requires MQL5 development.

### D. Keep MT5 always focused
Simplest workaround: user leaves MT5 as the active window. Cron keys go directly to it.
Trade-off: user loses desktop during trading hours.

## Current mt5_direct.py v4 Focus Method

```python
def focus_mt5():
    """Super → 'icmarkets' → Enter — busca GNOME overview."""
    ydotool('key', 'super')
    time.sleep(0.8)
    ytype('icmarkets')
    time.sleep(0.8)
    ydotool('key', 'enter')
    time.sleep(1.0)
    return True  # Assume success
```

⚠️ **STATUS (25/05):** Não verificado. Usuário relatou que atalhos não funcionam.
