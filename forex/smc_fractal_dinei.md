# Metodologia SMC Fractal — Dinei (absorvido 26/05/2026)

Fonte: Chat export Dinei + Lucas (Hermes Agent, GPT-5.5, profile trader)
Período: 04/05/2026 a 11/05/2026 — ~1500 mensagens

## Princípio Fractal

O fractal de um timeframe maior vira o range do timeframe 2 tempos abaixo.
1 tempo abaixo mostra apenas o CHOCH inicial, não o range completo.

```
Mensal   → chega em POI, inicia correção
Semanal  → 1 tempo abaixo → mostra CHOCH da correção
Diário   → 2 tempos abaixo → mostra o fractal (range) do Semanal
H4       → range do Diário
H1       → range do H4
M15/M5   → entradas
```

## Estrutura de Pivôs

Pivôs são validados com `ta.pivothigh(high, 5, 1)` / `ta.pivotlow(low, 5, 1)`:
- **5 candles atrás**: o pivô tomou liquidez de 5 candles anteriores
- **1 candle à frente**: confirma que não foi violado imediatamente
- Menor length → mais pivôs → mais sensível (3-10 configurável)

Isso garante que cada pivô já nasce como tomada de liquidez local.

## MSS (Market Structure Shift)

MSS não exige rompimento do topo/fundo oposto. Basta:
1. Preço faz perna de alta (HH/HL)
2. Toma liquidez do fundo anterior
3. Retorna → já é considerado mudança de estrutura

## Order Block

Definido como o extremo do trecho anterior ao rompimento:
- OB bullish: menor low do trecho antes do rompimento de alta
- OB bearish: maior high do trecho antes do rompimento de baixa
- Não é "última vela contrária" — é o range completo do trecho

## Pipeline de Análise

```
1. Semanal → viés macro e estrutura externa
2. Diário/H4 → confirmação da correção ou expansão
3. H1/M15 → viés do dia
4. M5/M1 → entrada com CHoCH/BOS
```

## Killzones (NY time)

- London Open: 03:00-05:00 NY
- NY Open: 08:00-10:00 NY  
- London Close: 10:00-12:00 NY

## Gestão de Risco

- Risco por trade: 1%
- RR mínimo: 3:1
- Max trades/dia: 3 (1 por killzone)
- Max loss/dia: 3%
- Break-even em 1.5R
- Sem trailing stop

## Ferramentas

- TradingView CLI: `tv draw shape --type long_position`, screenshots, anotações
- Pine Script: `pivothigh()` / `pivotlow()` com len configurável
- TradingEconomics Calendar: https://tradingeconomics.com/calendar
- Webhook TradingView → Hermes: rota única por fonte

## Anti-Padrões Descobertos

- Investing.com bloqueado por Cloudflare → usar TradingEconomics
- Rate limit 429 → não retentar em loop, esperar
- Nunca armazenar senhas em plaintext
- Webhooks separados por fonte (TradingView ≠ Evolution API)
- YOLO mode requer cuidado extra
