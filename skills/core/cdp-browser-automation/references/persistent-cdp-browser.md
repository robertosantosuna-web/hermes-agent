# Persistent CDP Browser — Brave/Chromium Headless as Systemd Service

**Date:** 2026-05-23
**Context:** Hermes v0.14, Brave 148, Ubuntu 24.04

## Architecture

```
┌─────────────────────────────────────────────────┐
│ hermes-brain-browser.service (systemd user)      │
│                                                  │
│ Brave headless --remote-debugging-port=9223      │
│ Profile: ~/.hermes/browser/profile/              │
│ Auto-restart: yes, RestartSec=5                  │
│                                                  │
│ ExecStartPre: tv_session_restore.py              │
│ ExecStartPost: sleep 3 && tv_session_restore.py  │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│ CDP Endpoint: http://localhost:9223             │
│                                                  │
│ Hermes Agent → browser.cdp_url config            │
│ Brain scripts → brain_browser.py CLI             │
└─────────────────────────────────────────────────┘
```

## Setup Commands

```bash
# 1. Create profile directory
mkdir -p ~/.hermes/browser/profile ~/.hermes/browser/logs

# 2. Install and enable service
systemctl --user daemon-reload
systemctl --user enable hermes-brain-browser
systemctl --user start hermes-brain-browser

# 3. Configure Hermes
hermes config set browser.cdp_url 'http://localhost:9223'

# 4. Verify
python3 scripts/brain_browser.py --status
curl -s http://localhost:9223/json/version | python3 -c "import json,sys; print(json.load(sys.stdin).get('Browser','DOWN'))"
```

## Cookie Persistence (Cross-Browser Session Import)

When a site requires human interaction for login (Google OAuth reCAPTCHA, Cloudflare Turnstile), the flow is:

1. **Human logs in on real desktop browser** (Brave with GUI)
2. **Cookies extracted** from `~/.config/BraveSoftware/Brave-Browser/Default/Cookies` (SQLite)
3. **Cookies injected** into headless CDP browser via `Network.setCookie`
4. **Session persists** via `tradingview_cookies.json` backup + systemd ExecStartPre/Post restore

```python
# Extract from real browser
import sqlite3, shutil
shutil.copy2(real_cookies_db, '/tmp/cookies_copy.sqlite')
conn = sqlite3.connect('/tmp/cookies_copy.sqlite')
cookies = conn.execute("""
    SELECT host_key, name, value, is_secure, is_httponly, has_expires, expires_utc
    FROM cookies WHERE host_key LIKE '%targetdomain%'
""").fetchall()
conn.close()

# Inject into CDP browser via Network.setCookie
# See scripts/tv_session_restore.py for full implementation
```

## brain_browser.py — CLI Controller

```bash
# Status check
python3 scripts/brain_browser.py --status

# Navigate + extract content
python3 scripts/brain_browser.py --navigate 'https://site.com' --content

# Screenshot
python3 scripts/brain_browser.py --screenshot /tmp/page.png

# JS eval
python3 scripts/brain_browser.py --eval 'document.title'

# Click element
python3 scripts/brain_browser.py --click '.my-button'

# List tabs
python3 scripts/brain_browser.py --tabs
```

## Sites Tested

| Site | CDP Works? | Notes |
|------|-----------|-------|
| TradingView | ✅ | Logged in via cookie import from real Brave |
| ForexFactory | ✅ | No Cloudflare |
| DailyFX | ✅ | No Cloudflare |
| Forexlive | ✅ | No Cloudflare |
| BabyPips | ❌ | Cloudflare blocks CDP |
| Investopedia | ❌ | Cloudflare blocks CDP |

## Pitfalls

- **SingletonLock**: if previous instance crashed, delete `~/.hermes/browser/profile/SingletonLock` before restart
- **Keyboard layout**: ydotool respects system layout (Brazilian ABNT2 types Ç instead of :). Use `brave-browser 'url'` command directly instead of ydotool for URLs
- **Cookie expiry**: TradingView session cookies expire. `tv_session_restore.py` needs periodic refresh (user re-login when session expires)
- **Memory usage**: headless Brave uses ~130MB. Acceptable for always-on service
