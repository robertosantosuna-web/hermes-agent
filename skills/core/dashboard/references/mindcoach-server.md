# MindCoach Live Reload Server — Technical Reference

## Architecture
```
mindcoach_server.py
  ├── Thread 1: HTTP server (porta 9878)
  ├── Thread 2: File watcher (mtime:size every 3s)
  └── Main: WebSocket server (porta 9879, asyncio)
```

## File Change Detection
```python
def file_hash(path):
    try:
        stat = path.stat()
        return f"{stat.st_mtime}:{stat.st_size}"
    except:
        return ''
```
⚠️ **DON'T use md5 of content** — `touch` doesn't change content hash, only mtime.

## Cross-Thread WebSocket Send
`websockets` library is async-only. To send from a sync thread:
```python
LOOP = None  # set in ws_server(): LOOP = asyncio.get_running_loop()

def notify_reload():
    for ws in list(ws_clients):
        asyncio.run_coroutine_threadsafe(
            ws.send(json.dumps({'type': 'reload'})),
            LOOP
        )
```
⚠️ `ws.send_message()` DOES NOT EXIST on websockets — it's `ws.send()`.

## Service Worker Cache Bust
When old SW cached `/sw.js` itself, new SW never loads. Fix:
```html
<!-- index.html -->
navigator.serviceWorker.register('/sw.js?v=4')
```
Increment `v=N` on each deploy that changes SW logic.
Also in sw.js: `const SW_VERSION = N;` and `const CACHE = 'mindcoach-v${N}';`

## Cloud Run Deploy with Data Injection
```bash
# 1. Dump neural data to static JSON
bash ~/.hermes/mindcoach-pro/build_data.sh

# 2. Deploy (Cloud Build)
cd ~/.hermes/mindcoach-pro
gcloud run deploy mindcoach --source . --region us-central1 --allow-unauthenticated
```
Project: `gen-lang-client-0455851315`
IAM: service account `hermes-deploy@...` can't setIamPolicy (needs manual grant)
URL: `https://mindcoach-541659260074.us-central1.run.app`

## Data Flow
```
Brain cron jobs → .hermes/forex/*.json
                    .hermes/mindcoach_state.json
                    .hermes/brain_context.json
                         ↓
              build_data.sh (cron: H+30)
                         ↓
                   data.json
                    ↙        ↘
          HTTP:9878          Cloud Run
       (live reload)      (public URL)
```

## Client-Side Live Reload
```html
<script>
(function() {
  const ws = new WebSocket('ws://127.0.0.1:9879');
  ws.onmessage = (e) => {
    const d = JSON.parse(e.data);
    if (d.type === 'reload') window.location.reload();
  };
  ws.onclose = () => setTimeout(connect, 2000);
})();
</script>
```
On Cloud Run, this WS connection silently fails → no reload. Desktop-only feature.
