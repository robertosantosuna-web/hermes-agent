#!/usr/bin/env python3
"""
Hermes Desktop Daemon v3 — WebSocket API + ydotool keycodes + screenshot fix.
Correções: keycodes numéricos, combos (alt+b, ctrl+a), screenshot via XWayland.
"""
import asyncio, json, os, subprocess, base64, io, sys, time

WS_HOST = "127.0.0.1"
WS_PORT = 9876

XAUTH = os.environ.get("XAUTHORITY", "") or subprocess.check_output(
    "ls /run/user/1000/.mutter-Xwaylandauth.* 2>/dev/null | head -1", shell=True
).decode().strip()

ENV = {
    **os.environ,
    "XDG_RUNTIME_DIR": "/run/user/1000",
    "WAYLAND_DISPLAY": "wayland-0",
    "DISPLAY": ":0",
    "XAUTHORITY": XAUTH,
}

# ═══════════════════════════════════════════
# KEYCODE MAP (Linux input event codes)
# ═══════════════════════════════════════════
KEYCODE = {
    # Function keys
    "f1": 59, "f2": 60, "f3": 61, "f4": 62, "f5": 63,
    "f6": 64, "f7": 65, "f8": 66, "f9": 67, "f10": 68,
    "f11": 87, "f12": 88,
    # Modifiers
    "alt": 56, "altgr": 100, "ctrl": 29, "shift": 42,
    "super": 125, "meta": 125,
    # Navigation
    "enter": 28, "return": 28, "tab": 15, "escape": 1, "esc": 1,
    "space": 57, "backspace": 14,
    "up": 103, "down": 108, "left": 105, "right": 106,
    "home": 102, "end": 107, "pageup": 104, "pagedown": 109,
    "insert": 110, "delete": 111,
    # Letters
    "a": 30, "b": 48, "c": 46, "d": 32, "e": 18, "f": 33,
    "g": 34, "h": 35, "i": 23, "j": 36, "k": 37, "l": 38,
    "m": 50, "n": 49, "o": 24, "p": 25, "q": 16, "r": 19,
    "s": 31, "t": 20, "u": 22, "v": 47, "w": 17, "x": 45,
    "y": 21, "z": 44,
    # Numbers
    "0": 11, "1": 2, "2": 3, "3": 4, "4": 5, "5": 6,
    "6": 7, "7": 8, "8": 9, "9": 10,
    # Symbols
    "minus": 12, "equal": 13, "dot": 52, "comma": 51,
    "slash": 53, "semicolon": 39, "apostrophe": 40,
    "leftbrace": 26, "rightbrace": 27, "backslash": 43,
}

# Aliases
KEYCODE["return"] = 28
KEYCODE["esc"] = 1
KEYCODE["meta"] = 125


def _keycode(keyname):
    """Resolve key name or keycode to int."""
    keyname = keyname.lower().strip()
    if keyname.isdigit():
        return int(keyname)
    kc = KEYCODE.get(keyname)
    if kc is None and len(keyname) == 1:
        kc = ord(keyname.upper()) - 32  # Rough mapping
    return kc


def _parse_combo(key_str):
    """
    Parse key combo string into press/release sequence.
    "F9" → [("67:1", "67:0")]
    "alt+b" → [("56:1",), ("48:1",), ("48:0",), ("56:0",)]
    "ctrl+a" → [("29:1",), ("30:1",), ("30:0",), ("29:0",)]
    "super+d" → [("125:1",), ("32:1",), ("32:0",), ("125:0",)]
    """
    parts = key_str.lower().replace("+", " ").split()
    
    if len(parts) == 1:
        kc = _keycode(parts[0])
        if kc is None:
            return None
        return [(f"{kc}:1", f"{kc}:0")]
    
    # Combo: modifier + key
    seq = []
    mods = []
    for p in parts[:-1]:
        kc = _keycode(p)
        if kc:
            mods.append(kc)
            seq.append(f"{kc}:1")
    
    kc = _keycode(parts[-1])
    if kc:
        seq.append(f"{kc}:1")
        seq.append(f"{kc}:0")
    
    for mod in reversed(mods):
        seq.append(f"{mod}:0")
    
    return seq if len(seq) >= 2 else None


# ═══════════════════════════════════════════
# Core functions
# ═══════════════════════════════════════════

def screenshot():
    """Screenshot via mss (XWayland DISPLAY=:0)."""
    import mss
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        img = sct.grab(monitor)
        return mss.tools.to_png(img.rgb, img.size)


def x11_env():
    """Subprocess env with DISPLAY=:0 for xdotool."""
    return {**ENV, "DISPLAY": ":0"}


def list_windows():
    """List visible XWayland windows with title, position, size. Returns list of dicts."""
    import subprocess
    result = []
    try:
        ids = subprocess.run(
            ["xdotool", "search", "--onlyvisible", "--name", ""],
            capture_output=True, text=True, timeout=5, env=x11_env()
        ).stdout.strip().split()
        for wid in ids:
            try:
                name = subprocess.run(
                    ["xdotool", "getwindowname", wid],
                    capture_output=True, text=True, timeout=2, env=x11_env()
                ).stdout.strip()
                geom = subprocess.run(
                    ["xdotool", "getwindowgeometry", wid],
                    capture_output=True, text=True, timeout=2, env=x11_env()
                ).stdout.strip()
                # Parse "Position: x,y" and "Geometry: wxh"
                pos_str = ""
                size_str = ""
                for line in geom.split('\n'):
                    if 'Position:' in line:
                        pos_str = line.split(':')[1].strip()
                    if 'Geometry:' in line:
                        size_str = line.split(':')[1].strip()
                result.append({"id": int(wid), "name": name, "position": pos_str, "size": size_str})
            except:
                pass
    except:
        pass
    return result


def focus_window(wid):
    """Focus an X11 window by ID."""
    subprocess.run(["xdotool", "windowfocus", str(wid)], capture_output=True, timeout=3, env=x11_env())


def get_active_window():
    """Get active window ID and name."""
    try:
        wid = subprocess.run(
            ["xdotool", "getactivewindow"],
            capture_output=True, text=True, timeout=3, env=x11_env()
        ).stdout.strip()
        name = subprocess.run(
            ["xdotool", "getwindowname", wid],
            capture_output=True, text=True, timeout=2, env=x11_env()
        ).stdout.strip()
        return {"id": int(wid), "name": name}
    except:
        return None


def find_mt5_window():
    """Find MT5 IC Markets main window. Returns window dict or None."""
    windows = list_windows()
    for w in windows:
        if 'icmarkets' in w['name'].lower() and 'conta' in w['name'].lower():
            return w
    for w in windows:
        if 'mt5' in w['name'].lower() or 'metatrader' in w['name'].lower():
            return w
    return None


def run_ydotool(*args):
    subprocess.run(["ydotool"] + list(args), capture_output=True, text=True, timeout=5, env=ENV)


def click(x, y, button=0):
    run_ydotool("mousemove", "--absolute", str(x), str(y))
    run_ydotool("click", str(button))


def mousemove_abs(x, y):
    run_ydotool("mousemove", "--absolute", str(x), str(y))


def type_text(text):
    subprocess.run(["ydotool", "type", "--file", "-"], input=text, capture_output=True, text=True, timeout=10, env=ENV)


def press_key(key_str):
    """Send key/combo using numeric keycodes."""
    seq = _parse_combo(key_str)
    if seq is None:
        return
    flat = []
    for item in seq:
        if isinstance(item, tuple):
            flat.extend(item)
        else:
            flat.append(item)
    run_ydotool("key", *flat)


def scroll(amount):
    btn = "4" if amount > 0 else "5"
    for _ in range(abs(amount)):
        run_ydotool("click", btn)


# ═══════════════════════════════════════════
# WebSocket handler
# ═══════════════════════════════════════════

async def handler(websocket):
    async for message in websocket:
        try:
            cmd = json.loads(message)
            action = cmd.get("action", "")
            params = cmd.get("params", {})
            req_id = cmd.get("id", 0)
            result = {"id": req_id, "ok": True}

            if action == "ping":
                result["data"] = "pong"

            elif action == "screenshot":
                png_bytes = screenshot()
                result["data"] = base64.b64encode(png_bytes).decode("ascii")
                result["size"] = len(png_bytes)

            elif action == "click":
                click(params["x"], params["y"], params.get("button", 0))

            elif action == "mousemove":
                mousemove_abs(params["x"], params["y"])

            elif action == "type":
                type_text(params["text"])

            elif action == "key":
                press_key(params["key"])

            elif action == "scroll":
                scroll(params.get("amount", 1))

            elif action == "screen_size":
                import mss
                with mss.mss() as sct:
                    m = sct.monitors[0]
                    result["data"] = {"width": m["width"], "height": m["height"]}

            elif action == "windows":
                result["data"] = list_windows()

            elif action == "focus":
                focus_window(params["wid"])
                result["data"] = get_active_window()

            elif action == "active":
                result["data"] = get_active_window()

            elif action == "find_mt5":
                w = find_mt5_window()
                if w:
                    focus_window(w["id"])
                    result["data"] = w
                    result["focused"] = True
                else:
                    result["ok"] = False
                    result["error"] = "MT5 not found"

            else:
                result["ok"] = False
                result["error"] = f"Unknown action: {action}"

            await websocket.send(json.dumps(result))

        except Exception as e:
            error_resp = {"id": 0, "ok": False, "error": str(e)}
            try:
                await websocket.send(json.dumps(error_resp))
            except:
                break


async def main():
    import websockets as ws
    
    os.environ.setdefault("DISPLAY", ":0")
    os.environ.setdefault("WAYLAND_DISPLAY", "wayland-0")
    os.environ.setdefault("XDG_RUNTIME_DIR", "/run/user/1000")
    os.environ.setdefault("XAUTHORITY", XAUTH)
    
    print(f"[daemon-v3] keycodes={len(KEYCODE)} port={WS_PORT}", flush=True)
    
    rc = subprocess.run(["pgrep", "ydotoold"], capture_output=True).returncode
    if rc != 0:
        print("[daemon-v3] starting ydotoold...", flush=True)
        subprocess.Popen(["ydotoold"], env=ENV)
    
    async with ws.serve(handler, WS_HOST, WS_PORT):
        print(f"[daemon-v3] ws://{WS_HOST}:{WS_PORT} ready", flush=True)
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[daemon-v3] stopped.")
    except Exception as e:
        print(f"[daemon-v3] fatal: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
