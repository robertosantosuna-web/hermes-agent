---
name: dashboard
description: "Dashboard operacional unificado: status de todas as camadas, saúde do sistema, oportunidades, mensagens pendentes, jobs ativos. Um comando = visibilidade total."
version: 1.0.0
author: Roberto Rodrigues
license: MIT
metadata:
  hermes:
    tags: [dashboard, status, monitoring, unified, overview]
    related_skills: [life-os, architecture, system-health, executive-communication, freelancing-automation, whatsapp]
---

# Dashboard — Comando Único de Status

Visibilidade total da ENTIDADE em um comando.

## COMANDO PRINCIPAL

```bash
echo "
════════════════════════════════════════
  ENTIDADE — DASHBOARD $(date '+%d/%m/%Y %H:%M')
════════════════════════════════════════

▸ SISTEMA
  Uptime:  $(uptime -p | cut -d' ' -f2-)
  RAM:     $(free -h | awk '/^Mem:/ {print $3"/"$2}')
  Disco:   $(df -h / | awk 'NR==2 {print $3"/"$2 " (" $5")"}')

▸ SERVIÇOS
  Brave:       $(pgrep -c brave || echo 0) procs
  Telegram:    $(pgrep -c telegram || echo 0) procs
  WhatsApp:    $(pgrep -c whatsapp || echo 0) procs

▸ COMUNICAÇÃO
  Email:       $(himalaya list -f INBOX -u 2>/dev/null | wc -l) não lidos
  Telegram:    verificar send_message
  WhatsApp:    browser web.whatsapp.com

▸ FINANCEIRO
  Oportunidades: freelancing-automation skill
  Plataformas:   Fiverr, 99Freelas, Workana

▸ JOBS
$(hermes cron list 2>/dev/null || echo '  use cronjob tool')

▸ SKILLS CORE
  $(ls ~/.hermes/skills/core/*/SKILL.md 2>/dev/null | wc -l) skills operacionais

════════════════════════════════════════
"
```

## SEÇÕES DO DASHBOARD

### 1. Sistema
- Uptime, RAM, Disco (via system-health)
- Alertas se algum recurso >80%

### 2. Serviços
- Processos críticos rodando (Brave, Telegram, WhatsApp)
- Serviços que deveriam estar ativos

### 3. Comunicação
- Emails não lidos (himalaya)
- Mensagens Telegram pendentes
- Mensagens WhatsApp pendentes

### 4. Financeiro
- Oportunidades ativas (freelancing-automation)
- Propostas pendentes
- Pagamentos aguardando

### 5. Jobs
- Cron jobs ativos e status
- Última execução de cada

### 6. Logs
- Últimos erros (journalctl -p err -n 5)
- Falhas recentes

## ALERTAS (se algo errado)

```
🔴 Sistema: Disco 92% → LIMPAR
🟡 Email: 15 não lidos → TRIAR
🟢 Financeiro: 3 propostas ativas
🔴 Job: health-check falhou → INVESTIGAR
```

## IMPLEMENTAÇÃO

### Via terminal (rápido)
```bash
hermes-dashboard   # se criado como script
```

### Via skill (preferido)
Carregar `dashboard` e executar o check.

### Via cronjob
```bash
# Dashboard diário (8h)
cronjob create \
  --name "Morning Dashboard" \
  --schedule "0 8 * * *" \
  --skills "dashboard,system-health,executive-communication" \
  --prompt "Run full dashboard check. Report system health, unread emails, active proposals, job status."
```

## MINDCOACH PRO — DASHBOARD WEB

### Servidor Desktop (Live Reload)
Serviço: `mindcoach-http.service` → porta 9878
Live reload WebSocket: porta 9879
Quando dados neurais mudam → `build_data.sh` reconstrói `data.json` → browser recarrega.

```bash
systemctl --user status mindcoach-http
# App: http://127.0.0.1:9878
# WS:  ws://127.0.0.1:9879
```

### Deploy Cloud Run
```bash
cd ~/.hermes/mindcoach-pro
bash build_data.sh              # Rebuild data.json
gcloud run deploy mindcoach --source . --region us-central1 --allow-unauthenticated
```

### Dados servidos
- `data.json`: forex bias, backtests, pilares, brain updates, alertas
- Rebuild automático via cron: `30 * * * *` (build_data.sh)
- Index.html carrega `data.json` on load e a cada 5 min

### Pitfalls
- **SW cacheia `/sw.js`**: usar `?v=N` no registro (`sw.js?v=4`) para forçar update
- **`touch` não muda hash**: usar `mtime:size` para detectar mudanças, não md5 do conteúdo
- **WebSocket cross-thread**: `websockets` é async → usar `asyncio.run_coroutine_threadsafe(ws.send(msg), loop)` de threads

Ver referência completa em `references/mindcoach-server.md`.

## EXTENSÕES FUTURAS

- Dashboard HTML servido localmente
- Notificações proativas (Telegram/WhatsApp)
- Gráficos de tendência (crescimento de receita, uso de recursos)
- Integração com freelancing-automation para status de propostas
