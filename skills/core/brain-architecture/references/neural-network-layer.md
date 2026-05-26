# Neural Network Layer — Session Implementation Notes (23/05/2026)

## Architecture

The Neural Network layer connects all brain modules through a shared Knowledge Base
and a Synapse Engine that cross-references discoveries.

## Key Files

| File | Purpose |
|------|---------|
| `~/.hermes/neural_knowledge_base.json` | Shared JSON knowledge base |
| `~/.hermes/scripts/neural_kb.py` | KB init/read/write/query API |
| `~/.hermes/scripts/synapse_engine.py` | Cross-module consolidation engine |
| `~/.hermes/scripts/kb_bridge.py` | Import helper for module integration |
| `~/.hermes/synapse_engine_log.jsonl` | Synapse engine execution log |

## Data Flow

```
Module output → kb_bridge.write() → Neural KB
                                      ↓
Synapse Engine (daily 07:00) → reads all modules → creates synapses
                                      ↓
Module decision ← kb_bridge.query() ← Neural KB
```

## Cross-Module Synapses Created (first run)

1. Pattern→Performance: 4 synapses linking chart pattern quality to pair WR
2. Market regime detection: "choppy" at 70% confidence (low vol, mixed WR)
3. 6/7 modules active (weekly analyzer not yet run)

## Integration Pattern

Each module adds these lines after its main logic:
```python
try:
    from kb_bridge import write, read, query, synapse
    write('module_name', {'key': value, ...})
    regime = query('market_regime')
    if regime != 'unknown':
        synapse('from', 'to', 'insight', confidence=0.8)
except ImportError:
    pass  # KB not available yet, no problem
```

## Market Regime Detection

Based on active pair ratio:
- ≥60% pairs ACTIVE/PRIORITY → "trending"
- 30-60% → "ranging"  
- <30% → "choppy"
- High CHoCH count in trending → "transitioning"

## Pitfalls

- `read_file` returns content with line number prefixes that break `json.loads()`.
  Use `terminal` with `python3 -c "import json; ..."` for JSON operations instead.
- `youtube-transcript-api` v1.2.4 uses `.fetch()`, NOT `.get_transcript()`.
  Install: `pip install --break-system-packages youtube-transcript-api`
