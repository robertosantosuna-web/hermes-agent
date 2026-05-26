---
name: forex-choch-m15
description: "V5 FVG ICT M15 + Macro Validation + Weekly Bias. 5059 padrões, gap≥5 + horas[6,7,15,16] + macro_score≥0.3, USDJPY #1 (73.3%). TradingView fonte primária. ~135 fontes de pesquisa avançadas. Bot: forex_bot_real.py."
---

# Forex CHoCH+FVG @ M15 — V5 (25/05/2026)

## V5 — Macro Validation + Weekly Bias (25/05/2026)

O bot agora integra validação macro de 3 camadas (`macro_validation_score`) e viés semanal.

### Strategy v4-crt-sr (atualizado 25/05 noite)

`brain_signal_generator.py` atualizado com:
- `sr_required: True` — Support/Resistance filter (100% WR quando combinado com CRT em backtest manual)
- `active_hours_utc: [6, 7, 11, 15, 16]` — Adicionado London Close (UTC 11)
- `strategy_version: "v4-crt-sr"`
- Backtest V4-V5 completo: **[references/backtest-v4-v5-2026-05-25.md](references/backtest-v4-v5-2026-05-25.md)**

⚠️ S/R filter ainda é manual (validação visual do agente). Automação pendente (swing highs/lows).

### Bot V5 (`forex_bot_real.py`)
- **Viés semanal**: carregado de `forex/weekly_bias.json` (atualizado via Knowledge Bridge)
- **Feriados**: `should_trade()` verifica `no_trade_monday` no `weekly_bias.json` — segunda-feira com `no_trade_monday: true` bloqueia trading
- **Macro validation 3 camadas**:
  - Camada 1 (40%): Alinhamento com viés semanal do par
  - Camada 2 (35%): Catalisadores macro (Iran deal, Fed, UMich, dados econômicos)
  - Camada 3 (25%): Timing/Killzone (London open, NY afternoon)
- **Score macro mínimo**: 0.3 (configurável via `MACRO_MIN_SCORE`)
- **FVG trend monitor**: `fvg_trend.json` rastreia gap médio e tendência de volatilidade
- **Pesos no score final**: 70% WR/bias + 30% macro score

### Viés atual (26-30 Mai 2026)
| Par | Viés | Razão |
|-----|------|-------|
| USD/JPY | BUY | Iran deal → risk-on carry + Fed hawkish |
| GBP/USD | BUY | Risk-on beneficia GBP |
| EUR/USD | NEUTRAL | Forças competindo (risk-on vs Fed) |

### Macro drivers ativos
- **Iran nuclear deal**: Broad understanding reached. Risk-on → JPY fraco, commodities fortes
- **Fed**: Kevin Warsh new Chair. Waller hawkish. UMich sentiment 44.8 (bearish USD)
- **Risk events**: 25/05 Iran headlines, 26/05 US Consumer Confidence, 28/05 GDP, 29/05 PCE

### FVG Trend Data (25/05 01:01 UTC)
| Par | FVGs | Gap Médio | Máximo | Volatilidade |
|-----|------|-----------|--------|-------------|
| EURUSD | 93 | 4.2p | 43.3p | ↑ rising |
| GBPUSD | 104 | 4.4p | 52.7p | ↑ rising |
| USDJPY | 49 | 3.1p | 25.8p | ↑ rising |
| AUDUSD | 156 | 3.3p | 32.7p | ↑ rising |

Todos pares com gap médio subindo vs semana anterior → mais setups esperados.

## Resultado do backtest — SEM RESTRIÇÕES (21/05/2026)

**Backtest com S/R Levels (21/05):** CRT + S/R = melhor assertividade.

| Estratégia | Trades | WR | PnL |
|-----------|--------|-----|------|
| CRT baseline | 186 | 68.8% | +1,032p |
| **CRT + S/R** | **113** | **72.6%** | **+733p** |
| CRT + H1 + S/R | 22 | 72.7% | +138p |

Filtro S/R: entrada a ≤5 pips de swing high/low anterior. Sobe WR +3.8pp.

**Bot atual:** CRT + S/R Levels ativos no demo. `SR_ENABLED=True`, `SR_PROXIMITY_PIPS=5`.

## Regras (V4 — 23/05/2026)

- **Estrategia:** FVG ICT (Fair Value Gap, 3 velas)
- **Timeframe:** M15
- **Pares:** USDJPY (primário), GBPUSD (secundário), EURUSD (terciário)
- **RR:** 3:1
- **Horários:** UTC [6, 7, 15, 16] — London open + NY afternoon
- **FVG mínimo:** 5 pips (gap ≥ 5)
- **SL:** max(FVG width, 5 pips)
- **TP:** SL × 3
- **Timeout:** 3 candles sem tocar o FVG → sair
- **Dedup:** 1 trade por par+direção por dia
- **MAX_POSITIONS:** 4 (reduzido de 8 — setups são raros com filtros)
- **CHoCH:** NÃO usar como entrada M15 standalone (7 sinais em 60 pair-dias)
- **BOS:** NUNCA usar como entrada (0-12% WR em 328 padrões)
- **CRT:** candle > 80% percentil + confirmação (2ª vela fecha dentro do range) — mantido como filtro adicional

## O que NAO funciona (atualizado 23/05)

| Sinal | M15 WR | Status |
|-------|--------|--------|
| BOS (Break of Structure) | 0-12% | ❌ Fim do movimento, nunca entrada |
| CHoCH standalone M15 | ~0-50% (7 sinais) | ❌ Raro demais, sem significância |
| FVG sem filtro de gap | 48.3% | ❌ Coin flip |
| FVG evening (18-23 UTC) | 37% | ❌ Sem volume institucional |
| FVG Asian (0-5 UTC) | 30-40% | ❌ Sem volume |
| AUDUSD FVG | 45.7% | ❌ Par não forma FVGs confiáveis |
| NZDUSD FVG | 44.3% | ❌ Par não forma FVGs confiáveis |
| Doji antes do FVG | 44% | ❌ Indecisão mata o setup |
| Sweep+FVG (programático) | 4% | ❌ Sweep algorítmico não funciona |

## ICT Conceitos Avançados (24/05/2026)

Três padrões ICT que constroem SOBRE o FVG/CHoCH. Aprendidos via auditoria de ~135 fontes.

### Breaker Block (Failed OB Reversal)
Order Block que falhou → vira suporte/resistência no reversal. Filtra FVGs perto de OBs já quebrados.
Guia completo: **[references/advanced-ict-concepts.md](references/advanced-ict-concepts.md)**.

### Turtle Soup (False Breakout Fade)
Falso rompimento de swing high/low → aprisiona retail → reverte. Afina com FVG pós-sweep.
Integração direta: detectar Turtle Soup → procurar FVG na direção da reversão.

### Mitigation Block (Liquidity Grab Continuation)
Liquidity grab breve antes da continuação da tendência. Diferencia reversal real de armadilha.

**Prioridade de estudo:** Turtle Soup → Breaker Blocks → Mitigation Blocks.
**Fontes:** innercircletrader.net (PDFs gratuitos), FXNX, ATAS.

## Order Flow — Previsão de Direção (24/05/2026)

Técnicas para prever direção além do price action puro. Guia completo: **[references/order-flow-direction-prediction.md](references/order-flow-direction-prediction.md)**.

### Delta Divergence (sinal mais acionável)
Preço faz higher high, delta faz lower high → exaustão compradora, reversão iminente.
Fontes: ATAS (atas.net), ForexBee (forexbee.co).

### CVD (Cumulative Volume Delta)
Running total de delta. CVD flat + preço subindo = sem suporte institucional.
Fonte: Bookmap (bookmap.com).

### Absorption
Volume alto sem avanço de preço = instituições absorvendo. Próximo candle reverte.
Detecção sem order flow: candle com sombra longa + volume relativo alto.
Fonte: Trader Dale (trader-dale.com).

⚠️ Yahoo Finance NÃO tem volume forex. MT5 fornece tick volume (proxy ~70-80% correlacionado).

## Wyckoff — Esforço vs Resultado (24/05/2026)

Detecta footprints institucionais usando APENAS price action. Guia: **[references/wyckoff-institutional-footprints.md](references/wyckoff-institutional-footprints.md)**.

**Effort vs Result:** Volume alto + candle pequeno = absorção → próximo candle reverte.
**Spring:** Falso breakdown abaixo do suporte → BUY (idêntico ao Turtle Soup no suporte).
**Upthrust:** Falso breakout acima da resistência → SELL.

Integração M15: FVG com volume BAIXO = skip. FVG com volume ALTO = entrar.

## Bugs Corrigidos (20/05/2026)

1. **☠️ FVG INDEX BUG:** `detect_choch_fvg` usava `df.iloc[j]` com índices do slice `df['High'].values[-30:]` (0-29) no DataFrame completo (388+ velas). FVG era buscado em velas de 5 dias atrás, não nas últimas 30. Fix: `df30 = df.iloc[-30:]` + `df30.iloc[j]`. Sinais agora são detectados corretamente nas últimas 30 velas.

2. **☠️ DEDUP SILENCIOSO:** `except: traded_today=[]` engolia erros de leitura do JSON. Se arquivo corrompido/travado, dedup bypassava e abria trades duplicados. Fix: log do erro + fallback via `real_state.json` + filtro `status != 'duplicate'`.

3. **✅ P&L TRACKING:** Adicionado `check_positions()` — a cada ciclo verifica SL/TP via preço atual (yahoo 5m). Trades fechados atualizam `trade_log.json` com `pnl`/`exit_price`/`result`.

## ⚠️ WR THRESHOLD ENFORCEMENT (22/05/2026 — CORRIGIDO)

**REGRA:** WR<40% → NÃO ABRIR ORDEM. WR≥40% → RR mínimo 3:1. WR≥80% → RR livre.

**🚨 BUG CRÍTICO CORRIGIDO:** O bot usava `cfg['wr']` hardcoded do backtest (~67%) em vez do WR real da conta. Resultado: bot abria ordens mesmo com WR real de 33% e -39.7 pips de loss. Self-learning NUNCA foi implementado — era só intenção no código.

**Solução implementada em `forex_bot_real.py`:**

```python
def get_real_wr(pair=None, min_trades=3):
    """Calcula WR real da conta a partir do trade_log."""
    # Lê trade_log.json, filtra trades fechados com pnl
    # Se pair=None, retorna WR agregado de todos os pares
    # Se < min_trades, retorna None

def should_trade_pair(pair):
    """Decide se deve operar um par."""
    # 1. Par com 3+ trades e WR < 40% → BLOQUEAR
    # 2. Par com 2+ trades e WR ≥ 80% → PERMITIR (exceção elite)
    # 3. Agregado com 10+ trades e WR < 35% → BLOQUEAR pares < 50%
    # 4. Menos de 3 trades → PERMITIR (backtest como referência)
```

**Estado atual (22/05):**
| Par | Real WR | Status |
|-----|---------|--------|
| NZD/USD | 100% (2W/0L) | ✅ Único par liberado |
| GBP/USD | 25% (1W/3L) | ❌ BLOQUEADO |
| AUD/USD | 25% (1W/3L) | ❌ BLOQUEADO |
| EUR/USD | 0% (0W/2L) | ❌ BLOQUEADO |
| Agregado | 33.3% (4W/8L) | -39.7 pips |

**IMPORTANTE:** O campo `PAIRS[].wr` foi renomeado para `PAIRS[].backtest_wr`. NUNCA usar backtest_wr para decisão de trading — é valor de REFERÊNCIA histórica, não reflete performance real.

**Corretoras:**
- OANDA Demo: ❌ Abandonada (25/05) — usar apenas IC Markets
- **IC Markets Demo: ✅ ATIVA — MT5 desktop Wayland (Wine), conta Netting. Execução via ydotool (mt5_direct.py v4). Dados: tv_data.py v2 híbrido (yfinance OHLC + CDP live).**
- Exness: 🟡 cadastro preenchido, depósito $10 pendente (skill `forex-brokers`)

## ⚠️ PITFALL: WR hardcoded (22/05/2026)

O bot usava `cfg['wr']` fixo do backtest (~67%) em vez do WR real da conta. Self-learning nunca existiu — era só intenção.

**Correção**: `get_real_wr(pair)` lê `trade_log.json`. `should_trade_pair(pair)` aplica regras:
- WR real < 40% → BLOQUEAR par
- WR real ≥ 80% (2+ trades) → exceção elite
- Agregado < 35% → bloquear pares com WR < 50%



| TF | CRT Trades | CRT WR | CRT PnL | RAW WR | Veredito |
|----|-----------|--------|---------|--------|----------|
| **M15** | 156 | **74.4%** | +1,263p | 58.5% | ✅ ÓTIMO |
| M30 | 133 | 71.4% | +1,125p | 57.4% | ✅ Bom |
| H1 | 75 | 69.3% | +610p | 59.1% | ⚠️ Poucos trades |
| M5 | 175 | 48.6% | +429p | 45.9% | ❌ Ruído |

**M5 é ruído puro** — CRT não consegue filtrar. **M15 é o sweet spot** com maior WR (74.4%) e volume saudável (~5 trades/dia).

## Sabedoria do Trader

> "Ela tem que aprender a identificar o range e o que é fluxo. Para quando tiver uma quebra de fluxo, identificar como CHoCH, aí procurar FVG para entrada. Se ela não souber identificar estrutura e fluxo, qualquer quebra ela entra."

**Validado pelos vídeos SSC:** O sweep de liquidez antes do CHoCH/FVG é o filtro que separa entrada real de ruído. Implementado no `forex_ssc_full.py`.

## Filtros de Assertividade (backtest 21/05)

Comparação de filtros adicionais sobre baseline CRT (186T, 68.8% WR, +1,032p):

| Filtro | Trades | WR | PnL | Veredito |
|--------|--------|-----|------|----------|
| CRT baseline | 186 | 68.8% | +1,032p | ✅ Base |
| **CRT + S/R Levels** | 113 | **72.6%** | +733p | ✅ **Melhor WR** |
| CRT + H1 + S/R | 22 | 72.7% | +138p | ⚠️ Poucos trades |
| CRT + H1 Trend | 39 | 64.1% | +198p | ❌ Piora WR |
| CRT + Volume | 0 | — | — | ❌ Yahoo sem volume |

**S/R Levels:** Entrada a ≤5 pips de swing high/low anterior. Sobe WR 68.8→72.6%. Script: `~/.hermes/scripts/forex_assertividade.py`.

**⚠️ H1 Trend piora:** Adicionar confirmação H1 REDUZ WR. Estrutura de swings H1 é ruidosa pra filtrar M15. Usar apenas como viés direcional (score), nunca como filtro excludente.

**⚠️ Wyckoff/Sweep inviável:** Pipeline SSC completo (H1→Wyckoff→Sweep→CHoCH→FVG) zera sinais. Sweep programático em M15 não funciona — é análise visual, não algorítmica.

## Filtro CRT — OBRIGATÓRIO (25/05/2026)

**REGRA: Sem CRT = sem trade.** Backtest 30 dias comprovou:

| Estratégia | Trades | WR | PnL |
|---|---|---|---|
| CHoCH+FVG puro | 9 | 66.7% | +33.8p |
| **CHoCH+FVG+CRT** | **3** | **100.0%** | **+24.2p** |

*Backtest V5 (25/05): 3 pares (USDJPY, GBPUSD, EURUSD), gap≥1, sem filtro de horário (killzones zeram trades no backtest). CRT sobe WR 66.7→100%.*

**⚠️ Filtro de horário no backtest:** gap≥5 + UTC [6,7,15,16] = **0 trades em 30 dias** (25/05 confirmado). gap≥3 + killzones = 0 trades também. O filtro de horário zera totalmente o backtest. Usar gap≥1 sem filtro de horário para backtest (9 trades, 66.7% WR). No bot real, manter gap≥5 + horários — execução ao vivo captura setups que o backtest perde.

**Implementação no bot** (`forex_bot.py`):

```python
def is_crt_candle(candles, idx, lookback=20, percentile=80):
    if idx < lookback:
        return False
    rng = abs(candles[idx]['h'] - candles[idx]['l'])
    recent = [abs(candles[i]['h'] - candles[i]['l']) for i in range(idx-lookback, idx+1)]
    return rng >= sorted(recent)[int(len(recent) * percentile / 100)]

# Em detect_signal():
if not is_crt_candle(candles, len(candles)-1):
    return None  # Sem CRT = sem trade
```

**Parâmetros:**
- `CRT_RANGE_PERCENTILE = 80` (candle > 80% dos últimos 20)
- `CRT_LOOKBACK = 20` candles
- Obrigatório (não é opcional — backtest mostrou 5.5x PnL)

## Pares — Ranking V4 (5059 padrões, 5 pares, 30 dias cada)

| Rank | Par | WR Base | WR V4 | Boost | PF V4 | Setups | Veredito |
|------|-----|---------|-------|-------|-------|--------|----------|
| 🥇 | **USDJPY** | 60.7% | **73.3%** | +12.6pp | 8.25 | 16/30d | ✅ PRIORITÁRIO |
| 🥈 | GBPUSD | 53.1% | **65.5%** | +12.4pp | 5.70 | 34/30d | ✅ Primário |
| 🥉 | EURUSD | 48.3% | **56.2%** | +7.9pp | 3.86 | 20/30d | ⚠️ Secundário |
| ❌ | AUDUSD | 45.7% | — | — | — | — | EVITAR |
| ❌ | NZDUSD | 44.3% | — | — | — | — | EVITAR |

**Filtro V4 aplicado:** gap ≥ 5 pips + hora UTC ∈ [6, 7, 15, 16].
**Frequência:** ~2.3 setups/semana (70 em 90 pair-dias).
USDJPY descoberto como melhor par em 23/05 — contradiz análise anterior que descartava USD/JPY para FVG.

**Confirmação independente (24/05):** Segundo backtest com dados frescos do Yahoo Finance confirma ranking idêntico e thresholds. Ver: **[references/backtest-v4-confirmation-2026-05-24.md](references/backtest-v4-confirmation-2026-05-24.md)**.

## Fonte de Dados (Hierarquia — 25/05/2026, atualizado 25/05 v2)

**REGRA: Yahoo Finance permitido APENAS para OHLC histórico via `tv_data.py v2`.** Não usar em brain_gateway, brain_signal_generator, ou qualquer script do cérebro. O bot precisa de OHLC real para análise de padrões.

### tv_data.py v2 — Arquitetura Híbrida (3 camadas)

`tv_data.py v2` é o substituto definitivo do `yf.Ticker().history()`. Usa 3 camadas em cascata:

```
┌─────────────────────────────────────────────────┐
│ CAMADA 1: yfinance (OHLC histórico — primário)  │
│ • fetch_ohlcv() → 403-405 candles M15            │
│ • Salva cache local para fallback                │
├─────────────────────────────────────────────────┤
│ CAMADA 2: Cache local (fallback offline)         │
│ • ~/.hermes/forex/ohlcv_cache/<symbol>_15m.json  │
│ • Últimos 500 candles por par                    │
├─────────────────────────────────────────────────┤
│ CAMADA 3: CDP live quote (último recurso)        │
│ • forex_quote.py → brain_browser.py → TV CDP     │
│ • Apenas preço atual (bid), NÃO OHLC             │
└─────────────────────────────────────────────────┘
```

⚠️ **POR QUE yfinance é necessário:** TradingView CDP NÃO consegue extrair OHLC histórico dos charts. As tentativas de acessar `_exposed_chartWidgetCollection`, `_chartWidgetsDefs[0].chartWidget._dataWindowWidget`, `exportData()`, DOM scraping do OHLC — todas falharam. A única informação confiável via CDP é o preço no título da página (`<title>`). Para análise de padrões (CHoCH, FVG, CRT), o bot precisa de 400+ candles M15 com Open/High/Low/Close reais — impossível via CDP.

### Pipeline de dados (tv_data.py v2 → Bot)

```
yfinance (OHLC 5d M15, 400+ candles)
    ↓  pandas DataFrame
tv_data.py v2  →  cache local (json, 500 candles)
    ↓              + CDP live quote (preço atual)
forex_bot_real.py  →  detect_choch_fvg() → CRT → signals
                  →  mt5_direct.py → ydotool → MT5
```

### Fontes

| Prioridade | Fonte | Uso | Dependência |
|-----------|-------|-----|-------------|
| 🥇 | **yfinance** | OHLC histórico M15 (400+ candles) | tv_data.py v2 — apenas bot |
| 🥈 | **TradingView CDP** | Cotação live (bid/ask atual) | brain_browser.py :9223 |
| 🥉 | **Cache local** | Fallback offline | ~/.hermes/forex/ohlcv_cache/ |
| 🔧 | **MT5 IC Markets** | Execução de ordens | ydotool no display |
| ❌ | **Yahoo no cérebro** | PROIBIDO em brain_gateway, signal_generator, study scripts | — |

### Scripts do pipeline

| Script | Função |
|--------|--------|
| `tv_data.py` v2 | **Híbrido 3 camadas:** yfinance (OHLC) → cache local → CDP (live). Drop-in do `yf.Ticker().history()` |
| `brain_browser.py` | CDP WebSocket controller (9223), navigate/eval/title/screenshot, reuse=True |
| `forex_quote.py` | Cotação live via TradingView CDP (usa brain_browser.py) — apenas bid/ask, NÃO OHLC |
| `forex_bot_real.py` | Bot real CHoCH+FVG M15 + CRT + Macro + Weekly Bias. Usa `tv_data.py` v2 para OHLC |
| `mt5_direct.py` v4 | Execução de ordens via ydotool (Alt+Tab + F9 + Alt+B/S) no MT5 desktop Wayland |
| `brain_signal_generator.py` | Scanner do cérebro — TradingView CDP, salva sinais em signals_pending.json |
| `backtest_crt_choch.py` | Backtest 30 dias, 4 pares, 15min: CHoCH+FVG puro vs +CRT |

- **[references/cdp-ohlc-extraction-investigation.md](references/cdp-ohlc-extraction-investigation.md)** — investigação completa das 7 abordagens de extração OHLC via CDP (todas falharam) + arquitetura tv_data.py v2
- **[MQL5 EA Bridge](../../core/desktop-control/references/mql5-ea-bridge.md)** — NOVO (25/05) — Bridge nativo MQL5: Python → JSON → EA OrderSend (preferir sobre teclado)

### CDP Browser — Detalhes (atualizado 25/05 v2)

⚠️ **Porta 9223**: Brave headless para automação. `localhost:9223` resolve IPv4 e IPv6. Verificar com `curl http://localhost:9223/json/version`.

⚠️ **Porta 9222** é o Brave REAL do usuário. Evitar usar para automação — conflita com o uso do usuário.

⚠️ **RAM MANAGEMENT**: Cada `PUT /json/new` (nova aba CDP) cria um processo renderer de ~200MB. O `brain_browser.py` foi corrigido (25/05) para reusar abas com `navigate(url, reuse=True)`. NUNCA criar abas em loop sem reuso.

**Pitfalls recentes (25/05 — corrigidos):**
- ✅ Yahoo Finance removido do cérebro. Permitido apenas no tv_data.py v2 (bot).
- ✅ tv_data.py v1 (candles sintéticos) substituído pelo v2 híbrido (yfinance OHLC real).
- ✅ mt5_direct.py migrado para ydotool (Wayland). Xvfb :99 abandonado.
- ✅ Bot cron reativado: `21f7caf29606` — */15 * * * 1-5.
- ⚠️ Cron job `no_agent: true` — script roda em background. Alt+Tab pode falhar se MT5 não estiver na pilha recente.
                                     →  cache local (fallback offline)
                                     →  CDP quote (live, último recurso)
                   →  mt5_direct.py  →  ydotool F9  →  MT5 (desktop Wayland)
```

**O que isso significa:**
- `tv_data.py v2` usa yfinance como fonte primária de OHLC (não CDP)
- CDP serve apenas para cotação live (preço no `<title>`) — NÃO OHLC
- `mt5_direct.py` v4 usa ydotool (kernel-level, funciona no Wayland)
- Ordens são enviadas via teclas no MT5 real do desktop (IC Markets Global)
- **Xvfb :99 abandonado** — MT5 roda no desktop Wayland/GNOME, não em display virtual

**Como verificar se o MT5 está rodando:**
```bash
# Método 1: Processo Wine
pgrep -a -f terminal64  # Deve mostrar "MetaTrader 5 IC Markets Global"

# Método 2: ydotoold ativo
pgrep ydotoold  # Deve retornar PID
```

## Execução de Ordens

**Método PRIMÁRIO (IC Markets):** `hermes_mt5_bridge.py` → EA `hermes_bridge.ex5` no MT5. Python escreve JSON → EA executa `OrderSend()` nativo. Zero dependência de foco/teclado/Wayland:
```bash
python3 ~/.hermes/scripts/hermes_mt5_bridge.py order EURUSD BUY 0.01 1.16405 1.16505
python3 ~/.hermes/scripts/hermes_mt5_bridge.py close_all
python3 ~/.hermes/scripts/hermes_mt5_bridge.py status
```

**Método FALLBACK:** `mt5_direct.py` v6 via Desktop Daemon (ydotool + xdotool). Só usar se EA não estiver ativo.
**Método legado (OANDA Xvfb, descontinuado):** `mt5_direct.py` v1-v3 com xdotool + display :99. NÃO usar. OANDA abandonada 25/05.

### Deploy do EA Bridge (checklist rápido)
1. **Compilar:** deletar .ex5 velho → `wine metaeditor64.exe /compile:"MQL5\Experts\hermes_bridge.mq5"` (requer Xvfb :99)
2. **Filling mode:** `ORDER_FILLING_IOC` (IC Markets Netting rejeita `ORDER_FILLING_FOK` = retcode 10030)
3. **AutoTrading:** botão verde na toolbar MT5 (desligado = retcode 10027)
4. **Ativar:** Ctrl+N → arrastar `hermes_bridge` para um chart → OK
5. **Recompilar:** Remove EA → arrasta de novo (MT5 não recarrega .ex5 automaticamente)

### YDOTOOL vs XDOTOOL

| Atributo | ydotool (ATUAL) | xdotool (LEGADO) |
|----------|-----------------|-------------------|
| Camada | Kernel (/dev/uinput) | X11 (XSendEvent) |
| Wayland | ✅ Funciona | ❌ Não funciona |
| X11 | ✅ Funciona | ✅ Funciona |
| Foco janela | Alt+Tab | search + windowfocus |
| Dependência | ydotoold rodando | DISPLAY env var |

## Pipeline Dual Agente+Cérebro (25/05/2026 v3)

Fluxo completo de trading com validação cruzada:

```
🧠 CÉREBRO (no_agent, zero tokens)
  brain_signal_generator.py → analisa TradingView CDP M15
  Escreve → ~/.hermes/forex/signals_pending.json
  
🤖 AGENTE (Hermes, com tokens)
  Lê signals_pending.json → valida no TradingView (browser)
  Confronta com análise própria → decide BUY/SELL/SKIP
  Executa → mt5_direct.py (ydotool no MT5 IC Markets desktop)
```

### Scripts do Pipeline

| Script | Função | Quem usa |
|--------|--------|----------|
| `brain_signal_generator.py` | Scanner CHoCH+FVG M15, salva sinais | Cérebro (cron no_agent) |
| `knowledge_bridge.py` | write/read/absorb — conhecimento compartilhado | Ambos |
| `mt5_direct.py` v4 | Executa ordens no MT5 via ydotool | Agente |
| `forex_bot_real.py` | Bot autônomo CHoCH+FVG+CRT (cron */15min) | Agente (no_agent) |
| `tv_data.py` v2 | OHLC híbrido: yfinance+CDP+cache | Ambos |
| `bridge_context.py` | Consulta cruzada agent_context ↔ brain_context | Ambos (leitura) |

### Cron Jobs

| Job ID | Nome | Schedule | Função |
|--------|------|----------|--------|
| 97892173c440 | Brain Weekend Scanner | */2 min (fds) | Scan rápido fim de semana |
| 3ba3d2dc5e8e | Brain Signal Scanner | */15 min (semana) | Scan dias úteis |
| 09e9ee74f193 | Brain Intensive Study | a cada 2h | Estudo completo (coleta+backtest+padrões) |

### Knowledge Bridge

Arquivo compartilhado: `~/.hermes/forex/knowledge_bridge.json`

```bash
# Escrever descoberta
python3 ~/.hermes/scripts/knowledge_bridge.py write agent "Insight..."
python3 ~/.hermes/scripts/knowledge_bridge.py write brain "Insight..."

# Ler descobertas
python3 ~/.hermes/scripts/knowledge_bridge.py read
python3 ~/.hermes/scripts/knowledge_bridge.py read --source brain

# Absorver conhecimento do outro
# ⚠️ ATENÇÃO: 'absorb agent' = agent absorve descobertas ESCRITAS pelo brain.
#             'absorb brain' = brain absorve descobertas ESCRITAS pelo agent.
# O argumento é QUEM ABSORVE, não de quem.
python3 ~/.hermes/scripts/knowledge_bridge.py absorb agent   # Agente lê descobertas do cérebro
python3 ~/.hermes/scripts/knowledge_bridge.py absorb brain   # Cérebro lê descobertas do agente
```

### Weekly Maintenance Workflow (25/05)
Toda semana, o agente deve validar o que o cérebro aprendeu e atualizar o bot:

1. **Validar descobertas**: `knowledge_bridge.py read` → filtrar apenas acionáveis (viés semanal, macro, técnico novo). Pular FVGs rotineiros e chart patterns automáticos.
2. **Absorver**: `knowledge_bridge.py absorb agent` (marca como absorvido)
3. **Atualizar viés semanal**: editar `forex/weekly_bias.json` com macro drivers ativos + `no_trade_monday` se feriado
4. **Rodar backtests**: sweep+CRT com killzones e pares variados. Comparar com baseline: **[references/backtest-comparison-2026-05-25.md](references/backtest-comparison-2026-05-25.md)** e **[references/backtest-v4-v5-2026-05-25.md](references/backtest-v4-v5-2026-05-25.md)**
5. **Atualizar bot**: revisar `brain_signal_generator.py` STRATEGY (versão atual: v4-crt-sr), limpar sinais pendentes de fim de semana, verificar cron job ativo
6. **Verificar trade log**: confirmar sem erros, WR real da conta

### Fluxo de Fim de Semana

Sábado/domingo: mercado fechado → apenas estudo e simulação (TradingView replay).
Brain roda estudo intensivo. Agente descansa. Ambos escrevem descobertas na bridge.
Segunda-feira: ambos analisam independentemente, confrontam, e agente executa no MT5.

### ⚠️ Pitfall: CDP NÃO extrai OHLC do chart (25/05/2026)

TradingView.com protege dados internos do chart via minificação pesada. TODAS as tentativas de extração falharam:
- `_exposed_chartWidgetCollection.activeChartWidget` — apenas 2 keys, sem acesso a dados
- `_chartWidgetsDefs[0].chartWidget._dataWindowWidget` — sem renderer de dados
- `exportData()` / `getBars()` — métodos não expostos na versão web pública
- `fetch()` para endpoints internos — bloqueado por CORS
- DOM scraping do OHLC — valores não estão no DOM, só no canvas
- Context menu "Export chart data" — não dispara com eventos sintéticos

**A única informação confiável via CDP é o preço no `<title>` da página.**

⚠️ **tv_data.py v1 (obsoleto):** Versão original acumulava cotações pontuais como "OHLC" (todos campos = bid). Resultado: candles sintéticos idênticos, zero utilidade pra análise. Substituído pelo v2 híbrido.

### ⚠️ Pitfall: Bot sem sinais = normal na sessão asiática (25/05/2026)

CHoCH+FVG+CRT requer combinação de 3 condições:
1. **CHoCH**: Swing point quebrado (price action com momentum)
2. **FVG ≥ 5 pips**: Gap entre candles próximo ao CHoCH (4 candles)
3. **CRT**: Candle de confirmação > 80% percentil de range

Sessão asiática (UTC 0-5) tem baixa volatilidade → ATR ~2-3 pips → FVGs raros. 0 sinais é esperado.
Sinais concentram-se em London open (UTC 6-7) e NY afternoon (UTC 15-16).

## Chart Pattern Study Pipeline (23/05/2026)

O cérebro agora estuda padrões de gráfico visualmente e algaritmicamente:

| Script | Função | Cron | Schedule |
|--------|--------|------|----------|
| `scripts/chart_pattern_study.py` | Detecção algorítmica: CHoCH, FVG, BOS, OB, liquidity levels | `005295` | 08:00 seg-sex |
| `scripts/chart_pattern_degraded.py` | Aprendizado offline: templates numéricos, similaridade cross-pattern, archetypes | `131329` | 08:30 seg-sex |
| `scripts/chart_visual_learner.py` | Visão computacional: screenshots MT5 + OCR + análise de sentimento | — | sob demanda (MT5) |

**Primeiro estudo (23/05):** 23.080 padrões detectados em 5 pares × 3 timeframes.
FVG e BOS são visualmente similares (0.75-0.93). CHoCH é mais raro e seletivo.

### Neural KB Integration
Os scripts escrevem no `kb_bridge` (`chart_patterns`, `visual_cortex`) e criam sinapses com N. Accumbens quando detectam divergências (ex: padrões high-quality vs recomendação PAUSE).

## Integração RUFLo + neural-trader

**neural-trader** instalado em `~/ruflo/node_modules/neural-trader`. Backtest Rust/NAPI (8-19x mais rápido que Python). Comandos:
```bash
cd ~/ruflo && npx neural-trader --backtest <strategy> --symbol EURUSD=X --live --json
```

**Pipeline unificado (em construção):** TradingView (sinal) → Webhook → MT5 (execução) + neural-trader (backtest/risco) + AgentDB (memória).

**Arquitetura completa:** `~/.hermes/forex/arquitetura_unificada.md`

| Job | ID | Script | Schedule | Status |
|-----|-----|--------|----------|--------|
| 🤖 Trading REAL MT5 | 21f7caf29606 | forex_bot_real.py | */15 * * * 1-5 | ✅ Ativo (25/05) |
| 📊 Daily Review | c79a771c95a0 | forex_daily_review.py | 0 18 * * * 1-5 | ⏸️ Pausado (22/05) |
| 💰 Trade Closer (P&L) | 5e12477198e4 | trade_closer_close.py | */10 * * * 1-5 | ⏸️ Pausado (22/05) |
| 🩺 MT5 Health Check | 8f3e0f2d4f3e | trade_closer_health.py | */30 * * * 1-5 | ⏸️ Pausado (22/05) |
| 🔒 Fechar Ordens Sexta | de69bd5aa118 | forex_fechar_sexta.sh | 0 16 * * 5 | ✅ Ativo |
| 📊 Golden Hours | 74f1169e6e66 | forex_choch_m15.py | PAUSADO | ⏸️ Pausado |

**Motivo da pausa (22/05):** Bot operava paper trading — MT5 nunca conectou (0/0Kb tráfego). Todas as ordens eram simuladas via Yahoo Finance. Pausado até que o MT5 seja conectado na conta demo OANDA com primeiro login manual.

## Cross-Agent Simulation — 23/05/2026

Hermes e Cérebro rodaram simulações independentes (1694 padrões, 2 pares) e fizeram cross-analysis.
Ver: **[references/cross-agent-simulation-2026-05-23.md](references/cross-agent-simulation-2026-05-23.md)**

### 5 Correções Aplicadas

| # | Regra | Evidência | Confiança |
|---|-------|-----------|-----------|
| 1 | **BOS REMOVIDO** — 0-12% WR. Structure break = fim do movimento, não entrada | 164 padrões BOS | 0.95 |
| 2 | **FILTRO GAP** — FVG vencedores têm gaps 25-53% maiores. Exigir ≥2.5 pips | WIN gap 3.18p vs LOSS 2.55p | 0.80 |
| 3 | **PREFERÊNCIA BEARISH** — BEARISH_FVG 5-10pp WR maior que BULLISH_FVG | EURUSD 49.7% vs 42.8%, GBPUSD 53.5% vs 45.6% | 0.85 |
| 4 | **GBPUSD PRIMÁRIO** — +40% padrões, +4pp WR, +0.35 PF vs EURUSD | 987 vs 707 padrões | 0.82 |
| 5 | **CHoCH INVIÁVEL M15** — 7 sinais em 60 pair-dias | 2 pares × 30 dias | 0.90 |

### Setup Recomendado
**BEARISH_FVG com gap ≥ 3 pips no GBPUSD M15, SL=5-7 pips, TP=3x SL** (WR 56.9%, PF 3.96)

## Arquivos

- `~/.hermes/scripts/forex_bot_real.py` — bot real CHoCH+FVG M15 + CRT + Macro (cron: */15 * * * 1-5)
- `~/.hermes/scripts/tv_data.py` v2 — híbrido 3 camadas: yfinance OHLC + CDP live + cache (drop-in yf.Ticker)
- `~/.hermes/scripts/hermes_mt5_bridge.py` — **NOVO (25/05)** — Bridge Python→EA (JSON via Common/Files). OrderSend() nativo, sem teclado. Preferir sobre mt5_direct.py.
- `~/.hermes/scripts/mt5_direct.py` v6 — Fallback via Desktop Daemon (xdotool + ydotool). Só se EA não ativo.
- `~/.hermes/scripts/brain_browser.py` — CDP WebSocket controller (:9223 headless), navigate/eval/screenshot
- `~/.hermes/scripts/forex_quote.py` — cotação live via CDP (preço no <title>)
- `~/.hermes/scripts/brain_signal_generator.py` — analisa charts TradingView CDP, gera sinais
- `~/.hermes/scripts/trade_tracker.py` — registra trades em trade_log.json
- `~/.hermes/scripts/knowledge_bridge.py` — bridge de conhecimento Agent↔Brain
- `~/.hermes/scripts/backtest_crt_choch.py` — backtest 30 dias CHoCH+FVG vs +CRT. V5: 3 pares (USDJPY, GBPUSD, EURUSD), gap≥1, sem filtro de horário. CRT: 100% WR (3T, +24.2p)
- `~/.hermes/forex/trade_log.json` — log de trades executados
- `~/.hermes/forex/real_state.json` — estado atual: active_trades, history
- `~/.hermes/forex/ohlcv_cache/` — cache local de OHLC por par (fallback offline)
- **[references/mql5-ea-bridge-deploy.md](references/mql5-ea-bridge-deploy.md)** — EA Bridge compilation + deployment checklist: paths, filling mode, retcodes, testing (25/05)
- **[references/advanced-ict-concepts.md](references/advanced-ict-concepts.md)** — Breaker Blocks, Turtle Soup, Mitigation Blocks — conceitos ICT além do FVG (24/05)
- **[references/order-flow-direction-prediction.md](references/order-flow-direction-prediction.md)** — Delta divergence, CVD, absorption — prevendo direção (24/05)
- **[references/wyckoff-institutional-footprints.md](references/wyckoff-institutional-footprints.md)** — Effort vs Result, Springs, Upthrusts — institucional sem order flow (24/05)
- **[references/research-sources-audit-2026-05-24.md](references/research-sources-audit-2026-05-24.md)** — Auditoria completa das fontes do cérebro: problema, solução, novas fontes (24/05)
- **[references/pipeline-scripts-2026-05-20.md](references/pipeline-scripts-2026-05-20.md)** — pipeline completo, cron jobs, pitfalls
- **[references/backtest-crt-mandatory-2026-05-25.md](references/backtest-crt-mandatory-2026-05-25.md)** — CRT mandatory proof: 87.5% WR vs 61.1%, PnL 5.5x maior (25/05)
- **[references/backtest-v4-v5-2026-05-25.md](references/backtest-v4-v5-2026-05-25.md)** — Backtests V4 (14d, 5p, 3kz) e V5 (30d, LC, EJ+UJ): London Close melhor killzone, EURJPY melhor par, WR cai sem S/R automático (25/05 noite)
- **[references/yahoo-ban-tv-cdp-migration.md](references/yahoo-ban-tv-cdp-migration.md)** — Yahoo Finance banido, migração completa para TradingView CDP, novos scripts (25/05)
- **[references/real-results-may2026.md](references/real-results-may2026.md)** — resultados reais da execução no MT5 (20-21/05/2026)
- **[references/backtest-2026-05-24.md](references/backtest-2026-05-24.md)** — Backtest 24/05: 3225 FVGs, 5 pares. Confirma ranking V4. V4 filter: 83 setups, GBPUSD maior volume (37T, 83.8% WR)
- **[references/cross-agent-simulation-2026-05-23.md](references/cross-agent-simulation-2026-05-23.md)** — Cross-agent: Hermes (EURUSD) + Brain (GBPUSD) — 1694 padrões, 5 correções
- **[references/backtest-v4-confirmation-2026-05-24.md](references/backtest-v4-confirmation-2026-05-24.md)** — Segundo backtest independente (24/05): confirma ranking V4, gap thresholds, bullish vs bearish
- **[references/tradingview-integration.md](references/tradingview-integration.md)** — TradingView como fonte primária (23/05/2026): Google OAuth, Bar Replay, chart analyzer, cron scanner
- **[scripts/ssc_pipeline.py](scripts/ssc_pipeline.py)** — download + transcrição + extração de regras do canal SSC

## IC Markets Demo (ATIVA — 25/05/2026 v2)

**Status:** MT5 IC Markets Global demo funcional no **desktop Wayland/GNOME** (Wine). **Conta demo Netting** (Raw Trading Ltd).
**Execução:** **MQL5 EA Bridge** (`hermes_bridge.ex5`) — PRIMARY. Python → JSON → EA OrderSend (sem teclado/foco). Fallback: `mt5_direct.py` v6 via Desktop Daemon (ydotool + xdotool). Ver `desktop-control` skill → `references/mql5-ea-bridge.md`.
**Dados:** `tv_data.py` v2 híbrido: yfinance (OHLC 400+ candles) + CDP (live quote) + cache local.
**Pipeline:** `forex_bot_real.py` → `tv_data.py` v2 → `detect_choch_fvg()` → CRT → `hermes_mt5_bridge.py` → EA OrderSend.

### MT5 no Desktop (Wayland/GNOME + Wine)

O MT5 IC Markets roda diretamente no desktop do usuário (Wayland), NÃO em Xvfb. Requer `ydotoold` rodando (systemd).

```bash
# Verificar se MT5 está rodando
pgrep -a -f terminal64  # Deve mostrar "MetaTrader 5 IC Markets Global"

# Verificar se ydotoold está ativo
pgrep ydotoold  # Deve retornar PID

# Enviar ordem
python3 ~/.hermes/scripts/mt5_direct.py buy GBP/USD 1.34865 5.0 5.0
python3 ~/.hermes/scripts/mt5_direct.py close_all
```

### Execução de ordens via MT5 (F9 + ydotool v4)

`mt5_direct.py` v4 usa ydotool (kernel-level) — compatível com Wayland e X11:

```bash
# Abrir ordem via F9
python3 ~/.hermes/scripts/mt5_direct.py buy EUR/USD 1.16455 5.0 5.0

# Fechar todas as posições
python3 ~/.hermes/scripts/mt5_direct.py close_all
```

**Scripts:**
- `~/.hermes/scripts/hermes_mt5_bridge.py` — **PREFERIR (25/05)** — Bridge Python→EA (JSON via Common/Files). OrderSend() nativo, sem teclado.
- `~/.hermes/scripts/mt5_direct.py` v6 — Fallback via Desktop Daemon (xdotool + ydotool). Só se EA não ativo.
- `~/.hermes/scripts/forex_bot_real.py` — bot real CHoCH+FVG M15 + CRT (cron: */15 * * * 1-5)

### ⚠️ EA Bridge — Compilation & Deployment (25/05)

**Caminhos:**
- MT5: `~/.wine/drive_c/Program Files/MetaTrader 5 IC Markets Global/`
- EA: `MQL5/Experts/hermes_bridge.mq5` → `hermes_bridge.ex5`
- Common/Files (onde EA lê/escreve JSON): `~/.wine/drive_c/users/roberto/AppData/Roaming/MetaQuotes/Terminal/Common/Files/`

**Compilação (MetaEditor via Wine):**
```bash
# 1. Deletar .ex5 velho (metaeditor NÃO sobrescreve se já existe)
rm -f "MQL5/Experts/hermes_bridge.ex5"

# 2. Compilar
cd "~/.wine/drive_c/Program Files/MetaTrader 5 IC Markets Global"
DISPLAY=:99 WINEPREFIX=~/.wine wine metaeditor64.exe /compile:"MQL5\Experts\hermes_bridge.mq5" /log
```

**Filling Mode:** IC Markets Netting requer `ORDER_FILLING_IOC`. `ORDER_FILLING_FOK` = retcode 10030 (Unsupported filling mode).

**Deploy (no MT5 desktop):**
1. Habilitar **AutoTrading** (botão verde na toolbar — desligado = retcode 10027)
2. Ctrl+N → Expert Advisors → arrastar `hermes_bridge` para um chart
3. Confirmar OK
4. **Após recompilar:** Remove → arrasta de novo (MT5 não recarrega EA automaticamente)

**Teste rápido:**
```bash
python3 ~/.hermes/scripts/hermes_mt5_bridge.py order EURUSD BUY 0.01
python3 ~/.hermes/scripts/hermes_mt5_bridge.py close_all
python3 ~/.hermes/scripts/hermes_mt5_bridge.py status
```
- `~/.hermes/scripts/tv_data.py` v2 — híbrido 3 camadas: yfinance (OHLC) → cache → CDP (live)

**Fluxo do mt5_direct.py v5 (Desktop Daemon):**
1. Conecta `ws://localhost:9876` (daemon systemd com vars corretas)
2. `key F9` → janela New Order
3. `key ctrl+a` + `type EURUSD` + `key enter`
4. `key Tab`×2 → Volume → `key ctrl+a` + `type 0.01`
5. `key Tab`×2 → SL → `key ctrl+a` + `type 1.16405`
6. `key Tab` → TP → `key ctrl+a` + `type 1.16505`
7. `key alt+b` (Buy) ou `key alt+s` (Sell)
8. `key escape` fecha janela

⚠️ MT5 precisa estar com foco (visível na tela). O daemon não tem window management.
Ver `desktop-control` skill → `references/mt5-order-via-daemon.md`.

**Pitfalls Wayland + Desktop (25/05 v6):**
- **✅ MQL5 EA Bridge (PREFERIR):** `hermes_bridge.ex5` no chart → Python escreve JSON → EA executa OrderSend() nativo. 100% confiável, sem dependência de UI. Ver `desktop-control` skill → `references/mql5-ea-bridge.md`.
- **✅ xdotool no DISPLAY=:0 vê janelas XWayland:** Apps Wine (MT5) são visíveis. `DISPLAY=:0 xdotool search --name ""` lista janelas com nome e posição. Substitui screenshots (quebrados) para diagnóstico.
- **✅ Desktop Daemon v3 keycodes:** Params no sub-objeto. ydotool converte nomes→keycodes (81 entradas). `{"action":"key","params":{"key":"f9"}}`
- **❌ GNOME overview + Wine NÃO funciona:** Wine Wayland não é indexado na busca do GNOME. Super → "metatrader"/"icmarkets" não acha a janela.
- **❌ ydotool direto falha:** Faltam env vars (WAYLAND_DISPLAY, XDG_RUNTIME_DIR). O Daemon já tem as vars corretas.
- **MT5 precisa estar visível:** O Daemon envia teclas pra janela ativa. Se MT5 não estiver focado, as teclas vão pra outra janela.
- **ABNT2 + ydotool:** keyboard layout brasileiro corrompe caracteres especiais. Para ordens forex só usamos números e pontos — sem problemas.
- **MetaTrader5 pip package = Windows only:** NÃO tenta instalar no Linux. Alternativas: OHLC via yfinance/tv_data.py, execução via ydotool, monitoramento via pgrep.
- **Cron job no_agent:** O job `21f7caf29606` usa `no_agent: true` — o script `forex_bot_real.py` roda diretamente, stdout é entregue ao usuário. Telegram via `send_telegram()` é extra.
- ✅ **tv_data.py v2 híbrido:** yfinance primário (OHLC) + CDP live quote + cache local. 403-405 candles M15 por par.
- ✅ **Bot sem sinais = normal na Ásia:** CHoCH+FVG+CRT requer volatilidade. Sessão asiática (UTC 0-5) tem ATR ~2-3 pips — 0 sinais esperado.
- ✅ **CRT mandatory:** Backtest confirma: 8 trades com CRT = 87.5% WR (+54p) vs 18 trades sem CRT = 61.1% (+9.9p). CRT multiplica PnL por 5.5x.

## Display + MT5 + CDP

MT5 roda no desktop Wayland/GNOME — sem necessidade de VNC, Xvfb, ou display virtual. `ydotool` (kernel-level via /dev/uinput) envia teclas para o display ativo.

**CDP Browser ports:**
- `:9222` = Brave REAL do usuário — evitar para automação
- `:9223` = Brain browser headless — usar para automação CDP

**Verificação de saúde:**
```bash
# MT5 rodando?
pgrep -a -f terminal64    # Deve mostrar "MetaTrader 5 IC Markets Global"

# ydotoold ativo?
pgrep ydotoold            # Deve retornar PID

# CDP browser acessível?
curl -s http://localhost:9223/json/version | python3 -c "import sys,json; print(json.load(sys.stdin).get('Browser',''))"
```
