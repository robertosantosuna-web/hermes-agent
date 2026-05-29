# Order Block & Breaker Block Detection

## Simple Order Block
```python
def detect_order_blocks(open_, high, low, close):
    """OB: última vela oposta antes do rompimento."""
    n = len(close)
    obs = []
    for i in range(n - 1):
        # Bullish OB: vela bearish cuja high é rompida pra cima
        if close[i] < open_[i] and close[i+1] > high[i]:
            obs.append({'index': i, 'type': 'bullish', 'zone_low': low[i], 'zone_high': open_[i]})
        # Bearish OB: vela bullish cuja low é rompida pra baixo
        elif close[i] > open_[i] and close[i+1] < low[i]:
            obs.append({'index': i, 'type': 'bearish', 'zone_low': open_[i], 'zone_high': high[i]})
    return obs
```

## Breaker Block (OB quebrado → inverte papel)
```python
def detect_breaker_blocks(close, obs):
    """BB: OB cuja zona foi violada → suporte vira resistência (ou vice-versa)."""
    n = len(close)
    breakers = []
    for ob in obs:
        for j in range(ob['index'] + 1, n):
            if ob['type'] == 'bullish' and close[j] < ob['zone_low']:
                breakers.append(ob); break
            elif ob['type'] == 'bearish' and close[j] > ob['zone_high']:
                breakers.append(ob); break
    return breakers
```

## Uso no scan
- OB atua como zona de suporte/resistência para entrada
- Se preço retorna ao OB + FVG na mesma zona → entrada de alta qualidade
- BB é nível ainda mais forte que OB original
