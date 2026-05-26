# Forex Pipeline v2 — Arquitetura Completa

**Data:** 18/05/2026 | **Versão:** 2.0

## Fluxo: Análise (T-5 min) → Execução (T+0)

```
04:55 BRT 🔍 Análise London → 05:00 🚀 Execução London
09:55 BRT 🔍 Análise NY  ⭐  → 10:00 🚀 Execução NY  ⭐
20:55 BRT 🔍 Análise Asia    → 21:00 🚀 Execução Asia
16:00 BRT 🔒 Fechar ordens (Sexta-feira)
```

7 cron jobs, Seg-Sex, `no_agent=True`, delivery via Telegram.

## Regras

| # | Regra | Descrição |
|---|-------|-----------|
| 1 | Day trade | Abre e fecha no mesmo dia (tracking: `ordens_abertas.json`) |
| 2 | News -5 min | Bloqueia ordens 15 min antes / 5 min depois de ★★★ | 
| 3 | Sexta ≤13h | Não abre novas ordens após 13:00 BRT |
| 4 | Sexta 16h | Fecha todas as ordens abertas |
| 5 | Fim de semana | Não opera sábado/domingo |
| 6 | Confirmação dupla | Re-check de dados frescos entre análise e execução |

## Algoritmo de Sinal

Score ponderado:
- **Recommend.All** × 2.0 (TradingView)
- **RSI** × 1.5 (<30 overbought, >70 oversold)
- **MACD vs Signal** × 1.0 (crossover)
- **Preço vs SMA20/50** × 1.0 (tendência)

Score > 1.5 = COMPRA | < -1.5 = VENDA | Entre = FRACO (segue Recommend)

## Arquivos

```
~/.hermes/forex/
├── tv_data.py                ← TradingView API (get_live_quotes)
├── forex_calendar.py         ← Filtro de notícias (should_block_trading)
├── simulacao_50x.py          ← Simulação alavancada
├── estado/                   ← Análises salvas (london.json, ny.json, asia.json)
├── historico/                ← Resultados de cada execução
└── ordens_abertas.json       ← Day trade tracking

~/.hermes/scripts/
├── forex_pipeline_v2.py      ← Pipeline principal
├── forex_analise_*.sh        ← Wrappers T-5 (3 picos)
├── forex_executar_*.sh       ← Wrappers T+0 (3 picos)
└── forex_fechar_sexta.sh     ← Fechamento Sexta 16:00
```

## Comandos

```bash
# Análise (5 min antes do pico)
/usr/bin/python3 ~/.hermes/scripts/forex_pipeline_v2.py analise --pico ny

# Execução (no horário do pico)
/usr/bin/python3 ~/.hermes/scripts/forex_pipeline_v2.py executar --pico ny

# Status geral
/usr/bin/python3 ~/.hermes/scripts/forex_pipeline_v2.py status

# Fechar todas as ordens (emergência ou sexta)
/usr/bin/python3 ~/.hermes/scripts/forex_pipeline_v2.py fechar
```

## Pitfalls

- **Python path:** Os scripts wrapper chamam `/usr/bin/python3` (não o venv do Hermes) porque as libs (requests, json) estão no sistema
- **Timezone:** Servidor em America/Bahia (BRT, GMT-3). Cron expressions em horário BRT
- **TradingView bloqueio:** Se a API mudar ou bloquear, fallback para Yahoo Finance (já implementado no tv_data.py)
