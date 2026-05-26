---
name: automation
description: "Automação consolidada: Playwright, agent-browser, pynput, mss, ydotool, pyautogui. Orquestração de todas as ferramentas de controle de browser, teclado, mouse e tela."
version: 1.1.0
author: Roberto Rodrigues
license: MIT
metadata:
  hermes:
    tags: [automation, playwright, browser, pynput, mss, ydotool, pyautogui, agent-browser]
    related_skills: [life-os, browser-automation, architecture, system-health, dashboard]
---

# Automation — Ferramentas Consolidadas

Todas as ferramentas de automação testadas e integradas.

---

## FERRAMENTAS E STATUS

| Ferramenta | Tipo | Status | Melhor Para |
|-----------|------|--------|-------------|
| playwright 1.59 | Browser CDP | ✅ | Automação web complexa, multi-página |
| agent-browser 0.27 | Browser CDP CLI | ✅ | Quick browser tasks, AI-optimized |
| pynput 1.8.2 | Mouse/Teclado virtual | ✅ | Input simulation Python |
| mss 10.2.0 | Screenshots | ❌ Wayland | Retorna tela preta em Wayland/GNOME. Usar gnome-screenshot ou portal D-Bus |
| ydotool 1.0.4 | CLI input (Wayland) | ⚠️ | Comandos shell de input (requer grupo input + relogin) |
| pyautogui 0.9.54 | GUI automation | ⚠️ | Automação visual (requer display ativo, tkinter para MouseInfo) |
| browser tools (Hermes) | Browser CDP | ✅ | Navegação simples, perfil real Brave |
| browser_vision (Hermes) | Screenshot browser | ✅ | Screenshot da página no navegador (funciona mesmo com Wayland) |
| gnome-screenshot | Screenshot Wayland | ⚠️ | Falha no GNOME/Mutter — usa fallback X11 quebrado |
| wl-paste | Clipboard Wayland | ✅ | Leitura do clipboard funciona. Instalar: `sudo apt install wl-clipboard` |
| Playwright (standalone) | Browser CDP | ✅ | Screenshot via page.screenshot() funciona independente do display |

---

## QUANDO USAR CADA UM

### Playwright → Automação web pesada
```
Cenários: multi-página, formulários complexos, upload de arquivos,
          espera por elementos dinâmicos, screenshots programáticos

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto('https://...')
    # interações complexas
    browser.close()
```

### agent-browser → Tarefas rápidas de browser
```
Cenários: abrir página, extrair dados, interagir via CLI
          Otimizado para AI agents

npx agent-browser snapshot https://web.whatsapp.com
npx agent-browser click "@e5"
npx agent-browser extract "table.data tr"
```

### pynput → Input virtual programático
```
Cenários: preencher formulários em apps desktop,
          navegar menus, digitar texto

from pynput.keyboard import Controller as KB
from pynput.mouse import Controller as Mouse
kb = KB(); m = Mouse()
m.position = (500, 300)  # move mouse
m.click(Button.left, 1)  # click
kb.type('Hello World')   # digita
```

### mss → Screenshots da tela
```
Cenários: capturar tela inteira ou região,
          base para OCR/visão computacional

import mss
with mss.MSS() as sct:
    # Tela inteira (monitor 1)
    img = sct.grab(sct.monitors[1])
    # Região específica
    region = {'left': 0, 'top': 0, 'width': 500, 'height': 500}
    img = sct.grab(region)
```

### ydotool → Input via linha de comando
```
Cenários: scripts shell que precisam simular input

ydotool click 0  # click com botão esquerdo
ydotool type "texto para digitar"
ydotool mousemove -x 500 -y 300
```

### pyautogui → Automação GUI completa
```
Cenários: localizar elementos na tela, clicar em ícones,
          automação de apps desktop com feedback visual

import pyautogui
pyautogui.click(100, 200)
pyautogui.write('texto')
local = pyautogui.locateOnScreen('botao.png')
```

---

## FLUXOS DE AUTOMAÇÃO

### Fluxo 1: Extrair dados de site com anti-bot
```
1. mss → screenshot da página via browser normal
2. pytesseract → OCR do texto visível
3. opencv → detectar elementos da UI
4. pynput → clicar/navegar como humano
5. mss → validar resultado visualmente
```

### Fluxo 2: Login + Extração em site autenticado
```
1. browser_navigate (Hermes) → usa perfil Brave real (cookies)
2. browser_snapshot → verifica se logado
3. browser_console → extrai dados da página
4. Se bloqueado: fallback para fluxo 1
```

### Fluxo 3: Automação de app desktop (Telegram/WhatsApp)
```
1. mss → screenshot do app
2. opencv → detectar botões/campos
3. pynput → clicar e digitar
4. mss → validar ação
```

### Fluxo 4: Pipeline completo com Playwright
```
1. playwright.launch → browser headful
2. page.goto → navegar
3. page.fill / page.click → interagir
4. page.screenshot → capturar evidência
5. page.evaluate → extrair dados via JS
6. browser.close → limpar
```

### Fluxo 5: Virtual Desktop Controller (controle remoto do desktop)
```bash
# Script unificado em ~/.hermes/scripts/virtual_desktop.py
# Usa /usr/bin/python3 (não o venv)

# Mouse
python3 virtual_desktop.py move 960 540
python3 virtual_desktop.py click left --x 500 --y 300
python3 virtual_desktop.py dblclick
python3 virtual_desktop.py drag 100 100 500 500
python3 virtual_desktop.py scroll 3 up

# Teclado
python3 virtual_desktop.py type "texto"
python3 virtual_desktop.py key enter
python3 virtual_desktop.py hotkey ctrl t

# Tela
python3 virtual_desktop.py screenshot ~/print.png
python3 virtual_desktop.py screen_info
python3 virtual_desktop.py position

# Apps
python3 virtual_desktop.py run firefox
python3 virtual_desktop.py open_url "https://..."
```

Backends (auto-detecção com fallback):
- **pynput** (mouse + teclado, XWayland) — primário
- **pyautogui** (mouse + teclado + screenshot, XWayland)
- **ydotool** (kernel uinput, Wayland nativo)
- **wtype** (Wayland text input nativo)

Ambiente testado: Wayland + GNOME, 3840×1080, todos os 4 backends ativos ✅.

---

## WORKFLOW ANTI-BOT COMPLETO

Quando CDP/Playwright são detectados:

```
Nível 1: Tentar Playwright com stealth
  → playwright-stealth plugin

Nível 2: Usar agent-browser com perfil real
  → agent-browser snapshot --profile ~/.config/BraveSoftware

Nível 3: pynput + mss (controle visual)
  → screenshot → OCR → detectar posição → clicar → digitar

Nível 4: Intervenção manual
  → Reportar [FALHA] e solicitar ação humana
```

---

## CHECKS DE SAÚDE

```bash
# Verificar se ferramentas estão operacionais
python3 -c "import playwright; print('playwright OK')" 2>/dev/null
npx agent-browser --version 2>/dev/null
python3 -c "from pynput.mouse import Controller; print('pynput OK')" 2>/dev/null
python3 -c "import mss; print('mss OK')" 2>/dev/null
systemctl --user is-active ydotool 2>/dev/null || echo 'ydotool: relogin pending'
```

---

## References

- **[ocr-setup.md](references/ocr-setup.md)** — Tesseract snap workaround, tessdata download, Wayland screenshot issues

## ANTI-PADRÕES

- NÃO usar pyautogui em produção sem fallback (frágil a mudanças de UI)
- NÃO fazer loop infinito de cliques/scraping
- NÃO usar automação visual se API/CDP funciona
- NÃO deixar browsers abertos após automação
- NÃO usar ydotool sem antes verificar se pynput resolve

---

## WAYLAND SCREENSHOT — PITFALLS

Capturar tela no Wayland é restritivo. Ferramentas e resultados:

| Ferramenta | Resultado | Motivo |
|-----------|----------|--------|
| mss (Python) | Tela preta (0 pixels) | Usa X11/XCB, não funciona em Wayland puro |
| grim | "compositor doesn't support wlr-screencopy" | Só funciona com compositores wlroots (Sway, Hyprland). GNOME/Mutter NÃO suporta |
| gnome-screenshot | Falha silenciosa | Tenta fallback X11 que também falha no Wayland |
| GNOME Shell D-Bus | "Screenshot is not allowed" | Bloqueado por política de segurança — só portal com interação do usuário |
| Portal D-Bus (org.freedesktop.portal.Desktop) | Funciona mas requer diálogo | Exige interação do usuário para aprovar |

### Workaround funcional
- Usar pynput para Ctrl+A, Ctrl+C e ler clipboard (wl-paste) — requer foco na janela alvo
- Instalar wl-clipboard: `sudo apt install -y wl-clipboard`
- O clipboard Wayland funciona via `wl-paste`

### Se nada funcionar
- Pedir que o usuário copie manualmente os valores visíveis na tela
- NÃO insistir em automação visual quando o ambiente bloqueia

## PITFALLS

### ydotool daemon no Wayland
O binário instala mas o daemon (`ydotoold`) requer que o usuário esteja no grupo `input`. 
Após `sudo apt install ydotool`, é necessário:
```bash
sudo usermod -aG input $USER
# Depois fazer relogin ou newgrp input
```
Se o daemon não estiver rodando, o CLI falha com "failed to connect socket".
**Fallback imediato: pynput** — cobre 100% dos casos de input simulation em Python,
sem dependência de daemon externo.

### Pip quota no /tmp
Em sistemas com `/tmp` tmpfs pequeno, instalações pesadas (CUDA, ultralytics) 
podem estourar com "Cota da disco excedida". Usar:
```bash
mkdir -p ~/tmp && TMPDIR=~/tmp pip install ...
```
