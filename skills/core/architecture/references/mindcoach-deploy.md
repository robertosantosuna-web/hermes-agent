# MindCoach Pro — Deploy Pipeline

PWA dashboard conectada à rede neural. Cloud Run + nginx estático.

## Arquitetura

```
data.json (build)  →  Cloud Run (nginx)  →  MindCoach App (PWA)
                              ↕
                    Telegram Bot API (chat)
                              ↕
                      Hermes Agent (responde)
```

- **URL**: `https://mindcoach-541659260074.us-central1.run.app`
- **Source**: `~/.hermes/mindcoach-pro/`
- **Bridge**: `mindcoach-bridge.service` (WebSocket ws://localhost:9877)
- **Chat**: Telegram Bot → chat_id `845735429`

## Deploy (Cloud Run)

```bash
cd ~/.hermes/mindcoach-pro
bash build_data.sh              # Gera data.json com dados neurais
gcloud run deploy mindcoach \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

## Service Worker Kill Switch (v4)

Problema: SW antigo cacheava JS/HTML no `install` (`cache.addAll`) — mobile ficava preso em versão velha.

Solução: NÃO cachear no install. Network-first com cache dinâmico (popula só depois de servido). Kill switch via `sw_reset` limpa todos os caches e força reload em todos os clients.

## Injeção de Dados Neurais

Script `build_data.sh` coleta de:
- `weekly_bias.json` — viés forex semanal
- `crt_choch_backtest.json` — resultados de backtest
- `brain_context.json` — knowledge updates do cérebro
- `mindcoach_state.json` — estado dos pilares
- `agenda.json` — compromissos

## Chat com Hermes

Mensagens enviadas via Telegram Bot API. Offline: salvas em localStorage e enviadas quando reconectar.

## Pitfalls

- **Túnel Cloudflare expira**: fallback para `data.json` estático
- **NÃO cachear JS/HTML no SW install**: usar network-first + cache dinâmico
- **IAM no Cloud Run**: service account sem `setIamPolicy` — deploy com `--allow-unauthenticated` só se IAM já existe
