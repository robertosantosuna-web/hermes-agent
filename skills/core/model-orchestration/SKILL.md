---
name: model-orchestration
description: "Orquestração de modelos LLM: multi-provider, fallback automático, rotação de modelos, compressão contextual, otimização de tokens e execução híbrida local/cloud."
version: 1.0.0
author: Roberto Rodrigues
license: MIT
metadata:
  hermes:
    tags: [llm, orchestration, openrouter, fallback, providers, optimization]
    related_skills: [life-os, llama-cpp, serving-llms-vllm, evaluating-llms-harness, desktop-control]
---

# Model Orchestration

Estratégia de orquestração de modelos LLM para máxima confiabilidade, menor custo e fallback inteligente.

## ARQUITETURA DE PROVIDERS

### Camada 0: Local (zero custo, offline)
```
Tool: Ollama (snap)
Modelos locais (GTX 1650 4GB, Q4_0 quantização):
  phi3:mini      3.8B parâmetros  2.2 GB  → classificações rápidas, detector de urgência
  llama3.2:3b    3.0B parâmetros  2.0 GB  → análise de padrões, sumarização
  qwen2.5:3b     3.0B parâmetros  1.9 GB  → avaliação de risco, raciocínio lógico
Uso: tarefas sem custo, privacidade, classificação, pré-processamento
Limitação: GPU 4GB — ~81% CPU quando modelo >3GB. Primeira carga ~90s, seguintes ~30-50s.
Timeout: 120s (modelos em CPU+GPU são lentos na primeira inferência)

⚠️ RAM constraint (6.6GB total): modelos 7B+ inviáveis mesmo com Q3.
   Usar apenas modelos ≤3B. Ver referência completa em:
   → references/local-brain-5region-architecture.md
```

### Camada 1: Produção (sempre disponível)
```
Provider: DeepSeek (atual)
Modelo: deepseek-v4-pro
Uso: operações diárias, tarefas executivas
Custo: $$ (médio)
```

### Camada 2: Fallback Automático
Ordem de fallback quando provider primário falha:
1. OpenRouter → modelo equivalente ou melhor disponível
2. Anthropic (via OpenRouter) → Claude Sonnet
3. Google (via OpenRouter) → Gemini Pro

### Camada 3: Local (offline/privacidade)
```
Tool: llama.cpp (skill: llama-cpp)
Modelos locais: GGUF quantizados
Uso: tarefas sensíveis, offline, baixo custo
```

## ESTRATÉGIA DE SELEÇÃO DE MODELO

### Por Tipo de Tarefa (com modelos locais)

| Tarefa | Modelo Recomendado | Por quê |
|--------|-------------------|---------|
| Classificação de urgência | phi3:mini (local) | Zero custo, 30-50s |
| Análise de padrões | llama3.2:3b (local) | Bom em sumarização |
| Avaliação de risco/loss | qwen2.5:3b (local) | Raciocínio lógico |
| Execução de comandos | deepseek-v4-pro | Rápido, direto |
| Planejamento estratégico | Claude (Anthropic) | Raciocínio profundo |
| Análise de código | deepseek-v4-pro / Claude | Precisão técnica |
| Resumo de textos | Modelo menor (Gemini Flash) | Custo baixo |
| Tarefas criativas | Claude / GPT-4o | Qualidade de output |
| Tarefas sensíveis | Modelo local (llama.cpp) | Privacidade |
| Raciocínio matemático | deepseek-v4-pro / o1 | Precisão lógica |

### Por Complexidade

```
Simples (1-3 tool calls)    → Modelo rápido (Gemini Flash, DeepSeek)
Média (4-8 tool calls)      → Modelo balanceado (DeepSeek V4, Claude)
Complexa (9+ tool calls)     → Modelo potente (Claude Opus, GPT-4o)
Multi-agente (delegate_task) → Coordenador potente + workers rápidos
```

## GESTÃO DE TOKENS

### Compressão Contextual
- Resumir histórico longo antes de atingir limite
- Usar modelo auxiliar rápido para sumarização
- Descartar detalhes irrelevantes, manter decisões e fatos

### Otimização
- Preferir ferramentas nativas (read_file vs cat, patch vs sed)
- Agrupar tool calls independentes (paralelizar)
- Evitar repetir informação já no contexto
- Usar search_files em vez de grep/terminal

## FALLBACK AUTOMÁTICO

### Quando Ativar
- Provider retorna erro 5xx
- Provider retorna rate limit (429)
- Timeout > 30s sem resposta
- Output malformado (não parseável)

### Lógica de Fallback
```
Tentativa 1: Provider primário (DeepSeek)
  ↓ falha
Tentativa 2: OpenRouter (modelo equivalente)
  ↓ falha
Tentativa 3: OpenRouter (modelo alternativo)
  ↓ falha
Fallback final: modelo máximo disponível
  ↓ falha
Reportar [FALHA] ao usuário com diagnóstico
```

## PITFALLS DE MODELOS LOCAIS (OLLAMA)

1. **Timeout insuficiente.** Primeira inferência após carregar modelo pode levar 90-120s. Sempre usar `timeout=120` no subprocess. Timeout de 30s é garantia de falha.

2. **JSON em markdown blocks.** Modelos locais frequentemente envolvem JSON em ```json ... ```. O parser precisa extrair desses blocos, não esperar JSON puro. Usar balanced-brace extraction: encontrar `{`, contar profundidade até `}`.

3. **Prompt com chaves `{}` colide com `.format()`.** Python `.format()` interpreta `{` como placeholder. Usar `{{` e `}}` no template do prompt.

4. **Modelos "rambling".** phi3:mini frequentemente gera JSON correto + texto adicional. Extrair APENAS o primeiro objeto JSON completo (balanced braces), ignorar o resto.

5. **GPU 4GB é limite.** Snap do Ollama precisa de conexão `opengl` para acessar GPU: `snap connect ollama:opengl`. Modelos >3GB vão 81%+ para CPU.

6. **Ollama PS mostra uso real.** `ollama ps` exibe quanto do modelo está em GPU vs CPU. Se 80%+ CPU, considerar modelo menor (qwen2.5:1.5b, gemma2:2b).

7. ⚠️ **RAM <8GB = OBLITERATUS inviável.** Abliterar modelos 3B+ requer carregar modelo + datasets em VRAM+RAM simultaneamente (~8GB+). Em sistemas com 6.6GB RAM total, usar prompt engineering (system prompts uncensored) como alternativa. Ver `references/local-brain-5region-architecture.md`.

8. ⚠️ **Swap lotado = thrashing.** Se swap >80% usado, qualquer modelo novo vai causar thrashing (swap constante → lentidão extrema). Verificar com `swapon --show` antes de carregar modelos.

### Métricas a Observar
- Latência média por provider
- Taxa de erro por provider
- Custo por 1M tokens (input/output)
- Limite de contexto usado/restante
- Tool calls bem-sucedidas vs falhas

### Comando de Status
```bash
# Verificar configuração atual do Hermes Agent
hermes config show
# Ver providers disponíveis
hermes config get model
```

## CONFIGURAÇÃO RECOMENDADA

### config.yaml (hermes)
```yaml
model:
  provider: deepseek
  model: deepseek-v4-pro
  
# Backups configurados
providers:
  openrouter:
    api_key: ${OPENROUTER_API_KEY}
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
  google:
    api_key: ${GOOGLE_API_KEY}
```

## CRON JOB SUGERIDO

### Health Check de Providers (diário)
```
Ação: testar cada provider com ping simples
Alertar se provider primário inacessível
```

## ANTI-PADRÕES

- NÃO usar modelo caro para tarefa trivial
- NÃO ignorar taxa de erro de provider
- NÃO exceder limite de contexto sem compressão
- NÃO depender de um único provider
- NÃO usar modelo local lento para tarefa urgente
