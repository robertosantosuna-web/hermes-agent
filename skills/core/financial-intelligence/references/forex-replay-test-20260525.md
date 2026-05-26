# Replay Test — CHoCH+FVG M15 + Weekly Bias (25/05/2026)

Teste realizado com dados coletados pelo cérebro (brain FVG analysis) simulando
o comportamento do TradingView Bar Replay. 3 pares analisados com gap≥5 pips.

## Resultados por Par

| Par | FVGs (gap≥5) | Avg Gap | WR Geral | WR Killzone | Trades KZ |
|---|---|---|---|---|---|
| GBPUSD | 198 | 8.8p | 69.9% | **83.8%** | 37 |
| EURUSD | 111 | 8.5p | 61.8% | **76.9%** | 13 |
| AUDUSD | 141 | 8.0p | 65.6% | **68.8%** | 16 |

- **Killzone**: London Open (06-07h UTC) + NY Open (15-16h UTC)
- **Média Killzone WR**: 76.5% (vs backtest V7 CRT+S/R: 72.6%)

## Confirmações

- ✅ Killzones têm WR consistentemente superior a qualquer outro horário
- ✅ Evening hours 18-23h UTC = **0% WR** (tóxico, nunca operar)
- ✅ gap≥5 pips elimina padrões de ruído (gap 0-4 são noise)
- ✅ GBPUSD é o melhor par para esta estratégia (83.8% WR, maior volume)
- ⚠️ CRT filter não pôde ser testado (range_pips ausente nos dados)

## Viés Semanal (26-30 Mai 2026)

- **USD/JPY: BUY** — Risk-on carry trade, Iran deal
- **GBP/USD: BUY** — Risk-on + Killzone WR 83.8% suporta
- **EUR/USD: NEUTRAL** — Forças conflitantes (Fed hawkish vs risk-on)

## Recomendação Final

Seguir V7 com:
- CHoCH+FVG M15, gap≥5, Killzones apenas
- CRT ativo quando dados disponíveis
- Viés semanal como filtro direcional
- RR 3:1, máx 4 trades/dia
- NUNCA 18-23h UTC
