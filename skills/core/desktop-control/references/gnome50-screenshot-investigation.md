# GNOME 50.1 — Screenshot Investigation (22/05/2026)

## Conclusão

**Nenhum método de screenshot programático funciona no GNOME 50.1 Wayland.** Apps nativos Wayland (Brave, Terminal) são invisíveis para ferramentas X11.

## Métodos Testados

### 1. mss (XWayland) — ❌ TELA PRETA
```python
import mss, os
os.environ['DISPLAY'] = ':0'
os.environ['XAUTHORITY'] = '/run/user/1000/.mutter-Xwaylandauth.PRYRP3'
with mss.MSS() as sct:
    img = sct.grab(sct.monitors[1])
```
Resultado: `RGB(0,0,0)` em todos os pixels. XWayland root é vazio — GNOME renderiza apps no Wayland nativo.

### 2. grim (wlr-screencopy) — ❌ GNOME não suporta
```bash
grim /tmp/scr.png
# compositor doesn't support wlr-screencopy-unstable-v1
```

### 3. GNOME D-Bus — ❌ AccessDenied
```bash
gdbus call --session --dest org.gnome.Shell.Screenshot \
  --object-path /org/gnome/Shell/Screenshot \
  --method org.gnome.Shell.Screenshot.Screenshot false false '/tmp/scr.png'
# Erro: GDBus.Error:org.freedesktop.DBus.Error.AccessDenied
```

### 4. GNOME Shell Extension — ❌ ERROR state
Extensão em `~/.local/share/gnome-shell/extensions/hermes-screenshot@entidade.local/`
- Testada com `extends Extension` (formato GNOME 45+)
- Testada como extensão de sistema (`/usr/share/gnome-shell/extensions/`)
- Testada com shell-version ["45"..."50.1"]
- Testada com código mínimo (apenas console.log)
- **Estado sempre ERROR** — bug no carregador do Shell 50.1 ou API Shell.Screenshot removida

### 5. Portal D-Bus — ⚠️ Requer confirmação humana
```bash
gdbus call --session --dest org.freedesktop.portal.Desktop \
  --object-path /org/freedesktop/portal/desktop \
  --method org.freedesktop.portal.Screenshot.Screenshot '' '{}'
```
Abre diálogo "Compartilhar tela" — precisa de clique humano.

## Solução Definitiva

Forçar apps a rodar no XWayland com `--ozone-platform=x11`:
```bash
brave-browser-stable --ozone-platform=x11
```
Custo: reiniciar o app 1x. Depois, mss captura normalmente.
