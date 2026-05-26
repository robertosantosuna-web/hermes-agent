---
name: income-tracker
description: "Rastreamento de receitas: pagamentos recebidos, trabalhos entregues, fontes de renda. Tracking de ROI por plataforma e projeções."
version: 1.0.0
---

# Income Tracker — Receitas e Pagamentos

## Por que existe

A ENTIDADE gasta tokens para operar. Cada token precisa gerar retorno ≥ custo. Esta skill rastreia tudo que entra para medir se estamos no lucro ou prejuízo.

## Arquivo de Registro

`~/.hermes/finance/income.json`

```json
{
  "updated": "2026-05-22T00:00:00-03:00",
  "token_cost_estimate": {
    "daily_avg_usd": 5.00,
    "monthly_estimate_usd": 150.00,
    "note": "Reduzido de ~$30/dia após motor local"
  },
  "transactions": [
    {
      "id": "inc-001",
      "date": "2026-05-19",
      "source": "99freelas",
      "project": "Martin L. - Clínicas Radiológicas",
      "type": "freelance",
      "amount_brl": 75.00,
      "amount_usd": 15.00,
      "status": "accepted",
      "paid": false,
      "payment_method": "99freelas"
    }
  ],
  "totals": {
    "brl_received": 0,
    "brl_pending": 75.00,
    "usd_received": 0,
    "usd_pending": 0
  }
}
```

## Projetos Ativos com Valor

| Projeto | Plataforma | Valor | Status |
|---------|-----------|-------|--------|
| Martin L. - Clínicas | 99Freelas | R$75 | Aceito, entregar |
| Planilha financeira | 99Freelas | Aberto | Proposta enviada |
| Discord tradução | 99Freelas | Aberto | Proposta enviada |

## Meta Financeira

- **Break-even mensal:** R$750 (~$150 USD em tokens)
- **Objetivo:** 2x break-even (R$1.500/mês) para reinvestir
- **Prazo:** 30 dias a partir de 22/05

## Como Atualizar

Após cada evento financeiro:

```bash
# Adicionar transação
python3 ~/.hermes/scripts/income_tracker.py add \
  --source 99freelas \
  --project "Martin L." \
  --amount 75 \
  --status accepted

# Ver resumo
python3 ~/.hermes/scripts/income_tracker.py summary
```

## Fontes de Renda (Potencial)

| Fonte | Tipo | Status | Potencial Mensal |
|-------|------|--------|-----------------|
| 99Freelas | Freelance | Ativo | R$200-500 |
| Forex (demo→real) | Trading | Em teste | Variável |
| Neevo | Micro-tarefas | Ativo | $10-30 |
| TimeBucks | Micro-tarefas | Ativo | $5-10 |
| Toloka | Micro-tarefas | Ativo | $5-20 |
| Workana | Freelance | Aguardando | R$100-300 |
| Crypto | Trading | Backtest | Variável |

## Monitoramento

Verificar semanalmente:
- [ ] Pagamentos recebidos
- [ ] Projetos pendentes de entrega
- [ ] Custo de tokens (dashboard da API)
- [ ] ROI por plataforma
- [ ] Projeção do mês

## Anti-Padrões

- NÃO contar dinheiro antes de receber
- NÃO aceitar projeto sem previsão de pagamento
- NÃO gastar mais tokens que a receita projetada
- NÃO ignorar projeto pago parado (Martin = R$75 parado)
