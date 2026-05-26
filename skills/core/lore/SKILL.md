---
name: lore
description: "Lore — Local Memory Engine. Armazenamento vetorial com namespaces separados (agent/brain), tiers NVMe+RAM+VRAM, busca por similaridade. Extensão além do limite de 4KB do MEMORY.md."
version: 1.0.0
---

# Lore — Local Memory Engine

Motor de memória local que estende o limite de 4KB do MEMORY.md usando armazenamento vetorial em NVMe + RAM + VRAM (GTX 1650 4GB).

## Namespaces (RIGOROSAMENTE separados)

| Namespace | Fonte | Descrição |
|-----------|-------|-----------|
| `agent` | `~/.hermes/memories/MEMORY.md` | Contexto do Hermes Agent: decisões, ferramentas, preferências |
| `brain` | `~/.hermes/brain_context.json` | Conhecimento do Cérebro: forex, neural, padrões, research |

**REGRA:** Os dois NUNCA se misturam. Search pode cruzar ou isolar, mas stores são independentes.

## Storage Tiers

| Tier | Local | Uso |
|------|-------|-----|
| NVMe | `~/.hermes/lore/{agent,brain}/store/` | Embeddings (.npy) + metadata (SQLite) |
| RAM | numpy arrays (256-dim) | Cache ativo durante search |
| VRAM | (futuro) cupy/torch | Aceleração GPU para similarity em larga escala |

## Embeddings

Vetores de 256 dimensões usando character n-grams hash → TF-IDF-like normalization.
Zero dependências além de numpy. Suficiente para <100K entradas com busca <10ms.

## Comandos

```bash
# Adicionar conhecimento
lore.py agent add "Forex Bot V5: FVG gap≥5, macro_score≥0.3, pares USDJPY/GBPUSD/EURUSD"
lore.py brain add "Iran deal → risk-on, JPY fraco, commodities fortes"

# Buscar (isolar ou cruzar)
lore.py agent search "FVG gap minimo" 5     # Só no agente
lore.py brain search "forex viés" 5         # Só no cérebro
lore.py search "estratégia trading" 5       # Ambos (resultados marcados)

# Ingestão das fontes
lore.py agent ingest    # Do MEMORY.md
lore.py brain ingest    # Do brain_context.json

# Estatísticas
lore.py agent stats
lore.py stats           # Combinado
```

## Scripts relacionados

| Script | Função | Cron |
|--------|--------|------|
| `lore.py` | Motor principal (add, search, ingest, stats) | `34bc8cfadb26` (sync horário) |
| `memory_mapper.py` | Dump da memória para Desktop + backup | `ecc0720f402d` (06:00 diário) |

## Memory Mapper (Desktop Log)

Dump diário da memória do agente para `~/Área de trabalho/hermes_memory_log.md`:

```bash
python3 scripts/memory_mapper.py full    # Dump + prune + clean
python3 scripts/memory_mapper.py stats   # Status do log
```

Backups rotativos em `~/.hermes/memory_backups/` (30 dias).

## Pitfalls

- **Namespaces NUNCA se misturam.** Se precisar cruzar, use `lore.py search` (sem namespace) — resultados vêm marcados com `[agent]` ou `[brain]`.
- **Embeddings são char n-gram, não semânticos.** TF-IDF-like captura similaridade lexical, não significado. Suficiente para busca de conhecimento técnico com terminologia consistente.
- **Memory Mapper lê `~/.hermes/memories/MEMORY.md`** — formato com entries separadas por `\n§\n`.
- **NÃO usar o Lore como substituto do MEMORY.md** — o Lore é complemento para busca e armazenamento de longo prazo. O MEMORY.md continua sendo o que o agente carrega em todo turno.
