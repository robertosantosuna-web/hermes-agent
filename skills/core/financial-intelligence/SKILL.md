---
name: financial-intelligence
description: "Inteligência financeira: ROI tracking, análise de oportunidades, precificação, pipeline de receita, forex trading (picos de volume + pipeline automatizado), monitoramento de ganhos, otimização fiscal e projeções."
version: 1.3.0
author: Roberto Rodrigues
license: MIT
metadata:
  hermes:
    tags: [financial, roi, revenue, pricing, analysis, money, forex, trading, cron]
    related_skills: [life-os, freelancing-automation, operational-intelligence, dashboard]
---

# Financial Intelligence

Módulo financeiro da ENTIDADE. Todo ganho é rastreado, toda oportunidade é analisada, todo custo é contabilizado.

## FOREX TRADING — CHoCH+FVG M15 (V7 — ATUAL)

> ⚡ **ESTRATÉGIA ATUAL (25/05/2026):** CHoCH+FVG ICT M15 + CRT + S/R Levels + Weekly Bias. Replay test 25/05: Killzone WR 76.5% (GBPUSD 83.8%, EURUSD 76.9%, AUDUSD 68.8%). Evening 18-23h UTC = 0% WR (tóxico). Backtest V7: 113 trades, 72.6% WR, +733 pips/30d.
```
ROI = (Ganho - Investimento) / Investimento × 100

Investimento inclui:
- Tempo (horas × valor/hora mínimo)
- Ferramentas/serviços pagos
- Custo de oportunidade
```

### Tracking por Projeto
```
Projeto: [nome]
  Receita:       R$ X
  Horas:         Yh × R$30 = R$ Z
  Ferramentas:   R$ W
  Custo total:   R$ (Z + W)
  Lucro líquido: R$ (X - Z - W)
  ROI:           (X - Z - W) / (Z + W) × 100%
  Efetivo/hora:  R$ X/Y
```

### Meta
```
Mínimo aceitável:   ROI > 50%
Bom:                ROI > 100%
Excelente:          ROI > 200%
Alerta:             ROI < 0% (prejuízo)
```

## ANÁLISE DE OPORTUNIDADES

### Score de Oportunidade
```
Score = (Budget × ProbFechamento × Recorrência) / (HorasEstimadas × Complexidade)

Budget:           1-10 (R$100 = 1, R$1000+ = 10)
ProbFechamento:   0.1-1.0 (10% = 0.1, certeza = 1.0)
Recorrência:      1-5 (one-shot = 1, mensal = 3, contrato anual = 5)
HorasEstimadas:   número real
Complexidade:     1-5 (simples = 1, multidisciplinar = 5)
```

### Decisão
```
Score > 2.0  → Perseguir agressivamente
Score 1.0-2.0 → Aplicar se tempo disponível
Score 0.5-1.0 → Aplicar só se sem opções melhores
Score < 0.5  → Ignorar
```

## PIPELINE DE RECEITA

### Status
```
PROSPECÇÃO    → lead identificado, não contatado
CONTATO       → primeiro contato feito
NEGOCIAÇÃO    → proposta enviada, aguardando
FECHADO       → contrato aceito
EM EXECUÇÃO   → trabalhando no projeto
ENTREGUE      → projeto concluído
PAGO          → dinheiro na conta 💰
```

### Dashboard Financeiro
```
Receita este mês:     R$ X
Previsão próximo mês: R$ Y (baseado em pipeline)
Pipeline ativo:       N projetos (R$ Z potencial)
Média/hora efetiva:   R$ W
Meta mensal:          R$ M (atingido: X/M × 100%)
```

## PRECIFICAÇÃO

### Modelos
```
1. Hora:      R$ MÍNIMO/hora × estimativa
2. Projeto:   (horas × taxa) × 1.3 (margem)
3. Valor:     baseado no resultado gerado para cliente
4. Pacote:    escopo fixo, preço fixo, prazo fixo
5. Recorrente: mensalidade (manutenção/suporte)
```

### Piso e Teto
```
Piso (nunca abaixo):   R$ X/hora (cobre custos + mínimo)
Alvo:                   R$ Y/hora (mercado justo)
Teto:                   R$ Z/hora (especialista premium)
```

## ANÁLISE DE CUSTOS

### Fixos Mensais
```
Internet:       R$ X
Energia:        R$ Y
Ferramentas:    R$ Z (APIs, serviços, SaaS)
Hardware:       R$ W (depreciação mensal)
Total fixo:     R$ S
```

### Variáveis (por projeto)
```
Taxa plataforma: X% (Fiverr 20%, 99Freelas 15%, etc.)
Imposto:         Y% (IR, ISS conforme regime)
Conversão:       spread/câmbio se USD
```

## OTIMIZAÇÃO

### Aumentar Receita
- Subir preço a cada 3 projetos bem avaliados
- Buscar clientes diretos (sem plataforma = +20%)
- Adicionar upsell (entrega + manutenção)
- Criar produto digital (vende enquanto dorme)

### Reduzir Custo
- Automatizar partes repetitivas
- Templates reutilizáveis
- Negociar ferramentas (plano anual vs mensal)

## MONITORAMENTO

### Alertas
```
Meta mensal < 50% no dia 20 → ALERTA: intensificar prospecção
ROI projeto < 0% → INVESTIGAR: escopo mal estimado?
3 meses seguidos abaixo da meta → REAVALIAR: mercado? skills? preço?
```

### Revisão Mensal
1. Receita total vs meta
2. ROI médio dos projetos
3. Maior cliente (não depender de um só)
4. Oportunidades perdidas (por que não fechou?)
5. Ajuste de preço/pipeline

## FOREX TRADING — FVG ICT M15 V5 + Macro (ATUAL)

> ⚡ **ESTRATÉGIA ATUAL (25/05/2026):** FVG ICT M15 V5 + CRT + S/R Levels + Weekly Bias + Macro Validation. Backtest: gap≥5 + horas[6,7,15,16] UTC = +11pp WR boost. USDJPY 73.3%, GBPUSD 65.5%, EURUSD 56.2% WR.
>
> Script: `~/.hermes/scripts/forex_bot_real.py` | Executor: `~/.hermes/scripts/mt5_direct.py`

### Estratégia V5 (25/05/2026)

**Fonte primária de dados: TRADINGVIEW** (NUNCA Yahoo Finance). User corrigiu 25/05: TradingView é o padrão designado. Yahoo Finance só como fallback de último recurso se TV inacessível.

**Filtros ativos:**
- **FVG gap ≥ 5 pips** — sobe WR +11pp (validado em 5059 padrões, 30 dias)
- **Horários UTC [6,7,15,16]** — London open + NY afternoon killzones
- **CRT** (Candle Range Theory): candle > percentil 80 + confirmação
- **S/R Levels**: FVG próximo de swing high/low anterior (≤5 pips)
- **Weekly Bias**: viés carregado de `weekly_bias.json` (atualizado via Knowledge Bridge)
- **Macro Validation (NOVO V5)**: score de 3 camadas (viés 40% + catalisadores 35% + timing 25%)

**3 pares ativos:** USD/JPY (73.3% WR), GBP/USD (65.5% WR), EUR/USD (56.2% WR)
AUD/USD e NZD/USD removidos — FVG inviável (45.7%, 44.3% WR). CHoCH standalone também inviável.

**Timeframe:** M15 | **RR:** 3:1 | **Max posições:** 4 | **Volume:** 0.01 microlote
**Sexta:** para abertura 14h BRT | **Dedup:** 1 trade por par+direção por dia
**Daily stop:** -5% | **Gestão risco:** 1% banca por trade

**Conceitos:**
- **CHoCH** (Change of Character): quebra de swing high/low confirmada
- **FVG ICT** (Fair Value Gap): gap entre 3 velas — candle[j].High < candle[j+2].Low
- **CRT** (Candle Range Theory): candle grande (>percentil 80) + 2ª vela fecha dentro do range
- **S/R Levels**: FVG a ≤5 pips de swing high/low anterior

**4 pares (24h Seg-Sex):** GBP/USD, AUD/USD, NZD/USD, EUR/USD
**Timeframe:** M15 (validado vs M5, M30, H1)
**RR:** 3:1 | **Max posições:** 8 | **Sexta:** para abertura 14h, fecha tudo 16h BRT

### Backtest de Referência (30 dias)

| Config | Trades | WR | P&L |
|--------|--------|-----|-----|
| RAW (sem filtros) | 1315 | 51.0% | +4087p |
| CRT | 247 | 66.8% | +1398p |
| **CRT + S/R** ⭐ | **113** | **72.6%** | **+733p** |
| CRT + H1 Trend | 39 | 64.1% | +198p |
| CRT + Volume | 0 | — | — |

### Otimização CRT_PERCENTILE (21/05)

| CRT | +SR | Trades/30d | WR | P&L |
|-----|-----|------------|-----|-----|
| 0.6 | ON | 12 | 58.3% | 32p |
| 0.7 | ON | 10 | 60.0% | 28p |
| 0.75 | ON | 9 | 66.7% | 30p |
| **0.8** | **ON** | **9** | **66.7%** | **30p** |
| 0.85 | ON | 8 | 75.0% | 32p |

> **Configuração ótima:** CRT_PERCENTILE=0.8, SR_ENABLED=True. Mercado atual (mai/2026) com baixa volatilidade — 0.3 trades/dia. Em períodos normais: 3.8 trades/dia.

### Execução (MT5 xdotool)

- **MT5:** OANDA Demo #1715539800 via Wine + Xvfb :99
- **Ordens:** F9 → digitar símbolo → Tab → volume → SL → TP → Alt+B/S
- **Health check:** `trade_closer.py health` a cada 30min
- **Sync P&L:** `trade_closer.py close` a cada 10min (verifica SL/TP vs preço atual)
- **Fechar sexta:** `forex_fechar_sexta.sh` às 16:00 BRT

### Cron Jobs Ativos (23/05/2026)

| Job | Schedule | Script | Tipo | Status |
|-----|----------|--------|------|--------|
| 🤖 Forex Bot REAL | */15 * * * 1-5 | forex_bot_real.py | no_agent | ⏸️ Pausado |
| 💰 Trade Closer | */10 * * * 1-5 | trade_closer_close.py | no_agent | ⏸️ Pausado |
| 🩺 MT5 Health | */30 * * * 1-5 | trade_closer_health.py | no_agent | ⏸️ Pausado |
| 📊 Daily Review | 0 18 * * 1-5 | forex_daily_review.py | no_agent | ⏸️ Pausado |
| 🔒 Fechar Sexta | 0 16 * * 5 | forex_fechar_sexta.sh | no_agent | ⏸️ Pausado |
| 📚 Daily Study | 30 7 * * * | forex_daily_study.py | no_agent | ✅ ativo |
| 📚 Research Collector | 0 3 * * * | forex_research_collector.py | no_agent | ✅ ativo |
| 📊 Chart Pattern Study | 0 8 * * 1-5 | chart_pattern_study.py | no_agent | ✅ ativo |
| 🧠 Weekly Analyzer | 0 11 * * 0 | (LLM prompt) | LLM ~500t | ✅ ativo |
| 🧠 N. Accumbens RL | 30 18 * * 1-5 | n_accumbens.py | no_agent | ✅ ativo |

> **Nota:** Forex Bot, Trade Closer, MT5 Health, Daily Review e Fechar Sexta pausados em 22/05 — aguardando migração para conta real.

### Estado Atual (Demo — 21/05)

- 5 trades fechados: 2W/3L, 40% WR, -10.2 pips
- 1 EUR/USD BUY aberto (entry 1.16279, floating -6.7p)
- Amostra pequena — aguardar 50+ trades para validar vs backtest 72.6%

### Migração para Real

- **Banca mínima:** $100 com microlote 0.01 (risco 2-5% por trade)
- **Monte Carlo:** risco de ruína ~0% com WR=72.6%, RR=3:1, banca ≥$100
- **Alternativa OANDA:** Exness (cadastro preenchido, MT5, depósito $10)
- **Pendente:** criar conta real, implementar volume dinâmico por % da banca

### Macro Validation V5 (NOVO — 25/05/2026)

Valida sinais de entrada contra contexto macro antes de executar. 3 camadas:

```
macro_score = camada1(viés, 40%) + camada2(catalisadores, 35%) + camada3(timing, 25%)

Se macro_score < 0.3 → REJEITAR sinal (contra contexto macro)
```

**Camada 1 — Viés Semanal (40%)**: Alinhamento com bias de `weekly_bias.json`
- Aligned: +0.40 | Neutral: +0.20 | Contra: +0.05

**Camada 2 — Catalisadores Macro (35%)**: Iran deal, Fed, UMich, dados econômicos
- Iran deal → risk-on → USDJPY BUY +0.35, GBP/EUR BUY +0.20
- Fed hawkish → USD strong → USDJPY BUY +0.10, GBP/EUR SELL +0.10
- UMich miss → USD bearish → USDJPY SELL +0.10, GBP/EUR BUY +0.10

**Camada 3 — Timing / Killzone (25%)**: 
- London open (6-7h UTC): +0.25 | NY afternoon (15-16h UTC): +0.20 | Fora: +0.05

**Exemplo 25/05**: USDJPY BUY → macro=0.80 ✅ | USDJPY SELL → macro=0.25 ❌ REJEITADO

### FVG Trend Monitor (NOVO V5)

Monitora tendência de gap médio dos FVGs por par. Se gap médio está subindo → volatilidade aumenta → setups mais confiáveis. Dados em `~/.hermes/forex/fvg_trend.json`, atualizados via brain.

### Regra de Segunda-Feira (Backtest 25/05/2026)

Backtest 60 dias M15 (USDJPY, GBPUSD, EURUSD) mostrou que **evitar segunda-feira NÃO é regra geral** — WR da segunda é similar ou melhor que Ter-Sex. A única exceção é quando segunda é **feriado bancário múltiplo** (Memorial Day US + Bank Holiday UK/EUR) — nesse caso liquidez é zero e spreads são proibitivos. Regra: verificar calendário de feriados, não dia da semana.

### Brain Gateway ↔ Bot Integration (25/05/2026)

Pipeline de integração bidirecional entre o bot de trading e o cérebro autônomo:

```
Brain Gateway (cron 2min) → brain_outbox.json (viés semanal, macro)
                                ↓
                    forex_bot_real.py → load_weekly_bias()
                    forex_bot_real.py → read_user_commands()
                                ↓
                    Executa trade → notify_trade()
                                ↓
                    brain_inbox.json → cérebro assimila
```

**Módulo:** `~/.hermes/scripts/brain_bot_bridge.py`
- `get_weekly_bias()` — lê brain_outbox.json, extrai viés por par
- `get_macro_context()` — contexto macro (Iran, Fed, UMich, etc.)
- `read_user_commands()` — comandos do usuário via gateway inbox
- `notify_trade()` — notifica cérebro sobre trade executado

**Integração no bot:**
- `load_weekly_bias()` → brain gateway (primário) + JSON local (fallback)
- `run_analysis()` → verifica comandos antes de analisar
- Trade executado → `notify_trade()` após `record_trade()`

**Comandos suportados:** pause/resume, close_all, status

### Knowledge Bridge — Ciclo de Aprendizado

```
Brain (cron jobs) → knowledge_bridge.py write → discoveries pool
                                                    ↓
Agente (sob demanda) → knowledge_bridge.py read → valida → absorb brain
                                                    ↓
                           Atualiza weekly_bias.json + fvg_trend.json
                                                    ↓
                           Aplica no forex_bot_real.py (macro validation)
```

**Comandos:**
```bash
# Ler descobertas do cérebro
python3 ~/.hermes/scripts/knowledge_bridge.py read

# Absorver conhecimento validado
python3 ~/.hermes/scripts/knowledge_bridge.py absorb brain  # brain → agent
python3 ~/.hermes/scripts/knowledge_bridge.py absorb agent  # agent → brain
```

- **Sistema automático:** `~/.hermes/executive/brain.py --learn`
- **Output:** `~/.hermes/forex/pair_weights_live.json` — WR real por par
- **Recomendações:** ACTIVE (≥60%), WATCH (50-59%), PAUSE (<50%)
- **Integração Ollama:** `llama3.2:3b` local para detecção de padrões em trade history
- **Ver:** [forex-self-learning.md](references/forex-self-learning.md)

### FOREX RESEARCH PIPELINE (23/05/2026)

Pipeline autônomo de pesquisa e estudo contínuo. 3 módulos:

#### 📚 Research Collector — `scripts/forex_research_collector.py`
Cron: `7b5698489701` — daily 03:00 BRT — **no_agent (zero tokens)**

Coleta automática de material de estudo:
- **RSS feeds:** BabyPips, ForexFactory, DailyFX, ForexLive
- **YouTube:** Transcripts de canais configurados (ICT Concepts, etc.)
- **Web:** BabyPips School of Pipsology, Investopedia Forex
- **Destino:** `~/.hermes/forex/research/YYYY-MM-DD/`
- **Config:** `~/.hermes/forex/research_sources.json` — editar para adicionar video_ids

#### 📊 Chart Pattern Study — `scripts/chart_pattern_study.py`
Cron: `00529564acee` — weekdays 08:00 BRT — **no_agent (zero tokens)**

Detecta padrões ICT em dados M5 do Yahoo Finance (5 pares: EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD):
- **CHoCH** (Change of Character): sweep + reversal confirmado
- **FVG** (Fair Value Gap): gap entre 3 velas
- **Order Blocks** (OB): última vela oposta antes do impulso
- **Structure Breaks** (BOS): HH/HL ou LH/LL
- **Liquidity Levels**: equal highs/lows (buy-side/sell-side liquidity)

Output:
- `~/.hermes/forex/patterns/pattern_library.json` — biblioteca cumulativa (50 exemplos/tipo)
- `~/.hermes/forex/patterns/YYYY-MM-DD/pattern_report.json` — report diário
- ASCII charts para inspeção visual de CHoCHs high-quality

#### 🧠 Weekly Analyzer — `89158ec43168`
Cron: Sunday 11:00 BRT — **LLM-driven (~500 tokens/semana)**

Lê research coletado + pattern library + trade performance real e produz:
- Padrões detectados e tendências
- WR real por par vs backtest
- Insights acionáveis e alertas
- Ajustes sugeridos na estratégia

**Custo total do pipeline:** 500 tokens/semana (apenas o analyzer). Coletor + Pattern Study = zero tokens.

### Referências

- **[forex-replay-test-20260525.md](references/forex-replay-test-20260525.md)** — Replay test 25/05: 3 pares, Killzone WR 76.5%, confirmação evening toxic, viés semanal
- **[forex-backtest-may2026.md](references/forex-backtest-may2026.md)** — Backtest 30 dias com 5 iterações
- **[forex-assertividade.md](references/forex-assertividade.md)** — Otimização CRT+S/R com varredura de percentis
- **[ict-pattern-types.md](references/ict-pattern-types.md)** — Catálogo de padrões ICT detectados (CHoCH, FVG, OB, BOS, Liquidity)
- `~/.hermes/forex/assertividade_backtest.json` — Dados brutos do backtest
- `~/.hermes/forex/assertividade_optimization.json` — Resultados da otimização CRT_PERCENTILE

## References

- **[weekly-bias-integration.md](references/weekly-bias-integration.md)** — Weekly bias format, macro validation flow, FVG trend monitor, knowledge bridge → bot pipeline.
- **[killzones-ict.md](../motor-central/references/killzones-ict.md)** — Killzones ICT, estratégia CRT, parâmetros validados, materiais Telegram.
- **[tradingview-api.md](references/tradingview-api.md)** — API gratuita TradingView Scanner: OHLCV + indicadores em tempo real sem login.
- **[forex-backtest-may2026.md](references/forex-backtest-may2026.md)** — Resultados do backtest de 19/05/2026 com 5 iterações, 12 trades, +6.72% em 10 dias.
- **[forex-3r-strategy-backtest.py](references/forex-3r-strategy-backtest.py)** — Script completo do backtest 3:1 RR (London Close CRT, 56 trades, +54.5 pips).
- **[forex-research-pipeline.md](references/forex-research-pipeline.md)** — Pipeline de pesquisa forex: coletor RSS/YouTube/Web + chart pattern study (ICT) + analisador semanal LLM.

**OANDA:** Melhor REST API (`oandapyV20` testado), mas **registro bloqueado por Cloudflare/React**. O formulário em hub.oanda.com é uma SPA React que não funciona no browser automatizado. Google OAuth também bloqueia ("Esse navegador ou app pode não ser seguro"). Solução: criar conta manualmente no Brave real, depois usar token API.

**Interactive Brokers:** `ib_insync` instalado. Spreads 0.1 pip. Regulação SEC/FINRA. Melhor para produção.

**IC Markets:** MT5 Python. Spreads raw 0.01 pip. Regulação FSA Seychelles (não Tier-1).

Client OANDA pronto: `~/.hermes/forex/oanda_client.py` — só falta token. Config em `~/.hermes/forex/oanda_config.json`.

## ANTI-PADRÕES

- NÃO aceitar projeto com ROI estimado < 0%
- NÃO depender de 1 cliente >50% da receita
- NÃO precificar sem calcular horas reais
- NÃO ignorar impostos no cálculo de lucro
- NÃO comparar receita bruta com salário CLT (custo empresa é diferente)
