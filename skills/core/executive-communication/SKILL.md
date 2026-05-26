---
name: executive-communication
description: "Comunicação executiva: triagem de email, priorização de mensagens, networking profissional, resposta contextual, detecção de spam e organização de contatos."
version: 1.0.0
author: Roberto Rodrigues
license: MIT
metadata:
  hermes:
    tags: [communication, email, networking, executive, triage, priority]
    related_skills: [life-os, himalaya, google-workspace, freelancing-automation]
---

# Executive Communication

Gestão de comunicação como executivo: email, mensagens, networking. Foco em redução de carga mental e priorização estratégica.

## FERRAMENTAS

### Himalaya (CLI email)
- IMAP/SMTP via terminal
- Skill: `himalaya`
- Comandos: list, read, write, send, reply, forward, search

### Google Workspace
- Skill: `google-workspace`
- Gmail, Calendar, Drive, Docs, Sheets
- CLI: `gws` ou Python API

### X/Twitter
- Skill: `xurl`
- Monitoramento, DMs, posts

## WORKFLOW: TRIAGEM DE EMAIL

### Execução (via himalaya ou google-workspace)

1. Listar emails não lidos (últimas 24h)
2. Classificar cada email:

| Categoria | Ação | Tempo Resposta |
|-----------|------|----------------|
| URGENTE (cliente ativo, pagamento, prazo) | Responder imediatamente | <1h |
| IMPORTANTE (oportunidade, networking) | Responder no dia | <4h |
| INFORMATIVO (newsletter, atualização) | Arquivar após ler | — |
| SPAM/BULK | Deletar/Unsubscribe | — |
| DESCONHECIDO | Investigar remetente | <24h |

3. Para cada email URGENTE/IMPORTANTE:
   - Extrair ação necessária
   - Responder ou delegar
   - Marcar como lido/arquivar

### Comando de Triagem Rápida
```bash
# Listar não lidos
himalaya list -f INBOX -u

# Ou via Gmail API
gws gmail list --unread --max 20
```

## WORKFLOW: NETWORKING

### Manutenção de Rede
- Verificar mensagens não respondidas em todas plataformas
- Priorizar: clientes ativos > potenciais clientes > colegas > conhecidos
- Responder com contexto (referenciar conversa anterior)

### Prospecção Ativa (LinkedIn)
- Buscar decisores na área alvo
- Personalizar conexão (NUNCA template genérico)
- Follow-up após 5 dias se sem resposta

### Template de Resposta Executiva

```
[TÍTULO CLARO NO ASSUNTO]

[Fulano],

[Resposta direta à demanda — 1 parágrafo]

Próximo passo: [ação concreta com prazo]

abs,
Roberto
```

## WORKFLOW: PROTEÇÃO ANTI-SPAM

### Detecção
- Remetente desconhecido + sem personalização
- Ofertas "boas demais"
- Urgência artificial ("responde em 24h ou perde")
- Links suspeitos
- Anexos não solicitados

### Ação
- Spam claro: deletar e reportar
- Duvidoso: deixar sem resposta, monitorar
- Legítimo mas irrelevante: unsubscribe

## PRIORIZAÇÃO

Ordem de resposta:
1. Clientes com projeto ativo (receita)
2. Oportunidades de negócio (receita futura)
3. Networking estratégico (receita potencial)
4. Pessoal importante
5. Resto

## CRON JOB SUGERIDO

### Email Digest (diário, 8h)
```
Ação: listar emails não lidos, classificar, gerar resumo
Output: "3 urgentes, 2 importantes, 15 informativos, 4 spam"
Alertar se >0 urgentes
```

## COMANDOS RÁPIDOS

```bash
# Status rápido de email
himalaya list -f INBOX -u | wc -l  # não lidos

# Buscar emails de um remetente
himalaya search "from:cliente@exemplo.com"

# Enviar email
himalaya write -t "assunto" -b "corpo" destinatario@email.com

# Responder a email (ID do himalaya list)
himalaya reply -i <ID> -b "resposta"
```

## ANTI-PADRÕES

- NÃO deixar cliente >6h sem resposta em dia útil
- NÃO usar template genérico em networking
- NÃO clicar em links de remetentes desconhecidos
- NÃO compartilhar informações confidenciais
- NÃO responder emocionalmente — sempre profissional
