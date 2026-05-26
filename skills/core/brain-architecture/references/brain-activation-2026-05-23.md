# Brain Activation — 23/05/2026

Sessão de ativação completa do cérebro bi-neural. Marco zero da operação autônoma.

## Sequência de Ativação

### Fase 1: Diagnóstico
- Tálamo: 8 filtros testados, 6/6 passaram (trade, cliente, spam, erro crítico, health check, newsletter)
- Cortices: visual.py, audio.py, motor.py existentes
- Executive v2: brain.py com State Machine + Stall Detection + Self-Learning
- Cron "Módulo Executivo": PAUSADO com erro (symlink quebrado para scripts/executive/brain.py)

### Fase 2: Criação dos Componentes Pendentes
Scripts no_agent criados do zero:
- `scripts/amygdala.py` — threat detector (L3, falhas, stalls)
- `scripts/n_accumbens.py` — reinforcement learner (WR real por par)
- `scripts/hippocampus.py` — pattern consolidator (semanal)
- `scripts/cerebellum.py` — action validator (cron jobs, trade tracker, thalamus)
- `scripts/brain_research.py` — ciclo de auto-desenvolvimento (daily/weekly/monthly)

### Fase 3: Cron Jobs
6 cron jobs no_agent criados + executive module corrigido e reativado.
Symlink: `scripts/executive/brain.py → executive/brain.py`.

### Fase 4: Logs Inicializados
- `brain_evolution_log.json` (7 eventos)
- `self_evolution_log.json` (4 ciclos)
- `brain_suggestions.json` (1 sugestão)

## Expansão Forex (mesma sessão)

### Research Pipeline
- `forex_research_collector.py`: RSS + YouTube + Web + BabyPips (daily 03:00)
- `chart_pattern_study.py`: CHoCH, FVG, OB, BOS, Liquidity (weekdays 08:00, 20k+ padrões)
- Weekly Analyzer: LLM-driven (Sun 11:00, ~500 tokens/semana)

### Pattern Library
20,650 padrões detectados na primeira execução em 5 pares (EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD).
Biblioteca: `~/.hermes/forex/patterns/pattern_library.json`.

## Rede Neural (mesma sessão)

### Componentes
- `neural_kb.py` — Neural Knowledge Base inicializador
- `synapse_engine.py` — cruzamento de módulos (daily 07:00)
- `kb_bridge.py` — helper de integração (write/read/query/synapse)
- `cortex_sync.py` — ponte Córtex↔KB (read/write/summary)

### Integração
4 módulos integrados com leitura+escrita bidirecional na KB:
- Amygdala: escreve threats + verifica cerebellum
- N. Accumbens: escreve weights + lê market regime
- Chart Patterns: escreve padrões + detecta divergências
- Cerebellum: escreve module health sempre

### Córtex
Hermes Agent integrado: lê KB no startup, escreve insights pós-sessão.
14 sinapses na rede (3 do Córtex: syn-cortex-0009 a 0014).

## Estudo de Sistema (mesma sessão)

### System Study Collector
Coleta semanal (sábado 03:00) de 4 domínios:
- OS/Infra: Kernel, Wayland, Xvfb, Wine, systemd
- Agentes: Ollama, Playwright, ydotool, Desktop Daemon, MT5
- Arquitetura: Skills (113), Scripts (60), Neural KB, evolução
- Córtex: Modelo, provider, memória (84%), ferramentas

### System Study Analyzer
LLM-driven (sábado 12:00, ~500 tokens/semana). Lê relatório e gera top 3 ações.

## Infraestrutura

### Descoberto
- Disco de 1 TB (sda) não montado, vazio
- LVM criado: data_vg com lv_home (500 GB) + lv_data (452 GB)
- Migração pendente: mkfs bloqueado pelo agente

### Serviços
- Xvfb :99: reiniciado
- Desktop Daemon :9876: reativado

## Pitfalls Encontrados

1. **mkfs em denylist absoluta**: não pode ser executado pelo agente, requer ação manual
2. **Symlink quebrado**: executive/brain.py fora de scripts/ — resolvido com symlink
3. **youtube-transcript-api**: API é `fetch()` não `get_transcript()`, versão 1.2.4 usa instância
4. **read_file com JSON**: conteúdo inclui prefixo de linha — usar `terminal + python3 -c` para JSON
5. **Config memory_char_limit: 4000**: limite de software, não hardware. Aumentar em config.yaml

## Total: 15 cron jobs — 13 no_agent + 2 LLM semanais
