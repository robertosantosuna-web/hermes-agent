#!/bin/bash
# TV Chart Scanner — Screenshot de todos os pares M15 a cada 30 min.
# Salva em ~/.hermes/forex/charts/tradingview/ para estudo visual.
# Zero tokens, roda via cron no_agent.

PAIRS="EURUSD GBPUSD AUDUSD NZDUSD USDJPY"
ANALYZER="$HOME/.hermes/scripts/tv_chart_analyzer.py"

for pair in $PAIRS; do
    python3 "$ANALYZER" --pair "$pair" --tf M15 --screenshot 2>/dev/null
    sleep 1
done

echo "TV Chart Scanner: $(date +%H:%M) — 5 pairs captured"
