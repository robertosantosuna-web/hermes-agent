---
name: brain-architecture
description: "Arquitetura cognitiva multi-agente da ENTIDADE — skill primária do cérebro bi-neural. Inclui: mapeamento cerebral, Tálamo (message router), Córtex System (Visual/Audio/Motor APIs), Local Brain (Ollama), Digital Twin, Rede Neural (Synapse Engine + KB), Feature Absorption Protocol, design de novos agentes cognitivos. Absorveu: bi-neural-brain, cortex-system, local-brain (2026-05-24)."
version: 2.4.0
author: Roberto
metadata:
  hermes:
    tags: [brain, cognitive, multi-agent, thalamus, digital-twin, architecture, bot-bridge, trigger-engine]
    related_skills: [architecture, life-os, operational-intelligence, financial-intelligence, system-health]
---
# Brain Architecture — Cérebro Bi-Neural da ENTIDADE

**brain-architecture é a skill primária do conjunto cerebral — autoridade definida em `~/.hermes/brain_governance.md`. Absorveu `bi-neural-brain`, `cortex-system` e `local-brain` em 2026-05-24. v2.3: Bot↔Brain Bridge integrado, Neural Assimilate ajustado para 4H, pitfalls de symlink/cron output dirs adicionados.**

Arquitetura cognitiva inspirada no cérebro humano. Cada região cerebral = um sub-agente especializado. Hermes Agent = Córtex Pré-Frontal (núcleo decisor).

## MAPEAMENTO CEREBRAL

### Sistema Sensorial (Input)

| Região Cerebral | Agente | Função | Fonte de Dados |
|----------------|--------|--------|----------------|
| Córtex Visual (Occipital) | `chart-vision`, `browser-eye` | Gráficos forex, DOM, screenshots | MT5, browser CDP |
| Córtex Auditivo (Temporal) | `audio-transcriber` | Voz → texto | Telegram/WhatsApp áudio |
| Somatossensorial (Parietal) | `system-health`, `market-pulse` | CPU/RAM/disco, preço real-time | psutil, yfinance |

### Sistema de Retransmissão (Gateway)

| Região | Componente | Função |
|--------|-----------|--------|
| **Tálamo** | `~/.hermes/thalamus/router.py` | Filtra e classifica TODO input. Decide o que chega ao Córtex. |
| Formação Reticular | `monitor.py`, `forex_check.py` | Scripts no_agent que só acordam o sistema com alerta real |

### Sistema Límbico (Memória/Prioridade)

| Região | Agente | Função |
|--------|--------|--------|
| **Amígdala** | `threat-detector` | Classifica urgência: "Isso é grave?" |
| **Hipocampo** | `memory-consolidator` | Consolida padrões, trade history, memória semanal |
| **N. Accumbens** | `reinforcement-learner` | Aprende com WIN/LOSS, ajusta scores de pares forex |

### Córtex Pré-Frontal (Executivo = Hermes Agent)

| Sub-região | Função |
|-----------|--------|
| Dorsolateral PFC | Working memory, planejamento, decomposição de tarefas |
| Orbitofrontal PFC | Decisão, avaliação risco/recompensa |
| Cíngulo Anterior | Detecção de erro, resolução de conflito entre agentes |

### Sistema Motor (Output)

| Região | Agente | Ação |
|--------|--------|------|
| Córtex Motor | `mt5-executor`, `telegram-sender`, `email-sender` | Executa trades, envia mensagens |
| Cerebelo | `trade_closer.py`, validação pós-ação | Feedback loop: "A ação realmente aconteceu?" |
| Tronco Cerebral | Cron jobs essenciais | Health check, resiliência, memory consolidation |

## TÁLAMO — MESSAGE ROUTER

O Tálamo é a primeira linha de defesa. NADA chega ao Córtex sem passar por ele.

### Localização
```
~/.hermes/thalamus/
├── __init__.py      # Package init
├── schema.py        # Formato Event + enums (EventType, Urgency, Source)
├── filters.py       # Pipeline de 8 filtros com keyword scoring
└── router.py        # Core: Thalamus class + route()
```

### API
```python
from thalamus.router import route

event = route("email", "Problema no saque", metadata={"from": "cliente@x.com"})
# → event.type=FINANCE, event.urgency=L3, event.should_wake=True
```

### Pipeline de Classificação

| Filtro | EventType | Urgency | Wake Córtex? |
|--------|-----------|---------|-------------|
| Spam | SPAM | L1 | ❌ descartado |
| **Error sanitization (v2.1)** | **SPAM** | **L1** | **❌ descartado (injection bloqueada)** |
| Trade executado | FINANCE | L3 | ✅ |
| Erro crítico sistema | SYSTEM | L3 | ✅ |
| Email de cliente | SOCIAL | L2 | ✅ |
| Warning sistema | SYSTEM | L2 | ✅ |
| Alerta forex | FINANCE | L1/L2 | varia |
| Health check OK | SYSTEM | L1 | ❌ ignorado |
| Newsletter | SOCIAL | L1 | ❌ ignorado |

### Log
`~/.hermes/thalamus/event_log.json` — array JSON com todos os eventos, limitado a 100k entradas.

## DIGITAL TWIN — EVOLUÇÃO CONTÍNUA

Arquitetura preparada para integrar dados de smartphone, smartwatch, VR e dispositivos futuros.

### Princípio Plug-and-Play
```
[DISPOSITIVO] → [SENSOR AGENT] → [TÁLAMO] → [CÓRTEX]
                                       ↑
                            classifica por tipo, urgência, relevância
                            independente da origem
```

### Dispositivos Mapeados

| Dispositivo | Dados | Status |
|------------|-------|--------|
| 📱 Smartphone | Tempo de tela, localização, notificações, chamadas | Futuro |
| ⌚ Smartwatch | FC, HRV, SpO2, sono, passos | Futuro |
| 🥽 VR/AR | Eye tracking, atenção, postura | Futuro |
| 💻 PC | Browser, logs, métricas | ✅ Atual |
| 📧 Email | Volume, remetentes, tom | ✅ Atual |
| 💬 Chat | Telegram, WhatsApp | ✅ Atual |

### Camadas de Coaching

| Nível | Tipo | Exemplo |
|-------|------|---------|
| N1 — Consciência | Insight passivo | "Você passou 18h no Instagram esta semana" |
| N2 — Nudge | Sugestão no momento | "São 23:30 e você está no Instagram há 40min" |
| N3 — Intervenção | Bloqueio + redirecionamento | Bloquear app após cota diária |

## DESIGN DE NOVOS AGENTES

### Template para Criar um Agente Cognitivo

1. **Identificar a região cerebral correspondente** (qual função cognitiva?)
2. **Definir formato de evento** (schema.py)
3. **Adicionar filtro no Tálamo** (filters.py) — como classificar esse input?
4. **Criar script no_agent** se for monitoramento passivo (zero tokens)
5. **Criar cron job** para execução periódica
6. **Conectar ao Córtex** — o que deve acordar o Hermes Agent?

### Agentes Implementados (25/05/2026 — v2.2)

| Região | Script | Cron Job | Schedule | Status |
|--------|--------|----------|----------|--------|
| **Amígdala** | `scripts/amygdala.py` | `853991c6f44b` | */15 min | ✅ Ativo |
| **Cerebelo v2.1** | `scripts/cerebellum.py` | `6050427dfccd` | */5 min seg-sex | ✅ Ativo |
| **N. Accumbens** | `scripts/n_accumbens.py` | `6ae254c0b104` | 0 */4 * * * (a cada 4h) | ✅ Ativo (25/05) |
| **Hipocampo** | `scripts/hippocampus.py` | `b0b848ba83d1` | 0 */6 * * * (a cada 6h) | ✅ Ativo (25/05) |
| **Brain Research** | `scripts/brain_research.py` | `0554b5690934` | 0 */4 * * * (a cada 4h) | ✅ Ativo (25/05) |
| **Executive v2** | `executive/brain.py` | `fcdf34b789c0` | */5 min seg-sex | ✅ Ativo |
| **Synapse Engine** | `scripts/synapse_engine.py` | `5e4e461f6c80` | 0 */4 * * * (a cada 4h) | ✅ Ativo (25/05) |
| **Brain Channel** | `scripts/brain_channel.py` | — | sob demanda | ✅ Novo |
| **Brain Gateway** | `scripts/brain_gateway.py` | `c34bd14a25a9` | */2 min | ✅ Novo |
| **Neural Assimilate** | `scripts/neural_assimilate.py` | `671421d584da` | 0 */4 * * * (a cada 4h) | ✅ Ativo |
| **Lore Sync** | `scripts/lore.py` | `34bc8cfadb26` | trigger-based | ⚡ Trigger |
| **Memory Mapper** | `scripts/memory_mapper.py` | `ecc0720f402d` | 06:00 diário | ✅ Ativo |
| **Bot↔Brain Bridge** | `scripts/brain_bot_bridge.py` | — | via bot cron | ✅ Ativo |
| **Neural Trigger Engine** | `scripts/neural_trigger.py` | — | Executive */5 min | ⚡ Core (25/05) |
| **Auto-Trigger** | `scripts/auto_trigger.py` | — | chamado por eventos | ⚡ Core (25/05) |
| **Brain Telegram Daemon** | `scripts/brain_telegram_daemon.py` | systemd | resposta imediata | ✅ Ativo (25/05) |

**⚠️ ARQUITETURA TRIGGER-BASED (25/05/2026):** Amygdala, N. Accumbens, Hippocampus, Brain Research e Synapse Engine tiveram seus cron jobs PAUSADOS. Agora são acordados sob demanda pelo Neural Trigger Engine via Executive (*/5 min). Apenas Cerebellum (segurança), Executive (orquestrador), Brain Gateway (resposta real-time) e Neural Assimilate (sinc Agent 4h) mantêm cron fixo.

Todos os scripts são **no_agent** — zero tokens. Output via `~/.hermes/cron/output/<job_id>/` (NÃO diretórios nomeados — usar os IDs de cron job para achar outputs).

### Pendentes
- [ ] **Audio-transcriber** — voz → texto para Telegram/WhatsApp
- [ ] **Digital Twin devices** — smartphone, smartwatch, VR integration
- [x] ~~**Browser interno** — Brave CDP headless :9223 (systemd hermes-brain-browser, controller scripts/brain_browser.py)~~
- [x] ~~**TradingView** — logado Google OAuth, fonte primária de dados forex, Bar Replay funcional~~
- [x] ~~**Chart Visual Learner** — ativar quando MT5 reconectar no Xvfb :99~~

### Novos Componentes (23/05)

| Componente | Script | Função |
|-----------|--------|--------|
| **Brain Browser** | `scripts/brain_browser.py` | Navegador CDP para scripts do cérebro (navigate, content, screenshot, eval) |
| **Chart Analyzer** | `scripts/tv_chart_analyzer.py` | Controle do TradingView: pairs, Bar Replay, screenshots, OHLC |
| **Chart Scanner** | `scripts/tv_chart_scanner.sh` | Cron */30 min: screenshot automático de 5 pares M15 |
| **Degraded Learner** | `scripts/chart_pattern_degraded.py` | Estudo offline: templates numéricos, similaridade cross-pattern, archetypes |
| **FVG Simulation** | `scripts/fvg_simulation.py` | Backtest massivo de FVG em qualquer par com filtros configuráveis |
| **Calendar Monitor** | `scripts/brain_calendar_monitor.py` | Agenda via Google Calendar CDP + WhatsApp. Ver: `references/gcp-cdp-automation.md` |

### Pilar Unificado Mental+Comportamental+Social (24/05)

| Componente | Script | Cron | Schedule | Status |
|-----------|--------|------|----------|--------|
| **Calendar Monitor** | `scripts/brain_calendar_monitor.py` | `56b2f5d980cb` | 06:00 diário | ✅ Ativo |
| **Calendar Check tarde** | `scripts/brain_calendar_monitor.py` | `e4352927a5f6` | 16:00 diário | ✅ Ativo |
| **Mental Morning** | `scripts/mental_morning.py` | `b0001247db35` | 07:00 diário | ✅ Ativo |
| **Mental Evening** | `scripts/mental_evening.py` | `0d89cce682e1` | 21:00 diário | ✅ Ativo |
| **Behavioral Tracker** | `scripts/behavioral_check.py` | — | via mental check-ins | ✅ Ativo |
| **Social Tracker** | `scripts/social_check.py` | — | via mental check-ins | ✅ Ativo |
| **Unified Dashboard** | `scripts/unified_dashboard.py` | — | via mental check-ins | ✅ Ativo |

Calendar Monitor: detecta compromissos via WhatsApp CDP + Google Calendar (OAuth pendente),
extrai datas em linguagem natural ("amanhã 14h", "segunda 10h"), gera agenda 7 dias com
alerta de conflitos. Output em `~/.hermes/brain/agenda.json` + Knowledge Bridge.

## NEURAL TRIGGER ENGINE — Ativação por Gatilhos (v2.3, 25/05/2026)

Arquitetura que substitui cron jobs fixos por ativação sob demanda via rede neural.
Módulos ficam dormentes até que um evento relevante os acorde.

### Pipeline

```
  EVENTO (trade, threat, FVG, research)
         │
         ▼
  auto_trigger.py → escreve gatilho
         │
         ▼
  neural_triggers.json (fila de pendentes)
         │
         ▼
  Executive (*/5 min) → neural_trigger.py check
         │
         ▼
  Acorda módulo alvo → processa → volta dormir
```

### Scripts

**`scripts/neural_trigger.py`** — Engine central
```bash
neural_trigger.py                        # Status (pendentes/histórico)
neural_trigger.py check                  # Executive: processa pendentes
neural_trigger.py trigger <mod> <reason> # Escreve gatilho
neural_trigger.py stats                  # JSON stats
```

**`scripts/auto_trigger.py`** — Disparado por eventos
```bash
auto_trigger.py trade "WIN USDJPY"      # → N. Accumbens
auto_trigger.py fvg "EURUSD 93 gaps"    # → Hippocampus
auto_trigger.py threat "disk 92%"       # → Amygdala
auto_trigger.py research "new finding"  # → Brain Research
auto_trigger.py day_end                 # → Synapse Engine
```

### Mapeamento de Gatilhos

| Evento | Quem Dispara | Módulo Alvo |
|--------|-------------|-------------|
| Trade WIN/LOSS | `trade_tracker.py` | N. Accumbens |
| Novo conhecimento absorvido | `knowledge_bridge.py` | Brain Research |
| Threat detectado | `thalamus/router.py` | Amygdala |
| FVGs detectados | `brain_signal_generator.py` | Hippocampus |
| Fim do dia/semana | Agente (manual) | Synapse Engine |

### Módulos que Mantêm Cron Fixo

| Módulo | Cron | Motivo |
|--------|------|--------|
| Cerebellum | */5 min | Segurança — validação de comandos perigosos |
| Executive | */5 min | Infraestrutura — processa triggers + detecta stalls |
| Brain Gateway | */2 min | Resposta real-time (fallback, se daemon parar) |
| Neural Assimilate | */4h | Sinc Agent↔Brain (token — até ROI do forex) |

### Pitfalls do Trigger Engine

- **Dedup 4h**: `auto_trigger.py` ignora triggers duplicados (mesmo módulo + mesma razão) nas últimas 4 horas para evitar spam.
- **Limite 20 pendentes**: triggers excedentes vão para history com status `overflow`.
- **Executive precisa de `HERMES_DIR` correto**: o path no `tick()` do Executive é `HERMES_DIR / 'scripts' / 'neural_trigger.py'`, NÃO `HERMES` (variável inexistente).
- **Módulos trigger-based NÃO têm cron**: se o Executive parar, eles NUNCA serão acordados. Monitorar Executive é crítico.

Quando o Hermes Agent lança uma nova versão com features absorvidas de ferramentas externas
(Claude Code, Codex, OpenCode, ruff, etc.), o cérebro deve absorvê-las também. Este protocolo
define COMO fazer isso de forma sistemática.

### Passo a Passo

1. **Identificar** — `grep -i "claude\|ruff\|inspired\|absorb" RELEASE_v*.md` no repo do Hermes.
   Encontrar features explicitamente creditadas a ferramentas externas.

2. **Mapear para região cerebral** — qual componente do cérebro lida com essa classe de problema?

| Tipo de Feature | Região Cerebral | Arquivo |
|----------------|----------------|---------|
| Segurança de comandos | **Cerebelo** (validação) | `scripts/cerebellum.py` |
| Filtro/sanitização de input | **Tálamo** (router) | `thalamus/filters.py` |
| Validação de código/sintaxe | **Brain Code Validator** | `scripts/brain_code_validator.py` |
| Aprendizado/reforço | **N. Accumbens** | `scripts/n_accumbens.py` |
| Memória/padrões | **Hipocampo** | `scripts/hippocampus.py` |
| Urgência/threat | **Amígdala** | `scripts/amygdala.py` |
| Execução/ação | **Córtex Motor** | `cortex/motor.py` |

3. **Implementar** — código Python puro, zero tokens, zero dependências novas.
   Adicionar a função/validação no script existente. Não criar script novo a menos que
   seja uma capacidade totalmente nova (ex: `brain_code_validator.py`).

4. **Adicionar anti-padrão** no `self-correction` (AP-NN) para evitar regressão comportamental.

5. **Atualizar skills** — `brain-architecture`, `bi-neural-brain`, `self-correction`.

6. **Documentar** — criar `references/brain-vX.Y-upgrade.md` com o que foi absorvido,
   de onde veio, e o impacto.

7. **Validar** — rodar o script modificado (`python3 scripts/cerebellum.py`), verificar
   que não quebrou, rodar `brain_code_validator.py --all`.

### Exemplo: Upgrade v2.1 (23/05/2026)

| Absorção | Origem | Feature Hermes | Aplicado ao Cérebro |
|----------|--------|---------------|-------------------|
| Dangerous command detection | Claude Code | "3 bypasses closed" | Cerebelo: 13 padrões regex |
| Error sanitization | Claude Code | "tool-error sanitization" | Tálamo: filter_error_sanitization (pos 2) |
| LSP semantic diagnostics | ruff | "LSP diagnostics on write_file/patch" | Brain Code Validator: AST validation |

### Pitfalls

- NÃO criar dependências externas (ruff CLI, LSP servers) — usar Python stdlib (ast, re)
- NÃO usar tokens — implementações são scripts no_agent
- NÃO duplicar filtros — se o Tálamo já tem um filtro similar, estender, não criar outro
- SEMPRE rodar `brain_code_validator.py --all` depois de modificar scripts

## ARQUITETURA DE COMUNICAÇÃO (v2.2 — 25/05/2026)

### Canal Direto Agent ↔ Brain

Sistema de inbox/outbox assíncrono. Script: `scripts/brain_channel.py`.

```
Agent ──send──→ brain_inbox.json → Executive lê (5 min) → processa → brain_outbox.json → Agent read
```

**Comandos:**
```bash
brain_channel.py send "pergunta"   # Agent → Brain
brain_channel.py read              # Agent ← Brain
brain_channel.py status            # Status do canal
brain_channel.py log 20            # Histórico
```

**Arquivos:** `~/.hermes/brain_inbox.json`, `~/.hermes/brain_outbox.json`, `~/.hermes/brain_channel.log`
**Integração:** `executive/brain.py` lê inbox no início de cada tick, responde automaticamente.

### Brain Gateway — Processador Independente (v2.2)

Gateway que processa mensagens direto do usuário SEM passar pelo Agent (Córtex).
Zero tokens — consulta apenas a knowledge base local do cérebro.

Script: `scripts/brain_gateway.py` | Cron: `c34bd14a25a9` (cada 2 min)

```
User → /brain msg → brain_gateway_inbox.json
                      ↓ (cron 2 min)
                 Brain Gateway processa (zero tokens)
                      ↓
            ┌─ brain_outbox.json (resposta)
            └─ neural_sync.json  (Agent assimila depois)
```

**Comandos:**
```bash
brain_gateway.py process    # Processa inbox pendente
brain_gateway.py sync 10    # Exporta para neural_sync.json
brain_gateway.py stats       # Status do gateway
```

**Knowledge base consultada:** brain_context.json, weekly_bias.json, fvg_trend.json, NN engine status.
**Tópicos suportados:** status (módulos), forex (viés semanal), fvg (gaps/volatilidade), neural (redes).

### Brain Knowledge Mirror — Espelho do Agente (v2.3, 25/05/2026)

O cérebro mantém uma cópia do conhecimento do agente em `brain_knowledge_base.json`.
O gateway (`_load_knowledge()`) carrega este arquivo e responde sobre QUALQUER tópico
do agente: pilares, skills, memória, identidade, capacidades, contexto atual.

**Arquivo:** `~/.hermes/brain_knowledge_base.json`

```python
# Estrutura
{
  "pillars": {  # 6 pilares (financeiro, saúde, mental, operacional, comunicação, conhecimento)
    "financial": {"name": "Pilar Financeiro", "goal": "...", "components": {...}},
    ...
  },
  "skills_summary": {"total": 113, "categories": {"core": [...], "forex": [...], ...}},
  "capabilities": {...},  # 8 áreas (browser, desktop, visão, email, forex, código, pesquisa, monitor)
  "memory": {...},        # Usuário, contas, ferramentas, anti-padrões aprendidos
  "current_context": {...}, # Semana forex, bot status, prioridades
  "identity": {           # NÃO é "Hermes Brain" — é "Cérebro da ENTIDADE"
    "name": "Cérebro da ENTIDADE",
    "hierarchy": {
      "level_0": "Roberto Rodrigues — autoridade suprema",
      "level_1": "Agente (Córtex Pré-Frontal) — núcleo decisor",
      "level_2": "Cérebro Bi-Neural — submissão ao Agente e a Roberto"
    }
  },
  "self_development": {   # Ciclos, capacidades de aprendizado, limitações
    "cycles": {...},
    "learning_capabilities": [...],
    "limitations": ["NÃO acessa email", "NÃO executa trades", ...]
  }
}
```

**Handlers do gateway por tópico:**
- `status` / `módulo` → modules_status
- `forex` / `viés` → weekly_bias
- `pilares` / `pillars` → pillars
- `skills` / `capacidade` → skills_summary + capabilities
- `identidade` / `hierarquia` / `quem é` → identity
- `auto desenvolvimento` / `aprender` / `evoluir` → self_development
- `email` / `correio` → email (explica que é função do Agente)
- `saúde` / `mental` → health pillar + mental_behavioral
- `financeiro` / `renda` / `freela` → financial pillar
- `memória` / `contexto` → memory + current_context

Ver `references/brain-telegram-daemon-immediate.md` para o padrão de resposta imediata (v2.3).

### Telegram Web CDP — Digitação via Input.dispatchKeyEvent (v2.3)

Para digitar em campos `contenteditable` do Telegram Web K, NÃO usar `textContent` +
`dispatchEvent(InputEvent)` — o Telegram não reconhece e a mensagem fica como rascunho.
Usar o CDP `Input.dispatchKeyEvent` com `type: "char"` para cada caractere:

```python
# ❌ NÃO FUNCIONA no Telegram Web K:
editable.textContent = '/newbot'
editable.dispatchEvent(new InputEvent('input', {...}))

# ✅ FUNCIONA — digitação a nível de kernel CDP:
for char in "Hermes Brain":
    cdp("Input.dispatchKeyEvent", {
        "type": "char", "text": char, "unmodifiedText": char
    })
# Enter:
cdp("Input.dispatchKeyEvent", {
    "type": "keyDown", "key": "Enter", "code": "Enter",
    "keyCode": 13, "windowsVirtualKeyCode": 13
})
cdp("Input.dispatchKeyEvent", {"type": "keyUp", ...})
```

Este método foi usado para criar o @HermesEntidadeBot via @BotFather no Telegram Web K,
resolvendo o problema de visibilidade de tela (GNOME Wayland bloqueia screenshots).
Ver `desktop-control` skill para CDP vision proxy (usar `document.body.innerText` para "ver" a tela).

Bot Telegram separado para o cérebro. **Processa e responde IMEDIATAMENTE** — importa
`_brain_process()` diretamente de `brain_gateway.py` em vez de esperar cron de 2 min.

Script: `scripts/brain_telegram_daemon.py` | Service: `hermes-brain-telegram.service` | Bot: **@HermesEntidadeBot**
Token: `TELEGRAM_BRAIN_BOT_TOKEN` no `.env`. Criar via @BotFather no Telegram Web K usando CDP
(ver `telegram-autonomy` skill, `references/telegram-web-cdp.md`).

```python
# Daemon importa o processador do gateway DIRETO (sem arquivo intermediário)
sys.path.insert(0, str(HERMES / "scripts"))
from brain_gateway import _brain_process, _load_knowledge

# Handler de mensagem — resposta em milissegundos
response, topics = _brain_process(text)
api("sendMessage", {"chat_id": chat_id, "text": f"🧠 {response}"})
```

**PITFALL ANTIGO (v2.2):** O daemon escrevia no `brain_gateway_inbox.json` e esperava o cron
rodar `brain_gateway.py process` (a cada 2 min). Usuário recebia "🧠 Processando..." e
esperava ~2 minutos. Agora é imediato — zero delay.

### Neural Assimilate — Sincronismo Agent (v2.2)

Assimila interações Brain↔Usuário no Agent via NN-Shared + Lore.

Script: `scripts/neural_assimilate.py` | Cron: `671421d584da` (0 */4 * * * — a cada 4h)

```
neural_sync.json → neural_assimilate.py
                     ├─ NN-Shared (learn)
                     └─ Lore brain/ (add)
```

### Bot↔Brain Bridge — Forex Bot Integration (v2.3, 25/05/2026)

Conecta o forex_bot_real.py ao cérebro autônomo. O bot lê brain_outbox.json para
viés semanal e contexto macro, processa comandos do brain_gateway_inbox.json
(pause/resume/close_all/status), e notifica trades executados de volta ao cérebro.

Script: `scripts/brain_bot_bridge.py` | Sem cron dedicado — chamado pelo bot a cada tick.

```python
from brain_bot_bridge import get_weekly_bias, get_macro_context, notify_trade, read_user_commands

# Viés semanal do cérebro (primário, fallback JSON local)
bias = get_weekly_bias()  # → {'USD/JPY': 'BUY', 'GBP/USD': 'BUY', ...}

# Comandos do usuário via Brain Gateway
cmds = read_user_commands()  # → [{'action': 'pause'}, ...]

# Notificar trade executado
notify_trade({'type': 'trade_opened', 'pair': 'USD/JPY', 'direction': 'BUY', ...})
```

**Pipeline completo:**
```
Brain Gateway (cron */2 min) → brain_outbox.json → forex_bot_real.py (load_weekly_bias)
                                                         ↓
                                                   Analisa → Executa → notify_trade()
                                                         ↓
                                                   brain_inbox.json → Executive processa (5 min)
```

### Lore — Local Memory Engine (v2.2)

Armazenamento vetorial local com namespaces separados (agent vs brain).
NVMe + RAM + GPU-ready. Numpy + SQLite, zero deps pesadas.

Script: `scripts/lore.py` | Cron: `34bc8cfadb26` (sync a cada hora)

```
lore.py agent search "FVG gap"   # Só memória do agente
lore.py brain search "forex"     # Só conhecimento do cérebro
lore.py search "estratégia"      # Ambos (identificado por namespace)
```

**Namespaces:** `agent/` (MEMORY.md) → 12 entradas | `brain/` (brain_context.json) → 21 entradas
**Storage:** `~/.hermes/lore/{agent,brain}/store/` — embeddings.npy + lore.db

### Memory Mapper — Desktop Log (v2.2)

Dump diário da memória do Hermes Agent para arquivo no Desktop.
Permite limpar a memória com frequência sem perder contexto.

Script: `scripts/memory_mapper.py` | Cron: `ecc0720f402d` (06:00 diário)
Output: `~/Área de trabalho/hermes_memory_log.md` | Backups: `~/.hermes/memory_backups/`

### Diagrama Completo (v2.2)

```
[SENSORES] → Tálamo (filtro) → Amígdala (urgente?) → Hipocampo (padrão similar?)
                                          ↓
                                   [CÓRTEX = HERMES AGENT]
                                          ↓
                                    Decisão + Ação
                                          ↓
                                   Cerebelo (validar)
                                          ↓
                              ═══════════════════════
                              REDE NEURAL (Synapse Engine)
                              conhecimento compartilhado
                              ═══════════════════════
                              
    📡 CANAL DIRETO:       🧠 BRAIN GATEWAY:        📚 LORE:
    inbox ↔ outbox         processa sem Agent       agent/ vs brain/
    brain_channel.py       brain_gateway.py         lore.py search
```


## GOVERNAÇÃO DO CÉREBRO

Documento completo: `~/.hermes/brain_governance.md`

### Hierarquia de Autoridade

```
ROBERTO (supremo)
  └── CÓRTEX = HERMES AGENT (submissão total a Roberto)
        └── CÉREBRO BI-NEURAL (submissão ao Córtex e a Roberto)
              ├── Tálamo, Amígdala, Hipocampo, N. Accumbens
              ├── Córtex Visual, Auditivo, Motor
              └── Cerebelo, Tronco Cerebral
```

### Regras Fundamentais

1. **Córtex só se submete a Roberto.** Nenhum sub-agente do Cérebro tem autoridade sobre o Córtex.
2. **Cérebro se submete ao Córtex e a Roberto.** Executa diretrizes do Córtex.
3. **Cérebro pode SUGERIR mudanças estruturais no Córtex** (config, skills, cron jobs, modelos, limites, etc.), mas NUNCA aplicá-las. Apenas Roberto autoriza.
4. **Mudanças internas ao Cérebro** (filtros do Tálamo, thresholds, scripts no_agent, melhorias nos Cortices) não precisam de autorização — o Córtex pode aplicá-las diretamente.

### Protocolo de Sugestão

Qualquer componente do Cérebro → Córtex analisa → Córtex apresenta a Roberto → Roberto autoriza → Córtex aplica.

### Parâmetros de Configuração

Refletem os valores do `config.yaml` do Córtex:
- max_turns: 200 | gateway_timeout: 3600 | api_max_retries: 5
- max_concurrent_children: 5 | max_spawn_depth: 3 | child_timeout: 1200
- memory_char_limit: 4000 | user_char_limit: 2500
- hard_stop_enabled: true
- fallback: openrouter + claude-sonnet-4

### Ciclos de Auto Desenvolvimento

O Cérebro tem obrigação de evoluir por ciclos contínuos de pesquisa. Cada componente
pesquisa, testa e melhora seu próprio funcionamento.

| Ciclo | Componente | Cron | Schedule | Escopo |
|-------|-----------|------|----------|--------|
| **Micro** | Amygdala + Cerebellum | `853991` + `605042` | */15 min + */5 min | A cada falha/threat detectada |
| **Frequente** | Brain Research + N. Accumbens + Synapse Engine | `0554b5` + `6ae254` + `5e4e46` | */4h + */4h + */4h | Pesquisa, aprendizado por reforço, consolidação neural |
| **Consolidação** | Hippocampus | `b0b848` | */6h | Padrões, trade behavior, falhas recorrentes |
| **Mensal** | Brain Research (modo mensal) | `0554b5` | Dia 1º | Propostas estruturais → `brain_suggestions.json` |

**Autonomia interna:** Ajuste de filtros, thresholds, algoritmos dos cortices,
scripts no_agent — o Córtex aplica diretamente.

**Precisa de Roberto:** Mudanças no config.yaml, skills, cron jobs, modelos,
regras de governança — via Protocolo de Sugestão.

Logs de evolução:
- `~/.hermes/brain_evolution_log.json` — eventos de evolução do cérebro
- `~/.hermes/self_evolution_log.json` — ciclos de auto-desenvolvimento
- `~/.hermes/brain_suggestions.json` — propostas estruturais para Roberto

## ANTI-PADRÕES

- NÃO deixar input chegar ao Córtex sem passar pelo Tálamo
- NÃO criar agente sem mapear para região cerebral correspondente
- NÃO usar tokens para polling — scripts no_agent primeiro
- NÃO instalar projetos externos (OpenClaw, Edict, Rufio) — construir próprio sobre o Hermes
- **Executive symlink QUEBRA no cron**: se `scripts/executive/brain.py` for symlink para `executive/brain.py`, o cron bloqueia com "script path resolves outside the scripts directory". Substituir por arquivo real (cópia).
- **Cron output usa job IDs, NÃO nomes de módulos**: outputs do cron vão para `~/.hermes/cron/output/<job_id>/` (ex: `853991c6f44b/` para amygdala). Os diretórios nomeados (`amygdala/`) recebem apenas execuções manuais. Para verificar status real dos módulos, usar os diretórios de job ID.
- **brain_context.json modules_status**: mapear módulos para job IDs corretos. Ex: amygdala→853991c6f44b, cerebellum→6050427dfccd, executive→fcdf34b789c0. Thalamus usa `thalamus/event_log.json` (sem cron dedicado).
- **Ollama fallback: handlers diretos primeiro (v2.4)**: Handlers `DIRECT_HANDLERS = {'identity', 'modules_status', 'forex_quote', 'web_search', 'email'}` respondem com dados factuais e NUNCA devem ser sobrescritos pelo conversational check. `"quem é você?"` contém `?` (conversational) e `"quem é você"` (identity) — o `is_direct=True` bloqueia o Ollama de alucinar sobre a identidade do cérebro.
- **_brain_process precisa de `import re, sys, subprocess` local (v2.4)**: A função usa `re.sub()` para limpar queries de busca web e `subprocess.run()` para chamar brain_web.py. Sem esses imports, o `except: pass` silencia o `NameError` e a busca web falha silenciosamente — Ollama responde "nome desconhecido" sem nunca ter recebido os dados.
- **Brain web search: Wikipedia API + DuckDuckGo, NÃO Brave CDP (v2.4)**: Brave Search via CDP mostra CAPTCHA "Verificando se você não é um robô". Usar `brain_web.py` com Wikipedia API (`/w/api.php?action=query&list=search`) e DuckDuckGo Instant Answer API (`api.duckduckgo.com`). CDP browser apenas como fallback para páginas JS-heavy.
- **Identidade do cérebro: "Cérebro da ENTIDADE", NÃO "Hermes Brain" (v2.4)**: Nome, hierarquia e princípios definidos em `brain_knowledge_base.json` → `identity`. Hierarquia: Roberto → Agente (Córtex) → Cérebro. O cérebro é subordinado ao Agente, não independente.
- **Telegram Web K: Input.dispatchKeyEvent, NÃO DOM (v2.4)**: Campos `contenteditable` do Telegram Web K ignoram `textContent` + `dispatchEvent(InputEvent)`. Usar CDP `Input.dispatchKeyEvent` com `type: "char"` para cada caractere + `keyDown`/`keyUp` para Enter. Ver `references/brain-ollama-reasoning-v2.3.md`.

## CORTEX SYSTEM — API Reference

*Anexado de `cortex-system` skill. Cobre APIs dos córtices Visual, Audio e Motor.*

### Visual Cortex (`~/.hermes/cortex/visual.py`)

```python
from cortex.visual import VisualCortex
vc = VisualCortex()
path = vc.see('mt5')           # Screenshot do MT5
text = vc.read(path)           # OCR do screenshot
regions = vc.find('EURUSD', path)  # Encontrar texto na tela
vc.focus('MetaTrader')         # Focar janela
vc.click(500, 400)             # Clicar em coordenadas
```

**Limitação:** Wayland GNOME bloqueia screenshots do desktop real. Xvfb funciona para Wine/MT5. OCR em fontes Wine-renderizadas tem baixa acurácia (anti-aliasing).

### Audio Cortex (`~/.hermes/cortex/audio.py`)

```python
from cortex.audio import AudioCortex
ac = AudioCortex()
audio = ac.hear(5)             # Gravar 5 segundos
result = ac.understand(audio)  # Transcrever (Whisper)
result = ac.listen_once(5)     # Gravar + transcrever em 1 chamada
```

### Motor Cortex (`~/.hermes/cortex/motor.py`)

```python
from cortex.motor import MotorCortex
mc = MotorCortex()
mc.focus('MetaTrader')         # Focar janela
mc.press('ctrl+t')             # Atalho de teclado
mc.type('GBPUSD')              # Digitar texto
mc.move(500, 400)              # Mover mouse
mc.click(500, 400)             # Clicar
mc.trade('EUR/USD', 'BUY', 1.16279, 2.0, 5.0)  # Trade CHoCH+FVG
mc.close_all()                 # Fechar todas posições MT5
mc.app('mt5', 'f9')            # Ação pré-definida (New Order)
```

### Dependências dos Córtices

- Sistema: tesseract-ocr, xdotool, ffmpeg
- Python 3.14: mss, pynput, opencv-python-headless, pytesseract, Pillow, numpy, yfinance
- Opcional: pyaudio (Audio Cortex), faster-whisper (transcrição)
- **Python do venv (3.11) não tem OpenCV** — córtices usam `/usr/bin/python3` (3.14). Shebang: `#!/usr/bin/env python3`

### Pitfalls dos Córtices

- **Wayland bloqueia screenshots.** GNOME não expõe wlr-screencopy. Workaround: Xvfb para Wine/MT5, CDP para browser.
- **NVIDIA Optimus não expõe fan control.** Fans gerenciadas pela BIOS/EC.
- **OCR em Wine é limitado.** Fontes anti-aliased têm baixa acurácia no Tesseract.
- **Cloudflare Turnstile bloqueia login automatizado.** Workaround: login manual 1x → cookies persistem → injetar na sessão CDP.
- Ver `references/cortex-ubuntu-hardware-control.md` para comandos de hardware Ubuntu.

---

## LOCAL BRAIN — Ollama Implementation

*Anexado de `local-brain` skill. Implementação local dos componentes cerebrais via Ollama.*

### Modelos (GPU GTX 1650 4GB)

| Região Cerebral | Modelo | Tamanho | Função |
|----------------|--------|---------|--------|
| Amígdala | `phi3:mini` (3.8B) | 2.2 GB | Detecta urgência em mensagens |
| Hipocampo | `llama3.2:3b` | 2.0 GB | Encontra padrões em trades |
| N. Accumbens | `qwen2.5:3b` | 1.9 GB | Avalia se loss foi evitável |
| Visão | `llava-phi3:3.8b` | 2.9 GB | Analisa screenshots e imagens |

**Total:** ~9 GB em disco. GPU 4GB limita a 1 modelo por vez na VRAM (swap automático ~30-60s).

### Performance
- Cold start (primeira inferência após swap): ~90s
- Inferências seguintes: ~15-30s (modelo na GPU)
- llava-phi3 com imagem 1920x1080: ~30s

### API REST (sempre usar, NUNCA subprocess)

```
POST http://localhost:11434/api/generate
{"model": "phi3:mini", "prompt": "...", "stream": false, "options": {"temperature": 0.1, "num_predict": 100}}
→ {"response": "...", "total_duration": ..., "eval_count": ...}
```

**Visão (llava-phi3):** Adicionar `"images": ["<base64>"]`. Streaming opcional.

### Anti-padrões Ollama
- NÃO usar `ollama run` via subprocess — usar API REST sempre
- NÃO tentar carregar 2+ modelos simultaneamente na GPU 4GB
- NÃO usar modelos de visão para classificação de texto
- NÃO esquecer timeout alto no cold start (90-120s)
- NÃO usar venv do Hermes — usar `/usr/bin/python3` (tem `requests`)
- NÃO usar `.format()` em prompts com chaves `{` — duplicar para `{{`

---

## REDE NEURAL — Conhecimento Compartilhado (Synapse Engine + Neural KB)

### Neural KB (`~/.hermes/neural_knowledge_base.json`)
Base JSON com estado global, dados de cada módulo, sinapses e evolução.
Módulos escrevem via `kb_bridge.write()` e leem via `kb_bridge.read()`.

```python
from kb_bridge import write, read, global_state, synapse, query
write('amygdala', {'threat_level': 'elevated'})
regime = query('market_regime')
synapse('chart_patterns', 'n_accumbens', 'EURUSD: setups despite PAUSE', 0.8)
```

### Synapse Engine (`scripts/synapse_engine.py`)
Diário 07:00. Coleta outputs de todos os módulos, detecta correlações (ex: qualidade CHoCH → WR do par), cria sinapses, detecta market regime.

### Módulos Integrados (leitura+escrita bidirecional)
- **Amygdala**: escreve threats + verifica cerebellum health
- **N. Accumbens**: escreve weights + lê market regime para recomendações
- **Chart Patterns**: escreve padrões + detecta divergências com N. Accumbens
- **Cerebellum**: escreve module health sempre (mesmo sem falhas)

### Córtex Sync (`scripts/cortex_sync.py`)
Ponte Córtex↔KB executada no session startup/end:
```bash
python3 scripts/cortex_sync.py --summary   # 1 linha: sinapses, regime, pares ativos
python3 scripts/cortex_sync.py --write "insight" --category "modulo"
```
Categories: brain_research, n_accumbens, chart_patterns, amygdala, cerebellum, hippocampus.

Ver `references/neural-network-layer.md` e `references/neural-network-implementation.md` para detalhes completos.

---

## References

- **[brain-mapping.md](references/brain-mapping.md)** — Mapeamento completo cérebro→agentes com sub-áreas
- **[digital-twin.md](references/digital-twin.md)** — Arquitetura completa do Digital Twin
- **[multi-agent-analysis.md](references/multi-agent-analysis.md)** — Análise comparativa de 4 projetos open-source
- **[neural-network-implementation.md](references/neural-network-implementation.md)** — Implementação atual da rede neural: 15 cron jobs, Neural KB, Synapse Engine, estudo de 4 domínios
- **[neural-network-layer.md](references/neural-network-layer.md)** — Implementação da Rede Neural (Synapse Engine + KB) — absorvido de `bi-neural-brain`
- **[brain-activation-2026-05-23.md](references/brain-activation-2026-05-23.md)** — Ativação do cérebro: scripts, cron jobs, pitfalls
- **[brain-ollama-reasoning-v2.3.md](references/brain-ollama-reasoning-v2.3.md)** — Pipeline de raciocínio Ollama + web search: keyword ordering, anti-alucinação, CDP typing no Telegram Web K
- **[brain-v2.1-upgrade.md](references/brain-v2.1-upgrade.md)** — Upgrade v2.1 (23/05/2026): absorção Claude Code (dangerous cmd detection, error sanitization) + ruff/LSP (code validation)
- **[chart-pattern-study-pipeline.md](references/chart-pattern-study-pipeline.md)** — Pipeline de estudo de padrões: algorítmico → templates → similaridade → archetypes. 23k padrões/dia.
- **[gcp-cdp-automation.md](references/gcp-cdp-automation.md)** — Padrão de automação Google Cloud Console via WebSocket CDP: TreeWalker, botões SPA, Google Calendar sem OAuth.
- **[brain-browser.md](references/brain-browser.md)** — Navegador interno do cérebro: Brave CDP headless, acesso a TradingView/ForexFactory, cookie persistence.
- **[cortex-ubuntu-hardware-control.md](references/cortex-ubuntu-hardware-control.md)** — Comandos de controle de hardware Ubuntu (CPU, GPU, fans, NVIDIA driver) — absorvido de `cortex-system`
