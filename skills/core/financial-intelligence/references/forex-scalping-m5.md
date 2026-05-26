# Scalping M5 — Análise de Curto Prazo

## Diferenças do Pipeline Diário

| Parâmetro | Swing D1 | Scalping M5 |
|-----------|----------|-------------|
| Timeframe | Diário (D1) | 5 minutos (M5) |
| Fonte | TradingView Scanner | Yahoo Finance intraday |
| Candles/dia | 1 | ~288 |
| Stop típico | 100-240 pips | 2-8 pips |
| Alavancagem real | 0.7-2.1x (inefetivo) | 30-50x (efetivo) |
| Indicadores | SMA 20/50, RSI 14 | EMA 9/21, RSI 9 |
| Momentum | Não usado | 5-candle momentum em pips |
| Breakout | Não usado | Range 10 candles |
| Volume | Não disponível | Confirmação opcional |

## Algoritmo de Score

| Sinal | Peso | Condição |
|-------|------|----------|
| EMA9 > EMA21 | +2 | Cruzamento bullish |
| EMA9 < EMA21 | -2 | Cruzamento bearish |
| RSI9 < 35 | +1.5 | Sobrevendido |
| RSI9 > 65 | -1.5 | Sobrecomprado |
| RSI9 > 50 | +0.5 | Viés bullish |
| RSI9 < 50 | -0.5 | Viés bearish |
| Mom > 2 pips | +1.5 | Momentum comprador |
| Mom < -2 pips | -1.5 | Momentum vendedor |
| Volume > 1.5× méd | ±0.5 | Confirmação |

**Entrada:** Score ≥ |2.0| (MODERADO), ≥ |3.5| (FORTE)

## Gestão de Risco (50x)

- Risco por trade: 1% do capital
- Relação Risco:Retorno: 1:3
- Stop: 1×ATR do M5
- Target: 3×ATR do M5

Com capital de R$ 1.000:
- Stop batido → -R$ 10 (-1%)
- Target batido → +R$ 30 (+3%)
- 3 targets/dia → +R$ 90/dia → +R$ 1.800/mês

## PITFALLS

- Yahoo Finance gratuito tem delay de ~15 min nos dados intraday
- TradingView Scanner não suporta timeframe < D1
- Para scalping real-time, necessário fonte de dados paga
- Mercado parado (domingo, madrugada) gera sinais NEUTRO — normal
- Volume do Yahoo Finance muitas vezes é 0 — ignorar nesses casos

## Scripts

- `~/.hermes/forex/scalping_m5.py` — módulo standalone
- `~/.hermes/scripts/forex_pipeline_v2.py scalping` — integrado ao pipeline
