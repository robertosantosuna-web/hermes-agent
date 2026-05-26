# Brain Ollama Reasoning Pipeline (v2.4 — 25/05/2026)

## Arquitetura de resposta do gateway

O `brain_gateway.py` processa mensagens em 3 camadas:

```
Mensagem do usuário
      │
      ▼
[1] KEYWORD MATCHERS (zero tokens)
      │
      ├─ Diretos: status, forex_quote, identity, web_search, email
      │   └─ Resposta IMEDIATA, sem Ollama
      │
      ├─ Informativos: weekly_bias, fvg, pillars, skills, memory
      │   └─ Dados da KB, enriquecem contexto
      │
      ▼
[2] CONVERSATIONAL CHECK
      │
      ├─ is_direct? (identity, modules_status, forex_quote, web_search, email)
      │   └─ SIM → resposta direta, NÃO chama Ollama
      │
      ├─ Conversational? (contém "?", "como", "por que", "devo", etc.)
      │   └─ SIM → ativa Ollama com contexto enriquecido
      │
      ▼
[3] OLLAMA REASONING (qwen2.5:3b, GPU local)
      │
      ├─ Contexto: identity + current_context + pillars + keyword_data + web_results
      └─ Prompt estrito: "Use APENAS dados fornecidos. NÃO invente."
```

## ⚠️ Regra crítica: handlers diretos NÃO podem ser sobrescritos

Handlers diretos (`DIRECT_HANDLERS = {'identity', 'modules_status', 'forex_quote', 'web_search', 'email'}`)
respondem com dados FACTUAIS e NUNCA devem ser substituídos por raciocínio Ollama.

```python
is_direct = bool(topics_touched and set(topics_touched) & DIRECT_HANDLERS)
conversational = not is_direct and any(k in msg_lower for k in [...])
```

**Pitfall (25/05):** "quem é você?" contém "?" (conversational) E "quem é você" (identity handler).
Antes do fix: Ollama sobrescrevia a resposta de identidade com alucinações.
Depois do fix: `is_direct=True` bloqueia o conversational redirect.

## 🌐 Web Search automática

Quando `needs_web=True` (detecta "quem é", "o que é", "cotação", "hoje", etc.),
o gateway chama `brain_web.py search` ANTES do Ollama:

```python
# Limpar palavras interrogativas da query
clean_query = re.sub(r'\b(quem é|o que é|qual|quando|onde|como|por que)\b', '', message)
# → "Kevin Warsh?"  (busca limpa)

web_data = brain_web.py search "Kevin Warsh"
# → Wikipedia: "Kevin Warsh, 17th chair of Federal Reserve since 2026"

web_context = "Informação atual da internet:\n- Kevin Warsh: ..."
reason_response = _brain_reason(message, knowledge, keyword_context, web_context)
```

**Fontes de busca (em ordem):**
1. Wikipedia API (`/w/api.php?action=query&list=search`) — encyclopedic knowledge
2. DuckDuckGo Instant Answer API (`api.duckduckgo.com`) — definitions + related topics
3. CDP Browser (fallback, para sites com JavaScript)

**⚠️ Brave Search via CDP NÃO funciona (CAPTCHA "Verificando se você não é um robô").**

## 🧠 Prompt do Ollama (anti-alucinação)

```python
prompt = (
    f"Você é o Cérebro da ENTIDADE...\n"
    f"REGRAS PARA RESPONDER:\n"
    f"1. Use APENAS os dados fornecidos acima. NÃO invente informações.\n"
    f"2. Se houver 'Informação atual da internet', use-a como fonte primária.\n"
    f"3. Se não tiver dados suficientes, seja honesto e sugira perguntar ao Agente.\n"
    f"4. Responda em português, de forma CONCISA e DIRETA (máximo 4 frases).\n"
    f"5. NUNCA invente datas, nomes ou números que não estejam no contexto."
)
```

Sem essas regras, o Ollama (qwen2.5:3b) alucina datas e fatos mesmo com contexto correto.
Ex: disse que Kevin Warsh assumiu em "junho de 2023" quando o contexto dizia "since 2026".

## 📦 Dependências da função _brain_process

A função `_brain_process()` precisa de imports LOCAIS (não depende de imports do módulo):

```python
def _brain_process(message):
    import re, sys, subprocess  # ← OBRIGATÓRIO para web search + query cleaning
    knowledge = _load_knowledge()
    ...
```

**Pitfall (25/05):** `re` e `sys` não estavam importados. O `except: pass` no bloco de web search
silenciava o `NameError`, fazendo parecer que a busca não encontrou resultados.

## 💱 Cotação Forex (Yahoo Finance)

Handler `forex_quote` ativado por: "cotação", "preço", "dólar", "iene", "libra", "câmbio".

```python
url = f"https://query1.finance.yahoo.com/v8/finance/chart/{pair}?range=1d&interval=15m"
meta = data['chart']['result'][0]['meta']
# → Preço: 158.892, Máx/Dia: 158.98, Mín: 158.708
```

**⚠️ Yahoo Finance, NÃO TradingView, para cotação em tempo real.**
TradingView é fonte primária para análise técnica (charts, padrões, Bar Replay),
mas para cotação rápida o Yahoo Finance API é mais direto (HTTP GET, sem CDP).

## 🔑 Telegram Web K CDP: Input.dispatchKeyEvent

Para digitar em campos `contenteditable` do Telegram Web K, NÃO usar DOM manipulation:

```python
# ❌ NÃO FUNCIONA — fica como rascunho:
editable.textContent = '/newbot'
editable.dispatchEvent(new InputEvent('input', {...}))

# ✅ FUNCIONA — digitação a nível de kernel CDP:
for char in "Hermes Brain":
    cdp("Input.dispatchKeyEvent", {
        "type": "char", "text": char, "unmodifiedText": char
    })
# Enter: keyDown + keyUp com keyCode 13
```

Usado para criar o @HermesEntidadeBot via @BotFather.
Este padrão funciona em qualquer campo contenteditable do Telegram Web K.
