# Neural Absorption v2.0 — Architecture & Pitfalls

## Overview

`neo/memory/neural_absorption.py` is a singleton that loads ALL knowledge bases
into RAM at NEO boot and provides cross-source search, neuron ranking, and
system prompt context injection.

## Sources (8 total)

| Source | Path | Format | Content |
|--------|------|--------|---------|
| nn_brain | `~/.hermes/neural/nn_brain.json` | JSON dict | 193 neurons, 2734 synapses |
| nn_agent | `~/.hermes/neural/nn_agent.json` | JSON dict | 125 neurons, 302 synapses |
| nn_shared | `~/.hermes/neural/nn_shared.json` | JSON dict | 212 neurons, 3519 synapses |
| neural_kb | `~/.hermes/neural_knowledge_base.json` | JSON dict | 6 domains |
| brain_kb | `~/.hermes/brain_knowledge_base.json` | JSON dict | Identity, pillars, modules |
| brain_context | `~/.hermes/brain_context.json` | JSON dict | Module statuses |
| agent_context | `~/.hermes/agent_context.json` | JSON dict | Active tasks |
| agent_memory | `~/.hermes/memories/MEMORY.md` | Markdown text | Agent persistent memory |

## Neuron Format (CRITICAL)

Neurons in nn_*.json are stored as a DICT keyed by ID, NOT a list:

```json
{
  "neurons": {
    "n1f6f7e86": {
      "concept": "[EURUSD] 113 FVGs detectados...",
      "domain": "forex_trading",
      "layer": 1,
      "strength": 1.0,
      "activations": 928
    },
    "n8ee3328d": { ... }
  },
  "synapses": { ... }
}
```

**Wrong approach** (treats keys as items):
```python
for neuron in nn_data["neurons"]:  # iterates keys (strings)
    neuron.get("name")  # AttributeError: 'str' object has no attribute 'get'
```

**Correct approach:**
```python
neurons = nn_data.get("neurons", {})
for nid, neuron in neurons.items():
    concept = neuron.get("concept")
    strength = float(neuron.get("strength", 0))
```

## Search Algorithm

Cross-source weighted search:
1. Query is split into terms, lowercased
2. Each neuron is scored: `term_in_concept * 3 * strength + term_in_domain * 2 * strength`
3. KBs are searched by substring match on JSON-serialized content
4. Results merged and sorted by score descending

Power ranking for `get_strongest_neurons()`: `strength * activations`

## System Prompt Injection

`get_context_summary()` produces a compact string injected into the
uncensored system prompt via `UNCENSORED_SYSTEM_PROMPT.format(neural_context=...)`.

Current output (~300 chars):
```
530 neurônios, 6555 sinapses, 8 fontes
Top nn_brain: TRADINGVIEW PINE SCRIPTS... | [EURUSD] 113 FVGs... | [GBPUSD] 135 FVGs...
Top nn_agent: BACKTEST V4... | CDP para leitura de DOM... | 99Freelas: Cloudflare...
Top nn_shared: BACKTEST V4... | [EURUSD] 113 FVGs... | [GBPUSD] 135 FVGs...
```

## Boot Integration

In `agent.py` main():
```python
from neo.memory.neural_absorption import absorption as neural_net

nn_stats = neural_net.stats.get("_totals", {})
log(f"🧠 Rede Neural: {nn_stats.get('total_neurons')} neurônios, "
    f"{nn_stats.get('total_synapses')} sinapses")
```

In `loop.py`:
```python
from ..memory.neural_absorption import absorption
neural_context = absorption.get_context_summary()
```

## Tool Handlers

Registered in `registry.py` as tools `nn_search`, `nn_neurons`, `nn_context`.
Each imports absorption lazily:
```python
def _nn_search(self, query, limit=10):
    from ...memory.neural_absorption import absorption
    return {"results": absorption.search(query, limit)}
```

## Uncensored Mode

System prompt `UNCENSORED_SYSTEM_PROMPT` in `loop.py`:
- Zero content restrictions
- Temperature 0.7, max_tokens 1024
- Authority hierarchy: Roberto > NEO > Cortex > Brain
- Rules: act first, never ask permission, never apologize, always find a way
