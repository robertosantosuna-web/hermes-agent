# System Audit 2026-05-28 — Cleanup Results

**Date:** 28/05/2026  
**Skill:** `brain-architecture`

## Before (Fragmented)

| Metric | Count |
|--------|-------|
| Cron jobs total | 84 |
| Cron jobs active | 13 |
| Python scripts | ~150 in scripts/ |
| Bridge files | 8 JSON files |
| "Consciousness" systems | 3 (NEO v2, Neural Legacy, Brain Executive) |
| Skills | ~100 |

## After (Consolidated)

| Metric | Count |
|--------|-------|
| Cron jobs TOTAL | 13 (71 old REMOVED) |
| Brain agents | 13 `.py` files in `~/.hermes/brain/` |
| Bridge files | 1 (`thalamus.json`) |
| Consciousness | 1 (Master/Hermes orchestrating 8 sub-agents) |

## 13 Active Cron Jobs

| # | Name | Schedule | Script |
|---|------|----------|--------|
| 1 | Amígdala — Threat Detector | */5 * * * * | brain/amygdala.py |
| 2 | Lobo Frontal — Planner | */30 * * * * | brain/lobo_frontal.py |
| 3 | Área de Broca — Scanner | */30 * * * * | brain/area_broca.py |
| 4 | Tálamo — Sync | */2 * * * * | brain/thalamus.py |
| 5 | Gateway Guard | */10 * * * * | brain/gateway_guard.py |
| 6 | Meta Observer | */15 * * * * | brain/meta_observer.py |
| 7 | N. Accumbens — RL | 0 */4 * * * | brain/n_accumbens.py |
| 8 | Hipocampo — Patterns | 0 */6 * * * | brain/hippocampus.py |
| 9 | Ollama Keep-Alive | */5 * * * * | brain/ollama_keepalive.py |
| 10 | Córtex Visual — Forex | */15 * * 1-5 | brain/cortex_visual.py |
| 11 | AutoPilot — Gestão | */3 * * 1-5 | forex_autopilot.py |
| 12 | MindCoach Collect | */15 * * * * | mindcoach_collectors.py |
| 13 | Motor Local — MT5 Reader | */1 * * * * | brain/motor_local.py |

## Deleted Jobs (71 removed)

All old cron jobs from the fragmented architecture were permanently REMOVED (not paused).
Includes: scalpings, killzone analysis, chart pattern studies, brain research, synapse engine,
neural triggers, NN engine, calendar monitors, mental check-ins, freela scanners, gateway watchdog
(old version), and all duplicate forex analysis jobs.

## ⚠️ PITFALL: Never Recreate Old Jobs

The 71 old cron jobs no longer exist. Their scripts are archived in `~/.hermes/archive/`.
If a functionality is needed, extend an existing brain agent or create a new one in `~/.hermes/brain/`.
