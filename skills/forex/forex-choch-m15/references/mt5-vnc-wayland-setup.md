# MT5 + VNC — Display Duplicado (Xvfb + GNOME/Wayland)

## Problema

MT5 roda no Xvfb :99 (headless) mas o usuário no GNOME/Wayland não vê as janelas. Solução: x11vnc espelha :99 e o usuário conecta via VNC viewer.

## x11vnc no Wayland — ARMADILHA

x11vnc detecta a variável `WAYLAND_DISPLAY` do ambiente GNOME e RECUSA rodar, mesmo com `DISPLAY=:99` apontando para Xvfb:

```
Wayland display server detected.
Wayland sessions are as of now only supported via -rawfb and the bundled deskshot utility. Exiting.
```

**Solução:** limpar as variáveis Wayland do ambiente antes de lançar o x11vnc:

```python
import subprocess, os

env = os.environ.copy()
env['DISPLAY'] = ':99'
env.pop('WAYLAND_DISPLAY', None)
env.pop('XDG_SESSION_TYPE', None)

p = subprocess.Popen(
    ['x11vnc', '-forever', '-shared', '-nopw', '-display', ':99'],
    start_new_session=True, env=env
)
```

## Setup completo

```bash
# 1. Xvfb (display virtual)
Xvfb :99 -screen 0 1280x720x24 &

# 2. MT5 no Xvfb
DISPLAY=:99 wine terminal64.exe /portable /login:LOGIN /password:SENHA /server:SERVER &

# 3. x11vnc (espelha :99 na porta 5900)
#    ⚠️ CRÍTICO: limpar WAYLAND_DISPLAY
WAYLAND_DISPLAY= XDG_SESSION_TYPE= DISPLAY=:99 \
  x11vnc -forever -shared -nopw -display :99 &

# 4. VNC viewer no GNOME
vncviewer localhost:5900 &
```

## MT5 login headless

Os parâmetros CLI (`/login`, `/password`, `/server`) NÃO conectam automaticamente no Wine headless. O terminal64 abre a janela de login mas não submete.

**Workaround via xdotool** (após janela aparecer):

```bash
DISPLAY=:99 xdotool windowfocus <WINDOW_ID>
DISPLAY=:99 xdotool key Tab Tab          # pular para campo senha
DISPLAY=:99 xdotool type "SENHA"
DISPLAY=:99 xdotool key Return           # conectar
```

Verificar sucesso: a janela "MetaTrader 5 - Netting - EURUSD,H1" deve aparecer no `xwininfo -root -tree`.

## Verificação de saúde

```bash
# Xvfb rodando?
pgrep -a Xvfb

# MT5 conectado?
DISPLAY=:99 xwininfo -root -tree | grep "MetaTrader 5 - Netting"

# VNC acessível?
python3 -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1',5900)); print(s.recv(12))"
```
