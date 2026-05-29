# Codex Heavy Computation Delegation (26/05/2026)

## Principle
All computationally expensive forex tasks (backtests, SMC fractal scans, multi-TF analysis)
are delegated to Codex CLI (OpenAI GPT-5.5), consuming **zero Hermes/DeepSeek tokens**.

## Pipeline
```
Hermes (strategy/decision) → delegates → Codex (execution) → JSON results → Hermes reads
```

## Commands
```bash
# One-shot backtest
codex exec --skip-git-repo-check --sandbox workspace-write \
  "Run python3 ~/.hermes/scripts/backtest_crt_choch.py. Save all output to JSON."

# Batch backtests (cron no_agent)
bash ~/.hermes/scripts/codex_daily_backtests.sh
```

## Cron Job
- **ID:** `20620209b959` — Codex Daily Backtests (0 tokens Hermes)
- **Schedule:** 10:00 BRT seg-sex
- **Type:** `no_agent: true` (script runs Codex directly)
- **Script:** `codex_daily_backtests.sh`
- **Output:** `forex/codex_output/`

## Results
- Tested 26/05: backtest_crt_choch.py with GBPJPY addition — 20.9k OpenAI tokens, 0 DeepSeek
- Codex successfully: reads scripts, edits code, runs Python, saves JSON

## Wrapper
`scripts/codex_backtest.sh` — standardizes Codex invocation for any Python script:
```bash
codex_backtest.sh backtest_crt_choch.py
codex_backtest.sh smc_fractal_detector.py --pair GBPJPY --tf 15m
```
