# Neural Trigger Engine — v2.3 Architecture (25/05/2026)

## Motivação

Antes: 5 módulos do cérebro rodavam em cron fixo (amygdala */15 min, n_accumbens */4h,
hippocampus */6h, brain_research */4h, synapse_engine */4h) — consumindo recursos
mesmo quando não havia eventos para processar.

Depois: pausados do cron. Acordam SOB DEMANDA via Neural Trigger Engine.

## Arquitetura

```
  EVENTO (trade, threat, FVG, research)
         │
         ▼
  auto_trigger.py → escreve neural_triggers.json
         │
         ▼
  Executive (*/5 min) → neural_trigger.py check
         │
         ├─ Acorda módulo alvo
         │      │
         │      └─ módulo processa → volta dormir
         │
         └─ Marca trigger como "done" → history
```

## Scripts

### `scripts/neural_trigger.py` — Engine central

```bash
neural_trigger.py                        # Status (pendentes/histórico)
neural_trigger.py check                  # Processa triggers pendentes
neural_trigger.py trigger <mod> <reason> # Escreve trigger manual
neural_trigger.py stats                  # JSON stats
```

### `scripts/auto_trigger.py` — Disparado por eventos

```python
# Chamado por outros scripts quando eventos acontecem
subprocess.run([
    sys.executable, "scripts/auto_trigger.py",
    "trade", "WIN USDJPY +15 pips"
])
```

Tipos de trigger suportados:

| Tipo | Módulo Alvo | Quem Dispara |
|------|------------|--------------|
| `trade` | N. Accumbens | `trade_tracker.py` após WIN/LOSS |
| `fvg` | Hippocampus | `brain_signal_generator.py` após detectar gaps |
| `threat` | Amygdala | `thalamus/router.py` após detectar ameaça |
| `research` | Brain Research | `knowledge_bridge.py` após absorver conhecimento |
| `day_end` | Synapse Engine | Agente no fim do dia |
| `week_end` | Synapse Engine | Agente no fim da semana |

## Dedup e Limites

- **Dedup 4h**: mesmo módulo + mesma razão é ignorado se já existe trigger pendente
- **Limite 20 pendentes**: excedentes vão para `history` com status `overflow`
- **Sem duplicatas**: se o trigger já foi processado (está no history), não é recriado

## Integração no Executive

Adicionado no início do `tick()` em `executive/brain.py`:

```python
# ⚡ NEURAL TRIGGER ENGINE
trigger_result = subprocess.run(
    [sys.executable, str(HERMES_DIR / 'scripts' / 'neural_trigger.py'), 'check'],
    capture_output=True, text=True, timeout=30
)
if trigger_result.returncode == 0:
    tr = json.loads(trigger_result.stdout)
    if tr.get('processed', 0) > 0:
        result['actions_taken'].append(f"triggers:{tr['processed']}")
```

## Módulos que MANTÊM cron fixo

| Módulo | Cron | Motivo |
|--------|------|--------|
| Cerebellum | */5 min | Segurança — validação de comandos perigosos |
| Executive | */5 min | Infraestrutura — processa triggers + detecta stalls |
| Neural Assimilate | */4h | Sinc Agent↔Brain (único que consome tokens) |

## Pitfalls

- **Executive usa `HERMES_DIR`, não `HERMES`**: variável definida no início do executive/brain.py.
  Usar `HERMES` causa `NameError` silencioso no `except: pass`.
- **Se Executive parar, módulos NUNCA acordam**: triggers ficam pendentes eternamente.
  Monitorar Executive é CRÍTICO.
- **auto_trigger.py é chamado via subprocess**: precisa do caminho absoluto.
  Usar `str(HERMES_DIR / 'scripts' / 'auto_trigger.py')`.
- **Triggers processados mas módulo falha**: o trigger vai para history como "done",
  mesmo que o script do módulo tenha falhado. Verificar output do módulo separadamente.
