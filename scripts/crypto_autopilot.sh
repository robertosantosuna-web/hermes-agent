#!/bin/bash
# Crypto AutoPilot 24/7 v2 — Hyperliquid feed + Scanner + Executor

cd /home/roberto/.hermes/crypto

# Scanner com feed Hyperliquid + Yahoo fallback
/usr/bin/python3 crypto_bot.py 2>&1

# Executor: envia ordens para Binance se houver sinais
if [ -f signals.json ]; then
    /usr/bin/python3 binance_executor.py 2>&1
fi
