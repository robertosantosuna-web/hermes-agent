#!/bin/bash
# Crypto Bot AutoPilot — chamado pelo cron a cada 5 min
# Opera 24/7 com seleção dinâmica de pares

cd /home/roberto/.hermes/crypto
/usr/bin/python3 crypto_bot.py 2>&1
