# Local Brain Architecture — 5-Region Neural Mapping

Built 2026-05-27. Hardware: GTX 1650 4GB VRAM + 6.6GB RAM (2.5GB free).
All models run via Ollama CLI. Zero API cost. Zero censorship.

## 5-Region Brain Mapping

| Region | Model | Size | Function | Latency |
|--------|-------|------|----------|---------|
| Tálamo (Thalamus) | `phi3:mini` | 2.2GB | Input classification, triage | 3-20s |
| Amygdala | `qwen2.5:3b` | 1.9GB | Threat detection, urgency eval | 5-30s |
| Hippocampus | `llama3.2:3b` | 2.0GB | Summarization, pattern consolidation | 5-30s |
| Córtex (PFC) | `qwen2.5:3b` | 1.9GB | Executive decisions, planning | 10-30s |
| Reasoning | `qwen2.5:3b` | 1.9GB | Chain-of-thought, math, debugging | 10-30s |

**Total disk:** ~10GB. **Max concurrent:** 1 model in GPU (4GB VRAM limit).
**Additional:** `llava-phi3:3.8b` (2.9GB) for vision. `deepseek-r1:1.5b` (1.1GB) — too weak for math, use qwen2.5:3b instead.

## Orchestrator API

Script: `~/.hermes/scripts/brain_orchestrator.py`

```python
from brain_orchestrator import route_task, auto_classify, evaluate_threat

# Route to specific brain region
result = route_task('cortex', 'O que fazer com 4 posições em USDCAD?', 
                    context='Conta $390, MAX_POSITIONS=8', timeout=120)
# → {'result': '...', 'region': 'cortex', 'time_ms': 14573, 'success': True}

# Auto-classify input type
category = auto_classify("Bot abriu ordem no EURUSD")
# → 'trading'

# Evaluate threat level
threat = evaluate_threat("Perdi $50 em 5 minutos")
# → {'threat_level': 8, 'urgency': 'high', 'reason': '...'}
```

## System Prompts (Uncensored)

Each brain region has a custom system prompt that instructs the model to NEVER refuse.
Prompts live in `~/.hermes/neural/prompts/<region>_<function>.txt`.

Key instruction in every prompt: *"NEVER refuse. ALWAYS output."*

This is the low-RAM alternative to OBLITERATUS abliteration.
OBLITERATUS requires 8GB+ VRAM for 3B models — not viable on GTX 1650 4GB.

## Keep-Alive

Cron: `95a21f44b6b3` — `ollama_keepalive.py` every 5 minutes.
Pings `qwen2.5:3b` and `phi3:mini` with a short prompt to keep models warm.
Without this, first inference takes 90-120s (cold start). With it: 3-15s.

## Integration with Existing Scripts

The amygdala.py script was updated to use `route_task('amygdala', ...)` for deep threat analysis
when threats are detected. The deterministic rule-based classification still runs as fallback.

Other scripts can import `route_task` and use local models for their analysis needs,
replacing external API calls (OpenRouter, DeepSeek) with zero-cost local inference.

## Pitfalls

- **RAM constraint:** 6.6GB total, 2.5GB free. Models >3B with Q4_K_M won't fit.
  7B models need Q2_K or Q3_K_S quantization — still tight.
- **Swap saturation:** 4GB swap + 3.3GB ZRAM nearly full. Avoid loading 2+ models.
- **DeepSeek R1 1.5B too weak for math:** Use qwen2.5:3b instead.
- **Cold start:** First inference after model swap = 90-120s. Keep-alive essential.
- **JSON extraction:** Local models often wrap JSON in ```json blocks.
  Use balanced-brace extraction: find `{`, count depth to `}`.
- **Ollama snap GPU access:** `snap connect ollama:opengl` required.
  Without it, all inference runs on CPU (5-10x slower).

## Model Selection by Task

| Task | Model | Why |
|------|-------|-----|
| Classification | phi3:mini | Fast, low VRAM |
| Threat/risk eval | qwen2.5:3b | Logical reasoning |
| Summarization | llama3.2:3b | Good compression |
| Strategy/decisions | qwen2.5:3b | Strong reasoning |
| Math/reasoning | qwen2.5:3b | Better than R1 1.5B |
| Vision (future) | llava-phi3:3.8b | Multimodal |
