# MindCoach Neural API v2 — Endpoints REST

API REST que conecta o app Android à ENTIDADE. Roda no Cloud Run via `chat_api.py :8081`, exposta pelo nginx em `/api/*`.

## Endpoints

### POST /api/v1/chat
Envia mensagem do usuário para a ENTIDADE.
Request: `{"from": "user", "text": "status", "state": "OPERANDO_FOREX"}`
Response: `{"ok": true, "id": 1, "status": "pending"}`

### GET /api/v1/chat?since=N
Recebe mensagens incluindo respostas da ENTIDADE.
Response: `{"messages": [...], "last_id": 2}`

### GET /api/v1/events
Eventos do ecossistema (cards de ação).
Response: `{"events": [...], "version": 1}`

### POST /api/v1/event/:id/action
Executa ação. Request: `{"action": "execute"|"dismiss"}`

### GET /api/v1/state
Estado da ENTIDADE: `{"state": "OPERANDO_FOREX", "ecosystem": {...}}`

### POST /api/v1/state
Atualiza estado: `{"state": "TEMPO_FAMILIA"}`

### GET /api/v1/ota
Update check: `{"version": 4, "apk_url": "...", "changelog": "..."}`

## Fluxo de comunicação

```
App → POST /api/v1/chat → chat_api.py → /tmp/mindcoach_chat.json
                                         /tmp/mindcoach_inbox.json
ENTIDADE (cron 1min) → GET inbox → POST response (from=coach)
App → GET /api/v1/chat?since=N (polling) → recebe resposta
```

## nginx.conf — CRÍTICO

`proxy_pass http://127.0.0.1:8081;` — SEM trailing slash para preservar `/api/`.

## urlparse

Usar `urllib.parse.urlparse` para query strings — `split('/')` quebra com `?since=N`.
