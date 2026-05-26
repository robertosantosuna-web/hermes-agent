# Calendário Econômico Forex — Regras de Blackout

**Data:** 18/05/2026
**Fonte:** Políticas compiladas de IQ Option, Olymp Trade, Deriv, XM, IC Markets, MetaTrader

## Política de Blackout

| Importância | Antes | Depois | Exemplos |
|------------|-------|--------|----------|
| ★★★ RED | 15 min | 5 min | NFP, FOMC, CPI, ECB, BOE, BOJ |
| ★★ ORANGE | 10 min | 3 min | Jobless Claims, ISM, GDP, Retail Sales |
| ★ YELLOW | 5 min | 2 min | Speeches, Auctions, Market Open |

## Janelas Diárias Fixas (GMT → BRT)

| GMT | BRT | Janela | Moedas |
|-----|-----|--------|--------|
| 12:30 | **09:30** | US MAIN data (NFP, CPI, Retail) | USD |
| 14:00 | **11:00** | US secondary (ISM, Sentiment) | USD |
| 18:00 | **15:00** | FOMC window | USD |
| 23:50 | **20:50** | Japan data (GDP, CPI, Tankan) | JPY |
| 01:30 | **22:30** | AU data (Employment, GDP) | AUD |
| 06:00 | **03:00** | UK/Europe data (CPI, GDP, PMI) | GBP/EUR |
| 09:00 | **06:00** | European data (IFO, ZEW) | EUR |

## Validação: Picos vs Blackouts

Todos os picos de trading estão FORA das janelas de blackout:

```
09:15-09:35 ★★★ US MAIN blackout → 09:55 Análise NY ✅ (20 min depois)
10:50-11:03 ★★ US SEC blackout  → 10:00 Execução NY ✅ (50 min antes)
14:45-15:05 ★★★ FOMC blackout   → Não afeta nenhum pico
20:40-20:53 ★★ Japan blackout    → 20:55 Análise Asia ✅ (2 min depois)
```

## Eventos de Alto Impacto (Calendário Fixo)

| Evento | Frequência | GMT | Moedas |
|--------|-----------|-----|--------|
| NFP + Unemployment | 1ª sexta do mês | 12:30 | USD |
| CPI (Consumer Price Index) | Meio do mês | 12:30 | USD |
| FOMC Rate Decision | 8x/ano (qua) | 18:00 | USD |
| Retail Sales | Meio do mês | 12:30 | USD |
| GDP (US) | Trimestral | 12:30 | USD |
| ECB Rate Decision | 6x/ano (qui) | 12:15 | EUR |
| BOE Rate Decision | 6x/ano (qui) | 11:00 | GBP |
| BOJ Rate Decision | 8x/ano (sex) | ~03:00 | JPY |
| RBA Rate Decision | 8x/ano (ter) | 04:30 | AUD |

## Módulo Python

`~/.hermes/forex/forex_calendar.py`
- `get_news_blackout_status(pairs)` — verifica se está em blackout agora
- `should_block_trading(pico_key, pairs)` — regra completa com sexta-feira
- `get_next_news_window()` — próximas janelas de notícias
