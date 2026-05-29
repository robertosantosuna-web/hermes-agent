# MindCoach Android App — Detalhes de Implementação (26/05/2026)

## Estrutura do Projeto
```
~/Downloads/mindcoach (1)/
├── app/src/main/java/com/example/
│   ├── MainActivity.kt                          # Entry point
│   ├── ui/
│   │   ├── MindCoachViewModel.kt                # Lógica de negócio + estados
│   │   ├── screens/MindCoachScreen.kt           # UI Compose (~445 linhas)
│   │   └── theme/{Color,Theme,Type}.kt          # Tema Material3
│   ├── data/
│   │   ├── model/ChatMessage.kt                 # Room entity
│   │   ├── model/EcosystemEvent.kt              # Room entity (6 categorias)
│   │   ├── local/AppDatabase.kt                 # Room DB
│   │   ├── local/MindDao.kt                     # DAO
│   │   ├── remote/EntidadeApi.kt                # Retrofit — ENTIDADE API
│   │   ├── remote/OtaManager.kt                 # Download + instalação OTA
│   │   ├── remote/GeminiApi.kt                  # LEGADO — não usado
│   │   └── repository/MindCoachRepository.kt    # Orquestrador
│   └── res/xml/file_paths.xml                   # FileProvider paths
├── app/build.gradle.kts                         # Dependências + secrets plugin
└── app/src/main/AndroidManifest.xml             # Permissões + FileProvider
```

## Dependências Chave
- Retrofit + OkHttp + Moshi — REST client
- Room — banco local
- Jetpack Compose + Material3 — UI
- Secrets Gradle Plugin — lê .env para GEMINI_API_KEY

## Fluxo de Dados
```
Usuário digita → ViewModel.sendMessage()
  → Repository.queryMindCoachAi()
    → EntidadeApi.sendMessage() [POST /api/v1/chat]
    → Polling: EntidadeApi.getMessages(since=N) [até 10 tentativas]
      → ENTIDADE (cron) processa inbox
      → Resposta como from=coach
    → Retorna texto para ViewModel
  → UI atualiza chat
```

## Eventos do Ecossistema
Categorias: FOREX, GOL, FINANCES, FAMILIA, TERAPIA (antes também AHGORA)
Status: ACTIVE, DISMISSED, RESOLVED
Ações: AGIR (executa comando) ou IGNORAR (dismiss)

## OTA Flow
1. App abre → ViewModel.init → checkForOtaUpdate()
2. OtaManager.checkForUpdate() → GET /api/v1/ota
3. Compara CURRENT_VERSION (constante) com remote version
4. Se update: banner com BAIXAR
5. DownloadManager → FileProvider → instala

## Pitfalls Específicos do Android
- `Icons.Default.*` do pacote core NÃO tem: TrendingUp, Flight, SelfImprovement, Download, Navigation
- Alternativas: Star, Place, FavoriteBorder, AccountCircle, Refresh, Send
- `RowScope.weight()` requer função com receiver `RowScope`
- `.env` obrigatório mesmo sem usar Gemini (plugin secrets exige)
- `usesCleartextTraffic=true` no Manifest para HTTP (dev)
- CURRENT_VERSION no OtaManager deve ser incrementado a cada release
- chat_api.py versão OTA deve match com CURRENT_VERSION
