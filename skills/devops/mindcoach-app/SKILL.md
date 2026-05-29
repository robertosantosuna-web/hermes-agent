---
name: mindcoach-app
description: "MindCoach Pro — app Android (WebView) + PWA fallback. REST-first, single-file HTML, Cloud Run, sistema de comandos neurais, OTA, chat_api.py. Cliente PRIMÁRIO: APK Android. UI iterável via browser."
version: 2.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [mindcoach, android, cloud-run, rest-api, ota, neural-interface]
    related_skills: [browser-automation, life-os]
---

# MindCoach Pro App

App PWA multi-plataforma (Cloud Run + desktop local). Exibe dados da rede neural (forex, pilares, backtests, alertas), chat bidirecional com o agente, e painel de autorizações. Deploy público: `mindcoach-541659260074.us-central1.run.app`.

## ARQUITETURA (v40 — REST-first, single-file HTML)

**A partir da v40 (26/05), o app migrou para arquitetura REST-first com um único `index.html` autocontido.** Os arquivos `core/main.js`, `core/websocket.js`, e `store/localDB.js` são LEGACY e não são mais usados. Toda a UI, lógica de polling, e renderização está inline no `index.html`.

```
[APK Android] → WebView → https://mindcoach-...run.app/index.html
     │                              │
     │ (Kotlin mínimo: OTA + WebView)│ (Toda UI no index.html)
     ▼                              ▼
[Cloud Run] ← nginx → chat_api.py → /tmp/mindcoach_*.json
                              ↓
                    /chat, /auth, /outbox, /notify, /calendar (REST)
```

### Arquivos principais (v40+)

| Arquivo | Função |
|---|---|
| `index.html` | **ÚNICO arquivo de UI** — Canvas neural, synapse stream, chat, comandos, polling REST. Autocontido (CSS + JS inline). |
| `chat_api.py` | REST API (:8081) — `/chat`, `/auth`, `/outbox`, `/notify`, `/calendar` |
| `nginx.conf` | Proxy `/auth`, `/outbox`, `/chat`, `/notify`, `/calendar` → :8081 |
| `sw.js` | Service Worker (cache + auto-reload) |
| `data.json` | Dados neurais estáticos (build_data.sh) |
| `Dockerfile` | python:3.11-slim + nginx |
| `mindcoach.apk` | APK servido para OTA |
| `scripts/mindcoach_commands.py` | Bridge: Hermes envia impulsos/lee respostas do app |
| `scripts/mindcoach_bridge.py` | LEGACY — WebSocket bridge (não usado pelo APK v40) |
| `core/main.js` | LEGACY — substituído pelo inline JS no index.html |
| `store/localDB.js` | LEGACY — IndexedDB (não usado na v40) |

## DEPLOY

```bash
cd ~/.hermes/mindcoach-pro
bash build_data.sh                    # reconstrói data.json
gcloud run deploy mindcoach \
  --source=. --region=us-central1 \
  --allow-unauthenticated --memory=512Mi \
  --project=gen-lang-client-0455851315
```

**Sempre antes do deploy:**
1. Bump `SW_VERSION` em `sw.js`
2. Atualizar `?v=N` em `index.html` (sw.js e main.js) + `id="app-version"`
3. Rodar `build_data.sh` para data.json fresco
4. Verificar que `data.json` tem as chaves esperadas (forex, pilares, tech_status)

## BUGS COMUNS (v39 LEGACY — multi-file architecture)

⚠️ **Os bugs 1-10 abaixo são da arquitetura v39 (multi-file: main.js + websocket.js + localDB.js).** Na v40 (single-file index.html REST-first), esses bugs não se aplicam mais. Mantidos como referência histórica.

### 1. Dashboard vazio / "Modo offline — conectando ao Hermes..."

**Causa:** O `fetch('/data.json')` completa mas `renderNeuralDashboard()` nunca é chamado porque `cacheSet()` no `.then()` lança exceção síncrona (`getStore` → `throw 'DB not initialized'`) antes do IndexedDB inicializar. A exceção cai no `.catch()`.

**Solução:** Envolver `cacheSet` em `try/catch`:
```js
fetch('/data.json', { cache: 'no-cache' })
  .then(d => { 
    neuralData = d;
    try { cacheSet('neural_data', d).catch(()=>{}); } catch(e) {}
    if (!currentState || !isOnline) renderNeuralDashboard();
  })
  .catch(e => console.log('[MAIN] Sem data.json:', e.message));
```

### 2. Bridge sobrescreve dashboard rico com estado vazio

**Causa:** WebSocket conecta → bridge envia `render` com `current_state` (pilares padrão vazios) → `renderScreen('dashboard', data)` sobrescreve o dashboard neural que `/data.json` já populou.

**Solução:** No `onMessage` handler, só renderizar tela se bridge enviou `data_cache` OU se não temos dados neurais ainda:
```js
case 'render':
  // processar data_cache, chat_history...
  if (data.data_cache || !neuralData || Object.keys(neuralData).length === 0) {
    renderScreen(data.screen, data);
  }
  break;
```

### 3. IndexedDB `getStore()` lança exceção síncrona

**Causa:** `getStore()` faz `if (!db) throw new Error(...)` — síncrono, quebra promise chains.

**Solução:** SEMPRE `try/catch` ao chamar funções do localDB antes da DB inicializar:
```js
try { cacheSet('key', data).catch(()=>{}); } catch(e) {}
```

### 4. Service Worker cache bloqueia JS novo

**Causa:** SW_VERSION parado, sem cache-bust nos imports, busy-check bloqueava reload.

**Solução:**
- Bump `SW_VERSION` a cada deploy
- Cache-bust: `<script src="/core/main.js?v=37">` e `register('/sw.js?v=8')`
- SW `activate`: `skipWaiting()` + `clients.claim()` + postMessage reload
- NO "busy" check — sempre recarregar (`controllerchange` + `refreshing` flag)

### 5. Conflito de renderização inline vs main.js

**Causa:** `index.html` inline script renderiza em `#main-screen`. `main.js` (módulo ES) sobrescrevia `#app` inteiro, destruindo `#main-screen`.

**Solução:**
- main.js renderiza em `document.getElementById('main-screen')` (não `#app`)
- inline script NÃO chama `loadNeuralData()` no init se `main.js` presente
- Botão Painel dispara `CustomEvent('reload-dashboard')` que main.js escuta

### 6. Botão 📊 Painel não carrega dados

**Causa:** `togglePanel()` chamava `loadNeuralData()` inline que está desativado quando main.js presente.

**Solução:** Botão Painel dispara `CustomEvent('reload-dashboard')` → main.js faz `fetch('/data.json')` + `renderNeuralDashboard()`.

### 7. Chat messages lost on deploy

**Causa:** `/tmp/mindcoach_chat.json` é efêmero no Cloud Run. Histórico reseta a cada deploy.

**Mitigação:** Bridge local (`mindcoach_bridge.py`) salva `chat_history` em `~/.hermes/mindcoach_chat_history.json` e envia ao app ao conectar.

### 8. Calendar panel trava após toggle rápido (v37→v38)

**Causa:** O Calendar usa **dois mecanismos** de controle: `classList.toggle('open')` E `style.display = 'flex'/'none'`. As funções `togglePanel()`, `toggleChat()`, e `toggleAuth()` setavam apenas `style.display = 'none'` sem remover a classe `'open'`. Na próxima chamada de `toggleCalendar()`, o `classList.toggle('open')` removia a classe (achando que estava aberto) mas o `style.display` continuava `'none'` → painel invisível mas classe ausente → estado dessincronizado.

**Locais afetados (5 pontos em `index.html`):**
1. `togglePanel()` linha 387 — só `style.display='none'`
2. `toggleChat()` linha 312 — só `style.display='none'`
3. `toggleChat()` linha 317 — verificava `style.display !== 'flex'`
4. `toggleAuth()` linha 368 — só `style.display='none'`
5. `toggleAuth()` linha 373 — verificava `style.display !== 'flex'`

**Solução:** Em todos os 5 pontos, adicionar `classList.remove('open')` junto com `style.display='none'` e trocar verificações para `classList.contains('open')`. Regra permanente: **NUNCA usar style.display e classList juntos para o mesmo controle de estado.**

**Diffs exatos:** Ver `references/calendar-painel-fixes-v38-v39.md` e `references/agenda-multi-fonte.md`.

### 9. Painel não fecha painéis (v38→v39)

**Causa:** `main.js` linha 129 sobrescreve `dockPainel.onclick` com uma arrow function que chama `cyclePilar()` para navegação entre pilares, mas **não chama `togglePanel()`**. O HTML inline tem `onclick="togglePanel()"` mas esse handler é substituído pelo main.js.

**Solução:** Adicionar `togglePanel()` como primeira linha do handler:
```js
dockPainel.onclick = () => {
  togglePanel(); // Fecha todos os painéis (Calendar, Chat, Auth)
  const next = cyclePilar();
  ...
};
```

**Pitfall:** SEMPRE verificar `element.onclick` no console do browser para confirmar qual handler está realmente ativo. O atributo HTML `onclick="..."` pode ser substituído silenciosamente por JavaScript.

### 10. Pilar detail view sobrescrito pelo bridge

**Causa:** Quando o usuário clica em um pilar na nav (`setupPilarNav()`), `renderPilar()` mostra a tela de detalhe. Mas o bridge continua enviando `render` com `screen: 'dashboard'`, que chama `renderDashboard()` e sobrescreve a tela de detalhe.

**Mitigação atual:** Nenhuma. O bridge não respeita `activePilar`. Para resolver seria necessário o bridge verificar o estado atual do app antes de enviar render.

**Workaround:** O pilar detail view existe e funciona (`renderPilar` mostra cards com key-value pairs do pilar selecionado), mas só persiste até o próximo push do bridge.

## DOCK BAR

4 botões fixos no rodapé, cada um toggle um panel. **ATENÇÃO**: `main.js:129` SOBRESCREVE `dockPainel.onclick` com `cyclePilar()`. O HTML tem `onclick="togglePanel()"` mas o handler real é o do main.js. Qualquer mudança no comportamento do Painel deve ser feita no main.js, não no HTML.

| Botão | Função | Panel | Handler real |
|---|---|---|---|
| 🔐 Auth | `toggleAuth()` | `#auth-panel` | HTML inline (não sobrescrito) |
| 📊 Painel | `togglePanel()` + `cyclePilar()` | fecha todos + navega pilar | `main.js:129` SOBRESCREVE |
| 💬 Chat | `toggleChat()` | `#chat-panel` | HTML inline (não sobrescrito) |
| 📅 Compromissos | `toggleCalendar()` | `#calendar-panel` | HTML inline (não sobrescrito) |

**Regras de consistência (TODOS os panels):**
1. Usar **SOMENTE** `classList.toggle('open')` para controle de estado. CSS: `.panel.open { display: flex; }`
2. NUNCA misturar `style.display` com `classList` — causa dessincronização (ver Bug #8)
3. Se precisar usar `style.display` (legado), SEMPRE fazer BOTH: `style.display = 'none'` **E** `classList.remove('open')`
4. Verificar estado com `classList.contains('open')`, NUNCA com `style.display !== 'flex'`
5. Abrir um panel fecha os outros (remove 'open' E seta display:none)
6. `dock-up` só remove quando NENHUM panel tem classe 'open'
7. Painel (`main.js:129`) chama `togglePanel()` ANTES de `cyclePilar()` (adicionado na v39)

## PERSONALIZATION RULES (CRITICAL)

**NUNCA inventar nomes de familiares, filhas, ou pessoas próximas ao Roberto.** Usar apenas dados confirmados:
- "2 filhas" (sem nomes — nunca "Eduarda e Sophia", "Heloisa e Isadora" ou qualquer outro nome)
- "mora com pai e irmã em Vespasiano-MG"
- "Igreja CURA Church"

Placeholders genéricos são melhores que invenções. Se não souber um dado, usar descrições genéricas (ex: "suas filhas", "sua família"). Esta regra se aplica tanto ao backend (entidade_bridge.py, chat_api.py) quanto ao app Android (MindCoachRepository.kt, MindCoachScreen.kt).

## ⚠️ CLIENTE PRIMÁRIO: ANDROID APK (NÃO web PWA)

**O APK Android é o cliente PRIMÁRIO do Roberto.** O web PWA (index.html no Cloud Run) é um fallback/backup, NÃO o destino principal de desenvolvimento de UI. **Sempre priorizar mudanças no APK Kotlin/Compose.** Quando o usuário pedir melhorias no "app", ele se refere ao APK instalado no celular Android dele, não ao site web.

## ANDROID APP (Kotlin + Compose) — CLIENTE PRIMÁRIO

App Android nativo em `/home/roberto/Downloads/mindcoach (1)/`. Conectado à ENTIDADE via REST API no Cloud Run.

### Arquitetura
```
[App Android (Kotlin/Compose)]
    │ Retrofit + OkHttp
    ▼
[Cloud Run /api/v1/*]
    │ nginx → chat_api.py :8081
    ▼
[ENTIDADE (cron 1min)]
    │ entidade_bridge.py — GET inbox → POST response
    ▼
[App Android] ← polling GET /api/v1/chat?since=N
```

### Arquivos-chave
| Arquivo | Função |
|---|---|
| `EntidadeApi.kt` | Interface Retrofit para a API neural |
| `MindCoachRepository.kt` | Lógica de chat, eventos, polling, fallback offline |
| `MindCoachScreen.kt` | UI Compose — estados, cards, chat, banner OTA |
| `MindCoachViewModel.kt` | Estado: chat, eventos, OTA, estados orgânicos |
| `OtaManager.kt` | Download e instalação de APK via DownloadManager |
| `AndroidManifest.xml` | Permissões: INTERNET, REQUEST_INSTALL_PACKAGES, FileProvider |

### Compilação
```bash
cd "/home/roberto/Downloads/mindcoach (1)"
export ANDROID_HOME=/home/roberto/android-sdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
echo "GEMINI_API_KEY=*** > .env  # exigido pelo plugin secrets
./gradlew assembleDebug
# APK em: app/build/outputs/apk/debug/app-debug.apk
```

### Estados orgânicos (cores)
- `OPERANDO_FOREX` → Dourado (#F59E0B) — "IC Markets · 6 pares · Bot ativo"
- `ESCALA_GOL` → Laranja GOL (#E87700) — "Téc CMM Lagoa Santa · R$3.671 · Jul/2026"
- `TEMPO_FAMILIA` → Verde (#10B981) — "2 filhas · CURA Church · Vespasiano-MG"
- `CONEXAO_TERAPIA` → Roxo (#8B5CF6) — "Telavita · Check-in 10h · Calistenia 11h"

### Ícones (material-icons-core apenas)
Star, Place, FavoriteBorder, AccountCircle, Refresh, Send (AutoMirrored)

## OTA SYSTEM

Atualização Over-The-Air real. App verifica versão ao iniciar, baixa APK e instala.

### Fluxo
1. App chama `GET /api/v1/ota` → `{"version": 4, "apk_url": "...", "changelog": "..."}`
2. Se `version > CURRENT_VERSION`, mostra banner "Atualização disponível"
3. Usuário clica BAIXAR → DownloadManager baixa → FileProvider instala

### Componentes
- `OtaManager.kt` — `checkForUpdate()` (HTTP), `downloadAndInstall()` (DownloadManager + BroadcastReceiver)
- `AndroidManifest.xml` — `<provider>` FileProvider + `REQUEST_INSTALL_PACKAGES`
- `res/xml/file_paths.xml` — `<external-files-path name="downloads" path="Download/" />`
- `chat_api.py` — `GET /api/v1/ota` endpoint
- `mindcoach.apk` — servido estaticamente pelo nginx no Cloud Run

### Atualizar versão
```bash
# 1. Compilar APK
cd "/home/roberto/Downloads/mindcoach (1)"
./gradlew assembleDebug

# 2. Copiar para servir no Cloud Run
cp app/build/outputs/apk/debug/app-debug.apk /home/roberto/.hermes/mindcoach-pro/mindcoach.apk

# 3. Incrementar versão no chat_api.py (endpoint /api/v1/ota)
# 4. Deploy
cd ~/.hermes/mindcoach-pro && gcloud run deploy mindcoach --source . --region us-central1 --allow-unauthenticated --quiet
```

## ENTIDADE BRIDGE (entidade_bridge.py)

Script Python que faz a ponte ENTIDADE ↔ Cloud Run via HTTP (não mais WebSocket/arquivos locais).

### Funcionamento
1. `GET /api/v1/chat?since=N` — busca mensagens pendentes
2. Para cada mensagem de usuário, gera resposta contextual
3. `POST /api/v1/chat` com `from=coach` — envia resposta

### Cron
```
Job: entidade-inbox-processor (970a8181cbd2)
Schedule: */1 * * * * (a cada 1 minuto)
Action: python3 /home/roberto/.hermes/mindcoach-pro/entidade_bridge.py
Skills: life-os, identidade-entidade
```

### Respostas por contexto
- "status" → Dashboard (Forex, GOL, ecossistema)
- "forex" → Sinais, pares, estratégias
- "gol" → Carta Proposta, cargo, salário, transição
- "família" → Filhas, CURA Church, Vespasiano-MG
- "terapia" → Telavita, check-in, calistenia
- "ajuda" → Lista de comandos

## AGENDA SCAN — Varredura Multicanal

Fluxo para atualizar compromissos no app a partir de todas as fontes:

### Fontes
| Fonte | Acesso | Conta |
|-------|--------|-------|
| Gmail pessoal | IMAP direto (`imaplib`) | robertosantos.una@gmail.com |
| Outlook trabalho | Edge CDP :9222 | robrsantos@voegol.com.br |
| Outlook pessoal | Edge CDP :9222 | robertosantos141@outlook.com |
| WhatsApp | Edge CDP :9224 | `scripts/whatsapp_bridge.py` |

### Pipeline
1. **Coleta:** 3 subagentes em paralelo varrem cada fonte desde a última varredura
2. **Compilação:** Unificar em `mindcoach-pro/data/agenda_scan.json` com campos: date, time, type, title, description, source, priority
3. **Notificação:** `python3 scripts/notify_app.py "📅 Agenda Atualizada" "N compromissos encontrados" info`
4. **Deploy:** `bash build_data.sh && gcloud run deploy` (se dados neurais também mudaram)

### Keywords de busca
Português: reunião, consulta, médico, terapia, voo, escala, compromisso, agendamento, prazo, entrevista, igreja, evento, calendário, confirmado, agendado, cirurgia, atestado
Inglês: meeting, appointment, deadline, interview, flight, schedule, training

### Estrutura do agenda_scan.json
```json
{
  "last_scan": "ISO timestamp",
  "sources": ["gmail_pessoal", "outlook_trabalho", "whatsapp"],
  "commitments": [{ "date", "time", "type", "title", "description", "source", "priority" }],
  "pending_actions": [{ "action", "source", "priority" }],
  "recurring": [{ "type", "title", "schedule" }]
}
```

### `/api/chat` (GET/POST)
- GET: `?since=N` → mensagens desde ID
- POST: `{"from": "user", "text": "..."}` → salva e opcionalmente forward Telegram

### `/api/auth` (GET/POST)
- GET: lista pendentes
- POST: criar `{"titulo", "msg", "actions"}`
- POST com `{"type":"command_response", "id": "req_0001", "action": "approve"|"reject"}` — responde a comando neural
- POST `/api/auth/ID/respond`: `{"action": "approved"|"rejected"}` (legacy)

### `/api/outbox` (GET)
- GET: respostas de comandos (`?since=N` opcional). A ENTIDADE lê para saber o que foi aprovado/recusado.

### `/api/notify` (GET/POST)
- GET: `?since=N` → notificações não lidas
- POST: `{"titulo", "msg", "tipo", "actions"}` → cria notificação
- App faz polling a cada 30s; notificações aparecem no dock bar

### `/api/calendar` (GET)
- Eventos Google Calendar (7 dias). Requer token OAuth via `GOOGLE_TOKEN_B64`.

## PWA / MOBILE

- Manifest: `manifest.json` (nome, ícones 192+512, standalone, theme_color #0a0a1a)
- Service Worker: network-first + auto-reload + push notifications
- Funciona offline após primeiro carregamento (IndexedDB cache)
- Instalável: "Adicionar à tela inicial" no Chrome mobile

## SCRIPTS AUXILIARES

```bash
# Enviar notificação para o app
python3 ~/.hermes/scripts/notify_app.py "Título" "Mensagem" [info|warn]

# Enviar impulso neural (comando para aprovação)
python3 ~/.hermes/scripts/mindcoach_commands.py send "Título" "Descrição detalhada"

# Ver respostas do usuário a comandos
python3 ~/.hermes/scripts/mindcoach_commands.py check

# Recarregar dados do bridge
python3 ~/.hermes/scripts/mindcoach_bridge.py  # send_command via thread

# Verificar status do bridge
curl http://localhost:9877/
```

## SISTEMA DE COMANDOS NEURAIS (26/05/2026)

Fluxo completo de aprovação bidirecional:

```
Hermes Agent → mindcoach_commands.py send → POST /auth (Cloud Run)
    ↓
App Android (polling 10s) → GET /auth → NeuralCommandDialog
    ↓
Roberto aprova/rejeita → POST /auth {type:"command_response", id, action}
    ↓
Cloud Run escreve em /tmp/mindcoach_outbox.json
    ↓
Hermes Agent → mindcoach_commands.py check → GET /outbox → lê resposta
```

### Componentes
| Componente | Função |
|---|---|
| `scripts/mindcoach_commands.py` | Bridge: Hermes envia comandos e lê respostas |
| `chat_api.py` (POST /auth) | Aceita `{type:"command_response", id, action}` |
| `chat_api.py` (GET /outbox) | ENTIDADE lê respostas aprovadas/recusadas |
| `EntidadeApi.kt` | Retrofit: `getPendingCommands()`, `respondToCommand()` |
| `MindCoachRepository.kt` | `getPendingCommands()`, `respondToCommand(id, approve)` |
| `MindCoachViewModel.kt` | `pendingCommands` StateFlow, polling 10s, `respondToCommand()` |
| `MindCoachScreen.kt` | `NeuralCommandDialog` — modal com glow, aprovar/rejeitar |

### Pitfall: Atualizar APK, não web PWA
**⚠️ O cliente primário é o APK Android.** Quando o usuário pede mudanças no "app", altere os arquivos Kotlin em `/home/roberto/Downloads/mindcoach (1)/` e recompile. O web PWA no Cloud Run é fallback.

## VERSÕES RECENTES

- v33-v39: Ver histórico completo no skill
- v40 (26/05): **APK migrado para WebView** — `MindCoachScreen.kt` agora é um wrapper WebView que carrega `https://mindcoach-...run.app`. Uma base de código web (index.html) serve tanto o PWA quanto o APK. Mudanças na UI são feitas no HTML/CSS/JS do Cloud Run e aparecem instantaneamente no APK sem recompilar.
- v40 (26/05): **Sistema de Comandos Neurais** — `/auth` agora aceita `{type:"command_response", id, action}`, `/outbox` para leitura de respostas, `mindcoach_commands.py` bridge.
- v40 (26/05): **Neural Link Interface** — índice neural com Canvas de partículas, Brain Core pulsante, synapse stream, NeuralCommandDialog modal.

## ⚠️ PITFALL CRÍTICO: NUNCA desenhar UI Compose às cegas

**Lição (26/05):** Tentar iterar visual de Kotlin Compose sem emulador/dispositivo = perda de tempo.
Usuário rejeitou 3 versões: "Visualize antes de enviar", "Está uma merda", "Não parece rede neural".

**Regra:** Toda UI visível mora no `index.html` do Cloud Run. Iterável no browser.
O APK Kotlin é um wrapper WebView puro:

```kotlin
// MindCoachScreen.kt — 5 linhas
AndroidView(factory = { ctx ->
    WebView(ctx).apply {
        settings.javaScriptEnabled = true
        loadUrl("https://mindcoach-...app")
    }
})
```

**Fluxo correto:** Editar HTML → Abrir no browser (browser_navigate + snapshot) → ver visual → fazer deploy.

## SISTEMA DE COMANDOS NEURAIS (26/05/2026)

Fluxo Hermes → Usuário (aprovação de ações):

```
Hermes → mindcoach_commands.py send → POST /auth → Cloud Run
  → APK poll a cada 10s → GET /auth → mostra diálogo modal
  → Usuário aprova/rejeita → POST /auth {type:'command_response'} → /outbox
  → Hermes lê → mindcoach_commands.py check → GET /outbox
```

### Enviar impulso (Hermes)
```bash
python3 scripts/mindcoach_commands.py send "Título" "Mensagem detalhada"
python3 scripts/mindcoach_commands.py check   # ver respostas
python3 scripts/mindcoach_commands.py notify "Título" "Msg" info  # notificação simples
```

### Endpoints envolvidos
| Endpoint | Método | Função |
|----------|--------|--------|
| `/auth` | GET | Lista comandos pendentes (`{requests: [...], total: N}`) |
| `/auth` | POST | Criar comando (`{titulo, msg, from}`) OU responder (`{type:"command_response", id, action}`) |
| `/outbox` | GET | Respostas do usuário (`{responses: [{id, action, time}]}`) |

O diálogo de comando no APK mostra: título, mensagem, botão ✓ APROVAR (roxo) e ✕ RECUSAR (vermelho).

```
[APK Android] → WebView → https://mindcoach-...run.app/index.html
     │                              │
     │ (Kotlin só gerencia)          │ (Toda UI em HTML/CSS/JS)
     │ • OTA updates                 │ • Canvas neural background
     │ • WebView config              │ • Synapse stream
     │ • Manifest permissions        │ • Command dialog
     │                              │ • Chat, Calendar, Auth
     ▼                              ▼
[Cloud Run] ← nginx → chat_api.py → /tmp/mindcoach_*.json
```

### Arquivos Kotlin (mínimo)
| Arquivo | Função |
|---|---|
| `MindCoachScreen.kt` | WebView wrapper (5 linhas) |
| `MindCoachViewModel.kt` | Estado + polling de comandos |
| `MindCoachRepository.kt` | REST endpoints (chat, auth, commands) |
| `EntidadeApi.kt` | Interface Retrofit + DTOs |

### Arquivos Web (iteráveis visualmente)
| Arquivo | Função |
|---|---|
| `index.html` | Shell neural completa (Canvas, synapse stream, comandos, chat, dock) |
| `chat_api.py` | REST API: `/chat`, `/auth`, `/outbox`, `/notify`, `/calendar` |
| `nginx.conf` | Proxy rotas → chat_api.py, serve estáticos |
| `sw.js` | Service Worker (cache + auto-reload) |
