# GNOME Remote Desktop (RDP) — 25/05/2026

**GNOME Remote Desktop** é nativo do GNOME 45+, porta 3389. Permite acesso remoto ao desktop.

## Configuração

```bash
# 1. Verificar status
systemctl --user status gnome-remote-desktop
ss -tlnp | grep 3389

# 2. Configurar credenciais
grdctl rdp set-credentials roberto 1797

# 3. Habilitar autenticação por senha
grdctl rdp set-auth-methods credentials

# 4. Habilitar backend RDP
grdctl rdp enable

# 5. (Opcional) Desabilitar view-only para controle remoto
grdctl rdp disable-view-only
```

## Conexão (cliente)

```bash
# Instalar cliente
sudo apt install -y freerdp3-x11

# Conectar
xfreerdp3 /v:127.0.0.1 /u:roberto /p:1797 /cert:ignore /sec:rdp /size:1280x900
```

**Flags essenciais:**
- `/sec:rdp` — OBRIGATÓRIO. Sem isso, `freerdp_post_connect failed` (erro 0x0002000D).
- `/cert:ignore` — ignora certificado auto-assinado
- `/size:1280x900` — tamanho da janela

## Pitfalls

- **`/sec:nla` (padrão) NÃO funciona** — GNOME Remote Desktop rejeita NLA. Usar `/sec:rdp`.
- **`grdctl status` pode travar** — o processo fica esperando stdin. Usar `timeout` ou background.
- **Senha precisa ser configurada ANTES** de habilitar. Ordem: `set-credentials` → `enable`.
- **View-only por padrão** — `disable-view-only` se precisar de controle remoto.
- O RDP roda como serviço user systemd (`gnome-remote-desktop.service`), sobrevive a bloqueio de tela.

## Vs Desktop Daemon

| Aspecto | RDP | Desktop Daemon (:9876) |
|---------|-----|----------------------|
| Acesso | Remoto (rede) | Local (localhost) |
| Visão | Tela completa | Cego (screenshots quebrados) |
| Interação | Mouse/teclado real | ydotool via API |
| Bloqueio tela | ✅ Sobrevive | ⚠️ Reinicia |
| Uso | Sessões interativas | Automação programática |
