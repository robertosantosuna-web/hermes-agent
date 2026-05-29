# Ciclo OODA Neural — Arquitetura de Auto-Evolução

**Data de implementação:** 26/05/2026 23:30 BRT  
**Status:** ATIVO — todos os 5 módulos límbicos + NN Engine + Meta-Observer

## O Problema (Antes)

O sistema era um **autômato** — scripts rodando em cron fixo, sem feedback:
```
Trade → Perda → AutoPilot fecha → WR cai → Bot BLOQUEIA par → MENOS trades → ESTAGNA
```
- Módulos límbicos PAUSADOS desde 25/05
- Redes neurais (507 neurônios, 6555 sinapses) DORMENTES
- Codex observava mas não AGIA
- Nenhum componente verificava saúde dos outros
- Pipelines quebrados (output sem consumidor) nunca detectados

## A Solução (Depois)

### Camada 1 — Coleta de Dados
Todos os scripts `no_agent` rodam em cron e escrevem em arquivos de estado:
- `monitor.py` → `monitor/alerts.json` (freelas)
- `forex_bot_multi.py` → `trade_log.json` (trades)
- `brain_signal_generator.py` → `signals_pending.json` (sinais)

### Camada 2 — Aprendizado (Sistema Límbico)

| Módulo | Cron | Função | Input → Output |
|--------|------|--------|----------------|
| **N. Accumbens** | */4h | Reinforcement learning | `trade_log.json` → `pair_weights_live.json` |
| **Hippocampus** | */6h | Pattern consolidation | `neural_knowledge_base.json` → redes neurais |
| **Amygdala** | */15min | Threat detection | `cerebellum_state.json` → alerts |
| **Brain Research** | */4h | Auto-development | pesquisa autônoma |
| **Synapse Engine** | */4h | Cross-pollination | cruza outputs de todos os módulos |

### Camada 3 — Ajuste de Parâmetros (Codex)
- **Codex Monitor** (48425c92b336): */30min, GPT-5.5 via OpenRouter
- **AGE** (não só observa): modifica `MAX_POSITIONS`, `MIN_SL_PIPS`, `RISK_PERCENT`
- Regras de ação:
  - Drawdown > 3% → reduz MAX_POSITIONS
  - WR < 40% → aumenta MIN_SL_PIPS
  - Equity > $420 → aumenta RISK_PERCENT
  - Concentração > 3 → fecha excesso

### Camada 4 — Feed-Forward Neural (NN Engine)
- **NN Engine** (f91ee6baae41): diário às 02:00 BRT
- Feed-forward: ativa neurônios com dados frescos
- Backpropagation: ajusta pesos com resultados de trades
- Cross-pollination: compartilha sinapses entre Brain, Agent, Shared
- **Primeira execução:** +140 sinapses criadas

### Camada 5 — Meta-Consciência (Meta-Observer)
- **Meta-Observer** (2faff491215b): */15 minutos
- Verifica 16 pipelines (output → consumidor)
- Detecta gaps (broken, orphan, unread, stale, missing)
- Reporta saúde (score %) 
- Detecta processos mortos

## O Ciclo Completo

```
┌─────────────────────────────────────────────────────────┐
│                    CICLO OODA NEURAL                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  OBSERVE:  monitor.py, brain_signal_generator,          │
│            forex_bot_multi.py, resiliencia.sh            │
│       ↓                                                  │
│  ORIENT:   Amygdala (threats), Hippocampus (patterns),   │
│            Cerebellum (validation), Executive (state)    │
│       ↓                                                  │
│  DECIDE:   N. Accumbens (weights), Brain Research,       │
│            Synapse Engine (cross-pollination),           │
│            Codex Monitor (parameter adjustment)          │
│       ↓                                                  │
│  ACT:      forex_bot_multi.py (abre trades),             │
│            forex_autopilot.py (gerencia),                │
│            realtime_monitor.py (trailing/breakeven)      │
│       ↓                                                  │
│  FEEDBACK: NN Engine (feed-forward + backprop),          │
│            Meta-Observer (health check),                 │
│            pair_weights_live.json → bot WR dinâmico      │
│       ↓                                                  │
│  (retorna ao OBSERVE com parâmetros melhorados)          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Métricas de Saúde

| Métrica | Antes (23:00) | Depois (00:06) |
|---------|---------------|-----------------|
| Módulos límbicos ativos | 0/5 | 5/5 |
| Pipelines saudáveis | 11/16 (68%) | 15/16 (93.8%) |
| Redes neurais ativas | 0/3 | 3/3 |
| Feed-forward diário | ❌ | ✅ 02:00 BRT |
| Codex age | ❌ (só observa) | ✅ (modifica parâmetros) |
| WR dinâmico | ❌ (estático) | ✅ (70% live, 30% backtest) |
| Meta-observação | ❌ | ✅ */15min |
| Freelas → Telegram | ❌ (Motor pausado) | ✅ */5min |
| Resiliência → consumidor | ❌ (ninguém lia) | ✅ Meta-Observer |

## Cron Jobs do Sistema Neural

| Job ID | Nome | Schedule | Função |
|--------|------|----------|--------|
| 853991c6f44b | Amygdala | */15min | Threat detection |
| 6ae254c0b104 | N. Accumbens | */4h | Reinforcement learning |
| b0b848ba83d1 | Hippocampus | */6h | Pattern consolidation |
| 0554b5690934 | Brain Research | */4h | Auto-development |
| 5e4e461f6c80 | Synapse Engine | */4h | Cross-pollination |
| f91ee6baae41 | NN Engine | 02:00/dia | Feed-forward + backprop |
| 2faff491215b | Meta-Observer | */15min | Pipeline health |
| 48425c92b336 | Codex Monitor | */30min | Age (modifica parâmetros) |
