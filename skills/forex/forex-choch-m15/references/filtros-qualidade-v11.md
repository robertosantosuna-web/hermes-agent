# Filtros de Qualidade V11 (29/05/2026)

Implementados em `forex_bot_multi.py` após detecção de FVG M1.

## Filtros

| Filtro | Threshold | Propósito |
|--------|-----------|-----------|
| Candle fechado | `idx < len-1` | Evitar entrada em candle aberto (ruído intrabarra) |
| ADX/DMI | `pdi > ndi` (BUY) / `ndi > pdi` (SELL) | Confirmar tendência na direção do bias |
| Volume | `vol > 1.3× vol_avg(20)` | Evitar entrada em baixa liquidez |
| SL ATR | `max(10, min(2×ATR(14), 30))` pips | SL adapta à volatilidade do par |

## Implementação

```python
# ATR manual sem talib
tr = np.maximum(h[-15:]-l[-15:], np.maximum(abs(h[-15:]-np.roll(c[-15:],1)), abs(l[-15:]-np.roll(c[-15:],1))))
tr[0]=h[-15]-l[-15]
atr = np.mean(tr[-14:])/pip

# DMI manual
up=h-np.roll(h,1); dn=np.roll(l,1)-l; up[0]=dn[0]=0
pdm=np.where((up>dn)&(up>0),up,0); ndm=np.where((dn>up)&(dn>0),dn,0)
atr_val=np.mean(tr[-14:])
pdi=100*np.mean(pdm[-14:])/atr_val
ndi=100*np.mean(ndm[-14:])/atr_val
trend_ok = (bias=='BUY' and pdi>ndi) or (bias=='SELL' and ndi>pdi)

# Volume
vol_ok = v[-1] > np.mean(v[-20:]) * 1.3

# Candle fechado
candle_closed = signal['idx'] < len(closes) - 1
```

## Resultado esperado
- Redução de trades (filtros eliminam ~60% dos sinais)
- Aumento de WR (20% → 35-40% estimado)
- SL adaptativo evita stop caçado em pares voláteis
