# MindCoach Auth — Pipeline de Autorização (25/05/2026)

## Arquitetura

```
Agente (Hermes)                 App MindCoach                  Roberto
     │                               │                            │
     │ POST /chat_api/auth           │                            │
     │ {titulo, msg, expires}        │                            │
     │──────────────────────────────>│                            │
     │                               │ 🔐 badge +1               │
     │                               │ notificação push          │
     │                               │──────────────────────────>│
     │                               │                            │
     │                               │         ✅ / ❌            │
     │                               │<──────────────────────────│
     │                               │                            │
     │ GET /chat_api/auth            │                            │
     │<──────────────────────────────│                            │
     │ status: approved/rejected     │                            │
     │                               │                            │
     ▼ Age conforme resposta         ▼                            ▼
```

## API

### POST /chat_api/auth — Criar solicitação
```json
{
  "titulo": "Executar trade USDJPY",
  "msg": "Setup: BUY @ 156.20, SL 155.80, TP 157.20",
  "from": "hermes",
  "expires": "2026-05-26T00:00:00"
}
```
Response: `{"ok": true, "id": "req_0001"}`

### GET /chat_api/auth — Listar pendentes
Response: `{"requests": [...], "total": 1}`

### POST /chat_api/auth/{id}/respond — Responder
```json
{"action": "approved"}
```
ou `{"action": "rejected"}`

## Script do agente

`~/.hermes/scripts/auth_request.py`:
```bash
# Enviar
python3 auth_request.py "Título" "Mensagem"
# → OK id=req_0001

# Verificar  
python3 auth_request.py --check req_0001
# → {"id": "req_0001", "status": "approved", ...}
```

## Endpoints no Cloud Run

- `/chat_api/auth` → proxy_pass http://127.0.0.1:8081/ (chat_api.py)
- `/chat_api/` → mesmo proxy (nginx.conf)
- Container: nginx:8080 + python3 chat_api.py:8081

## Deploy

```bash
cd ~/.hermes/mindcoach-pro
gcloud run deploy mindcoach --source . --region us-central1 --allow-unauthenticated
```
