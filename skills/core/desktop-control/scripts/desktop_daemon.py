#!/usr/bin/env python3
"""
Hermes Desktop Daemon v2 — WebSocket API para controle remoto do desktop.
Usa websockets library (server) + ydotool + mss + grim.
Wayland/GNOME com XWayland fallback para screenshots.
"""
import asyncio, json, os, subprocess, base64, io, sys, re

WS_HOST = "127.0.0.1"
WS_PORT = 9876
ENV = {
    **os.environ,
    "XDG_RUNTIME_DIR": "/run/user/1000",
    "WAYLAND_DISPLAY": "wayland-0",
    "DISPLAY": ":0",
    "XAUTHORITY": "/run/user/1000/.mutter-Xwaylandauth.RUIGP3",
}

def screenshot():
    """Screenshot via grim (Wayland) com fallback mss (XWayland)."""
    # Tentar grim primeiro
    r = subprocess.run(["grim", "-t", "png", "-"], capture_output=True, timeout=10,
        env={**ENV, "WAYLAND_DISPLAY": "wayland-0", "XDG_RUNTIME_DIR": "/run/user/1000"})
    if r.returncode == 0:
        return r.stdout
    # Fallback: mss via XWayland
    import mss
    from PIL import Image
    os.environ.update({k: v for k, v in ENV.items() if k in ("DISPLAY", "XAUTHORITY")})
    with mss.mss() as sct:
        img = sct.grab(sct.monitors[1])
        pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

def run_ydotool(*args):
    return subprocess.run(["ydotool"] + list(args), capture_output=True, text=True, timeout=5, env=ENV)

def click(x, y, button=0):
    run_ydotool("mousemove", "--absolute", str(x), str(y))
    run_ydotool("click", str(button))

def mousemove_abs(x, y):
    run_ydotool("mousemove", "--absolute", str(x), str(y))

def type_text(text):
    subprocess.run(["ydotool", "type", "--file", "-"], input=text, capture_output=True, text=True, timeout=10, env=ENV)

def press_key(keyname):
    run_ydotool("key", keyname)

def scroll(amount):
    btn = "4" if amount > 0 else "5"
    for _ in range(abs(amount)):
        run_ydotool("click", btn)

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
                result["data"] = {"width": 1920, "height": 1080}
            else:
                result["ok"] = False
                result["error"] = f"Unknown action: {action}"
            await websocket.send(json.dumps(result))
        except Exception as e:
            try:
                await websocket.send(json.dumps({"id": cmd.get("id", 0) if 'cmd' in dir() else 0, "ok": False, "error": str(e)}))
            except:
                break

async def main():
    import websockets as ws
    os.environ.setdefault("DISPLAY", ":0")
    os.environ.setdefault("WAYLAND_DISPLAY", "wayland-0")
    os.environ.setdefault("XDG_RUNTIME_DIR", "/run/user/1000")
    os.environ.setdefault("XAUTHORITY", "/run/user/1000/.mutter-Xwaylandauth.RUIGP3")
    rc = subprocess.run(["pgrep", "ydotoold"], capture_output=True).returncode
    if rc != 0:
        subprocess.Popen(["ydotoold"], env=ENV)
    print(f"[daemon] ws://{WS_HOST}:{WS_PORT}", flush=True)
    async with ws.serve(handler, WS_HOST, WS_PORT):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"[daemon] fatal: {e}", flush=True)
        sys.exit(1)
