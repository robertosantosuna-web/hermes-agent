# Análise Multi-Agente Open-Source

Documento completo: `~/.hermes/architecture/multi-agent-analysis.md` (26KB)

## Projetos Analisados (21/05/2026)

| Projeto | Lang | Estrelas | Melhor em |
|---------|------|----------|-----------|
| Hermes Agent | Python | — | Delegate tree, toolset narrowing, MemoryManager (nossa base) |
| Edict | Python | 15.8k | State machine, Event Bus Redis, Stall detection, 3-tier memory |
| Rufio | Node.js | ~0 | 3-tier model routing, Swarm topologies, Consensus (Raft) |
| OpenClaw | TypeScript | 373k+ | Push-based completion, Steering, ACP cross-runtime |

## Decisão
NÃO instalar nenhum projeto externo. Extrair padrões e implementar sobre o Hermes Agent.
Prioridade: State machine + Event Bus (Edict) e 3-tier routing (Rufio).
