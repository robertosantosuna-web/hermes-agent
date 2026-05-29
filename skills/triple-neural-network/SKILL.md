---
name: triple-neural-network
description: "Arquitetura das 3 redes neurais (NN-Brain, NN-Agent, NN-Shared) — motor de feed-forward, backpropagation, cross-pollination e consolidação diária. Documenta nn_engine.py, pitfalls de tipo (float vs str), ativação basal e ciclo OODA completo."
category: core
---

# Triple Neural Network — 3 Redes Neurais Interconectadas

## Estado Atual (27/05/2026)

**Migração para NEO em andamento.** As redes neurais estão sendo integradas ao agente neural
independente (`neo-agent`). O nn_engine.py continua rodando como cron job durante a transição.

| Rede | Arquivo | Neurônios | Ativos | Sinapses | Feed-Forward |
|------|---------|-----------|--------|----------|-------------|
| NN-Brain | `~/.hermes/neural/nn_brain.json` | 193 | 125 (65%) | 2734 | ✅ |
| NN-Agent | `~/.hermes/neural/nn_agent.json` | 125 | 125 (100%) | 302 | ✅ |
| NN-Shared | `~/.hermes/neural/nn_shared.json` | 212 | 212 (100%) | 3519 | ✅ |
| **TOTAL** | | **530** | **462 (87%)** | **6555** | |

## Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                    🔗 NN-Shared                         │
│           (sinapses cruzadas, conhecimento híbrido)      │
│           212 neurons | 3519 synapses                   │
└──────────────┬──────────────────┬───────────────────────┘
               │ cross-pollinate   │ cross-pollinate
               ▼                   ▼
┌──────────────────────┐ ┌──────────────────────┐
│   🧠 NN-Brain        │ │   🤖 NN-Agent        │
│   (forex, trading,   │ │   (automação,        │
│    padrões, sinais)  │ │    freelas, código)  │
│   193 N | 2734 S     │ │   121 N | 302 S      │
└──────────────────────┘ └──────────────────────┘
```

## Motor: nn_engine.py

**Local:** `~/.hermes/scripts/nn_engine.py`
**Cron:** `f91ee6baae41` — `0 2 * * *` (02:00 BRT diário, no_agent)
**Manutenção:** `bd65df932544` — `nn_daily_maintenance.sh` (09:00 BRT diário)

### Funcionamento (batch, sem CLI)

O script é executado como batch (`python3 nn_engine.py`) e faz 4 operações em sequência:

1. **Feed-Forward** — Ativa neurônios com inputs frescos (KB domains, trade log). Se não há inputs significativos, ativação basal: todos os neurônios com strength ≥ 0.3 recebem +0.05.
2. **Cross-Pollination** — Transfere neurônios com strength > 0.5 entre redes. Brain→Agent, Agent→Brain, →Shared.
3. **Backpropagation** — Ajusta pesos baseado em resultados de trades (WIN=+0.1, LOSS=-0.05).
4. **Compute Activity** — Calcula % de neurônios ativos (strength > 0.3).

Output salvo em `~/.hermes/cron/output/f91ee6baae41/` e `~/.hermes/neural/nn_*.json`.

## Ciclo de Aprendizado (OODA Neural) — COM PAPER TRADING (27/05)

Quando o MT5 está offline, o NEO fecha o ciclo OODA via paper trading. O processo é idêntico ao real, apenas a execução é simulada:

```
PaperTrader escaneia 6 pares (yfinance OHLC) a cada ~60s
     ↓ detecta FVG+CRT → simula trade → trade_log.json
     ↓
N. Accumbens (*/4h) → pair_weights_live.json (70% live / 30% backtest)
     ↓
NN Engine (02:00) → feed_forward → cross_pollinate → backprop
     ↓
Próximo scan usa pesos ajustados
```

**Diferença paper vs real:** trades simulados têm `source: paper` e `status: closed` por age de candle (hit SL/TP no próximo candle 5m). Trades reais usam `forex_realtime_monitor.py`.

**PITFALL:** Paper trading só funciona com yfinance. Sem internet, 0 sinais. Fim de semana = 0 sinais (mercado fechado).

## ☠️ PITFALL: Neurons são dict, não lista (27/05)

**Sintoma:** `AttributeError: 'str' object has no attribute 'get'` ao iterar neurônios.

**Causa:** `nn_brain.json` tem `"neurons": {"n1f6f7e86": {"concept": "...", "strength": 1.0, ...}, ...}` — é um dict de dicts, não uma lista.

**Correção:**
```python
neurons = nn_data.get("neurons", {})
for nid, neuron in neurons.items():
    if not isinstance(neuron, dict):
        continue
    concept = neuron.get("concept", "")
    strength = float(neuron.get("strength", 0))
```

**Formato real do neurônio:** `{concept, domain, layer, created, strength, activations}`. O campo de descrição é `concept`, NÃO `name`.

## ☠️ PITFALL: Força armazenada como string quebra comparações

**Sintoma:** Feed-forward retorna 0 ativações mesmo com neurônios de força 0.72. `compute_activity` lança `TypeError: '>=' not supported between instances of 'str' and 'float'`.

**Causa:** Versões antigas do nn_engine.py armazenavam `strength` e `activations` como strings (`str(round(...))`, `str(int(...))`). Comparações numéricas quebram com tipos mistos.

**Correção (27/05):**
1. `feed_forward`: normaliza todas as strengths para float no início. Armazena como float.
2. `cross_pollinate`: armazena `strength` como float (não `str(round(...))`). `activations` como int (não `str(...)`).
3. `backprop`: usa `try/except` para converter strength. Armazena como float.
4. `compute_activity`: wrapper `_get_strength(n)` com try/except.
5. Neurônios existentes com força string: converter com script de reparo.

## ☠️ PITFALL: Feed-forward sem ativação basal

**Sintoma:** Feed-forward retorna 0 ativações quando trade_log tem 0 trades (inputs = `{'recent_trades': '0', 'pairs_active': []}`).

**Causa:** O loop de matching tentava casar `'recent_trades'` com conceitos como "[EURUSD] 113 FVGs..." — impossível. Inputs existiam mas não eram "significativos".

**Correção (27/05):** Se `inputs` é vazio OU nenhum valor é uma lista não-vazia → ativação basal (todos neurônios com strength ≥ 0.3 recebem +0.05).

## ☠️ PITFALL: last_feed_forward nunca salvo

**Sintoma:** Arquivos `nn_*.json` mostram `last_feed_forward: "never"` mesmo após execuções bem-sucedidas.

**Causa:** O script salvava as redes mas não atualizava os timestamps.

**Correção (27/05):** `brain['last_feed_forward'] = now_ts` antes de `save()`.

## ☠️ PITFALL: N. Accumbens não gera pesos sem 5+ trades

**Sintoma:** `pair_weights_live.json` não existe → bot não lê pesos dinâmicos → usa só backtest WR estático.

**Causa:** `n_accumbens.py` retorna silenciosamente se `len(trades) < 5`.

**Correção (27/05):** Se < 5 trades → seed com backtest WR (USDJPY 66.1%, GBPJPY 67.6%, etc). Arquivo é criado com `source: "backtest_seed"`. Quando houver 5+ trades reais, o seed é substituído por dados live.

## Métricas por Rede

| Métrica | Significado |
|---------|-------------|
| neurons | Conceitos/fatos armazenados |
| synapses | Conexões entre conceitos |
| active_neurons | Neurônios com strength > 0.3 |
| activity_pct | % de neurônios ativos |
| last_feed_forward | Timestamp da última ativação |
| last_backprop | Timestamp do último ajuste por trade |

## Ativação Manual

```bash
# Executar ciclo completo agora (batch)
python3 ~/.hermes/scripts/nn_engine.py

# Ver output
cat ~/.hermes/cron/output/f91ee6baae41/$(date +%Y-%m-%d).md
```

## Integrações

- **N. Accumbens** → `pair_weights_live.json` → **Bot** lê e aplica 70% live / 30% backtest
- **Brain Study Session** → carrega NN-Brain antes de estudar, cross-pollinate depois
- **Meta-Observer** → verifica se `nn_engine` cron está ativo (pipeline `neural_knowledge_base.json`)
- **Self-Improve** → `self_improve.py` escreve no `self_evolution_log.json` após cada ciclo
- **NEO SONA-lite** → Fase 2 substituirá feed-forward estático por RL contínuo (Q-learning + pattern extraction). Ver skill `neo-agent`.

## ☠️ PITFALL: JSON type — array vs object em scripts no_agent

**Sintoma:** `AttributeError: 'list' object has no attribute 'get'` em scripts que leem JSON.

**Causa:** Arquivo JSON é array `[...]` (escrito por `json.dumps(list)`) mas código espera dict `{...}` e chama `.get()`.

**Correção:** Sempre verificar tipo antes de acessar:
```python
data = json.loads(path.read_text())
items = data if isinstance(data, list) else data.get('items', [])
```

**Exemplo real (27/05):** `monitor_consumer.py` quebrou porque `alerts.json` era array direto do `monitor.py`, mas o consumer esperava `alerts.get('alerts')`.

## ☠️ PITFALL: NN neurons são dict, NÃO lista — `neurons.items()` não `for n in neurons`

**Sintoma:** `AttributeError: 'str' object has no attribute 'get'` ao iterar neurônios.

**Causa:** As redes neurais (`nn_brain.json`, `nn_agent.json`, `nn_shared.json`) armazenam neurônios como dict `{id: {concept, domain, strength, activations}}`, não como lista `[{name, ...}]`.

**Formato real:**
```json
{"neurons": {
  "n1f6f7e86": {"concept": "...", "domain": "forex_trading", "strength": 1.0, "activations": 928},
  "n8ee3328d": {"concept": "...", "domain": "forex_trading", "strength": 1.0, "activations": 928}
}}
```

**Correção:**
```python
# ❌ ERRADO
for neuron in neurons:
    name = neuron.get("name")  # AttributeError: 'str' object has no attribute 'get'

# ✅ CORRETO
for nid, neuron in neurons.items():
    concept = neuron.get("concept")
    strength = float(neuron.get("strength", 0))
```

## ☠️ PITFALL: Ollama context length — qwen2.5:3b (32K) < mínimo Hermes (64K)

**Sintoma:** `ValueError: Model qwen2.5:3b has a context window of 32,768 tokens, which is below the minimum 64,000 required by Hermes Agent.`

**Causa:** Hermes Agent exige mínimo 64K contexto. Apenas modelos com ≥64K funcionam como provider.

**Modelos compatíveis:** `llama3.2:3b` (128K) ✅, `phi3:mini` (128K) ✅  
**Modelos incompatíveis:** `qwen2.5:3b` (32K) ❌, `deepseek-r1:1.5b` (32K) ❌

**Setup completo do Ollama provider:** Ver skill `brain-architecture` → `references/ollama-cron-provider.md`.
