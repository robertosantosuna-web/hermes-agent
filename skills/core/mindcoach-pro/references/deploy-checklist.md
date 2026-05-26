# MindCoach Deploy Checklist (v36+)

Checklist para cada deploy do MindCoach Pro. Evita regressões e loops de tentativa-e-erro.

## Antes do Deploy

- [ ] `SW_VERSION` incrementado em `sw.js` (ex: 6 → 7)
- [ ] `?v=N` nos imports JS atualizado em `index.html`:
  - `<script type="module" src="/core/main.js?v=N">`
  - `navigator.serviceWorker.register('/sw.js?v=N')`
- [ ] Versão visível atualizada: `<span id="app-version">vN</span>`
- [ ] SW força reload SEM busy-check (`controllerchange` + `statechange` → `location.reload()`)
- [ ] `main.js` usa `document.getElementById('main-screen')` como target de renderização (NUNCA `#app`)
- [ ] `data.json` rebuilt: `bash build_data.sh`
- [ ] Python syntax check: `python3 -c "compile(open('chat_api.py').read(), 'chat_api.py', 'exec')"`
- [ ] Novos endpoints adicionados no nginx.conf se necessário (`/api/` já proxy para :8081)

## Deploy

```bash
cd ~/.hermes/mindcoach-pro
gcloud run deploy mindcoach --source . --region us-central1 --allow-unauthenticated --memory=512Mi --project=gen-lang-client-0455851315
```

## Pós-Deploy

- [ ] Verificar app carrega: `curl -s -o /dev/null -w "%{http_code}" https://mindcoach-541659260074.us-central1.run.app/`
- [ ] Verificar data.json: `curl -s https://mindcoach-541659260074.us-central1.run.app/data.json | python3 -c "import json,sys;d=json.load(sys.stdin);print(list(d.keys()))"`
- [ ] Verificar notificações: `curl -s https://mindcoach-541659260074.us-central1.run.app/api/notify`
- [ ] Enviar notificação de teste: `python3 ~/.hermes/scripts/notify_app.py "Deploy" "MindCoach vN no ar" info`
- [ ] Se IAM warning: `gcloud beta run services add-iam-policy-binding mindcoach --region=us-central1 --member=allUsers --role=roles/run.invoker --project=gen-lang-client-0455851315`

## Pitfalls Comuns

- **SW não atualiza**: SW_VERSION não foi incrementado OU busy-check ainda está ativo no index.html
- **Telas vazias**: `main.js` ainda usando `document.getElementById('app')` em vez de `'main-screen'`
- **Dados offline não persistem**: `main.js` não está chamando `cacheSet()` no `onMessage`
- **Notificações não chegam**: polling não foi adicionado ao `main.js` (setInterval 30s no `/api/notify`)
