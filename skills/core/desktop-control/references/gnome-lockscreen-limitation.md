# GNOME Lockscreen Limitation (25/05/2026)

## Problema
Quando o GNOME bloqueia a tela (Super+L ou timeout), o compositor Wayland restringe acesso:
- `ydotool` perde acesso ao `/dev/uinput` para a sessão
- `mss` captura tela preta (XWayland root vazio)
- Desktop Daemon WebSocket cai

## Solução implementada
Systemd service com `Restart=always` + `RestartSec=5`:
- Daemon cai no bloqueio → systemd reinicia em 5 segundos
- Após desbloqueio, daemon já está pronto e reconectado ao Wayland

## O que NÃO funciona
- Manter daemon ativo durante bloqueio — requer modificar políticas GNOME (não recomendado)
- `systemd-inhibit` — não previne restrição do compositor Wayland
- `loginctl enable-linger` — já ativo, mas não resolve o problema do compositor

## Impacto real
- Bridge MQL5 (ordens forex) NÃO depende do daemon — continua funcionando normalmente
- Browser headless (:9223) NÃO é afetado — roda em processo separado
- Apenas interações com desktop real (cliques, teclas) ficam indisponíveis durante bloqueio

## Verificação
```bash
systemctl --user status hermes-desktop-daemon
# Active: active (running) → OK
# Se caiu, reinicia em 5s automaticamente
```
