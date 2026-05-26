# MindCoach Pro PWA — Debug & Maintenance Reference

## Architecture

```
User Phone/Browser
    ↓ HTTPS
Cloud Run (nginx :8080 + chat_api.py :8081)
    ↓ WebSocket (cloudflare tunnel → localhost:9877)
mindcoach_bridge.py (:9877)
    ↓ reads
mindcoach_state.json, data.json, brain_context.json
```

## Deploy Checklist

1. **Bump ALL versions** in one go:
   - `sw.js`: increment `SW_VERSION`
   - `index.html`: update `?v=NN` in `<script src="/core/main.js?v=NN">`, `sw.js?v=NN` registration, and version display span
2. **Rebuild data**: `bash build_data.sh`
3. **Deploy**: `gcloud run deploy mindcoach --source=. --region=us-central1 --allow-unauthenticated --memory=512Mi`
4. **Verify cache bust**: `curl -s URL/ | grep "vNN"`

## Rendering Conflict Bug (v36 fix)

### Symptom
Dashboard shows "Modo offline — conectando ao Hermes..." or "---" values despite `data.json` having real data.

### Root Cause Cascade
1. `fetch('/data.json')` completes → `renderNeuralDashboard()` populates dashboard with forex/pilares/tech
2. WebSocket connects → bridge sends `current_state` (default empty pilares from `mindcoach_bridge.py` init)
3. `renderScreen('dashboard', data)` **overwrites** the rich dashboard with empty bridge state

### Fix Applied
In `core/main.js`:
- Changed `const app = document.getElementById('app')` → `document.getElementById('main-screen') || document.getElementById('app')` to not destroy sibling panels
- fetch `.then()` calls `renderNeuralDashboard()` immediately if bridge hasn't sent data yet
- All `cacheSet()` calls wrapped in `try/catch` (see IndexedDB pitfall below)

## IndexedDB Race Condition

### Symptom
`cacheSet()` throws synchronous `"DB not initialized"` error that escapes `.catch()` on the promise chain, causing outer `.catch()` to fire (e.g., `[MAIN] Sem data.json` log even though fetch succeeded).

### Root Cause
`getStore()` in `store/localDB.js` throws **synchronously** if `db` is null (IndexedDB not yet opened). The `.catch(()=>{})` on the returned promise does NOT catch synchronous throws — they propagate to the caller's `.catch()`.

### Fix
```js
// BEFORE (broken):
cacheSet('key', value).catch(()=>{});

// AFTER (safe):
try { cacheSet('key', value).catch(()=>{}); } catch(e) {}
```

## Service Worker Auto-Update (v36 fix)

### Symptom
Every deploy requires manually clearing cache (Settings → Clear Browsing Data) to see new version.

### Root Cause
- `SW_VERSION` not bumped on deploy
- JS imports had no cache-bust parameter
- "Busy-check" (chat/auth panel open) prevented auto-reload

### Fix Applied
- `sw.js`: `skipWaiting()` + `claim()` + purge old caches on activate + force reload on `controllerchange`
- `index.html`: SW registration includes `controllerchange` listener that calls `window.location.reload()` WITHOUT checking if chat/auth panels are open
- All JS imports: `?v=NN` query parameter

## Notification Endpoint

`chat_api.py` has `GET/POST /api/notify`. Use `~/.hermes/scripts/notify_app.py`:
```bash
python3 ~/.hermes/scripts/notify_app.py "Título" "Mensagem" [info|warn]
```
The app polls `/api/notify?since=N` every 30s. Notifications show as dock bar alerts (⚠️ or 🔔).

## Debugging via Console

```js
// Check render state
JSON.stringify({
  connText: document.getElementById('conn-text')?.textContent,
  mainHTML: document.getElementById('main-screen')?.innerHTML?.substring(0, 500)
})

// Check console for data flow
// [MAIN] Rede neural carregada → data.json success
// [MAIN] Sem data.json → fetch failed or IndexedDB crash
// [WS] vivo! → WebSocket connected
```

## Pitfalls

- **Brain browser hijacks :9223**: Brain automation opens 80+ TradingView tabs. For app testing, kill brain browser and start clean with `--user-data-dir=/tmp/brave-mindcoach-test`
- **Cloud Run /tmp ephemeral**: Chat history and notifications in `/tmp/` lost on deploy
- **data.json built at deploy time**: Stale until next deploy or manual `build_data.sh`
