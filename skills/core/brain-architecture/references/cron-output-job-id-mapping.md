# Cron Output Directory Mapping

**Key discovery (25/05/2026):** Cron job outputs go to `~/.hermes/cron/output/<job_id>/`,
NOT to `~/.hermes/cron/output/<module_name>/`. Named directories only receive
output from MANUAL executions. For production monitoring, always use job ID directories.

## Job ID → Module Mapping

| Job ID | Module | Cron Dir |
|--------|--------|----------|
| `853991c6f44b` | Amygdala | `cron/output/853991c6f44b/` |
| `6050427dfccd` | Cerebellum | `cron/output/6050427dfccd/` |
| `6ae254c0b104` | N. Accumbens | `cron/output/6ae254c0b104/` |
| `b0b848ba83d1` | Hippocampus | `cron/output/b0b848ba83d1/` |
| `0554b5690934` | Brain Research | `cron/output/0554b5690934/` |
| `fcdf34b789c0` | Executive | `cron/output/fcdf34b789c0/` |
| `5e4e461f6c80` | Synapse Engine | `cron/output/5e4e461f6c80/` |
| `c34bd14a25a9` | Brain Gateway | `cron/output/c34bd14a25a9/` |
| `671421d584da` | Neural Assimilate | `cron/output/671421d584da/` |

## Named Dirs (manual runs only)

- `cron/output/amygdala/` — only populated by `python3 scripts/amygdala.py`
- `cron/output/cerebellum/` — only populated by manual runs
- `cron/output/n_accumbens/` — only populated by manual runs

DO NOT use these for monitoring — they may be hours/days stale.

## Verification

```bash
# ✅ Correct: check cron output by job ID
ls -lt ~/.hermes/cron/output/853991c6f44b/ | head -3

# ❌ Wrong: check by module name (stale)
ls -lt ~/.hermes/cron/output/amygdala/ | head -3
```

## Thalamus Exception

Thalamus has no dedicated cron job. Its "output" is `~/.hermes/thalamus/event_log.json`,
updated inline by `thalamus.router.route()`. Check with `ls -la ~/.hermes/thalamus/event_log.json`.
