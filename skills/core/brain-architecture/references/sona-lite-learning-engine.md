# SONA-lite — Motor de Aprendizado Contínuo

## Visão Geral

SONA-lite é um motor de aprendizado por reforço simplificado para a ENTIDADE v3.0.
Pipeline: Retrieve → Judge → Distill → Consolidate + Q-learning tabular.

## Pipeline

```
AÇÃO EXECUTADA (trade, proposta, comando)
    │
    ▼
RETRIEVE — Busca cosine similarity no Pattern Store
    │
    ▼
JUDGE — Classifica: success / failure / partial
    │
    ▼
DISTILL — Extrai aprendizado: "[domínio] ação → outcome"
    │
    ▼
CONSOLIDATE — Deduplica, reforça pesos, atualiza Q-table
```

## Q-Learning

Q(s,a) += α * [r + γ * max(Q(s')) - Q(s,a)]
- α = 0.1 (learning rate)
- γ = 0.9 (discount factor)
- r = +1.0 (success), -1.0 (failure), 0 (partial)

## Pattern Store

Cada padrão armazenado:
- context: descrição do contexto
- action: ação tomada
- outcome: success | failure | partial
- reward: valor numérico (-1.0 a +1.0)
- lesson: string compacta "[domínio] ação → outcome"
- weight: peso no consolidation (0.0 a 1.0)
- count: vezes observado
- timestamp: última ocorrência

## Integração

- Local: `~/.hermes/brain/sona_store.json`
- Chamado por cada sub-agente após executar ação
- Master consulta Q-table antes de decisões: `sona.best_action(state)`
- N. Accumbens usa SONA-lite para ajustar pesos de pares forex
