# V9 Multi-Confluence Strategy Results (28/05/2026)

## Backtest: Multi-Confluência SMC/ICT

**Script:** `~/.hermes/forex/backtests/multi_confluence_backtest.py`
**Dados:** 59d M15 + 90d H1 via Yahoo Finance
**Pares:** EURUSD, GBPUSD, USDJPY, GBPJPY, EURJPY

### Resultados

| Métrica | Multi-Confluência | Silver Bullet |
|---------|-------------------|---------------|
| Total Trades | 25 | 64 |
| Win Rate | **60.0%** | 23.4% |
| Profit Factor | **3.25** | 0.67 |
| Max Drawdown | 31.3 pips | 171.1 pips |
| Avg Win | 19.3 pips | 18.5 pips |

### Por Par (Multi-Confluência)

| Par | Trades | WR | P&L |
|-----|--------|-----|-----|
| GBPJPY | 7 | 71.4% | +129.4p |
| EURUSD | 6 | 66.7% | +50.0p |
| USDJPY | 5 | 60.0% | +31.0p |
| GBPUSD | 4 | 50.0% | +15.0p |
| EURJPY | 3 | 33.3% | -25.0p |

### Melhores Killzones

| Killzone | WR |
|----------|-----|
| London Open | 66.7% |
| NY Open | 66.7% |
| London Close | 50.0% |

## Backtest: XAUUSD (Ouro)

**Dados:** 60d M15, GC=F (COMEX futures)
**Config:** SL ATR×2.5, TP 1.5:1, 4+ confluências

| Métrica | Valor |
|---------|-------|
| Total Trades | 29 |
| Win Rate | 44.83% |
| Profit Factor | 1.08 |
| Expectancy | +0.12R |
| P&L Total | +3.50R |

**Conclusão:** Marginalmente lucrativo. Ouro reverte mais que forex — TP 1.5:1 é mais adequado que 2:1.

## Comparação com Estratégias Anteriores

| Estratégia | WR | PF | Status |
|-----------|-----|-----|--------|
| **Multi-Confluência (V9)** | 60% | 3.25 | ✅ ATIVO |
| CHoCH+FVG+CRT (V7) | 66.7% | ? | 📦 Arquivado |
| Silver Bullet puro | 23% | 0.67 | ❌ Descartado |
| SMC Fractal H1 | 5.6% | — | ❌ Descartado |

## Position Sizer Integrado

Calculadora de lote estilo EarnForex Position Sizer:
- `volume = (balance × risk%) / (sl_pips × pip_value)`
- 1% risco forex, 0.5% XAUUSD
- RR dinâmico: 1.5-5.0 baseado em HTF trend + confluências

## Bibliotecas Instaladas

```bash
pip install smart-money-concepts backtesting quantstats mplfinance forex-python
```

**smartmoneyconcepts usage:**
```python
from smartmoneyconcepts import smc
swings = smc.swing_highs_lows(df)
fvgs = smc.fvg(df)
obs = smc.ob(df, swings)
liquidity = smc.liquidity(df, swings)
bos_choch = smc.bos_choch(df, swings)
```
