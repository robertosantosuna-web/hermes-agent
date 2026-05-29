# CRT Model — Candle Range Theory
> Extraído do vídeo "WhatsApp Video 2026-05-29" — Centry Analyst

## Conceito

O CRT Model identifica reversões baseado no comportamento de velas:
1. Uma vela CRT (grande, direcional) aparece no H1
2. A vela seguinte varre a liquidez (sweep) além do range da CRT
3. A vela de sweep fecha DENTRO do range (armadilha)
4. Entrada no M15 via FVG dentro do range da vela de sweep

## Critérios de Entrada

### H1 — CRT + Sweep
- CRT candle: range > 1.3x média das últimas 20 velas
- BUY: CRT bearish → sweep varre o low → fecha acima do low
- SELL: CRT bullish → sweep varre o high → fecha abaixo do high

### M15 — FVG no Sweep Range
- FVG precisa estar dentro do range [sweep_low, sweep_high]
- Até 2 FVGs por setup (entrada dual)
- SL: 20% abaixo do low da CRT (BUY) ou 20% acima do high (SELL)

## Gestão de Trade

- **TP1 (1:1)**: Fecha 50% da posição, garante breakeven
- **TP2 (2:1)**: Resto corre com SL no breakeven após 1:1
- Se segunda entrada for ativada (L2), mesma gestão

## Exemplo do Vídeo

```
[108s] "We see a CRT candle, a significant bearish candlestick,
        and the following candle sweeps the low... then it closes above it"

[148s] "We go down to the 15 minute chart and the only thing we want
        to see is a fair value gap that forms INSIDE the sweep candle range"

[310s] "We always close 50% of our position at the one to one target"

[839s] "Here we have a small FVG, so we set a buy limit with a
        relatively larger stop loss"

[848s] "Following that, we have another FVG formation. So without
        canceling the first trade, we set up another one"
```

## Implementação

- `detect_crt_setup()`: Detecta CRT + sweep no H1
- `find_fvg_in_range()`: Busca FVGs dentro do sweep range no M15
- Arquivo: `~/.hermes/scripts/forex_bot_multi.py`
