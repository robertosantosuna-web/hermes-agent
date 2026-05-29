# SONA-lite Memory System for Freelancer Agent

Adaptação do sistema de aprendizado do Forex para freelancing.
Arquivo: `~/.hermes/brain/memory_freelancer.py`
Estado: `~/.hermes/forex/memory_weights.json`

## Arquitetura

```
7 CATEGORIAS com métricas independentes:
├── excel (keywords: planilha, spreadsheet, dashboard, macro, vba, fórmula)
├── data_entry (keywords: digitação, typing, cadastro, lista)
├── revisao (keywords: revisão, correção, ABNT, TCC, monografia)
├── traducao (keywords: tradução, translation, PT-EN, EN-PT)
├── python (keywords: script, automação, scraping, bot, API)
├── pdf_word (keywords: PDF, Word, converter, sumário)
└── virtual_assistant (keywords: assistente virtual, admin, suporte)
```

## Métricas por categoria

- `proposals_sent` — total de propostas enviadas
- `contracts_won` — contratos ganhos
- `conversion_rate` — taxa de conversão
- `avg_ticket_brl` / `avg_ticket_usd` — ticket médio
- `avg_delivery_hours` — tempo médio de entrega
- `roi_per_hour_brl` — R$/hora
- `best_template` — template com maior conversão
- `best_hour` — melhor horário para propor

## Templates ranqueados

Cada template tem:
- `uses` — vezes usado
- `wins` — vezes que converteu
- `conversion_rate` — taxa de conversão
- `deprecated` — flag se <10% após 5+ usos

## Replay Buffer

Últimos 200 eventos. Tipos:
- `proposal_sent` — proposta enviada
- `contract_won` — contrato ganho
- `proposal_lost` — proposta perdida

## Learning Cycle

```
OBSERVAR (job novo) → AGIR (proposta) → AVALIAR (resultado) → AJUSTAR (template)
     ↑                                                              |
     └──────────────────────────────────────────────────────────────┘
```

## Cold Start Problem

Sem dados iniciais, todas as 7 categorias aparecem como "oportunidade inexplorada".
Solução: inicializar com pesos empíricos baseados em pesquisa de mercado e especialistas:

```
Excel:      peso 0.8 (maior demanda, maior conversão)
Revisão:    peso 0.7 (demanda constante, ticket médio bom)
Python:     peso 0.6 (ticket alto, menos concorrência)
PDF/Word:   peso 0.5 (rápido, ticket ok)
Data Entry: peso 0.3 (volume alto, ticket baixo)
VA:         peso 0.2 (risco de cliente gruda)
Tradução:   peso 0.2 (muita concorrência)
```

## Correções pós-revisão (29/05)

- Keywords EN expandidas (35 termos) para Freelancer.com
- Negation check: regex PT/EN para evitar falsos positivos
- Multi-label: permitir top 2 categorias por job
- Exponential decay: eventos >30 dias = peso 0.1x (pendente implementar)
- Depreciação gradual: peso proporcional à taxa, não binário (pendente implementar)
