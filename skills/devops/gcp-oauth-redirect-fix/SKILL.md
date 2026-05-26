---
name: gcp-oauth-redirect-fix
description: Complete Google OAuth setup for GCP projects — from redirect_uri_mismatch to live API verification. Covers all pitfalls.
version: 1.1.0
---

# GCP OAuth Setup — Complete Flow

## When to use

Google OAuth `redirect_uri_mismatch`, `access_denied`, or any OAuth setup for a GCP project using the `google-workspace` skill's `setup.py`.

## Prerequisites

- GCP project with OAuth consent screen configured (even in Testing mode)
- `google-workspace` skill installed (provides `setup.py` and `google_api.py`)
- User's Google account must be accessible in a browser (CDP on :9222 works)

## Full Resolution Flow

### Phase 1: Fix redirect_uri_mismatch (manual, 30s)

**Symptom:** `Error 400: redirect_uri_mismatch` — ALL URIs rejected.

**Root cause:** The `client_secret.json` has redirect URIs that don't match GCP Console. This happens when the OAuth client was modified after JSON download, or client type was changed (Desktop ↔ Web).

**Fix:** User opens the OAuth client edit page and adds `http://localhost:1`:
```
https://console.cloud.google.com/apis/credentials/oauthclient/CLIENT_ID?project=PROJECT_ID
```
→ "URIs de redirecionamento autorizados" → "Adicionar URI" → type `http://localhost:1` → Enter → "Salvar"

### Phase 2: Fix access_denied (manual, 10s)

**Symptom:** `Error 403: access_denied` — "The developer hasn't given you access to this app."

**Root cause:** OAuth consent screen is in "Testing" mode and user's email isn't in test users.

**Fix:** User adds their email to test users:
```
https://console.cloud.google.com/auth/audience?project=PROJECT_ID
```
→ "Test users" → "Add users" → type email → "Save"

### Phase 3: Complete OAuth exchange (automated with human browser step)

Use the official `setup.py` — never build custom PKCE:

```bash
GSETUP="python3 ~/.hermes/skills/productivity/google-workspace/scripts/setup.py"

# Store client secret
$GSETUP --client-secret ~/.hermes/google_client_secret.json

# Generate auth URL
$GSETUP --auth-url
```

Send URL to user. After authorization, grab redirect from CDP browser:

```bash
REDIRECT_URL=$(python3 -c "
import urllib.request, json
pages = json.loads(urllib.request.urlopen('http://localhost:9222/json/list', timeout=5).read())
for p in pages:
    if 'localhost:1' in p.get('url','') and 'code=' in p.get('url',''):
        print(p['url'])
        break
")
$GSETUP --auth-code "$REDIRECT_URL"
```

### Phase 4: Enable APIs and verify

```bash
# Enable required APIs
gcloud services enable calendar-json.googleapis.com gmail.googleapis.com \
  drive.googleapis.com sheets.googleapis.com docs.googleapis.com \
  people.googleapis.com --project=PROJECT_ID

# Verify
$GSETUP --check       # → AUTHENTICATED
$GSETUP --check-live  # → LIVE_CHECK_OK
```

Token saved at `~/.hermes/google_token.json` with auto-refresh.

## Cloud Run / Docker Token Setup

For deploying the token to Cloud Run (where filesystem isn't persistent):

1. Base64-encode the token: `cat ~/.hermes/google_token.json | base64 -w0`
2. Set as env var: `gcloud run services update SERVICE --env-vars-file=/tmp/env.yaml`
3. Code reads from `GOOGLE_TOKEN_B64` env var, base64-decodes it, writes temp file

See `references/cloud-run-token-deploy.md` for full details.

## What NOT to do (burns tokens)

- ❌ Build custom OAuth PKCE flow — use `setup.py --auth-url` + `--auth-code`
- ❌ Automate GCP Console via CDP — Angular SPA resists programmatic clicks
- ❌ ydotool blind Tab navigation on GCP Console pages
- ❌ Try `urn:ietf:wg:oauth:2.0:oob` — deprecated by Google
- ❌ Use gcloud/API to modify OAuth clients (IAP deprecated, Identity Toolkit disabled)

## Related skills

- `google-workspace` — OAuth setup scripts (`setup.py`, `google_api.py`)
- `mindcoach-deploy` — Cloud Run deployment patterns including token env var setup
- `self-correction` (AP-15) — Consult skills before acting, update after failures

## Verification checklist

- [ ] `$GSETUP --check` prints AUTHENTICATED
- [ ] `$GSETUP --check-live` prints LIVE_CHECK_OK
- [ ] `$GAPI gmail search "is:unread" --max 1` returns results
- [ ] Token path and project ID saved to memory
