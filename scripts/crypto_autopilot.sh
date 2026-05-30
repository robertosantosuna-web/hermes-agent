#!/bin/bash
# Crypto AutoPilot 24/7 v5 — Robusto, com retry em erro
CRYPTO_DIR="/home/roberto/.hermes/crypto"
cd "$CRYPTO_DIR" || exit 1

# Scanner com retry
OUTPUT=""
SCANNER_OK=false
for attempt in 1 2; do
    OUTPUT=$(/usr/bin/python3 crypto_bot.py 2>&1)
    if [ $? -eq 0 ]; then SCANNER_OK=true; break; fi
    echo "[$(date '+%d/%m %H:%M')] Scanner falhou (tentativa $attempt)" >> autopilot_errors.log
    sleep 10
done

if ! $SCANNER_OK; then
    echo "{"error": "scanner_failed", \"time\": "$(date -Iseconds)", \"output\": "$(echo "$OUTPUT" | tail -5 | sed "s/"/\\"/g" | tr "\n" " ")"}" > autopilot_alert.json
    exit 0
fi

# Verificar se tem sinal
if echo "$OUTPUT" | grep -q "SINAL(is)"; then
    # Executor com retry
    for attempt in 1 2; do
        EXEC_OUTPUT=$(/usr/bin/python3 binance_executor.py 2>&1)
        if [ $? -eq 0 ]; then break; fi
        echo "[$(date '+%d/%m %H:%M')] Executor falhou (tentativa $attempt)" >> autopilot_errors.log
        sleep 10
    done
    
    {
        echo "[$(date '+%d/%m %H:%M')]"
        echo "$OUTPUT"
        [ -n "$EXEC_OUTPUT" ] && echo "$EXEC_OUTPUT"
        echo "---"
    } >> autopilot.log
fi

# Limpar logs grandes (>1000 linhas)
for logfile in autopilot.log autopilot_errors.log; do
    if [ -f "$logfile" ]; then
        lines=$(wc -l < "$logfile" 2>/dev/null || echo 0)
        if [ "$lines" -gt 1000 ]; then
            tail -500 "$logfile" > /tmp/crypto_log.tmp
            mv /tmp/crypto_log.tmp "$logfile"
        fi
    fi
done

exit 0
