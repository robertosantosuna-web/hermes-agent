# smartmoneyconcepts Library — Usage Guide (28/05/2026)

Instalado via: `pip install git+https://github.com/joshyattridge/smart-money-concepts.git`

## Import

```python
from smartmoneyconcepts import smc
import pandas as pd
```

## Funcoes SMC/ICT (8 funcoes)

### FVG (Fair Value Gap)
```python
fvgs = smc.fvg(df)  # df precisa de colunas: open, high, low, close
# Retorna DataFrame com colunas: Top, Bottom, FVG_Type (BULLISH/BEARISH)
```

### Swing Highs/Lows
```python
swings = smc.swing_highs_lows(df, swing_length=50)
# Retorna DataFrame com colunas: HighLow (HH/HL/LH/LL)
```

### Order Blocks
```python
obs = smc.ob(df, swings)  # REQUER swings primeiro!
# Retorna DataFrame com colunas: Top, Bottom, OB_Type
```

### Liquidity Levels
```python
liq = smc.liquidity(df, swings)  # REQUER swings
```

### BOS/CHoCH (Break of Structure / Change of Character)
```python
bos = smc.bos_choch(df, swings)  # REQUER swings
```

### Previous High/Low
```python
prev = smc.previous_high_low(df)
```

### Retracements (Fibonacci)
```python
fib = smc.retracements(df, swings)  # REQUER swings
```

### Sessions
```python
sess = smc.sessions(df, session='London')  # 'London', 'NY', 'Asia'
```

## PITFALLS

1. **ob(), liquidity(), bos_choch(), retracements()** precisam de `swings` como segundo argumento
2. `swings = smc.swing_highs_lows(df)` PRIMEIRO, depois usa nos outros
3. As colunas retornadas usam nomes como `Top`, `Bottom`, `FVG_Type`, `OB_Type` — case-sensitive
4. Direcao: `BULLISH`/`BEARISH` do FVG, mas `BUY`/`SELL` nos sinais do bot — mapear corretamente:
   - BULLISH FVG + HTF BULLISH = BUY signal
   - BEARISH FVG + HTF BEARISH = SELL signal

## Exemplo completo

```python
import pandas as pd
import yfinance as yf
from smartmoneyconcepts import smc

# Baixar dados
df = yf.download('EURUSD=X', interval='15m', period='5d', progress=False)

# Detectar SMC
swings = smc.swing_highs_lows(df, swing_length=50)
fvgs = smc.fvg(df)
obs = smc.ob(df, swings)
liquidity = smc.liquidity(df, swings)
bos = smc.bos_choch(df, swings)

# Usar ultimo FVG
last_fvg = fvgs.iloc[-1]
entry = (last_fvg['Top'] + last_fvg['Bottom']) / 2
```
