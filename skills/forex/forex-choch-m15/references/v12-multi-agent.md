# V12 — Multi-Agente + Self-Learning (29/05/2026)

## Pipeline

```
1. Multi-TF Bias (W/D/H4 PDH/PDL) → maioria define BUY/SELL
2. 5 Agentes votam: Perfil + Sessão + Estrutura + Padrão + Confluência
3. M1 FVG na direção do bias com scoring premium/discount
4. SL = 2× ATR(14), clamp 10-30p (dinâmico)
5. RR 3:1 fixo (NUNCA reduzir)
6. 2R breakeven + 3R trail
7. Self-learning ajusta pesos por resultado
```

## Agentes (multi_agent.py)

| Agente | Função | Peso |
|--------|--------|------|
| PERFIL | Par por sessão (Asia/London/NY) | 1.0 |
| SESSÃO | Ásia como preditora de London | 1.0 |
| ESTRUTURA | CRT + Order Block + Swings | 1.5x |
| PADRÃO | FVG scoring premium/discount | 1.2x |
| CONFLUÊNCIA | Maioria decide, confiança ≥30% | — |

## Regras de Timeframe

- M15: mínimo para ATR e CRT (estrutura/confirmação)
- Abaixo de M15: apenas entrada
- M1: entrada com FVG
- H1: CRT candle + sweep

## CRT — Regra de Uso

- CRT é filtro, NÃO substituto do bias
- CRT alinhado com bias = sinal premium
- Conhecimento do vídeo SOMA, não substitui

## Backtest Validado

- 21 dias, 7 pares: 110 trades, 62% WR, +162R, PF 4.86
- 5 pares otimizados: 62 trades, 63% WR, +94R, PF 5.09
- Melhor par: XAUUSD (83% WR)
- Simulação $100: BT1 (7 pares) +124% vs BT2 (5 pares) +60%

## Arquivos do Sistema

- `forex_bot_multi.py` — scan multi-agente (substituiu modelo dual)
- `multi_agent.py` — 5 agentes de análise
- `fvg_quality.py` — scoring FVG (premium/discount/gap/tendência)
- `self_learning.py` — ajuste de pesos por resultado
- `validate_before_apply.py` — validação pré-deploy (PF>2.0, WR>45%)
- `tv_ohlc_extractor.py` — extração CDP TradingView
- `forex_realtime_monitor.py` — gestão 2R/3R (breakeven + trail)

## FVG Quality Scoring

Critérios (threshold 45-55):
1. Tamanho mínimo (>2x spread) — OBRIGATÓRIO
2. Premium/Discount (30pts) — compra em discount, venda em premium
3. Alinhamento com tendência (25pts) — FVG na direção do momentum
4. First touch / não mitigado (20pts)
5. Vela de qualidade (10pts)
6. Penalidade FVGs consecutivos >3 (-15pts)
Score ≥55 eliminou 92% dos trades ruins em backtest.

## Anti-Correlação

Grupos por moeda BASE:
- USD: USDJPY, USDCAD
- EUR: EURUSD, EURJPY
- GBP_XAU: GBPUSD, GBPJPY, XAUUSD (libra lastro ouro)
MAX_CORRELATED_PAIRS = 1 (máx 1 par por grupo)

## Dados M1 — CDP TradingView

- `fetch_ohlcv` para M1 usa CDP TradingView como fonte PRIMÁRIA
- Brave :9222 WebSocket CDP
- ~544 velas M1 reais, sem erro de escala
- yfinance é FALLBACK (limite 7 dias, colunas inconsistentes)
- PITFALL: yfinance 1d retorna colunas minúsculas (h/l/c) — normalizar

## PITFALLS

1. RR 3:1 NUNCA reduzir — Roberto recusou explicitamente
2. CRT é filtro, não substituto do bias
3. M15 é timeframe mínimo para estrutura; M1 é só entrada
4. Cada par tem comportamento diferente (ligado ao país de origem)
5. Mercado asiático lateralizado mas prediz próximos mercados
6. Sempre testar em backtest antes de aplicar (validate_before_apply.py)
7. yfinance colunas minúsculas para 1d — usar col_map no get_multi_tf_bias
8. Brave :9222 bloqueia comandos de sessão CDP (Runtime.evaluate, etc)
