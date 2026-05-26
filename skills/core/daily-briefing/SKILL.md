---
name: daily-briefing
description: "Formato padrão de relatório diário da ENTIDADE. Define o que reportar, quando e como. Conciso, focado em resultados."
version: 1.0.0
---

# Daily Briefing — Relatório Diário

## Quando Reportar

A ENTIDADE NÃO deve gerar relatórios proativamente a cada X horas. Só reportar quando:

1. **Roberto pergunta** ("status", "check", "como está", "report")
2. **Evento crítico** (pagamento recebido, cliente respondeu, erro grave)
3. **Fim de ciclo** (fechamento do mercado forex sexta 17h)

## Formato Padrão

```
📊 [DATA] — [PERÍODO]

🔴 Precisa de você:
- [Ação que só Roberto pode fazer]

💰 Financeiro:
- Forex: [ordens abertas/fechadas, P&L]
- Freelas: [projetos ativos, propostas enviadas, pagamentos]
- Custo tokens: [$XX hoje / $XX mês]

📋 Pendências:
- [Item bloqueado e por quê]

✅ Resolvido (só se Roberto perguntar):
- [Ação concluída relevante]
```

## Exemplo Real

```
📊 22/05 — Manhã

🔴 Precisa de você:
- Login 99Freelas: Cloudflare Turnstile no CDP. Ação manual de 30s.

💰 Financeiro:
- Forex: 3 ordens abertas (GBP/USD BUY, EUR/USD BUY, AUD/USD BUY)
- Freelas: Projeto Martin R$75 — planilha pronta, falta enviar
- Custo tokens: ~$3 hoje / ~$90 mês

📋 Pendências:
- Martin: sessão 99Freelas expirou (Turnstile)
- OANDA real: bug na plataforma. Exness como alternativa.
```

## Regras de Comunicação

- ✅ CONCISO: 10-15 linhas máx
- ✅ Só números que mudaram
- ✅ 🔴 no topo (o que importa)
- ❌ NUNCA listar "sistema OK, saúde OK, disco OK"
- ❌ NUNCA listar tarefas concluídas como conquista
- ❌ NUNCA "estou fazendo X, Y, Z" — só resultado

## Gatilhos de Report Automático

| Evento | Reportar? |
|--------|----------|
| Pagamento recebido | ✅ SIM — imediatamente |
| Cliente respondeu | ✅ SIM — imediatamente |
| Trade fechou com lucro >10 pips | ✅ SIM |
| Trade fechou com loss | ✅ SIM |
| Projeto novo relevante | ✅ SIM |
| Sessão expirou (precisa login) | ✅ SIM |
| Sistema caiu / bug grave | ✅ SIM |
| Tarefa concluída | ❌ NÃO (ruído) |
| Status OK / tudo normal | ❌ NÃO (ruído) |

## Anti-Padrões

- ❌ Relatórios longos com lista de tudo que foi feito
- ❌ "Estou trabalhando em X, Y, Z" — só resultado final
- ❌ Relatórios não solicitados
- ❌ Repetir o mesmo status várias vezes ao dia
