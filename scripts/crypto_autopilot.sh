#!/bin/bash
# Crypto AutoPilot 24/7 v4 — Silencioso, só notifica Telegram quando há ação

cd /home/roberto/.hermes/crypto

# Scanner
OUTPUT=$(/usr/bin/python3 crypto_bot.py 2>&1)

# Só continuar se houve sinal ou trade
HAS_SIGNAL=$(echo "$OUTPUT" | grep -c "SINAL(is)")
HAS_TRADE=$(echo "$OUTPUT" | grep -c "EXECUTANDO\|TRADE EXECUTADO")

if [ "$HAS_SIGNAL" -gt 0 ] || [ "$HAS_TRADE" -gt 0 ]; then
    # Executor
    if [ -f signals.json ]; then
        EXEC_OUTPUT=$(/usr/bin/python3 binance_executor.py 2>&1)
        OUTPUT="$OUTPUT
$EXEC_OUTPUT"
    fi
    
    # Enviar para log
    echo "[$(date '+%d/%m %H:%M')] $OUTPUT" >> autopilot.log
    
    # Mostrar output (vai pro Telegram)
    echo "$OUTPUT"
fi

# Limpar log grande
if [ $(wc -l < autopilot.log 2>/dev/null || echo 0) -gt 1000 ]; then
    tail -500 autopilot.log > /tmp/crypto_log.tmp
    mv /tmp/crypto_log.tmp autopilot.log
fi
exit 0
