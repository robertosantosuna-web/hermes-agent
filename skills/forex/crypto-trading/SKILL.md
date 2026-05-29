---
name: crypto-trading
description: "Sistema Multi-Agente Crypto v9 — IR gate + TradingView + Binance. Backtest 7d: 75.7% WR PF 9.94. Fator mais discriminativo: Impulse Ratio ≥0.8."
version: 4.0.0
---

# Crypto Trading v9 — Sistema Completo

## Status: ATIVO 24/7 em Produção

- Binance Cross Margin: $19.70 USDT, auto_execute=true
- Feed: TradingView tvDatafeed (Binance direto, 1m/5m/15m/30m/1h/4h)
- Cron: */3 min → crypto_bot.py → signals.json → binance_executor.py
- Segurança: Circuit breaker ($5 min, $5/dia loss), OCO obrigatório, 1 trade simultâneo
- Dashboard ao vivo: comando `cripto-live` (terminal, atualiza 2s)

## Arquitetura de Agentes (validada por Replay)

| Agente | Função | WR Isolado | Peso |
|--------|--------|-----------|------|
| Tendência | Multi-TF H1→M1 gate | 27% (filtro) | 2.5x |
| Padrão | OB Fibonacci + MS | 70% (motor) | 2.0x |
| Sessão | Horário NY/Asia/London | 21% (bônus) | 0.5x |
| Fluxo | Correlação BTC | 25% (contexto) | 1.0x |
| Volatilidade | ATR + regime | N/A | 0.8x |
| **Conselho** | **Tendência+Padrão** | **79.5%** | - |

## Fatores de Influência (Testados)

| Fator | Impacto | Status |
|-------|---------|--------|
| **Impulse Ratio ≥0.8** | **+8.6pp WR** | ✅ GATE (melhor fator) |
| Market Structure | Gate primário | ✅ |
| OB + Fibonacci | Motor | ✅ |
| Multi-TF | Bônus | ✅ |
| **Quality Score** | **+2.7pp (inútil)** | ⚠️ Não usar como gate |
| **Confiança** | **0pp (zero discriminação)** | ❌ NUNCA usar |
| **Fear & Greed** | **-11pp WR** | ❌ NÃO usar |
| BTC Dominance | Neutro | ⚠️ Contexto |
| Correlação USD | 85% sinc | ✅ Max 1 trade |
| Volume/Wick/S/R | Bônus score | ✅ |

### Impulse Ratio — Descoberta v9

O **Impulse Ratio** (força do impulso ÷ ATR) é o fator MAIS discriminativo já encontrado:

| IR Threshold | Trades | WR | Δ |
|-------------|--------|-----|---|
| sem filtro | 222 | 67.1% | baseline |
| IR ≥ 0.5 | 161 | 68.9% | +1.8pp |
| **IR ≥ 0.8** | **86** | **73.3%** | **+6.1pp** |
| IR ≥ 1.0 | 60 | 75.0% | +7.9pp |
| IR ≥ 1.5 | 24 | 83.3% | +16.2pp |

**Implementação v9**: IR ≥ 0.8 como GATE no CryptoConfluencia.analyze(). Não é bônus — é requisito.

**Pré-análise semanal NÃO se aplica à crypto** (ver `references/crypto-factors-analysis.md`).
**Especialização por mercado**: ver `references/per-market-specialization.md`.
**Impulse Ratio**: ver `references/discrimination-analysis.md` — fator mais discriminativo.
**Scalper Mode**: ver `references/scalper-mode.md` — operar sem tendência com IR>=1.0.
**1000 velas**: ver `references/1000-candles-lesson.md` — mínimo para H1 funcionar.
**Binance Spot**: ver `references/binance-spot-limitation.md` — não permite short, use Margin.
**Binance API**: ver `references/binance-api-pitfalls.md` — base_url, precisão, margin flow.
**Telegram**: ver `references/telegram-notifications.md` — notificações enxutas.
**Fatores que NÃO funcionam**: ver `references/crypto-factors-analysis.md` — Fear & Greed, BTC Dominance.

## Regras de Ouro (Data-Driven)

1. **Impulse Ratio ≥ 0.8 = GATE obrigatório** (fator mais discriminativo: +8.6pp WR)
2. **M5 é BÔNUS, não gate** — bloquear por M5 reduz trades sem melhorar WR
3. **1000 velas M1 mínimo** — 200 velas = só 3 candles H1, insuficiente
4. **Fibonacci 0.5-0.618 + Market Structure = GATEs** (BEARISH 79.4% > BULLISH 64.4%)
5. RANGE permitido com IR ≥ 1.0 (scalper mode)
6. Confiança NÃO discrimina (0 poder) — nunca usar como gate
7. Quality Score NÃO discrimina (+2.7pp) — não usar como gate
8. Novos fatores = BÔNUS de score (volume, wick, S/R diário)
9. Anti-correlação USD: 85% sincronia → máximo 1 trade simultâneo
10. Spot não permite SELL — precisa Margin/Futures para short

## Backtests

| Período | Timeframe | Trades | WR | PF | +R | Notas |
|---------|-----------|--------|-----|-----|-----|-------|
| 7d M1 | yfinance | 70 | **75.7%** | 9.94 | +143 | v9 IR≥0.8 gate |
| 7d M1 | yfinance | 222 | 67.1% | 6.21 | +377 | v8 sem IR gate |
| 60d M5 | yfinance | 1493 | 62.4% | 4.98 | +2235 | - |
| 100d H1 | TradingView | 695 | 88.5% | - | +1765 | OB simples |

## Pares

BTCUSD (89.8% WR), ETHUSD (85.9%), DOGEUSD (88.5%), BNBUSD (89.7%)
Removidos: SOLUSD, XRPUSD, ADAUSD (redundantes/baixa performance)

## Binance API — Pitfalls e Correções

### base_url
A Binance tem DOIS caminhos de API sob o mesmo domínio:
- `https://api.binance.com/api/v3/*` — Spot (v3)
- `https://api.binance.com/sapi/v1/*` — Margin, Wallet, Earn (sapi)

**NUNCA** usar `base_url = 'https://api.binance.com/api'` — isso quebra todos os endpoints sapi (viram `/api/sapi/...` → 404).
**SEMPRE** usar `base_url = 'https://api.binance.com'` e prefixar v3 com `/api/v3/` e sapi com `/sapi/v1/`.

### Precisão de quantidades (step_size)
`round(quantity / step) * step` produz artifacts de floating point (ex: `0.00026000000000000003`).
A Binance rejeita com `Precision is over the maximum defined for this asset`.
**Fix**: `step_str = f'{step:.10f}'.rstrip('0')` → extrai número de decimais → `round(quantity, decimals)`.
SEMPRE passar quantity como string na chamada da API.

### Precisão de preços OCO (tick_size)
Preços com decimais extras causam `PRICE_FILTER` error no endpoint OCO.
**Fix**: `round_to_tick(price, 0.01)` antes de montar OCO. Tick size padrão: 0.01 para BTCUSDT/ETHUSDT.

### Margin — Fluxo para Short
Short via Cross Margin requer 3 passos:
1. `POST /sapi/v1/margin/loan` — emprestar o ativo (asset=BTC, amount=str(qty))
2. `POST /sapi/v1/margin/order` — vender a mercado (side=SELL, type=MARKET)
3. `POST /sapi/v1/margin/order/oco` — OCO de recompra (side=BUY, sideEffectType=AUTO_REPAY)

O base_asset se extrai do symbol: `symbol.replace('USDT', '')`.

### Margin — Fluxo para BUY
Quando o saldo está em Margin (não Spot), usar endpoints sapi:
1. `POST /sapi/v1/margin/order` — comprar (side=BUY, type=MARKET, quoteOrderQty=str(amount))
2. `POST /sapi/v1/margin/order/oco` — OCO de venda (side=SELL)

Spot `/api/v3/order` NÃO funciona com saldo em Margin → `Account has insufficient balance`.

### Saldo combinado
Verificar SEMPRE Spot + Margin: `get_balance('USDT') + _get_margin_balance('USDT')`.
Após transferência Spot→Margin, Spot fica zerado.

### Script cron
`crypto_autopilot.sh` deve terminar com `exit 0` explícito — o último condicional `[ $(wc -l) -gt 1000 ]` retorna 1 quando falso, causando falso erro no cron.
Ver: `references/binance-api-pitfalls.md`

## Comandos

```bash
# Dashboard ao vivo
cripto-live          # Tela rica (Rich): posição, OCO, P&L, saldo, margin level

# Scanner ao vivo
cd ~/.hermes/crypto && python3 crypto_bot.py

# Executor (ordens Binance)
python3 binance_executor.py

# Replay por agente (validar assertividade individual)
python3 replay_por_agente.py --pair BTCUSD --days 2

# Backtest 7d
python3 validate_crypto.py

# Backtest 60d  
python3 validate_crypto_long.py

# Backtest unificado (forex + crypto)
python3 backtest_unificado.py

# Feed TradingView
python3 tradingview_feed.py
```

## Referências Cruzadas

- Pré-análise semanal (Forex): ver skill `forex-choch-m15` → `references/weekly-pre-analysis.md`
- Arquitetura por agente: ver `references/agent-architecture-insights.md`

## Diagnóstico e Health Check

Verificar se tudo está operacional (`references/operational-health-check.md`):

```bash
# 1. Bot está gerando sinais?
cd ~/.hermes/crypto && python3 crypto_bot.py

# 2. Tem trade fantasma bloqueando?
cat open_trades.json  # se tem trade mas Binance não, limpar com echo '[]' > open_trades.json

# 3. Margin está ativo? (404 = NÃO)
curl -s -H "X-MBX-APIKEY: $BINANCE_KEY" "https://api.binance.com/sapi/v1/margin/account?timestamp=...&signature=..."

# 4. Executor consegue importar?
python3 -c "from binance_trader import BinanceTrader; print('OK')"

# 5. Cron status
cronjob action=list (ver job "Crypto AutoPilot 24/7" — last_status deve ser "ok")
```

## Pitfalls Comuns

1. **Trade fantasma** — `open_trades.json` tem trade que nunca executou na Binance (SyntaxError, API 404, etc). O `pair_selector` vê MAX_TOTAL_TRADES=1 atingido e não gera novos sinais. Solução: `echo '[]' > open_trades.json`
2. **SyntaxError silencioso** — `binance_trader.py` com try/except órfão impede import. O cron roda `crypto_bot.py` (não importa `binance_trader`) então gera sinais, mas o executor falha. Verificar com `python3 -c "from binance_trader import BinanceTrader"`
3. **Cron reporta erro mas script OK** — bash script sem `exit 0` explícito herda exit code do último condicional (`[ cond ] -gt N` retorna 1 quando falso). Sempre terminar scripts de cron com `exit 0`.
4. **Margin 404** — Cross Margin não ativado na conta. Só ativa pelo site Binance (Carteira → Margin). API não tem endpoint de ativação. Sem Margin, Spot-only → só executa BUY, ignora SELL.
5. **Símbolo yfinance vs Binance** — yfinance usa `BTC-USD`, Binance usa `BTCUSDT`. O `pair_selector` mapeia via `CORREL_GROUPS`. Não usar símbolo yfinance diretamente na API Binance.

## Data Feed

TradingView tvDatafeed (subprocess no venv): ~/.hermes/hermes-agent/venv/bin/python
Modo nologin: ~4000 velas M1 (~2.7 dias) ou 5000 velas M15 (~52 dias)
Cache 30s anti rate-limit. Yahoo Finance para daily bias.