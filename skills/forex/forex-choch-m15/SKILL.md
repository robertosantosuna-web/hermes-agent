---
name: forex-choch-m15
description: "V12 (29/05): Multi-Agente (Perfil+Sessão+Estrutura+Padrão) + Self-Learning. Backtest 21d: 110 trades, 62% WR, +162R, PF 4.86. CDP TradingView M1, RR 3:1, gestão 2R/3R."
---
## AutoPilot v12 — Multi-Agente + Self-Learning (29/05/2026) ⭐

> **Backtest 21 dias:** 110 trades, 62% WR, +162R, PF 4.86, 5 trades/dia
> **Pipeline:** Multi-TF Bias → 5 Agentes votam → Entrada M1 → RR 3:1 → 2R/3R
> **⚠️ REGRA #1:** RR 3:1 SEMPRE. Nunca reduzir. Roberto recusou RR 2:1.
> **⚠️ REGRA #2:** Validar em backtest antes de aplicar (`validate_before_apply.py`).
> **⚠️ REGRA #3:** CRT é filtro de qualidade, NÃO substituto do bias.
> **📚 Lições:** `references/multi-agent-lessons.md`

## Pipeline Final
```
1. Multi-TF Bias (W/D/H4 PDH/PDL) → maioria define BUY/SELL
2. CRT filter opcional → se CRT candle + sweep alinhar com bias = CRT+
3. M1 FVG na direção do bias
4. FILTROS: candle fechado + ADX/DMI alinhado + Volume > 1.3x média
5. SL = 2× ATR(14), clamp 10-30p (dinâmico, não fixo!)
6. RR 3:1 fixo (sempre!)
7. 2R breakeven + 3R trail no monitor
```

## Fonte de Dados M1 — TradingView CDP
**fetch_ohlcv para M1 usa CDP TradingView como fonte PRIMARIA:**
- Extrator: /home/roberto/tv_ohlc_extractor.py → Brave :9222 WebSocket CDP
- 544 velas M1 reais extraidas, sem erro de escala
- yfinance é FALLBACK (limite 7 dias M1, colunas inconsistentes)

**PITFALL yfinance colunas minusculas:** Para interval=1d, yfinance retorna h/l/c minusculas. get_multi_tf_bias normaliza via col_map. NAO usar df['High'] direto.

## Filtros de Ruido M1
- **ATR(14) no M15**: SL = 1.5x ATR, clamp 10-30p forex / 200-300t XAU. Ver `references/v12-timeframe-rules.md`
- **DMI(14) no M1**: so entra se alinhado com bias (BUY→DI+>DI-, SELL→DI->DI+)
- Volume: > 1.3x media movel 20 periodos
- Candle fechado: ignora candle atual (indice < len-1)
- **REGRA: M15 é o timeframe mínimo para ATR e DMI. M1 é só entrada.**
- Sem talib — numpy manual

## CRT Model (filtro adicional, NAO substitui)
Ver `references/crt-model-lessons.md` — regras completas e licoes.

## Anti-correlação (moeda BASE)
```python
{'USD': ['USDJPY','USDCAD'], 'EUR': ['EURUSD','EURJPY'], 'GBP_XAU': ['GBPUSD','GBPJPY','XAUUSD']}
MAX_CORRELATED_PAIRS = 1
```

## Backtest V10 (21 dias M1, yfinance chunking)
- 12 trades, 41.7% WR, +8R, PF 2.14
- M1 > M15: WR 42% vs 27%
|---------|-------------------|-----------------|
| Gatilho | PDH/PDL rompimento | CRT candle + sweep |
| Timeframe | Diário → H1/M15 | H1 → M15 |
| Entrada | FVG qualquer lugar | FVG dentro do sweep |
| Níveis | 1 por sinal | Até 2 por setup |
| SL | 10-20p fixo | Técnico (range CRT) |
| TP | 3:1 fixo | 1:1 parcial + 2:1 final |
   ├─ Rompeu PDH + fechou fora   → BUY
   ├─ Rompeu PDL + fechou fora   → SELL
   └─ NEUTRAL → pula

2. CONFIRMAÇÃO CHoCH (detect_choch) — H1, fallback M15
   ├─ BUY  → rompeu swing high?
   ├─ SELL → rompeu swing low?
   └─ Não → pula

3. ENTRADA M1 (detect_fvg_m1)
   FVG na direção confirmada → SL = gap*1.2 (10-20p)
```

### Risco & Gestão
- Risco fixo **0.5%**, RR **3:1** (meta 1.5%)
- Volume = risk_dollar / (sl_pips × pip_value)
- Anti-correlação: 1 par por moeda base (USD/EUR/GBP_XAU)

### Gestão 2R/3R (`forex_realtime_monitor.py`)
- **2R**: SL → entry (breakeven)
- **3R**: SL → +1.5R (trava lucro)
- Loss: fecha se -80% do risco
- Dados: `open_trades.json` salvo pelo `_save_open_trade()`_BALANCE).
> **📊 Daily Bias (Centry Analyst):** ver `references/centry-analyst-daily-bias.md` — PDH/PDL como filtro macro (reversão vs continuação).
> **🔄 Monitor 2R/3R:** `forex_realtime_monitor.py` — 2R→SL=entry (breakeven), 3R→SL=+1.5R (trava), -80%R→fecha.

### Estratégia V9.3: H1→M1 (29/05/2026) ⭐
Substitui as 3 estratégias antigas (E1/E2/E3). Uma única estratégia unificada:
1. **Direção H1**: SMA20 inclinação + preço vs SMA → BUY/SELL/NEUTRAL
2. **Entrada M1**: `detect_fvg_m1()` — FVG no M1 filtrado apenas na direção do H1
3. **SL**: gap M1 × 1.2, clamp 10-20 pips forex / 200-300 ticks XAU
4. **TP**: 3× SL (RR 3:1 fixo para todas as entradas)
5. **Risco fixo**: 0.5% do saldo (`RISK_PERCENT=0.5`, removido `calculate_dynamic_risk`)
6. **Anti-correlação por moeda BASE**: USD (USDJPY+USDCAD), EUR (EURUSD+EURJPY), GBP_XAU (GBPUSD+GBPJPY+XAUUSD). `MAX_CORRELATED_PAIRS=1`.
7. **Monitor 2R/3R**: `forex_realtime_monitor.py` lê `open_trades.json` — 2R breakeven, 3R trail +1.5R, loss -80%R

Versão revisada pelos 4 especialistas IA (Gemini, DeepSeek, ChatGPT, Grok) com 2 rodadas de feedback. Melhorias:

### Melhorias sobre v9.1

| # | Melhoria | Detalhe |
|---|----------|---------|
| 1 | **Breakeven em 1R com buffer** | SL vai pra `entry ± max(spread×1.5, ATR×0.1)` — nunca perde após confirmar |
| 2 | **6 Degraus progressivos** | 1R→25%, 2R→40%, 3R→55%, 5R→70%, 8R→82%, 12R→90% |
| 3 | **Aceleração por ativo** | EURUSD 1.30x, XAUUSD 1.15x, JPY 1.20-1.25x |
| 4 | **CAP absoluto 95%** | Stop nunca trava >95% (evita SL inválido acima do preço) |
| 5 | **ATR como piso** | `min(trailing_sl, price - 0.5 ATR)` — evita stop em ruído |

### Lógica v9.2

```python
# Parâmetros
LOCK_STEPS = [(1.0,0.25), (2.0,0.40), (3.0,0.55), (5.0,0.70), (8.0,0.82), (12.0,0.90)]
TRAIL_ACCEL_CAP = 0.95
ACCEL_BY_ASSET = {'XAUUSD':1.15, 'EURUSD':1.30, 'USDJPY':1.25, 'default':1.25}

# 1. Breakeven com buffer
if rr >= 1.0:
    buffer = max(spread * 1.5, atr * 0.1)
    breakeven_sl = entry + buffer  # long

# 2. Lock-in progressivo
protect_pct = max(pct for rr_thresh, pct in LOCK_STEPS if rr >= rr_thresh)

# 3. Aceleração com cap
accel = ACCEL_BY_ASSET.get(symbol, 1.25)
protect_pct = min(0.95, protect_pct * accel)

# 4. ATR piso
new_sl = entry + (profit_distance * protect_pct)
if atr > 0:
    new_sl = min(new_sl, current_price - atr * 0.5)  # Long
```

**Trigger parcial:** RR ≥ 3.0 → fecha 50% (mantido da v9.1)
**Tracking:** `~/.hermes/forex/partials.json`

Ver: **[references/trailing-stop-v2-ai-review.md](references/trailing-stop-v2-ai-review.md)** — análise completa dos 4 especialistas.

### Monitor de Conectividade (28/05/2026) 🛡️

Proteção contra instabilidade de rede: AutoPilot pausa NOVAS ordens quando detecta falha, mas continua gerenciando posições já abertas.

- **Ping:** 8.8.8.8 + 1.1.1.1, timeout 3s
- **MT5 bridge:** verifica `hermes_resp.json` atualizado nos últimos 30s
- **2 falhas consecutivas** → pausa + alerta crítico no Tálamo
- **5 checks estáveis** → retoma automaticamente (~15 min)
- Estado: `~/.hermes/forex/connectivity_state.json`
- Funções: `check_connectivity()`, `update_connectivity()`, `is_trading_paused()`

Ver: **[references/autopilot-connectivity-monitor.md](references/autopilot-connectivity-monitor.md)**.

### Circuit Breakers v2 — Kill Switch (Gemini feedback)

| Gatilho | Ação | Kill Switch? |
|---------|------|:---:|
| Drawdown ≥5% diário | 💀 Fecha TODAS posições | ✅ |
| 5 perdas consecutivas | 💀 Fecha TODAS posições | ✅ |
| >3 falhas bridge/hora | 💀 Fecha TODAS posições | ✅ |
| >40% BE prematuro (>2R potencial) | ⛔ Suspende novas ordens | ❌ |
| Slippage >2x spread | ⚠️ Alerta (não suspende) | ❌ |

Arquivo: `forex/circuit_breakers.json`. Reset automático todo dia 00:00 UTC.

### Ghost Tracker (Gemini: "price ghost")

Quando posição fecha no breakeven, continua monitorando o preço por 2h para ver se atingiria o target original. Dados salvos em `forex/ghost_tracker.json` para alimentar métrica de BE prematuro.

### Log isolado de bridge

`forex/bridge_errors.log` — timestamp + contagem de falhas/hora. Separa erros de infraestrutura de erros de execução.

### Navegador Interno (Chromium headless)

Porta CDP: 9226. Systemd service `internal-browser.service`. Script: `~/.hermes/brain/internal_browser.py`. Perfil: `~/.hermes/browser-profile/`. (28/05/2026) 🛡️

Sistema de suspensão automática de trading quando condições de risco são detectadas. Revisado por Gemini (métricas de suspensão).

| # | Breaker | Gatilho | Ação |
|---|---------|---------|------|
| 1 | Drawdown diário | equity -5% vs saldo inicial | ⛔ Suspende |
| 2 | Perdas consecutivas | 5 trades negativos seguidos | ⛔ Suspende |
| 3 | Falhas de bridge | >3 falhas em 1h | ⛔ Suspende |
| 4 | Breakeven prematuro | >40% BE saem antes de 2R | ⚠️ Alerta |
| 5 | Slippage alto | >2x spread normal | ⚠️ Alerta |

Estado: `~/.hermes/forex/circuit_breakers.json`. Reset diário às 00:00 UTC.
Resumo mostra `⛔CB` quando circuit breaker ativo.
Funções: `check_circuit_breakers()`, `record_trade_result()`, `record_bridge_failure()`.

Ver: **[references/circuit-breakers-v1.md](references/circuit-breakers-v1.md)** — implementação completa.

### Gemini: Fatos Crus (29/05/2026)

Análise mais prática entre os 4 especialistas. Destaques:
- Spread filter: pausar trailing se spread > 3x média (NY/Londres)
- ATR dissociado: XAUUSD 1.0 ATR vs forex 0.5 ATR  
- Execução cega 48h: terminal fechado, relatório automatizado

Ver: **[references/gemini-fatos-crus-2026-05-29.md](references/gemini-fatos-crus-2026-05-29.md)**.

### MQL5 patch bug (pitfall)

Ao editar arquivos .mq5 via `patch` tool, strings ficam double-escaped (`\"` vira `\\\"`).
Corrigir com: `python3 -c "p=open('arquivo.mq5','rb').read();open('arquivo.mq5','wb').write(p.replace(b'\\\\\\\\\"',b'\"'))"`

## V9.0 — Multi-Confluência SMC/ICT (28/05/2026) ⭐ ATUAL

A V8 (3 estratégias) foi substituída pela **Multi-Confluência SMC/ICT** validada por backtest: 25 trades, 60% WR, **Profit Factor 3.25**. Filtro 4+ confluências: Killzone + HTF Alignment + Liquidity Sweep (mandatórios) + FVG/OB/SMT (opcionais). Pares PRIORITY: USDJPY, EURJPY, GBPJPY. XAUUSD: 44.8% WR, PF 1.08 (paper apenas). Córtex Visual: `~/.hermes/brain/cortex_visual.py`. Cron: */15 * * * 1-5.

**Bibliotecas:** `smartmoneyconcepts.smc` (fvg, ob, liquidity, bos_choch), `backtesting` (Backtest, Strategy), `quantstats` (reports.full), `mplfinance`, `forex-python`.

**Documentos:** `~/.hermes/forex/BACKTEST_REPORT.md`, `~/daytrade_knowledge_avancado.md`.

**Pitfalls V9:** NUNCA Silver Bullet sem filtros (23% WR). NUNCA SMC Fractal standalone (5.6% WR). XAUUSD usar TP 1.5:1. smartmoneyconcepts precisa de `swing_highs_lows` primeiro.

Ver: `references/v9-multi-confluence-2026-05-28.md`

---
# HISTÓRICO (V8 e anteriores — referência)

## 🛡️ AutoPilot — Gerenciamento Autônomo (26/05/2026)

Sistema autônomo que gerencia posições sem intervenção humana:
- **AutoPilot** (`cdbae3c13baa`, */5 min): fecha pares tóxicos (WR<30%), corta perdas >$2 forex / >$10 metal, drawdown protection 3%, protege lucro, **fecha concentração ≥4 no mesmo par**
- **Monitor Tempo Real** (`forex_realtime_monitor.py`, */2s): breakeven @ 1R, trailing stop @ 2R, proteção de perda. Zero tokens. Comunicação via EA bridge (modify_position, close_symbol).
- **Codex Monitor** (`48425c92b336`, */30min): GPT-5.5 analisa status, envia alertas via Neural Link
- **Bot Multi-Strategy** (`ca8d82dc9fa5`, */15 min): scan + execução com SL≥15p, volume exponencial, WR enforcement

**REGRA ABSOLUTA:** NUNCA pedir pro Roberto fechar posição manualmente. O AutoPilot + Monitor fazem tudo.
**REGRA ABSOLUTA:** NUNCA abrir trade com SL < 15 pips (forex) ou < $12 (metal). STOPLEVEL do broker rejeita stops menores.
**REGRA ABSOLUTA:** Monitoramento em TEMPO REAL (3s) — NÃO polling de 5 minutos. Forex é rápido demais pra 5min.

## ⚡ Monitor Tempo Real — Breakeven + Trailing Stop (26/05/2026)

Script: `scripts/forex_realtime_monitor.py`. Roda como processo background (PID 631901).
Zero tokens (script no_agent). Comunicação via EA bridge (arquivo JSON).

### Funcionalidades
- **Polling a cada 3 segundos** — verifica posições abertas e age
- **Breakeven @ 1R** — move SL para entry quando lucro atinge $1.50 (forex) / $10 (ouro)
- **Trailing Stop @ 2R** — ativa com $3.00 (forex) / $20 (ouro), segue 75% do lucro
- **Proteção de perda** — fecha se perda > $2 (forex) / $10 (metal)
- **Lock file** (`Common/Files/.monitor_lock`) — evita conflito com comandos manuais

### Iniciar/parar
```bash
python3 ~/.hermes/scripts/forex_realtime_monitor.py &   # iniciar
pkill -f forex_realtime_monitor.py                       # parar
```

### ⚠️ PITFALL: Conflito de comandos EA bridge
O EA bridge usa arquivos únicos (`hermes_cmd.json` / `hermes_resp.json`). Se dois processos escrevem simultaneamente, um sobrescreve o outro. O monitor usa `fcntl.flock(LOCK_EX)` no arquivo `.monitor_lock` para serializar acesso. Comandos manuais devem usar o mesmo lock ou pausar o monitor primeiro.

Ver: **[references/realtime-monitor.md](references/realtime-monitor.md)**.

Ver: **[references/autopilot-system.md](references/autopilot-system.md)**.

## ⚡ EA Bridge v1.1 — Comandos disponíveis (26/05/2026)

EA `hermes_bridge.ex5` (42KB, MQL5) compilado com MetaEditor64 via Wine:
- `order` — abre posição com validação STOPLEVEL
- `close_all` — fecha todas as posições
- `close_symbol` — fecha posições de um símbolo específico
- `status` — retorna balance, equity, positions (c/ entry, sl, tp)
- `symbol_info` — retorna STOPLEVEL, spread, tick_value, digits de um símbolo
- **`modify_position`** — modifica SL/TP de posição existente via `CTrade::PositionModify`

### Comandos:
```bash
python3 hermes_mt5_bridge.py status
python3 hermes_mt5_bridge.py symbol_info XAUUSD
# modify_position requer envio direto via JSON:
echo '{"action":"modify_position","ticket":1669000000,"sl":1.10500}' > Common/Files/hermes_cmd.json
```
| Forex | -$2.00 | SL ~$1.50 (15p × $0.10) |
| **Metal (XAU)** | **-$10.00** | SL ~$12.00 (1200t × $0.01) |

### Concentração — Ação Automática
- 🔴 **≥4 no mesmo par** → FECHA TODAS as posições do par (não só alerta)
- 🔴 **≥4 no grupo correlacionado** → fecha o par mais concentrado do grupo
## 🛡️ AutoPilot — Gerenciamento Autônomo (26/05/2026)

Sistema autônomo que gerencia posições sem intervenção humana:
- **AutoPilot** (`cdbae3c13baa`, */5 min): fecha pares tóxicos (WR<30%), corta perdas >$2 forex / >$10 metal, drawdown protection 3%, protege lucro, **fecha concentração ≥4 no mesmo par**
- **Monitor Tempo Real** (`forex_realtime_monitor.py`, */2s): breakeven @ 1R, trailing stop @ 2R, proteção de perda. Zero tokens. Comunicação via EA bridge (modify_position, close_symbol).
- **Codex Monitor** (`48425c92b336`, */30min): GPT-5.5 analisa status, envia alertas via Neural Link
- **Bot Multi-Strategy** (`ca8d82dc9fa5`, */15 min): scan + execução com SL≥15p, volume exponencial, WR enforcement

**REGRA ABSOLUTA:** NUNCA pedir pro Roberto fechar posição manualmente. O AutoPilot + Monitor fazem tudo.
**REGRA ABSOLUTA:** NUNCA abrir trade com SL < 15 pips (forex) ou < $12 (metal). STOPLEVEL do broker rejeita stops menores.
**REGRA ABSOLUTA:** Monitoramento em TEMPO REAL (3s) — NÃO polling de 5 minutos. Forex é rápido demais pra 5min.

## ⚡ Monitor Tempo Real — Breakeven + Trailing Stop (26/05/2026)

Script: `scripts/forex_realtime_monitor.py`. Roda como processo background (PID 631901).
Zero tokens (script no_agent). Comunicação via EA bridge (arquivo JSON).

### Funcionalidades
- **Polling a cada 3 segundos** — verifica posições abertas e age
- **Breakeven @ 1R** — move SL para entry quando lucro atinge $1.50 (forex) / $10 (ouro)
- **Trailing Stop @ 2R** — ativa com $3.00 (forex) / $20 (ouro), segue 75% do lucro
- **Proteção de perda** — fecha se perda > $2 (forex) / $10 (metal)
- **Lock file** (`Common/Files/.monitor_lock`) — evita conflito com comandos manuais

### Iniciar/parar
```bash
python3 ~/.hermes/scripts/forex_realtime_monitor.py &   # iniciar
pkill -f forex_realtime_monitor.py                       # parar
```

### ⚠️ PITFALL: Conflito de comandos EA bridge
O EA bridge usa arquivos únicos (`hermes_cmd.json` / `hermes_resp.json`). Se dois processos escrevem simultaneamente, um sobrescreve o outro. O monitor usa `fcntl.flock(LOCK_EX)` no arquivo `.monitor_lock` para serializar acesso. Comandos manuais devem usar o mesmo lock ou pausar o monitor primeiro.

Ver: **[references/realtime-monitor.md](references/realtime-monitor.md)**.

Ver: **[references/autopilot-system.md](references/autopilot-system.md)**.

## ⚡ EA Bridge v1.1 — Comandos disponíveis (26/05/2026)

EA `hermes_bridge.ex5` (42KB, MQL5) compilado com MetaEditor64 via Wine:
- `order` — abre posição com validação STOPLEVEL
- `close_all` — fecha todas as posições
- `close_symbol` — fecha posições de um símbolo específico
- `status` — retorna balance, equity, positions (c/ entry, sl, tp)
- `symbol_info` — retorna STOPLEVEL, spread, tick_value, digits de um símbolo
- **`modify_position`** — modifica SL/TP de posição existente via `CTrade::PositionModify`

### Comandos:
```bash
python3 hermes_mt5_bridge.py status
python3 hermes_mt5_bridge.py symbol_info XAUUSD
# modify_position requer envio direto via JSON:
echo '{"action":"modify_position","ticket":1669000000,"sl":1.10500}' > Common/Files/hermes_cmd.json
```

## 📈 Risco Exponencial (26/05/2026)

Volume calculado dinamicamente: `calculate_volume(balance, sl_pips, pair, wr_real)`.
- Tiers: $400→2%, $600→3%, $1000→5%, $2000→7%, $5000→10%
- Bônus por WR: +1% a +3%. Penalidade: -1% a -2%.
- Resultado: $400→0.05 lot, $1000→0.40 lot, $5000→4.00 lot
Ver: **[references/exponential-risk-model.md](references/exponential-risk-model.md)**.

## 🥇 XAU/USD (Ouro) — V8 Multi-Strategy (26/05/2026)

Estudo completo em 59 dias, 3 timeframes. Ouro é **viável** com FVG+CRT.

### Resultados Backtest (GC=F, 59d, gap≥$1, CRT≥70%, RR=3:1)

| TF | Trades | WR | PF | T/dia | SL médio | Melhor KZ |
|----|--------|-----|-----|-------|----------|-----------|
| M5 | 540 | 58.0% | 3.08 | 9.3 | $6.7 | NY PM 69% |
| M15 | 235 | 63.4% | 2.80 | 4.2 | $10.0 | Lond Close 79% |
| **M30** | **143** | **67.1%** | **3.37** | **2.9** | **$11.8** | **Asia 77%** |

### Config Recomendada
```python
'XAUUSD': {'tf': '30m', 'wr': 67.1, 'min_sl_dollar': 12.0, 'min_gap_dollar': 1.0}
```

### Diferenças Ouro vs Forex
- ⚠️ **Ouro usa DÓLARES, não pips.** Gap de $1 = gap real (não 0.0001 como forex)
- STOPLEVEL IC Markets: ~20-30 pontos ($2-3). SL de $12 = 4-6× acima → seguro
- 0.01 lote = 1 oz = $0.10/ponto
- Volume para $399: 0.06 lotes (2% risco com SL $12)
- Killzones: Asia (0-5 UTC) é surpreendentemente boa (77% WR) — ouro tem volume 24h
- **FVG detection:** sem filtro de pavio (wick_pct quebra em ativos de preço alto)

### Integração no Bot
O `calculate_volume()` funciona sem adaptação (usa `sl_pips` em pontos, que no ouro são dólares).
Adicionar como 7º par no `forex_bot_multi.py`.

- **[references/v8.4-sl-tp-fixes-2026-05-27.md](references/v8.4-sl-tp-fixes-2026-05-27.md)** — V8.4 (27/05): SL/TP clamp, SL=0 rejection, audit log, pipeline cleanup. **PITFALL: never test with execute_trade() — it sends real MT5 orders. Use validate_sl_tp.py.**
- **[references/v8.1-fixes-2026-05-27.md](references/v8.1-fixes-2026-05-27.md)** — V8.1 fixes (27/05): XAUUSD precision, NN Engine activation, N. Accumbens seed, Meta-Observer auto-heal
- **[references/v8.2-autopilot-cycle-of-death.md](references/v8.2-autopilot-cycle-of-death.md)** — V8.2 critical fix (27/05): AutoPilot hardcoded $400 + 3% DD caused open→close→repeat cycle. 154 trades/day. Fix: dynamic balance, 15% DD, cooldown, MAX_DAILY_TRADES=20.
- **[references/v8.3-overtrading-fixes-2026-05-27.md](references/v8.3-overtrading-fixes-2026-05-27.md)** — V8.3 critical fix (27/05): Bot abriu 172 trades/dia por 4 bugs (timestamp mismatch, zero duplicate check, MAX_POSITIONS=8, trade_log ghost). NEO Analytical Worker debate → 5 recomendações implementadas: signal age filter, killzone universal gating, circuit breaker, learning loop, E2 strengthening.
- **[references/xauusd-backtest-2026-05-26.md](references/xauusd-backtest-2026-05-26.md)** para tabelas completas.

## ☠️ PITFALL: Fallback duplica ordens (corrigido 26/05)

**SINTOMA:** Mesma ordem aparece como `✅ ORDEM EXECUTADA` e depois `🔄 Fallback direto` no mesmo log, potencialmente abrindo 2 posições idênticas.

**CAUSA:** `execute_trade()` verificava `result.get('retcode') == 10009` (código do mt5_direct), mas o EA bridge retorna `{'status': 'ok', 'ticket': 123}` sem campo `retcode`. Como `retcode` era None, caía no `else` e disparava o fallback, mesmo com a ordem já executada.

**CORREÇÃO:** Verificar múltiplos indicadores de sucesso:
```python
is_ok = (result and (
    result.get('status') == 'ok' or       # EA bridge
    result.get('retcode') == 10009 or      # mt5_direct
    result.get('ticket')                   # EA bridge tem ticket
))
```
Se `is_ok` → sucesso. Se `result.get('status') == 'error'` → falha conhecida, não tentar fallback. Fallback só se EA nem respondeu (result é None).

## ☠️ PITFALL: Bot sem anti-duplicata = 172 trades/dia (27/05/2026)

**SINTOMA:** 172 trades em um dia com conta de $400. Balance $447→$363. Sinais repetidos a cada 15min nos mesmos pares.

**CAUSA:** 4 bugs simultâneos:
1. Limite diário nunca ativava (procurava `timestamp` mas bot salva `time` no trade_log)
2. Nenhuma verificação se o par já tinha posição aberta no MT5
3. `record_trade()` importado mas nunca chamado — trade_log fantasma
4. MAX_POSITIONS=8 com $400 (16% risco simultâneo)

**CORREÇÃO (27/05):**
```python
# 1. Fix trade counter
trades_hoje = sum(1 for t in data['trades'] 
                  if str(t.get('timestamp', t.get('time', ''))).startswith(today))

# 2. Anti-duplicata — verificar open_symbols do MT5
for p in status.get('positions_data', []):
    open_symbols.add(p.get('symbol', ''))
# Depois, no loop de seleção:
if pair_symbol in open_symbols:
    continue  # Já tem posição neste par

# 3. record_trade() chamado após cada send_order bem-sucedido
record_trade(direction, pair, entry, sl, tp, volume=VOLUME)

# 4. MAX_POSITIONS: 8 → 4
```

**Ver também:** `references/v8.3-overtrading-fixes-2026-05-27.md` para o diagnóstico completo + 5 recomendações NEO.

## ☠️ PITFALL: `PositionModify` não existe no MQL5 (26/05)

**SINTOMA:** Compilação do EA falha com `error 256: undeclared identifier 'PositionModify'`.

**CAUSA:** `PositionModify()` não é uma função global no MQL5. Para contas HEDGE, a modificação de SL/TP requer a classe `CTrade` do include `<Trade/Trade.mqh>`.

**CORREÇÃO:**
```cpp
#include <Trade/Trade.mqh>
CTrade Trade;
// ...
Trade.PositionModify(ticket, sl, tp);  // ✅ CORRETO
```
NUNCA usar `PositionModify(ticket, sl, tp)` — não compila.

**Ver também:** `Trade.PositionModify` também pode falhar silenciosamente (retorna false sem erro aparente). Verificar `GetLastError()` após a chamada. Causa comum: SL muito próximo do preço atual (STOPLEVEL violation).

**SINTOMA:** XAUUSD aberto com SL $12, fechado pelo AutoPilot com -$3.91 — apenas 32% do SL.

**CAUSA:** O AutoPilot usava threshold fixo de -$2.00 para TODOS os pares. Calibrado para forex (SL ~$1.50), não para ouro (SL $12.00).

**CORREÇÃO (26/05):** Threshold por tipo de par:
```python
if 'XAU' in symbol.upper():
    loss_limit = -10.0  # Ouro
else:
    loss_limit = -2.0   # Forex
```

**Também afetado:** AutoPilot NUNCA deve fechar trade antes do SL ser atingido. O threshold serve para cenários onde o SL foi ignorado (STOPLEVEL bug) — mas se o SL é válido, deixa o trade respirar.

## ☠️ PITFALL: SMC Fractal (E2) não calibrada para metais (26/05/2026)

**SINTOMA:** XAUUSD aberto pela E2 com SL $36 (inviável para conta de $400).

**CAUSA:** `detect_smc_fractal()` usa `min_swing_pips=5` — no ouro isso é $0.05. Os swings detectados são ruído. O SL resultante é enorme.

**CORREÇÃO:** E2 desabilitada para metais (`if not is_metal`). XAUUSD só opera E1 (FVG+CRT) e E3 (S/R+FVG).

**Regra:** Toda nova estratégia precisa ser calibrada para ouro separadamente. Parâmetros de forex NÃO se transferem.

## ☠️ PITFALL: `execute_trade()` testa com ordens REAIS (27/05/2026)

**SINTOMA:** Chamar `execute_trade()` via `python3 -c "from forex_bot_multi import execute_trade; ..."` abriu ordem real no MT5 (EURJPY ticket #1671521036), causando -$3.36 de prejuízo ao fechar.

**CAUSA:** `execute_trade()` chama `send_order()` que escreve JSON → EA bridge → MT5 OrderSend. Não existe modo "dry run" — toda chamada é real.

**CORREÇÃO:** Testar apenas funções isoladas (`calculate_sl_tp()`, `calculate_volume()`, `detect_fvg()`). Para teste completo de pipeline, usar `validate_sl_tp.py` (testes secos, sem MT5):
```bash
python3 ~/.hermes/scripts/validate_sl_tp.py  # Testa SL/TP sem abrir ordens
```

**REGRA:** NUNCA chamar `execute_trade()` fora do fluxo normal do bot. NUNCA testar com `python3 -c "import execute_trade"`.

## ☠️ PITFALL: Implementar correções sem validar primeiro (27/05/2026)

**REGRA ABSOLUTA:** Não implementar nada no código de produção sem testar ou validar primeiro.

Fluxo correto:
1. Identificar o bug → documentar
2. Criar script de validação isolado (ex: `validate_sl_tp.py`) 
3. Rodar validação → confirmar que a correção funciona
4. Só então aplicar no código de produção
5. NUNCA testar com `execute_trade()` — ordens reais

**Exemplo de validação segura:**
```bash
# Criar script que testa funções isoladas (sem MT5)
python3 -c "
from forex_bot_multi import calculate_sl_tp
sl, tp = calculate_sl_tp('SELL', 1.16242, 30.0, 2.0, 0.0001, False)
print(f'SL={sl:.5f} TP={tp:.5f}')  # Apenas matemática, sem ordens
"
```

## 📊 Chart Renderer — Gráficos sem Browser/CDP (27/05/2026)

`chart_renderer.py` e `terminal_chart.py` substituem completamente a dependência de browser/CDP/TradingView para análise visual:

### chart_renderer.py (HTML interativo)
- Dados: **TradingView via tvDatafeed** (primário) → yfinance (fallback)
- Detecta FVGs, swing highs/lows
- Renderiza HTML interativo com **lightweight-charts** (estilo TradingView, sem distorção de zoom)
- Salva em `~/.hermes/forex/charts/`

### terminal_chart.py (ASCII direto no terminal — ZERO browser)
- Dados: **TradingView via tvDatafeed** (sem browser, sem GUI)
- Renderiza candles coloridos (verde/vermelho), FVGs (▼▲), swings, sentimento
- ANSI color codes — funciona em qualquer terminal
- **PITFALL:** TvDatafeed retorna colunas minúsculas (`open`, `high`, `low`, `close`), NÃO maiúsculas como yfinance

```bash
# HTML interativo
python3 ~/.hermes/scripts/chart_renderer.py GBPJPY 15m     # Um par
python3 ~/.hermes/scripts/chart_renderer.py --all            # Todos os 6 pares

# Terminal ASCII (zero browser)
python3 ~/.hermes/scripts/terminal_chart.py GBPJPY 15m      # 60 velas
python3 ~/.hermes/scripts/terminal_chart.py EURUSD 1h 100  # H1, 100 velas
python3 ~/.hermes/scripts/terminal_chart.py XAUUSD 15m     # Ouro
```

Ver: **[scripts/chart_renderer.py](scripts/chart_renderer.py)** e **[scripts/terminal_chart.py](scripts/terminal_chart.py)**.

## 📊 Chart Pattern Consolidator (27/05/2026)

`chart_pattern_consolidator.py` reduz os dumps de 1.5MB do Chart Pattern Study em insights acionáveis:
- Consolida padrões por par/timeframe/tipo
- Calcula dominância de viés (bullish/bearish)
- Gera sinais quando dominância ≥70% em um timeframe
- Output: `~/.hermes/forex/chart_patterns_summary.json` (12KB) + `chart_signals.json`

```bash
python3 ~/.hermes/scripts/chart_pattern_consolidator.py      # Último dump
python3 ~/.hermes/scripts/chart_pattern_consolidator.py --json  # JSON output
```

Ver: **[scripts/chart_pattern_consolidator.py](scripts/chart_pattern_consolidator.py)**.

## 🔍 Descoberta: XAUUSD STOPLEVEL = 0 (26/05/2026)

Confirmado via `symbol_info` no EA bridge: XAUUSD não tem STOPLEVEL no IC Markets.
- `stoplevel_pips = 0` — sem distância mínima para stops
- `spread_pips = 40` ticks ($0.40) — aceitável
- `tick_value = 1.0` (por 1 lote padrão = 100 oz) → $0.01/tick com 0.01 lote
- `digits = 2`, `point = 0.01`

Isso significa que o ouro é **mais flexível que forex** para posicionamento de stops.
Mesmo assim, manter MIN_SL_METAL=1200 ticks ($12.00) por consistência com backtest.

## ☠️ STOPLEVEL Pitfall — SL ignorado pelo broker (26/05/2026)

**SINTOMA:** Ordens executadas, mas perdas 5-14x maiores que o SL configurado.
**CAUSA:** IC Markets STOPLEVEL ≈ 8-10 pips. SL < STOPLEVEL é rejeitado silenciosamente.
**FIX:** `MIN_SL_PIPS = 15` no bot + validação no EA (`SYMBOL_TRADE_STOPS_LEVEL`).
Ver: **[references/mt5-stoplevel-pitfall.md](references/mt5-stoplevel-pitfall.md)**.

## 📊 Log do Dia — 27/05/2026

**Sessão:** 10:00-11:30 UTC-3 | **Equity:** $370.20 | **Posições:** 6 abertas

### Correções Críticas
- 🔴 **AutoPilot ciclo de morte:** Balance hardcoded $400 + DD 3% = fecha tudo a cada $12 de loss. Corrigido: balance real, DD 15%, cooldown 30min
- 🟡 **154 trades/dia:** Sem limite diário. Adicionado MAX_DAILY_TRADES=20
- 🟡 **monitor_consumer.py:** `AttributeError: 'list' object has no attribute 'get'` — corrigido isinstance check
- 🟡 **brain_browser CDP :9223 → :9222:** Porta headless offline, migrado para Brave real

### Infraestrutura
- ✅ NEO agente neural autônomo ativo (systemd, Ollama llama3.2:3b)
- ✅ 6 cron jobs LLM migrados DeepSeek→Ollama (zero custo API)
- ✅ Brain Gateway processou 10 mensagens pendentes
- ✅ NN Engine: backprop ajustou 27 neurônios

## 📊 Log do Dia — 26/05/2026

**Sessão:** 18:00-23:30 UTC-3 | **Equity:** $390.69 (-2.3%) | **Trades:** 8 fechados

### Conquistas
- 🥇 **XAU/USD integrado** — backtest 59d, M30 67.1% WR, configuração completa
- ⚡ **Monitor tempo real** — polling 3s, breakeven @1R, trailing @2R, watchdog */1min
- 🔧 **EA v1.1** — `modify_position`, `entry/sl/tp` no status, compilado 0 erros
- 🛡️ **AutoPilot 2.0** — threshold por par (forex $2, metal $10), fecha concentração ≥4
- 🧬 **Sistema Límbico reativado** — 5 módulos (Amygdala, N.Accumbens, Hippocampus, Brain Research, Synapse) + NN Engine feed-forward diário + Codex age automaticamente
- 🔄 **Ciclo OODA fechado** — trade → resultado → N.Accumbens aprende → weights ajustam bot → próximo trade melhor
- 🐛 **3 bugs críticos corrigidos** — fallback duplicando ordens, AutoPilot matando ouro, SMC Fractal não calibrada

Ver: **[references/neural-ooda-loop.md](references/neural-ooda-loop.md)** — arquitetura completa do ciclo de aprendizado neural.

### Bugs Corrigidos
| Bug | Sintoma | Correção |
|-----|---------|----------|
| Fallback duplicava ordens | EA executava + mt5_direct abria segunda | Verificar `status=='ok'` ou `ticket`, não só `retcode==10009` |
| AutoPilot matava ouro | Threshold $2 fechava XAU com -$3.91 (SL era $12) | Threshold $10 para metais |
| SMC Fractal em metais | Abriu XAUUSD com SL=$36 (parâmetros forex) | E2 desabilitada para `metal=True` |

### Lições Aprendidas
1. **STOPLEVEL=0 no XAUUSD** — ouro não tem distância mínima no IC Markets
2. **Yahoo `XAUUSD=X` retorna 404** — usar `GC=F` (Gold Futures)
3. **CTrade::PositionModify** (não `PositionModify` global) para contas hedge
4. **Monitor conflita com comandos manuais** — implementar lock file (fcntl)
5. **WR enforcement bloqueia após 1 loss** — trade_log precisa de expurgo seletivo

### Estado dos Sistemas
| Sistema | Cron/Processo | Status |
|---------|--------------|--------|
| Bot Multi | ca8d82dc9fa5 */15min | ✅ |
| AutoPilot | cdbae3c13baa */5min | ✅ |
| Monitor RT | PID 653863 */3s | ✅ |
| Watchdog | fc2ef7b2b599 */1min | ✅ |
| Codex | 48425c92b336 */30min | ✅ |
| EA Bridge | v1.1 (42KB) | ✅ |

---

## 🥇 XAU/USD (Ouro) — Estudo e Integração (26/05/2026)

Backtest FVG+CRT 59 dias com GC=F (Gold Futures). Resultados:

| TF | Trades | WR | PnL ($) | PF | T/dia | SL médio |
|----|--------|-----|---------|-----|-------|----------|
| M5 | 540 | 58.0% | +37,116 | 3.08 | 9.3 | $6.7 |
| M15 | 235 | 63.4% | +21,994 | 2.80 | 4.2 | $10.0 |
| **M30** | **143** | **67.1%** | **+18,891** | **3.37** | **2.9** | **$11.8** |

### Configuração no Bot

```python
'XAUUSD': {'sym': 'GC=F', 'pip': 0.01, 'tf': '30m', 'killzone': None, 'wr': 67.1, 'metal': True}
'XAUUSD_KZ': {'sym': 'GC=F', 'pip': 0.01, 'tf': '30m', 'killzone': [0,1,2,3,4,5], 'wr': 77.0, 'metal': True}
```

- **MIN_SL_METAL = 1200** ticks ($12.00) — STOPLEVEL ouro é ~$2-3
- **min_gap = 100** ticks ($1.00) — gap mínimo para metais
- **PIP_VALUES['XAUUSD'] = 0.01** — $0.01/tick com 0.01 lote (1 oz)
- Melhor killzone: **Asia (0-5 UTC) — 77% WR**
- Volume escala automaticamente via `calculate_volume()`

### Detalhes Técnicos

- Yahoo Finance: `GC=F` (Gold Futures) — `XAUUSD=X` retorna 404
- MT5: símbolo `XAUUSD` (2 dígitos, tick=0.01, 1 lote = 100 oz)
- Correlação: **independente** (grupo XAU separado, máx 2 posições)

## ⚡ V8 Multi-Strategy — 3 Estratégias Simultâneas (26/05/2026)

**Evolução da V7:** A V7 rodava 1 estratégia (FVG+CRT) em 12 modos (6 KZ + 6 No-KZ). 
O backtest mostrou que **sem killzone** performa melhor: 393 trades, 67.9% WR, +4056p.
A V8 roda **3 estratégias distintas 24h** para diversificar fontes de sinal:

| Estratégia | Lógica | RR | Pares | TF |
|-----------|--------|-----|-------|-----|
| **E1: FVG+CRT** | Gap + CRT≥70% | 3:1 | 6 pares | M5/M15/M30 |
| **E2: SMC Fractal** | MSS + Order Block H1 | 2:1 | 6 pares | H1 |
| **E3: S/R+FVG** | FVG próximo a swing levels | 3:1 | 6 pares | M15/M30 |

**Script:** `scripts/forex_bot_multi.py` — bot multi-estratégia 24h (V8.3 — corrigido 27/05)
**Cron:** `ca8d82dc9fa5` — */15 * * * 1-5 (no_agent) — ⚠️ PAUSADO 27/05 após descoberta de overtrading. Corrigido, aguardando reativação.
**Bot antigo (V7):** `21f7caf29606` — PAUSADO (26/05, redundante com bot_multi)
**Cron jobs pausados (27/05):** Brain Signal Scanner (3ba3d2dc5e8e — fake signals), Chart Pattern Study (00529564acee + 1313292f5393 — 1.5MB dumps inúteis), Codex Forex Monitor (48425c92b336 — consumia tokens sem produzir)

### Trade Notifier — Telegram

`trade_notifier.py` envia confirmações via Telegram Bot API a cada ordem:
```bash
python3 scripts/trade_notifier.py open EURUSD BUY 1.1625 1.1615 1.1655 FVG+CRT KZ
python3 scripts/trade_notifier.py close EURUSD BUY 1.1625 1.1640 +15.0p WIN FVG+CRT
python3 scripts/trade_notifier.py summary "3 ordens abertas, PnL: +25p"
```
Integrado no `forex_bot_multi.py` — chamado após cada `send_order` bem-sucedido.
Token em `~/.hermes/.env` (`TELEGRAM_BOT_TOKEN`). Chat ID em `TELEGRAM_HOME_CHANNEL`.

### Config Final do Bot Multi-Strategy

```python
STRATEGIES = {
    'E1_FVG_CRT':     {'rr': 3.0, 'min_gap_pips': 2.0, 'crt_percentile': 0.7},
    'E2_SMC_FRACTAL': {'rr': 2.0, 'min_swing_pips': 8, 'min_gap_pips': 3.0},  # 27/05: min_swing 5→8, gap≥3p
    'E3_SR_FVG':      {'rr': 3.0, 'min_gap_pips': 3.0, 'sr_proximity_pips': 5},
}
BASE_PAIRS = {
    'USDJPY': {'tf': '5m',  'wr': 66.1},
    'GBPJPY': {'tf': '15m', 'wr': 67.6},
    'USDCAD': {'tf': '15m', 'wr': 90.0},
    'EURJPY': {'tf': '30m', 'wr': 64.9},
    'GBPUSD': {'tf': '30m', 'wr': 62.2},
    'EURUSD': {'tf': '30m', 'wr': 73.8},
}
# 3 estratégias × 6 pares = 18 combinações escaneadas a cada 15 min
# MAX_POSITIONS: 4 (reduzido 8→4 27/05 — $400 conta, 2% risco = 4 posições máx)
# MIN_WR_REAL: 55% (50→55% 27/05 — coin flip <55% tem expectância negativa com RR 2:1-3:1)
# MAX_CORRELATED_PAIRS: 2 (evita sobre-exposição JPY/USD)
# WR Enforcement: should_trade_pair() bloqueia pares com WR real < 55%
# Anti-duplicata: open_symbols do MT5 verificados antes de cada trade (27/05)
# Signal age filter: sinais >MAX_SIGNAL_AGE candles descartados (27/05)
# Killzone universal: 18-23h UTC bloqueado (WR 0-37%), 0-6h requer CRT=0.85 (27/05)
# Circuit breaker: DAILY_STOP_PERCENT=5% para o bot (antes só alertava) (27/05)
# Concentração: conta posições EXISTENTES no MT5 + novas, máx 2 por grupo
```

### Filtro de Correlação

O bot limita pares correlacionados simultâneos:
- **Grupo JPY**: USDJPY, GBPJPY, EURJPY → máx 2 abertos
- **Grupo USD**: GBPUSD, EURUSD, USDCAD → máx 2 abertos

### Prioridade de Sinais

Sinais ordenados por `gap × WR/100` (maior gap com melhor WR histórico primeiro).

## ⚡ V7 Final — Melhor TF por Par + KZ vs No-KZ (26/05/2026)

**Evolução da sessão 26/05:**
1. CHoCH+FVG M15 (3 pares) → 1 trade/mês ❌
2. FVG puro + CRT (6 pares) → 776 trades/59d ✅
3. Triple-TF (M5+M15+M30) → 1677 trades, WR ~57% ✅
4. **Melhor TF por par** → 393 trades, **67.9% WR**, +1.72R 🏆
5. **KZ vs No-KZ paralelo** → comparando qualidade vs volume em tempo real

### Config Final do Bot (12 entradas)

```python
PAIRS = {
    # ── COM Killzone (qualidade) ──
    'USD/JPY_KZ':  {tf:'5m',  killzone:[15,16], wr:66.1},
    'GBP/JPY_KZ':  {tf:'15m', killzone:[6,7],   wr:67.6},
    'USDCAD_KZ':   {tf:'15m', killzone:[15,16], wr:90.0},
    'EUR/JPY_KZ':  {tf:'30m', killzone:[11,15], wr:64.9},
    'GBP/USD_KZ':  {tf:'30m', killzone:[15,16], wr:62.2},
    'EUR/USD_KZ':  {tf:'30m', killzone:[15,16], wr:73.8},
    # ── SEM Killzone (24h, volume) ──
    'USD/JPY':     {tf:'5m',  killzone:None,    wr:66.1},
    'GBP/JPY':     {tf:'15m', killzone:None,    wr:67.6},
    'USDCAD':      {tf:'15m', killzone:None,    wr:90.0},
    'EUR/JPY':     {tf:'30m', killzone:None,    wr:64.9},
    'GBP/USD':     {tf:'30m', killzone:None,    wr:62.2},
    'EUR/USD':     {tf:'30m', killzone:None,    wr:73.8},
}
```

### Resultado Backtest 59d (Melhor TF por par, SEM killzone)

| Par | TF | Trades | WR | PnL | T/dia |
|-----|-----|--------|-----|------|-------|
| USD/JPY | M5 | 127 | 66.1% | +1141p | 10.8 |
| GBP/JPY | M15 | 74 | 67.6% | +787p | 6.3 |
| USDCAD | M15 | 20 | 90.0% | +206p | 1.7 |
| EUR/JPY | M30 | 37 | 64.9% | +310p | 3.1 |
| GBP/USD | M30 | 74 | 62.2% | +848p | 6.3 |
| EUR/USD | M30 | 61 | 73.8% | +764p | 5.2 |
| **TOTAL** | | **393** | **67.9%** | **+4056p** | **33.3** |

**Expectância: +1.72R/trade | ~147 trades/mês**

### Lições da Sessão

- ❌ CHoCH = 1 trade/mês. Removido.
- ❌ M10 não existe no Yahoo Finance (intervalos: 1m,2m,5m,15m,30m,60m)
- ❌ Rodar todos os TFs em todos os pares é ineficiente
- ✅ FVG puro + CRT é o filtro suficiente — killzone é opcional
- ✅ Cada par tem UM melhor TF — mapear isso sobe WR de 57% → 67.9%
- ✅ 60 dias é o limite do Yahoo pra 15m (59 dias funciona, 60 falha)
- ✅ M30 cobre 97.6% dos dias úteis com trades

## Execução Pesada Delegada ao Codex (26/05/2026)

Backtests, SMC fractal scans e análises multi-TF eram delegados ao Codex CLI (GPT-5.5/OpenAI), mas o sandbox Codex não resolve Yahoo Finance DNS e não escreve em `forex/codex_output/`.

**Corrigido (27/05):** Backtests agora rodam LOCALMENTE (sem sandbox). Yahoo Finance funciona. Script `codex_daily_backtests.sh` executa 3 backtests: CRT+CHoCH, Killzones, Chart Pattern Consolidation. Cron: `20620209b959` (no_agent, 10h dias úteis). Resultados em `forex/codex_output/`. Codex Forex Monitor (`48425c92b336`) pausado — consumia tokens sem produzir ações.

Ver: **[references/pipeline-cleanup-2026-05-27.md](references/pipeline-cleanup-2026-05-27.md)** e **[references/v8.3-overtrading-fixes-2026-05-27.md](references/v8.3-overtrading-fixes-2026-05-27.md)**.

## ICT Killzone Strategy — H1→M5→M1 Fractal (26/05/2026)

Metodologia ICT com análise fractal multi-timeframe. Absorvida de Roberto.
Guia completo: **[forex/ict_killzone_h1_m5_m1.md](forex/ict_killzone_h1_m5_m1.md)**.
Detector de liquidez: **[scripts/ict_killzone_detector.py](scripts/ict_killzone_detector.py)**.
Simulador: **[scripts/ict_simulation.py](scripts/ict_simulation.py)**.
Resultados: **[references/ict-simulation-results.md](references/ict-simulation-results.md)**.

**Killzones (UTC):** 🇯🇵 Asia 20-00 | 🇬🇧 London 03-06 | 🇺🇸 NY 08-11
**Pipeline:** H1 (Asia/Daily/Weekly/Monthly liquidity capture) → M5 (ChoCh c/ deslocamento + premium/discount) → M1 (POI OB/FVG >50% + ChoCh fractal → ENTRADA)
**Gestão:** SL topo do ChoCh M1, TP 3:1. SL >15p → skip.
**Regra de ouro:** Entrada é POR TOMADA DE LIQUIDEZ. NUNCA antes do rompimento + ChoCh.

**Resultados simulação (10 dias):**
- GBPJPY: 4W/3L **57.1% WR +54.6p** ✅ Viável
- EURJPY: 3W/5L 37.5% WR +18.3p ⚠️ Marginal
- USDCAD: 0W/4L 0% WR ❌ Não funciona com ICT

## Análise de Volatilidade Multi-Timeframe (26/05/2026)

Metodologia para rankear pares por volatilidade real em cada cruzamento de mercado
(Asia+London, London+NY, London Close, NY Open) × 4 timeframes (M5, M15, M30, H1).
GBPJPY é #1 em 16/16 cenários. London Close consistentemente o pico.
Ver: **[references/multi-tf-volatility-analysis.md](references/multi-tf-volatility-analysis.md)**.

## SMC Fractal — Metodologia Dinei (absorvido 26/05/2026)

Análise institucional baseada em Smart Money Concepts com leitura fractal de timeframes.
Fractal de timeframe maior vira range 2 TFs abaixo. Pivôs validados com 5+1 candles.
Pipeline: Semanal→Diário/H4→H1/M15→M5/M1. MSS = liquidez + retorno.
Ver: **[references/smc-fractal-dinei.md](references/smc-fractal-dinei.md)**.

## V5 — Macro Validation + Weekly Bias (25/05/2026)

O bot agora integra validação macro de 3 camadas (`macro_validation_score`) e viés semanal.

### Strategy v4-crt-sr (atualizado 25/05 noite)

`brain_signal_generator.py` atualizado com:
- `sr_required: True` — Support/Resistance filter (100% WR quando combinado com CRT em backtest manual)
- `active_hours_utc: [6, 7, 11, 15, 16]` — Adicionado London Close (UTC 11)
- `strategy_version: "v4-crt-sr"`
- Backtest V4-V5 completo: **[references/backtest-v4-v5-2026-05-25.md](references/backtest-v4-v5-2026-05-25.md)**

⚠️ S/R filter ainda é manual (validação visual do agente). Automação pendente (swing highs/lows).
   **NOVO (26/05):** SMC Fractal do Dinei absorvido — pivôs validados com 5+1 (ta.pivothigh/low),
   MSS não exige rompimento de topo, OB = extremo do trecho anterior. Ver:
   **[references/smc-fractal-dinei.md](references/smc-fractal-dinei.md)**.
   ICT Concepts LuxAlgo Pine Script disponível em `forex/ict_concepts_luxalgo.pine` (1143 linhas).

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

## Regras (V8.3 — 27/05/2026)

- **Estrategia:** 3 estratégias simultâneas: E1=FVG+CRT (RR 3:1), E2=SMC Fractal H1 (RR 2:1, min_swing=8p, gap≥3p), E3=S/R+FVG (RR 3:1)
- **Pares:** 6 pares (USDJPY M5, GBPJPY+USDCAD M15, EURJPY+GBPUSD+EURUSD M30)
- **MAX_POSITIONS:** 4 (reduzido 8→4 — $400 conta)
- **MIN_WR_REAL:** 55% (coin flip <55% tem expectância negativa)
- **MAX_CORRELATED_PAIRS:** 2
- **Anti-duplicata:** Verifica `open_symbols` do MT5 antes de cada trade
- **Signal age filter:** Sinais >MAX_SIGNAL_AGE candles são descartados
- **Killzone universal:** 18-23h UTC BLOQUEADO (WR 0-37%). 0-6h UTC requer CRT=0.85
- **Circuit breaker:** DAILY_STOP_PERCENT=5% PARA o bot (antes só alertava)
- **CHoCH:** NÃO usar (removido V7)
- **BOS:** NUNCA usar como entrada (0-12% WR)
- **CRT:** Obrigatório para E1 e E3. E2 exige gap≥3p + signal age filter

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


## SMC Fractal — Metodologia Dinei (absorvido 26/05/2026)

Metodologia completa de Smart Money Concepts absorvida do chat export Dinei + Lucas (04-11/05/2026).

### Princípio Fractal

O fractal de um timeframe maior vira o range do timeframe 2 tempos abaixo.
1 tempo abaixo mostra apenas o CHOCH inicial, não o range completo.

```
Mensal → Semanal (CHOCH) → Diário (fractal=range) → H4 → H1 → M15/M5
```

### Pivôs (5+1)

Validados com `ta.pivothigh(high, 5, 1)` / `ta.pivotlow(low, 5, 1)`:
- 5 candles atrás: o pivô tomou liquidez de 5 candles anteriores
- 1 candle à frente: confirma que não foi violado imediatamente

### MSS (Market Structure Shift)

NÃO exige rompimento de topo/fundo oposto. Basta:
1. Preço faz perna de alta/baixa
2. Toma liquidez do extremo anterior
3. Retorna → já é considerado mudança de estrutura (LuxAlgo)

### Order Blocks

Extremo do trecho ANTERIOR ao rompimento (não é "última vela contrária"):
- OB bullish: menor low do trecho antes do rompimento de alta
- OB bearish: maior high do trecho antes do rompimento de baixa

### Scripts

- `scripts/smc_fractal_detector.py` — Detector completo: swings, MSS, FVGs, OB, liquidez
- `forex/smc_fractal_dinei.md` — Metodologia completa documentada
- `forex/ict_concepts_luxalgo.pine` — Indicador Pine Script v5 (1143 linhas)

### Fontes

- **ForexFactory Calendar**: https://www.forexfactory.com/calendar (sem bloqueio, DOM query via CDP)
- **ICT Concepts LuxAlgo**: indicador Pine Script com MSS, BOS, FVG, OB, Liquidez, Killzones
- **Investing.com**: ❌ Bloqueado por Cloudflare — NÃO usar
- **TradingEconomics**: ❌ Bloqueado (HTTP 403) — NÃO usar

### Uso

```bash
python3 scripts/smc_fractal_detector.py                          # EURUSD M15
python3 scripts/smc_fractal_detector.py --pair GBPUSD --tf 1h   # GBPUSD H1
python3 scripts/smc_fractal_detector.py --json                   # JSON para bot
```

Ver referência completa: [references/smc-fractal-dinei.md](references/smc-fractal-dinei.md)

## ⚠️ Diagnóstico Rápido: Bot não abre ordens (26/05/2026)

Quando o bot não está abrindo ordens, verifique nesta ordem:

## ☠️ PITFALL: Bot sem limite diário = 154 trades/dia (27/05/2026)

**SintoMA:** 154 ordens em uma manhã. AutoPilot fecha, bot reabre, ciclo vicioso.
**Causa:** Sem `MAX_DAILY_TRADES`. Cada tick */15min abre 5+ ordens.
**Correção:** `MAX_DAILY_TRADES = 20` — lê `trade_log.json`, conta trades do dia, bloqueia scan se atingido.

```python
today = datetime.now().strftime('%Y-%m-%d')
trades_hoje = sum(1 for t in tlog_data.get('trades', []) 
                  if str(t.get('timestamp', '')).startswith(today))
if trades_hoje >= MAX_DAILY_TRADES:
    return  # ⛔ para scan
```

## ☠️ PITFALL: AutoPilot fecha tudo em ciclo de morte (27/05/2026)

**Sintoma:** Ordens abrem e fecham em sequência. 154 trades/dia. Nenhuma bate TP.
**Causa:** AutoPilot com balance hardcoded $400 e drawdown threshold 3% ($12). Qualquer loss >$12 fecha TODAS posições. Bot reabre no próximo tick. Ciclo vicioso.
**Correção:**
1. AutoPilot lê balance real do MT5, não $400 fixo
2. Drawdown threshold: 3% → 15%
3. Cooldown 30min após close_all
4. Bot: MAX_DAILY_TRADES = 20
**Ver também:** `references/v8.2-autopilot-cycle-of-death.md`

### 1. WR Enforcement bloqueando
**Sintoma:** logs com `[WR] <par>: WR agregado=X% — só pares com WR≥50% — pulando`
**Causa:** `trade_log.json` tem trades antigos de estratégias/pares que já não são usados.
**Solução:** Resetar `trade_log.json` se a estratégia mudou:
```bash
echo '{"trades": [], "daily": {}}' > ~/.hermes/forex/trade_log.json
```

### 2. Balance desatualizado limitando SL
**Sintoma:** logs com `[RISK] <par> SL=Xp > max=0.Xp — pulando`
**Causa:** `real_daily_state.json` tem balance defasado (ex: $85 após dia de losses).
**Solução:** Atualizar com balance real do MT5:
```bash
python3 ~/.hermes/scripts/hermes_mt5_bridge.py status  # pega balance real
# Editar ~/.hermes/forex/real_daily_state.json com o balance correto
```

### 3. MT5/EA Bridge offline
**Sintoma:** `pgrep terminal64` não retorna nada, ou `hermes_mt5_bridge.py status` dá timeout.
**Verificações:**
```bash
pgrep -a terminal64                    # MT5 rodando?
python3 ~/.hermes/scripts/hermes_mt5_bridge.py status  # EA respondendo?
```
**Se MT5 foi reiniciado:** O EA `hermes_bridge` é removido do chart. Precisa:
1. Ctrl+N → Expert Advisors → arrastar `hermes_bridge` para um chart
2. Verificar AutoTrading ligado (botão verde na toolbar)

### 4. `calculate_max_risk_sl` bug para pares JPY
**Sintoma:** `max_sl_pips` muito baixo (<1p) para GBPJPY, EURJPY, USDJPY.
**Causa:** `pip_dollar = volume * 100000 * pip_val` assume $10/pip para JPY, mas o real é ~$0.07.
**Workaround:** Aumentar `RISK_PERCENT` ou corrigir o cálculo para pares JPY (dividir por ~130-150).

## Bugs Corrigidos (20/05/2026)

1. **☠️ FVG INDEX BUG:** `detect_choch_fvg` usava `df.iloc[j]` com índices do slice `df['High'].values[-30:]` (0-29) no DataFrame completo (388+ velas). FVG era buscado em velas de 5 dias atrás, não nas últimas 30. Fix: `df30 = df.iloc[-30:]` + `df30.iloc[j]`. Sinais agora são detectados corretamente nas últimas 30 velas.

2. **☠️ DEDUP SILENCIOSO:** `except: traded_today=[]` engolia erros de leitura do JSON. Se arquivo corrompido/travado, dedup bypassava e abria trades duplicados. Fix: log do erro + fallback via `real_state.json` + filtro `status != 'duplicate'`.

3. **✅ P&L TRACKING:** Adicionado `check_positions()` — a cada ciclo verifica SL/TP via preço atual (yahoo 5m). Trades fechados atualizam `trade_log.json` com `pnl`/`exit_price`/`result`.

## 🩺 Bot Troubleshooting — Quando o bot não abre ordens (26/05/2026)

Checklist sistemática para diagnosticar por que o `forex_bot_real.py` não está abrindo ordens no MT5:

### 1. Verificar MT5 rodando
```bash
pgrep -a terminal64  # Deve mostrar "MetaTrader 5 IC Markets Global"
```
Se não rodando → usuário precisa reiniciar o MT5 no desktop Wayland.

### 2. Verificar EA Bridge
```bash
python3 ~/.hermes/scripts/hermes_mt5_bridge.py status
```
Se timeout → EA pode ter sido removido do chart ou AutoTrading desligado. Verificar:
- AutoTrading ligado (botão verde na toolbar)
- EA `hermes_bridge` em algum chart (Ctrl+N → arrastar)
- MT5 não crashou (ver logs em `~/.wine/.../logs/`)

### 3. Verificar CDP browser (:9223)
```bash
curl -s http://localhost:9223/json/version | python3 -c "import sys,json; print(json.load(sys.stdin).get('Browser','OFFLINE'))"
```
Se offline → `brain_signal_generator.py` falha, mas o bot ainda funciona com yfinance.
Para iniciar:
```bash
DISPLAY=:0 brave-browser --remote-debugging-port=9223 --headless=new --no-first-run --user-data-dir=~/.config/brave-headless &
```

### 4. Verificar bloqueios no bot (logs do cron)
```bash
cat ~/.hermes/cron/output/21f7caf29606/$(ls -t ~/.hermes/cron/output/21f7caf29606/ | head -1)
```
Padrões de bloqueio:
- `[WR] ... pulando` → WR enforcement bloqueando (ver item 4a)
- `[RISK] ... SL=X.Xp > max=Y.Yp — pulando` → Balance stale (ver item 4b)
- `[MACRO] ... REJEITADO` → Fora de killzone ou contra viés semanal
- `[LIMIT] ... sem novas entradas` → MAX_POSITIONS atingido
- Nenhum output → sem sinais detectados (normal na Ásia, verificar volatilidade)

### 4a. ☠️ PITFALL: trade_log contaminado por estratégia antiga
Quando a estratégia muda (pares diferentes, regras diferentes), o `trade_log.json` contém trades de pares antigos (ex: AUD/USD, NZD/USD) que puxam o WR agregado para baixo. O `should_trade_pair()` bloqueia pares com WR agregado < 35%.

**Solução:** Resetar o trade_log quando a estratégia mudar fundamentalmente:
```bash
cp ~/.hermes/forex/trade_log.json ~/.hermes/forex/trade_log_backup_$(date +%Y%m%d).json
echo '{"trades": [], "daily": {}}' > ~/.hermes/forex/trade_log.json
```

### 4b. ☠️ PITFALL: real_daily_state.json com balance stale
O `get_balance()` lê `real_daily_state.json`. Se o arquivo tem um balance antigo e baixo (ex: $85 de um dia de loss), `calculate_max_risk_sl()` calcula um SL máximo minúsculo (ex: 0.1 pips) e bloqueia todas as entradas.

**Solução:** Atualizar com o balance real do MT5:
```bash
# Obter balance do EA bridge
python3 ~/.hermes/scripts/hermes_mt5_bridge.py status  # anotar o balance

# Atualizar real_daily_state.json
cat > ~/.hermes/forex/real_daily_state.json << EOF
{
  "date": "$(date +%Y-%m-%d)",
  "balance": <BALANCE_REAL>,
  "pnl_today": 0,
  "updated": "$(date -Iseconds)"
}
EOF
```

### 5. Verificar retcode do MT5
Se o bot tentou abrir ordem mas crashou com `RuntimeError: OrderSend failed (retcode=XXXX)`:
- **10016** = Invalid stops — SL/TP inválidos (muito longe do preço, ou invertidos)
- **10027** = AutoTrading disabled — botão verde na toolbar desligado
- **10030** = Unsupported filling mode — IC Markets Netting requer `ORDER_FILLING_IOC`

### 6. Verificar logs do MT5 (diagnóstico de crash)
```bash
# Log está em UTF-16LE, usar strings para extrair
strings ~/.wine/drive_c/Program\ Files/MetaTrader\ 5\ IC\ Markets\ Global/logs/$(date +%Y%m%d).log | tail -30
```
Procure por: `failed market`, `Invalid stops`, `connection lost`, `authorized on`, `trading has been enabled`.

## ⚠️ Bot Debugging Playbook (26/05/2026)

Quando o bot para de abrir ordens, verificar em ordem:

### 1. WR Enforcement bloqueando?
```bash
# Ver output do cron
cat ~/.hermes/cron/output/21f7caf29606/*.md | grep "WR\|BLOCK\|pulando"
```
Se `WR agregado=33%` → trade_log contaminado com trades de estratégia antiga.
**Fix:** `echo '{"trades": [], "daily": {}}' > ~/.hermes/forex/trade_log.json`

### 2. Balance stale limitando SL?
```bash
cat ~/.hermes/forex/real_daily_state.json
```
Se `balance: 85.3` → SL máximo calculado em 0.1 pips, bloqueia tudo.
**Fix:** atualizar com balance real do MT5 (via bridge `get_status`).

### 3. MT5/EA bridge vivo?
```bash
pgrep -a terminal64          # MT5 rodando?
python3 scripts/hermes_mt5_bridge.py status  # EA respondendo?
```

### 4. EA crasha com ordens (SL/TP)?
Sintoma: `status` funciona, `send_order` com SL/TP dá timeout.
Causa: bug no EA `hermes_bridge.ex5` — não tratado. Após crash, EA precisa ser removido e recolocado no chart.
**Fix no bot:** `place_choch_order()` adaptado com fallback automático para `mt5_direct.py` (ydotool).
**Fix permanente:** recompilar EA com debug (`MetaEditor64.exe` case-sensitive no Wine, requer Xvfb :99):
```bash
cd "$HOME/.wine/drive_c/Program Files/MetaTrader 5 IC Markets Global"
rm -f MQL5/Experts/hermes_bridge.ex5
DISPLAY=:99 WINEPREFIX=~/.wine wine MetaEditor64.exe /compile:"MQL5/Experts/hermes_bridge.mq5" /log
```

### 5. `calculate_max_risk_sl` bug pares JPY
Fórmula antiga: `pip_dollar = volume * 100000 * pip_val` → GBPJPY (pip_val=0.01) = $10/pip (100x off).
**Corrigido (26/05):** `pip_dollar = volume * 10.0` (aproximação conservadora).

### 6. Conta é HEDGE (não Netting)
MT5 IC Markets demo: conta Hedge. Ordens SELL não fecham BUY automaticamente — abre posição separada.
Usar `close_all` para fechar posições.

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
- **IC Markets Demo: ✅ ATIVA — MT5 desktop Wayland (Wine), conta Hedge (Raw Trading Ltd). Execução via EA Bridge (`hermes_mt5_bridge.py` → `hermes_bridge.ex5`). Dados: tv_data.py v2 híbrido (yfinance OHLC + CDP live).**
- Exness: 🟡 cadastro preenchido, depósito $10 pendente (skill `forex-brokers`)

## ☠️ PITFALL: SL menor que STOPLEVEL → stop loss ignorado (26/05/2026)

**Este é o bug #1 que impede lucro no forex real.** Descoberto após análise forense de 7 trades com -$55 de prejuízo.

**Sintoma:** Trades perdem 5-15× mais que o SL configurado. SL=3.5p, perda real=27.6p.

**Causa raiz:** IC Markets (e a maioria dos brokers) tem STOPLEVEL mínimo (~8-10 pips para forex majors). Quando o SL é menor que esse mínimo, o OrderSend **retorna sucesso** (retcode 10009) mas os stops são **silenciosamente ignorados**. A posição abre nua, sem proteção.

**Evidência dos 7 trades (26/05):**

| Trade | SL Config | Perda Real | Violação |
|-------|-----------|------------|----------|
| GBP/USD BUY | 3.5p | -27.6p | 7.9× |
| GBP/JPY BUY | 3.0p | -14.4p | 4.8× |
| GBP/USD_KZ BUY | 3.5p | -49.4p | 14.1× |
| USD/JPY BUY | 2.6p | -3.1p | 1.2× |

**Correções aplicadas (3 camadas):**

1. **EA Bridge (.mq5):** Valida STOPLEVEL antes do OrderSend — rejeita comandos com SL < 1.5× o mínimo do broker:
   ```cpp
   long stoplevel = SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double min_distance = stoplevel * point;
   if(sl > 0 && MathAbs(price - sl) < min_distance * 1.5)
       return error("SL too close");
   ```

2. **Bot Python:** `MIN_SL_PIPS = 15` — todo SL agora é ≥15 pips, substituindo os limites anteriores de 2-10 pips:
   ```python
   'sl_pips': max(gap, MIN_SL_PIPS),  # era: min(max(gap, 2), 10)
   ```

3. **Compilar e recarregar EA:** Após recompilar o .mq5, remover e recolocar o EA no chart (MT5 não recarrega .ex5 automaticamente):
   ```bash
   cd "$HOME/.wine/drive_c/Program Files/MetaTrader 5 IC Markets Global"
   rm -f MQL5/Experts/hermes_bridge.ex5
   DISPLAY=:99 WINEPREFIX=~/.wine wine MetaEditor64.exe /compile:"MQL5/Experts/hermes_bridge.mq5" /log
   ```
   Depois: Ctrl+N → remover hermes_bridge do chart → arrastar novo hermes_bridge.

**Regra permanente:** NUNCA configurar SL menor que 15 pips em forex. Se o setup não comporta 15 pips de SL, o par não tem volatilidade suficiente para a estratégia.

## ⚠️ Pitfall: WR enforcement + concentration check ausentes na V8 (corrigido 26/05/2026)

A V8 do `forex_bot_multi.py` foi lançada **sem** as funções `get_real_wr()` e `should_trade_pair()` — o `MIN_WR_REAL = 50.0` estava definido mas nunca chamado. O filtro de concentração (`MAX_CORRELATED_PAIRS`) só contava pares NOVOS no ciclo atual, não as posições já abertas no MT5.

**Sintomas:**
- Bot abre trades mesmo com WR real de 14.3% (1W/6L)
- 4/6 posições no mesmo par (USDCAD) — concentração perigosa
- MAX_POSITIONS=6 travava o scan sem diversificar

**Correções aplicadas (26/05):**
1. `get_real_wr(pair, min_trades)` — lê `trade_log.json`, calcula WR real
2. `should_trade_pair(pair)` — bloqueia par se WR < 50% ou agregado < 35%
3. `MAX_POSITIONS: 6 → 8` (aprovado por Roberto via Neural Link)
4. Concentração agora conta posições EXISTENTES do MT5 + novas do ciclo

**Ver também:** `scripts/mindcoach_commands.py` — sistema de aprovação neural usado para autorizar o aumento de MAX_POSITIONS.

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

## Pares — Ranking V6 (6 pares, 26/05/2026)

### Ranking por WR (backtest FVG V4, 5059 padrões, 30 dias)

| Rank | Par | WR V4 | PF | Setups | Veredito |
|------|-----|-------|----|--------|----------|
| 🥇 | **USDJPY** | **73.3%** | 8.25 | 16/30d | ✅ PRIORITÁRIO |
| 🥈 | GBPUSD | **65.5%** | 5.70 | 34/30d | ✅ Primário |
| 🥉 | EURJPY | **57.0%** | — | — | ✅ London Close V4 |
| 4️⃣ | EURUSD | **56.2%** | 3.86 | 20/30d | ⚠️ Secundário |
| 🆕 | GBPJPY | pendente | — | — | 🆕 Rei volatilidade |
| 🆕 | USDCAD | pendente | — | — | 🆕 #2 London Close |

### Ranking por Volatilidade Multi-TF (26/05, 4 TFs × 4 cruzamentos)

| Rank | Par | Média | M15 | Melhor Cruzamento |
|------|-----|-------|-----|-------------------|
| 🥇 | **GBPJPY** | 17.9p/c | 12.8p/c | #1 em 16/16 cenários |
| 🥈 | EURJPY | 12.6p/c | 8.9p/c | Asia+London 9.7p/c |
| 🥉 | USDCAD | 12.4p/c | 10.9p/c | London Close 12.3p/c |
| 4️⃣ | USDJPY | 11.2p/c | 7.2p/c | London Close 9.4p/c |
| 5️⃣ | GBPUSD | 10.6p/c | 8.0p/c | London Close 9.1p/c |
| 6️⃣ | EURUSD | 7.6p/c | 6.0p/c | London Close 6.9p/c |

**GBPJPY é líder isolado** — #1 em todos os 16 cenários (4 TFs × 4 cruzamentos), sem exceção.
London Close (15-16 UTC) consistentemente o horário de pico para todos os pares.
Ver: **[references/multi-tf-volatility-analysis.md](references/multi-tf-volatility-analysis.md)**.

- ❌ AUDUSD: 45.7% WR — evitado (não forma FVGs confiáveis)
- ❌ NZDUSD: 44.3% WR — evitado

**Filtro V4 aplicado:** gap ≥ 5 pips + hora UTC ∈ [6, 7, 15, 16].
**Frequência:** ~2.3 setups/semana (70 em 90 pair-dias).
USDJPY descoberto como melhor par em 23/05 — contradiz análise anterior que descartava USD/JPY para FVG.

**Confirmação independente (24/05):** Segundo backtest com dados frescos do Yahoo Finance confirma ranking idêntico e thresholds. Ver: **[references/backtest-v4-confirmation-2026-05-24.md](references/backtest-v4-confirmation-2026-05-24.md)**.

## Fonte de Dados (Hierarquia — 27/05/2026 v3)

**REGRA: TvDatafeed (TradingView) é a fonte PRIMÁRIA de OHLC.** Yahoo Finance é fallback. NÃO usar Yahoo no cérebro.

### tvDatafeed — Dados Diretos do TradingView (27/05)
Instalado via pip: `pip install git+https://github.com/rongardF/tvdatafeed.git`
- Acesso sem login (nologin mode — dados podem ser limitados)
- Retorna DataFrame pandas com colunas: `open`, `high`, `low`, `close` (minúsculas!)
- Pares forex: `exchange='FX'`, símbolo sem prefixo (ex: `GBPJPY`)
- Ouro: `exchange='OANDA'`, símbolo `XAUUSD`
- Intervalos: `Interval.in_1_minute`, `in_5_minute`, `in_15_minute`, `in_30_minute`, `in_1_hour`, `in_4_hour`, `in_daily`
- MUITO mais dados que Yahoo: 3-6x mais FVGs detectados (ex: GBPUSD 60 FVGs vs 18)

```python
from tvDatafeed import TvDatafeed, Interval
tv = TvDatafeed()
df = tv.get_hist(symbol='GBPJPY', exchange='FX', interval=Interval.in_15_minute, n_bars=200)
```

### Pipeline de dados v3
```
TvDatafeed (TradingView OHLC — primário)
    ↓  pandas DataFrame
yfinance (fallback se TvDatafeed falhar)
    ↓
chart_renderer.py / terminal_chart.py / forex_bot_multi.py
```

Ver: **[references/tvdatafeed-integration.md](references/tvdatafeed-integration.md)**.

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
| `backtest_multi_pair.py` | Backtest FVG+CRT multi-par com killzones por par e toggle ON/OFF | Agente (manutenção) |

Ver: **[scripts/backtest_multi_pair.py](scripts/backtest_multi_pair.py)** — argparse, suporta --no-killzone, --gap, --days, --pairs.

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

### Weekly Maintenance Workflow (26/05 V7)

Toda semana, o agente deve validar o que o cérebro aprendeu e atualizar o bot:

1. **Validar descobertas**: `knowledge_bridge.py read` → filtrar acionáveis
2. **Absorver**: `knowledge_bridge.py absorb agent`
3. **Atualizar viés semanal**: editar `forex/weekly_bias.json`
4. **Rodar backtests**: `python3 scripts/backtest_multi_tf.py` (M15+M30, 6 pares FVG+CRT). Comparar com baseline: **[references/backtest-v7-2026-05-26.md](references/backtest-v7-2026-05-26.md)**.
5. **Atualizar bot**: verificar PAIRS, TIMEFRAMES, killzones no `forex_bot_real.py`. WR<40% em qualquer par/TF → remover.
6. **Verificar trade log**: WR real da conta vs backtest

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

### ⚠️ Pitfall: CDP NÃO extrai OHLC do chart (25/05/2026)

TradingView.com protege dados internos do chart via minificação pesada...

[...existing content kept...]

### ⚠️ Pitfall: Investing.com bloqueado por Cloudflare (26/05/2026)

Investing.com Economic Calendar (`https://br.investing.com/economic-calendar`) é bloqueado
por Cloudflare — acesso anônimo e CDP retornam bloqueio.

### ⚠️ Pitfall: TradingEconomics também bloqueado (26/05/2026)

TradingEconomics Calendar (`https://tradingeconomics.com/calendar`) agora retorna HTTP 403
(Access Denied) tanto via curl quanto CDP. NÃO usar mais.

### ✅ ForexFactory Calendar — FONTE PRIMÁRIA (26/05/2026)

ForexFactory (`https://www.forexfactory.com/calendar`) funciona sem bloqueios.
Extrair eventos via CDP console eval (DOM querying). Eventos de alto impacto têm
rows com estrutura: `date | time | currency | event | forecast | previous`.
Calendário mostra ~2-3 dias à frente no domingo. Quarta-sexta podem estar vazios
(publicação gradual).

### ⚠️ Pitfall: Bot sem sinais = normal na sessão asiática (25/05/2026)

CHoCH+FVG+CRT requer combinação de 3 condições:
1. **CHoCH**: Swing point quebrado (price action com momentum)
2. **FVG ≥ 5 pips**: Gap entre candles próximo ao CHoCH (4 candles)
3. **CRT**: Candle de confirmação > 80% percentil de range

Sessão asiática (UTC 0-5) tem baixa volatilidade → ATR ~2-3 pips → FVGs raros. 0 sinais é esperado.
Sinais concentram-se em London open (UTC 6-7) e NY afternoon (UTC 15-16).

## Backtest V2 — Qualidade (27/05/2026)

FVG+CRT standalone NÃO funciona como estratégia autônoma. Backtest V2 (30 dias, Gap≥10p, CRT≥85%, RR 2:1): 28 trades, 35.7% WR, +49p. Apenas USDJPY (100% WR) e EURJPY (66.7%) lucrativos. Pares PAUSED no bot: GBPJPY, USDCAD, GBPUSD, EURUSD (WR<55%). Lição: FVG precisa de filtros adicionais — multi-TF confirmation, notícias, volume.

Ver: **[references/backtest-v2-quality-2026-05-27.md](references/backtest-v2-quality-2026-05-27.md)**.

## Chart Pattern Study Pipeline (23/05/2026)

O cérebro agora estuda padrões de gráfico visualmente e algaritmicamente:

| Script | Função | Cron | Schedule | Status |
|--------|--------|------|----------|--------|
| `scripts/chart_pattern_consolidator.py` | 🆕 (27/05) Consolida dumps 1.5MB em insights: dominância por par/TF, viés, confiança | — | sob demanda | ✅ |
| `scripts/chart_pattern_study.py` | Detecção algorítmica: CHoCH, FVG, BOS, OB, liquidity levels | `005295` | 08:00 seg-sex | ⏸️ Pausado 27/05 |
| `scripts/chart_pattern_degraded.py` | Aprendizado offline: templates numéricos, similaridade cross-pattern, archetypes | `131329` | 08:30 seg-sex | ⏸️ Pausado 27/05 |
| `scripts/chart_visual_learner.py` | Visão computacional: screenshots MT5 + OCR + análise de sentimento | — | sob demanda (MT5) | ⏸️ |

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
| 🤖 Multi-Strategy REAL | ca8d82dc9fa5 | forex_bot_multi.py | */15 * * * 1-5 | ✅ Ativo (26/05) |
| 🤖 V7 Single (legado) | 21f7caf29606 | forex_bot_real.py | */15 * * * 1-5 | ⏸️ Pausado (26/05) |
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

- `~/.hermes/scripts/forex_bot_multi.py` — **🆕 V8 (26/05)** — Bot multi-estratégia: 3 estratégias × 6 pares, 24h (cron: `ca8d82dc9fa5` — */15 * * * 1-5)
- `~/.hermes/scripts/trade_notifier.py` — **🆕 (26/05)** — Notificador Telegram: confirmações de ordens abertas/fechadas/summary
- `~/.hermes/scripts/forex_bot_real.py` — Bot V7 single-strategy (PAUSADO 26/05, substituído pelo multi)
- `~/.hermes/scripts/tv_data.py` v2 — híbrido 3 camadas: yfinance OHLC + CDP live + cache (drop-in yf.Ticker)
- `~/.hermes/scripts/hermes_mt5_bridge.py` — **NOVO (25/05)** — Bridge Python→EA (JSON via Common/Files). OrderSend() nativo, sem teclado. Preferir sobre mt5_direct.py.
- `~/.hermes/scripts/mt5_direct.py` v6 — Fallback via Desktop Daemon (xdotool + ydotool). Só se EA não ativo.
- `~/.hermes/scripts/brain_browser.py` — CDP WebSocket controller (:9223 headless), navigate/eval/screenshot
- `~/.hermes/scripts/forex_quote.py` — cotação live via CDP (preço no <title>)
- `brain_signal_generator.py` — ⚠️ **PAUSADO (27/05)** — Placeholder que gerava sinais falsos (`PENDING_VALIDATION`, `price:"unknown"`, `needs_human_validation:true`). Nunca executava trades. Job `3ba3d2dc5e8e` pausado. Ver: **[references/pipeline-cleanup-2026-05-27.md](references/pipeline-cleanup-2026-05-27.md)**.
- `~/.hermes/scripts/trade_tracker.py` — registra trades em trade_log.json
- `~/.hermes/scripts/knowledge_bridge.py` — bridge de conhecimento Agent↔Brain
- `~/.hermes/scripts/smc_fractal_detector.py` — **NOVO (26/05)** — Detector SMC Fractal (metodologia Dinei): pivôs 5+1, MSS, FVGs, Order Blocks, Liquidez. Uso: `python3 smc_fractal_detector.py --pair EURUSD --tf 15m`
- `~/.hermes/forex/trade_log.json` — log de trades executados (⚠️ resetar quando estratégia mudar)
- `~/.hermes/forex/real_state.json` — estado atual: active_trades, history
- `~/.hermes/forex/real_daily_state.json` — **saldo diário** usado por `get_balance()` → `calculate_max_risk_sl()` (⚠️ atualizar se balanço stale)
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

**Status:** MT5 IC Markets Global demo funcional no **desktop Wayland/GNOME** (Wine). **Conta demo Hedge** (Raw Trading Ltd).
**Execução:** **MQL5 EA Bridge** (`hermes_bridge.ex5`) — PRIMARY. Python → JSON → EA OrderSend (sem teclado/foco). Fallback: `mt5_direct.py` v6 via Desktop Daemon (ydotool + xdotool). Ver `desktop-control` skill → `references/mql5-ea-bridge.md`.
**Dados:** `tv_data.py` v2 híbrido: yfinance (OHLC 400+ candles) + CDP (live quote) + cache local.
**Pipeline:** `forex_bot_real.py` → `tv_data.py` v2 → `detect_fvg()` → CRT → `hermes_mt5_bridge.py` → EA OrderSend.

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

# 2. Compilar — ATENÇÃO: MetaEditor64.exe é case-sensitive no Wine/Linux
MT5DIR="$HOME/.wine/drive_c/Program Files/MetaTrader 5 IC Markets Global"
cd "$MT5DIR"
DISPLAY=:99 WINEPREFIX=~/.wine wine "$MT5DIR/MetaEditor64.exe" /compile:"MQL5/Experts/hermes_bridge.mq5" /log
```

**Filling Mode:** IC Markets Hedge funciona com `ORDER_FILLING_IOC`. `ORDER_FILLING_FOK` = retcode 10030 (Unsupported filling mode).

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
- ⚠️ **EA Bridge `close_all` sempre timeout:** O comando `close_all` do `hermes_mt5_bridge.py` NÃO funciona (lê o comando, deleta arquivo, mas nunca escreve resposta). Fechar posições manualmente no MT5 (botão direito → Close Position / clicar no X).
- ⚠️ **EA Bridge trava com posição existente (Hedge):** Se já há posição aberta no par, enviar `send_order` trava o EA. Limpar com `rm -f .../Common/Files/hermes_*.json` e resetar o EA (Remove → arrastar de volta).
- ⚠️ **MT5 reiniciado = EA removido do chart:** Após fechar e reabrir o MT5, o EA `hermes_bridge` precisa ser arrastado de volta para um chart (Ctrl+N → Expert Advisors → arrastar). AutoTrading também pode desligar.
- ⚠️ **Trade log contamina WR entre estratégias:** Quando a lista de pares muda (ex: V4→V7 removeu AUD/NZD), o `trade_log.json` antigo puxa o WR agregado para baixo e bloqueia todos os pares. Resetar ao mudar de estratégia.
- ⚠️ **Balance no `real_daily_state.json` fica defasado:** Após dias de loss, o balance cai e o `calculate_max_risk_sl` reduz o SL máximo a <1 pip, bloqueando todas as entradas. Sincronizar com o balance real do MT5.
- ⚠️ **`calculate_max_risk_sl` superestima pip_dollar para pares JPY:** `pip_dollar = volume * 100000 * pip_val` assume $10/pip para GBPJPY (pip_val=0.01), mas o real é ~$0.07. Resultado: max_sl_pips fica ~60x menor que o correto. Workaround: aumentar `RISK_PERCENT` no bot ou corrigir a fórmula para dividir por ~145 para pares JPY.
- ⚠️ **MetaEditor64.exe case-sensitive no Wine/Linux:** O executável é `MetaEditor64.exe` (M e E maiúsculos). `metaeditor64.exe` (minúsculo) falha com "failed to open".
- ⚠️ **EA compilation exit code 1 = pode ser ruído do bash/Wine:** O Wine frequentemente emite warnings de terminal ("impossível definir grupo do processo do terminal") que resultam em exit code 1 mesmo com compilação bem-sucedida. **Sempre verificar `ls -l hermes_bridge.ex5`** — se o arquivo existe e tem tamanho > 20KB, a compilação foi OK independente do exit code.
- ⚠️ **EA `symbol_info` comando:** Disponível desde 26/05. Consulta STOPLEVEL, spread, tick_value de qualquer símbolo:
  ```bash
  python3 -c "import json; f=open('.../Common/Files/hermes_cmd.json','w'); f.write(json.dumps({'action':'symbol_info','symbol':'XAUUSD'}))"
  ```
  Retorna: `stoplevel_pips`, `stoplevel_dollar`, `spread_pips`, `tick_value`, `tick_size`, `vol_min/step/max`.
- Ver sessão completa de debug: **[references/ea-bridge-debug-2026-05-26.md](references/ea-bridge-debug-2026-05-26.md)**

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
