---
name: mindcoach-app
description: "MindCoach Pro PWA — desenvolvimento, debugging, deploy e manutenção. Cobre Cloud Run, WebSocket bridge, Service Worker, IndexedDB offline-first, chat, notificações, e bugs comuns com soluções validadas."
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [mindcoach, pwa, cloud-run, websocket, offline, debugging]
    related_skills: [browser-automation, life-os]
---

# MindCoach Pro App

App PWA multi-plataforma (Cloud Run + desktop local). Exibe dados da rede neural (forex, pilares, backtests, alertas), chat bidirecional com o agente, e painel de autorizações. Deploy público: `mindcoach-541659260074.us-central1.run.app`.

## ARQUITETURA

```
[index.html] ←→ [core/main.js] ←→ [core/websocket.js] → cloudflare tunnel → mindcoach_bridge.py (:9877)
     ↕ REST /api/* (nginx :8080 → chat_api.py :8081)
[chat_api.py] — Python HTTP server (chat, auth, calendar, notify endpoints)
[Dockerfile] — python:3.11-slim + nginx + google-auth deps
[data.json] — dados da rede neural (build_data.sh)
[sw.js] — Service Worker network-first + auto-reload
[store/localDB.js] — IndexedDB (pilares, métricas, cache, chat_history)
```

### Arquivos principais

| Arquivo | Função |
|---|---|
| `index.html` | PWA shell, dock bar, panels (chat/auth/calendar), inline functions |
| `core/main.js` | Renderização, WebSocket, IndexedDB, dados neurais, polling notify |
| `core/websocket.js` | Conexão WebSocket com o bridge |
| `store/localDB.js` | IndexedDB — `cacheSet/get`, `getLatest`, `getStore` |
| `chat_api.py` | REST API (:8081) — `/chat`, `/auth`, `/notify`, `/calendar` |
| `sw.js` | Service Worker v8 — network-first, auto-reload sem busy check |
| `nginx.conf` | Proxy `/api/` → :8081, serve estáticos |
| `Dockerfile` | python:3.11-slim + nginx + google-api-python-client |
| `build_data.sh` | Gera `data.json` dos dados locais da rede neural |
| `scripts/mindcoach_bridge.py` | WebSocket bridge Hermes ↔ App (:9877) |
| `scripts/notify_app.py` | Envia notificações para o app via REST |

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

## BUGS COMUNS E SOLUÇÕES

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

**Diffs exatos:** Ver `references/calendar-painel-fixes-v38-v39.md`.

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

## ENDPOINTS REST (chat_api.py :8081)

### `/api/chat` (GET/POST)
- GET: `?since=N` → mensagens desde ID
- POST: `{"from": "user", "text": "..."}` → salva e opcionalmente forward Telegram

### `/api/auth` (GET/POST)
- GET: lista pendentes
- POST: criar `{"titulo", "msg", "actions"}`
- POST `/api/auth/ID/respond`: `{"action": "approved"|"rejected"}`

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

# Recarregar dados do bridge
python3 ~/.hermes/scripts/mindcoach_bridge.py  # send_command via thread

# Verificar status do bridge
curl http://localhost:9877/
```

## VERSÕES RECENTES

- v33: Chat "✓" ack + Docker base fix (Alpine→python:3.11-slim)
- v34: Dockerfile google deps
- v35: Objetos unificados corrigidos
- v36: **SW v7 + cache-bust + force reload sem busy check**
- v37: **Bridge não sobrescreve + Painel recarrega + IndexedDB try/catch**
- v38: **Calendar panel: 5 correções classList/style.display (Bug #8)**
- v39: **main.js dockPainel.onclick adiciona togglePanel() antes de cyclePilar() (Bug #9)**
