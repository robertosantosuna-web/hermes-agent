# XAU/USD Backtest — 59 dias (26/05/2026)

## Metodologia
- **Fonte:** Yahoo Finance `GC=F` (Gold Futures) — `XAUUSD=X` retorna 404
- **Período:** 59 dias (limite Yahoo para dados 15m)
- **Estratégia:** FVG puro (3-candle gap) + CRT ≥ 70% + RR 3:1
- **Parâmetros:** gap ≥ $1.00, SL ≥ $2.00, sem killzone (24h)

## Resultados por Timeframe

| TF | Candles | Trades | Wins | Losses | WR | PnL ($) | PF | T/dia | SL Médio |
|----|---------|--------|------|--------|-----|---------|-----|-------|----------|
| M5 | 13278 | 540 | 313 | 227 | 58.0% | +37,116 | 3.08 | 9.3 | $6.7 |
| M15 | 4434 | 235 | 149 | 86 | 63.4% | +21,994 | 2.80 | 4.2 | $10.0 |
| **M30** | **2217** | **143** | **96** | **47** | **67.1%** | **+18,891** | **3.37** | **2.9** | **$11.8** |

## Killzones (M30)

| Zona | UTC | Trades | WR | PnL |
|------|-----|--------|-----|------|
| Asia | 0-5 | 31 | **77%** | +681p |
| London Open | 5-7 | 4 | 100% | +56p |
| London | 7-11 | 43 | 63% | +603p |
| London Close | 11-13 | 14 | 57% | +166p |
| NY AM | 13-16 | 7 | 57% | +50p |
| NY PM | 16-18 | 1 | 100% | +10p |
| After Hours | 18-24 | 43 | 65% | +323p |

## Bullish vs Bearish (M30)

| Direção | Trades | WR |
|---------|--------|-----|
| Bullish | 58 | 70.7% |
| Bearish | 85 | 64.7% |

## Diferenças Críticas Ouro vs Forex

| Aspecto | Forex | Ouro |
|---------|-------|------|
| Gap mínimo | 2 pips | $1.00 (100 ticks) |
| SL mínimo | 15 pips | $12.00 (1200 ticks) |
| STOPLEVEL | ~8-10 pips | **0** (sem restrição!) |
| Pip value (0.01 lot) | $0.10 | $0.01 |
| Spread típico | 0.1-2 pips | $0.40 (40 ticks) |
| Yahoo symbol | `EURUSD=X` | `GC=F` |
| MT5 digits | 5 | 2 |
| Wick filter | OK | **QUEBRA** — desabilitar |

## Wick Filter Bug

O filtro de pavio (`wick_pct = range / max(range, 0.01)`) é sempre ~1.0 para ouro, fazendo `wick_pct < 0.7` = sempre False. **NUNCA usar filtro de pavio em metais.** O `detect_fvg()` no bot foi corrigido para pular o filtro quando `is_metal=True`.

## Viabilidade na Conta Demo ($399)

- 0.01 lote = 1 oz = $0.01/tick
- SL $12.00 × $0.01 = $0.12 risco? NÃO — corrigir:
- SL $12.00 = 1200 ticks × $0.01/tick = **$12.00 de risco**
- 2% de $399 = $7.98 → **insuficiente para 0.01 lote!**
- Volume mínimo viável: 0.01 lote, risco $12.00, precisa de $600+ de saldo
- **Workaround:** reduzir SL para $8.00 (800 ticks) → risco $8.00 → viável com $400

## Configuração Final no Bot

```python
'XAUUSD': {
    'sym': 'GC=F', 'pip': 0.01, 'tf': '30m',
    'killzone': None, 'wr': 67.1, 'metal': True
}
'XAUUSD_KZ': {
    'sym': 'GC=F', 'pip': 0.01, 'tf': '30m',
    'killzone': [0,1,2,3,4,5], 'wr': 77.0, 'metal': True
}
MIN_SL_METAL = 1200  # ticks ($12.00)
MIN_SL_PIPS = 15      # forex
```

## Estratégias Compatíveis

| Estratégia | Compatível? | Motivo |
|-----------|------------|--------|
| E1: FVG+CRT | ✅ SIM | Calibrada com gap $1.00, CRT 70% |
| E2: SMC Fractal | ❌ NÃO | `min_swing_pips=5` = $0.05 no ouro → ruído |
| E3: S/R+FVG | ❌ NÃO | `sr_proximity_pips=5` = $0.05 → swings falsos |

Apenas E1 opera XAUUSD. E2 e E3 desabilitadas via `if not is_metal` no loop de scan.
