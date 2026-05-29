# Backtest V2 — Qualidade sobre Quantidade (27/05/2026)

## Resultados

**Estratégia:** FVG+CRT H1, 6 pares, 30 dias.
**Parâmetros:** Gap≥10p, CRT≥85%, Dominância≥80%, RR 2:1, SL 12-20p, Score≥0.7.
**Regra:** Máximo 1 trade/dia/par. Alinhamento com tendência EMA20/50.

```
TOTAL: 28 trades | WR=35.7% | PnL=+49p | +1.8p/trade
Expectância: +1.8p | Win: 30p | Loss: 14p
```

### Por par

| Par | Trades | WR | PnL | Veredito |
|-----|--------|-----|------|----------|
| USDJPY | 3 | **100.0%** | +88p | ✅ PRIORITY |
| EURJPY | 3 | **66.7%** | +52p | ✅ PRIORITY |
| GBPUSD | 7 | 28.6% | -4p | ❌ BREAKEVEN |
| GBPJPY | 8 | 25.0% | -32p | ❌ NEGATIVO |
| EURUSD | 6 | 16.7% | -36p | ❌ RUIM |
| USDCAD | 1 | 0.0% | -19p | ❌ PÉSSIMO |

## Lições

1. **FVG+CRT standalone NÃO funciona como estratégia autônoma.** Precisa de filtros adicionais (multi-TF confirmation, notícias, volume).
2. **USDJPY e EURJPY são os ÚNICOS pares lucrativos** no backtest de 30 dias.
3. **Gap≥10p + CRT≥85% + Dominância≥80%** reduz trades de 652→28 mas WR cai de 29%→35.7%. Ainda insuficiente.
4. **Tendência EMA é necessária mas não suficiente** — mercado lateral mata os sinais.
5. **Máximo 1 trade/dia/par** é saudável — evita overtrading.
6. **Cash is a position.** Melhor não operar que operar mal.

## Scripts

- `backtest_chart_analyzer.py` — V1: CRT≥70%, 652 trades, -1904p (FAIL)
- `backtest_v2_quality.py` — V2: CRT≥85%, 28 trades, +49p (MARGINAL)
- `n_accumbens_update.py` — Injeta resultados no pair_weights + brain_context

## Impacto no Sistema

Após o backtest, o `pair_weights_live.json` foi atualizado:
- PRIORITY: USDJPY (76.3%), EURJPY (65.4%), XAUUSD (67.1%)
- PAUSED: GBPJPY, USDCAD, GBPUSD, EURUSD (WR<55%)

O `MIN_WR_REAL=55%` no bot_multi automaticamente bloqueia os pares PAUSED.
