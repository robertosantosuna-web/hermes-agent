# ENTIDADE v4.0 — Neural Network Architecture
## Applied 28/05/2026 — Synthesized from Council of 4 IAs

## 6-Layer Architecture

1. **Governance** — constitution.yaml, policy_engine, consent_scope, risk_limits, audit_ledger
2. **Perception** — MT5, Telegram, Email, Browser, APIs, Files
3. **Neural Network** — Encoder→Attention→Decoder with EWC + Replay Buffer
4. **Execution** — Isolated from brain (trade_executor, browser_agent)
5. **Observability** — logs.jsonl, dashboard, healthcheck, anomaly_detector
6. **Memory** — N0(Working)→N1(Session)→N2(Episodic)→N3(Semantic/FAISS)→N4(Procedural)→N5(KG)

## Continuous Learning (No Catastrophic Forgetting)

Three pillars:
- **EWC** (Elastic Weight Consolidation): Fisher Information Matrix protects critical weights
- **Replay Buffer**: 10K experiences, 50% recent + 50% old interleaved sampling
- **Meta-Learning**: Per-parameter learning rate adjusted by Fisher importance

## Files Created

18 new files in ~/.hermes/{nn,governance,safety,observability}/
Key: nn/continuous_learner.py, governance/policy_engine.py, safety/rollback_manager.py
Document: ~/.hermes/plans/entidade-v4-rede-neural.md

## ⚠️ Cron Bug Fixed

ERRADO: */15 * * * 1-5  → days 1-5 of month
CERTO:  */15 * * * * 1-5 → Monday-Friday (5 fields before weekday!)
