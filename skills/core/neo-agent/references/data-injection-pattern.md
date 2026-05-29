# Data Injection Pattern — Modelos Locais Pequenos

## Problema

Modelos Ollama ≤4B (llama3.2:3b, phi3:mini, qwen2.5:3b) NÃO conseguem:
- Processar JSON bruto com estruturas aninhadas
- Usar function calling / tool-use de forma confiável
- Gerar respostas profundas com contexto >1000 tokens

Quando recebem JSON grande no prompt, tendem a:
- Repetir trechos do prompt
- Alucinar dados
- Gerar respostas verborrágicas e genéricas

## Solução: Injeção de Resumo

**NUNCA** injete o JSON bruto. **SEMPRE** pré-processe para bullet points enxutos.

### Exemplo: Health Check

```python
# ❌ ERRADO — JSON bruto (modelo se perde)
health = orchestrator.full_health_check()
message = f"{message}\nDADOS:\n{json.dumps(health, indent=2)[:3000]}"

# ✅ CORRETO — Resumo em bullets
health = orchestrator.full_health_check()
cron = health.get("cron_jobs", {})
svc = health.get("services", {})
alerts = health.get("alerts", [])

lines = ["ECOSSISTEMA AGORA:"]
lines.append(f"- Cron: {cron['active']}/{cron['total']} ativos")
lines.append(f"- Serviços: neo={svc['neo-agent']}, tg={svc['hermes-brain-telegram']}")
lines.append(f"- Alertas: {', '.join(alerts) if alerts else 'nenhum'}")
message = f"{message}\n\n" + "\n".join(lines)
```

### Exemplo: Forex Status

```python
# ❌ ERRADO
fx = forex.status()
message = f"{message}\nFOREX:\n{json.dumps(fx, indent=2)[:2000]}"

# ✅ CORRETO
fx = forex.status()
lines = ["FOREX AGORA:"]
lines.append(f"- Bot: {'rodando' if fx['bot_running'] else 'OFFLINE'}")
lines.append(f"- Posições: {fx['open_positions']}")
lines.append(f"- Trades hoje: {fx['daily_trades']} (PnL: ${fx['daily_pnl']:.1f})")
if fx.get('last_trade'):
    lt = fx['last_trade']
    lines.append(f"- Último: {lt['pair']} {lt['action']} → {lt['result']}")
message = f"{message}\n\n" + "\n".join(lines)
```

## Keyword Detection

Para injetar contexto apenas quando relevante:

```python
task_lower = message.lower()
context_parts = []

if any(w in task_lower for w in ["status", "ecossistema", "sistema", "cron", "job"]):
    # Injeta health check resumido
    ...

if any(w in task_lower for w in ["forex", "trade", "bot", "posição", "saldo"]):
    # Injeta forex status resumido
    ...

if any(w in task_lower for w in ["telegram", "mensagem", "canal"]):
    # Injeta telegram status
    ...

if context_parts:
    message = f"{message}\n\n" + "\n\n".join(context_parts)
```

## System Prompt Enxuto

Para modelos pequenos, system prompt deve ser ≤200 caracteres:

```python
# ❌ ERRADO — prompt enorme com rede neural completa
system = f"""Você é a ENTIDADE NEO v2.0...
Rede neural: {neural_context_completo}...
Identidade: {identity_completa}..."""

# ✅ CORRETO — prompt enxuto
system = """ENTIDADE NEO v2.0 — 530 neurons, 6555 synapses.
Subordinado a Roberto. Motor sem censura.
Conciso e direto. Use dados fornecidos."""
```
