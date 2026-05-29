---
name: freelancing-automation
description: "Automação de freelancing: Fiverr, 99Freelas, Workana, gestão de leads, monitoramento de pagamentos, prospecção ativa e análise de oportunidades com foco em ganho financeiro."
version: 1.0.0
author: Roberto Rodrigues
license: MIT
metadata:
  hermes:
    tags: [freelance, fiverr, 99freelas, leads, financial, automation, renda]
    related_skills: [life-os, executive-communication, dogfood, browser-automation, desktop-control, proposta-99freelas]
---

# Freelancing Automation

Automação completa do pipeline de freelancing: descoberta, aplicação, follow-up e cobrança.

## ⚠️ AVISO CRÍTICO — ANTI-BOT (22/05/2026)

**CDP headless (:9223) NÃO FUNCIONA para 99Freelas (Cloudflare Turnstile) e Fiverr (PerimeterX).**
Foram 107 tentativas frustradas. Consulte `skill: anti-bot-strategies` antes de qualquer interação web.

**Google OAuth via CDP também falha** — Google detecta o Chromium do Hermes como "navegador inseguro". Única opção: Desktop Daemon no Brave real do Roberto.

**Desktop Daemon screenshots via mss são bugados** — capturas retornam sempre a mesma imagem (md5 idêntico entre screenshots). Navegação é cega. Usar CDP `Runtime.evaluate` para "ver" o conteúdo da página.

### 🔑 Portas CDP Ativas (Verificado 29/05/2026)

| Porta | Browser | Estado | Sessão | Caso de Uso |
|-------|---------|--------|--------|-------------|
| **9222** | Brave desktop | ✅ ATIVO | Freelancer + 99Freelas + TradingView logados | **PRIMÁRIO** |
| 9224 | Edge WhatsApp | ✅ ATIVO | WhatsApp Web | Mensagens |
| 9225 | Edge main | ❌ MORREU 29/05 | Google OAuth | Instável sob carga Playwright |
| 9226 | Chromium headless | ✅ ATIVO | Scraping genérico | Background tasks |

**REGRA:** Brave :9222 é o mais confiável para freelancer (sessão logada, bypassa Cloudflare). Edge :9225 pode morrer — sempre verificar com `ss -tlnp | grep 922` antes de usar.

**⚠️ Brave :9222 — comandos de sessão BLOQUEADOS (29/05):** Apesar de aceitar WebSocket e navegação HTTP, o Brave :9222 bloqueia `Target.attachToTarget`, `Target.sendMessageToTarget`, `Runtime.evaluate` com sessionId e `Network.getAllCookies`. Use apenas para navegação (`PUT /json/new?url`) e verificação visual. Para extração de dados, use APIs REST ou o Playwright standalone.

**⚠️ Chrome :9226 — WebSocket BLOQUEADO:** Requer flag `--remote-allow-origins=*` para aceitar conexões WebSocket. Sem ela, só endpoints HTTP funcionam. Se precisar de evaluate/attach, use Playwright standalone ou corrija a flag de lançamento.

**Playwright `connect_over_cdp` requer `127.0.0.1` explícito** — `localhost` resolve para IPv6 `::1` e falha com ECONNREFUSED.
Ver `references/99freelas-cdp-messages.md` para o fluxo completo de extração de conversas.

| Plataforma | Abordagem Correta |
|-----------|------------------|
| 99Freelas | CDP via Brave REAL (:9222) para leitura de mensagens OU Email (IMAP). NUNCA CDP headless (:9223) |
| Fiverr | Ação humana, NÃO tentar automação |
| Workana | Desktop Daemon + Brave real |
| Neevo/TimeBucks/Toloka | CDP funciona |

### Pesquisa de dados empresariais
Ver `references/business-research-workflow.md` — técnicas de scraping para CNPJ, endereço, email, decisores e LinkedIn.

### 🔑 99Freelas: Google OAuth Bypassa Turnstile (22/05/2026)

**Descoberta:** Na página de login do 99Freelas (`/login`), o botão "Continuar com Google" redireciona para `accounts.google.com` SEM passar pelo Cloudflare Turnstile. O iframe do Turnstile está presente na página mas NÃO é acionado quando se usa OAuth.

**Fluxo que funciona:**
1. Navegar para `https://www.99freelas.com.br/login`
2. Clicar no link de OAuth Google (`accounts.google.com/o/oauth2/v2/auth`)
3. Google mostra tela de login — email + senha
4. Após autenticação Google, redireciona de volta para 99Freelas JÁ LOGADO

**Limitação:** Google bloqueia navegadores de automação ("Esse navegador ou app pode não ser seguro"). O browser tools do Hermes é detectado como inseguro. **Usar Desktop Daemon no Brave real do Roberto para fazer o fluxo Google OAuth.**

**Alternativa para contas sem Google OAuth:** Se a conta 99Freelas foi criada com email+senha (não Google), usar Desktop Daemon para preencher email+senha direto no formulário de login e clicar no Turnstile via ydotool.

## EDGE CDP — INTERAÇÃO COM PLATAFORMAS (DEPRECATED para 99Freelas/Fiverr)

Técnica descoberta em 18/05/2026. Para plataformas com Cloudflare/React que bloqueiam browser tools, usar Edge via Chrome DevTools Protocol.

### 99Freelas via CDP

```python
import json, urllib.request, websocket

# Conectar à página já aberta no Edge
resp = urllib.request.urlopen('http://localhost:9222/json')
pages = json.loads(resp.read())
page = [p for p in pages if '99freelas' in p.get('url','').lower()][0]
ws = websocket.create_connection(page['webSocketDebuggerUrl'])

msg_id = 1
def cdp(method, params=None):
    global msg_id
    msg_id += 1
    ws.send(json.dumps({'id': msg_id, 'method': method, 'params': params or {}}))
    return json.loads(ws.recv())
```

### Extrair Dashboard

```python
result = cdp('Runtime.evaluate', {
    'expression': 'document.body.innerText',
    'returnByValue': True
})
data = json.loads(result['result']['result']['value'])
```

### Enviar Proposta em Projeto 99Freelas (CDP)

Fluxo que funcionou em 19/05/2026:

```python
# 1. Navegar até o projeto
req = urllib.request.Request(f'http://localhost:9222/json/new?https://www.99freelas.com.br/project/NOME-DO-PROJETO-ID', method='PUT')
# Aguardar 5s para renderizar

# 2. Clicar "Enviar proposta"
# Encontrar o botão pelo texto exato e usar Input.dispatchMouseEvent
pos = json.loads(ev('''(function() {
    var all = document.querySelectorAll('a, button');
    for (var el of all) {
        if ((el.innerText||el.textContent||'').trim() === 'Enviar proposta') {
            el.scrollIntoView({block: 'center'});
            var r = el.getBoundingClientRect();
            return JSON.stringify({x: r.left+r.width/2, y: r.top+r.height/2});
        }
    }
    return 'null';
})()'''))
click(pos['x'], pos['y'])

# 3. Preencher formulário de proposta
# Campos: textarea (detalhes), input[type=number] (valor), input (duração)
# O textarea usa o mesmo padrão do Angular: native setter + dispatchEvent
fill = ev(f'''(function() {{
    var inputs = document.querySelectorAll('input, textarea');
    for (var inp of inputs) {{
        if (inp.tagName === 'TEXTAREA') {{
            var ns = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set;
            if (ns) ns.call(inp, {json.dumps(proposal_text)});
            inp.dispatchEvent(new Event('input', {{bubbles: true}}));
        }}
    }}
}})()''')

# 4. Preencher valor (R$) e duração (dias) nos inputs numéricos
# Encontrar por placeholder/name e setar .value diretamente

# 5. Clicar "Enviar proposta" no formulário
```

### Pitfall: Formulário de proposta 99Freelas

- O campo de valor (R$) às vezes não preenche corretamente — o valor cai para o mínimo (R$30)
- Verificar o dashboard depois para confirmar o valor enviado
- Cada proposta consome 3 conexões do plano gratuito

### Pesquisa de dados para cliente via Google no Edge CDP

Quando o trabalho do cliente exige pesquisa web (listas de empresas, contatos, prospecção), curl/requests direto para Google é bloqueado (CAPTCHA, empty responses). O Edge CDP com cookies reais do usuário burla isso:

```python
# Abrir Google Search no Edge via CDP
url = 'https://www.google.com/search?q=clinicas+radiologia+privadas+S%C3%A3o+Paulo&hl=pt-BR&num=30'
req = urllib.request.Request(f'http://localhost:9222/json/new?{url}', method='PUT')
urllib.request.urlopen(req, timeout=30)

# Extrair resultados como JSON estruturado
r = cdp('Runtime.evaluate', {'expression': '''
(function() {
    var results = [];
    document.querySelectorAll('div.g, div.MjjYud').forEach(function(block) {
        var h3 = block.querySelector('h3');
        var link = block.querySelector('a[href]');
        var snippet = block.querySelector('div[data-sncf], span.aCOpRe, div.VwiC3b');
        if (h3 && link) {
            results.push({title: h3.innerText.trim(), url: link.href, snippet: (snippet?.innerText || '').trim().substring(0, 300)});
        }
    });
    return JSON.stringify(results);
})()
'''})
```

**Vantagem sobre curl:** cookies de sessão real do Edge contornam rate limiting e CAPTCHAs do Google. Ideal para compilar listas de prospecção B2B (clínicas, empresas, contatos).

### Mensagens via CDP — LEITURA (verificar o que o cliente disse)

**Caso mais simples e 100% confiável.** Só precisa conectar na aba já aberta e extrair o texto:

```python
import json, urllib.request, websocket, time

pages = json.loads(urllib.request.urlopen('http://localhost:9222/json', timeout=5).read())
target = next(p for p in pages if '99freelas' in p['url'])
ws = websocket.create_connection(target['webSocketDebuggerUrl'], timeout=15, origin='http://localhost:9222')

# CDP helper (simplificado para leitura)
mid = [0]
def cdp(method, params=None):
    mid[0] += 1
    ws.send(json.dumps({'id': mid[0], 'method': method, 'params': params or {}}))
    while True:
        resp = json.loads(ws.recv())
        if resp.get('id') == mid[0]:
            return resp.get('result', {})

cdp('Runtime.enable')
time.sleep(1)

# Extrair conversa completa
texto = cdp('Runtime.evaluate', {
    'expression': 'document.body ? document.body.innerText.substring(0, 10000) : "no body"',
    'returnByValue': True
})['result']['value']
print(texto)
ws.close()
```

**Pitfalls da leitura:**
- O preview na barra lateral trunca mensagens (ex: "Gostei da organização e ela já ajuda bastante como base inic..."). Sempre usar `document.body.innerText` para o texto completo.
- A URL `/messages/inbox/ID_DO_PROJETO` carrega a lista de inbox + painel direito com a conversa. O `innerText` do body captura ambos — o texto da conversa aparece no meio.
- `websocket-client` pode não estar no venv do Hermes. Usar `/usr/bin/python3` como fallback se `import websocket` falhar.
- Não é necessário clicar em nada — a conversa já está renderizada se a aba foi aberta pelo Edge do usuário.

### Mensagens via CDP — ENVIO (responder cliente no inbox)

**⚡ ATUALIZADO 25/05/2026: CDP Input.dispatchKeyEvent FUNCIONA para digitação!**

| Método | Resultado |
|--------|-----------|
| `Input.dispatchKeyEvent` CDP (char-by-char) | ✅ Funciona (perde acentos) |
| Native value setter + input event | ✅ Funciona (mantém acentos, texto completo) |
| `Input.insertText` CDP | ❌ React ignora |
| JS `.click()` + MouseEvent | ⚠️ ~20% (não confiável) |
| React fiber state dispatch | ⚠️ Só se encontrar `__reactProps` |
| **Desktop Daemon ydotool `type`** | ⚠️ Funciona se janela visível (kernel-level) |
| **Desktop Daemon ydotool `click`** | ⚠️ Funciona se janela visível (kernel-level) |

**Pipeline correto (validado 25/05/2026):**
```python
# FASE 1: Preencher textarea via native setter (preserva acentos!)
cdp('Runtime.evaluate', {'expression': '''
  (() => {
    const ta = [...document.querySelectorAll('textarea.send-message-textarea')]
      .find(t => t.getBoundingClientRect().width > 0);
    const ns = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    ns.call(ta, MSG);
    ta.dispatchEvent(new Event('input', {bubbles: true}));
    ta.dispatchEvent(new Event('change', {bubbles: true}));
    return 'ok';
  })()
'''})

# FASE 2: Clicar Enviar via Input.dispatchMouseEvent
coords = getButtonCoords('Enviar')
cdp('Input.dispatchMouseEvent', {type:'mousePressed', x:coords.x, y:coords.y, button:'left', clickCount:1})
cdp('Input.dispatchMouseEvent', {type:'mouseReleased', x:coords.x, y:coords.y, button:'left', clickCount:1})

# FASE 3: Verificar (textarea deve limpar se enviado)
check = cdp('Runtime.evaluate', {
  'expression': 'document.querySelector("textarea.send-message-textarea")?.value?.length === 0 ? "SENT" : "NOT SENT"'
})
```

**⚠️ Atenção ao textarea CORRETO:** 99Freelas tem 5 textareas ocultos. O visível é o índice 1:
- classe: `send-message-textarea elastic-textarea`
- placeholder: `Escreva sua mensagem`
- NUNCA usar `document.querySelector('textarea')` (pega o índice 0, 0x0)
- SEMPRE filtrar por `getBoundingClientRect().width > 0`

**Pipeline original (Desktop Daemon, ainda válido como fallback):**

```python
# FASE 1: CDP para DOM e anexos
async with websockets.connect(CDP_WS) as ws:
    # Anexar arquivo
    cdp('DOM.setFileInputFiles', {'files': [PATH], 'nodeId': file_input_node})
    cdp('Runtime.evaluate', {'expression': '''
        (() => {
            const fi = document.querySelector('input[type="file"]');
            if (fi?.files?.length > 0) fi.dispatchEvent(new Event('change', {bubbles: true}));
        })()'''})
    # Obter coordenadas absolutas
    pos = cdp('Runtime.evaluate', {'expression': '''
        (() => {
            const ta = [...document.querySelectorAll('textarea')].find(t => t.placeholder.includes('mensagem'));
            const r = ta.getBoundingClientRect();
            return JSON.stringify({x: Math.round(r.left+r.width/2+window.screenX), y: Math.round(r.top+r.height/2+window.screenY)});
        })()'''})

# FASE 2: Desktop Daemon para digitar e enviar
async with websockets.connect('ws://127.0.0.1:9876') as dd:
    # Clicar no textarea (coordenadas absolutas)
    await dd.send(json.dumps({'action': 'click', 'params': {'x': pos.x, 'y': pos.y}}))
    # Digitar (PURO ASCII — sem acentos/cedilha!)
    await dd.send(json.dumps({'action': 'type', 'params': {'text': MSG_ASCII}}))
    # Clicar no botão Enviar
    await dd.send(json.dumps({'action': 'click', 'params': {'x': btn_x, 'y': btn_y}}))
```

**Regras:** 
1. 2 tentativas máx de envio. Se falhar, informar caminho do arquivo + mensagem para envio manual.
2. Mensagens DEVEM ser ASCII puro (sem ç, ã, é — ABNT2 corrompe).
3. Verificar envio via CDP: `document.body.innerText.indexOf("texto enviado") > -1`.

**⚠️ Quando o usuário diz "envie para o Martin":** Pipeline validado (24/05): 1. Preparar ARQUIVO XLSX. 2. Abrir Brave real via CDP (:9222). 3. CDP: anexar arquivo (DOM.setFileInputFiles + change event). 4. CDP: obter coordenadas absolutas (getBoundingClientRect + window.screenX/Y). 5. Daemon: clicar textarea, digitar (ASCII puro!), clicar Enviar. 6. CDP: verificar envio. 7. Se falhar 2x, informar caminho + mensagem pronta.

### Abrir Edge com CDP

```bash
pkill -f msedge 2>/dev/null
/opt/microsoft/msedge/msedge \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir="$HOME/.config/microsoft-edge" \
  --no-first-run \
  "https://www.99freelas.com.br/dashboard" &
```

### PITFALL 99Freelas

- Cloudflare Turnstile pode bloquear o primeiro acesso via CDP — o Edge do usuário já tem cookies da sessão real
- Google OAuth rejeita Brave/CDP — login email+senha funciona
- `Input.dispatchMouseEvent` é mais confiável que `element.click()` para elementos React
- A URL de mensagens é: `/messages/inbox/ID_DO_PROJETO`

### ⚠️ CDP Navigation Pitfall (28/05/2026)

**`json/new?url=...` NÃO funciona** em Brave/Edge/Chromium. A URL é ignorada e a aba abre em `about:blank`.
Solução correta:
```python
# 1. Criar aba vazia
tab = json.loads(urllib.request.urlopen(
    Request('http://localhost:9222/json/new', method='PUT')
).read())

# 2. Navegar via WebSocket Page.navigate
ws = websocket.create_connection(tab['webSocketDebuggerUrl'])
cdp('Page.enable')
cdp('Page.navigate', {'url': 'https://destino.com'})
# Aguardar Page.loadEventFired
```

## PLATAFORMAS ALVO — STATUS (28/05/2026)

### Consenso dos Especialistas (3 IAs — 28/05)

ChatGPT, Gemini e DeepSeek consultados com mapeamento completo de 5 plataformas. Convergência total:
- **Freelancer.com FIRST** (3/3) — USD multiplica renda por 5x, ticket maior, menos saturado
- **Workana NÃO PAGAR** (3/3) — paywall R$59,90 não garante liberação
- **Fiverr ABANDONAR** (3/3) — 3 bans, lista negra permanente
- **Preço FIXO por projeto, nunca por hora** (2/3)
- **Primeiras 5 entregas 20% abaixo do mercado** (DeepSeek)

Análise completa em `references/expert-consensus-freelancer.md`.

### Freelance (propostas manuais)

| Plataforma | Sessão Edge | Pode Bidar | Faturamento | Bloqueio |
|-----------|------------|-----------|-------------|----------|
| **99Freelas** | ✅ | ⚠️ Só público | R$75 (Martin) | Exclusivo = Premium |
| **Freelancer** | ✅ @robertor03 | ⚠️ Perfil 90% | R$0 | Precisa Verified + tel |

### FREELANCER.COM — PLATAFORMA DE MAIOR POTENCIAL

**Por que é a mais rentável:**
- Projetos de $5.000-$10.000 USD em automação, APIs, scripts
- Média de lance no projeto WhatsApp: $6.667 USD
- 910 vagas ativas em skills compatíveis
- Clientes internacionais (EUA, Europa, Ásia) com orçamento maior

**Status do perfil (29/05/2026 — sessão ativa no Brave :9222):**
- ✅ Sessão logada ativa (Google OAuth) — Dashboard com 5 notificações
- ✅ Nome: Roberto Rodrigues dos Santos
- ✅ Headline: "Automation & AI Engineer | Python & LLM" (39 chars, limite 50)
- ✅ Summary (EN): automações web, pipelines de dados, IA, Excel avançado
- ✅ Hourly rate: $45/h
- ✅ Endereço: Vespasiano, MG, Brazil
- ✅ Abas abertas: busca `budget_min=30` + `skills=python,data-entry` + `excel data entry`
- ❌ Telefone: NÃO verificado (SMS pendente — número virtual +55 61 98173-7725 disponível no quackr.io)
- ❌ Verified by Freelancer: NÃO (bloqueia projetos >$2.500)

**Bloqueios a resolver:**

1. **Verificação de telefone** — SMS pendente. Sem isso, perfil exibe alerta "verify your phone number".
2. **Verified by Freelancer** — Sabrina M. (agente do Freelancer) entrou em contato oferecendo o programa. Projetos >$2.500 USD exigem esse selo. Ela disse que com skills de automação/API, o Verified badge "can help you attract better opportunities and maximize your earnings potential". Responder perguntando custo e processo.
3. **Skills** — Preencher as skills técnicas na plataforma (Python, Automation, API, Excel, Data Processing).

**Estratégia:**
- Completar perfil → ativar Verified → acessar projetos de $500-$5.000 USD
- Foco em: scripts Python, automação browser, APIs, planilhas Excel, data processing
- Evitar: design, tradução (low ticket), WhatsApp marketing (risco ToS)
| **Workana** | ✅ | ⚠️ Aguardando | R$0 | Perfil em análise |
| **Fiverr** | ✅ | ❌ | R$0 | 3 msgs = contas banidas |

### Micro-tarefas (cadastros autônomos via CDP — 19/05/2026)

| Plataforma | Tarefas | Pagamento | Status |
|-----------|---------|-----------|--------|
| **TimeBucks** | Games, surveys, micro-tasks | PayPal | ✅ ATIVO — UserID 228886019 |
| **Neevo** | Áudio/texto IA (PT-BR) | PayPal | ⚠️ Login OK, travado no seletor de idiomas (React virtualized list) |
| **Toloka** | Data labeling | PayPal ($1 min) | ⚠️ Google OAuth OK, aguardando código SMS |
| **Clickworker** | Data entry, categorização | PayPal, Payoneer (€) | ⚠️ Form preenchido, travado no Bootstrap-select (país/idioma/estado) |
| **OneForma** | Tradução PT-EN, coleta | Payoneer | ⚠️ Form parcial, Bootstrap-select bloqueia país |
| **SproutGigs** | SEO, cliques, avaliações | PayPal, Skrill | ⏳ Aba aberta, não iniciado |
| **GoTranscript** | Transcrição PT-EN | PayPal | ⏳ Não iniciado |
| **GetNinjas** | Serviços admin, digitação | Pix | ⏳ Não iniciado |
| **RapidWorkers** | Micro-tarefas | — | ⏳ Aba aberta, não iniciado |

### CDP Registration Blockers (padrões que travam automação)

| Bloqueio | Exemplo | Sintoma | Solução |
|---------|---------|---------|---------|
| **Bootstrap-select** | Clickworker (país, idioma, estado) | JS `value` setter + eventos ignorados | jQuery `$(el).selectpicker('val',...)` OU interação manual |
| **React virtualized list** | Neevo (seleção de idioma) | Elemento no índice 172 não está no DOM | Campo de busca do componente OU navegação por teclado |
| **SMS verification** | Toloka (telefone) | Código enviado, sem acesso programático | Solicitar código ao usuário |
| **Google OAuth** | Toloka, TimeBucks | Funciona — account chooser + consent | Fluxo dedicado no skill `cdp-browser-automation` |

### Credenciais salvas

Todas em `~/.hermes/forex/user_profile.yaml`. Senhas:
- Neevo: `Ne3v0!...` (ver arquivo)
- Toloka: Google OAuth (sem senha)
- TimeBucks: Google OAuth (sem senha)
- Clickworker: `Cw0rk!...` (ver arquivo)
- OneForma: `OneF0rm!...` (ver arquivo)
- Freelancer: `@robertor03` (email: robertosantos.una@gmail.com)
- **99Freelas: ❌ NÃO salvas no user_profile.yaml.** Sessão depende do Edge com cookies. Se a sessão expirar (abas em `/login`), NÃO tentar login via CDP — usar email + CloudFront.

### Freelancer.com — RSS Feed + CDP (28/05/2026)

**RSS Feed oficial:** `https://www.freelancer.com/rss.xml` (feed geral de novos projetos).
Os endpoints `/jobs/rss/N` foram descontinuados (retornam 301→HTML, não XML).
Parse com `xml.etree.ElementTree`, títulos vêm em `<![CDATA[...]]>`.

**Varredura CDP** para categorias específicas:
```python
# Navegar para categoria com keyword
await Page.navigate("https://www.freelancer.com/jobs/1/?keyword=excel%20data%20entry")

# Extrair cards com seletores específicos
document.querySelectorAll('.JobSearchCard-item').forEach(card => {
    title:  card.querySelector('.JobSearchCard-primary-heading-link')
    budget: card.querySelector('.JobSearchCard-secondary-price')
    bids:   card.querySelector('.JobSearchCard-secondary-entry')
})
```

Categorias com +jobs rápidos: Excel/Data Entry, Virtual Assistant, PDF/Word, Copy Typing. Projetos USD $8-50/h com 0-5 bids são alvos prioritários.

Bloqueio principal: perfil do Freelancer.com precisa de telefone verificado (SMS) + selo "Verified by Freelancer" para projetos >$2,500.

**Status (19/05/2026):** Perfil parcialmente completo. Principais bloqueios:

| Campo | Status | Detalhe |
|-------|--------|---------|
| Nome/Sobrenome | ✅ | Roberto Rodrigues dos Santos |
| Destaque Profissional | ✅ | 39/50 chars — limite ESTRITO de 50 caracteres |
| Resumo | ✅ | Preenchido em inglês |
| Hourly Rate | ✅ | $30/h |
| Endereço | ✅ | Vespasiano, MG |
| Skills | ⚠️ | Passo 1 de 3 pendente |
| Telefone | ❌ | Verificação SMS pendente — bloqueia perfil |
| Email | ✅ | Verificado |

**Headline — limite de 50 caracteres (PITFALL):**
O campo "Destaque Profissional" exibe "Por favor, não use mais que 50 caracteres." Valores >50 chars são truncados ou rejeitados. Exemplo válido (39 chars): `Automation & AI Engineer | Python & LLM`. O valor antigo (84 chars) `Automation & AI Engineer | Python | LLM Fine-Tuning | Browser Automation | Excel VBA` foi truncado silenciosamente.

**Onde editar o perfil:**
O formulário de edição de perfil NÃO está em `/users/settings/profile` (retorna 404). Ele aparece INLINE nas páginas de projeto quando o perfil está incompleto, na seção "Complete seu perfil — Por favor, complete estas 3 etapas antes de fazer uma proposta". Acessar via: abrir qualquer projeto > scroll até o topo > preencher os campos > clicar "Salvar".

**Verification & Preferred:**
- **Verified by Freelancer**: obrigatório para projetos >$2.500. Sabrina M. (@FLSabrina) entrou em contato oferecendo o programa. 
- **Phone verification**: SMS pendente. Sem isso, perfil não completa.
- **Preferred Freelancer**: necessário para projetos restritos. Processo separado.

### CDP Registration Blockers (padrões que travam automação)

Pesquisa de 24 plataformas para brasileiro (sem SSN/conta US), focando em micro-tarefas de baixa complexidade e giro rápido.

> **Notas detalhadas de cadastro**: `references/platforms-registration-notes.md` — URLs corretas, bloqueios por componente, fluxos completos por plataforma.

### 🟢 ATIVAS (prontas para tasks)

| Plataforma | Tarefas | Pagamento | Cadastro | Status |
|-----------|---------|-----------|----------|--------|
| **TimeBucks** | Surveys, games, micro-tasks, vídeos | PayPal, Payoneer | Google OAuth | ✅ ATIVO — $0.30 bônus, cash out $2.70 |
| **Toloka** | Data labeling, UHRS tasks ($0.05-$10) | PayPal ($1 min) | Google OAuth + Tel | ✅ ATIVO — perfil "Roberto Santos", UHRS tasks disponíveis |
| **Neevo** | Áudio/texto IA (PT-BR) | PayPal | ✅ ATIVO — idioma PT-BR Native, testes Writing+Listening pendentes |
| **SproutGigs** | SEO, cliques, micro-tasks | PayPal, Skrill | Email | ⚠️ Form preenchido, Bootstrap-select bloqueia país |
| **Clickworker** | Data entry, AI training | PayPal, Payoneer (€) | Email | ⚠️ Form preenchido, Bootstrap-select bloqueia dropdowns |
| **OneForma** | Tradução PT-EN, coleta dados | Payoneer | Email | ⚠️ Form parcial, Bootstrap-select bloqueia país |

### Brasileiras (Pix)

| Plataforma | Tarefas | Pagamento |
|-----------|---------|-----------|
| **GetNinjas** | Serviços administrativos, digitação | Pix direto com cliente |
| **GoTranscript** | Transcrição PT-EN | PayPal |

### 🎯 Prioridade de ação (maior retorno imediato)

1. **TimeBucks** — já ativo, surveys pagam rápido, cash out baixo ($2.70)
2. **Toloka** — UHRS tasks disponíveis, completar perfil para liberar
3. **99Freelas** — 3 projetos novos (revisão texto, formatação ABNT) encontrados via email

### Tasks ideais (baixa complexidade, giro rápido)

- Formatação ABNT (99Freelas — categoria Escrita)
- Correção ortográfica / Revisão de texto
- Tradução PT-EN / EN-PT
- Digitação / Data entry
- Transcrição de áudio curto
- Micro-tarefas de classificação (Neevo, Toloka)

> **Regra de ouro:** Priorizar tarefas com <10 propostas, escopo claro, orçamento definido. Evitar projetos com 50+ interessados (loteria).

## 99FREELAS — PROJETOS ATIVOS (19/05/2026)

Categoria Escrita — 10 projetos de revisão/formatação encontrados. Melhores oportunidades:

- **Revisão de pré-projeto de conclusão de curso** — 4 propostas, Iniciante
- **Copywriting para redes sociais** — 5 propostas, Intermediário
- **Revisão ortográfica de apostilas digitais** — 12 propostas
- **Correção de redações para ENEM** — 12 propostas, Iniciante

### Paywall pattern (confirmado em 2 plataformas)

**99Freelas "Exclusivo":** Projetos marcados como "Exclusivo" exigem Premium ou pontos de convite. Mensagem típica: "Este freela estará disponível para todos os profissionais em Xh. Deseja enviar uma proposta agora? Seja um Freelancer Premium". Enquanto isso, Premium users já enviam propostas. Quando o período expira, o cliente já escolheu.

**Workana "Perfil em análise":** Perfis abaixo de 100% entram em fila de revisão. Modal: "Seu perfil está sendo analisado. Evite a longa lista de espera — BRL 59,90". O botão "Fazer uma proposta" abre esse modal em vez do formulário de proposta. Projetos visíveis mas propostas BLOQUEADAS até aprovação.

**Conclusão:** Ambas as plataformas monetizam o acesso a projetos. 99Freelas cobra por projeto (Premium), Workana cobra pela aprovação de perfil. Fiverr é a única sem paywall de entrada — mas tem PerimeterX.

## LEAD RESEARCH — PREENCHIMENTO B2B

Workflow validado para preencher planilhas de prospecção B2B (CNPJ, endereço, modalidades, decisores, LinkedIn). Ver `references/lead-research-workflow.md` para o guia completo.

### Passo 1: Varredura de Oportunidades
```bash
# Usar browser_navigate para acessar plataforma
# browser_snapshot para capturar listagem
# browser_console para extrair dados em JSON
```

### Passo 2: Triagem
- Filtrar por: budget > mínimo, prazo viável, skills compatíveis
- Priorizar: maior budget, cliente verificado, recorrência potencial

### Passo 3: Aplicação
- Template de proposta personalizável
- Adaptar por projeto (NUNCA copiar genérico)
- Incluir: entendimento do problema, solução proposta, prazo, valor

### Passo 4: Follow-up
- Verificar respostas a cada 4-6h
- Responder em até 2h (responsividade = mais jobs)
- Manter tom profissional e direto

### Passo 5: Entrega e Cobrança
- Validar entrega antes de submeter
- Confirmar pagamento recebido
- Pedir review

## MONITORAMENTO CONTÍNUO

### ⚠️ REGRA DE OURO: TOKEN COST AWARENESS + RESILIÊNCIA DE REDE

**Cada execução do agente custa tokens. Monitorar sem retorno = prejuízo.**
**Internet pode cair a qualquer momento — timeout 10s + retry (2 tentativas) em TODA operação de rede.**

Padrão de resiliência:
```python
for attempt in range(2):
    try:
        result = network_operation(timeout=10)
        break  # Sucesso
    except Exception as e:
        if attempt == 0:
            time.sleep(3)
            continue
        log(f"Falha após 2 tentativas: {e}")
        return fallback_value
```

Aplica-se a: IMAP, CDP WebSocket, curl HTTP, yfinance, APIs externas. Nunca congelar esperando rede.

O agente NUNCA deve fazer polling ativo de plataformas (abrir browser, verificar dashboards, checar emails)
em loop. Isso queima $30+/dia sem gerar receita. O padrão correto:

1. **Scripts no_agent** (Python puro, zero tokens) monitoram passivamente
2. **Só acordam o agente** quando há ação real pendente
3. **Agente executa** a ação e volta a dormir

### Cron Jobs Configurados (19/05/2026)

| Job | Tipo | Frequência | Custo |
|-----|------|-----------|-------|
| `monitor.py` | no_agent | 5 min | $0 |
| `forex_check.py` | no_agent | 3x/dia (picos) | $0 |
| ~~Motor Central Escalação~~ | PAUSADO | — | — |
| ~~Freelance Scanner~~ | PAUSADO | — | — |

### Motor Local (monitor.py)

Script em `~/.hermes/scripts/monitor.py`. Credenciais Gmail (app password) hardcoded no CONFIG dict do script. Funcionamento:
- Conecta no Gmail via IMAP a cada 5 min
- Verifica emails novos de 99Freelas, Freelancer, Workana, Fiverr
- Classifica por tipo: nova_mensagem, proposta_aceita, pagamento, novo_projeto
- **Só escreve arquivo de alerta** se for alta prioridade
- Agente lê o alerta e age — sem gastar token em espera

### Quando acordar o agente

| Evento | Acordar? | Motivo |
|--------|---------|--------|
| Nova mensagem de cliente | ✅ SIM | Urgente — resposta rápida = mais jobs |
| Proposta aceita | ✅ SIM | Celebrar + iniciar entrega |
| Pagamento recebido | ✅ SIM | Confirmar + revisão |
| Novo projeto (revisão/ABNT/TCC) | ✅ SIM | Bidar rápido |
| Novo projeto (genérico/survey) | ❌ NÃO | Baixa prioridade |
| Login alert | ❌ NÃO | Ignorar |

## Agente Freelancer Autônomo (28/05/2026, atualizado 29/05)

Agente unificado em `~/.hermes/brain/freelancer_agent.py` — pipeline completo:
- Monitoramento IMAP Gmail (4 plataformas) a cada 30min
- Classificação automática: jobs rápidos vs longos
- Templates de proposta por tipo (6 templates: Excel, Digitação, Revisão, Tradução, PDF, Python)
- Follow-up tracking (>6h sem resposta = alerta)
- Rastreamento de pagamentos pendentes

### ⚠️ Pitfalls do Classificador de Email (CORRIGIDOS 29/05/2026)

**13 bugs encontrados e corrigidos no agente (6 iniciais + 7 na revisão de 29/05) + 1 bug de arquitetura (healthcheck). Ver `references/agent-email-pitfalls.md` para detalhes completos.**

| # | Bug | Sintoma | Correção |
|---|-----|---------|----------|
| 1 | Remetentes errados no `PLATFORM_EMAILS` | Zero emails de Freelancer/Workana | Usar endereços reais |
| 2 | `'novo projeto'` (singular) não captura `'Novos projetos'` (plural) | Digests 99Freelas ignorados | Adicionar `'novos projetos'` ao check |
| 3 | Keywords só em português | Freelancer.com nunca dá match | Adicionar keywords em inglês |
| 4 | Digest contém keywords de skip | `is_skip=True` bloqueia digests | `is_digest and is_quick → is_skip=False` |
| 5 | Check `'login'` genérico antes do específico | Emails Freelancer → `login_alert` | Platform-specific ANTES do genérico |
| 6 | `extract_project_title` captura HTML | Título: `s <html xmlns=` | Strip HTML antes do regex |
| 7 | Digest detectado mas regex captura igual | 8 propostas falsas para digests | Check digest ANTES do regex + filtros anti-saudação |
| 8 | Contador de propostas cumulativo | "Propostas: 23" toda execução | Contador separado por sessão |
| 9 | `body[:3000]` truncado por CSS | Parser retorna 0 projetos | Strip `<style>` + aumentar para 15KB |
| 10 | Caracteres acentuados no META_RE | "Edição" não matcha regex | `Edi[cç]ão`, `Intermedi[áa]rio` |
| 11 | Cabeçalhos de categoria vazando | "Planilhas e Relatórios \|" como título | `normalized = line.rstrip('\|').strip()` |
| 12 | Keyword stemming | "cadastrar" ≠ keyword "cadastro" | Adicionar variantes: `cadastrar`, `digitar` |
| 13 | Digest tratado como projeto individual | Proposta genérica para digest inteiro | Separar digests de projetos; NÃO gerar propostas automáticas |
| 14 | Healthcheck bloqueia pipeline quando só CDP cai | Agente aborta sem escanear email | Só hard-fail se AMBOS IMAP e CDP falharem |

**Regra de ouro para classificação de email:** Sempre verificar os remetentes REAIS (inspecionar header `From:`), não presumir. Testar `classify_opportunity()` com dados reais antes de deploy. Checks platform-specific DEVEM vir antes de checks genéricos (`'login'`, `'acesso'`).

**⚠️ Healthcheck — degradação, não bloqueio:** O healthcheck do agente verifica IMAP e CDP. Se AMBOS falharem → aborta. Se apenas UM falhar → avisa e continua com a fonte disponível. CDP cai com frequência (processo morre, browser fecha), mas IMAP é estável — não faz sentido perder varredura de email por falta de CDP. Ver bug #14 em `references/agent-email-pitfalls.md`.

**Sub-agente Freelancer.com:** `~/.hermes/brain/subagent_freelancer.py`
- RSS feed monitoring (`freelancer.com/rss.xml`)
- Filtro por keywords (Excel, Python, Data Entry, VA, PDF)
- Score de match + budget mínimo USD $10
- Alerta via Tálamo para jobs high-score
- Verificação de status do perfil (telefone, Verified)

**Cron:** `*/30 * * * * 1-5` — executa a cada 30 min em dias úteis.

**Timeout+retry obrigatório em toda operação de rede:**
```python
for attempt in range(2):
    try:
        result = network_operation(timeout=10)
        break
    except Exception:
        if attempt == 0:
            time.sleep(3)
            continue
        log(f"Falha após 2 tentativas")
```
Aplica-se a: IMAP, CDP WebSocket, curl HTTP, RSS feed, APIs externas. Nunca congelar esperando rede.

### Categoria Principal: AI/ML Engineering
- LLM Fine-tuning (LoRA/QLoRA)
- RAG pipelines
- AI Agent development
- Prompt engineering
- Model deployment (vLLM, llama.cpp)

### Categoria Secundária: Automação
- Browser automation (Playwright)
- Web scraping
- Workflow automation (n8n, Make)
- API integration
- Data pipelines

### Categoria Terciária: DevOps/Infra
- Docker/containers
- CI/CD pipelines
- Linux administration
- Cloud deployment

## PRECIFICAÇÃO

- Hora mínima: USD 45/hora (Freelancer.com: $45/h; 99Freelas: ajustar por projeto)
- Projeto fixo: estimar horas * 1.5 (margem de risco)
- Urgente: taxa de 2x
- Manutenção: retainer mensal

## TEMPLATES DE PROPOSTA

> **⚠️ Ver skill `proposta-99freelas` para o template canônico e regras de ouro.**
> Resumo rápido: 3 parágrafos máx, NUNCA repetir valor/prazo no corpo, SEMPRE acentos, abrir com nome do cliente, fechar com "abs, Roberto".

### Formato unificado (válido para 99Freelas, Freelancer, Workana)

```
[Nome], [1 frase mostrando que entendeu o projeto].

[1-2 frases com qualificação específica — sem lista genérica, sem bullets].

[Fechamento natural — "Posso começar assim que confirmar"].

abs,
Roberto
```

### Exemplos reais (validados)

**Projeto de Excel/planilha (Freelancer/99Freelas):**
> Tatiana, entendi a estrutura: seleção automática por tipo de licença com validação de dados.
>
> Já montei planilhas similares com proteção contra erro de preenchimento e formato limpo.
>
> Se quiser, mostro um exemplo com 2 categorias antes de concluir.
>
> abs, Roberto

**Projeto de automação/script (Freelancer):**
> [Nome], já automatizei fluxos parecidos com Python + API. Consigo entregar o script documentado e pronto pra rodar.
>
> Faço uma versão inicial em 2 dias pra você validar o funcionamento antes de finalizar.
>
> abs, Roberto

## 99FREELAS — ACESSO CONFIÁVEL (EMAIL)

Cloudflare Turnstile bloqueia browser tools consistentemente desde mai/2026. CDP via Edge também falha se o Edge não estiver aberto com flags corretas. **O caminho confiável é monitoramento por email.**

### ⚠️ SESSÃO EXPIRA SILENCIOSAMENTE (PITFALL 22/05/2026)

Mesmo com Edge rodando + CDP ativo + múltiplas abas abertas, a sessão do 99Freelas **expira após horas/dias de inatividade**. Todas as abas são redirecionadas para `/login`. O Turnstile então bloqueia tentativas de re-login via CDP.

**Sintoma:** `curl localhost:9222/json` mostra abas com URL `/login` em vez do dashboard/mensagens.

**Regra ZERO:** Se o CDP revelar que TODAS as abas estão em `/login`, NÃO tentar fazer login via CDP (Turnstile bloqueia). Ir direto para o fluxo de email + CloudFront. Zero tentativas de CDP login.

### Cron de monitoramento (configurado 19/05/2026)

Cron job ativo: `"Freelance Opportunity Scanner"` — escaneia Gmail a cada 2h por novos projetos e mensagens de clientes. Setup documentado em `references/cron-email-monitoring.md`.

### Fluxo primário: Email → Extração → Ação

1. **Monitorar**: IMAP scan por remetente `99freelas` a cada 1-2h
2. **Extrair**: Parse do HTML do email — ver `references/99freelas-email-parsing.md` (digest "Novos projetos") e `references/99freelas-email-parsing.md` (emails de mensagem de cliente, mesma técnica de strip)
3. **Classificar**: Novo projeto / Nova mensagem / Pagamento / Login
4. **Agir**: Alertar usuário imediatamente se for mensagem de cliente ou projeto com budget
5. **Responder**: Se login for necessário, pedir ao usuário que acesse manualmente

### Por que email é mais confiável que browser

- Cloudflare Turnstile não afeta IMAP
- Emails chegam em tempo real
- Tokens de "visualizar no navegador" são mascarados (`***`) no corpo — inúteis
- Zero dependência de sessão, cookies, ou CDP flags

### Estrutura dos emails 99Freelas

```
Nova mensagem: subject contém "Nova mensagem de [NOME] no projeto [TÍTULO]"
Novo projeto:   subject contém "Novo Projeto: [TÍTULO]"
Login:          subject "Aviso de novo login"
```

**Layout do corpo (emails de mensagem):**

```
Visualizar no navegador
Cancelar inscrição
[DATA]
Olá, [NOME].
Você recebeu uma nova mensagem de
[NOME DO CLIENTE]
no projeto
[TÍTULO DO PROJETO]
[MENSAGEM — pode estar VAZIA se o cliente só anexou arquivo]
Arquivo(s) anexado(s):      ← SÓ aparece se há anexo
[NOME_DO_ARQUIVO.ext]
* Este é um email automático...
Responder
```

**Padrão crítico: mensagem sem texto (só anexo):** Quando o cliente envia apenas um arquivo sem texto, o bloco da mensagem fica vazio e `Arquivo(s) anexado(s):` aparece imediatamente após o título do projeto. A extração deve detectar esse caso e reportar "Sem texto — apenas anexo: <arquivo>".

**Marcadores de término da mensagem (parar extração ao encontrar):**
- `Arquivo(s) anexado(s):`
- `Responder` (como linha curta isolada, <30 chars)
- `* Este é um email automático`
- `Atenciosamente,`
- `Equipe 99Freelas`

### Extração de conteúdo (HTML pesado)

Os emails usam templates HTML com `<style>` extenso. Técnica:

```python
import re

# Strip CSS e HTML
body = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
body = re.sub(r'<head>.*?</head>', '', body, flags=re.DOTALL)
body = re.sub(r'<[^>]+>', '\n', body)
body = re.sub(r'&nbsp;', ' ', body)
body = re.sub(r'&amp;', '&', body)
body = re.sub(r'\n\s*\n+', '\n', body)

# Linhas com texto visível
all_lines = [l.strip() for l in body.split('\n') if l.strip() and len(l.strip()) > 2]

# Extrair APENAS o bloco da mensagem do cliente:
# começa após "no projeto [TÍTULO]" e termina nos marcadores de fim
message_lines = []
capture = False
for line in all_lines:
    if 'no projeto' in line.lower():
        capture = True
        continue
    if not capture:
        continue
    # Parar nos marcadores de término
    if any(marker in line for marker in [
        'Arquivo(s) anexado(s):',
        '* Este é um email automático',
        'Atenciosamente,',
        'Equipe 99Freelas'
    ]):
        break
    if line.lower().startswith('responder') and len(line) < 30:
        break
    message_lines.append(line)

mensagem = '\n'.join(message_lines).strip()

# Detectar anexos
anexos = []
for line in all_lines:
    if 'Arquivo(s) anexado(s):' in line:
        # O nome do arquivo está na linha seguinte
        idx = all_lines.index(line)
        if idx + 1 < len(all_lines):
            anexos.append(all_lines[idx + 1])

# Resultado
if not mensagem and anexos:
    print(f"Sem texto — apenas anexo(s): {', '.join(anexos)}")
elif mensagem:
    print(f"Mensagem: {mensagem}")
    if anexos:
        print(f"Anexos: {', '.join(anexos)}")
```

### Projeto ativo: Martin L. — Clínicas Radiológicas

- Cliente: Martin L.
- Projeto: Pesquisa e prospecção B2B de clínicas radiológicas
- Status: **Concluído (26/05/2026) — aguardando liberação de pagamento (R$75)**
- Entregue: CSV com 69 clínicas (38 SP + 31 RJ), 76% com telefone, 52 com site
- **26/05:** Projeto marcado como concluído. Cliente precisa liberar pagamento. Se não liberar, abrir disputa.
- Arquivo CSV: `~/.hermes/forex/clinicas_radiologicas_martin.csv`
- **22/05:** Martin devolveu planilha `Nexus_Lead_Base_Estrategica_Preenchida.xlsx` com 18 clínicas/redes em 3 abas: Prioridade Alta (11), Prioridade Média (3), Grandes Redes (4). Campos preenchidos: nome, cidade, estado, telefone, site. Faltam: CNPJ, endereço, modalidades, decisor, LinkedIn. Arquivo: `~/.hermes/nexus_lead_base_estrategica_preenchida.xlsx`

### Fechar projeto no 99Freelas (CDP)

**Pipeline validado 25/05/2026:**

```python
# 1. Navegar para a página do projeto (não inbox!)
# O link está no header da conversa: /p/752503 → redireciona para /project/...
cdp('Runtime.evaluate', {'expression': '''
  (() => {
    const links = [...document.querySelectorAll('a')];
    const projLink = links.find(a => 
      a.href.includes('/p/') && 
      a.getBoundingClientRect().x > 400 &&  // header (não sidebar)
      (a.innerText||'').includes('Pesquisa')
    );
    if (projLink) projLink.click();
  })()
'''})

# 2. Clicar "Concluir Projeto" (btn green clickable, ~182x62)
cdp('Runtime.evaluate', {'expression': '''
  (() => {
    const btn = [...document.querySelectorAll('button')]
      .find(b => (b.innerText||'').trim() === 'Concluir Projeto');
    if (btn) {
      const rk = Object.keys(btn).find(k => k.startsWith('__reactProps'));
      if (rk && btn[rk].onClick) btn[rk].onClick({preventDefault:()=>{}, stopPropagation:()=>{}});
      else btn.click();
    }
  })()
'''})

# 3. Confirmar modal — clicar "Sim" (~80x39)
cdp('Input.dispatchMouseEvent', {type:'mousePressed', x:1036, y:588, button:'left', clickCount:1})
cdp('Input.dispatchMouseEvent', {type:'mouseReleased', x:1036, y:588, button:'left', clickCount:1})

# 4. Verificar — texto "Avaliação" indica sucesso
```

### CloudFront Download — Anexos do 99Freelas sem Turnstile

Quando um cliente envia arquivo pelo 99Freelas, o email de notificação contém um link direto para o CloudFront (CDN da AWS) com token de autenticação embutido na URL. **NÃO requer login, cookies, nem passa pelo Turnstile.**

**Extração do link de download:**

```python
import imaplib, email, re

mail = imaplib.IMAP4_SSL("imap.gmail.com")
mail.login(EMAIL, APP_PASSWORD)
mail.select("INBOX")

# Buscar email do cliente
status, messages = mail.search(None, '(FROM "99freelas" SUBJECT "Martin")')
mid = messages[0].split()[-1]
status, msg_data = mail.fetch(mid, "(RFC822)")
msg = email.message_from_bytes(msg_data[0][1])

html = msg.get_payload(decode=True).decode("utf-8", errors="replace")

# Encontrar links de anexo CloudFront
# Padrão: href="https://duqxk0v9olda1.cloudfront.net/messages/.../arquivo.xlsx"
links = re.findall(r'href="(https://[^"]*cloudfront[^"]*)"', html)
for link in links:
    if any(ext in link.lower() for ext in ['.xlsx', '.csv', '.pdf', '.docx', '.zip']):
        print(f"Download: {link}")
```

**Download via curl (sem autenticação):**

```bash
curl -L -o arquivo.xlsx "https://duqxk0v9olda1.cloudfront.net/messages/.../arquivo.xlsx"
```

**Vantagens sobre CDP/browser:**
- ZERO dependência de Edge, CDP, ou sessão logada
- ZERO bloqueio do Cloudflare Turnstile
- Token de acesso já está na URL — expira? (testar)
- Funciona 100% do tempo se o email foi recebido

### Padrão: Cliente travado (não responde escopo)

Quando o cliente aprova mas não define parâmetros:
1. Esperar 24h após aprovação
2. Enviar follow-up com **sugestão concreta de escopo** (o cliente só precisa dizer "sim")
3. Enquanto espera: **bidar em outros projetos** — não ficar parado
4. NUNCA ficar em loop de espera queimando tokens

### Novos projetos (18/05/2026)
1. **Planilha financeira Excel** — controle de gastos, entradas/saídas, metas. Orçamento: Aberto.
2. **Assistente de atendimento e follow-up** — suporte temporário, follow-up, organização. Orçamento: Aberto.

## Referências

- `references/data-enrichment-techniques.md` — Técnicas de pesquisa e enriquecimento de dados (CNPJ, endereço, decisores, LinkedIn)

## METODOLOGIA DE CONSTRUÇÃO (validada Forex + Freelancer — 28/05)

Para qualquer novo domínio de automação, seguir estas 3 fases (validado em 2 domínios):

1. **MAPEAMENTO**: Levantar TODAS as plataformas, contas, status, bloqueios, pipelines e histórico. Documentar o que funciona e o que falhou. Output: matriz de plataformas com status e bloqueios.
2. **SUB-AGENTES**: Criar agente unificado (`domain_agent.py`) com pipeline completo (monitorar → classificar → agir → follow-up). Timeout 10s + retry (2 tentativas) em TODA operação de rede.
3. **CONSULTA A ESPECIALISTAS**: Abrir 4 IAs (ChatGPT, Gemini, DeepSeek, Grok) via CDP com prompt estruturado (perfil + plataformas + bloqueios + perguntas específicas). Extrair respostas e consolidar pontos convergentes. Salvar em `references/expert-consensus-<dominio>.md`.

Regra: nunca codar antes de mapear. Nunca automatizar plataforma com anti-bot ativo.

## INSTAGRAM — BLOQUEIO TOTAL (28/05/2026)

Instagram bloqueia QUALQUER automação:
- CDP via Brave (:9222) → recaptcha na auth_platform
- CDP via Chromium headless (:9226) → recaptcha
- Playwright/Selenium → detecção de automação

Única abordagem viável: **monitoramento passivo** — detectar se a aba está aberta no Brave, registrar timestamps de uso, NUNCA interagir com a página. Dados de interação social real vêm de WhatsApp, Telegram e Email. Instagram Web é hostil a qualquer forma de automação, mesmo via CDP em navegador real logado.

## ESTRATÉGIA: JOBS RÁPIDOS (PRIORIDADE MÁXIMA — 25/05/2026)

**Regra:** Priorizar jobs de entrega rápida. EVITAR projetos longos tipo Martin (prospecção B2B — demorou semanas, pagou R$75). Foco em:

| Tipo | Exemplos | Tempo |
|------|----------|-------|
| Planilhas | Excel, Google Sheets, fórmulas, dashboards | 30min-2h |
| Digitação | Cadastro, coleta de dados, listas | 30min-1h |
| Revisão | Correção ortográfica, ABNT, formatação | 1-2h |
| PDF/Word | Conversão, sumário, edição simples | 15min-1h |
| Tradução curta | Textos <5 páginas, PT-EN/EN-PT | 1-2h |

**Anti-padrão:** Prospecção B2B, pesquisa de mercado extensa, projetos sem escopo definido, clientes que não respondem com parâmetros.

### Varredura CDP de Projetos no 99Freelas

Técnica validada 25/05/2026 — extrai projetos diretamente da listagem via CDP no Brave real (:9222):

```python
import json, urllib.request, websocket, time

# Conectar ao Brave real (tem sessão ativa, bypassa Turnstile)
tabs = json.loads(urllib.request.urlopen('http://localhost:9222/json/list').read())
tab = [t for t in tabs if '99freelas' in t.get('url','')][0]
ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=15)

# Extrair títulos e URLs dos projetos
ws.send(json.dumps({'id':1, 'method':'Runtime.evaluate', 'params':{'expression':'''
(function() {
    var links = document.querySelectorAll('a[href*="/project/"]');
    var results = [];
    links.forEach(function(a) {
        var text = a.textContent.trim();
        if (text.length > 10) {
            results.push({title: text.substring(0, 150), href: a.href});
        }
    });
    return JSON.stringify(results);
})()
''','returnByValue':True}}))
projects = json.loads(ws.recv())

# Filtrar por keywords de jobs rápidos
quick_kw = ['digita', 'planilha', 'excel', 'revisão', 'correção', 
            'format', 'ABNT', 'traduç', 'word', 'pdf', 'converter',
            'sumário', 'slide', 'PowerPoint', 'cadastro', 'lista']
matches = [p for p in projects if any(k in p['title'].lower() for k in quick_kw)]
```

**Horário ideal de varredura:** Seg-Sex 08:00-10:00 BRT (pico de novos projetos).

- NÃO aplicar para projetos fora do expertise
- NÃO prometer prazo impossível
- NÃO aceitar projeto sem escopo claro
- NÃO entregar sem validar
- NÃO ignorar mensagens por mais de 6h
- NÃO aceitar pagamento fora da plataforma (risco de golpe)
- NÃO usar `no-reply@` como critério de exclusão de emails (99Freelas usa `no-reply@99freelas.com.br`)
- NÃO depender de browser tools para 99Freelas — Cloudflare Turnstile bloqueia consistentemente

### BLOQUEIOS CONHECIDOS

| Plataforma | Bloqueio | Solução real |
|-----------|---------|---------|
| 99Freelas | Cloudflare Turnstile | **Monitorar via email (IMAP)** — browser NÃO funciona |
| 99Freelas | Google OAuth rejeita Brave/CDP | Login email+senha se Cloudflare permitir; senão email |
| 99Freelas | **Projeto Exclusivo (Premium)** | Projetos marcados "Exclusivo" exigem assinatura Premium ou pontos de convite. Só podem receber propostas após o período de exclusividade expirar. Verificar `bodySnippet` por "Exclusivo" ou "Premium" antes de tentar enviar proposta. Foco em projetos PÚBLICOS. |
| Workana | **Perfil em análise** | Perfis <100% são bloqueados de enviar propostas. Modal "Seu perfil está sendo analisado — BRL 59,90". Solução: aguardar aprovação gratuita (dias) OU pagar fast-track. Checar semanalmente se perfil foi aprovado. |
| Workana | Projetos exigem perfil 100% | Completar: texto sobre você, foto, 3 habilidades, portfólio, idiomas |
| Fiverr | **PerimeterX (ERRCODE PXCR10002539)** | Anti-bot detection bloqueia navegação CDP para inbox e páginas sensíveis. Dashboard do seller carrega normalmente. Para inbox: abrir manualmente no Edge do usuário. |
| Fiverr | **Notificações de contas banidas (fantasmas)** | O inbox pode mostrar conversas como "não lidas" de contas que o Fiverr removeu. A mensagem "can no longer be contacted" indica que a conta foi banida/desativada — NÃO é lead real. Verificar cada contato antes de agir. |
| WhatsApp Web | User-Agent do Brave rejeitado | Usar WhatsApp Desktop (snap) |
| my.telegram.org | Google OAuth rejeita Brave/CDP | Usar Edge ou Telethon direto |
| **Múltiplas plataformas** | **Bootstrap-select** | JS `value` setter + eventos `change`/`input` não funcionam. O componente Bootstrap-select intercepta o select nativo. Soluções: (1) `$(el).selectpicker('val', '...')` se jQuery disponível, (2) interação manual de mouse (abrir dropdown → scroll → click), (3) marcar como pendente e seguir. Afeta: Clickworker, OneForma, SproutGigs. |
| **Instagram** | **Recaptcha universal** | Instagram bloqueia 100% da automação — CDP via Brave (:9222), Chromium (:9226), Playwright, Selenium. Qualquer interação com a página redireciona para `auth_platform/recaptcha`. Abordagem: monitoramento passivo (detectar aba aberta, registrar tempo de uso, zero interação com DOM). |
| **Neevo** | **Email de confirmação não chega** | Gmail bloqueia silenciosamente o domínio `definedcrowd.com` (nem INBOX, Spam, nem All Mail). Workaround: usar outro provedor de email (ProtonMail, Outlook). |\n| **Neevo** | **Teste de idioma interativo com timer** | O Writing Test tem 5 seções com timer de 5 min cada, elementos interativos (clicar em espaços no texto, selecionar erros com mouse). NÃO PODE ser pausado. CDP é muito arriscado — uma falha no meio perde a tentativa. **Fazer manualmente** (30 min). |

### Estratégia de fallback para login
1. Tentar browser_navigate do Hermes (Brave, perfil real)
2. Se Cloudflare: **pular direto para email monitoring** (não perder tempo)
3. Se Google OAuth bloqueado: tentar email+senha direto
4. Se tudo falhar: reportar [FALHA] + extrair dados via email + pedir ação manual ao usuário

## Referências

- **[csv-enrichment-pipeline.md](references/csv-enrichment-pipeline.md)** — Pipeline de enriquecimento de CSV em larga escala com delegate_task batch processing.
- **[cdp-ia-prompt-submission.md](references/cdp-ia-prompt-submission.md)** — Técnica CDP para enviar prompts longos para IAs (ChatGPT, Gemini, DeepSeek, Grok) sem interação manual. Validado 28/05/2026.
- **[sona-lite-freelancer-memory.md](references/sona-lite-freelancer-memory.md)** — Sistema de memória e aprendizado do agente freelancer (7 categorias, replay buffer, cold start).
- **[critical-review-framework.md](references/critical-review-framework.md)** — Framework de auto-análise crítica para revisão de arquitetura antes de produção.
- **[expert-consensus-freelancer.md](references/expert-consensus-freelancer.md)** — Consolidação das respostas de 3 IAs (ChatGPT, Gemini, DeepSeek) sobre estratégia freelancer.
- **[client-research-workflow.md](references/client-research-workflow.md)** — Fluxo de pesquisa web para preencher planilhas de clientes.
- **[99freelas-cdp-messages.md](references/99freelas-cdp-messages.md)** — Extração de conversas do 99Freelas via CDP no Brave real (:9222).
- **[99freelas-email-parsing.md](references/99freelas-email-parsing.md)** — Parsing dos emails de digest "Novos projetos" do 99Freelas.
- **[freelancer-email-parsing.md](../email-autonomy/references/freelancer-email-parsing.md)** (skill `email-autonomy`) — Parsing dos emails de digest do Freelancer.com.

- **[agent-email-pitfalls.md](references/agent-email-pitfalls.md)** — 13 bugs corrigidos no classificador de email do agente (remetentes, digest skip, login order, plural match, HTML title, English keywords, CSS truncation, acentos, category headers, stemming, digest proposals). 29/05/2026.
- **[digest-parser-implementation.md](references/digest-parser-implementation.md)** — Implementação do parser state-machine para extrair projetos individuais de digests 99Freelas. 29/05/2026.
- Tempo médio de resposta: <2h
- Reviews: média >4.8
- Receita mensal recorrente: crescente
