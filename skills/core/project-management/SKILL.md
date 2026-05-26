---
name: project-management
description: "Gestão de projetos: tracking de status, entregas, prazos, dependências, histórico de decisões e documentação por projeto."
version: 1.0.0
author: Roberto Rodrigues
license: MIT
metadata:
  hermes:
    tags: [projects, management, tracking, delivery, deadlines]
    related_skills: [life-os, freelancing-automation, financial-intelligence, dashboard]
---

# Project Management

Rastreamento de projetos ativos, entregas e decisões. Cada projeto tem identidade, status e histórico.

## ESTRUTURA DE PROJETO

### Diretório
```
~/projects/
  <cliente>-<projeto>/
    README.md        ← visão geral, status, contatos
    contract.md      ← escopo, valor, prazo
    decisions.md     ← decisões tomadas e porquê
    progress.md      ← log de progresso diário
    deliverables/    ← entregas
    src/             ← código (se aplicável)
```

### Template README.md
```markdown
# Projeto: [Nome]
Cliente: [Nome/Empresa]
Plataforma: [Fiverr/99Freelas/Direto]
Contato: [Email/Telefone/WhatsApp]

## Status: [PROSPECÇÃO|NEGOCIAÇÃO|EM EXECUÇÃO|ENTREGUE|PAGO]

## Escopo
- [Item 1]
- [Item 2]

## Valores
Valor total: R$ X
Forma pagamento: [À vista/Parcelado/Plataforma]
Recebido: R$ Y
Pendente: R$ Z

## Prazos
Início: [data]
Entrega: [data]
Horas estimadas: Xh
Horas gastas: Yh

## Stack
- [Tecnologia 1]
- [Tecnologia 2]

## Notas
[Observações, riscos, dependências]
```

## STATUS TRACKING

### Estados
```
🔵 PROSPECÇÃO    → lead identificado
🟡 CONTATO       → primeiro contato feito  
🟠 NEGOCIAÇÃO    → proposta enviada
🟢 EM EXECUÇÃO   → trabalhando ativamente
🔵 REVISÃO       → aguardando feedback
🟣 ENTREGUE      → submetido ao cliente
⏳ AGUARDANDO    → pagamento pendente
✅ CONCLUÍDO     → pago + review recebido
❌ CANCELADO     → projeto perdido/abandonado
```

### Comando de Status
```bash
echo "=== PROJETOS ATIVOS ==="
for d in ~/projects/*/; do
  status=$(grep "Status:" "$d/README.md" 2>/dev/null | head -1)
  echo "  $(basename $d): $status"
done
```

## DECISÕES (decisions.md)

Registrar TODA decisão não-trivial:
```markdown
## [DATA] Decisão: [título]

Contexto: [situação que levou à decisão]
Opções consideradas:
1. [Opção A] — prós/contras
2. [Opção B] — prós/contras
Decisão: [Opção X]
Motivo: [por que essa]
Impacto: [prazo +X dias, custo +R$Y, etc.]
```

## PROGRESSO (progress.md)

Log diário:
```markdown
## [DATA]
Feito: [o que foi concluído]
Bloqueios: [o que está travando]
Próximo: [próxima ação]
Horas: Xh
```

## DEPENDÊNCIAS

### Tracking
```
[Projeto A] → aguardando acesso ao servidor do cliente
[Projeto B] → aguardando feedback da entrega parcial
[Projeto C] → sem dependências, em execução
```

### Alerta
Se projeto bloqueado >48h → escalar com cliente
Se projeto bloqueado >1 semana → risco de cancelamento

## REVISÃO PÓS-ENTREGA

Após cada projeto concluído:
1. ROI real vs estimado
2. Horas reais vs estimadas (precisão da estimativa)
3. O que deu certo (replicar)
4. O que deu errado (não repetir)
5. Feedback do cliente (nota, comentário)
6. Lições aprendidas → salvar na memória

## MÉTRICAS AGREGADAS

```
Projetos este mês:    N ativos, M concluídos
Taxa de sucesso:      concluídos / total propostas
Precisão estimativa:  horas reais / horas estimadas (média)
Satisfação:           média de reviews
Tempo médio:          dias da prospecção ao pagamento
```

## ANTI-PADRÕES

- NÃO começar projeto sem escopo documentado
- NÃO entregar sem testar
- NÃO esquecer de pedir review
- NÃO acumular 3+ projetos ativos simultâneos
- NÃO deixar cliente sem update por >48h
