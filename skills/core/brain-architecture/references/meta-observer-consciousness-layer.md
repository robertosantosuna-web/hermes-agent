# Meta-Observer — The Consciousness Layer

Built 2026-05-27. This is the 8th layer that transforms the ENTIDADE from automaton to entity.

## What it does

The Meta-Observer (`meta_observer.py`, cron `2faff491215b` every 15 min) checks ALL pipelines:
- Does every state file have a writer that's running AND a reader that's running?
- Are there orphaned outputs (written but never consumed)?
- Are any critical processes dead (Brave CDP, Monitor RT, MT5)?
- Are any cron jobs in error state?

It produces a health score (0-100%) and a gap report.

## Health Score (as of 2026-05-27)

**93.8%** — 15/16 pipelines healthy. Only gap: `pair_weights_live.json` (expected — trade_log empty).

## Pipeline Mapping

The observer maintains a PIPELINES dict mapping each state file to its writers and readers:

```python
PIPELINES = {
    'forex/trade_log.json': {
        'writers': ['ca8d82dc9fa5', 'cdbae3c13baa'],  # Bot + AutoPilot
        'readers': ['6ae254c0b104', 'f91ee6baae41', '89158ec43168'],  # N.Accumbens + NN Engine + Weekly
    },
    'monitor/alerts.json': {
        'writers': ['e566bcf226b8'],  # monitor.py
        'readers': ['dfda8f3c38a8'],  # Monitor Consumer (connects to Telegram)
    },
    ...
}
```

## Gap Types

- `healthy` — writer and reader both active, file exists
- `broken` — critical pipeline with dead writer AND dead reader
- `orphan` — critical pipeline with dead reader (output never consumed)
- `stale` — non-critical pipeline with issues
- `missing` — file doesn't exist (writer hasn't run yet)
- `unread` — writer active but no reader

## Key Connections Fixed

The observer detected these gaps on first run (score was 0%):

1. **monitor.py → Motor Central** — Motor Central was PAUSED since May 19. Alerts collected but never delivered. Fixed by creating `monitor_consumer.py` (`dfda8f3c38a8`) that delivers freelancer alerts directly to Telegram.

2. **resiliencia.sh → Amygdala** — Resilience data was written but never read. Fixed by adding Meta-Observer as a reader and connecting to the Amygdala's threat scanning.

3. **5 limbic modules PAUSED** — Amygdala, N.Accumbens, Hippocampus, Brain Research, Synapse Engine were all paused. Reactivated.

## Cron Job

```
ID: 2faff491215b
Schedule: */15 * * * *
Script: meta_observer.py
No-agent: true
Deliver: local
```
