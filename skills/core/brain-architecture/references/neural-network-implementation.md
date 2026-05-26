# Neural Network Implementation — Estado Atual (23/05/2026)

Implementação completa da rede neural bi-neural com 15 cron jobs autônomos, Neural KB compartilhada, Synapse Engine de cruzamento, e Córtex integrado.

## ARQUITETURA ATUAL (v2.1)

```
SENSORES (monitor.py, forex_check.py, email)
        │
        ▼
    TÁLAMO (8 filtros) ──→ event_log.json
        │
        ├── AMYGDALA ────→ threats
        │
        ▼
    NEURAL KB (neural_knowledge_base.json) ◄── shared state
        │
        ├── N. ACCUMBENS ─→ pair_weights_live.json
        ├── HIPPOCAMPUS ──→ hippocampus_patterns.json
        ├── CEREBELLUM ───→ validation state
        ├── CHART PATTERNS → pattern_library.json (20k+)
        ├── RESEARCH ─────→ study articles
        ├── BRAIN RESEARCH → evolution proposals
        └── CÓRTEX ◄──────→ cortex_synapses.jsonl
                             ↑ cortex_sync.py (read/write bridge)
                │
                ▼
        SYNAPSE ENGINE (daily 07:00) — cross-reference all modules
```

## CRON JOBS ATIVOS (15 total, 13 no_agent)

### Núcleo Cognitivo (6)
| Job ID | Componente | Schedule | Tokens |
|--------|-----------|----------|--------|
| 853991 | Amygdala Threat Detector | */15 min | zero |
| 605042 | Cerebellum Validator | */5 min seg-sex | zero |
| 6ae254 | N. Accumbens RL | 18:30 seg-sex | zero |
| b0b848 | Hippocampus Consolidation | Dom 10:00 | zero |
| 0554b5 | Brain Research Cycle | 06:30 diário | zero |
| fcdf34 | Executive Module v2 | */5 min seg-sex | zero |

### Rede Neural (2)
| Job ID | Componente | Schedule | Tokens |
|--------|-----------|----------|--------|
| 5e4e46 | Synapse Engine | 07:00 diário | zero |
| — | Neural KB + kb_bridge | importado por módulos | zero |

### Pipeline Forex (3)
| Job ID | Componente | Schedule | Tokens |
|--------|-----------|----------|--------|
| 7b5698 | Research Collector | 03:00 diário | zero |
| 005295 | Chart Pattern Study | 08:00 seg-sex | zero |
| 89158e | Weekly Analyzer (LLM) | Dom 11:00 | ~500/sem |

### Estudo de Sistema (2)
| Job ID | Componente | Schedule | Tokens |
|--------|-----------|----------|--------|
| 7d50bd | System Study Collector | Sáb 03:00 | zero |
| 7074dc | System Study Analyzer (LLM) | Sáb 12:00 | ~500/sem |

### Infraestrutura (2)
| Job ID | Componente | Schedule | Tokens |
|--------|-----------|----------|--------|
| e566bc | Email Monitor | */5 min | zero |
| 038416 | Resiliência | */30 min | zero |

## ARQUIVOS DA REDE NEURAL

| Arquivo | Função | API |
|---------|--------|-----|
| `neural_knowledge_base.json` | KB compartilhada: estado global, sinapses, dados de todos os módulos | — |
| `scripts/synapse_engine.py` | Motor que cruza outputs dos módulos e cria sinapses | `python3 scripts/synapse_engine.py` |
| `scripts/kb_bridge.py` | Helper de integração | `from kb_bridge import write, read, query, synapse` |
| `scripts/cortex_sync.py` | Ponte Córtex↔KB | `--read`, `--write "text" --category "mod"`, `--summary` |
| `cortex_synapses.jsonl` | Log de todos os insights escritos pelo Córtex | — |
| `synapse_engine_log.jsonl` | Log de todas as consolidações neurais | — |

## CÓRTEX NA REDE NEURAL

O Córtex (Hermes Agent) é parte ativa da rede neural:

1. **Leitura no startup:** `python3 ~/.hermes/scripts/cortex_sync.py --summary` → 1 linha com sinapses, regime, ameaças, pares ativos
2. **Escrita pós-sessão:** `python3 ~/.hermes/scripts/cortex_sync.py --write "insight" --category "modulo" --confidence 0.8`
3. **Categorias válidas:** brain_research, n_accumbens, chart_patterns, amygdala, cerebellum, hippocampus, cortex
4. **Session-startup** atualizado para incluir leitura da rede neural no passo 5

## FLUXO DE SINAPSES

1. Módulo escreve descoberta na KB via `kb_bridge.write()`
2. Synapse Engine (07:00) lê TODOS os módulos
3. Detecta correlações (ex: qualidade CHoCH ↔ WR do par)
4. Cria sinapses com confidence score
5. Atualiza estado global (market regime, risk level)
6. Córtex lê via `cortex_sync.py --summary` no startup
7. Córtex escreve insights da sessão via `cortex_sync.py --write`
8. Sinapses do Córtex viram input para futuras consolidações

## DOMÍNIOS DE ESTUDO

### Forex (diário + semanal)
- Research Collector: RSS (BabyPips, ForexFactory, DailyFX, ForexLive) + YouTube + Web
- Chart Pattern Study: CHoCH, FVG, Order Blocks, Structure Breaks, Liquidity Levels (20k+ padrões/dia)
- Weekly Analyzer: LLM-driven insights (~500 tokens/semana)

### Sistema & Self (semanal, sábado)
- **OS/Infra:** Kernel, Wayland, Xvfb, Wine, systemd, disk/RAM, LVM
- **Agentes:** Ollama, Playwright, ydotool, Desktop Daemon, MT5, Python libs
- **Arquitetura:** Skills (113), Scripts (60), Neural KB, Brain components, evolução
- **Córtex:** Modelo, provider, memória, ferramentas, atividade recente

## LIMITAÇÕES DE MEMÓRIA

A memória do cérebro é distribuída em 8 silos. O fator limitante NÃO é hardware (3.7 GB RAM livre, 205 GB disco, 16 cores) mas sim software:

| Limite | Onde | Valor | Impacto |
|--------|------|-------|---------|
| `memory_char_limit` | `config.yaml` | 4000 chars | ~10 fatos no memory tool |
| `user_char_limit` | `config.yaml` | 2500 chars | Perfil do Roberto |
| Fragmentação | 8 arquivos separados | — | Nenhum sumariza o todo |
| Crescimento infinito | pattern_library.json | 20k+ padrões | Sem retenção configurada |

Para aumentar: editar `memory_char_limit` e `user_char_limit` no `~/.hermes/config.yaml`.

## INFRAESTRUTURA

- **NVMe 476 GB:** sistema (/), 54% usado
- **SDA 953 GB:** LVM configurado (data_vg: lv_home 500 GB + lv_data 452 GB), migração pendente (mkfs bloqueado pelo agente)
- **Xvfb :99:** ativo, necessário para MT5 via Wine
- **Desktop Daemon :9876:** ativo, necessário para 99Freelas

## KEY INSIGHTS

- **Zero tokens**: 13 dos 15 jobs são no_agent (scripts Python puros)
- **Self-healing**: Cerebellum detecta módulos com falha, Executive tenta recovery
- **Adaptive**: N. Accumbens atualiza scores de pares com performance real
- **Evolutionary**: Brain Research detecta gaps e propõe melhorias
- **Cross-learning**: Synapse Engine permite que Chart Patterns aprenda com Performance, Amygdala com Cerebellum, etc.
- **Córtex integrado**: Hermes Agent lê e escreve na Neural KB, session-startup inclui verificação
- **Estudo sistêmico**: 4 domínios além de forex (OS, agentes, arquitetura, córtex) com coleta semanal
