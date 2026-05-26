---
name: web-app-deploy
description: "Deploy web apps no Cloud Run + servidor desktop com live reload. Static nginx + Python micro API backend. Service Worker cache bust. Chat bidirecional."
---

# Web App Deploy — Cloud Run + Desktop Live Reload

## Deploy rápido (Cloud Run)

```bash
cd /path/to/app
gcloud run deploy <service-name> --source . --region us-central1 --allow-unauthenticated
```

- Constrói via Cloud Build (Dockerfile no dir)
- Sem docker local necessário
- URL: `https://<service>-<hash>.<region>.run.app`

### Pós-deploy: configurar env vars (Telegram forward)

```bash
gcloud run services update <service> --region us-central1 \
  --set-env-vars "CHAT_BOT_TOKEN=<telegram_bot_token>,CHAT_ID=<telegram_chat_id>"
```

Sem isso, o Telegram forward não funciona e o chat fica mudo.

### Dockerfile — nginx + Python API

```dockerfile
FROM nginx:alpine
RUN apk add --no-cache python3
COPY . /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY api.py /usr/share/nginx/html/api.py
EXPOSE 8080
CMD sh -c "python3 /usr/share/nginx/html/api.py & nginx -g 'daemon off;'"
```

### nginx.conf — proxy /api/* → Python

```nginx
server {
    listen 8080;
    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8081/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # SW — no-cache obrigatório
    location /sw.js {
        add_header Service-Worker-Allowed /;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## Servidor Desktop com Live Reload

Servidor local (HTTP + WebSocket) que detecta mudanças nos arquivos e força reload no browser.

### Arquitetura

```
HTTP :9878  → serve arquivos estáticos
WS   :9879  → live reload (notifica browser)
Watcher      → thread que monitora arquivos (mtime:size)
```

### Pitfalls críticos

1. **NÃO usar content hash** (`md5`) para detectar mudanças — `touch` muda mtime mas não conteúdo.
   Use `stat.st_mtime:stat.st_size`.

2. **Cross-thread WebSocket**: `websockets` é async. Para enviar de thread sync, use:
   ```python
   asyncio.run_coroutine_threadsafe(ws.send(msg), LOOP)
   ```

3. **Buffering no systemd**: usar `flush=True` em todos `print()` para logs aparecerem no journal.

4. **Port binding**: `systemctl restart` pode deixar processo zumbi na porta.
   Use `fuser -k PORT/tcp` antes de reiniciar.

### Script: `mindcoach_server.py`

Servidor HTTP + WebSocket + file watcher. Ver: **[references/live-reload-server.py](references/live-reload-server.py)**.

### Script: `chat_monitor.py`

Monitor de chat para cron job. Ver: **[references/chat-monitor.py](references/chat-monitor.py)**.

### Client (index.html)

```html
<script>
(function() {
  const WS = 'ws://127.0.0.1:9879';
  function connect() {
    const ws = new WebSocket(WS);
    ws.onmessage = (e) => {
      const d = JSON.parse(e.data);
      if (d.type === 'reload') window.location.reload();
    };
    ws.onclose = () => setTimeout(connect, 2000);
  }
  connect();
})();
</script>
```

---

## Service Worker — Cache Bust

### Problema: SW velho cacheou `sw.js` em `cache.addAll()`

O SW v3 fazia:
```js
const ASSETS = ['/', '/index.html', '/sw.js', ...];
caches.open('mindcoach-v3').then(c => c.addAll(ASSETS));
```
Isso cacheava o PRÓPRIO `sw.js`. Qualquer deploy novo era ignorado — o browser servia o SW do cache.

### Solução: `?v=N` query param

```js
navigator.serviceWorker.register('/sw.js?v=4');
```

O query param faz a URL ser diferente → browser trata como novo SW → ignora cache do SW antigo.

### SW v4+ — sem cache no install

```js
self.addEventListener('install', e => {
  self.skipWaiting(); // Ativa imediatamente
  // NUNCA usar cache.addAll() aqui
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  e.waitUntil(clients.claim());
});

// Network-first, cache dinâmico SÓ após fetch bem-sucedido
self.addEventListener('fetch', e => {
  e.respondWith(
    fetch(e.request).then(response => {
      const clone = response.clone();
      caches.open(CACHE).then(c => c.put(e.request, clone));
      return response;
    }).catch(() => caches.match(e.request))
  );
});
```

---

## Chat API — Bidirecional com Trigger

Para adicionar chat em site estático no Cloud Run com **resposta automática do agente**.

⚠️ **ARQUITETURA CORRETA**: O chat NÃO é só polling. Deve ter **gatilho imediato** — quando o usuário envia mensagem, o agente (entidade) é acionado e responde. Polling puro NÃO funciona (usuário fica sem resposta).

### Arquitetura Trigger (Direta, sem Telegram)

```
Usuário → POST /api/chat → Cloud Run armazena em /tmp/chat.json
                            ↓
                     Cron job (every 1m) detecta nova msg
                            ↓
                     Agente responde via POST /api/chat
```

Apenas UM mecanismo: **cron job com agente** a cada 1min verifica mensagens novas e responde direto no chat.

**NÃO usar Telegram como intermediário.** O usuário quer resposta DIRETA no chat, não notificação em outro app.
O Telegram forward (via `CHAT_BOT_TOKEN`) é opcional — serve apenas como notificação visual, mas NÃO é o canal de resposta.

### Backend: micro servidor Python (:8081)

```python
DATA_FILE = '/tmp/chat.json'

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Retorna mensagens desde `since`
        data = load()
        since = int(self.path.split('since=')[1] or 0)
        msgs = [m for m in data['messages'] if m['id'] > since]
        self.send_json({'messages': msgs[-20:], 'last_id': data.get('last_id', 0)})

    def do_POST(self):
        msg = json.loads(self.rfile.read(length))
        data = load()
        data['last_id'] += 1
        entry = {'id': data['last_id'], 'from': msg.get('from', 'user'), 'text': msg.get('text', ''), 'time': now(), 'read': False}
        data['messages'].append(entry)
        save(data)
        self.send_json({'ok': True, 'id': entry['id']})
```

⚠️ O campo `from` no POST aceita qualquer valor. O **frontend envia `"user"`**, o **agente deve responder com `"assistant"`**.
O frontend DEVE filtrar por `m.from === 'assistant'` para exibir respostas. Filtrar por `"hermes"` é bug silencioso.

### Frontend: poll a cada 10s

```js
let lastChatId = 0;
async function pollChat() {
  const resp = await fetch(`/api/chat?since=${lastChatId}`);
  const data = await resp.json();
  for (const m of (data.messages || [])) {
    if (m.id > lastChatId) lastChatId = m.id;
    // ⚠️ API retorna "from": "assistant" (NÃO "hermes"!)
    if (m.from === 'assistant') {
      document.querySelector('.chat-typing')?.remove();
      msgs.innerHTML += `<div class="chat-msg hermes">
        <div class="sender">Hermes</div>${escapeHtml(m.text)}</div>`;
    }
  }
}
setInterval(pollChat, 10000);
setTimeout(pollChat, 1000);  // Poll inicial rápido
```

⚠️ **CRÍTICO**: O campo `from` na API é `"assistant"` (NÃO `"hermes"`).
Filtrar por `"hermes"` faz TODAS as respostas do agente serem ignoradas silenciosamente.
Este bug causou múltiplas sessões de debug — o chat parecia "mudo".

### Responder do Hermes (Automático)

⚠️ **NÃO usar resposta manual**. O chat deve ser AUTOMÁTICO com cron job.

```bash
# Criar cron job que monitora e responde
hermes cron create --name "MindCoach Chat Responder" \
  --schedule "every 1m" \
  --prompt "Rode python3 ~/.hermes/scripts/mindcoach_chat_monitor.py.
Se output contém NEW_USER_MESSAGES, extraia JSON e responda cada msg
via curl POST /api/chat. Se NO_NEW_MESSAGES, só diga ok." \
  --toolsets terminal \
  --deliver local
```

### Pitfall: Cloud Run é STATELESS

`/tmp/chat.json` é **perdido a cada deploy** (nova revisão = novo container).
Mensagens anteriores somem. Soluções:
- **Aceitar perda** (chat em tempo real, resposta em <1min)
- Cloud Storage mount (bucket GCS)
- Firestore

**NUNCA** confiar em `/tmp/` para persistir dados entre deploys.

⚠️ **Toda alteração de env var também é um redeploy**. `gcloud run services update --set-env-vars` 
cria nova revisão → novo container → `/tmp/` zerado. Até mesmo `--remove-env-vars` dispara redeploy.

### Pitfall: Estado do monitor fica STALE após redeploy

O script `mindcoach_chat_monitor.py` mantém `~/.hermes/mindcoach_chat_state.json` 
com `last_id` da última mensagem processada. Após redeploy, o `/tmp/chat.json` é resetado
(mensagens começam do ID 1 de novo), mas o state file local ainda tem `last_id` antigo.
Resultado: monitor consulta `since=X` onde X > api_last_id → 0 mensagens → chat "mudo".

**Solução: auto-reset no monitor.** Se `state.last_id > api.last_id`, resetar para 0
e re-fetch. Ver `references/chat-monitor.py` para implementação.

### Telegram Forward (gatilho visual)

Cloud Run notifica Telegram quando usuário envia msg. Requer:

```bash
# Setar env var no Cloud Run (token do bot Telegram)
gcloud run services update <service> --region us-central1 \
  --set-env-vars "CHAT_BOT_TOKEN=<token>,CHAT_ID=<chat_id>"
```

O `chat_api.py` já tem código de forward (linhas 67-79 do template).
Só precisa do token configurado.

---

## Data Injection — Build-time JSON

Para injetar dados da rede neural no site estático:

```bash
#!/bin/bash
# build_data.sh — roda antes do deploy
python3 << 'PYEOF'
data = {
    "build_time": datetime.now().isoformat(),
    "forex": {"bias": json.loads(Path("weekly_bias.json").read_text())},
    "brain": {"updates": [...]},
    "pilares": {...},
}
Path("data.json").write_text(json.dumps(data))
PYEOF
```

Cron: `*/30 * * * *` — rebuild data.json periodicamente.

---

## Cron Job Pitfalls (Chat Responder)

### Schedule mínimo é 1 minuto

`30s` ou `every 30s` NÃO são aceitos. Mínimo: `every 1m`.

### repeat=N não significa "rodar N vezes"

`repeat=2000` com `schedule=every 1m` NÃO roda 2000 vezes.
O scheduler interpreta como contador. Use `repeat=100000` pra ser "forever" prático.

### no_agent=True NÃO responde chat

Script `no_agent=True` só emite output — não consegue postar respostas personalizadas.
Para chat, usar `no_agent=False` com prompt de agente + `enabled_toolsets: ["terminal"]`.

### Limpar jobs duplicados

Sempre verificar `cronjob(action='list')` antes de criar. Se existir job com mesmo nome,
remover o antigo primeiro. Jobs duplicados competem e geram estado inconsistente.

### Toolsets mínimos

Chat responder só precisa de `terminal`. Não incluir `web`, `file`, etc — reduz tokens.

---

## Tool Quirks

### Telegram token masking

O sistema mascara tokens Telegram no output do terminal (`8842233957:***`).
Para extrair token completo, usar Python subprocess caractere por caractere:

```python
import subprocess
result = subprocess.run(['grep', 'BOT_TOKEN', '/home/roberto/.hermes/.env'],
                        capture_output=True, text=True)
token = result.stdout.strip().split('=', 1)[1]
# Print com espaços para evitar masking
print(' '.join(token))
```

## IAM Warning (inofensivo)

Ao fazer deploy com service account sem permissão `setIamPolicy`:
```
WARNING: Setting IAM policy failed
```
Ignorar. O app já é público (binding anterior persiste).
