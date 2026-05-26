# Wayland/GNOME Screenshot Limitations — 2026-05-18

## Ambiente

- Display: Wayland (wayland-0), GNOME/Mutter
- GPUs: NVIDIA GTX 1650 + AMD Renoir (dual GPU)
- Monitores: HDMI-1 (1920x1080) + eDP-1 (1920x1080)

## Ferramentas testadas

| Ferramenta | Resultado | Motivo |
|-----------|----------|--------|
| mss (Python) | ❌ Tela preta | Não suporta Wayland (usa X11/XCB) |
| grim | ❌ | GNOME não suporta wlr-screencopy-unstable-v1 |
| gnome-screenshot | ❌ | Fallback X11, gdk_pixbuf falha |
| org.gnome.Shell.Screenshot (D-Bus) | ❌ | "Screenshot is not allowed" |
| org.freedesktop.portal.Desktop (D-Bus) | ⚠️ Assíncrono | Requer interação do usuário (dialog permissão) |
| import (ImageMagick) | ❌ | X11-only |
| browser_vision (Hermes) | ✅ | Captura dentro do navegador apenas |

## Soluções funcionais

### 1. Screenshot do navegador
`browser_vision` — captura a página renderizada no Brave. Limitado ao viewport do browser.

### 2. Portal D-Bus (requer usuário)
```python
# Funciona mas é assíncrono e precisa de interação
gdbus call --session --dest org.freedesktop.portal.Desktop \
  --object-path /org/freedesktop/portal/desktop \
  --method org.freedesktop.portal.Screenshot.Screenshot '' '{}'
```
O usuário precisa aprovar o dialog de permissão.

### 3. xdg-desktop-portal-gnome
O portal GNOME implementa o protocolo. Se estiver rodando, capturas podem funcionar.

## Workaround para automação visual

Quando screenshot da tela inteira é necessário e as ferramentas falham:
1. Usar `browser_vision` para capturar conteúdo web
2. Para apps desktop: usar Telegram/WhatsApp via API (não via screenshot)
3. Para extrair dados visuais: redirecionar para web (abrir no browser)
4. Último recurso: pynput + mss (se display gráfico ativo)
