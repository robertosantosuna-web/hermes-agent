---
name: architecture
description: "Arquitetura das 7 camadas operacionais da ENTIDADE: mapeamento de ferramentas, Camada 7 (Córtex Bi-Neural), status de cada componente, gaps e plano de instalação."
version: 1.1.0
tags: [architecture, layers, system, tools, infrastructure, cortex, brain, neural]
license: MIT
metadata:
  hermes:
    tags: [architecture, layers, system, tools, infrastructure]
    related_skills: [life-os, system-health, browser-automation, model-orchestration, cortex-system, financial-intelligence]
---

# Architecture — 7 Camadas Operacionais

Status real do ambiente (2026-05-17). Wayland + NVIDIA GTX 1650 + AMD Renoir.

---

## CAMADA 1 — CONTROLE DO SISTEMA

### Status: PARCIAL (50%)

| Ferramenta | Status | Alternativa |
|-----------|--------|-------------|
| Terminal Linux | ✅ Hermes terminal tool | bash, processos, background |
| Sistema de arquivos | ✅ read/write/patch/search | Native tools |
| Processos | ✅ process tool | kill, wait, poll, background |
| xdotool | ❌ | ydotool (Wayland) — instalar |
| ydotool | ❌ | `sudo apt install ydotool` |
| wmctrl | ❌ | Wayland: usar wlrctl ou kanshi |
| xprop/xwininfo | ✅ Presente | via XWayland |
| scrot | ❌ | grim+slurp (Wayland) — instalar |
| grim/slurp | ❌ | `sudo apt install grim slurp` |
| ffmpeg | ✅ Instalado | Processamento mídia |
| imagemagick | ❌ | `sudo apt install imagemagick` |
| tesseract OCR | ❌ | `sudo apt install tesseract-ocr tesseract-ocr-por` |
| Python3 | ✅ 3.14.4 | pip3 disponível |
| pyautogui | ❌ | `pip install pyautogui` |
| pynput | ❌ | `pip install pynput` |
| mss | ❌ | `pip install mss` (Wayland: limitado) |
| pillow | ❌ | `pip install pillow` |
| pytesseract | ❌ | `pip install pytesseract` |
| opencv-python | ❌ | `pip install opencv-python-headless` |
| pygetwindow | ❌ | Wayland: usar wlrctl |

### O que funciona AGORA
- Terminal: comandos shell, scripts Python, processos longos
- Arquivos: leitura, escrita, edição, busca
- Processos: gestão completa (start, monitor, kill)

### O que precisa instalar
- Wayland screen capture: grim, slurp
- OCR: tesseract-ocr + pytesseract
- Imagem: imagemagick, pillow
- Automação: ydotool (Wayland-native)
- Visão: opencv-python-headless

---

## CAMADA 2 — NAVEGADOR

### Status: FUNCIONAL (80%)

| Ferramenta | Status | Detalhe |
|-----------|--------|---------|
| Brave Browser | ✅ v148 | Perfil em ~/.config/BraveSoftware/ |
| CDP | ✅ | Hermes browser tools usam CDP internamente |
| Cookies reais | ✅ | Sessão persiste entre browser_navigate |
| Sessões autenticadas | ✅ | Cookies/storage mantidos |
| Playwright | ❌ | `pip install playwright && playwright install` |
| Abas | ✅ | browser_navigate para cada URL |
| Cliques | ✅ | browser_click |
| DOM | ✅ | browser_snapshot, browser_console |
| Formulários | ✅ | browser_type, browser_press |
| Uploads | ❌ | browser tools não expõem file input ainda |
| Dashboards | ✅ | browser_vision para análise visual |

### O que funciona AGORA
- Navegação completa com perfil real do Brave
- Sessões autenticadas persistentes
- Interação DOM (snapshot, click, type)
- Extração de dados via JS console
- Screenshots + análise visual

### O que falta
- Instalar Playwright para cenários complexos
- File upload (limitação das browser tools nativas)

### Comando CDP Manual (se precisar fora do Hermes)
```bash
brave-browser \
  --remote-debugging-port=9222 \
  --user-data-dir=$HOME/.config/BraveSoftware/Brave-Browser &
```

---

## CAMADA 3 — CONTROLE VISUAL REAL

### Status: MÍNIMO (20%)

| Ferramenta | Status | Alternativa |
|-----------|--------|-------------|
| Screenshot tela | ❌ | grim (Wayland) — instalar |
| Screenshot browser | ✅ | browser_vision |
| Análise de imagem | ✅ | vision_analyze (modelo auxiliar) |
| OpenCV | ❌ | `pip install opencv-python-headless` |
| YOLO | ❌ | Pode instalar via pip |
| pyautogui | ❌ | ydotool + grim como alternativa |
| OCR | ❌ | tesseract — instalar |
| Mouse virtual | ❌ | ydotool mousemove |
| Teclado virtual | ❌ | ydotool type |

### Fluxo Anti-Bot (quando implementado)
```
1. grim → screenshot da tela/região
2. tesseract/pytesseract → OCR do texto
3. opencv → detectar botões/campos visualmente
4. ydotool → mover mouse, clicar, digitar
5. grim → validar resultado visualmente
```

### Limitação REAL
Este ambiente é primariamente CLI/Wayland híbrido. 
Controle visual da tela inteira só funciona se houver sessão gráfica ativa.
Para operação headless/CLI: preferir APIs e CDP.

---

## CAMADA 4 — TELEGRAM / DESKTOP APPS

### Status: BOM (70%)

| Ferramenta | Status | Detalhe |
|-----------|--------|---------|
| Telegram Desktop | ✅ Rodando | PID ativo, snap |
| Telethon | ❌ | `pip install telethon` |
| Pyrogram | ❌ | `pip install pyrogram` |
| Hermes send_message | ✅ | Se Telegram configurado |
| API oficial | ✅ | Telethon recomendado |
| OCR do app | ❌ | Não recomendado — use API |

### Recomendação
**Usar Telethon (API oficial)**, NÃO controle visual do app:
- Mais confiável
- Não quebra com updates de UI
- Funciona mesmo sem sessão gráfica
- Suporta: ler mensagens, enviar, grupos, mídia, bots

### Setup Telethon
```bash
pip install telethon
# Depois configurar API_ID e API_HASH do my.telegram.org
```

---

## CAMADA 5 — EMAIL

### Status: FUNCIONAL (90%)

| Ferramenta | Status | Detalhe |
|-----------|--------|---------|
| himalaya | ✅ v1.2.0 | IMAP/SMTP |
| Gmail API | ✅ | google-workspace skill |
| Leitura | ✅ | himalaya list/read |
| Envio | ✅ | himalaya write/send |
| Classificação | ✅ | Executivo analisa |
| Resumo | ✅ | LLM resume |
| Triagem | ✅ | executive-communication skill |
| Anexos | ✅ | himalaya attachments |
| Filtros | ✅ | himalaya search/flags |

### Comandos Rápidos
```bash
himalaya list -f INBOX -u          # não lidos
himalaya search "from:cliente"     # busca
himalaya write -t "assunto" ...    # enviar
```

---

## WAYLAND/GNOME — RESTRIÇÕES E WORKAROUNDS

O ambiente Wayland + GNOME impõe restrições severas de segurança que bloqueiam:
- Screenshots não-interativos (portal D-Bus retorna "Access denied")
- Input sintético (wtype: "Compositor does not support virtual keyboard protocol")
- Conexão WebSocket CDP de origens diferentes (`--remote-allow-origins=*` necessário)

### Ferramentas testadas (o que NÃO funciona)
| Ferramenta | Erro | Motivo |
|-----------|------|--------|
| mss | Tela 100% preta | X11-only, não captura Wayland |
| grim | "compositor doesn't support wlr-screencopy" | GNOME não é wlroots |
| gnome-screenshot | "Unable to capture screenshot" | API interna do GNOME bloqueada |
| wtype | "Compositor does not support virtual keyboard" | GNOME não expõe wlr-virtual-keyboard |
| pynput (keyboard) | Teclas enviadas, mas Alt+Tab não funciona | Wayland isola input entre apps |
| gdbus Screenshot.Screenshot | "Access denied" | GNOME bloqueia screenshots não-interativos |

### Soluções testadas (o que FUNCIONA)
| Abordagem | Status | Setup |
|----------|--------|-------|
| Playwright com Chromium | ✅ Funcional | Já instalado, abre browser controlado |
| Browser CDP do Hermes (Brave) | ✅ Funcional | Perfil real, cookies, DOM |
| Telegram como fonte de dados | ✅ Funcional | Histórico recuperou dados do 99Freelas |
| ydotool com uinput | ⚠️ Parcial | Binário instalado, uinput carregado, mas daemon precisa de grupo input + relogin |
| X11 (alternar GDM) | ⚠️ Requer logout | `WaylandEnable=false` em `/etc/gdm3/custom.conf` |

### Padrão de recuperação: Telegram como fallback
Quando browser/screenshot falham (Cloudflare, Wayland), usar o Telegram:
1. Buscar histórico na conversa "Entidade" via Telethon
2. Dados de plataformas freelancer foram preservados lá
3. Sessão persistente em `~/roberto3.session`

## CAMADA 6 — EXECUTIVO DIGITAL [90%]

### Pilares da ENTIDADE

| Pilar | Skill | Status |
|-------|-------|--------|
| Financeiro | `financial-intelligence`, `freelancing-automation` | ATIVO (prioridade #1) |
| Saúde | `health-pillar` | Conhecimento compilado, tracking desativado |
| Social | `social-pillar` | ATIVO — engenharia comportamental e social, análise de rede |
| Técnico | `architecture`, `triple-neural-network` | ATIVO |

14 subsistemas integrados.

### Subsistemas

| # | Subsistema | Status | Skill/Ferramenta |
|---|-----------|--------|------------------|
| 1 | executor | ✅ | terminal + process tools |
| 2 | browser | ✅ | browser tools + browser-automation |
| 3 | terminal | ✅ | terminal tool (bash, python, processos) |
| 4 | automações | ✅ | cronjob + skills + scripts |
| 5 | strategist | ✅ | operational-intelligence |
| 6 | ROI | ✅ | financial-intelligence |
| 7 | priorização | ✅ | operational-intelligence (matriz) |
| 8 | análise financeira | ✅ | financial-intelligence |
| 9 | decisões | ✅ | operational-intelligence (RACE framework) |
| 10 | memory | ✅ | memory tool (persistente cross-session) |
| 11 | perfil | ✅ | user memory store + ENTIDADE identity |
| 12 | histórico | ✅ | session_search (cross-session recall) |
| 13 | contexto | ✅ | memory + session_search + skills |
| 14 | projetos | ✅ | project-management |

### Infraestrutura

| Componente | Status | Implementação |
|-----------|--------|---------------|
| Scheduler | ✅ | cronjob tool |
| Cronjobs | ✅ | 2 ativos (health + memory) |
| Rotinas | ✅ | Skills + cron |
| Monitoramento | ✅ | system-health |
| Observer | ✅ | watch_patterns, cronjob scripts |
| Logs | ✅ | ~/.hermes/logs/, journalctl |
| Dashboards | ✅ | dashboard skill |
| Emails | ✅ | himalaya + executive-communication |
| Mensagens | ✅ | send_message + whatsapp + telegram |
| Oportunidades | ✅ | freelancing-automation + financial-intelligence |
| **MindCoach Pro** | ✅ | PWA Cloud Run — dashboard neural + chat Hermes |

### Subsistemas

| # | Subsistema | Status | Skill/Ferramenta |
|---|-----------|--------|------------------|
| 1 | executor | ✅ | terminal + process tools |
| 2 | browser | ✅ | browser tools + browser-automation |
| 3 | terminal | ✅ | terminal tool (bash, python, processos) |
| 4 | automações | ✅ | cronjob + skills + scripts |
| 5 | strategist | ✅ | operational-intelligence |
| 6 | ROI | ✅ | financial-intelligence |
| 7 | priorização | ✅ | operational-intelligence (matriz) |
| 8 | análise financeira | ✅ | financial-intelligence |
| 9 | decisões | ✅ | operational-intelligence (RACE framework) |
| 10 | memory | ✅ | memory tool (persistente cross-session) |
| 11 | perfil | ✅ | user memory store + ENTIDADE identity |
| 12 | histórico | ✅ | session_search (cross-session recall) |
| 13 | contexto | ✅ | memory + session_search + skills |
| 14 | projetos | ✅ | project-management |

### Infraestrutura

| Componente | Status | Implementação |
|-----------|--------|---------------|
| Scheduler | ✅ | cronjob tool |
| Cronjobs | ✅ | 2 ativos (health + memory) |
| Rotinas | ✅ | Skills + cron |
| Monitoramento | ✅ | system-health |
| Observer | ✅ | watch_patterns, cronjob scripts |
| Logs | ✅ | ~/.hermes/logs/, journalctl |
| Dashboards | ✅ | dashboard skill |
| Emails | ✅ | himalaya + executive-communication |
| Mensagens | ✅ | send_message + whatsapp + telegram |
| Oportunidades | ✅ | freelancing-automation + financial-intelligence |
| **MindCoach Pro** | ✅ | PWA Cloud Run — dashboard neural + chat Hermes |

---

## PLANO DE INSTALAÇÃO (PRIORIZADO)

### Imediato (ganho real)
```bash
# Python base (necessário para quase tudo)
pip install pillow requests numpy

# Telegram API (comunicação)
pip install telethon

# OCR (leitura de documentos/imagens)
sudo apt install -y tesseract-ocr tesseract-ocr-por tesseract-ocr-eng
pip install pytesseract
```

### Curto prazo
```bash
# Imagem e visão
sudo apt install -y imagemagick grim slurp
pip install opencv-python-headless

# Automação Wayland
sudo apt install -y ydotool

# Browser avançado
pip install playwright
playwright install chromium
```

### Médio prazo
```bash
# Orquestração e observabilidade
pip install fastapi uvicorn redis loguru rich

# Visão computacional pesada (ATENÇÃO: usar TMPDIR)
mkdir -p ~/tmp
TMPDIR=~/tmp pip install --break-system-packages --no-cache-dir ultralytics transformers

# Memória vetorial
TMPDIR=~/tmp pip install --break-system-packages --no-cache-dir chromadb lancedb

# Redis server
sudo snap install redis
```

## ⚠️ PITFALL: /tmp tmpfs quota

Em sistemas com /tmp montado como tmpfs com usrquota (tamanho ~50% da RAM), 
instalações pip grandes falham com EDQUOT. Usar TMPDIR=~/tmp como workaround.
Ver `system-health` references/tmpfs-quota-workaround.md.

---

## MATRIZ DE COBERTURA (FINAL)

## MATRIZ DE COBERTURA (FINAL)

```
CAMADA 1 [██████████] 95% — Terminal + Python tools OK.
CAMADA 2 [████████░░] 80% — Browser tools OK. WhatsApp Web bloqueia Brave (User-Agent).
CAMADA 3 [████████░░] 80% — mss + pynput + tesseract + OpenCV OK. Wayland screenshots restritos.
CAMADA 4 [█████████░] 90% — Telethon + Pyrogram OK.
CAMADA 5 [██████████] 95% — email-autonomy OK.
CAMADA 6 [█████████░] 90% — 14 subsistemas + dashboard + cron jobs + GPU local.
CAMADA 7 [████████░░] 85% — Tálamo + Visual + Audio + Motor Cortex. Bi-neural architecture.

TOTAL:   88% de cobertura
```

### References
- **[telegram-setup.md](references/telegram-setup.md)** — Telegram API setup, phone format, pitfalls

## CAMADA 7 — CÓRTEX BI-NEURAL [85%]

Sistema nervoso artificial. Módulos de visão, áudio, controle motor e roteamento. Ver **cortex-system** skill.

| Módulo | Local | Status |
|--------|-------|--------|
| Tálamo | `~/.hermes/thalamus/` | ✅ |
| Visual Cortex | `~/.hermes/cortex/visual.py` | ✅ |
| Audio Cortex | `~/.hermes/cortex/audio.py` | ✅ |
| Motor Cortex | `~/.hermes/cortex/motor.py` | ✅ |

**Documentação:** `~/.hermes/architecture/brain-mapping.md`, `brain-dev-journal.md`, `ubuntu-hardware-control.md`

**Pitfalls:** Wayland bloqueia screenshots (Xvfb para Wine). NVIDIA Optimus sem fan control. OCR Wine limitado. Cloudflare Turnstile bloqueia 99Freelas.

---

### Instalado com Sucesso (Python)
```
pillow==12.1.1           opencv-python-headless==4.13.0
numpy==2.4.5             pytesseract==0.3.13
telethon==1.43.2         pyrogram==2.0.106
pyautogui==0.9.54        pynput==1.8.2
mss==10.2.0              playwright==1.59.0
pygetwindow==0.0.9       requests==2.32.5
```

### Instalado com Sucesso (Sistema)
```
tesseract==5.4.1 (snap)  ffmpeg==8.0.1
brave-browser==148       himalaya==1.2.0
telegram-desktop (snap)  
```

### Apenas 4 precisam de sudo (não críticos)
```
imagemagick → PIL/OpenCV suprem
grim/slurp  → mss supre screenshots
ydotool     → pynput supre input
```

## ANTI-PADRÕES

- NÃO tentar pyautogui em Wayland (não funciona)
- NÃO usar OCR do app Telegram se API existe
- NÃO instalar tudo de uma vez (priorizar por ganho)
- NÃO fazer scraping visual se API/CDP funciona
