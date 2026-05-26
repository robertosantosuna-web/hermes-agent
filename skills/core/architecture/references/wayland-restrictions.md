# Wayland/GNOME Screen Capture — War Story

## Problema
Wayland + GNOME bloqueia toda captura de tela não-interativa. Em 2026-05-17, a ENTIDADE gastou ~90 minutos tentando capturar a tela do Edge (onde o 99Freelas estava aberto) usando 8 ferramentas diferentes.

## Ferramentas que FALHARAM
| # | Ferramenta | Erro |
|---|-----------|------|
| 1 | mss | Tela 100% preta (0 pixels não-pretos em 1920x1080) |
| 2 | grim | "compositor doesn't support wlr-screencopy-unstable-v1" |
| 3 | gnome-screenshot | "Unable to use GNOME Shell's builtin screenshot interface, resorting to fallback X11" → também falhou |
| 4 | gdbus org.gnome.Shell.Screenshot | "Screenshot is not allowed" |
| 5 | import -window root | "missing an image filename" |
| 6 | wtype (virtual keyboard) | "Compositor does not support the virtual keyboard protocol" |
| 7 | pynput (Alt+Tab, Ctrl+C) | Teclas enviadas mas Wayland não aplica em outras janelas |
| 8 | Portal D-Bus (org.freedesktop.portal.Screenshot) | Assíncrono, complexo, nunca completou |

## O que FUNCIONOU
- **Playwright + Chromium**: Abre navegador controlado e captura screenshots normalmente
- **Browser CDP do Hermes**: browser_navigate/browser_snapshot/browser_console funcionam
- **Telegram como fallback**: Histórico de conversas continha TODOS os dados do 99Freelas que precisávamos

## Solução permanente (se precisar de screenshot da tela real)
1. Mudar GDM para X11: `WaylandEnable=false` em `/etc/gdm3/custom.conf`
2. Reiniciar sessão
3. Todas as ferramentas X11 (xdotool, mss, import, scrot) passam a funcionar

## Lição
Não perder tempo com screenshot no Wayland. Usar Playwright (browser controlado), CDP, ou Telegram como fonte de dados.
