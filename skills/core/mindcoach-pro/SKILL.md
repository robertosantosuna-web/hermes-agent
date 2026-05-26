---
name: mindcoach-pro
description: "MindCoach Pro — PWA orgânica controlada remotamente pelo Hermes Agent via WebSocket. App é casca viva que recebe JSON e renderiza. 7 pilares (financeiro, saúde, mental, social, produtividade, técnico, espiritual). Hot-reload via Service Worker. Dados offline-first (IndexedDB). Docker-ready."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [mindcoach, pwa, websocket, app, dashboard, life-os]
    related_skills: [life-os, dashboard, desktop-control]
---

# MindCoach Pro

App PWA (Progressive Web App) que funciona como **bolha viva** — o Hermes Agent controla
100% da interface remotamente via WebSocket. O app é uma casca que renderiza JSON,
sem lógica própria de decisão.

## UI: Dock Bar (v29+)

Balões flutuantes foram substituídos por **dock bar fixa no rodapé** (3 ícones):
- 🔐 **Auth** — autorizações pendentes (badge vermelho com contador)
- 📊 **Painel** — dashboard com dados neurais
- 💬 **Chat** — chat bidirecional com a ENTIDADE

O dock sobe junto quando chat ou auth são abertos (`transform: translateY(-60dvh)`).
CSS com `safe-area-inset-bottom` para respeitar notch e gesture bar.

### Auth API

Endpoint REST no Cloud Run (`/api/auth` e `/api/notify`):
- `GET /api/auth` — lista solicitações pendentes
- `POST /api/auth` — cria solicitação (agente → app)
- `POST /api/auth/{id}/respond` — responde (app → agente)

### Notificações Push (v33+)

Endpoint `/api/notify` no Cloud Run — o agente pode enviar notificações diretamente para o app:
- `GET /api/notify?since=N` — poll de notificações (app faz a cada 30s)
- `POST /api/notify` — enviar notificação `{"titulo":"...", "msg":"...", "tipo":"info|warn"}`

Script helper: `~/.hermes/scripts/notify_app.py`
```bash
python3 ~/.hermes/scripts/notify_app.py "Título" "Mensagem" [info|warn]
```

O frontend faz polling a cada 30s. Notificações aparecem como alerta no dock bar.

### Cache e Atualização

**Problema**: PWA instala e nunca atualiza (SW cache antigo). Requer limpeza manual de cache.
**Solução v36 (definitiva)**:
- **Force reload sem busy-check**: SW novo → `controllerchange` + `statechange` → `window.location.reload()` SEM verificar se chat/auth abertos. O usuário não precisa mais limpar cache manualmente.
- **Cache-bust nos imports**: `<script type="module" src="/core/main.js?v=36">` e `/sw.js?v=7` — cada deploy incrementa.
- **SW_VERSION** em `sw.js` incrementado a cada deploy. CACHE usa `mindcoach-v${SW_VERSION}`.
- **`skipWaiting()` + `self.clients.claim()`** no activate — SW assume controle imediatamente, sem esperar tabs fecharem.
- **SW network-first** com cache dinâmico (popula só depois de servido, nunca no install).
- Indicador de versão no topo (`v36`) — 3 toques = reset total.

### Bridge: Chat — Agente responde (não Ollama)

**Fluxo (v29+):**
1. Usuário envia mensagem no app → WebSocket → bridge
2. Bridge salva em `mindcoach_chat_inbox.json` + envia "📨 Recebido! Estou processando..."
3. Bridge marca `pending_chat: true` no `gateway_checkpoint.json`
4. **O agente (DeepSeek/Claude) responde** com qualidade total, NÃO o Ollama
5. Agente usa `respond_chat.py` ou comando `chat_response` no bridge

**Script para responder:**
```bash
python3 ~/.hermes/scripts/respond_chat.py "Mensagem de resposta"
```
Envia via WebSocket (bridge :9877) + REST (Cloud Run) dual-channel.

**⚠️ Nunca deixar o Ollama responder.** Se o bridge responder automaticamente com qualidade baixa, o fluxo está quebrado. O bridge só envia "📨 Recebido!" e acorda o agente.

### Deploy Cloud Run

```bash
cd ~/.hermes/mindcoach-pro
gcloud run deploy mindcoach --source . --region us-central1 --allow-unauthenticated
```
URL: `https://mindcoach-541659260074.us-central1.run.app`

## Arquitetura

```
Hermes Agent
    │
    ├── mindcoach_control.py  (CLI de comandos)
    │
    ▼
mindcoach_bridge.py  (WS :9877, systemd)
    │
    ├── App clients  (main.js → WS)
    └── SW clients   (sw.js → WS)
         │
         ▼
    MindCoach Pro  (HTTP :9878)
    ├── index.html
    ├── core/main.js       (renderizador JSON→DOM)
    ├── core/websocket.js   (conexão viva)
    ├── core/renderer.js    (utilidades de UI)
    ├── store/localDB.js    (IndexedDB)
    ├── sw.js              (Service Worker, hot-reload)
    └── manifest.json      (PWA)
```

## Serviços

| Serviço | Porta | systemd |
|---------|-------|---------|
| Bridge WS | 9877 | `mindcoach-bridge.service` |
| HTTP | 9878 | `mindcoach-http.service` |
| Data Sync | cron */5 | `adf627711438` (no_agent) |

## Comandos do Hermes → App

Via `python3 ~/.hermes/scripts/mindcoach_control.py <comando> [args]`:

| Comando | Args | Efeito |
|---------|------|--------|
| `render` | `dashboard\|pilar\|analysis\|goals\|chat` | Troca a tela |
| `update_pilar` | `<nome> '<json>'` | Atualiza dados de um pilar |
| `alerta` | `"<titulo>" "<msg>" [warn\|info]` | Push de alerta |
| `theme` | `'{"accent":"#cor","bg":"#cor"}'` | Muda cores |
| `bubble` | `<emoji> [true\|false] ["texto"]` | Atualiza bolha flutuante |
| `chat` | `'[{mensagens}]'` | Coach IA — envia mensagens pro chat do app |

### Chat: formato das mensagens
```json
[{"role": "hermes", "texto": "Como você está?"}, {"role": "voce", "texto": "Bem!"}]
```

### Chat: recebendo mensagens do celular
Mensagens enviadas do app caem em `~/.hermes/mindcoach_chat_inbox.json`:
```json
[{"texto": "Olá", "timestamp": 1716667200000, "lido": false}]
```
Ler inbox: `python3 -c "import json; msgs=json.load(open('$HOME/.hermes/mindcoach_chat_inbox.json')); [print(m['texto']) for m in msgs if not m['lido']]"`

## Atualização Remota (Hot-Reload)

O Service Worker (`sw.js`) mantém WebSocket aberto mesmo com app fechado.
Hermes envia `update_app` → SW faz cache dos novos arquivos → notifica clientes → reload.

```bash
python3 mindcoach_control.py update_app v2
```

## Integrador de Dados

`mindcoach_integrator.py` — puxa dados reais (forex, MT5, cérebro) e envia ao app.
Roda via cron `*/5 * * * *` (no_agent).

Fontes:
- MT5: `hermes_mt5_bridge.py status` → saldo, equity, posições
- Backtest: `forex/crt_choch_backtest.json` → WR, PnL, trades
- Cérebro: `forex/brain_context.json` → módulos ativos, descobertas

## Deploy

### Local
```bash
systemctl --user enable --now mindcoach-bridge.service
systemctl --user enable --now mindcoach-http.service
# App em http://<IP>:9878 (bind 0.0.0.0)
```

### Cloud Run
```bash
cd ~/.hermes/mindcoach-pro
gcloud run deploy mindcoach --source . --region us-central1 --allow-unauthenticated --quiet
```
Após deploy, verificar: `curl -s https://mindcoach-541659260074.us-central1.run.app/ | grep data-version`

## Referências

- `references/chat-debugging.md` — Diagnóstico quando chat do celular não chega ao inbox
- `references/gateway-checkpoint.md` — Recuperação de contexto pós-queda do gateway
- `references/deploy-checklist.md` — Checklist completo de deploy (v36+)

## Arquivos

- `~/.hermes/mindcoach-pro/` — app fonte
- `~/.hermes/scripts/mindcoach_bridge.py` — servidor WebSocket (:9877, processa chat_message → inbox + marca pending_chat)
- `~/.hermes/scripts/mindcoach_control.py` — CLI de comandos
- `~/.hermes/scripts/respond_chat.py` — agente envia resposta de chat (WS + REST dual-channel)
- `~/.hermes/scripts/notify_app.py` — envia notificações push para o app via POST /api/notify
- `~/.hermes/scripts/auth_request.py` — agente envia solicitação de autorização (POST /api/auth)
- `~/.hermes/scripts/mindcoach_server.py` — servidor HTTP (bind 0.0.0.0:9878)
- `~/.hermes/scripts/mindcoach_integrator.py` — sync de dados
- `~/.hermes/mindcoach_state.json` — estado persistido
- `~/.hermes/mindcoach_chat_inbox.json` — mensagens recebidas do celular
- `~/.hermes/mindcoach_chat_history.json` — histórico de chat persistente (bridge)
- `~/.hermes/mindcoach-pro/data.json` — dados da rede neural (build_data.sh)
- `~/.hermes/gateway_checkpoint.json` — estado de sessão (carregado ao iniciar, bridge marca pending_chat)

## Pitfalls

- **PWA não atualiza após deploy (RESOLVIDO v36)**: SW com `skipWaiting()` + `controllerchange` força reload automático SEM busy-check. Sempre incrementar `SW_VERSION` em `sw.js` e `?v=N` nos imports (`/sw.js?v=N`, `/core/main.js?v=N`). Bump também o `data-version` no `index.html`.
- **Telas vazias (conflito renderização)**: `index.html` inline script e `main.js` (ES module) renderizam no mesmo DOM. `main.js` deve usar `document.getElementById('main-screen')`, NUNCA `document.getElementById('app')`. O inline script não deve chamar `loadNeuralData()` se `main.js` estiver presente (`document.querySelector('script[src*="main.js"]')`).
- **Bridge sobrescreve dashboard rico com estado vazio**: O bridge envia `render` com `current_state` (pilares vazios). Se `/data.json` já carregou e populou `neuralData`, NÃO chamar `renderScreen()` — manter `renderNeuralDashboard()`. Prioridade: `data_cache` → `renderNeuralDashboard()`, senão → `renderScreen()`.
- **Bridge envia estado salvo de sessão anterior**: `mindcoach_state.json` guarda `screen` e `pilar` da última sessão. Ao receber nova conexão WebSocket, resetar para `screen: 'dashboard', pilar: 'dashboard'` ANTES de enviar o estado inicial.
- **IndexedDB race condition**: `cacheSet()` chama `getStore()` que lança exceção SÍNCRONA se `db` não inicializado. O `.catch(()=>{})` na promise NÃO captura throws síncronos. SEMPRE envolver `cacheSet()` em `try { ... } catch(e) {}` no `main.js`.
- **populateDashboard() vs renderNeuralDashboard()**: `populateDashboard()` existe no script INLINE do index.html, NÃO no módulo `main.js`. O módulo usa `renderNeuralDashboard()`. Nunca chamar `populateDashboard()` de dentro do `main.js`.
- **togglePanel() quebrado com main.js presente**: `togglePanel()` chamava `loadNeuralData()` inline, que está desativado quando `main.js` existe. Solução: disparar `window.dispatchEvent(new CustomEvent('reload-dashboard'))` e adicionar listener no `main.js` que faz `fetch('/data.json')` + `renderNeuralDashboard()`.
- **Dados somem offline**: `main.js` deve salvar `data_cache` e `chat_history` no IndexedDB (`cacheSet(...)`) ao receber via WebSocket. No init, carregar do IndexedDB como fallback se `/data.json` falhar.
- **Brave cache**: Ao testar via CDP (:9222), usar `?v=N` na URL para bypassar cache do navegador.
- **sendChat precisa ser global**: Função `sendChat()` deve estar em `<script>` normal (não `type="module"`) para onclick funcionar.
- **Dock e painéis**: Sempre abrir/fechar dock junto com painéis (`dock.classList.add('dock-up')`). Fechar o outro painel ao abrir um novo.
- **Chat REST API**: path `/chat_api/chat`. Nginx proxy de `/chat_api/` → `:8081` e `/api/` → `:8081`.
- **Notificações**: path `/api/notify`. Dados em `/tmp/mindcoach_notify.json` (Cloud Run, volátil). Script helper: `~/.hermes/scripts/notify_app.py`.
- **Auth API**: path `/api/auth`. Dados em `/tmp/mindcoach_auth.json` (Cloud Run, volátil).
