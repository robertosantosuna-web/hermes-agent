# Backtest CRT — Resultados Corrigidos (20/05/2026)

## Contexto

O backtest original (51-97 trades, 87.5% WR) usava código com **bug de índice**: 
`df.iloc[j]` com índices do slice `[-30:]` no DataFrame completo. FVG era buscado
em velas aleatórias de 5 dias atrás, não nas últimas 30.

O FVG também estava errado: usava gap adjacente (`candle[j+1].Low > candle[j].High`)
que praticamente não existe em forex 15m. Corrigido para FVG ICT de 3 velas:
`candle[j].High < candle[j+2].Low`.

## Resultados Corrigidos (30 dias, 4 pares)

| Par | Raw Trades | Raw WR | Raw PnL | CRT Trades | CRT WR | CRT PnL |
|-----|-----------|--------|---------|------------|--------|---------|
| GBP/USD | 3 | 66.7% | +9.4p | 2 | 100.0% | +13.0p |
| AUD/USD | 1 | 0.0% | -4.1p | 0 | — | — |
| EUR/USD | 0 | — | — | 0 | — | — |
| NZD/USD | 0 | — | — | 0 | — | — |
| **TOTAL** | **4** | **50.0%** | **+5.3p** | **2** | **100.0%** | **+13.0p** |

## Comparação: Antes vs Depois

| Métrica | Antigo (bug) | Corrigido |
|---------|-------------|-----------|
| Trades/30d | 51-97 | 4 |
| WR | 87.5% | 50% (raw) / 100% (CRT) |
| PnL | +43.4p | +5.3p (raw) / +13.0p (CRT) |
| Pares ativos | 4 | 1-2 |

## Diagnóstico

O FVG ICT de 3 velas em janela de 30 candles M15 é **extremamente raro** em forex.
Apenas GBP/USD produz setups consistentes. AUD/USD, EUR/USD e NZD/USD
praticamente não formam FVG detectável nas últimas 30 velas.

**Causas prováveis da baixa frequência:**
1. Janela de 30 velas M15 = 7.5 horas — muito curta para formar swing points significativos
2. FVG de 3 velas exige gap real entre candle 1 e 3 — raro em forex 24h
3. Detecção de swing exige 3 velas de confirmação em cada lado — muito restritivo

## Próximos Passos

1. Expandir janela de detecção de 30 para 96 velas (24h M15)
2. Relaxar swing detection (2 velas em vez de 3)
3. Adicionar filtro de sweep/liquidez antes do CHoCH (vídeos SSC)
4. Testar M5 em vez de M15 (mais velas por unidade de tempo)
5. Considerar FVG de 2 velas (adjacente com tolerância de overlap)

## Sabedoria do Trader

> "Ela tem que aprender a identificar o range e o que é fluxo. Para quando tiver
> uma quebra de fluxo, identificar como CHoCH, aí procurar FVG para entrada.
> Se ela não souber identificar estrutura e fluxo, qualquer quebra ela entra."

**Pipeline correto:** Range/Fluxo → Estrutura → CHoCH → FVG → Entrada
