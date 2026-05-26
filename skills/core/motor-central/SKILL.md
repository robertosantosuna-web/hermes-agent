---
name: motor-central
description: Arquitetura de monitoramento contínuo com mínimo consumo de tokens. Camada 1 (motor_central.py) coleta dados de renda e trade localmente sem LLM. Camada 2 (escalação) só aciona o LLM quando há flags relevantes.
---

# Motor Central — Arquitetura de Duas Camadas

**📊 Stack monitoramento: `motor-central` (coleta+escalação) → alimenta `dashboard` (visualização). `system-health` monitora hardware (CPU/RAM/disco). Use motor-central para pipeline de dados, dashboard para visão geral, system-health para alertas de infra.**

## Princípio

Sistema local faz TODO o trabalho pesado (coleta, parsing, análise). LLM só entra quando necessário — para julgamento, priorização e decisão.

```
┌──────────────────────────────────────────┐
│ CAMADA 1: Coleta (Zero Tokens)          │
│ motor_central.py — cada 10 min          │
│ no_agent=true, deliver=local            │
│                                          │
│ 📧 Email (IMAP): 99Freelas, Fiverr...   │
│ ⚡ Forex M5: Yahoo Finance + análise    │
│                                          │
│ Output: JSON → ~/.hermes/cron/output/   │
└──────────────┬───────────────────────────┘
               │ context_from
               ▼
┌──────────────────────────────────────────┐
│ CAMADA 2: Escalação (LLM mínimo)        │
│ Escalation Agent — cada 15 min          │
│ deliver=origin (Telegram)               │
│                                          │
│ Se 0 flags → "✅" (1 token)             │
│ Se LOW → "📊 N sinais fracos" (poucos)  │
│ Se HIGH/MEDIUM → briefing estruturado   │
└──────────────────────────────────────────┘
```

## Arquivos

| Arquivo | Função |
|---------|--------|
| `~/.hermes/scripts/motor_central.py` | Coleta unificada (email + forex, killzones + CRT) |
| `~/.hermes/scripts/resiliencia.sh` | Health check automático (CDP, wtype, disco, mem) — cada 30 min |

## Cron Jobs

| Job ID | Nome | Schedule | Tipo | Status |
|--------|------|----------|------|--------|
| `450c131d281f` | 🔍 Motor Central — Coleta | */10 * * * * | no_agent, local | ativo |
| `d8d0e9c72a99` | 🧠 Motor Central — Escalação | */15 * * * * | LLM, origin | ativo |
| `5278a8375b63` | 🇧🇷 London Close T-2 | 58 11 * * 1-5 | no_agent, origin | **único killzone ativo** |
| `03841690b459` | 🛡️ Resiliência ENTIDADE | */30 * * * * | no_agent, local | ativo |
| ~~`ede982fa7428`~~ | ~~🇬🇧 London T-2~~ | — | — | ❌ desativado (backtest negativo 18/05) |
| ~~`0ebf8fdb96bd`~~ | ~~🇺🇸 NY T-2~~ | — | — | ❌ desativado (backtest negativo 18/05) |

## Flags de Escalação

| Prioridade | Tipo | Significado |
|-----------|------|-------------|
| 🔴 HIGH | CLIENT_MSG | Mensagem nova de cliente |
| 🔴 HIGH | PAYMENT | Pagamento ou problema financeiro |
| 🟡 MEDIUM | NEW_PROJECT | Novo projeto nas plataformas |
| 🟡 MEDIUM | SIGNAL_STRONG | Sinal trade com score >= 3.5 |
| 🟢 LOW | SIGNAL | Sinal trade com score >= 2.0 |
| ⚪ INFO | BLACKOUT | Bloqueio por notícias |

## Economia de Tokens

Antes (sem motor):
- Email: ~2000 tokens/scan × 12/dia = 24.000/dia
- Trade: ~1500 tokens/análise × 24/dia = 36.000/dia
- Total: ~60.000 tokens/dia

Depois (com motor):
- Coleta: 0 tokens (no_agent)
- Escalação sem flags: ~5 tokens × 96/dia = 480/dia
- Escalação com flags: ~200 tokens × 12/dia = 2.400/dia
- Total típico: ~1.000-3.000 tokens/dia

**Redução: ~95-98%**

## Referências

- `references/killzones-ict.md` — Horários ICT, estratégia CRT, parâmetros validados, fontes do grupo Sociedade Secreta do Cifrão

## Referências

| Arquivo | Conteúdo |
|---------|----------|
| `references/killzones-ict.md` | Horários exatos dos 3 picos de volume, estratégia CRT, parâmetros validados, simulação 18/05 |
| `references/edge-cdp-automation.md` | Técnica de automação via Edge CDP porta 9222 — interagir com páginas logadas sem Cloudflare |
