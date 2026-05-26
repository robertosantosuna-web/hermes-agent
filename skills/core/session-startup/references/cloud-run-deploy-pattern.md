# Cloud Run Deploy Pattern

## MindCoach Pro — Cloud Run

**URL:** `https://mindcoach-541659260074.us-central1.run.app`
**Projeto GCP:** `gen-lang-client-0455851315`
**Conta de serviço:** `hermes-deploy@gen-lang-client-0455851315.iam.gserviceaccount.com`
**Região:** `us-central1`

## Deploy rápido (sem Docker local)

```bash
cd /home/roberto/.hermes/mindcoach-pro
gcloud run deploy mindcoach --source . --region us-central1 --allow-unauthenticated
```

O `--source .` aciona Cloud Build remotamente (não precisa de Docker local). Build + deploy ~3-5 min.

## Estrutura do app

- **Nginx + estático:** Dockerfile copia tudo pra `/usr/share/nginx/html`, nginx.conf em `/etc/nginx/conf.d/`
- **Porta:** 8080 (Cloud Run exige)
- **Service Worker:** `/sw.js` com headers `no-cache` (nginx.conf)
- **JS modules:** `/core/` com headers `no-cache`

## Service Worker — v5 (25/05/2026)

⚠️ **v5:** Chat input adicionado ao `main.js`. Bridge processa `chat_message` → inbox. HTTP bind 0.0.0.0 pra acesso mobile via WiFi. Cloud Run redeploy necessário após mudanças no core JS.

**Solução v4/v5:**
- Sem `cache.addAll` no install — cache só populado via fetch (dinâmico)
- `skipWaiting()` no install para ativação imediata
- `clients.claim()` + notificação de reload no activate
- Kill switch via `sw_reset` message
- Index.html registra SW com `updatefound` + polling a cada 1h

## Teste de deploy

```bash
# Verificar versão
curl -s https://mindcoach-541659260074.us-central1.run.app/sw.js | head -3

# Forçar reload do SW no browser
# Abrir DevTools → Application → Service Workers → "Update" ou "Unregister"
```

## ⚠️ /tmp é VOLÁTIL (25/05/2026)

Cloud Run containers são efêmeros. `/tmp/` é apagado em:
- Todo redeploy (nova revision)
- Escalonamento para zero (cold start)
- Substituição de instância

**NUNCA usar `/tmp/` para estado que precisa sobreviver a deploys.** O chat MindCoach armazenava mensagens em `/tmp/mindcoach_chat.json` — cada deploy apagava tudo e o `last_id` local ficava stale.

**Fix:** WebSocket bridge local (mindcoach_bridge.py :9877) — estado no filesystem local, não no Cloud Run.

## Arquitetura do Chat (v21)

```
Mobile (Cloud Run) → WebSocket (wss://tunnel) → Bridge (:9877) → inbox.json
                                                      ↑
                                               Cron (1min) → send_command → broadcast
```

### Componentes UI (DUAS telas diferentes):
- **main.js (Coach IA)** — recebe `type:'render'` e renderiza chat com input
- **index.html (💬 bubble)** — painel separado que NÃO recebe `type:'render'`

**Pitfall (v19):** Broadcast vai para main.js, mas usuário olhava index.html. Resposta invisível.
**Fix (v21):** 💬 agora chama `window.openHermesChat()` que navega para o Coach IA.

## ✅ Deploy Checklist (AP-14)

Antes de deployar QUALQUER fix no MindCoach:
1. [ ] Mapear fluxo completo: send → receive → process → respond → display
2. [ ] Identificar TODOS os breakpoints
3. [ ] Verificar qual componente UI vai receber a resposta  
4. [ ] Testar round-trip manualmente
5. [ ] Corrigir TODOS os bugs de uma vez
6. [ ] Deployar UMA vez

## Pitfalls

- **Docker não instalado localmente:** usar `gcloud run deploy --source .` (Cloud Build remoto)
- **SW velho no mobile:** limpar dados do site (Settings → Site Settings → Clear Data) OU abrir em aba anônima
- **nginx.conf no-cache essencial:** sem headers `no-cache` no `/sw.js`, browser pode ignorar nova versão por 24h+
- **/tmp volátil:** nunca armazenar estado que precise sobreviver a deploys
- **UI components desconectados:** main.js e index.html têm handlers WebSocket diferentes — verificar qual está ativo
