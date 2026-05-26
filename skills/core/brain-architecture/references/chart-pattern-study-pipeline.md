# Chart Pattern Study Pipeline — v1.0

**Date:** 2026-05-23
**Components:** chart_pattern_study.py, chart_pattern_degraded.py, chart_visual_learner.py

## Pipeline Flow

```
08:00 BRT — chart_pattern_study.py (algorítmico)
  │  Detecta: CHoCH, FVG, BOS, Order Blocks, Liquidity Levels
  │  Fonte: Yahoo Finance M5/M15
  │  Output: pattern_library.json, ASCII charts
  │
  ▼
08:30 BRT — chart_pattern_degraded.py (templates + similarity)
  │  Cria templates numéricos de cada padrão
  │  Calcula similaridade entre tipos (CHoCH vs FVG, FVG vs BOS)
  │  Encontra archetypes (padrão mais representativo)
  │  Output: degraded_studies/*.json, Neural KB
  │
  ▼
(on-demand) — chart_visual_learner.py (MT5 screenshots)
  │  Captura telas do MT5 via Xvfb :99
  │  OCR extrai preços
  │  Análise visual: sentimento, densidade de velas
  │  Output: visual_library.json, screenshots/
  │  ⚠ Requer MT5 rodando no Xvfb
```

## Key Findings (First Study — 23,080 patterns)

| Pair | M5 | M15 | H1 | Archetypes |
|------|-----|-----|-----|------------|
| EURUSD | 2,475 | 707 | 188 | FVG+BOS |
| GBPUSD | 3,951 | 990 | 224 | CHoCH+FVG+BOS |
| AUDUSD | 4,946 | 1,138 | 234 | CHoCH+FVG+BOS |
| NZDUSD | 4,912 | 1,139 | 230 | CHoCH+FVG+BOS |
| USDJPY | 1,311 | 498 | 137 | FVG+BOS |

### Cross-Pattern Similarities

- **FVG ↔ BOS**: very high similarity (0.75-0.93) — share geometric candle structure
- **CHoCH ↔ BOS**: high similarity (0.60-0.90) — both involve structure breaks
- **CHoCH ↔ FVG**: moderate similarity (0.60-0.85) — CHoCH often occurs near FVG zones
- **Strongest archetype**: AUDUSD M15 FVG (0.934 avg similarity, bullish trend)

### Pattern Frequency

| Type | Count | Notes |
|------|-------|-------|
| FVG | 21,089 | Most common — every gap between candles |
| BOS | 1,933 | Structure breaks — more selective |
| CHoCH | 58 | Rare — reversal confirmation, potentially highest quality |

## Template Format

Each pattern creates a numeric template:
```json
{
  "candles": [{"rel_idx": -12..12, "o_norm": ..., "h_norm": ..., "direction": "bull"}],
  "features": {"body_sizes": [...], "wick_ratios": [...], "directions": [1/-1/0], "gaps": [...]},
  "summary": {"avg_body": ..., "trend": "bull|bear|neutral", "bullish_count": N}
}
```

Templates are compared via score_pattern_similarity() using:
- Trend match (0.3 weight)
- Body ratio match (0.25)
- Direction sequence match (0.25)
- Average body comparison (0.2)

## Neural KB Integration

Patterns flow into the Neural KB via kb_bridge:
- `chart_patterns` key updated by both studies
- Cross-references with `n_accumbens` (WR data)
- Synapse engine (07:00 daily) detects correlations

## Cron Jobs

| Job ID | Script | Schedule | Status |
|--------|--------|----------|--------|
| `005295` | chart_pattern_study.py | 08:00 seg-sex | ✅ |
| `131329` | chart_pattern_degraded.py | 08:30 seg-sex | ✅ |
| — | chart_visual_learner.py | on-demand | ⏸️ (MT5 offline) |
