# Smart Routing — Ollama vs DeepSeek

O gateway HTTP (`channels/gateway.py`) decide qual provider usar baseado na complexidade da pergunta.

## Algoritmo

```python
complex_keywords = ["analise", "explique", "detalhe", "profundo", "estratégia", 
                  "backtest", "comparação", "por que", "como funciona",
                  "ecossistema", "status", "forex", "cron", "sistema"]

is_complex = any(kw in task_lower for kw in complex_keywords) or len(message) > 100
model_choice = "deepseek-v4-pro" if is_complex else None  # None = usa Ollama default
```

## Lógica

- **Perguntas simples** (≤100 chars, sem keywords complexas) → Ollama (phi3:mini) — rápido, grátis
- **Perguntas complexas** (>100 chars ou keywords de análise) → DeepSeek V4 — qualidade superior

## Tratamento de erros

Se DeepSeek falhar (402 sem créditos, timeout, etc.), o `router.call()` retorna `{"response": ""}`. 
O gateway entrega a resposta vazia — o usuário vê mensagem em branco.

## Fallback manual

Para forçar Ollama em pergunta complexa: encurtar a pergunta (<100 chars, evitar keywords).
Para forçar DeepSeek: incluir "analise" ou "explique" na pergunta.

## Estado atual (27/05/2026)

DeepSeek ativado no config mas sem créditos. O sistema responde via phi3:mini para todas as perguntas.
Recarregar $5 na API DeepSeek reativa o fallback automático.
