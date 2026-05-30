#!/bin/bash
# codex_daily_backtests.sh — Backtests locais (sem Codex sandbox)
# Yahoo Finance NÃO funciona no sandbox Codex (DNS bloqueado)
# → Rodamos direto na máquina local

OUTPUT_DIR="$HOME/.hermes/forex/codex_output"
mkdir -p "$OUTPUT_DIR"
DATE=$(date +%Y%m%d_%H%M)

echo "📊 Daily Backtests — $DATE"

# Backtest 1: CRT CHoCH+FVG (local)
echo "  [1/3] CRT+CHoCH Backtest..."
python3 "$HOME/.hermes/scripts/backtest_crt_choch.py" \
    > "$OUTPUT_DIR/backtest_crt_${DATE}.json" 2>&1 || echo "  ⚠️ CRT backtest falhou"

# Backtest 2: Killzones (local)
echo "  [2/3] Killzones Backtest..."
python3 "$HOME/.hermes/forex/backtest_killzones.py" \
    > "$OUTPUT_DIR/backtest_killzones_${DATE}.json" 2>&1 || echo "  ⚠️ Killzone backtest falhou"

# Backtest 3: Chart Pattern Consolidation (novo, local)
echo "  [3/3] Chart Pattern Consolidation..."
python3 "$HOME/.hermes/scripts/chart_pattern_consolidator.py" --json \
    > "$OUTPUT_DIR/chart_patterns_${DATE}.json" 2>&1 || echo "  ⚠️ Chart pattern falhou"

echo "✅ Done — $DATE"
echo ""
echo "📁 Outputs:"
ls -lh "$OUTPUT_DIR"/*${DATE}* 2>/dev/null || echo "  (nenhum output)"
