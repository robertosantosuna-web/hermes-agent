# Forex Backtest V4 — CRT Killzones (18/05/2026)

## Metodologia

- **Fonte:** Yahoo Finance via yfinance, 5m candles, 10 dias
- **Pares:** EUR/USD, GBP/USD, EUR/GBP, USD/JPY, EUR/JPY
- **Killzones testadas:** London 04:00, NY 09:30, London Close 12:00 (BRT)
- **Script:** `~/.hermes/forex/backtest_killzones.py`

## Resultados por Killzone

| Killzone | Trades | Win Rate | P&L | Status |
|----------|--------|----------|-----|--------|
| London Close (12-13h) | 12 | 50% | +6.72% | ✅ ATIVA |
| London Open (04-04:30) | 2 | 0% | -0.82% | ❌ Descartada |
| NY Open (09:30-10) | 1 | 0% | -0.95% | ❌ Descartada |

## Conclusão

Apenas London Close gera resultado positivo. Motivos:
- EUR/USD tem ranges de 2-3 pips na London Open (insuficiente para stops >3p)
- NY Open tem volatilidade mas sem padrão CRT claro (ruído de notícias)
- London Close captura o fechamento europeu + início da tarde NY = maior range

## Parâmetros Ótimos (London Close)

- **Janela:** 12:00-13:00 BRT (60 min)
- **Pares:** USD/JPY (stop 5-8p, target 7.5-12p), EUR/JPY (stop 5-10p, target 7.5-15p)
- **RR:** 1:1.5
- **Wick mínimo:** 2.0p (JPY), 1.5p (GBP)
- **Momentum mínimo:** 2p (3 velas)
- **Range pré-killzone:** >5p (média 5 velas)

## 12 Trades Detalhados

| Data | Par | Tipo | Result | Pips | P&L | Dur | Signal |
|------|-----|------|--------|------|-----|-----|--------|
| 05/05 | USD/JPY | BUY | TC+1.6 | +1.6 | +0.30% | 15m | L3.4p |
| 06/05 | EUR/JPY | SELL | TP | +8.7 | +1.42% | 15m | H6.6p |
| 06/05 | USD/JPY | SELL | TP | +7.5 | +1.44% | 10m | H5.0p |
| 06/05 | USD/JPY | BUY | TP | +7.5 | +1.44% | 25m | L2.5p |
| 07/05 | EUR/JPY | BUY | TP | +7.5 | +1.22% | 30m | L2.2p |
| 11/05 | USD/JPY | SELL | TC-0.9 | -0.9 | -0.17% | 10m | H3.2p |
| 14/05 | USD/JPY | SELL | TP | +9.1 | +1.74% | 50m | H3.6p |
| 14/05 | GBP/USD | BUY | SL | -4.0 | -0.89% | 30m | L2.2p |
| 15/05 | EUR/JPY | SELL | TP | +7.5 | +1.22% | 10m | H2.5p |
| 15/05 | EUR/JPY | SELL | SL | -5.0 | -0.81% | 15m | H2.4p |
| 15/05 | USD/JPY | BUY | TC-0.1 | -0.1 | -0.02% | 25m | L2.1p |
| 18/05 | USD/JPY | BUY | TC-0.9 | -0.9 | -0.17% | 15m | L2.8p |

**Legenda:** TP = take profit, SL = stop loss, TC = time close (fim da killzone)
