---
name: forex-choch-m15
description: "Sistema Multi-Agente Forex V12 — 5 agentes + Self-Learning. Backtest 21d: 62% WR PF 4.86. Backtest 100d H1: 80.4% WR."
version: 12.1.0
---

# Forex Multi-Agent System V12

## Status

Rodando via cron */3 min seg-sex. MT5 bridge ativo. Pausado fins de semana.

## Arquitetura (5 Agentes)

| Agente | Função | Direção | Peso |
|--------|--------|---------|------|
| Perfil | Horário/sessão | Modificador (não vota) | 0.5-1.5x mult |
| Sessão | Volatilidade Asia | Modificador (não vota) | 0.5-1.5x mult |
| Estrutura | CRT pattern | Vota BUY/SELL | 1.5x |
| Padrão | FVG gap >= 2 pips | Vota BUY/SELL | 1.2x |
| Confluencia | Conselho | Decisão final | - |

## Regras de Ouro

1. **Perfil e Sessão NÃO votam direção** — são modificadores de peso (0.5-1.5x). Ver `references/perfil-sessao-modifiers.md`.
2. Só Estrutura e Padrão votam BUY/SELL
3. Gap FVG mínimo: 2 pips (subiu de 1 para filtrar trades ruins)
4. **Gate vs Bônus**: ver `references/gate-vs-bonus-lesson.md` — nunca confundir
5. Daily bias REAL dos dados (não fixo 'NEUTRAL')
7. **Telegram: só abertura/fechamento** ver `references/telegram-notifications.md`
8. RR 3:1 fixo
7. **Telegram notificações**: ver `references/telegram-notifications.md` — só abertura/fechamento

## Pré-Análise Semanal (+20.4pp WR) 🔥

**Maior fator de assertividade já descoberto.** Ver [references/weekly-bias-impact.md](references/weekly-bias-impact.md) e [references/weekly-pre-analysis.md](references/weekly-pre-analysis.md).

- Calcula força de 8 moedas via 11 pares (7 dias)
- Seleciona pares com maior divergência
- Direção: compra forte, vende fraca
- Resultado: WR 98.9% com viés vs 78.5% sem viés
- Script: `weekly_analysis.py` (rodar domingo), `replay_semanal.py` (validar)

## Performance por Agente (Replay 10d M15)

| Agente | WR Médio | Melhor Par |
|--------|---------|------------|
| Padrão (FVG) | 46% | GBPUSD 65.5% |
| Estrutura (CRT) | 18% | AUDUSD 37.5% |
| Conselho | 14% | ⚠️ pior que Padrão sozinho |

## Descoberta Crítica

**Padrão sozinho > Conselho atual.** O Conselho dilui a performance do Padrão.
Para 24h contínuo, OB simples em H1 (80.4% WR) funciona melhor que FVG em M15.
**Causa raiz**: Perfil e Sessao votavam NEUTRAL com confiança, diluindo o score total.
**Solução aplicada**: Perfil+Sessao viram modificadores de peso (0.5-1.5x). Estrutura+Padrão votam direção.

## Pitfall: ConfluenciaAgent Diluição

Se o ConfluenciaAgent voltar a ter threshold < 20% ou Perfil/Sessao voltarem a votar,
a performance cai drasticamente (de ~67% para ~14% WR). Testar sempre com replay_forex_agentes.py.

## Pares Prioritários

GBPUSD (65.5%), AUDUSD (55.8%), USDJPY (49.1%)
Removidos: EURUSD (10%), NZDUSD (9.7%) — FVG não funciona nestes pares

## Backtests

| Período | Timeframe | Trades | WR | PF | +R |
|---------|-----------|--------|-----|-----|-----|
| 21d M1 | yfinance | 110 | 62% | 4.86 | +162 |
| 100d H1 | TradingView | 1303 | 80.4% | - | +2889 |

## Comandos

```bash
# Dashboard ao vivo
forex-live              # Tela rica (Rich): trades MT5, P&L pips, sinais, bias

# Scanner
python3 ~/.hermes/scripts/forex_bot_multi.py

# Backtest unificado (forex + crypto)
python3 ~/.hermes/crypto/backtest_unificado.py

# Replay forex por agente
python3 ~/.hermes/crypto/replay_forex_agentes.py
```

## Diferenças Estruturais Forex vs Crypto

| Característica | Forex | Crypto |
|---------------|-------|--------|
| Horário | Seg-Sex, sessões | 24/7 |
| Padrão | FVG (pips) | OB (% preço) |
| Gate | Sessão London/NY | Tendência H1+H4 |
| SL | 10-20 pips | 0.15-0.3% |
| Correlação | Moeda base | Tudo vs BTC |
| Conselho | Atrapalha (14%) | Melhora (79.5%) |