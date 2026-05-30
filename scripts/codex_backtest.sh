#!/bin/bash
# codex_backtest.sh — Delegates backtests to Codex (OpenAI tokens, not Hermes)
# Usage: codex_backtest.sh <script> [args...]
# Example: codex_backtest.sh backtest_crt_choch.py --days 30 --pairs GBPJPY,USDJPY

SCRIPT="${1:-backtest_crt_choch.py}"
shift 2>/dev/null || true
ARGS="$*"
OUTPUT_DIR="$HOME/.hermes/forex/codex_output"
mkdir -p "$OUTPUT_DIR"
OUTPUT="$OUTPUT_DIR/$(basename "$SCRIPT" .py)_$(date +%Y%m%d_%H%M).json"

echo "🤖 Codex running: $SCRIPT $ARGS"
codex exec --skip-git-repo-check --sandbox workspace-write \
  "Run python3 ~/.hermes/scripts/$SCRIPT $ARGS. Save ALL output (stdout + stderr) to $OUTPUT as JSON with keys: 'result', 'console', 'timestamp'. Don't ask questions, just execute." 2>&1

echo "✅ Output: $OUTPUT"
python3 -c "import json; d=json.load(open('$OUTPUT')); print(json.dumps(d.get('result', d), indent=2)[:2000])" 2>/dev/null || cat "$OUTPUT" 2>/dev/null | head -20
