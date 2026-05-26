---
name: mindcoach
description: "MindCoach — Motor de monitoramento permanente multi-dimensão: psicológico, emocional, social, financeiro, comportamental, saúde. Integrado à Rede Neural. Dashboard do digital twin."
version: 1.1.0
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

## Chat — Arquitetura WebSocket (gatilho direto, sem polling)

O chat do MindCoach (💬) usa **WebSocket direto** via Cloudflare Tunnel para resposta em tempo real.

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

### Fallback REST (quando WebSocket offline)

O chat também suporta fallback via REST API no Cloud Run:
- POST `/api/chat` → armazena em `/tmp/mindcoach_chat.json`
- GET `/api/chat?since=N` → retorna mensagens desde ID N
- ⚠️ `/tmp` é **efêmero** — dados perdidos a cada deploy do Cloud Run

## Pitfalls

- **Saúde sem input = 0.00** — o score depende de dados do usuário (wearable ou manual). Sem input, permanece zerado e gera alerta falso.
- **Google Fit sync requer Huawei Health com Google Services** — verificar no celular antes de tentar ativar rota automática.
- **NÃO gastar com apps de sync** — usuário tem orçamento limitado.
- **MindCoach Checkpoint usa LLM** (cron job com agente) — consome tokens. Manter apenas a cada 30 min.
- **Coletores usam no_agent** — scripts Python puros, zero tokens.
- **Chat: `/tmp` do Cloud Run é efêmero** — mensagens são perdidas a cada deploy. Usar WebSocket como via primária, REST apenas como fallback offline.
- **Chat: `'hermes'` vs `'assistant'`** — o frontend antigo filtrava `m.from === 'hermes'` mas a API REST retorna `'assistant'`. Corrigido na v6 para usar WebSocket com `role: 'hermes'`.
- **Chat: estado do monitor** — `mindcoach_chat_monitor.py` salva `last_id` em `~/.hermes/mindcoach_chat_state.json`. Após redeploy (que zera IDs), o estado fica inconsistente (`last_id > api_last_id`). Versão atual faz auto-reset.
- **Chat: o usuário quer gatilho, não polling** — WebSocket é a arquitetura correta. Nunca implementar polling como solução primária.
