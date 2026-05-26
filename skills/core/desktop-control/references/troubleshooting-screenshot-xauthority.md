# Desktop Daemon Troubleshooting (22/05/2026)

## Problemas Corrigidos

### 1. Screenshot quebrado (grim → mss)

**Sintoma:** Daemon retornava erro no screenshot. `grim` não funciona com GNOME (requer wlr-screencopy que o GNOME não implementa).

**Solução:** Substituir `grim` por `mss` (MSS — Multiple Screen Shots library):

```python
def screenshot():
    import mss
    with mss.mss() as sct:
        monitor = sct.monitors[0]  # todos os monitores combinados
        img = sct.grab(monitor)
        png_data = mss.tools.to_png(img.rgb, img.size)
        return png_data
```

### 2. XAUTHORITY hardcoded

**Sintoma:** Após reboot, o XAUTHORITY muda (ex: `.RUIGP3` → `.PRYRP3`). Script falhava com path fixo.

**Solução (2 pontos no código):**

```python
# No ENV dict (topo do arquivo):
"XAUTHORITY": os.environ.get("XAUTHORITY", "") or subprocess.check_output(
    "ls /run/user/1000/.mutter-Xwaylandauth.* 2>/dev/null | head -1", shell=True
).decode().strip(),

# No main() (linha ~121):
os.environ.setdefault("XAUTHORITY", ENV["XAUTHORITY"])
```

### 3. screen_size fixo

**Sintoma:** Retornava `1920x1080` mas o desktop real é `3840x1080` (dual monitor).

**Solução:** Autodetect via mss:

```python
elif action == "screen_size":
    import mss
    with mss.mss() as sct:
        m = sct.monitors[0]
        result["data"] = {"width": m["width"], "height": m["height"]}
```

### 4. Sem systemd service

**Sintoma:** Daemon não iniciava no boot. Porta 9876 vazia após reboot.

**Solução:** Criar `~/.config/systemd/user/hermes-desktop-daemon.service`:

```ini
[Unit]
Description=Hermes Desktop Daemon - Remote Desktop Control
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/roberto/.hermes/scripts/desktop_daemon.py
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0
Environment=WAYLAND_DISPLAY=wayland-0
Environment=XDG_RUNTIME_DIR=/run/user/1000

[Install]
WantedBy=graphical-session.target
```

Ativar: `systemctl --user enable --now hermes-desktop-daemon.service`

## API Confirmada (ws://localhost:9876)

| Ação | Params | Funciona? |
|------|--------|-----------|
| `ping` | — | ✅ |
| `screenshot` | — | ✅ PNG via mss |
| `screen_size` | — | ✅ autodetect |
| `click` | `{x, y, button?}` | ✅ ydotool |
| `mousemove` | `{x, y}` | ✅ ydotool |
| `type` | `{text}` | ✅ ydotool |
| `key` | `{key}` | ✅ ydotool |
| `scroll` | `{amount}` | ✅ ydotool |

## O que NÃO funciona

| Ferramenta | Motivo |
|-----------|--------|
| `grim` | GNOME não implementa wlr-screencopy |
| `wtype` | GNOME não suporta virtual keyboard protocol |
| `gnome-screenshot` | Fallback X11 falha no Wayland |
| `wmctrl` | Não funciona no Wayland |
| `xdotool` | Funciona no XWayland (DISPLAY=:0 + XAUTHORITY) |

## Debug: Verificar se Daemon está rodando

```bash
# Porta
ss -tlnp | grep 9876

# systemd
systemctl --user status hermes-desktop-daemon

# Teste rápido
python3 -c "
import asyncio, json, websockets
async def t():
    async with websockets.connect('ws://localhost:9876') as ws:
        await ws.send(json.dumps({'action': 'ping', 'id': 1}))
        print(await asyncio.wait_for(ws.recv(), timeout=2))
asyncio.run(t())
"
```
