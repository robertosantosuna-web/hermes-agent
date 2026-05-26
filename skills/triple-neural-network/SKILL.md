---
name: triple-neural-network
description: Arquitetura das 3 redes neurais (NN-Brain, NN-Agent, NN-Shared) — motor de sinapses, backpropagation, cross-pollination, pruning e consolidação. Documenta o nn_engine.py e as 3 redes em ~/.hermes/neural/.
category: core
---

# Triple Neural Network — 3 Redes Neurais Interconectadas

## Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                    🔗 NN-Shared                         │
│           (sinapses cruzadas, conhecimento híbrido)      │
│           neurons: 5+ | synapses: 10+                   │
└──────────────┬──────────────────┬───────────────────────┘
               │ cross-pollinate   │ cross-pollinate
               ▼                   ▼
┌──────────────────────┐ ┌──────────────────────┐
│   🧠 NN-Brain        │ │   🤖 NN-Agent        │
│   (forex, trading,   │ │   (automação,        │
│    padrões, sinais)  │ │    freelas, pipeline) │
│   neurons: 7+        │ │   neurons: 23+       │
│   synapses: 7+       │ │   synapses: 11+      │
└──────────────────────┘ └──────────────────────┘
         │                        │
         └────────┬───────────────┘
                  │
         knowledge_bridge.json
         (descobertas bidirecionais)
```

## Redes

| Rede | Arquivo | Domínio | Função |
|------|---------|---------|--------|
| NN-Brain | `~/.hermes/neural/nn_brain.json` | Forex, trading, padrões, sinais | Aprendizado do cérebro |
| NN-Agent | `~/.hermes/neural/nn_agent.json` | Automação, freelas, pipeline, erros | Aprendizado do agente |
| NN-Shared | `~/.hermes/neural/nn_shared.json` | Conhecimento híbrido | Sinapses cruzadas |

## Motor: nn_engine.py

Local: `~/.hermes/scripts/nn_engine.py`

### Comandos

```bash
# Inicializar as 3 redes
python3 scripts/nn_engine.py init

# Status completo
python3 scripts/nn_engine.py status

# Absorver knowledge bridge → redes
python3 scripts/nn_engine.py absorb

# Aprender fato novo
python3 scripts/nn_engine.py learn <network> "<fact>"

# Adicionar neurônio
python3 scripts/nn_engine.py add_neuron <network> "<concept>" [domain]

# Conectar sinapse
python3 scripts/nn_engine.py add_synapse "<source>" "<target>" <weight> <network>

# Registrar sucesso (aumenta hits, sobe confidence)
python3 scripts/nn_engine.py register_success <network> "<approach>"

# Registrar erro (adiciona anti-pattern, backprop automático)
python3 scripts/nn_engine.py register_error <network> "<error>" "<failed>" "<correct>"

# Feed-forward (ativar sinapses)
python3 scripts/nn_engine.py feed_forward [brain|agent|shared|all]

# Backpropagation (corrigir pesos por hit/miss ratio)
python3 scripts/nn_engine.py backprop [brain|agent|shared|all]

# Cross-pollinate (transferir sinapses high-confidence → shared)
python3 scripts/nn_engine.py cross_pollinate

# Consolidar (mesclar sinapses duplicadas)
python3 scripts/nn_engine.py consolidate [brain|agent|shared|all]

# Podar (remover sinapses fracas)
python3 scripts/nn_engine.py prune [brain|agent|shared|all]
```

## Ciclo de Aprendizado

```
1. Cérebro estuda → escreve no knowledge_bridge
2. Agente age → registra sucesso/erro no nn_agent
3. nn_engine.py absorb → puxa bridge → NN-Brain + NN-Agent
4. nn_engine.py cross_pollinate → transfere sinapses ≥0.6 confidence → NN-Shared
5. nn_engine.py backprop → corrige pesos por hit/miss ratio
6. nn_engine.py consolidate → mescla duplicatas
7. nn_engine.py prune → remove sinapses fracas (peso<0.1)
```

## Integração com Brain Study Session

`brain_study_session.py`:
- **FASE 0.5:** `absorb` + `feed_forward brain` (carrega conhecimento antes de estudar)
- **FASE 5.5:** `cross_pollinate` + `backprop brain` (compartilha descobertas após estudo)

## Manutenção Diária (cron)

```bash
# 06:00 BRT — Manutenção diária das 3 redes
0 9 * * * cd ~/.hermes && python3 scripts/nn_engine.py absorb && python3 scripts/nn_engine.py cross_pollinate && python3 scripts/nn_engine.py backprop all && python3 scripts/nn_engine.py consolidate all && python3 scripts/nn_engine.py prune all
```

**Cron ativo:** `bd65df932544` — `nn_daily_maintenance.sh`, roda 09:00 UTC diário.

## Brain Study Integration

`brain_study_session.py` FASE 0.5 carrega NN-Brain + absorb, FASE 5.5 cross-pollinate + backprop.

## Brain TradingView Study

**Cron ativo:** `6decb9230502` — `brain_study_tradingview.py`, 09:00 BRT seg-sex. Estuda Pine Scripts, ideias, calendário econômico, pares forex no TradingView.

## Métricas por Rede

| Métrica | Significado |
|---------|-------------|
| neurons | Conceitos/fatos armazenados |
| synapses | Conexões entre conceitos |
| assertiveness | hits / (hits + misses) — acurácia da rede |
| avg_weight | Peso médio das sinapses (0-1) |
| avg_confidence | Confiança média das sinapses (0-1) |
| prunes | Sinapses removidas por baixo peso |
| cross_pollinations | Sinapses transferidas entre redes |

## Anti-padrões Detectados (via register_error)

Erros registrados viram anti-padrões permanentes. A rede aprende:
- ❌ CDP input em React → ✅ Daemon+ydotool
- ❌ ATR genérica → ✅ FVG V4
- ❌ bridge spam → ✅ delta>5% filter
- ❌ YouTube sem PYTHONPATH → ✅ PYTHONPATH fix

## Ativação Manual (agente)

Quando o agente executa uma ação, deve:
1. Antes: `python3 scripts/nn_engine.py feed_forward agent` (ativar sinapses relevantes)
2. Depois: `register_success` ou `register_error` (aprender com o resultado)
3. Ao final da sessão: `cross_pollinate` + `backprop all` (compartilhar + corrigir)
