# ICT Pattern Types — Catálogo de Padrões Detectados

Referência para o módulo Chart Pattern Study (`scripts/chart_pattern_study.py`).
Todos os padrões são derivados dos conceitos ICT (Inner Circle Trader) e detectados
em candles M5 via Yahoo Finance.

## CHoCH — Change of Character

Sinal de reversão. Ocorre quando o preço faz um sweep de liquidez (rompe um swing
high/low anterior) e reverte com força.

**Bullish CHoCH:**
- Preço faz sweep abaixo de swing low anterior (hunting sell-side liquidity)
- Fecha acima da abertura (v candle bullish)
- Próxima vela rompe acima da máxima da vela de sweep
- Quality: 'high' se fechar acima de 50% do range da vela

**Bearish CHoCH:**
- Preço faz sweep acima de swing high anterior (hunting buy-side liquidity)
- Fecha abaixo da abertura (v candle bearish)
- Próxima vela rompe abaixo da mínima da vela de sweep

**Uso na estratégia:** CHoCH é o gatilho de entrada. Após CHoCH confirmado,
entrar na direção da reversão com SL no sweep level.

## FVG — Fair Value Gap

Gap de valor justo — desequilíbrio entre 3 velas consecutivas onde o preço
"pulou" um nível sem negociar nele.

**Bullish FVG:**
- candle[0].high < candle[2].low
- Gap entre a máxima da vela 0 e a mínima da vela 2
- Preço tende a retornar para preencher o gap (rebalance)

**Bearish FVG:**
- candle[0].low > candle[2].high
- Gap entre a mínima da vela 0 e a máxima da vela 2

**Significância:** gap_size_pct > 0.02% é considerado significativo.
FVGs próximos a S/R levels têm mais peso.

## Order Blocks (OB)

Última vela de direção oposta antes de um impulso forte. Representa onde
instituições colocaram ordens.

**Bullish OB:**
- Vela anterior é bearish (fecha abaixo da abertura)
- Vela atual rompe acima da máxima da anterior (bullish breakout)
- Próximas velas confirmam continuação (média dos fechamentos > máxima do OB)

**Bearish OB:**
- Vela anterior é bullish
- Vela atual rompe abaixo da mínima da anterior
- Continuação bearish confirmada

**Quality:** 'high' quando o rompimento é limpo (fecha além do OB).

## Structure Breaks (BOS)

Break of Structure — continuação de tendência. Diferente do CHoCH (que é reversão),
BOS confirma que a tendência atual continua.

**Bullish BOS:**
- 3 swing highs consecutivos mais altos (HH)
- Precedido por 2 swing lows consecutivos mais altos (HL)
- Força: proporção da distância entre swings / preço médio

**Bearish BOS:**
- 3 swing lows consecutivos mais baixos (LL)
- Precedido por 2 swing highs consecutivos mais baixos (LH)

## Liquidity Levels

Níveis onde há acúmulo de ordens (stops, entradas pendentes).

**Equal Highs (sell-side liquidity):**
- 2+ swing highs no mesmo nível de preço
- Stops de compradores acumulados acima
- Alvo para sweep antes de reversão bearish

**Equal Lows (buy-side liquidity):**
- 2+ swing lows no mesmo nível de preço
- Stops de vendedores acumulados abaixo
- Alvo para sweep antes de reversão bullish

## Swing Detection

Swing highs e lows são detectados com método fractal de 5 velas:
- Swing high: candle[i].high > max(candle[i-2..i+2].high)
- Swing low: candle[i].low < min(candle[i-2..i+2].low)

## Snapshot

Cada padrão CHoCH high-quality é salvo com:
- 10 velas de contexto antes + 5 depois
- Dados OHLC + body/wick/direction por vela
- ASCII chart para inspeção visual rápida
- Pair, timestamp, quality

## Pattern Library

`~/.hermes/forex/patterns/pattern_library.json`:
- Máximo 50 exemplos por tipo de padrão
- Cumulativo entre execuções
- Usado pelo Weekly Analyzer para identificar padrões recorrentes
