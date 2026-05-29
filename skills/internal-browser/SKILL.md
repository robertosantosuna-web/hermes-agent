---
name: internal-browser
description: "Navegador interno da ENTIDADE: Chromium headless systemd (:9226) + Playwright/Brave legado. CDP para automação web, consultas IA, scraping. Não conflita com navegadores desktop."
category: core
---

# Internal Browser — Navegador Interno Multi-Agente

Navegador headless dedicado da ENTIDADE para automação web, consultas a IAs, scraping, e orquestração multi-agente.

## Dois Modos

| Modo | Porta | Browser | Uso |
|------|-------|---------|-----|
| **Chromium interno** (recomendado) | 9226 | Chromium 147 headless | Systemd service, sempre online |
| Playwright + Brave | — | Brave | Via NEO, conflita com Brave desktop |

## Chromium Interno (9226) ⭐

Service systemd que mantém Chromium headless sempre disponível.

```bash
# Controle
systemctl --user start internal-browser
systemctl --user stop internal-browser
systemctl --user status internal-browser

# Ou via script
python3 ~/.hermes/brain/internal_browser.py [start|stop|status|restart]
```

**Config:** Porta 9226, perfil `~/.hermes/browser-profile/`, auto-restart on failure.

**CDP endpoint:** `ws://localhost:9226/devtools/browser/<id>`

**Usar via CDP:**
```python
import json, subprocess
# Criar nova aba
r = subprocess.run(['curl', '-s', '-X', 'PUT', 'http://localhost:9226/json/new'],
    capture_output=True, text=True)
tab = json.loads(r.stdout)
ws_url = tab['webSocketDebuggerUrl']
# Conectar e navegar via websocket...
```

**Portas ocupadas:** :9222 Brave, :9224 Edge WA, :9225 Edge, :9226 INTERNO

## Playwright + Brave (legado)

## Arquitetura

```
NEO → Playwright → Brave (perfil persistente)
                    ├── DeepSeek (chat.deepseek.com)
                    ├── Gemini (gemini.google.com)
                    ├── ChatGPT (chatgpt.com)
                    ├── Claude (claude.ai)
                    └── Copilot (copilot.microsoft.com)
```

## Instalação Systemd (28/05/2026)

Chromium headless como serviço persistente na porta 9226:

Service file em `~/.config/systemd/user/internal-browser.service`:
```
ExecStart=/home/roberto/.cache/ms-playwright/chromium-1217/chrome-linux64/chrome \
    --remote-debugging-port=9226 \
    --user-data-dir=/home/roberto/.hermes/browser-profile \
    --headless=new --no-first-run --no-sandbox \
    --disable-gpu --disable-extensions about:blank
```

Ativar: `systemctl --user enable --now internal-browser`

Script de controle: `~/.hermes/brain/internal_browser.py` (start/stop/status/restart)

**Portas CDP do sistema (29/05):**
| Porta | Navegador | Modo |
|-------|-----------|------|
| 9224 | Edge WhatsApp | Wayland |
| 9225 | Edge main | Wayland (primário para CDP) |
| 9226 | Chromium interno | headless (systemd) |

Portas 9222/9223 (Brave) descontinuadas.

## ⚠️ CDP Navigation (29/05)

`PUT /json/new?url=...` **funciona no Edge :9225** (com URL encoded). No Chromium headless :9226, `/json/new` retorna vazio — a URL é ignorada e a aba abre em `about:blank`. Para abas persistentes com URL específica, usar Edge :9225. Para Chromium :9226, usar `PUT /json/new` → `Page.navigate` via WebSocket ou Playwright `connect_over_cdp`.

## Pré-requisitos

- Brave fechado (Playwright precisa de acesso exclusivo ao perfil)
- `pip install playwright`
- Perfil Google logado no Brave (para "Sign in with Google" automático)

## Instagram — Bloqueio Total (28/05)

Instagram bloqueia QUALQUER automação via CDP, mesmo em navegador real logado (Brave :9222).
Qualquer `Runtime.evaluate` ou navegação redireciona para `auth_platform/recaptcha`.
8 abas do Brave ficaram presas em loop de recaptcha durante testes.
Única abordagem: monitoramento passivo (detectar aba aberta, registrar timestamps, zero interação com DOM).

## Uso via NEO

```python
from neo.execution.browser.playwright_browser import NeoBrowser

browser = NeoBrowser(headless=True)
page = browser.new_tab("https://chat.deepseek.com/")

# Verifica login
if page.locator('textarea').count() > 0:
    page.locator('textarea').fill("Pergunta aqui")
    page.keyboard.press("Enter")
    # ... aguarda resposta
    response = page.locator("body").inner_text()

browser.save_session("deepseek")
browser.close()
```

## Ferramentas NEO

| Ferramenta | Função |
|-----------|--------|
| `browser_open(agent)` | Abre agente IA e verifica login |
| `browser_ask(agent, prompt)` | Envia prompt e retorna resposta |
| `browser_debate(topic, agents, rounds)` | Painel de debate multi-agente |
| `browser_list_agents()` | Lista agentes disponíveis |
| `browser_auto_login(agents)` | Login automático via Google |

## Agentes Configurados

| Agente | URL | Seletor Input | Status |
|--------|-----|--------------|--------|
| deepseek | chat.deepseek.com | `textarea` | ✅ Testado |
| gemini | gemini.google.com/app | `div[contenteditable="true"]` | ✅ Testado |
| chatgpt | chatgpt.com | `textarea, #prompt-textarea` | ✅ Logado |
| claude | claude.ai | `div[contenteditable="true"]` | 🔐 Pendente |
| copilot | copilot.microsoft.com | `textarea, #userInput` | 🔐 Pendente |

## Pitfalls

- ⚠️ **Brave precisa estar FECHADO** para Playwright acessar o perfil (modo legado apenas)
- ✅ **Chromium interno (9226) não conflita** com nenhum navegador desktop — use este para tudo
- ⚠️ **Ubuntu 26.04** — Playwright não instala Chromium nativo. Usar `executable_path` do cache do Playwright
- ⚠️ **`/json/new` requer PUT**, não GET
- ⚠️ **Chromium interno usa `headless=new`** — algumas páginas podem exigir `--headless=old` para renderização completa
- ⚠️ **Systemd user service** — precisa de `linger` habilitado para persistir após logout: `loginctl enable-linger`
- ⚠️ **Instagram bloqueia CDP em QUALQUER navegador** — Brave (:9222), Edge (:9225), Chromium (:9226) são todos redirecionados para `auth_platform/recaptcha` quando acessados via CDP. O protocolo DevTools é detectado pelo Instagram, não importa o browser. Única abordagem viável: monitoramento passivo (detectar aba aberta, zero interação com DOM).
