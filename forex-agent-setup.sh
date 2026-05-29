#!/bin/bash
# FOREX MULTI-AGENT SETUP — 1 comando
set -e
echo "═══════════════════════════════════════"
echo "  FOREX MULTI-AGENT SETUP"
echo "═══════════════════════════════════════"
sudo apt update -qq
sudo apt install -y -qq python3 python3-pip curl git 2>/dev/null
pip3 install --break-system-packages -q yfinance pandas numpy 2>/dev/null

HERMES="$HOME/.hermes"
mkdir -p "$HERMES"/{scripts,forex,skills,brain}

# Baixar scripts do repositório
echo "Baixando sistema multi-agente..."
wget -q -O "$HERMES/scripts/multi_agent.py" https://raw.githubusercontent.com/robertosantosuna-web/hermes-agent/master/scripts/multi_agent.py 2>/dev/null || true
wget -q -O "$HERMES/scripts/fvg_quality.py" https://raw.githubusercontent.com/robertosantosuna-web/hermes-agent/master/scripts/fvg_quality.py 2>/dev/null || true
wget -q -O "$HERMES/scripts/self_learning.py" https://raw.githubusercontent.com/robertosantosuna-web/hermes-agent/master/scripts/self_learning.py 2>/dev/null || true
wget -q -O "$HERMES/scripts/forex_bot.py" https://raw.githubusercontent.com/robertosantosuna-web/hermes-agent/master/scripts/forex_bot.py 2>/dev/null || true

echo "✅ Sistema instalado em ~/.hermes/"
echo "▶️  Para iniciar: cd ~/.hermes/scripts && python3 forex_bot.py"
