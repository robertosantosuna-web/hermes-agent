# Brain ↔ Bot Bridge — Reference

**Created:** 2026-05-25 | **Version:** 1.0

## Architecture

```
brain_gateway.py (cron */2 min)
        ↓
brain_outbox.json  ←  weekly bias, macro context, alerts
        ↓
forex_bot_real.py  ←  load_weekly_bias(), read_user_commands()
        ↓
Trades executed    →  notify_trade() → brain_inbox.json
        ↓
executive/brain.py (cron */5 min) → processes inbox, learns patterns
```

## Key Files

| File | Role |
|------|------|
| `scripts/brain_bot_bridge.py` | Bridge module: read_brain_signals(), read_user_commands(), notify_trade() |
| `brain_outbox.json` | Brain → Bot: viés semanal, macro context, alerts |
| `brain_inbox.json` | Bot → Brain: trades executados, status updates |
| `brain_gateway_inbox.json` | User → Brain: commands (pause, resume, close_all, status) |
| `neural_sync.json` | Sync channel for neural assimilate |
| `forex/weekly_bias.json` | Local fallback if brain gateway offline |

## Integration Points in forex_bot_real.py

1. **load_weekly_bias()**: Tries brain gateway first → falls back to JSON file
2. **run_analysis() start**: Checks brain_gateway commands (pause/close_all/status)
3. **After trade execution**: notify_trade() writes to brain_inbox.json

## Trade Notification Format

```json
{
  "type": "trade_opened",
  "pair": "USD/JPY",
  "direction": "BUY",
  "entry": 158.860,
  "sl": 158.810,
  "tp": 159.010,
  "wr": 73.3,
  "tid": "trade_20260525_001"
}
```

## Pitfalls

- Brain gateway offline doesn't block the bot — all brain calls wrapped in try/except
- Symlinks in scripts/executive/ break cron jobs — use real files
- Cron output directories use job IDs, not module names
- Neural assimilate now runs every 4H (0 */4 * * *), not every 10 min
