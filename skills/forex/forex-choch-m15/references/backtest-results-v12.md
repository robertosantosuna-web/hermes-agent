# Backtest Results — 29/05/2026

## Evolução da Estratégia

| Versão | Modelo | Dias | Trades | WR | R | PF | MaxDD |
|--------|--------|------|--------|-----|----|----|-------|
| v9.5 | M15 FVG simples | 30 | 144 | 27% | -11R | 0.77 | 13R |
| v10 | M1 FVG + Bias | 21 | 59 | 20% | -11R | 0.77 | 21R |
| v11 | + DMI M1 + ATR M1 | 5 | 10 | 60% | +14R | 4.50 | 2R |
| v11.1 | + DMI M5 + ATR M5 | 5 | 1 | 100% | +3R | ∞ | 0R |
| v11 dual | A (M1) + B (M5) | 5 | 9 | 55% | +11R | 2.50 | 2R |
| v12 agent | Multi-Agente (7p) | 21 | 110 | 62% | +162R | 4.86 | - |
| v12 agent | Multi-Agente (5p) | 21 | 62 | 63% | +94R | 5.09 | - |

## Performance por Par (v12, 21 dias, 7 pares)

| Par | Trades | WR | R |
|-----|--------|-----|----|
| XAUUSD | 12 | 83% | +28R |
| EURJPY | 12 | 75% | +24R |
| USDJPY | 13 | 54% | +15R |
| EURUSD | 11 | 55% | +13R |
| GBPUSD | 14 | 50% | +14R |

## Simulação Carteira $100 (21 dias)

| Modelo | Capital Final | Lucro | Trades/dia |
|--------|--------------|-------|------------|
| BT1 (7 pares) | $224 | +124% | 5.2 |
| BT2 (5 pares) | $160 | +60% | 3.0 |

**Veredito:** BT1 (7 pares) vence por compounding com mais trades.

## Lições Aprendidas

1. **FVG sem filtro = prejuízo** (27% WR em 30 dias)
2. **DMI sozinho ajuda mas não basta** (60% WR em 5 dias, 17% em 30)
3. **FVG Quality Scoring eliminou 92% dos trades ruins** (WR 24% → 40%)
4. **Multi-agente superou tudo** (62% WR, PF 4.86)
5. **Mais trades > melhor PF** para compounding (BT1 > BT2)
6. **Períodos de 5 dias enganam** — 60% WR em tendência vira 22% em 30 dias
7. **ADX > 20 necessário mas não suficiente**
