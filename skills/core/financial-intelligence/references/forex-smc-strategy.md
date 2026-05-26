# Estratégia Forex — ICT/SMC + 3:1 RR
# Fonte: Sessão 2026-05-19 + pesquisa consolidada

## Conceitos (ICT/SMC — Inner Circle Trader / Smart Money Concepts)

### Market Structure (Estrutura de Mercado)
- **Bullish**: Higher Highs (HH) + Higher Lows (HL) consecutivos
- **Bearish**: Lower Highs (LH) + Lower Lows (LL) consecutivos
- **BOS** (Break of Structure): Preço rompe high/low anterior confirmando tendência
- **CHoCH** (Change of Character): Preço rompe estrutura na direção oposta — sinal de reversão

### Liquidity (Liquidez)
- **Buy-side liquidity**: Acima das máximas anteriores — onde estão os stops dos shorts
- **Sell-side liquidity**: Abaixo das mínimas anteriores — onde estão os stops dos longs
- **Liquidity sweep**: Preço "caça" stops antes de reverter — armadilha clássica
- **Judas swing**: Falso rompimento na abertura de killzone que caça liquidez e reverte

### Order Blocks (Blocos de Ordens)
- **Bullish OB**: Último candle bearish ANTES de um impulso forte de alta
- **Bearish OB**: Último candle bullish ANTES de um impulso forte de baixa
- Uso: Preço retorna ao OB para "respeitar" a zona de ordens institucionais

### Fair Value Gaps (FVG)
- Padrão de 3 candles onde o candle do meio deixa um gap entre o primeiro e o terceiro
- **Bullish FVG**: Low do candle 1 > High do candle 3 (gap acima)
- **Bearish FVG**: High do candle 1 < Low do candle 3 (gap abaixo)
- Preço frequentemente retorna ao FVG para "corrigir" a ineficiência

## Regras de Entrada (5 passos)

### LONG
1. M15 confirma tendência de alta (HH + HL)
2. M5 faz sweep abaixo de mínima anterior (caça sell-side liquidity)
3. CHoCH bullish: candle seguinte fecha ACIMA da máxima do candle de sweep
4. Preço retorna ao Order Block (último candle bearish) ou FVG bullish
5. Entrada no fechamento do candle que toca o OB/FVG
6. SL: abaixo da mínima do sweep | TP: 3x SL

### SHORT (PREFERENCIAL — 44.4% WR no backtest)
1. M15 confirma tendência de baixa (LH + LL)
2. M5 faz sweep acima de máxima anterior (caça buy-side liquidity)
3. CHoCH bearish: candle seguinte fecha ABAIXO da mínima do candle de sweep
4. Preço retorna ao Order Block (último candle bullish) ou FVG bearish
5. Entrada no fechamento do candle que toca o OB/FVG
6. SL: acima da máxima do sweep | TP: 3x SL

## Filtros

- NÃO entrar sem CHoCH confirmado (sweep sem confirmação = armadilha)
- NÃO entrar se OB/FVG já foi testado 2x (perde força)
- NÃO entrar contra tendência do M15 (só a favor)
- NÃO entrar se notícia de alto impacto em 5 min
- SIM quando OB coincide com Fibonacci 0.62-0.79
- SIM em FVG "fresh" (não testado ainda)

## Killzones (BRT)

| Killzone | Horário | Pares |
|----------|---------|-------|
| London Open | 05:00-07:00 | EURUSD, GBPUSD, EURGBP |
| NY Open | 10:00-12:00 | EURUSD, GBPUSD, USDJPY |
| London Close ⭐ | 12:00-14:00 | EURUSD, EURJPY, USDJPY |

## Backtest Results (15 dias, 56 trades)

| Métrica | Valor |
|---------|-------|
| Win Rate | 28.6% |
| PnL | +54.5 pips |
| PnL/Trade | +1.0 pip |
| Profit Factor | 2.1 |
| SHORT WR | 44.4% (vs LONG 21.1%) |
| Best Pair | EURUSD (36.4% WR) + EURJPY (33.3% WR) |
