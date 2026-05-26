# Backtest Pitfalls — CHoCH+FVG

## 1. Sliding Window vs Last-Candle (☠️ CRÍTICO)

**Bug:** `detect(df, pv)` sempre analisa `df.iloc[-30:]` (últimas 30 velas), NÃO a janela do anchor.

```python
# ❌ ERRADO — sempre analisa últimas 30 velas, ignora anchor
for idx in range(30, len(df)-10, 4):
    sigs = detect(df, pv)  # sempre as MESMAS 30 velas!

# ✅ CORRETO — analisa a partir do anchor
def detect_at(df, anchor, pv):
    start = max(0, anchor-30)
    df30 = df.iloc[start:anchor+1]
```

**Sintoma:** Backtest retorna 0-4 trades em 30 dias (vs 247 reais). Cada "passo" encontra os mesmos sinais.

## 2. df.iloc[j] com índices do slice (☠️ CRÍTICO)

**Bug:** `df['High'].values[-30:]` cria array indexado 0-29. Mas `df.iloc[j]` acessa o DataFrame COMPLETO (índice 0 = primeira vela dos dados, não a 30ª de trás pra frente).

```python
# ❌ ERRADO
highs = df['High'].values[-30:]  # índices: 0 a 29
# ... depois ...
df.iloc[j]['High']  # j=0 acessa vela de 5 dias atrás!

# ✅ CORRETO
df30 = df.iloc[-30:]
df30.iloc[j]['High']  # acessa vela correta
```

## 3. Step Size Trade-off

Step=1 (toda vela): mais trades, redundância, lento (O(n²))
Step=4 (a cada hora): equilibrado pra backtest 30d
Step=len(df)//500: densidade uniforme, perde ~20% sinais

**Recomendação:** Step=4 pra backtest rápido. Step=1 pra resultado final.

## 4. FVG ICT vs Adjacent Gap

FVG correto (ICT): `candle[j].High < candle[j+2].Low` (gap de 3 velas)
FVG errado (adjacente): `candle[j+1].Low > candle[j].High` — NUNCA acontece em forex

Adjacent gap só existe em stocks com after-hours. Forex 24h não tem.
