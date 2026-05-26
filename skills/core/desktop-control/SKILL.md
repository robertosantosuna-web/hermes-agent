---
name: desktop-control
description: "Controle remoto do desktop Wayland/GNOME via WebSocket — mouse, teclado, screenshot. Inclui: Vision Engine (OCR + multi-backend capture), MT5 + VNC Display Setup (Xvfb :99), daemon systemd. Usa ydotool (uinput) + mss (XWayland). Absorveu: vision-engine, mt5-vnc-display-setup (2026-05-24)."
version: 1.2.0
author: Roberto Rodrigues
metadata:
  hermes:
    tags: [desktop, wayland, remote-control, ydotool, mouse, keyboard, screenshot, daemon]
    related_skills: [cdp-browser-automation, freelancing-automation, browser-automation]
---

# Desktop Control

**✅ OPERACIONAL (22/05/2026)** — Daemon via systemd `hermes-desktop-daemon.service`, porta 9876. Mouse, teclado e screenshot funcionais.

## API WebSocket (ws://localhost:9876) — DAEMON v3 (25/05/2026)

**⚠️ Keycodes numéricos + visão XWayland via xdotool.** Ver `references/mt5-order-via-daemon.md`.

### Ações disponíveis

| Action | Params | Descrição |
|--------|--------|-----------|
| `ping` | — | `"pong"` |
| `screen_size` | — | `{width, height}` |
| `screenshot` | — | PNG base64 (⚠️ tela preta no GNOME Wayland) |
| `click` | `{x, y, button?}` | Move + clica |
| `mousemove` | `{x, y}` | Move mouse (absoluto) |
| `type` | `{text}` | Digita texto |
| `key` | `{key}` | Tecla/combo — daemon converte nome→keycode (81 entradas) |
| `scroll` | `{amount}` | Scroll |
| **`windows`** | — | **NOVO v3** — Lista janelas XWayland visíveis `[{id, name, position, size}]` |
| **`focus`** | `{wid}` | **NOVO v3** — Foca janela X11 por ID |
| **`active`** | — | **NOVO v3** — Retorna janela ativa `{id, name}` |
| **`find_mt5`** | — | **NOVO v3** — Encontra e foca MT5 IC Markets |

### Visão XWayland (xdotool no DISPLAY=:0)

Apps Wine (MT5) criam janelas XWayland visíveis via xdotool. Isso substitui screenshots (quebrados) para "ver" o desktop. NÃO usar GNOME overview — não indexa Wine.

```python
# Listar janelas
r = await call("windows")
for w in r['data']:
    if w['name']:
        print(f"[{w['id']}] {w['name'][:60]} @ {w['position']} {w['size']}")

# MT5: [10486700] 52892799 - ICMarketsSC-Demo... @ 87,32 1833x1048
# Chart: [27263015] USDJPY, US Dollar vs Japanese Yen @ 430,32 903x963
```

### Cálculo de coordenadas (dual-monitor)

Coordenadas do `getBoundingClientRect()` são relativas ao VIEWPORT. Para ydotool (absoluto), somar `window.screenX/screenY`:

```python
# Via CDP Runtime.evaluate
js = '''
  (() => {
    const el = document.querySelector('textarea');
    const r = el.getBoundingClientRect();
    return JSON.stringify({
      absX: Math.round(r.left + window.screenX + r.width/2),
      absY: Math.round(r.top + window.screenY + r.height/2)
    });
  })()
'''
# → usar absX, absY no ydotool click
```

**PITFALL ABNT2:** `ydotool type` corrompe caracteres acentuados no teclado brasileiro (ç→?, ã→?, é→?). **Mensagens devem ser PURO ASCII** — sem acentos, sem cedilha, sem caracteres especiais.

### CDP Input.dispatchKeyEvent — Digitação em React SPAs (Telegram Web K, etc.)

Quando DOM manipulation (textContent + InputEvent) falha em React SPAs — o React
ignora eventos sintéticos. Usar `Input.dispatchKeyEvent` do CDP com `type: "char"`:

```python
# Digitar caractere por caractere via CDP (nível de kernel do browser)
for char in "Hermes Brain":
    cdp("Input.dispatchKeyEvent", {
        "type": "char",
        "text": char,
        "unmodifiedText": char
    })
    time.sleep(0.05)

# Pressionar Enter para enviar
cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Enter", "code": "Enter", "keyCode": 13})
cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Enter", "code": "Enter", "keyCode": 13})
```

**Por que funciona:** `Input.dispatchKeyEvent` injeta eventos no pipeline de input do
Chromium, antes da reconciliação do React. O React vê como input genuíno de teclado.
`type: "char"` é essencial — `keyDown`/`keyUp` sem `char` não inserem texto.

**O que NÃO funciona:**
- `editable.textContent = '/newbot'` + `InputEvent('input')` → React ignora
- `KeyboardEvent('keydown', {key:'Enter'})` no contentEditable → React ignora
- `document.execCommand('insertText', ...)` → inconsistente entre versões

**Casos validados:** Telegram Web K (React), @BotFather bot creation, chat messages.

### Verificação após ação (navegação cega)

Como screenshots via mss são inúteis no GNOME/Wayland (tela preta), usar CDP para "ver":

```python
# Verificar se texto apareceu na página
cdp('Runtime.evaluate', {
    'expression': 'document.body.innerText.indexOf("texto esperado") > -1',
    'returnByValue': True
})
```

| Ação | Params | Retorno |
|------|--------|---------|
| `ping` | — | `"pong"` |
| `screenshot` | — | `{data: base64 PNG, size: N}` |
| `screen_size` | — | `{width, height}` — 3840x1080 |
| `click` | `{x, y, button?}` | `ok` |
| `mousemove` | `{x, y}` | `ok` |
| `type` | `{text}` | `ok` |
| `key` | `{key}` | `ok` |
| `scroll` | `{amount}` | `ok` |

## Systemd

Serviço: `hermes-desktop-daemon.service` (user)
- `systemctl --user status hermes-desktop-daemon`
- `systemctl --user restart hermes-desktop-daemon`

**Configuração atualizada (25/05):**
```ini
# ~/.config/systemd/user/hermes-desktop-daemon.service
[Unit]
Description=Hermes Desktop Daemon (WebSocket :9876)
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart=/home/roberto/.hermes/hermes-agent/venv/bin/python3 /home/roberto/.hermes/scripts/desktop_daemon.py
Restart=always
RestartSec=5
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=WAYLAND_DISPLAY=wayland-0
Environment=DISPLAY=:0
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical-session.target
```

**Comportamento no bloqueio de tela:** GNOME Wayland restringe acesso ao compositor quando a tela bloqueia → daemon perde conexão → systemd reinicia em 5s (`Restart=always` + `RestartSec=5`). Após desbloqueio, já está pronto. Isso é o melhor possível sem modificar políticas do GNOME.

## VISION ENGINE — OCR & Multi-Backend Capture

*Anexado de `vision-engine` skill. Captura de imagens e OCR em múltiplos backends.*

### Backends Disponíveis

| Backend | Comando | Uso |
|---------|---------|-----|
| Xvfb | `DISPLAY=:99 import -window root` | MT5, Wine, apps X11 |
| Edge CDP | `Page.captureScreenshot` via WebSocket | Páginas web autenticadas |
| Wayland | `grim` | Sway/wlroots (GNOME não suporta) |
| Browser | `browser_vision` | Conteúdo web (Brave) |

### Comandos OCR

```bash
vision_engine.py xvfb                  # Captura + OCR Xvfb (MT5)
vision_engine.py xvfb --numbers-only   # Só números (preços)
vision_engine.py ocr_only --image /path/img.png --lang por  # OCR imagem
vision_engine.py mt5_account           # Conta MT5 (região inferior)
```

### Edge CDP — extração de dados visuais de páginas autenticadas

Quando `browser_vision` (Brave) não está logado mas o Edge CDP (:9222) tem sessão ativa:

```python
# 1. Abrir aba no domínio autenticado
urllib.request.urlopen(urllib.request.Request(
    'http://localhost:9222/json/new?https://site.com', method='PUT'))

# 2. Capturar screenshot da página
ws = websocket.create_connection(f'ws://localhost:9222/devtools/page/{page_id}')
ws.send(json.dumps({"id":1, "method":"Page.captureScreenshot", "params":{"format":"png"}}))
# Decodificar base64 → salvar PNG → OCR

# 3. Extrair texto direto do DOM
ws.send(json.dumps({"id":2, "method":"Runtime.evaluate",
    "params":{"expression": "document.body.innerText", "returnByValue": True}}))
```

**Páginas com sessão ativa no Edge CDP (:9222):** Gmail, 99Freelas, OANDA, TradingView, Toloka.

### Pitfalls de Visão/OCR

- **DeepSeek não suporta visão nativa**: `vision_analyze` retorna `unknown variant image_url`. Usar OCR como fallback.
- **GNOME Wayland**: grim retorna `wlr-screencopy` error. Usar Xvfb ou Edge CDP.
- **PEP 668**: script usa `#!/usr/bin/python3` (system python).
- **Xvfb sem WM**: `windowactivate` falha → usar `windowfocus` + teclas diretas.
- **OCR do MT5 não lê números**: saída típica "2- - +". Para dados financeiros, usar xdotool Ctrl+C ou F9+Tab.
- **OCR de tabelas MT5**: qualidade baixa para dados estruturados. Preferir xdotool Ctrl+C sobre OCR.
- OCR serve apenas para confirmação visual (ex: "a janela de ordem abriu?"). Ver `references/mt5-vision-ocr-notes.md`.

---

## MT5 + VNC DISPLAY SETUP

**⚠️ ATUAL (25/05/2026):** MT5 IC Markets Global roda no desktop Wayland/GNOME (não no Xvfb).

### Ordem preferida de abordagem:

1. **MQL5 EA Bridge (RECOMENDADO):** `hermes_bridge.ex5` no chart → Python escreve JSON → EA executa `OrderSend()` nativo. Zero dependência de foco/teclado/Wayland. Ver `references/mql5-ea-bridge.md`.

2. **Desktop Daemon WebSocket:** ydotool keycodes + xdotool visão. Usar quando EA não está ativo. Fluxo: `find_mt5` → foco chart → click → F9 → preencher → Alt+B. Ver `references/mt5-order-via-daemon.md`.

O setup Xvfb abaixo é LEGADO — mantido para referência de diagnóstico OCR e VNC.

*Anexado de `mt5-vnc-display-setup` skill. Setup do MetaTrader 5 + MetaEditor no Xvfb :99 com VNC para duplicação de vídeo.*

### Comandos de Inicialização

```bash
# Xvfb (já deve estar rodando)
Xvfb :99 -screen 0 1280x720x24 &

# MT5
export WINEPREFIX=~/.wine_mt5 DISPLAY=:99
wine "C:/Program Files/MetaTrader 5/terminal64.exe" /portable /login:1715539800 /password:wc0ZO6#p /server:OANDA_Global-Demo-1 &

# MetaEditor
wine "C:/Program Files/MetaTrader 5/MetaEditor64.exe" &

# VNC (CRÍTICO: unset Wayland)
python3 -c "
import subprocess, os
env = os.environ.copy()
env['DISPLAY'] = ':99'
env.pop('WAYLAND_DISPLAY', None)
env.pop('XDG_SESSION_TYPE', None)
subprocess.Popen(['x11vnc', '-forever', '-shared', '-nopw', '-display', ':99'],
                 start_new_session=True, env=env)
"

# Usuário conecta:
vncviewer localhost:5900
```

### Verificação

```bash
ps aux | grep -E "Xvfb|terminal64|MetaEditor|x11vnc" | grep -v grep
ss -tlnp | grep 5900
DISPLAY=:99 xwininfo -root -tree | grep -E "MetaTrader|MetaEditor" | grep -v 1x1
```

### Verificar conexão MT5 (online vs offline)

**Método 1 — OCR do status bar (mais confiável):**
```bash
xwd -display :99 -root | convert - -crop 500x60+1100+660 /tmp/mt5_status.png
convert /tmp/mt5_status.png -resize 300% /tmp/mt5_status_big.png
tesseract /tmp/mt5_status_big.png /tmp/mt5_ocr
cat /tmp/mt5_ocr.txt
```
- `0/0Kb` → OFFLINE (não conectado ao servidor)
- `XX/YYKb` com números > 0 → CONECTADO

**Método 2 — Título da janela:**
```bash
DISPLAY=:99 xdotool getwindowname $(DISPLAY=:99 xdotool search --name MetaTrader | head -1)
```
- Conectado: `MetaTrader 5 - OANDA Global Demo-1 - EURUSD,H1`
- Offline: `MetaTrader 5 - Netting - EURUSD,H1` (só mostra tipo de conta)

### Pitfalls MT5 + VNC

- `x11vnc` DETECTA Wayland e morre se WAYLAND_DISPLAY estiver setada → unset antes
- CLI params do MT5 (`/login /password /server`) NÃO auto-conectam no Wine headless → precisa xdotool
- xdotool `windowactivate` NÃO funciona sem window manager no Xvfb → usar `windowfocus`
- `pgrep terminal64` não acha processo Wine → usar `ps aux | grep`
- MT5 log é UTF-16LE com null bytes → `data.decode('utf-16-le').replace('\x00', '')`

---

## References

- **[daemon-fixes-2026-05-22.md](references/daemon-fixes-2026-05-22.md)** — Correções: grim→mss, screen_size autodetect, XAUTHORITY autodetect, systemd
- **[troubleshooting-screenshot-xauthority.md](references/troubleshooting-screenshot-xauthority.md)** — Troubleshooting de screenshot e XAUTHORITY
- **[gnome50-screenshot-investigation.md](references/gnome50-screenshot-investigation.md)** — Investigação completa de screenshot no GNOME 50.1
- **[mt5-order-via-daemon.md](references/mt5-order-via-daemon.md)** — Fluxo validado de ordens MT5 IC Markets via Desktop Daemon (25/05/2026)
- **[mql5-ea-bridge.md](references/mql5-ea-bridge.md)** — **NOVO (25/05)** — Bridge MQL5 nativo — Python → JSON → EA OrderSend (sem ydotool/sem foco/sem teclas). Preferir este sobre daemon para ordens.
- **[mt5-vision-ocr-notes.md](references/mt5-vision-ocr-notes.md)** — Notas de OCR e visão no MT5 — absorvido de `vision-engine`
- **[cdp-vision-proxy-telegram-web.md](references/cdp-vision-proxy-telegram-web.md)** — Técnica CDP Runtime.evaluate para "ver" apps Wayland via versão web (validado Telegram Web K, 25/05/2026)
- **[gnome-lockscreen-limitation.md](references/gnome-lockscreen-limitation.md)** — Bloqueio de tela GNOME: diagnóstico, solução systemd Restart=always, impacto (25/05/2026)
- **[gnome-remote-desktop-rdp.md](references/gnome-remote-desktop-rdp.md)** — **NOVO (25/05)** — Acesso remoto via RDP nativo do GNOME: grdctl, xfreerdp3, /sec:rdp, port 3389

### Screenshot: grim → mss
**Problema:** `grim` não funciona no GNOME (requer wlr-screencopy, não disponível no GNOME Shell).
**Solução:** Usar `mss` (MSS) que captura via XWayland — compatível com GNOME.
```python
import mss
with mss.mss() as sct:
    monitor = sct.monitors[0]  # todos os monitores combinados
    img = sct.grab(monitor)
    png_data = mss.tools.to_png(img.rgb, img.size)
```

### screen_size: autodetect
**Problema:** Hardcoded 1920x1080. Monitor real: 3840x1080 (2 telas).
**Solução:** Autodetect via mss.monitors[0].
```python
with mss.mss() as sct:
    m = sct.monitors[0]
    result = {"width": m["width"], "height": m["height"]}
```

### XAUTHORITY: autodetect
**Problema:** Path hardcoded como `.mutter-Xwaylandauth.RUIGP3` — muda a cada sessão.
**Solução:** Autodetect do ambiente ou via ls.
```python
"XAUTHORITY": os.environ.get("XAUTHORITY", "") or 
    subprocess.check_output(
        "ls /run/user/1000/.mutter-Xwaylandauth.* 2>/dev/null | head -1", 
        shell=True).decode().strip()
```

### wtype: NÃO funciona no GNOME
**Problema:** "Compositor does not support the virtual keyboard protocol"
**Solução:** Usar `ydotool type` em vez de wtype. Ambos estão instalados, mas só ydotool funciona no GNOME/Wayland.

### systemd: serviço para auto-start
Ver seção **Systemd** acima para configuração completa com `Restart=always`.

## ARQUITETURA

```
Agente → WebSocket (ws://127.0.0.1:9876) → Desktop Daemon
                                                  ├─ ydotool (mouse/key via uinput)
                                                  ├─ grim (Wayland screenshot)
                                                  └─ wtype (teclado Wayland, fallback)
```

**Por que ydotool e não wtype/pyautogui:**
- `ydotool` usa `/dev/uinput` (kernel evdev) — funciona em qualquer compositor Wayland
- `wtype` requer `zwp-virtual-keyboard-v1` — GNOME não suporta
- `pyautogui` depende de X11 — não funciona em Wayland puro

## PRÉ-REQUISITOS

```bash
# ydotool (mouse + teclado)
sudo apt install -y ydotool
sudo usermod -a -G input $USER
# Reiniciar sessão para grupo input ter efeito

# grim (screenshot Wayland nativo)
sudo apt install -y grim

# Python deps (system python, não venv)
/usr/bin/python3 -m pip install --break-system-packages websockets mss pillow
```

**Verificar se está pronto:**
```bash
# ydotool daemon deve estar rodando
pgrep ydotoold

# Grupo input ativo
groups | grep -o input

# /dev/uinput acessível
ls -la /dev/uinput
```

## INICIAR O DAEMON

**Systemd (auto-start no boot):**
```bash
systemctl --user status hermes-desktop-daemon
systemctl --user restart hermes-desktop-daemon
journalctl --user -u hermes-desktop-daemon -f
```

**Manual (debug):**
```bash
/usr/bin/python3 -u /home/roberto/.hermes/scripts/desktop_daemon.py
```

**IMPORTANTE:** O daemon precisa do `/usr/bin/python3` (system Python com `mss` e `websockets`), NÃO do venv do Hermes. O systemd service já está configurado com as variáveis de ambiente corretas.

## API WEBSOCKET

Todos os comandos são JSON: `{"id": N, "action": "...", "params": {...}}`

| Action | Params | Descrição |
|--------|--------|-----------|
| `ping` | — | Health check → `"pong"` |
| `screen_size` | — | Retorna `{width, height}` |
| `screenshot` | — | Retorna PNG base64 + size |
| `click` | `{x, y, button?}` | Move + clica (0=esq, 1=dir, 2=meio) |
| `mousemove` | `{x, y}` | Move mouse (coordenadas absolutas) |
| `type` | `{text}` | Digita texto via ydotool |
| `key` | `{key}` | Pressiona tecla por nome (ex: `"enter"`, `"F9"`, `"alt+b"`, `"ctrl+a"`) |
| `scroll` | `{amount}` | Scroll vertical (+ = cima, - = baixo) |

**⚠️ CRÍTICO — Formato dos params:** Os parâmetros vão DENTRO de um sub-objeto `params`, NÃO no nível raiz:
```python
# ✅ CORRETO
{"action": "type", "params": {"text": "EURUSD"}}
{"action": "key", "params": {"key": "F9"}}
{"action": "click", "params": {"x": 500, "y": 300}}

# ❌ ERRADO — vai falhar com erro citando o nome do param
{"action": "type", "text": "EURUSD"}
{"action": "key", "key": "F9"}
```
O daemon faz `params = cmd.get("params", {})` e extrai `params["text"]`, `params["key"]`, etc. Parâmetros no nível raiz são ignorados.

### Exemplo de uso (Python)

```python
import json, asyncio, base64
import websockets

async def control():
    async with websockets.connect('ws://127.0.0.1:9876') as ws:
        # Screenshot
        await ws.send(json.dumps({'id':1, 'action':'screenshot'}))
        resp = json.loads(await ws.recv())
        png = base64.b64decode(resp['data'])
        
        # Clicar no centro da tela
        await ws.send(json.dumps({'id':2, 'action':'click', 
            'params':{'x':960, 'y':540}}))
        
        # Digitar URL
        await ws.send(json.dumps({'id':3, 'action':'key', 
            'params':{'key':'56:1'}}))  # Alt press
        await ws.send(json.dumps({'id':4, 'action':'key', 
            'params':{'key':'15:1'}}))  # Tab press

asyncio.run(control())
```

## SCREENSHOT — GNOME 50.1 WAYLAND

**⚠️ NENHUM método programático funciona para apps nativos Wayland.** Ver `references/gnome50-screenshot-investigation.md` para a investigação completa.

| Método | Resultado |
|--------|-----------|
| mss (XWayland) | ❌ Tela 100% preta (RGB 0,0,0) — root XWayland vazio |
| grim | ❌ GNOME não suporta wlr-screencopy |
| GNOME D-Bus | ❌ AccessDenied |
| GNOME Extensão | ❌ ERROR state (bug Shell 50.1) |
| Portal D-Bus | ⚠️ Requer clique humano no diálogo |

**Solução definitiva:** Forçar apps a rodar no XWayland com `--ozone-platform=x11`. Após isso, mss funciona.
```bash
brave-browser-stable --ozone-platform=x11
```
Custo: reiniciar o app 1x e refazer login.

**Pattern prático (25/05):** Para qualquer app desktop que tenha versão web: usar Brave + CDP para VER e ydotool para DIGITAR/CLICAR no app real. Ex: Telegram Desktop → abrir web.telegram.org no Brave (porta 9222) → CDP Runtime.evaluate lê DOM, Page.captureScreenshot captura tela. NÃO tentar screenshot do app nativo Wayland — é tela preta garantida. Ver `references/cdp-web-app-visibility.md`.

**Enquanto isso:** Navegação via Daemon é cega. Confirmar cada passo visualmente com o Roberto. Mas ver **CDP Vision Proxy** abaixo para apps com versão web.

### CDP Vision Proxy — "Ver" Apps Wayland via Web + CDP

**Regra de ouro (25/05/2026):** Antes de qualquer interação cega, verificar se o app tem versão web. Se sim, abrir no Brave (porta 9222) e usar CDP `Runtime.evaluate` para ler o DOM. Isso SUBSTITUI screenshots para navegação.

**Técnica validada (Telegram Web K):**
```python
import json, urllib.request, websocket

# 1. Achar a aba do app
tabs = json.loads(urllib.request.urlopen('http://localhost:9222/json/list').read())
tab = [t for t in tabs if 'web.telegram.org' in t.get('url','')][0]
ws_url = tab['webSocketDebuggerUrl']

# 2. Extrair TODO texto visível da tela (sem screenshot)
def cdp(method, params=None):
    ws = websocket.create_connection(ws_url, timeout=10)
    ws.send(json.dumps({"id": 1, "method": method, "params": params or {}}))
    resp = json.loads(ws.recv())
    ws.close()
    return resp

text = cdp("Runtime.evaluate", {
    "expression": "document.body.innerText",
    "returnByValue": True
})['result']['result']['value']
# → retorna toda a chat list, mensagens, cabeçalhos como texto puro
```

**Apps e seus proxies web (porta 9222):**

| App Desktop | Versão Web | CDP Funciona? |
|------------|-----------|---------------|
| Telegram | `web.telegram.org/k/` | ✅ DOM extraction perfeito |
| WhatsApp | `web.whatsapp.com` | ✅ (se logado) |
| Google Calendar | `calendar.google.com` | ✅ |
| Gmail | `mail.google.com` | ✅ |
| TradingView | `br.tradingview.com` | ✅ (já usado) |

**Quando NÃO usar CDP Vision Proxy:**
- App não tem versão web (MT5, apps Wine)
- Versão web bloqueada por Cloudflare (raramente)
- App requer interação por clique/teclado real (usar Daemon + ydotool)

**Pipeline correto para apps Wayland (25/05):**
```
1. App tem versão web? → SIM → Abrir no Brave :9222 → CDP Runtime.evaluate para VER
                                    → CDP Page.captureScreenshot para IMAGEM (se modelo tiver visão)
                                    → Daemon + ydotool para CLICAR/DIGITAR (se precisar input kernel-level)
2. App NÃO tem versão web? → Daemon + ydotool (cego) → confirmar com Roberto
```

## KEYBOARD: ydotool keycodes numéricos

| Ferramenta | Protocolo | Funciona no GNOME? |
|-----------|-----------|-------------------|
| `ydotool key` | uinput (kernel) | ✅ Sim (via daemon v3) |
| `ydotool type` | uinput (kernel) | ✅ Sim |
| `wtype` | zwp-virtual-keyboard-v1 | ❌ Não |

**⚠️ ydotool só aceita KEYCODES NUMÉRICOS, não nomes.** O daemon v3 converte automaticamente:

```bash
# ❌ NÃO FUNCIONA (ydotool direto):
ydotool key F9          # Falha — "F9" não é keycode
ydotool key "alt+b"     # Falha — string não reconhecida

# ✅ FUNCIONA (keycodes):
ydotool key 67:1 67:0             # F9
ydotool key 56:1 48:1 48:0 56:0   # Alt+B
ydotool key 56:1 15:1 15:0 56:0   # Alt+Tab
```

**Keycodes essenciais:** F9=67, Enter=28, Tab=15, Escape=1, Alt=56, Ctrl=29, B=48, S=31, A=30, Super=125

O daemon v3 aceita nomes no campo `key` e traduz internamente:
```python
await call("key", {"key": "f9"})       # → keycode 67
await call("key", {"key": "alt+b"})    # → 56:1 48:1 48:0 56:0
await call("key", {"key": "ctrl+a"})   # → 29:1 30:1 30:0 29:0
```

## PITFALLS

1. **ydotoold precisa estar rodando.** Sem ele, comandos ydotool falham silenciosamente. O daemon inicia o ydotoold automaticamente.

2. **Grupo `input` necessário.** Sem grupo, ydotool não acessa `/dev/uinput`. Requer logout/login após `usermod -aG`.

3. **wtype NÃO funciona no GNOME.** GNOME não implementa `zwp-virtual-keyboard-v1`. Usar SEMPRE ydotool para teclado.

4. **grim NÃO funciona no GNOME.** GNOME não suporta `wlr-screencopy`. O daemon já usa mss (XWayland) como fallback.

5. **XAUTHORITY muda a cada sessão.** O arquivo tem nome aleatório (`/run/user/1000/.mutter-Xwaylandauth.*`). O daemon (v2) faz auto-detect.

6. **screen_size hardcoded (v1).** Versão antiga tinha `1920x1080` fixo. v2 usa `mss.monitors[0]` para autodetect (3840x1080 real).

7. **⚠️ CRÍTICO: mss NÃO captura janelas Wayland nativas.** O GNOME/Ubuntu renderiza aplicativos como Brave e Terminal via Wayland nativo. mss captura via XWayland — só vê janelas X11 legadas. Screenshots do Daemon mostram wallpaper ou tela preta, nunca o conteúdo real que o Roberto vê. GNOME D-Bus (`org.gnome.Shell.Screenshot`) retorna AccessDenied. Extensão GNOME criada mas quebrada (API incompatível com GNOME 50). **Resultado: navegação cega é a norma.** Confirmar cada passo com o Roberto.

8. **Navegação cega é frágil.** Sem feedback visual, contar Tabs e assumir posições de elementos é arriscado. Preferir que o Roberto execute ações críticas (login, upload) manualmente e usar o Daemon apenas para digitação e navegação simples.

9. **Clipboard (wl-paste) não funciona de background.** Workaround: digitar Ctrl+C via ydotool na janela focada, depois tentar `xclip -o` com `DISPLAY=:0` e `XAUTHORITY`.

10. **Edge CDP vs desktop-control — escolha:** Desktop Daemon para anti-bot (99Freelas, Fiverr). Edge CDP apenas para plataformas sem anti-bot (Neevo, TimeBucks, Toloka). Ver `anti-bot-strategies` para matriz completa.

11. **⚠️ DUAL MONITOR: CDP viewport ≠ ydotool coordinates.** O setup tem 2 monitores (3840x1080 = 2×1920). Coordenadas do `getBoundingClientRect()` do CDP são relativas ao VIEWPORT do navegador, não à tela absoluta. Para clicar via ydotool, somar o offset do monitor onde o navegador está. Ex: se Brave está no monitor direito → `x_real = x_cdp + 1920`. Se o clique falha, testar AMBOS os monitores antes de desistir.

12. **Screenshots via mss são idênticos.** mss captura via XWayland (tela preta com GNOME). Não confiar em screenshots para confirmar ações. Usar `Runtime.evaluate` do CDP para "ver" o conteúdo da página (ex: `document.body.innerText`).

14. **⚠️ `window.location.href` quebra WebSocket CDP**: Navegar via `Runtime.evaluate("window.location.href = '...'")` recarrega a página e DESTRÓI a conexão WebSocket atual. A próxima chamada CDP falha com `JSONDecodeError`. Solução: abrir NOVA aba via `http://localhost:9222/json/new?<url>` e conectar ao WebSocket dela. Ex para Telegram: `json/new?https://web.telegram.org/k/%23@BotFather`.

15. **Telegram Web K DOM input NÃO envia**: `textContent` + `InputEvent` deixa mensagem como "Draft:". Usar `Input.dispatchKeyEvent` com `type: "char"` para cada caractere + `keyDown`/`keyUp` Enter.

17. **⚠️ DETECTAR LOOP DE FERRAMENTA QUEBRADA:** Se uma ação falhar 2x com a mesma ferramenta, NÃO tentar uma 3ª vez. PARAR, mapear a causa raiz, e trocar de abordagem. Ex: xdotool falhou no Wayland? → ydotool. ydotool direto falhou (env vars)? → Desktop Daemon. GNOME overview não acha janela Wine? → Daemon direto na janela já focada. Desperdiçar tokens repetindo abordagem quebrada é o erro mais caro.

18. **⚠️ ydotool não aceita nomes de tecla (25/05):** `ydotool key "F9"` falha — só aceita keycodes numéricos (`67:1 67:0`). O daemon v3 faz a tradução automática. NUNCA chamar ydotool direto com nomes. Ver `KEYBOARD` acima.

21. **⚠️ Google bloqueia browser headless para OAuth (25/05):** Tentar autenticar Google (gcloud, Gmail, etc.) via CDP browser headless falha com "Esse navegador ou app pode não ser seguro". Google detecta e bloqueia Chrome headless no fluxo de login. Para auth Google, usar: (a) Desktop Daemon + Brave real no display :0, ou (b) service account key JSON (via `gcloud auth activate-service-account`). NUNCA tentar OAuth Google via CDP browser headless — é perda de tempo garantida.

19. **⚠️ MT5 F9 só funciona em janela de CHART (25/05):** No terminal principal do MT5 ("ICMarketsSC-Demo: Conta Demo..."), F9 NÃO abre ordem. Precisa focar uma janela de chart primeiro (ex: "USDJPY, US Dollar vs Japanese Yen"). Usar `windows` para listar, `focus` para focar chart, `click` para garantir foco (ydotool click, não xdotool windowfocus), depois F9. Sempre verificar se chart existe antes de tentar ordem — se não houver chart aberto, usar EA bridge. Ver `references/mt5-order-via-daemon.md`.

20. **⚠️ PREFERIR EA BRIDGE sobre automação de teclado (25/05):** Interagir com MT5 via teclado/mouse (F9, Alt+B) é frágil — depende de janela certa focada, keycodes corretos, timing. O EA bridge (`hermes_bridge.ex5`) usa `OrderSend()` nativo do MQL5 — 100% confiável, sem dependência de UI. Só usar automação de teclado se EA não estiver ativo no chart.

## ARQUIVOS

- Daemon: `~/.hermes/scripts/desktop_daemon.py`
- Logs: stdout do daemon
- Porta: `127.0.0.1:9876` (WebSocket)

## QUANDO USAR ESTE SKILL

- Edge/CDP não está rodando (sem `--remote-debugging-port=9222`)
- Cloudflare Turnstile bloqueia browser tools
- Preciso interagir com aplicação desktop qualquer (não só browser)
- Preciso de controle de mouse/teclado a nível de sistema
- Como fallback quando CDP falha no botão "Enviar" do 99Freelas
