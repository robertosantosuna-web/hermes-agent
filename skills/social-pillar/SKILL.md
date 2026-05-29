---
name: social-pillar
description: "Pilar Social da ENTIDADE: engenharia comportamental e social, mapeamento de relações, análise de redes de contato, padrões de interação, influência e dinâmica de grupos."
category: core
---

# Pilar Social — Engenharia Comportamental e Social

## Status: ATIVO (analise profunda 24/05/2026)

### Segunda analise (24/05/2026 — Analise Comportamental Completa)

**Fontes:** WhatsApp (66 conversas, 2617 nao lidas) + Telegram (13 conversas, 0 nao lidas)

#### 6 Diagnosticos Comportamentais

| # | Diagnostico | Gravidade |
|---|-------------|-----------|
| 1 | Sobrecarga de Informacao (2617 msgs nao lidas) | 🔴 ALTA |
| 2 | Subscriber Fantasma (8 comunidades, 1539 msgs) | 🔴 ALTA |
| 3 | Hiperfoco Familiar (7/9 familia, 10/49 social) | 🟡 MEDIA |
| 4 | Rede Social Inchada (66 WA vs 13 TG, superficial) | 🟡 MEDIA |
| 5 | Evitacao de Compromisso Social (nao sai, nao silencia) | 🟡 MEDIA |
| 6 | Baixa Manutencao de Relacoes Antigas (abandonos) | 🟡 MEDIA |

#### Plano de Correcao (5 acoes)
1. FAXINA SOCIAL IMEDIATA — Hoje: sair de grupos nao lidos, silenciar, arquivar. Meta: 66→25 conversas
2. SISTEMA DE RESPOSTA EM LOTES — Diario: 2 horarios fixos (09h/18h), WhatsApp fechado fora disso
3. RECONSTRUIR RELACOES ABANDONADAS — Esta semana: Germanio Pai (206d), Mae TG (565d)
4. REGRA ANTI-SUBSCRIBER — Permanente: delay 24h antes de entrar, 1-in-1-out, max 3 grupos
5. TREINO DE ASSERTIVIDADE — Continuo: dizer nao, sair de grupos = autocuidado

#### Metricas-Alvo (semanais)
- Msgs nao lidas: 2617 → <50
- Conversas pendentes: 14 → <5
- Grupos ativos: ? → max 3
- Novas conversas/semana: 0 → min 1
- Relacoes recuperadas/mes: 0 → min 2

**Relatorio completo:** `~/.hermes/data/social/analise_comportamental_2026-05-24.json`

---

**Primeira análise (24/05/2026):** 73 contatos mapeados, 11 interações prolongadas detectadas.

### Descobertas principais (analise 1)

| # | Contato | Mensagens | Período | Tipo | Áudios |
|---|---------|-----------|---------|------|--------|
| 1 | Dinei Cleia | 2000+ | 3.8 anos | Social | 627 |
| 2 | Germanio | 2000+ | 3.3 anos | Social | 601 |
| 3 | Automatizando | 2000+ | 1.5 anos | Grupo | 345 |
| 4 | Germanio Pai | 200 | 1.8 anos | Família | 172 |
| 5 | Mãe | 438 | 3.1 anos | Família | 111 |
| 6 | RigSimtac | 1835 | 2.3 anos | Social | 66 |

**Distribuição:** 44 sociais, 11 serviços, 7 família, 7 trabalho, 4 grupos.

## Sub-áreas

### 1. Engenharia Comportamental
- Análise de padrões de comunicação (frequência, horários, reciprocidade)
- Detecção de relações de alta intensidade/interação prolongada
- Identificação de influenciadores e nós centrais na rede
- Padrões de linguagem e tom por interlocutor

### 2. Engenharia Social
- Mapeamento da rede de contatos (grafo social)
- Classificação de relações: família, trabalho, networking, serviços
- Detecção de oportunidades via rede (indicações, projetos)
- Análise de grupos e comunidades

### 3. Métricas

| Métrica | Descrição | Fonte |
|---------|-----------|-------|
| Frequência | Mensagens/dia por contato | Telegram + WhatsApp |
| Duração | Período total da relação | Datas primeira/última msg |
| Reciprocidade | Ratio msg enviadas/recebidas | Direção das mensagens |
| Intensidade | Volume total de interação | Contagem total |
| Profundidade | Tamanho médio das mensagens | Caracteres/msg |

### 4. Fontes de Dados

| Plataforma | Acesso | Status |
|-----------|--------|--------|
| Telegram | Telethon API | 13 conversas |
| WhatsApp | Edge CDP :9224 | 105 conversas |
| 99Freelas | Brave CDP | Mensagens de projetos |
| Instagram | Brave CDP :9222 | `~/.hermes/brain/instagram_monitor.py` |

## Protocolo Diário (24/05/2026)

Integrado ao Pilar Unificado (ver skill `health-pillar` e `references/unified-pillar-architecture.md`).

**Lotes de resposta:** 09h e 18h — WhatsApp aberto apenas nesses horários (máx 15 min cada).
**Faxina de grupos:** Quarta-feira — sair de 1 grupo inativo.
**Outreach:** Segunda-feira — retomar 1 contato abandonado.
**Auditoria completa:** Domingo — revisar pendências, métricas, planejar semana.

Script: `~/scripts/social_check.py` (roda 07:00 e 21:00 via cron).

```
1. Extrair mensagens de todas as plataformas
2. Consolidar por contato (cross-platform)
3. Calcular métricas de interação
4. Classificar relações (família, trabalho, social, serviço)
5. Gerar grafo social
6. Identificar padrões e oportunidades
7. Reportar insights
```

## Integração com NN-Shared

Descobertas deste pilar alimentam a rede neural compartilhada:
- Padrões de comunicação bem-sucedidos → sinapses de alta confiança
- Relações de alto valor → neurônios priorizados
- Oportunidades via rede → alertas para pilar financeiro

## Protocolo Diário (24/05)

Integrado ao Pilar Unificado Mental+Comportamental+Social.

### Lotes de Resposta
- 🌅 **09h**: Abrir WhatsApp, responder pendências (máx 15 min). Fechar após.
- 🌆 **18h**: Abrir WhatsApp, responder pendências (máx 15 min). Fechar após.
- 🔒 **Fora dos lotes**: WhatsApp fechado. Zero notificações.

### Ritual Semanal
- **Segunda**: Outreach — retomar 1 contato abandonado
- **Quarta**: Faxina de grupos — sair de 1 inativo
- **Domingo**: Auditoria completa + planejar outreach da semana

### Tracking
- Script: `~/scripts/social_check.py` (roda nos check-ins 07:00 e 21:00)
- Tracker: `~/.hermes/data/social/tracker.json`
- Dashboard unificado: `~/scripts/unified_dashboard.py`
