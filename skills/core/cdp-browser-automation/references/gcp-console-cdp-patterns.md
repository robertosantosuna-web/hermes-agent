# GCP Console — CDP Navigation Patterns

Session: 2026-05-24. Authenticated via Edge CDP port 9222 (real Brave browser).

## Service Account Creation Flow

### Step 1: Open Service Accounts page
```python
req = urllib.request.Request(
    'http://localhost:9222/json/new?https://console.cloud.google.com/iam-admin/serviceaccounts?project=PROJECT_ID',
    method='PUT'
)
resp = json.loads(urllib.request.urlopen(req).read())
ws = websocket.create_connection(resp['webSocketDebuggerUrl'], timeout=15)
```

### Step 2: Click "Criar conta de serviço"
```javascript
// Find by text content
document.querySelectorAll('button').forEach(el => {
    if (el.textContent.trim() === 'Criar conta de serviço') el.click();
});
```

### Step 3: Fill service account name (Material Design inputs)
Material inputs have dynamic IDs like `_0rif_mat-input-0`. Use CDP `Input.dispatchKeyEvent` with `type: "char"`:

```python
# Focus + type each character
cdp("Runtime.evaluate", {
    "expression": "document.getElementById('_0rif_mat-input-0').focus()",
    "returnByValue": True
})
for char in "hermes-deploy":
    cdp("Input.dispatchKeyEvent", {
        "type": "char", "text": char, "unmodifiedText": char
    })
    time.sleep(0.03)
```

Service account ID auto-fills from name. Description field is `_0rif_mat-input-2`.

### Step 4: Click "Criar e continuar"
```javascript
document.querySelectorAll('button, span').forEach(el => {
    if (el.textContent?.includes('Criar e continuar')) el.click();
});
```

### Step 5: Select "Editor" role
The role selector is `<CFC-SELECT-DUAL-COLUMN>` with dynamic id `_0rif_cfc-select-dual-column-0`.

```python
# Click to open dropdown
cdp("Runtime.evaluate", {
    "expression": "document.getElementById('_0rif_cfc-select-dual-column-0').click()",
    "returnByValue": True
})

# Wait for dropdown, then find and click "Editor"
cdp("Runtime.evaluate", {
    "expression": """
    (() => {
        const spans = document.querySelectorAll('.mdc-list-item__primary-text');
        for (const s of spans) {
            if (s.textContent.trim() === 'Editor') {
                let parent = s.parentElement;
                while (parent) {
                    if (parent.tagName === 'MAT-OPTION' || parent.getAttribute('role') === 'option') {
                        parent.click();
                        return 'clicked';
                    }
                    parent = parent.parentElement;
                }
            }
        }
        return 'not found';
    })()
    """,
    "returnByValue": True
})
```

### Step 6: "Continuar" → "Concluído"
Click "Continuar" on step 2 (permissions), then "Concluído" on step 3 (skip grant access).

### Step 7: Navigate to Keys page
Service account numeric ID is shown in the table row. Navigate directly:
```
PUT /json/new?https://console.cloud.google.com/iam-admin/serviceaccounts/details/{NUMERIC_ID}/keys?project={PROJECT_ID}
```

### Step 8: Create JSON key
```python
# Click "Adicionar chave" → "Criar nova chave" → JSON is default → Click "Criar"
# The "Criar" button is in a dialog (.cdk-overlay-pane or mat-dialog-container)

cdp("Runtime.evaluate", {
    "expression": """
    (() => {
        const dialogs = document.querySelectorAll('[role="dialog"], .cdk-overlay-pane');
        for (const d of dialogs) {
            const btns = d.querySelectorAll('button');
            for (const b of btns) {
                if (b.textContent?.trim() === 'Criar') {
                    b.click();
                    return 'clicked';
                }
            }
        }
        return 'not found';
    })()
    """,
    "returnByValue": True
})
```

### Step 9: Capture downloaded key
The key downloads as a temporary file in `~/Downloads/`:
```bash
# Find the partial download
ls ~/Downloads/.org.chromium.Chromium.*
# Copy to permanent location
cp ~/Downloads/.org.chromium.Chromium.XXXXX ~/.hermes/gcp_sa_key.json
chmod 600 ~/.hermes/gcp_sa_key.json
```

### Step 10: Authenticate gcloud
```bash
gcloud auth activate-service-account hermes-deploy@PROJECT_ID.iam.gserviceaccount.com \
    --key-file=~/.hermes/gcp_sa_key.json \
    --project=PROJECT_ID
```

## Key DOM Patterns

### Material Design select (mat-select)
- Trigger: `CFC-SELECT-DUAL-COLUMN` with dynamic id
- Dropdown: `.cdk-overlay-container` contains the options
- Options: `mat-option` elements with `role="option"`
- Selection text: `.mdc-list-item__primary-text`

### Form inputs
- Standard: `<input id="_0rif_mat-input-N">`
- Focus then type via `Input.dispatchKeyEvent` char-by-char
- JS `.value` setter does NOT work for Material forms

### Buttons in GCP Console
- Standard buttons respond to JS `.click()`
- Buttons inside dialogs: search within `[role="dialog"]` or `.cdk-overlay-pane`

### Notifications
- GCP shows notifications at page bottom: "Conta de serviço criada", "Nenhuma alteração..."
- These don't block interaction but indicate success/failure

## Billing
Cloud Run, Cloud Build, and Artifact Registry require billing enabled:
```
gcloud services enable → FAILED_PRECONDITION: Billing account not found
```
User must enable billing at: https://console.cloud.google.com/billing/projects

## Service Account Email Format
`{name}@{project_id}.iam.gserviceaccount.com`
Example: `hermes-deploy@gen-lang-client-0455851315.iam.gserviceaccount.com`
Numeric ID is separate — found in the console table row.

## Enable GCP APIs via CDP

Google APIs (Cloud Run, Cloud Build, Cloud Resource Manager, Artifact Registry) need to be enabled before use. Service accounts may lack permission to enable them — use the user's browser.

### Pattern
```python
# Navigate to API enable page (use numeric project ID from error messages)
url = 'https://console.developers.google.com/apis/api/{api_name}.googleapis.com/overview?project={NUMERIC_ID}'
req = urllib.request.Request(f'http://localhost:9222/json/new?{url}', method='PUT')

# Click "Ativar" button
cdp("Runtime.evaluate", {
    "expression": """
    (() => {
        const buttons = document.querySelectorAll('button');
        for (const b of buttons) {
            if (b.getAttribute('aria-label') === 'ativar esta API') {
                b.click();
                return 'clicked';
            }
        }
        return 'not found';
    })()
    """,
    "returnByValue": True
})
# Wait for "Carregando..." to disappear (~10-20s)
```

Common APIs to enable:
- `serviceusage` — Service Usage API (needed to enable other APIs)
- `cloudresourcemanager` — Cloud Resource Manager API (IAM policies)
- `run` — Cloud Run Admin API
- `cloudbuild` — Cloud Build API
- `artifactregistry` — Artifact Registry API

## Cloud Run: Build & Deploy Commands

### One-time setup
```bash
# Create Artifact Registry repo (once)
gcloud artifacts repositories create REPO --repository-format=docker --location=us-central1 --project=PROJECT_ID
```

### Build via Cloud Build (no local Docker needed)
```bash
cd /path/to/app
gcloud builds submit --tag us-central1-docker.pkg.dev/PROJECT_ID/REPO/IMAGE --project=PROJECT_ID
```

### Deploy to Cloud Run
```bash
gcloud run deploy SERVICE \
  --image us-central1-docker.pkg.dev/PROJECT_ID/REPO/IMAGE \
  --platform managed --region us-central1 \
  --allow-unauthenticated --port 8080 \
  --project=PROJECT_ID
```

### Verify public access
```bash
curl -s -o /dev/null -w "HTTP %{http_code}" https://SERVICE_URL
# 200 = public, 403 = needs IAM fix (see Cloud Run IAM section above)
```

### Static site Dockerfile
See `templates/cloudrun-static-dockerfile` and `templates/cloudrun-nginx.conf` for a minimal nginx:alpine setup with SPA fallback and PWA headers.

### Pitfalls
- **Editor role lacks `run.services.setIamPolicy`**: deploy succeeds but IAM is empty → 403. Fix via console (see Cloud Run IAM section).
- **API not enabled**: Cloud Run, Cloud Build, Artifact Registry need enabling. `gcloud services enable` may fail if Service Usage API isn't enabled first.
- **Service Worker + WebSocket**: Service Workers do NOT support `new WebSocket()`. This fails silently. Keep WebSocket connections in the main thread only.
- **Numeric vs string project IDs**: Error messages use numeric ID (541659260074), console URLs use string ID (gen-lang-client-0455851315). Both work in gcloud commands with `--project=`.

When service account lacks `run.services.setIamPolicy` (Editor role doesn't include it), deploy with `--allow-unauthenticated` fails silently — service deploys but IAM policy is empty. Fix via console:

### Step 1: Navigate to Security tab
```python
url = 'https://console.cloud.google.com/run/detail/{REGION}/{SERVICE}/permissions?tab=permissions&project={PROJECT_ID}'
# Open in Edge :9222
```

### Step 2: Toggle "Permitir acesso público" radio button
⚠️ `mat-radio-button.click()` does NOT work on GCP Console. Must manipulate DOM directly:

```javascript
// Radio buttons: _0rif_mat-radio-0-input (public) vs _0rif_mat-radio-1-input (restricted)
const publicInput = document.getElementById('_0rif_mat-radio-0-input');
const restrictedInput = document.getElementById('_0rif_mat-radio-1-input');
const publicRadio = document.getElementById('_0rif_mat-radio-0');
const restrictedRadio = document.getElementById('_0rif_mat-radio-1');

// Set public
publicInput.checked = true;
publicInput.dispatchEvent(new Event('change', {bubbles: true}));
publicRadio.classList.add('mat-radio-checked');

// Unset restricted
restrictedInput.checked = false;
restrictedRadio.classList.remove('mat-radio-checked');
```

### Step 3: Click "Salvar"
"Cancelar" and "Salvar" buttons appear after radio state changes. Click "Salvar" to apply.

**Pitfall:** Even with `--allow-unauthenticated` flag during `gcloud run deploy`, if SA lacks `run.services.setIamPolicy`, the flag is silently ignored. Always verify with:
```bash
curl -s -o /dev/null -w "%{http_code}" https://SERVICE-URL
# 403 = not public, 200 = success
```
