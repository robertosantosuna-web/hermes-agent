---
name: gcp-deployment
description: Deploy de aplicações no Google Cloud Platform — autenticação, Cloud Run, Artifact Registry, Cloud Build.
version: 1.1.0
author: Roberto Rodrigues
metadata:
  hermes:
    tags: [gcp, deploy, cloud-run, docker, auth]
---

# GCP Deployment

Deploy de apps containerizadas no GCP via gcloud CLI.

## Autenticação

### ⚠️ gcloud v569+ mudou o fluxo `--no-browser`

Versões antigas imprimiam URL → visitar no browser → colar código. v569+ usa `--remote-bootstrap` que exige rodar o comando NA máquina com browser:

```bash
# NÃO funciona mais como antes:
gcloud auth login --no-browser
# → imprime "gcloud auth login --remote-bootstrap=URL"
# → espera a SAÍDA desse comando rodado em outra máquina
```

**Pitfalls:**
- Cada chamada gera novo PKCE `code_challenge` — códigos de verificação NÃO são reutilizáveis entre chamadas
- Google bloqueia browsers headless (Chrome headless, CDP) para OAuth: "Esse navegador ou app pode não ser seguro"
- `gcloud auth application-default login --no-browser` tem o mesmo comportamento

### Caminhos de auth viáveis

| Método | Interativo? | Funciona headless? |
|--------|-------------|-------------------|
| `gcloud auth login` (browser) | Sim | ❌ Precisa de browser real |
| `gcloud auth login --no-browser` (v569+) | Sim | ❌ Precisa de outra máquina com browser |
| Service account key JSON | Não | ✅ Totalmente headless |
| Workload Identity Federation | Não | ✅ (requer configuração prévia) |

### Service Account Key (recomendado para headless)

```bash
# 1. Criar SA no console: IAM → Service Accounts → Criar
#    Role: Editor (ou mais restrito conforme necessidade)
# 2. Baixar JSON key
# 3. Autenticar:
gcloud auth activate-service-account --key-file=/path/to/key.json --project=PROJECT_ID

# 4. Verificar:
gcloud auth list
gcloud config set project PROJECT_ID
```

### Instalação do gcloud CLI

```bash
# Snap (mais simples)
sudo snap install google-cloud-cli --classic

# Verificar
gcloud version
gcloud auth list
```

## Deploy no Cloud Run

### Pré-requisitos
- Dockerfile na raiz do projeto
- `.dockerignore` configurado
- gcloud autenticado com projeto correto

### Deploy manual

```bash
# Build + push + deploy
gcloud run deploy SERVICE_NAME \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --project PROJECT_ID
```

### Docker Compose local → Cloud Run

Docker Compose não é suportado diretamente no Cloud Run. Converter para:
- Serviço único com Dockerfile multi-stage, OU
- Múltiplos serviços Cloud Run (um por container)

### Regiões com free tier
- `us-central1` (Iowa)
- `us-east1` (South Carolina)
- `us-west1` (Oregon)

## GCP Console Automation via CDP (porta 9222)

Quando o service account não tem permissões de IAM/Admin, usar o browser REAL do Roberto (Edge CDP porta 9222, NÃO 9223 que é o brain browser headless) para operações que exigem Owner:

```python
import json, websocket, urllib.request, time

# Listar abas autenticadas
tabs = json.loads(urllib.request.urlopen('http://localhost:9222/json/list').read())
# Procurar por console.cloud.google.com → é o browser com sessão Google ativa

# Abrir nova aba autenticada
req = urllib.request.Request(
    'http://localhost:9222/json/new?https://console.cloud.google.com/...',
    method='PUT'
)
tab = json.loads(urllib.request.urlopen(req).read())
WS_URL = tab['webSocketDebuggerUrl']

def cdp(method, params=None):
    ws = websocket.create_connection(WS_URL, timeout=15)
    ws.send(json.dumps({"id": 1, "method": method, "params": params or {}}))
    resp = json.loads(ws.recv())
    ws.close()
    return resp
```

### Operações comuns via CDP no GCP Console

**Criar Service Account:**
1. Navegar para `iam-admin/serviceaccounts?project=PROJECT_ID`
2. Clicar "Criar conta de serviço" (BUTTON) — usar busca por textContent
3. Preencher nome via `Input.dispatchKeyEvent` com `type: "char"` (Material Design ignora `.value =`)
4. Clicar "Criar e continuar"
5. Role selector: elemento `cfc-select-dual-column` — clicar, depois achar "Editor" em `.mdc-list-item__primary-text`, clicar no `mat-option` pai
6. Clicar "Continuar" → "Concluído"
7. Actions menu: botão com `aria-label="Menu de ações da conta de serviço"` → "Gerenciar chaves"
8. "Adicionar chave" → "Criar nova chave" → JSON selecionado por padrão → "Criar"
9. Download vai para `~/Downloads/.org.chromium.Chromium.*` (temp) → copiar e renomear

**Enable APIs:**
1. Navegar para `console.developers.google.com/apis/api/API_NAME/overview?project=NUM`
2. Clicar botão "Ativar" (BUTTON, `aria-label="ativar esta API"`)
3. Aguardar "Carregando..." sumir

**Set IAM Policy (permitir acesso público no Cloud Run):**
1. Navegar para `console.cloud.google.com/run/detail/REGION/SERVICE/permissions?tab=permissions`
2. Clicar aba "Segurança" (A tag)
3. Radio buttons: `#_0rif_mat-radio-0-input` (public) vs `#_0rif_mat-radio-1-input` (restricted)
4. ⚠️ `mat-radio-button.click()` NÃO funciona — precisa manipular DOM direto:
   ```js
   input.checked = true;
   input.dispatchEvent(new Event('change', {bubbles: true}));
   matRadio.classList.add('mat-radio-checked'); // elemento pai
   // Desmarcar o outro:
   otherInput.checked = false;
   otherRadio.classList.remove('mat-radio-checked');
   ```
5. Clicar "Salvar" que aparece após mudança

## Cloud Build (sem Docker local)

Quando Docker não está instalado na máquina, usar Cloud Build:

```bash
# Build remoto + push para Artifact Registry
gcloud builds submit --tag LOCATION-docker.pkg.dev/PROJECT_ID/REPO/IMAGE --project=PROJECT_ID

# Depois deploy no Cloud Run
gcloud run deploy SERVICE \
  --image LOCATION-docker.pkg.dev/PROJECT_ID/REPO/IMAGE \
  --platform managed --region REGION \
  --allow-unauthenticated --port 8080 \
  --project PROJECT_ID
```

### Criar Artifact Registry repo
```bash
gcloud artifacts repositories create REPO_NAME \
  --repository-format=docker --location=us-central1 \
  --project=PROJECT_ID
```

## Cloudflare Tunnel (expor serviços locais)

Para expor WebSocket/HTTP local (ex: bridge na porta 9877) para a internet sem abrir portas no roteador:

```bash
# Instalar
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /tmp/cloudflared
chmod +x /tmp/cloudflared && sudo mv /tmp/cloudflared /usr/local/bin/

# Quick tunnel (sem conta Cloudflare) — URL aleatória, muda a cada restart
cloudflared tunnel --url http://localhost:9877
# → https://random-name.trycloudflare.com

# Systemd para persistir
# ~/.config/systemd/user/cloudflared-mindcoach.service:
# [Service] ExecStart=/usr/local/bin/cloudflared tunnel --url http://localhost:9877
# Restart=always
```

### URL dinâmica para WebSocket

URLs `trycloudflare.com` MUDAM a cada restart do túnel. Padrão para apps que precisam conectar:

1. Arquivo estático `/bridge-url` no Cloud Run contendo a URL atual do túnel WS
2. App faz `fetch('/bridge-url')` pra descobrir endpoint antes de conectar WebSocket
3. Script `update_bridge_config.py` (ver [scripts/update_bridge_config.py](scripts/update_bridge_config.py)) extrai URL do `journalctl --user -u cloudflared-*` e atualiza o arquivo.

### Verificação do túnel
```bash
# WebSocket upgrade test
curl -s -H "Upgrade: websocket" -H "Connection: Upgrade" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  -o /dev/null -w "HTTP %{http_code}\n" https://TUNNEL.trycloudflare.com
# HTTP 426 = WebSocket upgrade required → funcionando
# HTTP 530 = Cloudflare erro (túnel caiu/propagando)
```

## PWA no Cloud Run

Service Workers em apps deployados precisam de atenção extra:

### Cache versionado
- Usar nome de cache com versão (`mindcoach-v3`) e limpar versões antigas no `activate`
- **cache-first quebrado** → usar **network-first com cache fallback** pra evitar servir versão antiga
- Após deploy, Service Worker antigo pode servir cache stale — `skipWaiting()` + `clients.claim()` + `postMessage('sw_updated')`

### WebSocket em Service Worker
**Service Workers NÃO suportam WebSocket.** Código como `new WebSocket(...)` dentro de `sw.js` falha silenciosamente e pode bloquear o SW. Manter WebSocket apenas na página principal (module script). SW deve fazer apenas: cache, fetch proxy, push notifications.

### Offline-first
App deve funcionar SEM WebSocket:
- Mostrar UI offline amigável (não tela branca nem erro)
- Dados via IndexedDB como fallback (`getLatest()` do cache local)
- Indicador de status sutil (`online`/`offline`), não bloqueante
- WebSocket opcional — tentar conectar em background, não travar UI

## Pitfalls

1. **Cloud Run NÃO suporta docker-compose**: Cada serviço vira um Cloud Run service separado. Volumes não persistem — usar Cloud Storage ou Firestore.
2. **Cold start**: primeiro request após inatividade tem latência extra (500ms-2s). Configurar `min-instances=1` elimina mas custa mais.
3. **WebSocket no Cloud Run**: WebSocket é suportado mas requer HTTP/2 desabilitado e timeout de request alto (>300s).
4. **Porta padrão**: Cloud Run expõe porta 8080 por padrão. Seu container precisa ouvir em `$PORT` (variável de ambiente).
5. **Limite de 32MB por request**: payloads maiores precisam de streaming ou chunked upload.
6. **gcloud v569 auth**: tentar `--no-browser` em máquina sem browser real é perda de tempo — usar service account key direto.
7. **Service Account Editor NÃO tem `run.services.setIamPolicy`**: deploy com `--allow-unauthenticated` falha silenciosamente (IAM policy vazia). Usar console do Roberto (CDP :9222) ou dar role `roles/run.admin` à SA.
8. **Billing obrigatório**: Cloud Run, Cloud Build e Artifact Registry exigem billing account ativa no projeto — sem ela, `gcloud services enable` falha com `UREQ_PROJECT_BILLING_NOT_FOUND`.
9. **Material Design no GCP Console**: `.click()` em `mat-radio-button` não funciona. Precisa manipular `input.checked` + `dispatchEvent('change')` + toggle `mat-radio-checked` class.
10. **trycloudflare.com URLs são efêmeras**: cada restart do `cloudflared` gera nova URL. Usar padrão de config dinâmica (`/bridge-url`). Para produção, usar named tunnel com domínio próprio.
11. **Service Worker + WebSocket = erro silencioso**: SW não suporta WebSocket API. Remover qualquer `new WebSocket()` do `sw.js`.
12. **nginx.conf port fixa quebra no Cloud Run**: Cloud Run injeta `$PORT` (default 8080). nginx precisa ouvir em 8080, não 80.