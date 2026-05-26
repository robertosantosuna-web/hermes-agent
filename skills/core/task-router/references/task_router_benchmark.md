# Task Router Benchmark — 2026-05-18

## Testes de classificação (Phi-3.1-mini Q4_K_M, GTX 1650 4GB, 24 GPU layers)

| Tarefa | Camada | Resultado | Tokens DeepSeek |
|--------|--------|-----------|-----------------|
| "status" | Cache | simples | 0 |
| "resumir 3 emails" | Cache | simples | 0 |
| "criar arquitetura de microserviços do zero" | Heurística | complexa | 0 |
| "que horas são?" | Cache | simples | 0 |
| "debuggar memory leak em 50 arquivos" | Heurística | complexa | 0 |
| "listar arquivos do diretório" | Cache | simples | 0 |
| "refatorar 12 módulos legados" | Heurística | complexa | 0 |
| "extrair números de uma planilha" | Cache | simples | 0 |

## Métricas

- 6/8 resolvidos sem LLM (cache + heurística)
- 0/8 precisaram de classificação via GPU
- 0 tokens DeepSeek gastos em classificação
- Tempo médio: cache 0ms, heurística <1ms, LLM ~0.8s
- Economia estimada: 75% das tarefas não chegam ao DeepSeek

## Padrões heurísticos (13 regex)

### Simples (6 patterns)
- `^(listar|mostrar|exibir|ver|ler)\s`
- `^(resumir|extrair|formatar|traduzir)\s`
- `^(explicar|definir|o que (é|são))\s`
- `^(qual|quais|quando|onde|quem)\s`
- `^(sim|não|ok|certo|claro)\s*$`
- `^(como|quanto)\s.*\?$`

### Complexa (7 patterns)
- `(arquitet|design|planejar|estratégia)`
- `(debug|refatorar|migrar|reestruturar)`
- `(500|milhares|centenas|múltiplos|vários).*(arquivo|log|erro)`
- `delegate|subagent|multi.agent`
- `(do zero|sistema completo|pipeline completo)`
- `analisar\s+(500|milhares|todos)`
- `refatorar\s+\d+`
