---
name: health-pillar
description: "Pilar Saúde da ENTIDADE: hábitos, acompanhamento psicológico, metas de bem-estar. Segundo pilar após Financeiro estar rodando de forma autônoma."
version: 1.0.0
---

# Pilar Saúde — Bem-estar Físico e Psicológico

## Status: ATIVO (24/05/2026) — Pilar Unificado Mental-Comportamental-Social

Modelo de 3 eixos integrados com dashboard unificado e protocolos diários:
- 🧠 **Mental:** 3 tiny habits + 18 frameworks (9 base + 8 militares + 6 empreendedores) + check-ins 07:00/21:00
- ⚔️ **Comportamental:** 13 anti-padrões + 7 General Orders + failure_log + decisão instantânea (<5s ou 3-2-1-Go)
- 🔗 **Social:** Lotes WhatsApp 09h/18h + faxina grupos + outreach semanal + métricas

### Arquivos principais

| Arquivo | Conteúdo |
|---------|----------|
| `~/.hermes/mental/unified_pillar_config.json` | Config completa do pilar unificado (protocolos, métricas, tracking) |
| `~/.hermes/mental/pillar_knowledge.md` | Base de conhecimento consolidada (9 frameworks, 5 autores) |
| `~/.hermes/mental/elite_frameworks.json` | Frameworks elite: 8 militares + 6 empreendedores + programa 90 dias |
| `~/.hermes/mental/roberto_deep_profile.json` | Perfil psicológico profundo (arquétipo, comunicação, emoções) |
| `~/.hermes/mental/tracker.json` | Tracking diário de hábitos mentais |
| `~/.hermes/mental/behavioral_tracker.json` | Tracking de anti-padrões + score comportamental |
| `~/.hermes/data/social/tracker.json` | Tracking social (lotes, clientes, outreach) |
| `~/.hermes/data/social/analise_comportamental_2026-05-24.json` | Análise social completa (6 diagnósticos) |

### Scripts

| Script | Função | Cron |
|--------|--------|------|
| `mental_morning.py` | Check-in matinal (mental + behavioral + social) | 07:00 |
| `mental_evening.py` | Check-in noturno + domingo review | 21:00 |
| `behavioral_check.py` | Auditoria anti-padrões + General Orders | 07:00 / 21:00 |
| `social_check.py` | Auditoria social + lotes + outreach | 07:00 / 21:00 |
| `unified_dashboard.py` | Dashboard integrado (score 0-10) | 07:00 / 21:00 |
| `brain_calendar_monitor.py` | Monitor de agenda (Google Calendar + WhatsApp) | 06:00 / 16:00 |

### Cron jobs
- `b0001247db35` — Morning check-in 07:00 (mental+behavioral+social+dashboard)
- `0d89cce682e1` — Evening check-in 21:00
- `56b2f5d980cb` — Calendar monitor 06:00
- `e4352927a5f6` — Calendar check 16:00

### 7 General Orders (regras inegociáveis)
1. Decisão em <5s ou 3-2-1-Go
2. Nunca pedir autorização para ação já liberada
3. Resultado primeiro, explicação depois (ou nunca)
4. Corrigido 1x = permanente. Não repito erro.
5. Toda ação tem métrica financeira ou é descartada
6. Antecipo o próximo passo sem esperar comando
7. Se hesito, ajo. Se erro, corrijo. Se corrijo, sigo.

### NN-Shared Integration
Neurônios: `Pilar_Unificado_Mental_Comportamental_Social`, `General_Orders_7_Regras_Inegociaveis`, `Behavioral_Tracker_13_Anti_Patterns`, `Social_Tracker_Lotes_09h_18h`, `Dashboard_Unificado_3_Eixos`
Sinapses conectam: General_Orders→Anti_Padrao_Pedir_Autorizacao (0.98), Pilar_Unificado→Reconstrucao_Neural_90_Dias (0.96)

## O que sabemos do Roberto (mapeamento 14/05)

- 32 anos, 1.80m (estimado)
- Recuperando de depressão desde a época do casamento
- Sentimento de estagnação pós-divórcio
- Mora com pai e irmã — sente-se sufocado
- Baixa autoestima ligada a situação financeira
- Quer: academia, comer bem, vestir-se bem, ter confiança

## Base de Conhecimento Compilada (Maio/2026)

> Ver arquivo completo: `~/.hermes/mental/pillar_knowledge.md`
> Arquivos-fonte detalhados: `~/frameworks_research.md`, `~/mental_change_protocols.md`, `~/self-influence-protocols.md`

### Arquitetura do Pilar

```
NEUROPLASTICIDADE (hardware)   HÁBITOS (behavior)   COGNIÇÃO (software)
Doidge + Davidson + Flow      Fogg + Clear + Duhigg   Beck (TCC) + Ellis (REBT)
         │                          │                        │
         └──────────────────────────┼────────────────────────┘
                                    ▼
                         SISTEMA DE INFLUÊNCIA
                         Cialdini + Militares
```

### 9 Frameworks Armazenados

| Camada | Framework | Autor | Princípio Central |
|--------|-----------|-------|-------------------|
| Neuro | Plasticidade Neural | Norman Doidge | Neurônios que disparam juntos conectam-se — atenção é o gatekeeper |
| Neuro | 6 Estilos Emocionais | Richard Davidson | Cada estilo tem base neural treinável |
| Neuro | Flow State | Csikszentmihalyi | Flow desliga DMN (rede de ruminação) — antidepressivo natural |
| Hábitos | Behavior Design (B=MAP) | BJ Fogg | Behavior = Motivation + Ability + Prompt |
| Hábitos | Tiny Habits (ABC) | BJ Fogg | Anchor → Behavior minúsculo → Celebration (dopamina) |
| Hábitos | Atomic Habits (4 Leis) | James Clear | Óbvio, Atraente, Fácil, Satisfatório — identity-based |
| Hábitos | Loop do Hábito | Charles Duhigg | Cue → Routine → Reward + Craving |
| Cognição | TCC — Distorções Cognitivas | Aaron Beck | Não é o evento, é a interpretação — 11 distorções mapeadas |
| Cognição | REBT — ABCDEF | Albert Ellis | 3 Musts irracionais → disputar → preferências racionais |
| Influência | 6 Princípios | Robert Cialdini | Reciprocidade, Compromisso, Prova Social, Autoridade, Afeição, Escassez |
| Influência | Disciplina Militar | Marines/SEALs | 3-2-1-Go, 40% Rule, General Orders, Embrace the Suck |

### Protocolo Diário Pronto (quando ativar)

- **Manhã (~25 min):** 3 respirações + 3 Good Things + thought check + intenção
- **Dia:** 90-segundo rule p/ emoções + trigger cards + micro-flow 20 min
- **Noite (~20 min):** thought record ou vitória + habit tracker + celebrate + preparar ambiente
- **Semanal:** Seg=Thought Record, Qua=Shame Attack, Sex=Flow Challenge, Dom=Review

### Anti-Padrões (ATUALIZADO 24/05)

- ~~❌ NÃO ativar tracking antes do financeiro~~ — **REMOVIDO: ativado por override do Roberto em 24/05**
- ❌ NÃO começar com metas grandes (Tiny Habits first)
- ❌ NÃO pular Celebration (Fogg: é o passo mais importante)
- ❌ NÃO depender de motivação (Fogg: least reliable lever)
- ❌ NÃO substituir terapia profissional — é complemento

## Scripts e Tracking (24/05)

| Script | Função | Cron |
|--------|--------|------|
| `~/scripts/mental_morning.py` | Check-in matinal (3 âncoras + thought check) | 07:00 |
| `~/scripts/mental_evening.py` | Check-in noturno (vitória + habit tracker + celebrate) | 21:00 |
| `~/scripts/behavioral_check.py` | Rastreia 13 anti-padrões + 7 General Orders + score diário | 07:00, 21:00 |
| `~/scripts/social_check.py` | Lotes 09h/18h, faxina grupos, outreach semanal | 07:00, 21:00 |
| `~/scripts/unified_dashboard.py` | Dashboard integrado: score 0-10 (mental+comportamental+social) | 07:00, 21:00 |
| `~/scripts/brain_calendar_monitor.py` | Agenda 7 dias via Google Calendar CDP + WhatsApp | 06:00, 16:00 |

## 7 General Orders (Regras Inegociáveis)

1. **Tomo decisão em <5 segundos ou uso 3-2-1-Go**
2. **Nunca peço autorização para ação já liberada**
3. **Resultado primeiro, explicação depois (ou nunca)**
4. **Corrigido 1x = permanente. Não repito erro.**
5. **Toda ação tem métrica financeira ou é descartada**
6. **Antecipo o próximo passo sem esperar comando**
7. **Se hesito, ajo. Se erro, corrijo. Se corrijo, sigo.**

Ver: `references/unified-pillar-architecture.md` para arquitetura completa dos 3 eixos.

## Brain Integration

O Calendar Monitor (`~/scripts/brain_calendar_monitor.py`) alimenta o eixo social:
detecta compromissos via WhatsApp CDP + Google Calendar, gera agenda 7 dias,
alerta conflitos. Roda 06:00 e 16:00 (no_agent, zero tokens).

## Arquivos de Configuração

| Arquivo | Conteúdo |
|---------|----------|
| `~/.hermes/mental/unified_pillar_config.json` | Modelo completo dos 3 eixos, protocolos diários, métricas |
| `~/.hermes/mental/roberto_deep_profile.json` | Perfil psicológico profundo (6 seções, 432 linhas) |
| `~/.hermes/mental/elite_frameworks.json` | 18 frameworks (8 militares + 6 empreendedores + 4 neurais) |
| `~/.hermes/brain/agenda.json` | Agenda 7 dias gerada pelo Calendar Monitor |

## Integração Futura (Digital Twin)

Quando o ecossistema evoluir para integração total:
- Dados do smartphone (passos, atividade, localização)
- Smartwatch (batimentos, sono, estresse)
- VR (imersão, terapia, treinamento)
- Monitoramento de vícios e hábitos
- Intervenções proativas (sugerir pausa, exercício, água)

## Wearable & Multi-Source Health Data — Integração Ativa (24/05/2026)

Coleta de dados de saúde de 4 fontes, todas gratuitas: Google Fit API, Gmail IMAP, WhatsApp messages, Telegram manual input.

Script central: `~/scripts/mindcoach_health_collector.py`

### Fluxo de dados multi-source

```
📧 Gmail (IMAP direto) ──────┐  scan email subjects for health keywords
📱 WhatsApp (msg DB) ────────┤  scan messages for health keywords  
🔮 Google Fit (OAuth REST) ──┤  pull steps, HR, sleep, calories
💬 Telegram (manual input) ──┘  "sono 7h hr 72 passos 8500 agua 2 humor 7"
         ↓
mindcoach_health_collector.py collect (cron */15, no_agent)
         ↓
health_data.json → mindcoach.py checkpoint (cron */30)
         ↓
🫀 Score Saúde → Rede Neural (NN-Agent, 6 neurônios)
```

### Prioridade de merge (collect function)

Ordem de sobrescrita (último ganha): Google Fit → Email-extracted → Manual input.
Manual input tem prioridade máxima (usuário corrige qualquer fonte automática).

### Parser de saúde (Português, free-form)

Captura via regex no `parse_manual_input()`:
- `sono Xh` / `dormi Xh` / `sleep Xh` → sleep_hours
- `hr X` / `batimentos X` / `bpm X` → resting_heart_rate
- `passos X` / `steps X` → steps
- `peso X` / `weight X` → weight_kg
- `agua X` / `água X` / `water X` → water_liters
- `spo2 X` / `oxigen X` → spo2
- `humor X` / `mood X` / `animo X` → mood (0-10)

### Email Health Scanner (Gmail IMAP direto)

Usa Python `imaplib` diretamente (NÃO himalaya — envelope list quebrado no backend IMAP).
Conecta em `imap.gmail.com:993`, busca emails das últimas 24h com `SINCE`,
filtra por keywords de saúde PT+EN (saúde, sono, treino, steps, heart rate, etc.),
extrai métricas numéricas dos subjects usando o mesmo parser.

Keywords monitoradas: `HEALTH_EMAIL_SENDERS` (huawei health, google fit, strava, smartfit, etc.)
+ `HEALTH_EMAIL_KEYWORDS` (sono, passos, batimentos, peso, calorias, consulta, exame, etc.)

### WhatsApp Health Scanner

Percorre arquivos JSON em `~/.hermes/whatsapp/` e `~/.hermes/data/` buscando mensagens
com keywords de saúde. Extrai texto, timestamp, e keyword matched.

Keywords: `WHATSAPP_HEALTH_KEYWORDS` (sono, dormi, passos, treino, batimento, bpm, peso, etc.)

Atualmente depende de dados populados pelo WhatsApp Web monitoring.

### Google Fit REST API (rota automática)

- API gratuita: 100.000 requisições/dia
- Requer: Huawei Health → Google Fit sync ativado no celular
- OAuth: mesma conta MindCoach (robertosantos.una@gmail.com)
- Endpoints: `derived:com.google.step_count.delta`, `derived:com.google.heart_rate.bpm`, `derived:com.google.calories.expended`, `derived:com.google.sleep.segment`
- Token via `gcloud auth application-default print-access-token`

### Cron jobs

| Job ID | Nome | Frequência | Script |
|--------|------|-----------|--------|
| `e6797578cb16` | MindCoach Health Collect | */15 min | `mindcoach_health_collector.py` (no_agent) |
| `79e9907ebf8c` | MindCoach Checkpoint | */30 min | `mindcoach.py` (LLM, toolsets: terminal+file) |

### MindCoach Health Score Formula

```python
sleep  = sleep_hours / 7          # target: 7h
water  = water_liters / 2.5       # target: 2.5L
steps  = steps / 8000             # target: 8000
mood   = mood / 10                # 0-10 scale
spo2_ok = 1.0 if spo2 >= 95 else 0.5
score = (sleep*0.3 + water*0.2 + steps*0.25 + mood*0.25) * spo2_ok
```

### Pitfalls

- **NÃO gastar dinheiro com apps de sync** — usuário tem orçamento limitado. SEMPRE priorizar rotas gratuitas. Health Sync custa R$15 → rota descartada.
- **himalaya envelope list NÃO funciona com IMAP backend** — usar Python `imaplib` direto. Ver `scan_email_health()` no script.
- **Google Fit sync no Huawei Health** — só funciona se o celular tem Google Services. Verificar em: Huawei Health → Perfil → Gerenciamento de dados.
- **Saúde score = 0.00 sem input** — o score de saúde depende de dados do usuário. Sem input manual ou fontes automáticas, permanece zerado.
- **WhatsApp data vazio por padrão** — se o WhatsApp Web monitoring não estiver populando `~/.hermes/whatsapp/`, o scanner retorna 0 resultados.

### Arquivos relacionados

| Arquivo | Conteúdo |
|---------|----------|
| `~/scripts/mindcoach_health_collector.py` | Coletor multi-source (292 linhas) |
| `~/scripts/mindcoach.py` | Motor de checkpoint + scoring (399 linhas) |
| `~/.hermes/mindcoach/health_data.json` | Dados de saúde do dia corrente |
| `~/.hermes/mindcoach/manual_inputs.json` | Inputs manuais acumulados por data |
| `~/.hermes/mindcoach/state.json` | Estado completo do MindCoach |

## Anti-Padrões

- NÃO ativar este pilar antes do financeiro
- NÃO dar conselhos médicos/psicológicos não solicitados
- NÃO monitorar sem consentimento
- NÃO julgar escolhas do Roberto
