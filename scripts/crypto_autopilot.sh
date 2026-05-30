#!/bin/bash
# Crypto AutoPilot 24/7 v6 — Persiste sinal entre ciclos, retry até executar
set -e
CRYPTO_DIR="/home/roberto/.hermes/crypto"
cd "$CRYPTO_DIR" || exit 1

# Se já existe sinal pendente (<10min), pular scanner e ir direto pro executor
if [ -f signals.json ]; then
    SIGNAL_AGE=$(($(date +%s) - $(stat -c %Y signals.json 2>/dev/null || echo 0)))
    if [ "$SIGNAL_AGE" -lt 600 ]; then
        echo "[$(date '+%d/%m %H:%M')] Sinal pendente (${SIGNAL_AGE}s), indo direto pro executor" >> autopilot.log
        HAS_SIGNAL=1
    else
        # Sinal velho (>10min), limpar e fazer scanner novo
        rm -f signals.json
        HAS_SIGNAL=0
    fi
else
    HAS_SIGNAL=0
fi

# Scanner (só se não tem sinal pendente)
if [ "$HAS_SIGNAL" -eq 0 ]; then
    SCANNER_OK=false
    for attempt in 1 2; do
        OUTPUT=$(/usr/bin/python3 crypto_bot.py 2>&1)
        if [ $? -eq 0 ]; then SCANNER_OK=true; break; fi
        echo "[$(date '+%d/%m %H:%M')] Scanner falhou (tentativa $attempt)" >> autopilot_errors.log
        sleep 10
    done
    
    if ! $SCANNER_OK; then
        echo "{\"error\": \"scanner_failed\", \"time\": \"$(date -Iseconds)\"}" > autopilot_alert.json
        exit 0
    fi
    
    if echo "$OUTPUT" | grep -q "SINAL(is)"; then
        HAS_SIGNAL=1
    fi
fi

# Executor (retry até 3x com backoff)
if [ "$HAS_SIGNAL" -eq 1 ] && [ -f signals.json ]; then
    EXEC_OK=false
    for attempt in 1 2 3; do
        EXEC_OUTPUT=$(/usr/bin/python3 binance_executor.py 2>&1)
        if [ $? -eq 0 ] && echo "$EXEC_OUTPUT" | grep -q "OCO\|executed\|TRADE EXECUTADO"; then
            EXEC_OK=true
            break
        fi
        WAIT=$((attempt * 15))
        echo "[$(date '+%d/%m %H:%M')] Executor falhou (tentativa $attempt), retry em ${WAIT}s" >> autopilot_errors.log
        sleep $WAIT
    done
    
    if $EXEC_OK; then
        {
            echo "[$(date '+%d/%m %H:%M')] ✅ TRADE EXECUTADO"
            echo "$EXEC_OUTPUT"
            echo "---"
        } >> autopilot.log
    else
        echo "{\"error\": \"executor_failed_3x\", \"time\": \"$(date -Iseconds)\"}" > autopilot_alert.json
        echo "[$(date '+%d/%m %H:%M')] ❌ Executor falhou 3x — alerta gerado" >> autopilot_errors.log
    fi
fi

# Limpar logs grandes
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
