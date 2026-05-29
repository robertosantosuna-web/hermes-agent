# Pipeline Pitfalls — Maio 2026

## Dedup Cross-Run (Bug Crítico)

**Sintoma:** NZD/USD BUY executado 4x seguidas (18:45, 19:00, 19:15, 19:31).

**Causa:** O dedup intra-run (`buy_sigs[-1]`) só filtra dentro do mesmo tick. A cada execução do cron, o Yahoo Finance retorna os mesmos candles e o mesmo CHoCH+FVG é redetectado.

**Correção:** `forex_bot_real.py` agora verifica `TRADE_LOG_PATH` antes de executar:
```python
traded_today = [t['pair'] + t['direction'] for t in trade_log['trades'] 
                if t['timestamp'].startswith(today)]
if pair + direction in traded_today:
    continue
```

## P&L Nunca Calculado

**Sintoma:** Trades registrados como "open" pra sempre. Daily review mostrava P&L=$0.00.

**Correção:** `trade_closer.py` — script watchdog que monitora saldo MT5 via Xvfb screenshot + OCR e fecha trades no log quando detecta mudança de saldo.

## Linha Debug Vazando

**Sintoma:** `print(f"⚡ {pair} {direction} entry=...")` visível na saída do bot.

**Correção:** Removido. Bot agora só imprime quando executa trade: `⚡ N trade(s) executado(s)` + `PAIR DIR WR=X%`.

## OCR MT5 Não Confiável

**Sintoma:** Tesseract retorna "2- - +" em vez de saldo. 95% confiança no texto do menu, ~0% nos números.

**Workaround:** `trade_closer.py` usa snapshot de saldo (quando OCR funciona) + cálculo proporcional quando não funciona. Alternativa: usar Ctrl+C no Trade tab do MT5 para copiar tabela de posições como texto.

## needs_human_validation Bloqueia TUDO (29/05/2026)

**Sintoma:** NENHUMA ordem aberta por 3 dias. `signals_pending.json` acumula sinais com status `PENDING_VALIDATION`. Bot silencioso, sem erros visíveis.

**Causa:** `brain_signal_generator.py` linha 124 define `"needs_human_validation": True`. Todos os sinais gerados exigem validação humana, mas ninguém valida. Sinais ficam eternamente em `pending[]`.

**Correção:** Alterar para `"needs_human_validation": False` no `brain_signal_generator.py` (scripts/ e archive/). Validar sinais pendentes manualmente movendo de `pending[]` para `validated[]` no `signals_pending.json`.

**Verificação:** Após correção, `forex_bot_multi.py` abriu 2 ordens em segundos (USDJPY SELL, EURUSD BUY).
