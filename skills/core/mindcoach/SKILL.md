---
name: mindcoach
description: "MindCoach Pro — App Android nativo + PWA Cloud Run. Chat com a ENTIDADE, 6 pilares, Córtex Dual, OTA. Conexão neural via REST API. Deploy Cloud Run + compilação Android."
version: 2.0.0
---

# MindCoach — Motor de Monitoramento Permanente

Sistema de consciência contínua que monitora 6 dimensões da vida do usuário, calcula scores, detecta tendências e alerta sobre declínios. Totalmente integrado à Rede Neural (NN-Engine).

## Arquitetura

```
Fontes (email, forex, Telegram, WhatsApp, Huawei Watch)
       ↓
Coletores (mindcoach_collectors.py, mindcoach_health_collector.py)
       ↓
Dimensões (6 scores 0-1 com pesos)
       ↓
NN-Sinapses (6 neurônios MindCoach conectados aos domínios)
       ↓
Dashboard (relatório texto + state.json)
```

## Dimensões

| Dimensão | Peso | Fontes | Threshold Alerta |
|----------|------|--------|-----------------|
| 🧠 Psicológico | 1.0 | Email tone, message patterns, night activity | <0.2 |
| 💙 Emocional | 1.0 | Sentiment analysis, stress markers | <0.2 |
| 👥 Social | 0.8 | Contact frequency, isolation index | <0.3 |
| 💰 Financeiro | 1.2 | Forex P&L, freelas, banking alerts | <0.3 |
| ⚡ Comportamental | 1.0 | Anti-patterns, task completion | <0.3 |
| 🫀 Saúde | 0.9 | Sono, água, passos, HR, SpO2, humor | <0.2 |

## Scripts

| Script | Função | Cron |
|--------|--------|------|
| `mindcoach.py` | Checkpoint (coleta + scores + NN sync + relatório) | A cada 30 min |
| `mindcoach_collectors.py` | Coleta de dados brutos (email, forex, social) | A cada 15 min (no_agent) |
| `mindcoach_health_collector.py` | Coleta saúde (Google Fit API + input manual) | A cada 15 min (no_agent) |

## Comandos

```bash
# Checkpoint completo (coleta + scores + sync NN)
python3 ~/.hermes/scripts/mindcoach.py checkpoint

# Relatório texto
python3 ~/.hermes/scripts/mindcoach.py report

# Status resumido
python3 ~/.hermes/scripts/mindcoach.py status

# JSON cru
python3 ~/.hermes/scripts/mindcoach.py json

# Input manual de saúde
python3 ~/.hermes/scripts/mindcoach_health_collector.py parse "sono 7h hr 68 passos 9200 agua 2"
```

## Saúde — Integração Multi-Fonte

Dados de saúde vêm de **4 fontes**, processadas por `mindcoach_health_collector.py`:

| Fonte | Método | Custo |
|-------|--------|-------|
| Google Fit API | OAuth REST (robertosantos.una@gmail.com) | Grátis (100k req/dia) |
| Gmail IMAP | Scan de emails por keywords de saúde | Grátis |
| WhatsApp | Scan de mensagens por keywords de saúde | Grátis |
| Telegram manual | Parse de input do usuário | Grátis |

**Pipeline:**
```
Google Fit ────┐
Gmail IMAP ────┤
WhatsApp ──────┤→ mindcoach_health_collector.py collect (15 min, no_agent)
Telegram ──────┘         ↓
                   health_data.json
                          ↓
                   mindcoach.py checkpoint → 🫀 Score
```

**Scanner de Email (saúde):** Keywords PT+EN em subjects de emails recentes (24h via IMAP):
- Senders: huawei health, google fit, samsung health, strava, gympass, smartfit, myfitnesspal
- Keywords: sono, passos, batimentos, peso, exercício, treino, sleep, steps, heart rate, workout

**Scanner de WhatsApp:** Keywords em `~/.hermes/whatsapp/messages.json` e `~/.hermes/data/social_whatsapp_chats.json`.

### Auditoria de Email (MindCoach)

Para auditar emails recentes em busca de dados de saúde e outros sinais:
```python
import imaplib, email, json
from email.header import decode_header
from datetime import datetime, timedelta
from collections import defaultdict

mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
mail.login("robertosantos.una@gmail.com", APP_PASSWORD)
mail.select("INBOX")

since = (datetime.now() - timedelta(hours=72)).strftime("%d-%b-%Y")
status, ids = mail.search(None, f'(SINCE "{since}")')

categories = defaultdict(list)
for eid in ids[0].split()[-100:]:  # últimos 100
    status, data = mail.fetch(eid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
    # ... classificar por categoria (freelas, financeiro, saúde, segurança, etc.)
```

Ver skill `email-autonomy` para o pipeline completo de IMAP, classificação e triagem.

## Rede Neural

6 neurônios MindCoach conectados à NN:
- `mindcoach_psychological` ↔ `mental_health`
- `mindcoach_emotional` ↔ `mental_health`
- `mindcoach_social` ↔ `communication`
- `mindcoach_financial` ↔ `forex_trading`
- `mindcoach_behavioral` ↔ `error_handling`
- `mindcoach_health` ↔ `system_health`

Cada checkpoint faz `learn` na NN com o overall score e trend.

## Cron Jobs

| Job ID | Nome | Frequência |
|--------|------|-----------|
| `79e9907ebf8c` | MindCoach Checkpoint | A cada 30 min (hora cheia + 30) |
| `ab9b27edb892` | MindCoach Data Collect | A cada 15 min (no_agent) |
| `e6797578cb16` | MindCoach Health Collect | A cada 15 min (no_agent) |

## Arquivos de estado

| Arquivo | Conteúdo |
|---------|----------|
| `~/.hermes/mindcoach/state.json` | Estado completo (scores, checkpoints, alerts, trend) |
| `~/.hermes/mindcoach/health_data.json` | Dados de saúde do dia (Wearable/Manual) |
| `~/.hermes/mindcoach/manual_inputs.json` | Inputs manuais de saúde por data |

## Score da Saúde (fórmula)

```
sleep_score = sleep_hours / 7
water_score = water_liters / 2.5
steps_score = steps / 8000
mood_score = mood / 10
spo2_penalty = 1.0 if spo2 >= 95 else 0.5

health = (sleep*0.3 + water*0.2 + steps*0.25 + mood*0.25) * spo2_penalty
```


## APP ANDROID NATIVO (Kotlin + Compose)

App nativo conectado à ENTIDADE via REST API. Substitui Gemini API.

### Localização
`~/Downloads/mindcoach (1)/`

### Compilação
```bash
cd ~/Downloads/mindcoach\ \(1\)/
export ANDROID_HOME=~/android-sdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
echo "GEMINI_API_KEY=*** > .env  # obrigatório
./gradlew assembleDebug
# APK: app/build/outputs/apk/debug/app-debug.apk
```

### Interface — Córtex Dual + 6 Pilares
- **Córtex Dual bar**: Hermes (DeepSeek V4) + Codex (GPT-5.5) + status ONLINE
- **6 pilares**: Financeiro (Ouro), Saúde (Verde), Mente (Roxo), Operacional (Laranja GOL), Comunicação (Azul), Conhecimento (Ciano)
- **Chat** com input + histórico (bolhas "Você" vs "ENTIDADE")
- **Cards de ação** com AGIR/IGNORAR
- **OTA banner** quando update disponível

### Estados (cores automáticas)
- OPERANDO_FOREX → Ouro | ESCALA_GOL → Laranja
- TEMPO_FAMILIA → Roxo | CONEXAO_TERAPIA → Verde

### EntidadeApi.kt — Retrofit Client
Conecta ao Cloud Run: `POST/GET /api/v1/chat`, `/events`, `/state`, `/ota`

### OTA System (OtaManager.kt)
- Verifica `GET /api/v1/ota` ao iniciar
- Compara `CURRENT_VERSION` (constante no código)
- Download via `DownloadManager` + instalação via `FileProvider`
- Permissões: `REQUEST_INSTALL_PACKAGES`, `WRITE_EXTERNAL_STORAGE`

### Repository — anti-invenção
- `generateOfflineResponse()` usa dados reais da memória
- NUNCA contém nomes inventados — "2 filhas", sem nomes
- Fallback para GOL, Forex, Família, Terapia com dados confirmados

## NEURAL API v2 (Cloud Run)

### chat_api.py (:8081, proxy nginx /api/ → :8081)

Endpoints: POST/GET /api/v1/chat, /api/v1/events, /api/v1/state, /api/v1/ota, /api/v1/notify

### ENTIDADE Bridge (entidade_bridge.py)
Cron 1min (970a8181cbd2). GET mensagens pendentes → gera resposta → POST como coach.

### Deploy
```bash
cd ~/.hermes/mindcoach-pro
gcloud run deploy mindcoach --source . --region us-central1 --allow-unauthenticated --quiet
```
URL: mindcoach-541659260074.us-central1.run.app | Projeto: gen-lang-client-0455851315
APK servido em /mindcoach.apk

O chat do MindCoach (💬) usa **WebSocket direto** via Cloudflare Tunnel para resposta em tempo real. O app Android (Kotlin/Retrofit) também se conecta via REST API HTTP com polling, processado pela ENTIDADE bridge.

### Interfaces de Chat

| Interface | Transporte | Método |
|-----------|-----------|--------|
| PWA (browser) | WebSocket | Cloudflare Tunnel → bridge :9877 |
| Android App | REST HTTP | Cloud Run `/api/v1/chat` → polling → ENTIDADE bridge |
| Telegram fallback | Bot API | Encaminhamento opcional (visual) |

### PWA App (Cloud Run + Frontend)

Ver **`references/pwa-maintenance.md`** para:
- Deploy checklist (bump versions, cache bust, build data)
- Correção de conflito de renderização (bridge sobrescreve dados após data.json carregar)
- IndexedDB race condition (cacheSet com DB não inicializado)
- Service Worker auto-update (não precisa mais limpar cache manualmente)
- Endpoint de notificações (`/api/notify`)

### Arquitetura

```
App mobile (💬) ──WebSocket──▶ Cloudflare Tunnel (trycloudflare.com)
                                      │
                                      ▼
                           mindcoach_bridge.py (:9877)
                                      │
                       ┌──────────────┼──────────────┐
                       ▼              ▼              ▼
                  inbox.json    broadcast()    hermes_command()
                  (mensagens    (push p/ app)  (chat, alerta,
                   do usuário)                  render, bubble)
                       │
                       ▼
              Cron job (1 min, agente)
              lê inbox.json → responde
              via send_command({'type':'chat'})
```

### Componentes

| Componente | Arquivo | Função |
|-----------|---------|--------|
| WebSocket Bridge | `scripts/mindcoach_bridge.py` | Servidor :9877, recebe `chat_message`, salva inbox, faz broadcast |
| Chat inbox | `~/.hermes/mindcoach_chat_inbox.json` | Mensagens do usuário (lidas pelo agente) |
| Chat Responder | cron `9ce3846eadc8` (1 min) | Lê inbox, responde via `send_command({'type':'chat'})` |
| Chat monitor (fallback) | `scripts/mindcoach_chat_monitor.py` | Polling REST `/api/chat` no Cloud Run (legado) |
| Chat API (Cloud Run) | `mindcoach-pro/chat_api.py` | Servidor REST :8081, storage em `/tmp/` (efêmero!) |

### Frontend — localStorage obrigatório

O chat NÃO pode limpar ao minimizar/fechar. Toda mensagem deve ser salva em `localStorage['mc_chat_msgs']` e restaurada em `loadChatHistory()`. A conexão WebSocket é estabelecida em `connectChatWS()` usando o túnel Cloudflare (`wss://rehab-meditation-birds-submissions.trycloudflare.com`).

### Comandos do agente para o chat

```python
from mindcoach_bridge import send_command

# Responder chat
send_command({'type': 'chat', 'mensagens': [
    {'role': 'hermes', 'texto': 'Oi! Como vai?'}
]})

# Atualizar bolha
send_command({'type': 'bubble', 'alert': True, 'emoji': '💬', 'text': 'Nova mensagem'})
```

### Chat inbox → ENTIDADE Bridge (HTTP polling)

A ENTIDADE roda localmente e se comunica com o Cloud Run via HTTP (não filesystem compartilhado):

```python
# entidade_bridge.py — roda via cron a cada 1min
state = load('/tmp/mindcoach_state_local.json', {"last_processed_id": 0})
data = http_get(f"{CLOUD_URL}/api/v1/chat?since={state['last_processed_id']}")
user_msgs = [m for m in data['messages'] if m['from'] == 'user' and m.get('pending')]

for msg in user_msgs:
    response = generate_response(msg['text'], msg.get('state'))
    http_post(f"{CLOUD_URL}/api/v1/chat", {"from": "coach", "text": response})
```

**CRÍTICO**: A ENTIDADE responde como `"coach"`, NÃO como `"assistant"` ou `"hermes"`. O app Android filtra `from === "coach"` para exibir respostas.

### Fallback REST (quando WebSocket offline)

O chat também suporta fallback via REST API no Cloud Run:
- POST `/api/v1/chat` → armazena mensagem + encaminha para inbox
- GET `/api/v1/chat?since=N` → retorna mensagens desde ID N
- ⚠️ `/tmp` é **efêmero** — dados perdidos a cada deploy do Cloud Run. Usar HTTP bridge como via primária.

## Pitfalls

- **NUNCA inventar nomes de familiares.** Usar descrições genéricas: "2 filhas", sem nomes. Nomes como "Eduarda", "Sophia", "Heloisa", "Isadora" eram FALSOS e foram removidos. Placeholders genéricos > invenções.
- **Dados do app devem vir da memória/API, não do código.** O bridge Python e o Repository Kotlin usam dados reais (GOL R$3.671, CURA Church, Vespasiano-MG, Telavita).
- **`/tmp` do Cloud Run é efêmero** — mensagens perdidas a cada deploy. Usar HTTP bridge como via primária.
- **Chat: ENTIDADE responde como `"coach"`**, NÃO `"assistant"` ou `"hermes"`. O app filtra `from === "coach"`.
- **OTA: CURRENT_VERSION no OtaManager.kt deve ser incrementado** a cada release. Versão no chat_api.py deve match.
- **Compilação requer `.env` com GEMINI_API_KEY** mesmo sem usar Gemini — plugin secrets exige.
- **Ícones Material: usar apenas `Icons.Default.*` do pacote core** (Star, Place, FavoriteBorder, AccountCircle, Refresh, Send). Ícones como TrendingUp, Flight, SelfImprovement, Download, Navigation NÃO existem no core.
- **`RowScope.weight()` só funciona em funções com receiver `RowScope`.** Declarar `fun RowScope.PilarChip(...)` quando usar `.weight(1f)` dentro de Row.
- **Saúde sem input = 0.00** — score depende de dados do usuário.
- **NÃO gastar com apps de sync** — usuário tem orçamento limitado. Google Fit REST API (grátis).
