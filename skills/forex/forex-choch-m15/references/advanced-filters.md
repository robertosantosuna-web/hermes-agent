# Filtros Avançados (Especialistas 29/05)

## 1. RSI Filter (evitar zona neutra)
- RSI(14) no M5
- Só compra se RSI > 55 (força bullish)
- Só vende se RSI < 45 (força bearish)
- RSI 45-55 = zona neutra, não operar

## 2. EMA Multi-TF Alignment
- M1 só opera se M5 e M15 alinhados
- EMA(20) no M5 vs EMA(20) no M15
- Compra: EMA_M1 > EMA_M5 > EMA_M15
- Venda: EMA_M1 < EMA_M5 < EMA_M15

## 3. Bollinger Squeeze (evitar congestão)
- BB(20,2) no M5
- Largura = (upper - lower) / middle
- Só operar se largura > 0.001 (expansão)
- Squeeze (largura mínima) = congestão, evitar

## 4. Padrões de Candle (confirmação extra)
- **Engolfo**: candle atual engole o anterior na direção do bias
- **Pin Bar**: wick > 2× body, rejeição na direção do bias
- **Inside Bar + Breakout**: rompimento do IB confirma direção

## 5. Anti-Whipsaw
- Esperar 2 candles de confirmação após FVG
- Heikin Ashi para suavizar ruído (substituir OHLC por HA)
- Filtrar ATR < 50% da média (sem volatilidade = sem trade)

## 6. Kelly Criterion (gestão adaptativa)
- f = WR - (1-WR)/RR
- Ex: WR=55%, RR=3 → f = 0.55 - 0.45/3 = 0.40 (40% da banca)
- Na prática: usar 1/4 de f (Kelly fracionado) para suavizar
- Ajustar tamanho da posição baseado no WR das últimas 20 trades
