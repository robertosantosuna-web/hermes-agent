---
name: browser-automation
description: "Automação de browser consolidada: Playwright/Chromium via ferramentas nativas, login persistente, scraping operacional, fallback anti-bot, DOM inspection e interação visual."
version: 1.2.1
author: Roberto Rodrigues
license: MIT
metadata:
  hermes:
    tags: [browser, automation, scraping, playwright, chromium, dom]
    related_skills: [life-os, dogfood, freelancing-automation]
---

# Browser Automation

**⚠️ CONSOLIDAÇÃO 22/05: Esta é a skill primária para browser. `cdp-browser-automation` é especialização para CDP (Edge porta 9222). `anti-bot-strategies` substitui ambas quando há Cloudflare/PerimeterX. Consulte a matriz em `anti-bot-strategies` antes de qualquer ação web.**

Automação de navegador usando ferramentas nativas do Hermes Agent. Cobre extração de dados, interação com formulários, login persistente e scraping operacional.

## FERRAMENTAS DISPONÍVEIS

```
browser_navigate    → Abrir URL, retorna snapshot inicial
browser_snapshot    → Capturar árvore de acessibilidade (full=true para completo)
browser_click       → Clicar em elemento (@ref)
browser_type        → Digitar em campo (@ref)
browser_press       → Tecla (Enter, Tab, Escape, ArrowDown)
browser_scroll      → Rolar página (up/down)
browser_back        → Voltar na história
browser_console     → Executar JS no console, ler erros
browser_vision      → Screenshot + análise visual
browser_get_images  → Listar imagens da página
```

## WORKFLOW PADRÃO DE SCRAPING

### Fase 1: Navegação
```
1. browser_navigate(url="https://alvo.com")
   → Retorna snapshot compacto com elementos interativos (@e1, @e2...)
2. Se página tem lazy load: browser_scroll(direction="down") até carregar
```

### Fase 2: Extração
```
Opção A: browser_snapshot(full=true)
  → Extrai texto estruturado da página inteira
  → Melhor para páginas simples/estáticas

Opção B: browser_console(expression="document.querySelector(...).innerText")
  → Extrai dados específicos via JS
  → Melhor para dados estruturados (tabelas, listas)

Opção C: browser_console(expression="JSON.stringify(Array.from(document.querySelectorAll('.item')).map(el => ({title: el.querySelector('.title')?.innerText, price: el.querySelector('.price')?.innerText})))")
  → Serialização JSON direta do DOM
  → Melhor para listas de itens
```

### Fase 3: Interação (se necessário)
```
1. browser_click(ref="@e5")       → clicar botão
2. browser_type(ref="@e3", text="...") → preencher campo
3. browser_press(key="Enter")     → submeter
4. browser_snapshot()              → verificar resultado
```

## LOGIN PERSISTENTE

### Estratégia
Browsers do Hermes mantêm sessão entre chamadas (cookies/storage persistem).
Para plataformas que exigem login:

1. Navegar para página de login
2. Preencher credenciais com browser_type
3. Submeter com browser_press("Enter")
4. Verificar login com browser_snapshot (procurar elemento pós-login)
5. Sessão fica persistente para próximas chamadas

### Verificação de Sessão
```javascript
// browser_console
document.cookie.includes('session') || document.querySelector('[data-logged-in]')
```

## FALLBACK ANTI-BOT

Sites podem detectar automação. Estratégias:

### Nível 1: Normal
Usar ferramentas nativas — maioria dos sites funciona.

### Nível 2: Cloudflare/JS Challenge
- browser_vision para ver se há CAPTCHA
- Se sim: reportar [LIMITAÇÃO] e esperar intervenção manual

### Nível 3: Bloqueio Total
- Tentar user-agent alternativo (não configurável nas tools nativas)
- Reportar [FALHA] e sugerir abordagem alternativa (API, curl, etc.)

## EXTRAÇÃO DE DADOS COMUNS

### Tabelas
```javascript
// browser_console
Array.from(document.querySelectorAll('table tr')).map(row => 
  Array.from(row.querySelectorAll('td,th')).map(cell => cell.innerText.trim())
)
```

### Listas de Cards
```javascript
Array.from(document.querySelectorAll('.card, .listing, .item, article')).map(el => ({
  title: el.querySelector('h1,h2,h3,h4,a')?.innerText?.trim(),
  link: el.querySelector('a')?.href,
  price: el.querySelector('[class*="price"]')?.innerText?.trim(),
  description: el.querySelector('p, .desc')?.innerText?.trim()
}))
```

### Formulários
```javascript
Array.from(document.querySelectorAll('form input, form select, form textarea')).map(el => ({
  name: el.name,
  type: el.type,
  required: el.required,
  placeholder: el.placeholder
}))
```

## PADRÕES DE INTERAÇÃO

### Paginação
```
1. browser_navigate → snapshot da página 1
2. Extrair dados
3. browser_click no botão "Próximo" (@ref)
4. browser_snapshot → página 2
5. Repetir até acabar páginas
```

### Busca
```
1. browser_type no campo de busca (@ref)
2. browser_press("Enter")
3. browser_snapshot → resultados
4. Extrair
```

### Download de Arquivo
```
1. Identificar link de download (@ref)
2. browser_click → iniciar download
3. Arquivo salvo no filesystem do backend
4. Verificar com search_files ou terminal ls
```

## SITES ALVO FREQUENTES

### Fiverr
- URL: https://www.fiverr.com/
- Alvo: briefs, mensagens, analytics
- Autenticação: login persistente necessário

### 99Freelas
- URL: https://www.99freelas.com.br/
- Alvo: projetos novos, propostas
- Autenticação: login persistente necessário

### Workana
- URL: https://www.workana.com/
- Alvo: projetos

### WhatsApp Web
- URL: https://web.whatsapp.com
- **PITFALL**: WhatsApp bloqueia Brave e outros navegadores não-Chrome. Verifica User-Agent e mostra tela de "atualize o Chrome".
- **Solução**: usar WhatsApp Desktop (snap) via pynput para controle visual, ou alterar User-Agent antes de navegar:
```javascript
// Antes de navegar, execute no about:blank:
Object.defineProperty(navigator, 'userAgent', {
  get: () => 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'
});
```
- **Alternativa**: WhatsApp Desktop instalado via snap (`whatsapp-desktop-linux`), controlável via pynput + mss (se Wayland permitir captura)

### GitHub
- API preferível (gh CLI)
- Browser só para ações sem API

### Google (Search, Gmail, etc.)
- API preferível (google-workspace skill)
- Browser como fallback

## BRAVE CDP HEADLESS — NAVEGADOR INTERNO DO CÉREBRO (v1.1, 23/05/2026)

Brave headless na porta 9223 como serviço systemd. Disponível 24/7 para scripts do cérebro e Hermes Agent.

### Serviço
```bash
systemctl --user status hermes-brain-browser
# Porta: 9223 | Profile: ~/.hermes/browser/profile/
# Brave 148.x headless=new, sem sandbox, sem GPU
```

### Controller (`scripts/brain_browser.py`)
```bash
# Navegar e extrair conteúdo
python3 scripts/brain_browser.py --navigate 'https://site.com' --content --json

# Screenshot
python3 scripts/brain_browser.py --screenshot /tmp/page.png

# Executar JS
python3 scripts/brain_browser.py --eval 'document.title'

# Status
python3 scripts/brain_browser.py --status
```

### Config Hermes
```yaml
browser:
  cdp_url: 'http://localhost:9223'
```

### Sites que funcionam vs Cloudflare
- ✅ ForexFactory, DailyFX, Forexlive — sem anti-bot
- ❌ BabyPips, Investopedia — Cloudflare bloqueia → usar Desktop Daemon + ydotool no Brave real

### Pitfalls

- **REGRA ABSOLUTA — 1 aba por vez:** NUNCA abrir múltiplas abas no brain browser (:9223). Usar `reuse=True`. Se precisar de outro par, navegar na mesma aba. Abas extras = desperdício de RAM + risco de crash.
- **TAB LEAK — múltiplos scripts concorrentes:** Quando 2+ scripts chamam `brain_browser.py` simultaneamente (ex: cron jobs a cada 2min + a cada 15min), cada chamada pode criar uma nova aba porque a aba existente está ocupada. Resultado: 80+ abas acumuladas em horas. **Solução:** file lock (`fcntl.LOCK_EX | LOCK_NB`) no início da main + `cleanup_tabs()` que fecha abas extras no startup, mantendo só 1 página. Ver `references/brain-browser-lock-pattern.md`.
- **Cron jobs que batem no brain browser:** "Brain Weekend Study Scanner" (cada 2min) e "TV Chart Scanner" (cada 30min) são os piores ofensores. Para uso estável, manter só 1-2 scanners em horários espaçados.
- **SingletonLock:** após teste manual, o lock fica. Limpar com `rm -f ~/.hermes/browser/profile/SingletonLock`
- **Headless não herda cookies da sessão gráfica** — para sites com Cloudflare, usar Edge CDP com perfil real ou Desktop Daemon
- **WebSocket CDP é obrigatório para JS eval** — `Page.navigate` + `Runtime.evaluate` via WS, não HTTP

## EDGE (MICROSOFT EDGE) VIA CDP

### Iniciar Edge com CDP no Wayland

```bash
# Encontrar as vars da sessão GNOME
cat /proc/$(pgrep -u $USER gnome-shell | head -1)/environ | tr '\0' '\n' | grep -E "DISPLAY|WAYLAND|XDG_RUNTIME"

# Comando completo (AJUSTAR XAUTHORITY para o arquivo real)
XAUTHORITY=/run/user/1000/.mutter-Xwaylandauth.RUIGP3 \
DISPLAY=:0 WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 \
/usr/bin/microsoft-edge \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir="$HOME/.config/microsoft-edge" \
  --no-first-run \
  "https://www.99freelas.com.br/dashboard" &
```

**PITFALL:** Sem `XAUTHORITY`, o Edge falha com "Missing X server or $DISPLAY" / "The platform failed to initialize." Encontrar o arquivo com: `ls /run/user/1000/.mutter-Xwaylandauth.*`

**⚠️ Cloudflare Turnstile:** O Edge CDP NÃO herda cookies da sessão gráfica ativa. Se o site alvo usa Cloudflare, o Edge CDP será barrado no Turnstile (página de desafio). Use `desktop-control` para interagir com o browser já logado na sessão do usuário.

Para automação completa via CDP em SPAs Angular/React (incluindo preenchimento de inputs, onboarding, etc.), ver **skill `cdp-browser-automation`** — cobre `Input.dispatchMouseEvent`, `Input.dispatchKeyEvent`, e padrões para `fl-input`/`fl-textarea` Angular.

**Flags críticas:**
- `--remote-debugging-port=9222` → porta do CDP
- `--remote-allow-origins=*` → **OBRIGATÓRIO**. Sem esta flag, conexões WebSocket são rejeitadas com "403 Forbidden"
- `--user-data-dir` → usa o perfil existente do Edge (com cookies/sessões)
- `--no-first-run` → evita wizard de primeira execução

### Playwright `connect_over_cdp` (alternativa mais leve)

Para interações simples (ler texto, clicar em elementos), o Playwright oferece uma API mais ergonômica que o websocket-client raw:

```python
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        ctx = browser.contexts[0]
        
        for page in ctx.pages:
            if "fiverr.com/inbox" in page.url:
                await page.bring_to_front()
                body = await page.inner_text("body")
                print(body[:2000])
                break
        
        await browser.close()

asyncio.run(main())
```

**Vantagens sobre websocket-client:**
- `page.inner_text()`, `page.click()`, `page.screenshot()` prontos
- `page.locator('text=Python')` para encontrar elementos por texto
- `page.query_selector_all('[data-testid="contact"]')` para seletores CSS

**PITFALL — Timeout em SPAs pesadas:** `connect_over_cdp` trava (timeout silencioso >30s) em páginas React com DOM muito grande (>5000 nós). Ex: Freelancer skills page. Nesses casos:
- Use `curl http://127.0.0.1:9222/json` para listar abas (sempre funciona)
- Use websocket-client raw com `Runtime.evaluate` minimal (expressões curtas, sem tree-walking pesado)
- Se até o raw CDP falhar, a página é pesada demais — peça ação manual ao usuário

### Python Client via websocket-client

```python
import json, urllib.request, websocket

# Listar abas abertas
resp = urllib.request.urlopen('http://localhost:9222/json')
pages = json.loads(resp.read())
for p in pages:
    print(f'{p["title"][:60]} | {p["url"][:80]}')

# Conectar a uma aba específica
target = pages[0]  # ou filtrar por URL
ws = websocket.create_connection(target['webSocketDebuggerUrl'], origin='http://localhost:9222')

msg_id = 1
def cdp(method, params=None):
    global msg_id
    msg_id += 1
    ws.send(json.dumps({'id': msg_id, 'method': method, 'params': params or {}}))
    return json.loads(ws.recv())
```

### Extrair Dados da Página

```python
# Extrair texto visível
result = cdp('Runtime.evaluate', {
    'expression': 'document.body.innerText',
    'returnByValue': True
})
text = result['result']['result']['value']

# Extrair HTML
result = cdp('Runtime.evaluate', {
    'expression': 'document.documentElement.outerHTML',
    'returnByValue': True
})
```

### Clicar em Elementos (confiável para SPAs)

`element.click()` falha em React/Angular. Usar coordenadas:

```python
# 1. Obter coordenadas do elemento
result = cdp('Runtime.evaluate', {
    'expression': '''
    (function() {
        var el = document.querySelector('seletor');
        el.scrollIntoView({block: 'center'});
        var rect = el.getBoundingClientRect();
        return JSON.stringify({x: rect.left + rect.width/2, y: rect.top + rect.height/2});
    })()
    ''',
    'returnByValue': True
})
pos = json.loads(result['result']['result']['value'])

# 2. Clicar via Input.dispatchMouseEvent
cdp('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': pos['x'], 'y': pos['y'], 'button': 'left', 'clickCount': 1})
cdp('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': pos['x'], 'y': pos['y'], 'button': 'left', 'clickCount': 1})

# 3. Aguardar e verificar navegação
import time; time.sleep(2)
result = cdp('Runtime.evaluate', {
    'expression': 'window.location.href',
    'returnByValue': True
})
```

### Screenshot via CDP

```python
result = cdp('Page.captureScreenshot', {'format': 'jpeg', 'quality': 50})
import base64
img_data = base64.b64decode(result['result']['data'])
with open('/tmp/screenshot.jpg', 'wb') as f:
    f.write(img_data)
```

### Abrir Nova Aba via CDP

```python
import requests
r = requests.put(f'http://localhost:9222/json/new?{url}', timeout=10)
new_page = r.json()
ws = websocket.create_connection(new_page['webSocketDebuggerUrl'])
# A nova aba tem Page/Runtime limpos — enable ambos antes de usar
```

### PITFALLS CDP

- **`PUT /json/new?url` para abrir abas.** GET retorna "unsafe HTTP verb — only PUT supported". Cada aba aberta via PUT tem WebSocket próprio e Runtime domain limpo.
- **Runtime.evaluate falha após Page.navigate:** O contexto de execução é destruído na navegação. Re-enable `Runtime.enable` após cada `Page.navigate` e aguardar 3-8s para SPAs React renderizarem. Verificar `document.body.innerText.length > 500` antes de interagir.
- **`Input.dispatchMouseEvent` é obrigatório para SPAs.** `element.click()` não dispara eventos React corretamente.
- **React textarea injection:** Usar `HTMLTextAreaElement.prototype.value` setter nativo + `dispatchEvent('input')` para preencher campos em React/Angular. `textarea.value = "texto"` sozinho NÃO dispara o state update do React. Padrão correto:
  ```javascript
  var setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
  setter.call(ta, "texto");
  ta.dispatchEvent(new Event('input', { bubbles: true }));
  ```
- **Sempre usar `--remote-allow-origins=*`** ou WebSocket será rejeitado.
- **Edge já rodando sem CDP:** se a porta :9222 já estiver ativa, USE-A diretamente. `curl http://localhost:9222/json` lista as abas. Só reabra o Edge com flags se a porta NÃO estiver ativa.
- **CDP screenshots funcionam no Wayland** (diferente de pyautogui/gnome-screenshot).
- **NÃO feche a aba durante a sessão CDP** — o WebSocket desconecta.
- **`Runtime.evaluate` com `await`/Promise** precisa do parâmetro `awaitPromise: true` no comando CDP, senão retorna `None`.
- **Timeout em WebSocket CDP:** operações longas (>30s) podem travar. Use timeout no connect e mantenha comandos atômicos.
- **PerimeterX (ERRCODE PXCR10002539):** Fiverr e outros sites com proteção PerimeterX bloqueiam CDP em páginas sensíveis (inbox, checkout). O dashboard principal pode carregar normalmente. Indetectável via CDP — requer navegação manual no browser real.
- **TradingView canvas ignora CDP clicks:** O canvas do TradingView (chart + bar replay) usa custom pointer handling que NÃO responde a `Input.dispatchMouseEvent`. Clicks via CDP no canvas são ignorados. Para interagir com o replay/gráfico, usar Desktop Daemon + ydotool (se desktop desbloqueado) ou ação manual do usuário.

## PLAYWRIGHT COM PERFIL PERSISTENTE DO BRAVE

Para herdar cookies/sessões do Brave no Playwright (evita login manual):

```python
from playwright.sync_api import sync_playwright

browser = p.chromium.launch_persistent_context(
    user_data_dir=os.path.expanduser('~/.config/BraveSoftware/Brave-Browser/Default'),
    headless=False,
    args=['--no-sandbox', '--disable-blink-features=AutomationControlled'],
    viewport={'width': 1280, 'height': 900},
)
```

**Importante:** Fechar o Brave antes de usar o perfil, senão dá conflito de lock.

## GOOGLE OAUTH — PITFALL

- Brave/Chromium headless são detectados como "app não seguro" pelo Google OAuth → "Esse navegador ou app pode não ser seguro"
- Playwright com `--disable-blink-features=AutomationControlled` + user_agent normal passa pelo bloqueio
- **`gio open` do terminal:** `DISPLAY=:0 gio open "URL"` abre a página no navegador REAL do desktop (Brave/Edge), usando a sessão já logada. Contorna o bloqueio "navegador não seguro" do Google OAuth sem precisar de CDP. O navegador abre na sessão gráfica do usuário com todos os cookies.
- Google 2FA bloqueia automação completa — requer interação humana no celular
- Sessão persiste após primeira verificação bem-sucedida

## GOOGLE CLOUD CONSOLE — ANGULAR MATERIAL SPA

A console do Google Cloud é uma SPA Angular Material com componentes customizados (CFC).
CDP funciona para **leitura** do DOM e navegação de dropdowns. **Ações de submit**: comportamento varia por página — algumas aceitam JS `.click()` (Cloud Run Security, Service Accounts, API enablement), outras exigem `event.isTrusted` (OAuth Consent Screen, OAuth Client Creation) e precisam de Desktop Daemon ou clique manual.

**Pipeline:** CDP para ler + preencher campos + selecionar dropdowns → CDP ou Desktop Daemon para clicar em Criar/Salvar (dependendo da página).

Ver `references/google-cloud-console-spa.md` para padrões detalhados de:
- Preenchimento de inputs Angular Material (setter nativo + eventos)
- Seleção de dropdowns cfc-select
- Limitações de botões de submit
- Gerenciamento de Client Secrets (Google não mostra mais)

### Google Identity Verification (OAuth Consent Screen — passo final)

**LIMITAÇÃO DURA:** O passo final de criação do OAuth consent screen exige **verificação de identidade com senha Google**. Esta tela NÃO pode ser burlada via CDP, ydotool, ou qualquer automação. É proposital — o Google exige interação humana real para confirmar a criação de credenciais OAuth.

- CDP `element.click()` no botão "Criar" → ignorado
- `Input.dispatchMouseEvent` nas coordenadas → ignorado  
- ydotool (kernel-level) → ignorado se desktop bloqueado; se desktop aberto, funciona mas o prompt de senha ainda aparece
- **Solução:** usuário precisa clicar "Criar" e digitar a senha manualmente. Não há workaround.

## CLOUDFLARE/REACT SPAs — PITFALL

- Cloudflare Turnstile e React SPAs (ex: OANDA hub, 99Freelas login) bloqueiam interação via browser tools do Hermes
- **Solução:** usar Edge via CDP com o perfil real do usuário — cookies e sessões já existentes contornam o Cloudflare
- **Fallback:** abrir a página no Brave real do desktop via `xdg-open` e usar pynput para preencher formulários
- NUNCA tentar burlar CAPTCHA visual — perda de tempo. Use o perfil real com sessão existente.

### PADRÃO: Verificar API Interna Antes de Forçar Login

Quando o login OAuth falha (ou antes mesmo de tentar), investigue se o site tem uma **API interna** acessível sem autenticação. Muitos sites expõem endpoints de dados que o frontend consome — e esses endpoints frequentemente não exigem token:

1. Abra o DevTools do site em um browser normal (F12 → Network → XHR/Fetch)
2. Recarregue a página e observe as chamadas para endpoints internos
3. Replique a chamada com `curl` ou `requests` — adicione `Origin` e `Referer`
4. Se a API retornar dados sem auth, use-a diretamente em vez de browser automation

**Case study — TradingView (18/05/2026):**
- Login Google OAuth → bloqueado ("não seguro") no browser automatizado
- Investigação revelou `scanner.tradingview.com/forex/scan` — API REST aberta
- Retorna OHLCV + RSI, MACD, SMA, Bollinger, ATR, Recommend.All em tempo real
- Headers necessários: `Origin: https://br.tradingview.com` + `Referer` + `User-Agent` realista
- Resultado: pipeline forex inteiro migrado de Yahoo Finance para TradingView API, sem login
- Ver `financial-intelligence` skill, referência `tradingview-api.md`

### Angular/React Text Input — Input.dispatchKeyEvent

`element.value = "texto"` e `Input.insertText` NÃO funcionam em componentes Angular (`fl-input`, `fl-textarea`).
O setter nativo (`Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set`) às vezes funciona em `<input>`, mas NÃO em `<textarea>` de SPAs.

**Funciona:** `Input.dispatchKeyEvent` — simula digitação caractere por caractere:

```python
def type_text(cdp, text):
    """Digita texto via CDP — funciona em Angular fl-input/fl-textarea"""
    for char in text:
        cdp('Input.dispatchKeyEvent', {
            'type': 'keyDown',
            'text': char,
            'unmodifiedText': char,
            'key': char
        })
        cdp('Input.dispatchKeyEvent', {
            'type': 'keyUp',
            'text': char,
            'unmodifiedText': char,
            'key': char
        })
    time.sleep(0.3)
```

**Fluxo completo para preencher campo Angular:**
1. `scrollIntoView` + coordenadas do elemento
2. `Input.dispatchMouseEvent` (triple-click) para selecionar todo o texto existente
3. `Input.dispatchKeyEvent` para cada caractere do novo texto
4. Verificar contador de caracteres (ex: `document.body.innerText.match(/\\d+ characters left/)`)

**Validado em:** Freelancer.com Angular 19 — headline (fl-input) e summary (fl-textarea).

### Google Cloud Console — Angular Material + cfc-select (validado 25/05/2026)

O Console do Google Cloud usa uma combinação de Angular Material + componentes customizados (`cfc-select`). Técnicas específicas que FUNCIONAM via CDP:

**Preencher `mat-form-field input` (texto):**
```javascript
// Achar o input pelo mat-form-field wrapper
var input = document.querySelectorAll('mat-form-field input')[0]; // índice 0 = primeiro campo
input.focus();
var setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
setter.call(input, 'MindCoach');  // valor desejado
input.dispatchEvent(new Event('input', { bubbles: true }));
input.dispatchEvent(new Event('change', { bubbles: true }));
input.dispatchEvent(new Event('blur', { bubbles: true }));
// Verificar: input.classList.contains('ng-dirty') → true
```

**Selecionar em `cfc-select` (dropdown com opções existentes):**
```javascript
// 1. Clicar no select para abrir
var select = document.querySelector('cfc-select[formcontrolname="userSupportEmail"]');
// getBoundingClientRect + Input.dispatchMouseEvent para clicar

// 2. Dropdown abre (aria-expanded="true"), opções aparecem como <mat-option>
// 3. Clicar na opção desejada
var options = document.querySelectorAll('mat-option');
for (var opt of options) {
    if (opt.innerText.includes('email@desejado.com')) {
        // getBoundingClientRect + Input.dispatchMouseEvent
    }
}
// 4. Verificar: select.classList.contains('ng-valid') → true
```

**PITFALL — CDP WebSocket async:** Eventos CDP (`Runtime.executionContextCreated`, etc.) chegam entre as respostas de comando. Filtrar sempre por `r.get('id') == msg_id`:
```python
def cdp(method, params=None):
    msg_id[0] += 1
    ws.send(json.dumps({'id': msg_id[0], 'method': method, 'params': params or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get('id') == msg_id[0]:  # ignora eventos (têm 'method', não 'id')
            return r
```

**PITFALL — `input[type=text]:not([type=search])` falha no GCloud:** O seletor CSS `input[type=text]:not([type=search])` retorna vazio no Console do Google Cloud. Usar `document.querySelectorAll('mat-form-field input')` para achar os campos.

1. SEMPRE verificar se API existe antes de fazer scraping
2. Respeitar robots.txt (verificar com curl primeiro)
3. Não sobrecarregar — espaço de 2-5s entre ações
4. browser_snapshot em vez de múltiplos browser_console (mais eficiente)
5. browser_vision para confirmar ações visuais (login, CAPTCHA)
6. Extrair dados estruturados com browser_console + JSON.stringify
7. Salvar resultados em arquivo via write_file para reprocessamento

## DEBUG

### Ver Erros JS da Página
```
browser_console → mostra console.log/error/warn da página
```

### Inspecionar Elemento Específico
```
browser_console(expression="document.querySelector('#target').outerHTML")
```

### Screenshot para Debug
```
browser_vision(question="O que está visível na página? Há erros?")
```

## NAVEGAÇÃO EM PLATAFORMAS

**Regra de ouro:** NUNCA adivinhar URLs. Navegar a partir da homepage ou dashboard da plataforma. Links diretos frequentemente quebram (páginas movidas, rotas dinâmicas, query params obsoletos).

```python
# ❌ ERRADO: adivinhar URL
cdp('Page.navigate', {'url': 'https://site.com/secao/que-talvez-nao-exista'})

# ✅ CERTO: navegar pelo menu da plataforma
cdp('Page.navigate', {'url': 'https://site.com/dashboard'})  # homepage
# Depois clicar nos menus: Projects → Search → Categoria
```

**Para buscar projetos/tarefas:**
1. Ir ao dashboard/homepage
2. Clicar no menu "Projetos" ou "Find Work"
3. Usar os filtros nativos da plataforma (categoria, orçamento)
4. NUNCA tentar construir URLs com query params manualmente

## ANTI-PADRÕES

- NÃO adivinhar URLs — navegar a partir da homepage
- NÃO fazer scraping em loop infinito
- NÃO usar browser para APIs REST documentadas (use curl/terminal)
- NÃO tentar burlar CAPTCHA (perda de tempo)
- NÃO clicar em elementos sem verificar snapshot antes
- NÃO assumir que elemento @ref existe — verificar com snapshot
