---
name: mindcoach-deploy
description: Deploy and maintain the MindCoach Pro app — Cloud Run, bridge WebSocket, chat persistence, UI fixes.
version: 1.0.0
---

# MindCoach Pro — Deploy & Architecture

MindCoach Pro is a PWA (Svelte-free vanilla JS) with:
- **Frontend**: Static HTML/JS served by nginx on Cloud Run
- **Backend**: Python HTTP server (`chat_api.py`) for `/api/chat`, `/api/auth`, `/api/calendar`
- **Bridge**: Local WebSocket server (`mindcoach_bridge.py` :9877) connecting the app to the Hermes Agent and neural data

## Architecture

```
[App (Cloud Run)] ---REST---> [chat_api.py :8081]
       |                            |
   WebSocket                  /tmp/ files
       |                      (volatile!)
       v                            |
[Bridge :9877 (local)] <---REST-----+
       |
  File storage (persistent)
  - mindcoach_chat_history.json
  - mindcoach_state.json
  - data.json (neural network)
```

**Key rule**: The Cloud Run filesystem is VOLATILE. Chat history and neural data MUST flow through the local bridge. Never rely on `/tmp/` for persistence.

## Deploy — Cloud Run

### Dockerfile (working)

```dockerfile
FROM python:3.11-slim  # NOT nginx:alpine — Google libs need glibc
RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*
RUN pip install google-api-python-client google-auth google-auth-oauthlib
COPY . /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080 8081
CMD sh -c "python3 /usr/share/nginx/html/chat_api.py & nginx -g 'daemon off;'"
```

### Deploy command

```bash
gcloud run deploy mindcoach \
  --source=/home/roberto/.hermes/mindcoach-pro \
  --region=us-central1 \
  --allow-unauthenticated \
  --memory=512Mi \
  --project=PROJECT_ID
```

### Token for Cloud Run

Google token doesn't persist on filesystem. Use base64 env var:

```bash
# Set env var
TOKEN_B64=$(cat ~/.hermes/google_token.json | base64 -w0)
echo "GOOGLE_TOKEN_B64: $TOKEN_B64" > /tmp/cloudrun_env.yaml
gcloud run services update mindcoach --region=us-central1 --env-vars-file=/tmp/cloudrun_env.yaml
```

Code reads from `GOOGLE_TOKEN_B64` env var, decodes and writes temp file.

## Bridge (`mindcoach_bridge.py`)

### Start/Restart

```bash
systemctl --user restart mindcoach-bridge.service
```

### Chat Flow

1. App sends `chat_message` via WebSocket
2. Bridge saves to `chat_history` (persistent file) + sets `pending_chat` in gateway checkpoint
3. Bridge sends `✓` quick acknowledgment (not robotic "Recebido!")
4. Agent checks gateway checkpoint for pending chat
5. Agent responds via `chat_to_app.py "text"` → WebSocket → bridge → app

### Chat Persistence

- `~/.hermes/mindcoach_chat_history.json` — last 100 messages
- Bridge loads on startup, broadcasts `chat_history` on client connect
- App `main.js` renders from `chatHistoryCache`

### Data Cache

- `~/.hermes/mindcoach-pro/data.json` — built by `build_data.sh`
- Bridge loads into `data_cache` and broadcasts on connect + on `refresh_data` command
- Cron job `mindcoach-data-refresh` rebuilds every 30min

### Agent Response Script

```bash
python3 ~/.hermes/scripts/chat_to_app.py "texto da resposta"
```

Connects to `ws://127.0.0.1:9877`, sends `{"type": "chat_response", "texto": "..."}`.

## UI Bug Fixes

> **Nota:** Bugs de UI agora são documentados em `mindcoach-app` (skill principal de debugging). Esta seção cobre apenas bugs específicos de deploy.

### togglePanel empty (Painel button does nothing)

**ATENÇÃO:** `main.js:129` sobrescreve `dockPainel.onclick` com `cyclePilar()`. O handler correto (v39+) é:
```javascript
dockPainel.onclick = () => {
  togglePanel(); // Fecha todos os painéis
  const next = cyclePilar();
  ...
};
```

### Calendar panel state management (CORRIGIDO v38)

NUNCA usar `style.display` e `classList` juntos. Usar SOMENTE `classList.toggle('open')` com CSS `.panel.open { display: flex; }`. Ver Bug #8 em `mindcoach-app`.

## nginx.conf routing

**CRITICAL**: `proxy_pass` with trailing slash (`http://127.0.0.1:8081/`) STRIPS the `location` prefix — `/api/v1/chat` arrives as `/v1/chat` on the backend. WITHOUT trailing slash (`http://127.0.0.1:8081`), the full path is preserved. Match your backend's expected paths.

```nginx
# Chat API — proxy para Python server (preserva /api/ prefix)
location /api/ {
    proxy_pass http://127.0.0.1:8081;   # sem trailing slash → preserva /api/
    proxy_http_version 1.1;
    proxy_set_header Host $host;
}

# Legacy paths (sem /api/) — também proxy
location /chat { proxy_pass http://127.0.0.1:8081; proxy_http_version 1.1; proxy_set_header Host $host; }
location /auth { proxy_pass http://127.0.0.1:8081; proxy_http_version 1.1; proxy_set_header Host $host; }
location /notify { proxy_pass http://127.0.0.1:8081; proxy_http_version 1.1; proxy_set_header Host $host; }
location /calendar { proxy_pass http://127.0.0.1:8081; proxy_http_version 1.1; proxy_set_header Host $host; }
```

See also: **[references/android-neural-api.md](references/android-neural-api.md)** — multi-endpoint REST API for Android app ↔ ENTIDADE connection.

## Verification Checklist

- [ ] `curl https://APP_URL/` → 200
- [ ] `curl https://APP_URL/api/chat` → `{"messages":[],"last_id":0}`
- [ ] `curl https://APP_URL/api/calendar` → `{"events":[...],"total":N}`
- [ ] Bridge: `systemctl --user is-active mindcoach-bridge.service` → active
- [ ] Data refresh cron: runs every 30min, no_agent, local delivery
- [ ] Chat persistence: `cat ~/.hermes/mindcoach_chat_history.json` has messages
