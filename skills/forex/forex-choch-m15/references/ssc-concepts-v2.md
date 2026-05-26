# SSC Concepts — 16 vídeos transcritos (21/05/2026)

## Fonte
Canal SSC Telegram (-1001868821926), 33 vídeos, 16 transcritos via faster-whisper.
177,865 caracteres de texto. 808 menções de conceitos.

## Conceitos Extraídos

### CRT — Candle Range Theory (217 menções)
- Tendência dominante → intervalo de velas opostas → acumulação/manipulação/distribuição
- CRT candle = vela de range grande no contexto da tendência
- "Vela de recú" = retracement candle — não é reversão, é oportunidade
- Entrada no FVG após confirmação do CRT

### Wyckoff — Power of Three (219 menções)
- **Acumulação:** Smart Money compra/vende silenciosamente dentro do range
- **Manipulação:** "Preço finge sair da faixa e volta" — sweep de liquidez
- **Distribuição:** Movimento real na direção oposta ao sweep
- "Quando o preço finge sair da faixa e volta, é a fase de manipulação. É aí que o Smart Money deixa seu rastro."

### Estrutura de Mercado (111 menções)
- H1 para big picture: "Estou em alta, baixa ou consolidando"
- Higher highs + higher lows = tendência de alta
- Lower highs + lower lows = tendência de baixa
- "Se o preço passar e fechar acima da máxima anterior, confirma quebra de estrutura"

### Sweep/Liquidez (110 menções)
- Sweep é a manipulação: rompe extremo do range e reverte
- "Expurgo cronometrado entre 9 e 10 da manhã"
- "Se a limpeza ocorrer fora desse período, não haverá"
- Pavio de rejeição > corpo do candle

### Fluxo de Ordens (35 menções)
- "Fluxo de ordens contrário" — contra-order flow
- Mercado cria liquidez na perna de mitigação
- "Através da câmara de fluxo para marcar seu range"
- Sem padrão de fluxo = sem entrada

## Aplicabilidade ao Bot

| Conceito | Backtest | Conclusão |
|----------|----------|-----------|
| CRT | ✅ Funciona | 68.8% → 72.6% WR com S/R |
| Wyckoff/Sweep | ❌ 0 trades | Inválido como filtro algorítmico |
| H1 Trend | ❌ Piora WR | 64.1% vs 68.8% baseline |
| Volume | ❌ 0 trades | Yahoo Finance sem dados de volume |
| S/R Levels | ✅ Funciona | +3.8pp WR |
| Multi-TF M5 | ❌ Ruído | 48.6% WR mesmo com CRT |
| Multi-TF M30/H1 | ⚠️ Poucos trades | Bom WR mas baixa frequência |

## Lição Principal

Os conceitos SSC (estrutura, fluxo, Wyckoff, sweep) funcionam para **análise visual** humana.
Como filtros algorítmicos em M15, apenas **CRT + S/R Levels** sobrevivem com resultado positivo.
Sweep/Wyckoff requerem reconhecimento de padrão contextual que não se traduz em regras booleanas simples.
