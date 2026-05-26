# Google Cloud Console CDP Automation

> Discovered: 2026-05-24 | Brain Calendar Monitor development

## Pattern: Automating GCP Console via WebSocket CDP

Google Cloud Console is a heavy SPA (Angular/Material Design). Standard CDP approaches fail because:
- Elements are dynamically rendered
- Shadow DOM in some components (mat-select, services-*)
- Text is often in accessibility-tree-only nodes
- Buttons need JS `.click()` not `Input.dispatchMouseEvent`

### Core Technique: TreeWalker for Text Extraction

```javascript
var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
var node;
while (node = walker.nextNode()) {
    var txt = node.textContent.trim();
    // Filter and collect
}
```

Works reliably even when `document.body.innerText` is empty or `querySelectorAll` misses SPA elements.

### Button Clicking in Google Cloud Console

**DO NOT use Input.dispatchMouseEvent** — GCP React/Angular ignores raw mouse events.

**USE JavaScript `.click()`:**
```javascript
var btns = document.querySelectorAll('button');
for (var btn of btns) {
    if ((btn.textContent || '').trim() === 'Criar credenciais') {
        btn.click();
    }
}
```

### Finding Elements by Text

Scan all elements, filter by text content:
```javascript
var els = document.querySelectorAll('*');
for (var el of els) {
    if (el.offsetParent === null) continue; // invisible
    var txt = (el.textContent || '').trim();
    if (txt.includes('target text')) { ... }
}
```

### Google Calendar Extraction (without OAuth)

1. Connect to existing browser session (Brave :9222)
2. Navigate to `https://calendar.google.com/calendar/u/0/r/week`
3. Use TreeWalker to find text nodes matching patterns:
   - `tarefa: ... Não concluída, D de mês de ANO, HHam`
   - `evento: ... , D de mês de ANO`
4. Parse Portuguese dates with month name mapping:
   ```python
   meses = {"janeiro":1, "fevereiro":2, "março":3, ...}
   ```

### Pitfalls

- **CDP HTTP endpoint (`/cdp/{tab_id}`) returns 404** — must use WebSocket
- **Python venv 3.11 lacks `websocket-client`** — use `/usr/bin/python3` (system Python 3.14)
- **Always import `time`** — missing import causes silent failure in `except: pass` blocks
- **SPA elements load async** — always `time.sleep(4-6)` after navigation, drain WebSocket messages
- **`Runtime.evaluate` with multi-line JS** — triple-quote strings, no backtick conflicts
- **Text is NOT in `aria-label`** for GCP — must use TreeWalker or full `innerText`

### Tools Used
- `/usr/bin/python3` with `websocket-client` (pip installed with `--break-system-packages`)
- Brave CDP port 9222 for Google-authenticated sessions
- Edge CDP port 9224 for WhatsApp
