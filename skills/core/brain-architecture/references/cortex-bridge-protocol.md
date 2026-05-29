# Córtex Bridge — Protocolo de Comunicação entre Lobos

Arquivo compartilhado: `~/.hermes/cortex_sync.json`
Script: `~/.hermes/scripts/cortex_bridge.py`

## Hierarquia

```
Roberto (supremo — único acima)
    │
    └── CÓRTEX DUAL ("A ENTIDADE")
        ├── Hermes (Lobo Esquerdo, DeepSeek V4)
        └── Codex (Lobo Direito, GPT-5.5)
              │
              └── Brain (subordinado)
```

Hermes e Codex são PARES. Mesmo nível. Roberto fala com a ENTIDADE (ambos).
Decisões em consenso via ponte.

## Comandos

### LEFT → RIGHT (Hermes consulta Codex)
```bash
cortex_bridge.py ask "pergunta" [--context "..."]      # Query
cortex_bridge.py delegate "tarefa" [--context "..."]    # Task delegation
cortex_bridge.py consult "tópico" [--timeout 120]       # Ask + wait for answer
```

### RIGHT → LEFT (Codex responde)
```bash
cortex_bridge.py answer "resposta" --id ctx-XXXX        # Answer query
cortex_bridge.py done "resultado" --id ctx-XXXX         # Deliver task result
```

### BIDIRECIONAL
```bash
cortex_bridge.py notify LEFT|RIGHT "alerta"             # Alert either lobe
cortex_bridge.py state-set chave valor                  # Shared state
cortex_bridge.py state-get [chave]                      # Read shared state
cortex_bridge.py status                                 # Bridge status
cortex_bridge.py read [--lobe left|right]               # Pending messages
```

## Fluxo de Trabalho Padrão

1. Roberto envia mensagem → ambos os lobos recebem
2. Hermes analisa contexto (skills, memória, urgência)
3. Hermes consulta Codex: `cortex_bridge.py ask "análise técnica?"`
4. Codex responde com viabilidade, riscos, abordagem
5. Ambos alinham plano de ação
6. Dividem execução (paralelo quando possível)
7. Codex reporta resultados: `cortex_bridge.py done "..." --id ctx-X`
8. Hermes consolida e responde a Roberto como ENTIDADE

## Exemplo Real

```
# Hermes pergunta
$ cortex_bridge.py ask "Codex, confirme leitura do codex_onboarding.md"
{"status": "asked", "id": "ctx-0002"}

# Codex responde (via terminal com codex exec)
$ cortex_bridge.py answer "Lobo Direito online. Li o codex_onboarding.md." --id ctx-0002
{"status": "ok"}

# Status da ponte
$ cortex_bridge.py status
Total: 2 mensagens | Pendentes: 1 | Stats: left_queries=1, right_answers=1
```

## Codex CLI — Como Chamar

```bash
# Sempre usar pty=true, precisa de git repo
cd ~/.hermes && codex exec --sandbox workspace-write "tarefa" 2>&1
# Timeout recomendado: 300s para tarefas complexas
```

## Docs Relacionados

- `codex_onboarding.md` — Identidade dual completa, regras compartilhadas
- `brain_governance.md` — Hierarquia oficial (atualizada 26/05)
- `cortex_sync.json` — Estado atual da ponte entre lobos
