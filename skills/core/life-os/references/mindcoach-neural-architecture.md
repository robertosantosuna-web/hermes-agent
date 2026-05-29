# MindCoach Neural Architecture v2

## Arquitetura (26/05/2026)

```
📱 App Android (Kotlin/Compose)
    │  HTTP REST (Retrofit)
    ▼
☁️ Cloud Run (mindcoach-541659260074.us-central1.run.app)
    │  chat_api.py (:8081) — 5 endpoints REST
    │  nginx (:8080) — proxy /api/* → :8081
    │
    ▼ (polling HTTP a cada 1min)
🧠 ENTIDADE (entidade_bridge.py)
    │  GET /api/v1/chat?since=N  → lê inbox
    │  POST /api/v1/chat          → responde como coach
    │  GET /api/v1/events         → eventos do ecossistema
    │  GET/POST /api/v1/state     → estado orgânico
```

## Endpoints REST

| Método | Path | Função |
|--------|------|--------|
| POST | /api/v1/chat | App envia mensagem → ENTIDADE responde |
| GET | /api/v1/chat?since=N | App recebe respostas (polling) |
| GET | /api/v1/events | Eventos do ecossistema (GOL, Forex, etc.) |
| POST | /api/v1/event/:id/action | Executar ação em evento |
| GET/POST | /api/v1/state | Estado orgânico (OPERANDO_FOREX, etc.) |

## Deploy

```bash
cd ~/.hermes/mindcoach-pro
gcloud run deploy mindcoach --source . --region us-central1 --allow-unauthenticated --quiet
```

## Compilação APK

```bash
cd ~/Downloads/mindcoach\ \(1\)
export ANDROID_HOME=~/android-sdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
echo "GEMINI_API_KEY=dummy" > .env
./gradlew assembleDebug
# APK em: app/build/outputs/apk/debug/app-debug.apk
```

## Arquivos-chave

- `chat_api.py` — servidor REST Python (roda no Cloud Run :8081)
- `entidade_bridge.py` — processa inbox via HTTP (roda no cron local)
- `EntidadeApi.kt` — cliente Retrofit no app Android
- `MindCoachRepository.kt` — repositório com fallback offline

## Cron da ENTIDADE

```bash
# Job ID: 970a8181cbd2
# Schedule: */1 * * * *
# Ação: python3 ~/.hermes/mindcoach-pro/entidade_bridge.py
```

## Pitfalls

1. **nginx proxy_pass trailing slash**: `proxy_pass http://127.0.0.1:8081;` (sem / no final) preserva o path completo. Com `/` no final, remove o prefixo do location.
2. **Query string no path**: `self.path` inclui query string. Usar `urlparse(self.path).path` para extrair só o path.
3. **Arquivos /tmp/ isolados**: O Cloud Run e a ENTIDADE local não compartilham `/tmp/`. Comunicação deve ser via HTTP, não via arquivos.
4. **NUNCA inventar nomes**: App e bridge não devem conter nomes fictícios de familiares. Usar descrições genéricas ("2 filhas").
