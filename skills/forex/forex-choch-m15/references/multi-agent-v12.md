# Multi-Agent System V12 (29/05/2026)

## Arquitetura

5 agentes especializados votam para decidir entrada:

| Agente | Função | Peso | Como vota |
|--------|--------|------|-----------|
| PERFIL | Perfil do par por sessão | 1.0x | WR histórico da sessão (Asia/London/NY) |
| SESSÃO | Ásia como preditora | 1.0x | Range asiático vs pré-asiático |
| ESTRUTURA | CRT + Order Block + Swings | 1.5x | CRT setup + OB + estrutura HH/HL |
| PADRÃO | FVG quality scoring | 1.2x | Premium/discount + gap + mitigação |
| CONFLUÊNCIA | Maioria decide | - | Confiança mínima 30% |

## Backtest Results

| Período | Trades | WR | R | PF | Trades/dia |
|---------|--------|-----|----|----|------------|
| 21 dias (7 pares) | 110 | 62% | +162R | 4.86 | 5.2 |
| 21 dias (5 pares) | 62 | 63% | +94R | 5.09 | 3.0 |

Melhores pares: XAUUSD (83% WR), EURJPY (75% WR)

## Self-Learning

- `self_learning.py` ajusta pesos dos agentes baseado em resultado real
- Agentes que acertam ganham peso (+5% por WIN)
- Agentes que erram perdem peso (-5% por LOSS)
- Histórico salvo em `~/.hermes/forex/agent_learning.json`

## Regras de Ouro

1. **RR 3:1 fixo** — NUNCA reduzir (Roberto recusou 2:1)
2. **Testar antes de aplicar** — `validate_before_apply.py` (PF>2.0, WR>45%, min 5 trades)
3. **CRT é filtro, não substituto** — soma ao bias, não substitui
4. **ATR/DMI mínimo M15** — abaixo disso é ruído de entrada
5. **M1 é entrada, não estrutura** — usar M15+ para confirmação
6. **Cada par tem comportamento único** — XAUUSD ≠ EURUSD ≠ USDJPY
7. **Ásia lateralizada** = London breakout provável
8. **Anti-correlação** — máx 1 par por moeda base

## FVG Quality Scoring (fvg_quality.py)

Eliminou 92% dos trades ruins. Critérios:
- Gap mínimo > 2 pips (obrigatório)
- Premium/Discount (30pts) — compra em discount, venda em premium
- Tendência alinhada (25pts)
- First touch / não mitigado (20pts)
- Threshold ideal: 45-50

## Pipeline Completo

```
1. fetch_ohlcv → CDP TradingView (M1) ou yfinance fallback
2. Multi-TF Bias (W/D/H4) → define BUY/SELL/NEUTRAL
3. 5 agentes analisam → maioria vota
4. Se NEUTRAL ou confiança < 30% → pula
5. SL = ATR(M5)×1.5, clamp 10-30p
6. Entrada M1 via EA bridge ou mt5_direct fallback
7. Monitor 2R/3R gerencia posição
8. Self-learning registra resultado e ajusta pesos
```

## Scripts

| Script | Função |
|--------|--------|
| forex_bot_multi.py | Bot principal com multi-agente |
| multi_agent.py | 5 agentes de análise |
| fvg_quality.py | Scoring de qualidade FVG |
| self_learning.py | Aprendizado contínuo |
| validate_before_apply.py | Validação pré-aplicação |
| forex_realtime_monitor.py | Gestão 2R/3R |
| tv_data.py | Fonte dados híbrida (CDP+yfinance) |
| tv_ohlc_extractor.py | Extrator CDP TradingView |
