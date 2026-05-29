# Pipeline Cleanup — 27/05/2026

## Jobs pausados (sistema limpo)

| Job ID | Nome | Motivo |
|--------|------|--------|
| `3ba3d2dc5e8e` | Brain Forex Signal Scanner | Gerava sinais falsos (`PENDING_VALIDATION`, `needs_human_validation: true`, `price: "unknown"`). Placeholder — nunca executava trades. |
| `00529564acee` | Chart Pattern Study | 1.5MB de JSON/dump, zero integração com trading. |
| `1313292f5393` | Chart Pattern Degraded Study | Mesmo problema acima. |
| `48425c92b336` | Codex Forex Monitor | Consumia tokens (Ollama llama3.2) a cada 30min sem produzir ações. |

## Correções aplicadas

1. **Label "Conta REAL" → "Conta DEMO (IC Markets)"**: `forex_bot_real.py` linha 934.
2. **Codex daily backtests**: Agora rodam localmente, sem sandbox Codex. Yahoo Finance funciona fora do sandbox. Script: `codex_daily_backtests.sh` (3 backtests: CRT+CHoCH, Killzones, Chart Pattern Consolidation).
3. **Chart Pattern Consolidator**: Novo script `chart_pattern_consolidator.py`. Consolida dumps de 1.5MB em 12KB de insights. Detecta dominância de padrão por par/timeframe, gera sinais quando ≥70% dos padrões apontam mesma direção.

## Resultado
- Cron jobs: 48 → 44
- Sinais falsos/dia: ~96 → 0
- Dumps inúteis/dia: 12 (~18MB) → 1 (~12KB)
- Backtests funcionando: 0/3 → 3/3

## Sinais do Brain que estavam acumulados
6 sinais `PENDING_VALIDATION` desde 26/05, todos com `price: "unknown"`, `needs_human_validation: true`. O `analyze_pair()` no `brain_signal_generator.py` era um placeholder (linha 116-131) que nunca fazia análise real — só marcava como pendente.
