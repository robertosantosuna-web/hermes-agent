# Desktop Daemon — Correções (22/05/2026)

## Bugs Corrigidos

### 1. Screenshot quebrado: grim → mss
**Sintoma**: `grim` retornava "compositor doesn't support wlr-screencopy-unstable-v1"
**Raiz**: GNOME não implementa wlr-screencopy. grim é para wlroots (Sway, Hyprland).
**Correção**: Substituir `grim` por `mss` (Multiple ScreenShot) que captura via XWayland.
```python
# Antes (quebrado)
subprocess.run(["grim", "-t", "png", "-"], ...)

# Depois (funcional)
import mss
with mss.mss() as sct:
    monitor = sct.monitors[0]
    img = sct.grab(monitor)
    png_data = mss.tools.to_png(img.rgb, img.size)
```

### 2. screen_size hardcoded
**Sintoma**: Sempre retornava 1920x1080
**Raiz**: Valor fixo no código
**Correção**: Autodetect via mss.monitors[0] → 3840x1080 real (2 monitores)

### 3. XAUTHORITY hardcoded
**Sintoma**: Screenshot preto após reboot
**Raiz**: Path `/run/user/1000/.mutter-Xwaylandauth.RUIGP3` fixo — muda a cada sessão
**Correção**: Autodetect do ambiente ou via ls glob
```python
"XAUTHORITY": os.environ.get("XAUTHORITY", "") or 
    subprocess.check_output(
        "ls /run/user/1000/.mutter-Xwaylandauth.* 2>/dev/null | head -1",
        shell=True).decode().strip()
```
**Locais corrigidos**: 2 pontos no desktop_daemon.py (ENV dict + setdefault no main)

### 4. Sem systemd service
**Sintoma**: Daemon não iniciava no boot
**Correção**: Criado `~/.config/systemd/user/hermes-desktop-daemon.service`
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

## Limitação Conhecida (não corrigível)

### mss não captura janelas Wayland nativas
GNOME/Ubuntu renderiza apps (Brave, Terminal) via Wayland nativo. mss captura via XWayland — só vê janelas X11 legadas. Screenshots mostram wallpaper/tela preta, nunca o conteúdo que o Roberto vê.

Alternativas testadas e falhas:
- GNOME D-Bus Screenshot API → AccessDenied
- grim → GNOME não suporta wlr-screencopy
- Portal Desktop Screenshot → requer diálogo de permissão (interação humana)
- Extensão GNOME (hermes-screenshot@entidade.local) → quebrada, API incompatível GNOME 50

## Estado Final

| Componente | Antes | Depois |
|-----------|-------|--------|
| Daemon | ❌ Offline | ✅ systemd, auto-start |
| Screenshot | ❌ grim quebrado | ✅ mss funcional (XWayland apenas) |
| Screen size | ❌ 1920x1080 fixo | ✅ 3840x1080 autodetect |
| XAUTHORITY | ❌ Path fixo | ✅ Autodetect |
| Mouse | ✅ ydotool | ✅ ydotool |
| Teclado | ✅ ydotool (wtype quebrado) | ✅ ydotool |
| Visão real | ❌ Nunca funcionou | ❌ Wayland bloqueia (limitação do GNOME) |
