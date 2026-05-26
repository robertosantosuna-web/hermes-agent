# MindCoach Chat Debug — Full Version Timeline
## Session 2026-05-25 — 21 deploys, 1 root cause

### Architecture Map
```
Mobile Browser → Cloud Run (nginx :8080) → /api/ → chat_api.py :8081 → /tmp/mindcoach_chat.json
                                      ↘ /core/main.js (ES module)
                                      ↘ Service Worker (sw.js v4)
                                      ↘ 💬 bubble (index.html inline JS)

Cloudflare Tunnel → wss://...trycloudflare.com → mindcoach_bridge.py :9877
                                                      ↓
                                              inbox.json (local)
                                                      ↓
                                              Ollama phi3:mini (auto-responder)
```

### Version Timeline

| Rev | Change | What broke | Why |
|-----|--------|-----------|-----|
| 00008 | SW v4 + nginx no-cache | Page loads ✅ | — |
| 00012 | Chat API Python + REST | UI doesn't show responses | Frontend checked `m.from === 'hermes'`, API returns `'assistant'` |
| 00014 | nginx proxy /api/ → :8081 | Same bug persists | `hermes` vs `assistant` mismatch still present |
| 00016 | Telegram bot token set | Messages lost on deploy | /tmp wiped on Cloud Run redeploy |
| 00017 | Telegram token removed | Stale state file | `state.last_id=2` > `api.last_id=0` → monitor never saw new msgs |
| 00018 | Fix `'hermes'` → `'assistant'` | Still no responses | Cron ran BEFORE messages arrived (timing) |
| 00019 | WebSocket + localStorage v6 | Bridge sent `type:'render'` but frontend expected `type:'chat'` | Format mismatch |
| 00020 | Handler for both `render` and `chat` | `} catch(_) {}` accidentally removed | Patch error |
| 00021 | 💬 opens Coach IA tab | `openHermesChat` was `undefined` | **main.js NEVER loaded** — duplicate `renderDashboard()` |
| 00022 | Renamed `renderDashboard` → `renderInitialDashboard` | main.js loads ✅ but chat offline | Cloudflare tunnel unstable on mobile |
| 00023 | REST API as chat backbone + 3s polling | REST works, WebSocket flaky | Tunnel dependency still in path |

### ROOT CAUSE (found at rev 00022)

```javascript
// line 110: placeholder version (no params)
function renderDashboard() {
  if (neuralData) renderNeuralDashboard();
  else renderOfflineDashboard();
}

// line 208: real version (with data)
function renderDashboard(data) {
  // ... renders dashboard with data
}
```

**Duplicate function declaration in an ES module causes SILENT failure.** The module never executes, but no console error is shown. Every function/export from main.js was `undefined`.

### How It Was Found

CDP via terminal (not via browser tools, which were connected to wrong port):
```python
import asyncio, json, websockets
ws_url = "ws://localhost:9222/devtools/page/..."
async with websockets.connect(ws_url) as ws:
    await ws.send(json.dumps({"id":1, "method":"Runtime.evaluate", 
        "params":{"expression": "import('/core/main.js').catch(e => e.message)", 
                  "returnByValue": True, "awaitPromise": True}}))
    # Response: "Identifier 'renderDashboard' has already been declared"
```

### Key Pitfalls Discovered

1. **Service Worker cache poisoning:** `transferSize: 0` for main.js = SW returning empty response. Fix: unregister SW + clear caches before hard reload.
2. **CDP port mismatch:** Config said 9223, actual browser on 9222. Always check ALL ports.
3. **ES module silent failure:** Duplicate declarations prevent module load with NO console error.
4. **Cloud Run /tmp volatility:** Every deploy wipes /tmp/mindcoach_chat.json. Messages lost.
5. **Cron timing:** Cron at 15:34:18, message at 15:34:29 → 11-second miss. Need sub-minute polling or push-based system.
6. **`patch` tool can remove code:** When old_string matches more context than intended, use replace_all=false carefully.

### Solution Architecture (final)

```
User → Chat input → WebSocket + REST API (dual)
                         ↓
WebSocket → Bridge :9877 → Ollama phi3:mini → auto_responder → WebSocket broadcast
                                                              → REST API POST
REST API → /api/chat → /tmp/mindcoach_chat.json → frontend polls every 3s
```

**Instant responses:** 4.6 seconds via local LLM (phi3:mini on Ollama).
**Backup:** Cron job every 1 minute reads both local inbox AND REST API.
**Redundancy:** Response sent via WebSocket broadcast AND REST API POST.
