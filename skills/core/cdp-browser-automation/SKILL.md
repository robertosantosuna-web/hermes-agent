---
name: cdp-browser-automation
description: "Automação de browser via Chrome DevTools Protocol usando Edge existente com sessão logada. Funciona em Wayland, contorna SPAs Angular/React usando Input.dispatchMouseEvent."
version: 1.1.0
author: Roberto Rodrigues
metadata:
  hermes:
    tags: [cdp, browser, automation, edge, playwright-fallback, angular, react]
    related_skills: [browser-automation, freelancing-automation, desktop-control]
---

# CDP Browser Automation

Automação confiável de browser usando Chrome DevTools Protocol conectado ao Microsoft Edge ou Brave/Chromium existente. Funciona em Wayland, contorna SPAs Angular/React usando Input.dispatchMouseEvent.

**Suporte multi-browser:** Edge (porta 9222, IPv4), Edge WhatsApp (porta 9224, IPv4), Brave/Chromium headless (porta 9223, **IPv6-only `[::1]:9223`**, systemd service).

### CDP Port Matrix (atualizado 25/05)

| Porta | Browser | IP | Uso | Cuidados |
|-------|---------|-----|-----|----------|
| `:9222` | Brave real (usuário) | IPv4 `localhost` | Evitar — interfere na navegação | Pode estar offline |
| `:9223` | Brave headless (brain) | **IPv4 OU IPv6** | Automação forex (TradingView) | Testar `localhost` E `[::1]` |
| `:9224` | Edge (WhatsApp) | IPv4 `localhost` | WhatsApp Web automação | Sob demanda |

⚠️ **PITFALL — Porta 9223 muda IPv4/IPv6:** Dependendo de como o Brave foi iniciado (systemd vs manual), a porta 9223 pode escutar em IPv4 (`127.0.0.1`) ou IPv6 (`[::1]`). Sempre testar ambos: `curl http://localhost:9223/json/version` e `curl http://[::1]:9223/json/version`. O `brain_browser.py` usa `CDP_URL = 'http://localhost:9223'` (cobre ambos se o sistema resolver localhost para IPv4+IPv6).

**NUNCA abrir abas novas sem reuso** — cada `PUT /json/new` consome ~200MB RAM. Usar `navigate(url, reuse=True)`. **REGRA (25/05): máximo 1 aba ativa no brain browser.** Se precisar de outro par/símbolo, navegar na MESMA aba. Múltiplas abas = crash garantido.

**PITFALL — Vazamento de abas por cron jobs concorrentes (25/05/2026):** Múltiplos cron jobs (`brain_signal_generator.py`, `tv_chart_scanner.sh`, `forex_quote.py`) podem chamar `brain_browser.py` simultaneamente. Sem lock, cada chamada concorrente cria nova aba → 80+ abas em minutos. **Solução:** file lock (`fcntl.LOCK_EX | LOCK_NB`) + `cleanup_tabs()` no startup. Ver `references/brain-browser-config.md` para implementação completa e lista de jobs que causam leak.

**Google services — usar Edge :9222, NÃO Brave headless:** Google bloqueia navegadores headless/automatizados com "Esse navegador ou app pode não ser seguro". O Edge :9222 (Brave real do usuário) tem cookies de sessão Google (Gmail, Cloud Console, etc.) e passa na verificação. Serviços Google (AI Studio, Gmail, Calendar, Cloud Console) → abrir NO Edge :9222. Brave headless :9223 só para TradingView/análises sem autenticação Google.

### GCP Console Navigation & Service Account Creation (via CDP :9222)

Quando `gcloud auth login` falha (Google bloqueia browser headless), usar o Edge CDP :9222 para criar uma service account via console e autenticar com `gcloud auth activate-service-account`.

**Workflow completo (Service Account + Deploy):**
1. Abrir Service Accounts page no Edge :9222
2. Preencher formulário Material Design via `Input.dispatchKeyEvent` (char por char)
3. Selecionar role "Editor" usando CFC-SELECT-DUAL-COLUMN
4. Criar JSON key e capturar download de `~/.chromium.Chromium.*`
5. `gcloud auth activate-service-account --key-file=<json>`
6. Habilitar APIs necessárias (pode exigir browser se SA não tiver permissão)
7. Build via Cloud Build: `gcloud builds submit --tag ...`
8. Deploy: `gcloud run deploy ... --allow-unauthenticated --port 8080`
9. Se 403: liberar acesso público via console (radio "Permitir acesso público" → DOM manipulation → Salvar)

Templates para deploy: `templates/cloudrun-static-dockerfile`, `templates/cloudrun-nginx.conf`.

**Pitfalls específicos do GCP Console:**
- **Role selector** usa `<CFC-SELECT-DUAL-COLUMN>` (id dinâmico como `_0rif_cfc-select-dual-column-0`). Clicar abre dropdown com categorias à esquerda + roles à direita. Role "Editor" está em `.mdc-list-item__primary-text`, clicar no `mat-option` pai.
- **Service account ID** é derivado automaticamente do nome — não precisa preencher.
- **Download da key JSON** salva como `~/.chromium.Chromium.XXXXX` temporário no ~/Downloads. Capturar o arquivo `.org.chromium.Chromium.*` e renomear.
- **Formulários Material Design** aceitam `Input.dispatchKeyEvent` com `type: "char"` — NÃO usar `.value =` setter.
- **Botões** no GCP Console respondem a JS `.click()` (não precisa de `Input.dispatchMouseEvent` para botões simples).
- **Billing necessário** para Cloud Run/Cloud Build/Artifact Registry. Sem billing account vinculada, `gcloud services enable` falha com `UREQ_PROJECT_BILLING_NOT_FOUND`.

Ver `references/gcp-console-cdp-patterns.md` para DOM queries detalhadas e fluxo completo.

Setup do Brave headless persistente: `references/persistent-cdp-browser.md`.
Configuração do brain browser (systemd, pitfalls): `references/brain-browser-config.md`.

## ⚠️ RAM MANAGEMENT — CRÍTICO (25/05/2026)

**Cada nova aba CDP = ~200MB de RAM** (um processo renderer Brave/Chromium). Abrir 4 abas em sequência satura 800MB+.

### REGRA: SEMPRE REUSAR ABAS

```python
# brain_browser.py já suporta reuse=True (padrão desde 25/05)
async def navigate(url, reuse=True):
    """Reusa aba existente. Só cria nova se não houver nenhuma."""
    tab = None
    if reuse:
        tabs = json.loads(urllib.request.urlopen(f"{CDP_URL}/json/list").read())
        tab = next((t for t in tabs if t.get('type') == 'page'), None)
    if not tab:
        req = urllib.request.Request(f"{CDP_URL}/json/new", method='PUT')
        tab = json.loads(urllib.request.urlopen(req, timeout=5).read())
    # ... Page.navigate no tab existente
```

**NUNCA chamar `PUT /json/new` sem antes verificar se já existe aba reutilizável.** Para forex, usar `forex_quote.py` que chama `brain_browser.py --navigate` (reusa por padrão).

### Sinais de saturação
- RAM > 90% em máquina 8GB
- 10+ processos Brave renderer com idade < 5min
- Swap crescendo rapidamente
- **Ação**: matar renderers recentes e consertar o script que está criando abas

## PRÉ-REQUISITOS

**⚠️ REGRA ZERO: Verificar antes de usar.** Edge/Brave DEVE estar rodando com flags CDP. Se não estiver, NÃO tentar CDP — usar `desktop-control` skill como fallback.

### Verificar se CDP está disponível

```bash
# Teste rápido — deve retornar JSON com abas
curl -s --max-time 3 http://localhost:9222/json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{len(d)} tabs')" 2>&1
curl -s --max-time 3 http://[::1]:9223/json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{len(d)} tabs')" 2>&1
```

Se retornar erro ou vazio → browser NÃO está rodando com CDP. NÃO insistir com CDP. Usar desktop-control.

### ⚠️ IPv4 vs IPv6 na porta 9223

A porta 9223 pode estar em **IPv4** ou **IPv6** dependendo de como o Brave foi iniciado:
- **Systemd**: `--remote-debugging-port=9223` → pode ser IPv6-only `[::1]:9223`
- **Manual**: mesma flag → pode ser IPv4 `127.0.0.1:9223`

**Sempre testar ambos** antes de desistir:
```bash
curl -s http://localhost:9223/json/version || curl -s http://[::1]:9223/json/version
```

### Iniciar Edge com CDP (se necessário)

```bash
/usr/bin/microsoft-edge \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir="$HOME/.config/microsoft-edge" \
  --no-first-run
```

**⚠️ PITFALL — Turnstile bloqueia mesmo com perfil real:** Mesmo usando `--user-data-dir` apontando para o perfil ativo do usuário (com cookies de sessão válidos), o Cloudflare Turnstile ainda redireciona para `/login`. O CDP altera o fingerprint do navegador (WebSocket debugger, flags de automação) e o Turnstile detecta. **Injetar cookies de sessão via `Network.setCookie` também não resolve** — o Turnstile valida mais que cookies (canvas fingerprint, TLS fingerprint, presença de CDP). Conclusão: quando Turnstile está ativo, a ÚNICA via confiável é email monitoring + CloudFront download de anexos.

## BIBLIOTECA

Usar `websocket-client` (síncrono), NÃO `websockets` (async):
```python
import websocket  # websocket-client package
```
Instalar se necessário: `pip install websocket-client`

## PADRÃO DE CONEXÃO

```python
import json, time, urllib.request, websocket

# Listar abas
pages = json.loads(urllib.request.urlopen('http://localhost:9222/json', timeout=5).read())

# Filtrar por URL
target = next(p for p in pages if 'site-alvo.com' in p['url'])

# Conectar
ws = websocket.create_connection(target['webSocketDebuggerUrl'], timeout=10, origin='http://localhost:9222')

# Contador de mensagens
mid = [0]
def cdp(method, params=None):
    mid[0] += 1
    ws.send(json.dumps({'id': mid[0], 'method': method, 'params': params or {}}))
    while True:
        resp = json.loads(ws.recv())
        if resp.get('id') == mid[0]:
            return resp.get('result', {})

def ev(expr):
    """Evaluate JS, return value"""
    return cdp('Runtime.evaluate', {'expression': expr, 'returnByValue': True}).get('result', {}).get('value')
```

## NOVA ABA (REUSA SESSÃO EDGE)

```python
url = 'https://site-alvo.com/pagina'
req = urllib.request.Request(f'http://localhost:9222/json/new?{url}', method='PUT')
resp = json.loads(urllib.request.urlopen(req, timeout=8).read())
ws = websocket.create_connection(resp['webSocketDebuggerUrl'], timeout=15, origin='http://localhost:9222')

# Aguardar renderização
time.sleep(4)
cdp('Runtime.enable')
time.sleep(1)
```

**IMPORTANTE:** `PUT /json/new?url` (não GET). Cada aba tem WebSocket próprio e Runtime domain limpo.

**Telegram Web K específico:** O envio de mensagens usa `Input.dispatchKeyEvent` com `type: "char"` (NUNCA `textContent` — fica como draft). BotFather bot creation flow completo documentado. Ver `references/telegram-web-k-cdp.md`.

### Reusar aba existente vs nova aba

```python
# Verificar se já existe aba para a plataforma
pages = json.loads(urllib.request.urlopen('http://localhost:9222/json', timeout=5).read())
existing = next((p for p in pages if 'dominio-alvo.com' in p.get('url','')), None)

if existing:
    # Reconectar na aba existente (preserva estado do formulário)
    ws = websocket.create_connection(existing['webSocketDebuggerUrl'], timeout=15, origin='http://localhost:9222')
else:
    # Abrir nova aba
    req = urllib.request.Request(f'http://localhost:9222/json/new?{url}', method='PUT')
    resp = json.loads(urllib.request.urlopen(req, timeout=8).read())
    ws = websocket.create_connection(resp['webSocketDebuggerUrl'], timeout=15, origin='http://localhost:9222')
```

**Quando reusar:** formulário parcialmente preenchido, sessão autenticada pós-OAuth, dashboard já carregado.
**Quando abrir nova:** primeira visita à plataforma, página limpa sem estado, evitar contaminação de cookies/scripts de outras abas.

> Ver `references/platform-registration-results-2026-05-19.md` para o log detalhado de cadastros multi-plataforma.

## CLICAR EM ELEMENTOS (SPAs Angular/React)

`element.click()` NÃO funciona em SPAs. Usar `Input.dispatchMouseEvent` com coordenadas:

```python
def click(x, y):
    cdp('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': x, 'y': y})
    time.sleep(0.05)
    cdp('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})
    time.sleep(0.05)
    cdp('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})
```

### Encontrar coordenadas de elemento

```python
# Por seletor CSS
pos = json.loads(ev(f'''
    (() => {{
        const el = document.querySelector('{selector}');
        if (!el) return JSON.stringify({{error: "not found"}});
        el.scrollIntoView({{block: "center", behavior: "instant"}});
        const r = el.getBoundingClientRect();
        return JSON.stringify({{x: r.left + r.width/2, y: r.top + r.height/2}});
    }})()
'''))

# Por texto contido em fl-list-item (Angular)
pos = json.loads(ev(f'''
    (() => {{
        const items = document.querySelectorAll("fl-list-item");
        for (const item of items) {{
            if (item.textContent.includes("{target_text}")) {{
                const header = item.querySelector(".BitsListItemHeader");
                header.scrollIntoView({{block: "center", behavior: "instant"}});
                const r = header.getBoundingClientRect();
                return JSON.stringify({{x: r.left + r.width/2, y: r.top + r.height/2}});
            }}
        }}
        return JSON.stringify({{error: "not found"}});
    }})()
'''))
```

## PREENCHER INPUTS EM ANGULAR

Angular 19 usa componentes customizados (`fl-input`, `fl-textarea`) que envolvem um `<input class="NativeElement">` ou `<textarea class="TextArea">` nativo. O setter de `value` nativo NÃO funciona nesses wrappers — o counter de caracteres e a validação do Angular não disparam.

### Método que FUNCIONA: `Input.dispatchKeyEvent` caractere por caractere

```python
def type_text(text):
    """Type text via keyboard events — Angular change detection picks this up"""
    for char in text:
        cdp('Input.dispatchKeyEvent', {
            'type': 'keyDown', 'text': char, 
            'unmodifiedText': char, 'key': char
        })
        cdp('Input.dispatchKeyEvent', {
            'type': 'keyUp', 'text': char, 
            'unmodifiedText': char, 'key': char
        })
```

**Fluxo completo para campo Angular:**
```python
# 1. Encontrar o input nativo DENTRO do wrapper
pos = ev('''
    (() => {
        const inp = document.querySelector('fl-input .NativeElement');
        if (!inp) return null;
        inp.scrollIntoView({block: "center", behavior: "instant"});
        const r = inp.getBoundingClientRect();
        return {x: r.left + r.width/2, y: r.top + r.height/2};
    })()
''')

# 2. Clicar triplo para selecionar todo o texto existente
cdp('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': pos['x'], 'y': pos['y']})
time.sleep(0.05)
cdp('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': pos['x'], 'y': pos['y'], 'button': 'left', 'clickCount': 3})
time.sleep(0.05)
cdp('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': pos['x'], 'y': pos['y'], 'button': 'left', 'clickCount': 3})
time.sleep(0.2)

# 3. Digitar caractere por caractere
for char in new_text:
    cdp('Input.dispatchKeyEvent', {'type': 'keyDown', 'text': char, 'key': char})
    cdp('Input.dispatchKeyEvent', {'type': 'keyUp', 'text': char, 'key': char})
```

**Para textarea Angular (`fl-textarea`):**
```python
# O seletor é 'textarea.TextArea'
pos = ev('''
    (() => {
        const ta = document.querySelector('textarea.TextArea');
        if (!ta) return null;
        ta.scrollIntoView({block: "center"});
        const r = ta.getBoundingClientRect();
        return {x: r.left + r.width/2, y: r.top + r.height/2};
    })()
''')
# Depois mesma lógica: triple-click → type_text()
```

### React textarea: `execCommand('insertText')` (FALLBACK CRÍTICO)

Quando `Input.dispatchKeyEvent` NÃO funciona (ex: 99Freelas React SPA), usar `execCommand`:

```python
ev('''
(() => {
    const ta = document.querySelector('textarea');
    if (!ta) return "no textarea";
    ta.focus();
    ta.select();
    const ok = document.execCommand('insertText', false, `MENSAGEM AQUI`);
    return JSON.stringify({ok, len: ta.value.length});
})()
''')
```

**Verificar** sempre após preencher:
```python
ev('document.querySelector("textarea")?.value?.substring(0, 80) || "EMPTY"')
```

### Método que NÃO funciona (evitar)

- `Input.insertText` → Angular/React ignora
- Setter nativo de `value` + eventos `input`/`change`/`blur` → counter não atualiza, validação não dispara
- `element.value = "texto"` direto → Angular/React não detecta
- `Input.dispatchKeyEvent` em React (99Freelas) → texto não entra no campo

## SCREENSHOT

```python
result = cdp('Page.captureScreenshot', {'format': 'jpeg', 'quality': 60})
import base64
with open('/tmp/screenshot.jpg', 'wb') as f:
    f.write(base64.b64decode(result['data']))
```

## FALLBACK: DESKTOP CONTROL

Quando Edge/CDP NÃO está disponível, usar `desktop-control` para interagir com o desktop via mouse/teclado:

```python
# Iniciar daemon (se não estiver rodando)
subprocess.Popen(['/usr/bin/python3', '/home/roberto/.hermes/scripts/desktop_daemon.py'], 
    env={'DISPLAY': ':0', 'WAYLAND_DISPLAY': 'wayland-0', 'XDG_RUNTIME_DIR': '/run/user/1000'})

# Conectar e controlar
import websockets, json
async with websockets.connect('ws://127.0.0.1:9876') as ws:
    await ws.send(json.dumps({'id':1, 'action':'click', 'params':{'x':500, 'y':300}}))
```

**Quando usar desktop-control em vez de CDP:**
- Edge não está rodando com `--remote-debugging-port`
- Cloudflare Turnstile bloqueou o acesso CDP à página
- Botão React não responde a `Input.dispatchMouseEvent` (caso do 99Freelas "Enviar")
- Preciso interagir com app não-browser (file picker, diálogo nativo)

## FALLBACK: EXECUÇÃO DE SCRIPTS CDP

CDP scripts normalmente usam `execute_code` (com `from hermes_tools import terminal`). Se `execute_code` falhar, usar `terminal()` com Python inline:

```bash
# Prefira /usr/bin/python3 (tem websocket-client)
/usr/bin/python3 -c '
import json, urllib.request, websocket, time
# ... script CDP ...
'
```

**Pitfall de escaping:** `terminal()` com `-c` exige cuidado com aspas. Use aspas simples no outer, duplas no inner. Evite f-strings com aspas triplas aninhadas. Se o script for muito longo, escreva com `python3 -c "open('/tmp/script.py','w').write(...)"` e execute depois.

## ANTI-PADRÃO: RETENTAR CDP SEM DIAGNÓSTICO

**NUNCA repetir chamadas CDP quando a porta 9222 não responde.** Se `curl localhost:9222/json` falhar:
1. Verificar se Edge está rodando: `pgrep -a msedge`
2. Se não: iniciar Edge COM as flags CDP, OU usar desktop-control
3. Se sim mas sem CDP: matar Edge e reiniciar COM flags

Repetir a mesma chamada CDP 3+ vezes sem diagnóstico é desperdício de tokens e frustração do usuário.

| Componente | Onde aparece | Sintoma | Solução |
|-----------|-------------|---------|---------|
| **Bootstrap-select** | Clickworker, SproutGigs, OneForma | `select.value = "br"` + `change` event NÃO funciona. Dropdown visual não atualiza. | Mouse click no dropdown customizado + click na opção. Ou usuário resolve manualmente. |
| **React custom dropdown** | Neevo language selector | Lista virtualizada, `Input.dispatchKeyEvent` não filtra, opções não estão no DOM | Scroll no container até a opção aparecer + click. Ou usar `select.options[i].selected` + `dispatchEvent` (funcionou para definir valor mas não para UI React) |
| **PerimeterX CDP block** | Fiverr inbox | ERRCODE PXCR10002539 bloqueia navegação CDP | Sem workaround. Usar email monitoring. |
| **Google OAuth consent** | Conta Google | Account chooser + consent screen normais | Padrão funciona: click profile → click "Continuar". Sessão Google do Edge é herdada. |

16. **99Freelas botão "Enviar" (React) — RESISTENTE a tudo**: o botão de envio de mensagens do 99Freelas ignora `Input.dispatchMouseEvent`, JS `.click()`, `dispatchEvent(new MouseEvent(...))`, e tecla Enter via `Input.dispatchKeyEvent`. **WORKAROUND PARCIAL**: o textarea ACEITA `document.execCommand('insertText', false, texto)` — o campo preenche corretamente (ver seção "React textarea: execCommand" acima). Só o submit que nunca dispara. **Solução final**: preencher via `execCommand('insertText')` e entregar o conteúdo pronto ao usuário para clicar Enviar manualmente (~30s).
17. **Elementos React com 0x0 dimensions**: quando React esconde textareas/botões condicionalmente, `getBoundingClientRect()` retorna (0,0,0,0). Forçar visibilidade via CSS inline antes de interagir:
    ```javascript
    el.style.display = 'block';
    el.style.visibility = 'visible';
    el.style.width = '600px';
    el.style.height = '100px';
    ```
    Após forçar, re-query `getBoundingClientRect()` para obter coordenadas válidas para `Input.dispatchMouseEvent`.
18. **NodeIds do DOM.getDocument são VOLÁTEIS**: entre chamadas CDP consecutivas, os nodeIds podem expirar (erro "Could not find node with given id"). Re-executar `DOM.querySelector` imediatamente antes de `DOM.setFileInputFiles` ou `DOM.focus`. Não armazenar nodeIds entre chamadas separadas por `Runtime.evaluate` ou `time.sleep()`.
19. **`Input.insertText` + foco prévio funciona em alguns casos React**: após forçar visibilidade CSS e clicar no elemento para focá-lo, `Input.insertText` caractere por caractere preenche textareas React. Mas quando falhar, usar `document.execCommand('insertText', false, texto)` — este método funcionou no 99Freelas (React) quando `Input.insertText` e `Input.dispatchKeyEvent` falharam. Ver seção "React textarea: execCommand" acima.
20. **Navegação por UI, NÃO por URL guessing — REGRA ZERO**: NUNCA construir URLs manualmente (`/users/settings/profile`, `/messages/inbox/ID`, `/verified`). Esta é a falha mais frequente e mais custosa nesta sessão. Páginas de SPA (Angular/React) frequentemente retornam 404 ou redirect inesperado para URLs diretas mesmo quando a funcionalidade existe via navegação por UI. O caminho correto: (1) abrir a página base da plataforma via `PUT /json/new`, (2) navegar clicando nos menus, (3) verificar `window.location.href` após cada clique. Exemplo real 19/05: `freelancer.com/verified` → 404, mas o link "Trust & Verification" no menu da sidebar carrega a página correta.

1. **`element.click()` — regra por tipo de página**: 
   - **React/Angular SPAs**: `Input.dispatchMouseEvent` é o padrão, mas NÃO é universal. Botões de submit em alguns frameworks React (ex: 99Freelas) podem ignorar `Input.dispatchMouseEvent` e só responder a JS `.click()` + `dispatchEvent(new MouseEvent(...))`. Se `Input.dispatchMouseEvent` falhar, tentar o fallback JS.
   - **Google OAuth (account chooser, consent)**: `element.click()` FUNCIONA e é mais confiável que mouse events.
   - **Server-rendered pages (Rails, PHP)**: `element.click()` geralmente funciona.
   - Regra prática: se `Input.dispatchMouseEvent` não surtiu efeito (URL não mudou, texto não enviou), tentar `element.click()` + dispatch de MouseEvent como fallback. Testar ambos antes de desistir.
2. **Sempre `scrollIntoView({block: "center"})`** antes de `getBoundingClientRect` — elemento fora da viewport retorna coordenadas erradas.
3. **Múltiplos botões "Next"**: ordenar por `bottom` e pegar o mais baixo (o submit real).
4. **`returnByValue: True` retorna o valor diretamente**: se o JS retorna `{x: 1}`, `ev()` retorna o dict `{x: 1}`, NÃO uma string JSON. Não usar `json.loads()` no retorno. Usar `json.loads()` só quando o JS retorna `JSON.stringify(...)`.
5. **Runtime.evaluate falha após navegação**: re-enable Runtime após Page.navigate e aguardar 3-4s para SPAs renderizarem.
6. **Timeout em páginas pesadas**: Angular 19 com 1000+ nós DOM pode travar eval_js. Abrir nova aba limpa via `PUT /json/new?url` — cookies/sessão do Edge são herdados.
7. **Botões "Skip" podem ser `<a>` tags**: buscar em `button, a, [role="button"]`, não só `button`.
8. **Campos Angular customizados (`fl-input`, `fl-textarea`)**: o input nativo está dentro como `.NativeElement` (input) ou `.TextArea` (textarea). Usar `Input.dispatchKeyEvent` caractere por caractere — setter nativo + eventos NÃO funcionam.
9. **PerímetroX (Fiverr inbox)**: bloqueia CDP completamente. Não há workaround.
10. **Navegação entre páginas**: `Page.navigate` destrói contexto de execução. Melhor abrir nova aba via `PUT /json/new?url`.
11. **`await`/Promise em Runtime.evaluate**: precisa do param `awaitPromise: true`.
12. **React virtualized/windowed lists**: elementos fora do viewport podem NÃO estar no DOM (ex: Neevo language picker — "Portuguese" no índice 172 não existe no DOM até scroll). `scrollTop` no container não adiciona itens ao DOM. Usar o campo de busca/filtro do componente ou navegação por teclado (ArrowDown + Enter).
13. **Bootstrap-select custom components**: JS `value` setter + eventos `change`/`input` NÃO funcionam. O Bootstrap-select intercepta o select nativo e só responde à API jQuery (`$(el).selectpicker('val', '...')`) ou interação de mouse (abrir dropdown → clicar opção). Se jQuery estiver disponível no page context, usar; senão, interação manual. Ex: formulário do Clickworker.
14. **Service worker iframe após redirects**: após submissão de formulário ou navegação, a aba pode redirecionar para um iframe de service worker (`*.run.app/_/service_worker/...`). Verificar `window.location.href` após cada ação de navegação; se cair em iframe, re-listar abas e reconectar à aba principal da plataforma.
15. **Testes interativos com timer (ex: Neevo Writing Test)**: testes que não podem ser pausados, têm timer por seção, e exigem interações precisas (clicar em espaços no texto, selecionar erros com mouse) são **ALTO RISCO** para CDP. Uma falha de conexão ou elemento não encontrado no meio do teste perde a tentativa. Nestes casos, **reportar ao usuário e recomendar execução manual.**

## WORKFLOW COMPLETO (FREELANCER EXEMPLO)

```python
# 1. Abrir nova aba logada
url = 'https://www.freelancer.com/new-freelancer/skills'
req = urllib.request.Request(f'http://localhost:9222/json/new?{url}', method='PUT')
resp = json.loads(urllib.request.urlopen(req, timeout=8).read())

# 2. Conectar e aguardar renderização
ws = websocket.create_connection(resp['webSocketDebuggerUrl'], timeout=15)
time.sleep(4)
cdp('Runtime.enable')

# 3. Interagir
# ... cliques com Input.dispatchMouseEvent ...

# 4. Fechar
ws.close()
```

## GOOGLE OAUTH FLOW (CONFIÁVEL)

Fluxo testado e funcional em Toloka e TimeBucks (19/05/2026). A sessão do Google no Edge é herdada pela nova aba CDP.

```python
# 1. Clicar "Continue with Google" — Input.dispatchMouseEvent ou element.click()
google_btn = json.loads(ev('''(function() {
    const all = document.querySelectorAll("button");
    for (const el of all) {
        if (el.innerText.trim().includes("Google")) {
            el.scrollIntoView({block: "center", behavior: "instant"});
            const r = el.getBoundingClientRect();
            return JSON.stringify({x: r.left+r.width/2, y: r.top+r.height/2});
        }
    }
    return "null";
})()'''))
click(google_btn['x'], google_btn['y'])
time.sleep(6)

# 2. Google Account Chooser — usar element.click() (NÃO Input.dispatchMouseEvent)
#    Input.dispatchMouseEvent no account chooser NÃO funciona. JS click sim.
ev('''(function() {
    const all = document.querySelectorAll("*");
    for (const el of all) {
        if (el.childNodes.length <= 3 && el.innerText.includes("Roberto")) {
            let clickable = el;
            for (let i = 0; i < 5; i++) {
                if (clickable.hasAttribute("data-profileindex") || clickable.tagName === "LI") {
                    clickable.click(); return "clicked " + clickable.tagName;
                }
                clickable = clickable.parentElement;
            }
            el.click(); return "clicked text element";
        }
    }
    return "not found";
})()''')
time.sleep(5)

# 3. OAuth Consent — clicar "Continuar"
ev('''(function() {
    const all = document.querySelectorAll("button, span");
    for (const el of all) {
        if (el.innerText.trim() === "Continuar") { el.click(); return "clicked"; }
    }
    return "not found";
})()''')
time.sleep(6)

# 4. Verificar URL final — deve estar de volta na plataforma alvo
url = ev('window.location.href')
```

**Pitfalls Google OAuth:**
- O account chooser `/v3/signin/accountchooser` pode demorar 5-8s para carregar
- Se o perfil não for encontrado, tentar `Input.dispatchMouseEvent` na região central (~960, 400)
- A tela de consentimento (`/signin/oauth/consent`) pede "Continuar" — clicar e aguardar redirect
- Após redirect, verificar que `window.location.href` voltou ao domínio da plataforma

## MULTI-PLATFORM REGISTRATION PIPELINE

Padrão para cadastro autônomo em múltiplas plataformas via CDP:

```
Para cada plataforma:
  1. PUT /json/new?url → nova aba com sessão Edge
  2. Aguardar 4-6s + Runtime.enable
  3. Scan da página: título, body text, inputs, buttons
  4. Se landing page → encontrar link de signup/register e navegar direto
  5. Preencher formulário (por placeholder ou ID)
  6. Submeter
  7. Verificar redirect (URL mudou? body mudou?)
  8. Salvar credenciais em arquivo YAML
  9. Se bloqueio (Bootstrap-select, React virtualized list) → marcar como "pendente" e seguir
  10. Próxima plataforma
```

**Heurísticas de formulário:**
- Campos de texto padrão: `el.value = "..."` + dispatch `input` + `change` = funciona
- Bootstrap-select: NÃO funciona com JS setter — marcar como pendente
- React virtualized dropdowns: elementos podem não estar no DOM — tentar search/filter, se falhar marcar pendente
- Checkboxes: `el.checked = true` + dispatch `change` = funciona
- Google OAuth: usar o flow dedicado acima

**Arquivo de credenciais** (`~/.hermes/forex/user_profile.yaml`):
```yaml
plataformas:
  nome_plataforma:
    email: "..."
    senha: "..."
    status: "ativo|pendente|aguardando_sms"
    url: "..."
    data_cadastro: "YYYY-MM-DD"
```

## VNC DO XVFB (Espelhamento de Tela)

Para o usuário ver o display virtual (ex: MT5 no Wine), usar x11vnc:

```bash
# Instalar
sudo apt install -y x11vnc tigervnc-viewer

# Iniciar VNC no Xvfb :99 (CRÍTICO: unset WAYLAND_DISPLAY)
python3 -c "
import subprocess, os
env = os.environ.copy()
env['DISPLAY'] = ':99'
env.pop('WAYLAND_DISPLAY', None)
env.pop('XDG_SESSION_TYPE', None)
subprocess.Popen(['x11vnc', '-forever', '-shared', '-nopw', '-display', ':99'], env=env)
"

# Conectar (abre janela no GNOME)
vncviewer localhost:5900
```

### Pitfall: x11vnc detecta Wayland mesmo com DISPLAY=:99
x11vnc 0.9.17+ detecta `WAYLAND_DISPLAY` no ambiente e recusa iniciar com "Wayland display server detected". Solução: remover `WAYLAND_DISPLAY` e `XDG_SESSION_TYPE` do ambiente ao iniciar o x11vnc.

```bash
# Verificar se CDP está ativo
curl -s --max-time 3 http://localhost:9222/json | python3 -c "import json,sys; print(f'{len(json.load(sys.stdin))} tabs')"
```
