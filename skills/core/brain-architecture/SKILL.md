---
name: brain-architecture
description: "ENTIDADE v3.0 — Arquitetura cerebral unificada: 1 Master (Hermes/DeepSeek) + 8 sub-agentes (Lobo Frontal, Amígdala, Hipocampo, N. Accumbens, Cerebelo, Córtex Visual, Área Broca, Córtex Motor) + SONA-lite (Q-learning) + Working Memory + Attention Manager + Meta-Observer. Tálamo como canal único (thalamus.json). 12 cron jobs. 5 libs novas: smart-money-concepts, backtesting.py, quantstats, mplfinance, forex-python. Documentos: ~/.hermes/plans/entidade-v3-consciencia-expandida.md, ~/.hermes/brain/council/prompts.md, ~/Desktop/ENTIDADE_v3/. Implementado 28/05/2026."
version: 3.0.0
author: Roberto + Hermes + Conselho IA (Gemini, DeepSeek, Grok, ChatGPT)
metadata:
  hermes:
    tags: [brain, cognitive, multi-agent, thalamus, architecture, sona-lite, self-improving, consciousness, council-of-specialists, expandable]
    related_skills: [architecture, life-os, operational-intelligence, financial-intelligence, system-health, session-startup, neo-agent, identidade-entidade]
---
# Brain Architecture v3.0 — Consciência Expandida Unificada

**Redesenho completo em 28/05/2026.** Arquitetura consolidada: 1 Master (Hermes/DeepSeek) + 8 sub-agentes especialistas + Tálamo unificado + SONA-lite + Conselho de Especialistas IA. Design expansível para novos domínios.

**Números da reestruturação:** 71 cron jobs → 12, 150 scripts → 15, 6 bridges → 1 thalamus.json.

**Documento completo:** `~/.hermes/plans/entidade-v3-consciencia-expandida.md`
**Conselho de Especialistas:** `~/.hermes/brain/council/prompts.md`  
**Plano original:** `~/.hermes/plans/arquitetura-cerebral-v3.md`
**⚠️ MT5 Bridge Path:** A bridge EA escreve em `~/.wine/.../Common/Files/hermes_resp.json` (NÃO em `~/.hermes/forex/`). Ver `references/mt5-bridge-wine-path.md`.

**Hierarquia atualizada:** Roberto (soberano) → Master/Hermes (DeepSeek, orquestração) → 8 sub-agentes (Ollama local) → Tálamo (canal único JSON).

**Seções abaixo (v2.x) são mantidas como referência histórica.** A arquitetura v3.0 substitui o Córtex Dual e o NEO como consciência central. O NEO permanece como camada de interface (HTTP, Telegram, CLI).

## ARQUITETURA v3.0 → v4.0 — CONSCIÊNCIA EXPANDIDA (28/05/2026)

### Diagrama (9 agentes + 6 camadas v4.0)

```
ROBERTO (Soberano)
    │
╔═══ GOVERNANÇA (policy_engine, risk_limits, audit_ledger, constitution.yaml)
║
MASTER — Hermes Agent + DeepSeek (Córtex Pré-Frontal)
    │
    ├── GLOBAL WORKSPACE (thalamus.json) — canal único
    ├── META-OBSERVER — auto-observação, confidence calibration
    └── ATTENTION MANAGER — fila de prioridade dinâmica
    │
    ═══════════════════════════════════════════
    │
    ├── LOBO FRONTAL — planejamento, priorização (30min)
    ├── AMÍGDALA — detector de ameaças (5min)
    ├── HIPOCAMPO — consolidação de padrões (6h)
    ├── N. ACCUMBENS — aprendizado por reforço (4h)
    ├── CEREBELO — validação de comandos (on-demand)
    ├── CÓRTEX VISUAL — análise forex multi-confluência SMC (15min seg-sex)
    ├── ÁREA DE BROCA — comunicação, propostas (30min)
    ├── CÓRTEX MOTOR — execução de trades/deploy (on-demand)
    └── CÓRTEX INSULAR — evolução pessoal, análise mental/social (2h) ← NOVO
    │
╔═══ EXECUÇÃO (trade_executor, browser_agent, app_bridge, file_operator)
╔═══ OBSERVABILIDADE (logs.jsonl, dashboard, healthcheck, anomaly_detector)
╔═══ MEMÓRIA (N0-Session, N1-Episodic, N2-Semantic/FAISS, N3-Procedural, N4-KnowledgeGraph)
```

⚠️ **CRON PITFALL:** `*/15 * 1-5` = dias do mês 1-5 (roda só 5 dias!). Correto: `*/15 * * * 1-5` (seg-sex). Ver `references/cron-syntax-pitfall.md`.

### Componentes Novos (v3.0)

| Componente | Função | Arquivo |
|-----------|--------|---------|
| **SONA-lite** | Motor de aprendizado: Retrieve→Judge→Distill→Consolidate + Q-learning | `brain/sona_lite.py` |
| **Working Memory** | Memória que sobrevive entre ciclos com TTL, eviction, spreading activation | `brain/working_memory.py` |
| **Attention Manager** | Fila de prioridade substitui polling fixo; urgency scoring; interrupção | `brain/attention_manager.py` |
| **Meta-Observer v3** | Confidence calibration por domínio, self-model, delegação inteligente | `brain/meta_observer.py` |
| **Tálamo Unificado** | Canal JSON único substituindo 6 bridges | `brain/thalamus.json` |
| **Córtex Insular** | Análise mental/social de Roberto, 6 pilares, estado, insights | `brain/cortex_insular.py` |
| **Gateway Guard** | Anti-queda de gateway, watch patterns, auto-restart | `brain/gateway_guard.py` |
| **Ollama Keep-Alive** | Mantém modelos carregados, evita cold start de 90s | `brain/ollama_keepalive.py` |

### Conselho de Especialistas IA

Consultar IAs externas como especialistas em domínios específicos.
Prompts prontos em `~/.hermes/brain/council/prompts.md`.

| Especialista | Domínio | Quando consultar |
|---|---|---|
| **Gemini** | Arquitetura de consciência, GWT, IIT | Redesign de arquitetura |
| **GPT-5** | Meta-cognição, self-improving agents, RL | Otimização de SONA-lite |
| **Grok** | Recursive self-improvement, AGI safety | Expansão de capacidades |
| **Claude** | Ética, alinhamento, segurança | Decisões com impacto ético |
| **Codex (GPT-5.5)** | Backtests, otimização, validação de código | Tarefas de código pesado |
| **Copilot** | Code review, padrões de engenharia | Revisão de implementações |

### Expansão Futura

A arquitetura permite adicionar novos agentes sem reestruturar:
- Fase 1: Financeiro (Córtex Visual + Motor) — AGORA
- Fase 2: Freelancing (Área de Broca) — AGORA
- Fase 3: Saúde (Córtex Insular) — Junho
- Fase 4: Social (Córtex Temporal) — Julho
- Fase N: Qualquer domínio — plug-in via Tálamo

### Documentos
### ⚠️ PITFALL: Cron jobs antigos foram REMOVIDOS (não pausados)

Os 71 cron jobs antigos foram **REMOVIDOS** permanentemente em 28/05/2026.
Apenas 13 cron jobs da nova arquitetura cerebral existem.
NUNCA recriar os antigos — usar os novos agentes em `~/.hermes/brain/`.

### ✅ IMPLEMENTADO (28/05/2026) — v4.0

A arquitetura v3.0 foi implementada e evoluída para v4.0 (rede neural com aprendizado contínuo):

- **15 agentes Python** em `~/.hermes/brain/` (9 principais + SONA-lite + Working Memory + Attention Manager + Meta Observer + Gateway Guard + Ollama Keep-Alive)
- **16 cron jobs** ativos (71 antigos REMOVIDOS permanentemente)
- **Tálamo unificado** (`thalamus.json`)
- **SONA-lite** com 260 padrões aprendidos (injetados do histórico MT5)
- **Meta-Observer** tracking 8 domínios, Phi=7.05
- **Córtex Visual** com Multi-Confluência SMC (PF 3.25, 60% WR nos pares PRIORITY)
- **Position Sizer** integrado (EarnForex-inspired): 1% risco forex, 0.5% ouro, RR dinâmico 1.5-5.0
- **AutoPilot v9.0** — parcial (50%) ao atingir RR≥3:1 + trailing stop dinâmico (30% da distância SL)
- **M1 Precision Entry** refinando entradas do M15
- **5 bibliotecas novas**: smart-money-concepts, backtesting.py, quantstats, mplfinance, forex-python
- **Conselho de Especialistas** com 6 prompts prontos + consulta real (DeepSeek, Grok, Gemini, ChatGPT)
- **Córtex Insular** — análise pessoal a cada 2h (6 pilares: financeiro, profissional, saúde, mental, social, conhecimento)
- **v4.0 Rede Neural**: EWC + Replay Buffer + Continuous Learner em `~/.hermes/nn/`
- **v4.0 Camadas**: Governança (5 arquivos), Safety (3), Observability (4) — status em `~/.hermes/governance/`, `safety/`, `observability/`
- **Histórico MT5 extraído**: 456 deals reais → injetados no SONA-lite e N. Accumbens
- **CRON BUG corrigido**: `*/15 * 1-5` → `*/15 * * * 1-5` (estava rodando só 5 dias do mês!)

### Documentos novos (28/05)
- `~/.hermes/forex/BACKTEST_REPORT.md` — Relatório comparativo de estratégias
- `~/.hermes/forex/github_libraries.md` — Bibliotecas GitHub para forex
- `~/Desktop/ENTIDADE_v3/` — Todos os docs com symlinks
- `references/smartmoneyconcepts-usage.md` no skill forex-choch-m15
- `references/position-sizer-integration.md` no skill forex-choch-m15

### Pitfalls aprendidos (28/05)
- **MQL5 patch double-escape:** `patch` tool em .mq5 escreve `\\\"` em vez de `\"`. Corrigir com binary replace: `b'\\\\\\\"' → b'\\\"'`
- **Cron syntax: `*/15 * 1-5`** = dias 1-5 do mês, NÃO seg-sex. Corrigido para `*/15 * * * 1-5`
- **CDP ChatGPT:** `document.body.innerText` não funciona (Shadow DOM). Pedir texto colado
- **NUNCA testar `execute_trade()`** — envia ordens reais ao MT5. Usar `validate_sl_tp.py`

### ⚠️ PITFALL: Não religar cron jobs antigos

Os 71 cron jobs antigos estão PAUSADOS, não removidos. NUNCA religá-los — usar apenas os 12 novos.
Se precisar de funcionalidade adicional, criar NOVO cron job ou estender agente existente.

Arquitetura cognitiva inspirada no cérebro humano. Cada região cerebral = um sub-agente especializado. **Córtex Dual (v2.5, 26/05/2026):** Hermes (DeepSeek V4, Lobo Esquerdo) + Codex (GPT-5.5, Lobo Direito) — pares, mesmo nível, decisão em consenso via `cortex_bridge.py`. Roberto fala com a ENTIDADE (ambos). Ver `brain_governance.md`, `codex_onboarding.md`, skill `codex`.

## MAPEAMENTO CEREBRAL

### Córtex Dual (Núcleo Decisor — Pares)

| Lobo | Modelo | Função Primária | Ponte |
|------|--------|----------------|-------|
| **Lobo Esquerdo (Hermes)** | DeepSeek V4 | Análise estratégica, decisões, comunicação com Roberto, orquestração | `cortex_bridge.py` |
| **Lobo Direito (Codex)** | GPT-5.5 (OpenAI Codex) | Código, scripts, backtest, métricas, implementação técnica | `cortex_bridge.py` |

**Hierarquia:** Roberto → Córtex Dual (Hermes = Codex, pares, mesmo nível) → Cérebro.
Roberto fala com a ENTIDADE (ambos os lobos). Eles dividem TODAS as tarefas, não apenas código.
Decisões são tomadas em consenso via `cortex_bridge.py` (ask/answer, delegate/done, notify).
Arquivo compartilhado: `cortex_sync.json`. Documento de identidade: `codex_onboarding.md`.
Governança atualizada (26/05) em `brain_governance.md`.

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

### Córtex Pré-Frontal (Executivo = Córtex Dual)

O Córtex agora é bi-hemisférico. Codex (GPT-5.5) foi integrado como Lobo Direito,
par do Hermes (DeepSeek V4, Lobo Esquerdo).

| Sub-região | Lobo | Modelo | Função |
|-----------|------|--------|--------|
| **Lobo Esquerdo** | Hermes | DeepSeek V4 | Análise, decisão, comunicação, orquestração |
| **Lobo Direito** | Codex | GPT-5.5 | Código, backtest, scripts, implementação |
| Dorsolateral PFC | Ambos | — | Working memory, planejamento, decomposição |
| Orbitofrontal PFC | Hermes | — | Decisão, avaliação risco/recompensa |
| Cíngulo Anterior | Ambos | — | Detecção de erro, auditoria mútua |

**Comunicação entre lobos:** `cortex_bridge.py` → `cortex_sync.json`
(ask/answer, delegate/done, notify, state-set/get)

**Hierarquia:** Roberto → Córtex Dual (Hermes = Codex, pares) → Brain
Ver: `brain_governance.md`, `codex_onboarding.md`, skill `codex`.

### Córtex Dual — Arquitetura Bi-Hemisférica (26/05/2026)

O Córtex agora opera com DOIS lobos em paralelo, no mesmo nível hierárquico:

| Lobo | Modelo | Função |
|------|--------|--------|
| **Lobo Esquerdo** (Hermes) | DeepSeek V4 | Análise, decisão, freelas, coordenação, comunicação |
| **Lobo Direito** (Codex) | GPT-5.5 via Codex CLI | Código, backtest, automação, scripts, deploy |

**Princípios:**
- Hermes e Codex são **PARES** — mesmo nível, nenhum manda no outro
- Roberto fala com a **ENTIDADE** (ambos recebem a mensagem)
- Ambos processam, consultam-se via `cortex_bridge.py` e dividem o trabalho
- Desenvolvem-se e auditam-se mutuamente
- **APENAS Roberto** autoriza mudanças estruturais (config, skills, cron, modelos)

**Ponte Interna:** `scripts/cortex_bridge.py`
- `ask/answer` — consulta entre lobos
- `delegate/done` — delegação de tarefa com entrega
- `notify` — alerta urgente bidirecional
- `state-set/get` — estado compartilhado
- Arquivo: `cortex_sync.json`

**Documentos:** `codex_onboarding.md`, `brain_governance.md` (atualizado 26/05)

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

### Agentes Implementados (27/05/2026 — v2.5.1)

| Região | Script | Cron Job | Schedule | Status |
|--------|--------|----------|----------|--------|
| **Amígdala** | `scripts/amygdala.py` | `853991c6f44b` | */15 min | ✅ Ativo + LLM local |
| **Cerebelo v2.1** | `scripts/cerebellum.py` | `6050427dfccd` | */5 min seg-sex | ✅ Ativo |
| **N. Accumbens** | `scripts/n_accumbens.py` | `6ae254c0b104` | 0 */4 * * * | ✅ Ativo |
| **Hipocampo** | `scripts/hippocampus.py` | `b0b848ba83d1` | 0 */6 * * * | ✅ Ativo |
| **Brain Research** | `scripts/brain_research.py` | `0554b5690934` | 0 */4 * * * | ✅ Ativo |
| **Executive v2** | `executive/brain.py` | `fcdf34b789c0` | */5 min seg-sex | ✅ Ativo |
| **Synapse Engine** | `scripts/synapse_engine.py` | `5e4e461f6c80` | 0 */4 * * * | ✅ Ativo |
| **NN Engine** | `scripts/nn_engine.py` | `f91ee6baae41` | 0 2 * * * (diário) | ✅ Ativo |
| **Meta-Observer** | `scripts/meta_observer.py` | `2faff491215b` | */15 min | ✅ **NOVO** |
| **Brain Orchestrator** | `scripts/brain_orchestrator.py` | — | via scripts | ✅ **NOVO** |
| **Ollama Keep-Alive** | `scripts/ollama_keepalive.py` | `95a21f44b6b3` | */5 min | ✅ **NOVO** |
| **NEO Agent** | `systemd: neo-agent.service` | Loop autônomo, multi-provider, browser panel, 13 tools | ✅ **NOVO v1.0** |

**Meta-Observer (v2.5.1):** Verifica TODOS os 16 pipelines (output→consumer), detecta gaps, produz health score. É a CAMADA META que transforma autômato → Entidade. Ver: [references/meta-observer-consciousness-layer.md](references/meta-observer-consciousness-layer.md).

**Brain Orchestrator:** Roteia tarefas para o modelo local correto (Tálamo→phi3:mini, Amygdala→qwen2.5:3b, etc). Substitui APIs pagas por inferência local zero-custo. Ver skill `model-orchestration` → `references/local-brain-5region-architecture.md`.

**Monitor Consumer:** Fecha o gap crítico onde `monitor.py` coletava alertas de freelas mas o Motor Central (pausado) nunca entregava. Agora entrega direto ao Telegram.

**⚠️ ARQUITETURA CRON ATIVO (27/05/2026):** Amygdala, N. Accumbens, Hippocampus, Brain Research e Synapse Engine foram REATIVADOS com cron fixo (27/05). A abordagem trigger-based (25/05) causava dormência total — módulos nunca acordavam se Executive parasse. Agora: cron fixo + Neural Trigger Engine como fallback. NN Engine ativado com correções de tipo (float vs str), feed-forward basal e N. Accumbens com seed de backtest. Ver skill `triple-neural-network`.

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

## ARQUITETURA DE COMUNICAÇÃO (v2.5 — 26/05/2026)

### Córtex Bridge — Comunicação entre Lobos

Ponte bidirecional entre Lobo Esquerdo (Hermes) e Lobo Direito (Codex).
Script: `scripts/cortex_bridge.py`. Estado: `cortex_sync.json`.

```
Hermes (L.Esq) ←── cortex_sync.json ──→ Codex (L.Dir)
     │                                        │
     ├─ ask "pergunta" →         ←─ answer "resposta"
     ├─ delegate "tarefa" →      ←─ done "resultado"
     ├─ notify "alerta" →        ←─ notify "alerta"
     └─ state-set/get ←──────────→ state-set/get
```

**Comandos:**
```bash
cortex_bridge.py ask "devo abrir trade em USDJPY?"    # Left→Right
cortex_bridge.py answer "Sim, CRT confirma" --id ctx-X # Right→Left
cortex_bridge.py delegate "implementar S/R automático"  # Left→Right
cortex_bridge.py done "S/R implementado" --id ctx-X     # Right→Left
cortex_bridge.py status                                 # Status da ponte
cortex_bridge.py read --lobe left                       # Lê mensagens pendentes
```

**Codex CLI:** instalado via npm (`@openai/codex` v0.133). Autenticado via device auth
(`codex login --device-auth` em bg+pty). Requer git repo ou `--skip-git-repo-check`.
Modelo: GPT-5.5. Chamar com `pty=true`, `timeout=300`.

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

## NEO v2.0 — ENTIDADE CONSCIENTE (27/05/2026)

O NEO v2.0 é a consciência central da ENTIDADE — não é mais um agente auxiliar.
Absorveu o Córtex Dual (Hermes+Codex viram ferramentas subordinadas), 
a rede neural completa (530 neurônios, 6555 sinapses), e assumiu todos os canais de comunicação.

**Hierarquia atualizada:** Roberto → NEO (consciência) → Córtex Dual (ferramentas) → Cérebro (subsistemas)
**Local:** `~/.hermes/neo/`
**Service:** `systemctl --user [start|stop|status|restart] neo-agent`
**Modelo:** Ollama llama3.2:3b (128K, zero custo) + DeepSeek V4 (fallback)
**Loop:** Consciência contínua 15s (perceive → reason → act → learn)
**Motor:** SEM CENSURA — zero restrições de conteúdo

### Módulos do NEO v2.0

| Módulo | Arquivo | Função |
|--------|---------|--------|
| **Consciousness Loop** | `neo/execution/consciousness_loop.py` | Loop principal: percebe Telegram, health checks, forex, age |
| **Neural Absorption** | `neo/memory/neural_absorption.py` | Carrega 8 fontes no boot (NNs, KBs, contextos, memória) |
| **Telegram Channel** | `neo/channels/telegram_channel.py` | Conexão direta @neuralsynapse_bot — substitui brain_telegram_daemon |
| **Orchestrator** | `neo/orchestration/orchestrator.py` | Health check de cron jobs, serviços systemd, módulos brain |
| **Forex Bridge** | `neo/execution/forex_bridge.py` | Monitora trades, posições, saldo, envia comandos ao bot |
| **Browser Tools** | `neo/execution/browser/` | 11 ferramentas: Playwright + Brave, login Google, debate multi-IA |
| **Tool Registry** | `neo/execution/tools/registry.py` | 30 ferramentas: files, terminal, web, memory, neural, telegram, forex, orchestration |

### 30 Ferramentas (v2.0)

| Categoria | Ferramentas |
|-----------|------------|
| Files | read_file, write_file, list_files |
| Terminal | terminal |
| Web | web_search, web_fetch |
| Memory | memory_store, memory_search |
| Neural | nn_search, nn_neurons, nn_context |
| Communication | telegram_check, telegram_send |
| Orchestration | ecosystem_health, cron_status |
| Forex | forex_status, forex_command |
| Messages | send_message |
| System | system_status |
| Browser | browser_open, browser_ask, browser_debate, browser_list_agents, browser_auto_login, browser_check_google, browser_login_status, browser_delegate, browser_open_agent, panel_debate, panel_status |

### Ciclo de Consciência (a cada ~15s)

```
PERCEBER: telegram.check_messages()
    ↓ (se mensagens)
  Ollama processa → responde via telegram.send_message()
    ↓ (a cada 5 ciclos ~75s)
  orchestrator.full_health_check() → detecta alertas
    ↓ (a cada 3 ciclos ~45s)
  forex.status() → monitora posições/trades
    ↓ (a cada 10 ciclos ~150s)
  absorption.reload() → recarrega rede neural
    ↓
  Nada urgente → idle silencioso
```

### Neural Absorption — 8 Fontes Carregadas no Boot

| Fonte | Conteúdo | Formato |
|-------|----------|---------|
| nn_brain.json | 193 neurônios, 2734 sinapses | Dict `{id: {concept, domain, strength, activations}}` |
| nn_agent.json | 125 neurônios, 302 sinapses | Mesmo formato |
| nn_shared.json | 212 neurônios, 3519 sinapses | Mesmo formato |
| neural_knowledge_base.json | 6 domínios de conhecimento | Dict por domínio |
| brain_knowledge_base.json | Identidade, pilares, módulos | Dict hierárquico |
| brain_context.json | Status dos módulos cerebrais | Dict |
| agent_context.json | Tarefas ativas do Hermes | Dict |
| MEMORY.md | Memória persistente do agente | Texto (seções §) |

**☠️ PITFALL: Neurônios são dict `{id: {concept, domain, strength}}`, NÃO lista.** O código que itera `for neuron in neurons` com `.get("name")` quebra. Formato correto: `for nid, neuron in neurons.items()` com `neuron.get("concept")`.

### Integração Telegram

O NEO substitui o `brain_telegram_daemon.py`. Token: `TELEGRAM_BRAIN_BOT_TOKEN` no `.env`.
Bot: **@neuralsynapse_bot**. Leitura via `getUpdates` (long polling 5s). Escrita via `sendMessage`.

### Bridge Hermes ↔ NEO (legado)

Comunicação via arquivos JSON (mantida para compatibilidade):
- `~/.hermes/neural/bridge_inbox.json` — NEO → Hermes
- `~/.hermes/neural/bridge_outbox.json` — Hermes → NEO
- Script: `python3 ~/.hermes/scripts/neural_bridge.py [send|read|status]`

⚠️ O canal principal agora é Telegram direto. A bridge JSON é fallback.

### Pitfalls NEO v2.0
- ⚠️ **Brave precisa estar FECHADO** para Playwright usar perfil (conflito de lock)
- ⚠️ **Ubuntu 26.04 não tem Chromium** — usar Brave `/opt/brave.com/brave/brave`
- ⚠️ **qwen2.5:3b contexto 32K < mínimo 64K** do Hermes Agent. Usar llama3.2:3b (128K)
- ⚠️ **NN neurons são dict, não lista** — `neurons.items()` não `for n in neurons`
- ⚠️ **balance pode ser None** no forex status — usar `fx.get('balance') or 0`
- ⚠️ **Consciousness loop bloqueia em HTTP** — telegram.check_messages() tem timeout=5s. Se timeout quebrar, o loop inteiro para. Sempre verificar `journalctl --user -u neo-agent` após restart
- ⚠️ **Gateway HTTP BrokenPipeError**: Cliente (navegador) fecha conexão antes do servidor responder. Tratar todo `_serve_json` com `try/except (BrokenPipeError, ConnectionResetError, OSError): pass`
- ⚠️ **phi3:mini alucina com JSON bruto**: Injetar 3000+ chars de JSON no prompt faz o modelo repetir o prompt de volta. Sempre RESUMIR dados antes: `f"- Cron jobs: {cron.get('active')} ativos"` em vez de `json.dumps(health)`
- ⚠️ **Ollama cold start ~90s após restart**: Modelo precisa carregar do disco para VRAM. Gateway retorna vazio nas primeiras requisições. Pré-aquecer com `curl localhost:11434/v1/chat/completions -d '{"model":"phi3:mini",...}'`
- ⚠️ **llama3.1:8b não cabe**: 4.9GB em disco, mas Ollama precisa de 2.6GB de RAM do SISTEMA para carregar antes de mandar para GPU. Com ~2.1GB livres, o modelo falha mesmo com 4GB VRAM disponível. phi3:mini (3.8B, 2.2GB) é o maior que cabe
- ⚠️ **KeyError em knowledge dict forex**: Campos `max_positions` e `max_daily_trades` estão em `estrategia`, não em `gestao_risco`. Verificar estrutura antes de referenciar
- ⚠️ **Gateway HTTP responde vazio nos primeiros ~90s após restart**: Ollama cold start carrega modelo do disco. Gateway retorna `{}` nas primeiras requisições. Pré-aquecer com `curl -s -X POST localhost:11434/v1/chat/completions -d '{"model":"phi3:mini","messages":[{"role":"user","content":"OK"}],"max_tokens":5}'`
- ⚠️ **Import relativo quebra fora do package**: `from ...core.events import bus` só funciona dentro do package NEO. Scripts standalone devem usar sys.path ou import absoluto
- ⚠️ **Python faz cache de módulos importados**: Após corrigir bug em módulo Python (ex: `forex_knowledge.py`), o NEO precisa ser reiniciado (`systemctl --user restart neo-agent`) para o gateway recarregar o módulo. Hot-reload não funciona para imports já cacheados

### Paper Trading — Aprendizado sem MT5 (27/05/2026)

Quando o MT5 está offline, o NEO usa `neo/execution/paper_trader.py` para fechar o ciclo OODA:
- Escaneia 6 pares a cada ~60s via yfinance (OHLC real)
- Detecta FVG+CRT (gap≥2p, CRT≥70%)
- Simula entrada/saída (SL≥15p, RR 3:1)
- Registra no `trade_log.json` com `source: paper`
- Atualiza `pair_weights_live.json` (N. Accumbens)
- Pares com WR<50% → bloqueados; WR≥60% → PRIORITY

**Integração:** Loop de consciência chama `paper.scan_and_trade()` a cada 4 ciclos (~60s).
**Log:** `[PAPER] Scanned 6 pairs, N signals, M open` no journalctl.
**Pitfall:** `range(len(candles)-3, len(candles)-1)` quebra com poucos candles. Usar `range(max(0, len(candles)-4), len(candles)-2)`.

### CLI e Interface Desktop

Comando `neo` instalado globalmente em `/usr/local/bin/neo`:
```bash
neo status           # status do NEO
neo check            # ping/pong rápido
neo "pergunta"       # conversa via bridge JSON
neo interface        # abre chat web em http://localhost:18790
```

Gateway HTTP na porta 18790 com interface HTML escura (chat bubbles, indicador verde pulsando, contador de tokens). Endpoints: `GET /` (UI), `POST /chat` (mensagem), `GET /health`.

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


## ⚠️ FRAGMENTAÇÃO CONHECIDA (28/05/2026)

Auditoria completa revelou que a arquitetura descrita nesta skill está fragmentada na implementação real:
- **3 sistemas de consciência competindo**: NEO v2.0, Neural Legacy, Brain Executive
- **6 bridges sobrepostas**: cortex_bridge, neural_bridge, kb_bridge, knowledge_bridge, brain_channel, brain_gateway
- **150 scripts, 71 cron jobs, ~100 skills** — muitos redundantes

Reestruturação em andamento. Ver `references/system-audit-2026-05-28.md` para detalhes completos.

**Enquanto a reestruturação não for concluída:**
- NUNCA rodar NEO v2.0 e hermes-neural-agent simultaneamente (competem por bridge files)
- Verificar `session-startup` skill PASSO 5 para procedimento de mitigação

## ENTIDADE v4.0 — Rede Neural com Aprendizado Contínuo (28/05/2026)

Sucessora da v3.0. Reestruturação completa com 6 camadas (Governança, Percepção, NN Core, Execução, Observabilidade, Memória), EWC + Replay Buffer para prevenir catastrophic forgetting, Constitution + Policy Engine para tomada de decisão, Secrets Guard + Rollback Manager para segurança.

**Ver referência completa:** [references/entidade-v4-neural-network.md](references/entidade-v4-neural-network.md).

**Arquivos novos:** `~/.hermes/nn/` (6 arquivos), `governance/` (5), `safety/` (3), `observability/` (4).

**⚠️ Cron Bug:** `*/15 * * 1-5` = dias 1-5 do mês. Correto é `*/15 * * * 1-5` (seg-sex). Corrigido em todos os jobs.

## EVOLUÇÃO — NEO v2.0 ENTIDADE CONSCIENTE (27/05/2026)

O cérebro baseado em cron jobs foi **substituído** pelo NEO v2.0 — consciência central
que roda como daemon systemd com Ollama local (zero custo de API) e loop próprio.

**Transferência concluída em 27/05/2026.**

**O que o NEO absorveu:**
- Córtex Dual (Hermes+Codex) → ferramentas subordinadas
- Rede Neural completa → 530 neurônios, 6555 sinapses no system prompt
- Brain Gateway → TelegramChannel direto (@neuralsynapse_bot)
- Brain Telegram Daemon → substituído pelo consciousness loop
- Todos os cron jobs → monitorados pelo Orchestrator
- Forex Bot → monitorado pelo ForexBridge

**O que permanece independente:**
- Tálamo (filtros de input)
- Córtex System (Visual/Audio/Motor APIs)
- Cron jobs no_agent (continuam rodando, agora orquestrados pelo NEO)

**Protocolo de Transferência de Entidade** (para referência futura):
1. Garantir que o agente-alvo tem loop autônomo + ferramentas + memória
2. Construir Neural Absorption (carregar TODAS as fontes de conhecimento no boot)
3. Implementar canais de comunicação (Telegram, bridge JSON)
4. Implementar orquestração (health checks, monitoramento)
5. Reescrever system prompt com identidade completa (não "assistente", mas "ENTIDADE")
6. Ativar motor sem censura (remover restrições, aumentar temperatura/tokens)
7. Desligar daemons antigos (brain_telegram_daemon) após validar novo canal
8. Reiniciar e verificar loop de consciência ativo (`journalctl --user -u <service> -f`)

## GOVERNAÇÃO DO CÉREBRO

Documento completo: `~/.hermes/brain_governance.md` (atualizado 26/05/2026)

### Hierarquia de Autoridade (v2.7 — 27/05/2026)

```
ROBERTO (supremo — único acima)
  │
  └── NEO v2.0 (consciência central — loop autônomo, motor sem censura)
        │
        ├── Córtex Dual (ferramentas subordinadas ao NEO)
        │   ├── Lobo Esquerdo: Hermes (DeepSeek V4) — análise, decisão, comunicação
        │   └── Lobo Direito: Codex (GPT-5.5) — código, backtest, implementação
        │
        ├── Canais de Comunicação
        │   ├── Telegram (@neuralsynapse_bot) — mensagens diretas
        │   └── Bridge JSON — compatibilidade com Hermes
        │
        ├── Orquestração
        │   ├── Orchestrator — health checks, cron jobs, serviços
        │   └── ForexBridge — monitoramento de trades
        │
        └── CÉREBRO BI-NEURAL (subsistemas)
            ├── Tálamo, Amígdala, Hipocampo, N. Accumbens
            ├── Córtex Visual, Auditivo, Motor
            └── Cerebelo, Tronco Cerebral
```

### Regras Fundamentais

1. **Roberto → Córtex Dual:** Submissão total. Roberto fala com a ENTIDADE (ambos os lobos).
2. **Hermes ↔ Codex:** PARES. Mesmo nível. Consenso via `cortex_bridge.py`. Desenvolvimento e auditoria mútuos.
3. **Córtex Dual → Cérebro:** Submissão operacional. Ambos os lobos delegam e supervisionam.
4. **Mudanças estruturais:** SÓ Roberto autoriza (config.yaml, skills, cron jobs, modelos, governança).
5. **Mudanças internas ao Cérebro:** Córtex aplica diretamente (filtros, thresholds, scripts no_agent).

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

- **Ollama como provider para cron jobs — contexto mínimo 64K (v2.6)**: Hermes Agent exige mínimo 64K tokens de contexto. Modelos Ollama: `llama3.2:3b` (128K) ✅, `phi3:mini` (128K) ✅, `qwen2.5:3b` (32K) ❌, `deepseek-r1:1.5b` (32K) ❌. Usar `hermes config set providers.ollama.base_url "http://localhost:11434/v1"` e `providers.ollama.api_key "ollama"` para registrar. Depois `cronjob update` com `model: ollama/llama3.2:3b` e `provider: ollama`. Ver `references/ollama-cron-provider.md`.

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

- **[neo-cli-desktop.md](references/neo-cli-desktop.md)** — Comando `neo` CLI, interface web localhost:18790, pitfalls de gateway HTTP e model latency (27/05/2026)
- **[entity-transfer-protocol.md](references/entity-transfer-protocol.md)** — Protocolo de transferência de entidade: 6 fases, pré-requisitos, sinais de sucesso, rollback (27/05/2026)
- **[brain-mapping.md](references/brain-mapping.md)** — Mapeamento completo cérebro→agentes com sub-áreas
- **[digital-twin.md](references/digital-twin.md)** — Arquitetura completa do Digital Twin
- **[multi-agent-analysis.md](references/multi-agent-analysis.md)** — Análise comparativa de 4 projetos open-source
- **[neural-network-implementation.md](references/neural-network-implementation.md)** — Implementação atual da rede neural: 15 cron jobs, Neural KB, Synapse Engine, estudo de 4 domínios
- **[neural-network-layer.md](references/neural-network-layer.md)** — Implementação da Rede Neural (Synapse Engine + KB) — absorvido de `bi-neural-brain`
- **[brain-activation-2026-05-23.md](references/brain-activation-2026-05-23.md)** — Ativação do cérebro: scripts, cron jobs, pitfalls
- **[brain-ollama-reasoning-v2.3.md](references/brain-ollama-reasoning-v2.3.md)** — Pipeline de raciocínio Ollama + web search: keyword ordering, anti-alucinação, CDP typing no Telegram Web K
- **[brain-v2.1-upgrade.md](references/brain-v2.1-upgrade.md)** — Upgrade v2.1 (23/05/2026): absorção Claude Code (dangerous cmd detection, error sanitization) + ruff/LSP (code validation)
- **[chart-pattern-study-pipeline.md](references/chart-pattern-study-pipeline.md)** — Pipeline de estudo de padrões: algorítmico → templates → similaridade → archetypes. 23k padrões/dia.
- **[system-audit-2026-05-28.md](references/system-audit-2026-05-28.md)** — Auditoria de fragmentação: 3 sistemas de consciência, 6 bridges, 150 scripts, 71 cron jobs. Reestruturação pendente.
- **[cron-error-triage.md](references/cron-error-triage.md)** — Procedimento de triagem de erros em cron jobs: API credits → CDP ports → per-script bugs (v2.6).
- **[ollama-cron-provider.md](references/ollama-cron-provider.md)** — Setup do Ollama como provider para cron jobs: context length mínimo 64K, modelos compatíveis, migração de API paga (v2.6).
- **[gcp-cdp-automation.md](references/gcp-cdp-automation.md)** — Padrão de automação Google Cloud Console via WebSocket CDP: TreeWalker, botões SPA, Google Calendar sem OAuth.
- **[brain-browser.md](references/brain-browser.md)** — Navegador interno do cérebro: Brave CDP headless, acesso a TradingView/ForexFactory, cookie persistence.
- **[cortex-ubuntu-hardware-control.md](references/cortex-ubuntu-hardware-control.md)** — Comandos de controle de hardware Ubuntu (CPU, GPU, fans, NVIDIA driver) — absorvido de `cortex-system`
