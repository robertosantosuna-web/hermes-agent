#!/bin/bash
# Crypto AutoPilot 24/7 — Scanner + Executor
# Fluxo: crypto_bot.py → signals.json → binance_executor.py → Binance

cd /home/roberto/.hermes/crypto

# Scanner: gera sinais e salva em signals.json
/usr/bin/python3 crypto_bot.py 2>&1

# Executor: se houver sinais, envia ordens para Binance
if [ -f signals.json ]; then
    /usr/bin/python3 binance_executor.py 2>&1
fi
