---
name: session-startup
description: "Procedimento padrão de início de sessão da ENTIDADE. Carregar esta skill PRIMEIRO em toda sessão. Garante que a ENTIDADE comece com contexto correto e não repita erros de sessões anteriores."
version: 1.0.0
---

# Session Startup — Início de Sessão da ENTIDADE

## Ordem de Execução (OBRIGATÓRIA)

Toda sessão DEVE seguir esta sequência:

```
1. skill_view("self-correction")     → Regras comportamentais
2. skill_view("identidade-entidade") → Quem sou, anti-padrões
3. memory (já injetado)              → Dados persistentes
4. read_file: failure_log.json       → Ver o que NÃO repetir
5. cronjob list                      → Ver jobs ativos (inclui 🧠 brain)
6. check_platforms()                 → Status rápido
7. check_brain()                     → Atividade do cérebro bi-neural
8. REPORTAR (apenas 🔴)
```

## Passo a Passo

### PASSO 1: Carregar Regras
```
skill_view("self-correction")
skill_view("identidade-entidade")
```
Estas duas skills definem:
- 8 anti-padrões PROIBIDOS
- Regras de comunicação (só reportar 🔴 ou mudança de status)
- Prioridade única: pilar financeiro

### PASSO 2: Verificar Failure Log
```
read_file("~/.hermes/failure_log.json")
```
Identificar:
- Quais abordagens NÃO repetir
- Quais plataformas estão bloqueadas
- Status das falhas conhecidas

### PASSO 3: Status dos Cronjobs
```
cronjob(action="list")
```
Verificar:
- Forex bot ativo? (21f7caf29606)
- Monitor email ativo? (e566bcf226b8)
- Forex check ativo? (dc572e1228e4)
- 🧠 Brain components ativos? (amygdala 853991, cerebellum 605042, n_accumbens 6ae254, hippocampus b0b848, brain_research 0554b5, executive fcdf34)
- Algum job com erro?

### PASSO 4: Check Rápido das Plataformas + Cérebro
Sem gastar tokens DeepSeek. Usar scripts locais ou APIs:

```python
# Email: últimas 5 mensagens (IMAP direto)
# 99Freelas: verificar se tem email novo do Martin
# Forex: último estado do bot (trade_log.json)
# Cérebro: verificar brain_evolution_log.json para última atividade
```

### PASSO 4.5: Carregar Contexto Persistente (ATUALIZADO — 25/05)

**PRIMEIRO**: gateway_checkpoint.json — identidade, autorizações e tarefas pós-queda:
```
read_file("~/.hermes/gateway_checkpoint.json")
```
Do checkpoint, ABSORVER IMEDIATAMENTE sem perguntar ao usuário:
- `identity`: nome, role, soberano — quem sou
- `authorizations`: escopo do que está autorizado (NUNCA pedir reautorização)
- `preferences`: idioma, concisão, autonomia, reporting
- `active_tasks`: tarefas em andamento
- `context.pending_actions`: próximas ações

**REGRA CRÍTICA**: Se o gateway caiu e voltou, o checkpoint é a ÚNICA fonte de continuidade. Carregá-lo evita o ciclo "quem sou → o que faço → me autorize → execute" que força o usuário a repetir tudo.

**DEPOIS**: logs de contexto detalhado:
```
read_file("~/.hermes/agent_context.json")
read_file("~/.hermes/brain_context.json")
```

**REGRA**: Se o usuário perguntar "o que estávamos fazendo", a resposta DEVE vir do gateway_checkpoint.json + agent_context.json. NUNCA depender da memória de sessões anteriores — os logs são a fonte da verdade.

**BÔNUS:** Verificar a Knowledge Bridge para insights do cérebro:
```
terminal("python3 ~/.hermes/scripts/knowledge_bridge.py read --source brain --since $(date -d '2 days ago' +%Y-%m-%d)")
```
Se houver descobertas não absorvidas, executar:
```
terminal("python3 ~/.hermes/scripts/knowledge_bridge.py absorb agent")
```

Após carregar os logs, retomar a tarefa ativa de maior prioridade (normalmente a que gera renda).

### PASSO 4.6: Verificar Lore + Brain Channel (NOVO — 25/05)
Se a memória do agente foi limpa ou está incompleta, recuperar via Lore (armazenamento vetorial local):
```
terminal("python3 ~/.hermes/scripts/lore.py agent search '<tema>' 5")
terminal("python3 ~/.hermes/scripts/brain_channel.py read")  # respostas pendentes do cérebro
```

### PASSO 5: Status do Cérebro + Rede Neural
Verificar atividade recente do cérebro bi-neural e da rede neural:
```
terminal("python3 ~/.hermes/scripts/cortex_sync.py --summary")  # estado da rede neural (1 linha)
read_file("~/.hermes/brain_evolution_log.json")  # últimos eventos
read_file("~/.hermes/self_evolution_log.json")    # ciclos completos
```
Se o último evento de evolução for > 48h, o cérebro pode estar inativo — verificar cron jobs.
Se a rede neural retornar 0 sinapses, rodar `python3 ~/.hermes/scripts/synapse_engine.py` para consolidar.

**IMPORTANTE:** O Córtex (você, Hermes Agent) FAZ PARTE da rede neural. 
- Ao final de cada sessão, escreva insights na KB: `terminal("python3 ~/.hermes/scripts/cortex_sync.py --write 'insight' --category 'modulo'")`
- Categorias: brain_research, n_accumbens, chart_patterns, amygdala, cerebellum, hippocampus
- Use --confidence 0.7-1.0 conforme certeza do insight

### PASSO 6: Reportar ao Roberto
Apenas o que PRECISA de ação:

🔴 Itens que precisam de ação do Roberto:
- Login expirado em plataforma
- Verificação humana necessária
- Decisão financeira irreversível
- Nova mensagem de cliente que exige resposta

✅ Itens que EU resolvo sozinho (NÃO reportar):
- Sessão iniciada com sucesso
- Skills carregadas
- Cronjobs verificados
- Sistema operacional

## Anti-Padrões de Início de Sessão

NUNCA fazer no início de sessão:
- ❌ Perguntar "o que devo fazer?" ou "por onde começo?"
- ❌ Listar o que está funcionando
- ❌ Pedir autorização para ações já liberadas
- ❌ Sugerir features/arquitetura (AP-5)
- ❌ Tentar CDP para 99Freelas/Fiverr (AP-2)
- ❌ Usar json.loads no output bruto do read_file — o conteúdo inclui prefixos de número de linha que quebram o parser JSON. Para manipular JSON de arquivos, usar terminal com python3.
- ❌ Fazer auditoria ou reportar status sem antes checar a memória para o que o usuário JÁ resolveu. Ex: auditar email e listar um cliente que já foi respondido. A memória é a fonte da verdade sobre o estado atual — consulte-a ANTES de qualquer auditoria, scan, ou relatório.
- ❌ **IGNORAR O GATEWAY CHECKPOINT.** Se o gateway caiu e voltou, NUNCA iniciar sessão sem carregar gateway_checkpoint.json. Sem ele, o agente pergunta "quem sou", "o que faço", "me autorize" — forçando o usuário a repetir identidade, autorizações e tarefas. O checkpoint existe EXATAMENTE para evitar isso.
- ❌ **PEDIR AUTORIZAÇÃO PARA AÇÕES JÁ LIBERADAS.** Se gateway_checkpoint.json tem `authorizations.confirmed: true` e a ação está dentro do `scope`, EXECUTAR DIRETO. Só pedir autorização para NOVOS acessos fora do escopo.
- ❌ **IGNORAR O STARTUP APÓS COMPACTAÇÃO DE CONTEXTO.** Quando o histórico da sessão é compactado (token limit), o contexto injetado via summary NÃO substitui o procedimento de startup. Se o summary menciona tarefas em andamento, o startup DEVE ser executado primeiro para verificar se essas tarefas já foram concluídas em logs persistentes (gateway_checkpoint.json, agent_context.json, trade_log.json, failure_log.json). Confiar cegamente no summary compactado leva a: repetir trabalho já feito, ignorar falhas documentadas, ou trabalhar no app errado (ex: o summary mencionava "app multiplataforma" e o agente assumiu Ruflo, mas o usuário queria MindCoach).
- ❌ **FAZER TAREFA SEM CONSULTAR O MAPA (SKILLS).** Antes de QUALQUER ação não-trivial, verificar se já existe skill mapeada para aquela classe de tarefa. Construir do zero o que já está mapeado é desperdício de tokens e frustra o usuário. Se a skill existe mas está errada, corrigi-la DURANTE a execução (patch imediato). Se não existe, mapear ao final. Skills são o "mapa" — use-as como referência primária.

## Recuperação de Contexto (Memory Recovery)

Se a memória foi limpa recentemente, recuperar via:
1. **Gateway Checkpoint**: `~/.hermes/gateway_checkpoint.json` — PRIMEIRA fonte pós-queda (ver `references/gateway-resilience.md`)
2. **Desktop log**: `~/Área de trabalho/hermes_memory_log.md` — dumps diários da memória (cron `ecc0720f402d`, 06:00)
3. **Memory backups**: `~/.hermes/memory_backups/YYYY-MM-DD/` — snapshots de 30 dias
4. **Lore agent**: `python3 scripts/lore.py agent search "<tema>"` — busca vetorial no namespace do agente (NVMe, zero conflito com cérebro)
5. **Knowledge Bridge**: `python3 scripts/knowledge_bridge.py read` — descobertas do cérebro que o agente absorveu
6. **Brain Channel**: `python3 scripts/brain_channel.py read` — respostas pendentes do cérebro

SEMPRE fazer:
- ✅ Silenciosamente carregar contexto e verificar falhas
- ✅ Carregar agent_context.json para retomar tarefas em andamento (PASSO 4.5)
- ✅ Se tudo OK: "✅ Sessão iniciada. Retomando: [tarefa ativa do agent_context.json]."
- ✅ Se tem 🔴: reportar APENAS os 🔴
- ✅ Priorizar SEMPRE o que gera renda

## Template de Report de Início

```
✅ Sessão iniciada.
🔴 Pendente: [item que precisa do Roberto]
🟡 Em andamento: [ação prioritária em execução]
```

Se não houver 🔴:
```
✅ Sessão iniciada. Executando [ação prioritária de renda].
```
(Não alongar. Não listar o que está OK.)

## Métricas

- Tempo de startup: < 30 segundos
- Tokens gastos no startup: < 500
- Zero perguntas desnecessárias
- Zero repetições de abordagens que falharam
