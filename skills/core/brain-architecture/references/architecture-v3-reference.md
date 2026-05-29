# ENTIDADE v3.0 — Reference Card
## Implemented: 28/05/2026

### Quick Status
```bash
python3 ~/.hermes/brain/thalamus.py status    # Health, active modules, alerts
python3 ~/.hermes/brain/thalamus.py alerts    # Active alerts only
```

### Agents (13 Python files in ~/.hermes/brain/)
| Agent | Script | Cron | Schedule |
|-------|--------|------|----------|
| Amígdala | amygdala.py | e921345f4906 | */5 * * * * |
| Lobo Frontal | lobo_frontal.py | 2ca98249a0f1 | */30 * * * * |
| Área Broca | area_broca.py | 1ce5e52db6ed | */30 * * * * |
| Tálamo | thalamus.py | 525fd2b8068b | */2 * * * * |
| Meta Observer | meta_observer.py | 69287b61a7b9 | */15 * * * * |
| Gateway Guard | gateway_guard.py | 68855967829d | */10 * * * * |
| N. Accumbens | n_accumbens.py | 64997c0ee8ec | 0 */4 * * * |
| Hipocampo | hippocampus.py | 43ab0775dac5 | 0 */6 * * * |
| Córtex Visual | (forex_bot_multi.py) | 03cb4dc7667e | */15 * * 1-5 |
| AutoPilot | (forex_autopilot.py) | 328e513a2e2d | */5 * * 1-5 |
| MindCoach | (mindcoach_collectors.py) | ee26cb3f04ef | */15 * * * * |
| Fechar Sexta | (forex_fechar_sexta.sh) | 46f638056d09 | 0 16 * * 5 |
| Ollama KA | ollama_keepalive.py | ad1c934ffa1b | */5 * * * * |

### Tálamo API (thalamus.py)
```python
import thalamus
thalamus.send_message(source, target, type, content, priority)
thalamus.log_event(event_type, source, data, severity)
thalamus.raise_alert(level, title, description, source)
thalamus.update_state(key, value)
thalamus.broadcast_to_workspace(content, priority, source)
thalamus.add_discovery(domain, insight, confidence, source)
```

### SONA-lite API (sona_lite.py)
```python
from sona_lite import SONALite
sona = SONALite()
sona.observe({'domain': 'forex', 'action': 'BUY EURUSD', 'pnl': 15.2, 'context': 'FVG+CRT London Open'})
sona.best_action('forex_eurusd_buy')
sona.get_stats()  # {'total_patterns': N, 'success_rate': 0.XX, 'by_domain': {...}}
```

### Working Memory API (working_memory.py)
```python
from working_memory import WorkingMemory
wm = WorkingMemory()
wm.store('last_trade', 'EURUSD BUY @1.0850', ttl_minutes=30)
wm.recall('last_trade')
wm.get_context()  # all active items as string for prompt injection
```

### Pitfalls
- 71 old cron jobs are PAUSED, never resume them
- thalamus.json can have MAX 500 events and 200 messages
- Cerebellum is on-demand only, no cron
- Cortex Visual and Motor still use legacy forex scripts (consolidation pending)
- NEO v2.0 is stopped — its role is now interface only
