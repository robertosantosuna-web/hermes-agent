# MAPEAMENTO DE ERROS — CRYPTO AUTOPILOT v9
# Atualizado: 30/05/2026
# Cada erro = 1 aprendizado permanente

## ERROS RESOLVIDOS

### 1. CRON: Script retornava exit code 1 (falso erro)
- Causa: `[ $(wc -l) -gt 1000 ]` retorna 1 quando falso
- Sintoma: Cron marcava `last_status: error` mesmo com execução OK
- Correção: `exit 0` explícito no final + stderr redirecionado
- Arquivo: scripts/crypto_autopilot.sh

### 2. BINANCE: base_url errada para sapi endpoints
- Causa: base_url = 'https://api.binance.com/api' + '/sapi/v1/...' = 404
- Correto: base_url = 'https://api.binance.com' (v3 → /api/v3/*, sapi → /sapi/v1/*)
- Sintoma: Todos os /sapi/* retornavam 404
- Arquivo: crypto/binance_trader.py

### 3. BINANCE: SyntaxError try/except órfão
- Causa: `except` sem `try` correspondente no _margin_sell
- Sintoma: ImportError ao carregar o módulo
- Arquivo: crypto/binance_trader.py

### 4. PRECISÃO: Quantidade com floating point na OCO
- Causa: round(qty / step) * step introduz erro de ponto flutuante
- Sintoma: Binance rejeitava "Precision is over maximum"
- Correção: round_to_step() usa f-string para determinar decimais
- Arquivo: crypto/binance_trader.py

### 5. PRECISÃO: Saldo insuficiente após comissão
- Causa: Comissão reduzia saldo, OCO tentava vender quantidade cheia
- Sintoma: "Account has insufficient balance"
- Correção: round_to_step(use_floor=True) arredonda pra BAIXO
- Arquivo: crypto/binance_trader.py

### 6. OCO: Price relationship incorreto (BUY)
- Causa: SL/TP calculados com preço do SINAL, não do FILL real
- Sintoma: Compra a $696, SL/TP em $684/$688 → preços abaixo do mercado
- Correção: Recalcular SL/TP com entry_price real do fill
- Arquivo: crypto/binance_trader.py (execute_signal e _margin_sell)

### 7. FLUXO: Scanner poluía open_trades.json antes da execução
- Causa: crypto_bot.py salvava em open_trades.json ao gerar sinal
- Sintoma: Se executor falhava, trade fantasma bloqueava novos sinais
- Correção: Scanner só gera signals.json. Executor que atualiza open_trades.json
- Arquivo: crypto/crypto_bot.py + crypto/binance_executor.py

### 8. MONITOR: Close monitor não detectava fechamento
- Causa: API Binance retorna 'isBuyer' (bool), código usava 'side' (string)
- Sintoma: Trade fechava mas JSON não atualizava, sem notificação
- Correção: Usar tr['isBuyer'] em vez de tr['side']
- Arquivo: scripts/trade_monitor.py

### 9. MONITOR: Dois scripts separados (close + partial)
- Causa: trade_close_monitor.py + partial_tp_monitor.py independentes
- Sintoma: Duas cron jobs, lógica duplicada, SL→BE e close competiam
- Correção: Unificado em trade_monitor.py (1 cron, 2 funções)
- Arquivo: scripts/trade_monitor.py

### 10. SELETOR: Par escolhido por momentum, não por WR
- Causa: Score = vol + mom + tier, sem considerar performance histórica
- Sintoma: BNBUSD (+9.5% mom) escolhido sobre DOGEUSD (96% WR)
- Correção: _get_wr_bonus() adiciona +25 a -15 baseado na WR do backtest
- Arquivo: crypto/pair_selector.py

### 11. AUTOPILOT: Sem retry em falha
- Causa: Script bash sem tratamento de erro
- Sintoma: Uma falha de rede parava o ciclo
- Correção: 2 tentativas com 10s intervalo + log de erros separado
- Arquivo: scripts/crypto_autopilot.sh

### 12. ALERTA: Sem trigger automático em falha crítica
- Causa: Falha do autopilot passava despercebida
- Sintoma: Autopilot parado por horas sem ninguém saber
- Correção: autopilot_alert.json → Emergency Fix cron (agente acionado)
- Arquivo: scripts/crypto_autopilot.sh + scripts/crypto_alert_check.py

## REGRAS PERMANENTES (NUNCA MAIS QUEBRAR)

1. Scanner NUNCA escreve em open_trades.json
2. SL/TP SEMPRE recalculados com preço REAL do fill
3. Quantidades de venda SEMPRE usam use_floor=True
4. Scripts bash SEMPRE terminam com exit 0
5. API Binance: isBuyer (bool), NÃO side (string)
6. Pair selector SEMPRE considera WR histórica
7. Todo script crítico tem retry + log de erro
8. Falha crítica gera alerta que aciona o agente
