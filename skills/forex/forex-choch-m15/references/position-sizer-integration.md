# Position Sizer — Calculadora de Lote Integrada (28/05/2026)

Implementada no `cortex_visual.py`, mesma lógica do Position Sizer EA do EarnForex.

## Fórmula

```
volume = (balance x risk_pct) / (sl_pips x pip_value)
```

- balance: saldo real do MT5
- risk_pct: 0.01 (1% forex), 0.005 (0.5% XAUUSD)
- sl_pips: distancia do SL em pips
- pip_value: valor de 1 pip por 0.01 lote (EURUSD=0.10, USDJPY=0.09, XAUUSD=0.10)

## RR Dinamico

```python
def dynamic_rr(pair, htf_trend, n_confluences):
    base = 2.0
    if htf_trend in ("BULLISH", "BEARISH"): base += 0.5
    else: base -= 0.5
    if n_confluences >= 5: base += 1.0
    elif n_confluences >= 4: base += 0.5
    if "XAU" in pair: base = min(base, 2.0)
    return max(1.5, min(base, 5.0))
```

## Pip values (0.01 lote)

| Par | Pip Value |
|-----|-----------|
| EURUSD, GBPUSD, AUDUSD, NZDUSD | $0.10 |
| USDJPY, EURJPY, GBPJPY | $0.09 |
| USDCHF, USDCAD | $0.10 |
| EURGBP | $0.13 |
| XAUUSD | $0.10 |

## Integracao

O PositionSizer eh chamado automaticamente apos cada sinal detectado pelo Cortex Visual.
