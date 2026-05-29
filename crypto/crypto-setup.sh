#!/bin/bash
# ═══════════════════════════════════════════════
# CRYPTO MULTI-AGENT SETUP — 1 comando
# ═══════════════════════════════════════════════
set -e
echo "═══════════════════════════════════════"
echo "  CRYPTO MULTI-AGENT SETUP"
echo "═══════════════════════════════════════"

sudo apt update -qq 2>/dev/null
sudo apt install -y -qq python3 python3-pip 2>/dev/null
pip3 install --break-system-packages -q yfinance pandas numpy 2>/dev/null

CRYPTO="$HOME/.hermes/crypto"
mkdir -p "$CRYPTO"

# Baixar scripts
wget -q -O "$CRYPTO/crypto_multi_agent.py" \
  https://raw.githubusercontent.com/robertosantosuna-web/hermes-agent/master/crypto/crypto_multi_agent.py 2>/dev/null || true
wget -q -O "$CRYPTO/crypto_bot.py" \
  https://raw.githubusercontent.com/robertosantosuna-web/hermes-agent/master/crypto/crypto_bot.py 2>/dev/null || true

echo "✅ Crypto System instalado em ~/.hermes/crypto/"
echo "▶️  python3 ~/.hermes/crypto/crypto_bot.py"
