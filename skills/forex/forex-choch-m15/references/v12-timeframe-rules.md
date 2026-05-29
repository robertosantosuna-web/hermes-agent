# V12 — Regras de Timeframe (29/05/2026)

## Regra Zero: Tempo Mínimo para Estrutura

**ATR e DMI: timeframe MÍNIMO é M15.** Abaixo disso (M5, M1) é apenas tempo de ENTRADA.

```
Timeframe    Função                    Indicadores
─────────    ──────                    ───────────
D/H4         Viés de fundo             Multi-TF Bias, CRT candle+sweep
M15          Estrutura e confirmação   ATR(14), DMI(14)
M1           Entrada apenas            FVG (Fair Value Gap)
```

## Por que M15?

- **ATR no M15** captura o range real de 15 minutos — mais representativo que M1 (0.1-3 pips) ou M5
- **DMI no M15** mostra tendência de estrutura, não ruído de curto prazo
- M1 é ruidoso demais para indicadores de tendência — serve só para precisão de entrada

## SL Dinâmico

- **ATR(14) no M15 × 1.5**, clamp 10-30 pips forex / 200-300 ticks XAU
- Não usar ATR do M1 (muito pequeno, sempre cai no mínimo)
- Não usar ATR do M5 (intermediário, mas M15 é o padrão)

## DMI para Confirmação

- **DMI(14) no M15**: só entrar se DI+/DI- alinhado com o bias
- BUY: DI+ > DI- (força compradora)
- SELL: DI- > DI+ (força vendedora)
- DMI do M1 troca de sinal rápido demais — falsos rompimentos

## Backtest Comparison

| Versão  | ATR/DMI | FVG  | Trades | WR    | R     | PF   |
|---------|---------|------|--------|-------|-------|------|
| v10     | None    | M15  | 59     | 20.3% | -11R  | 0.77 |
| v11     | M1/M1   | M1   | 10     | 60.0% | +14R  | 4.50 |
| v11.1   | M5/M5   | M1   | 1      | 100%  | +3R   | ∞    |

**Conclusão:** DMI no M1 + ATR no M5/M15 deu o melhor equilíbrio (60% WR, PF 4.50). DMI no M15 é muito lento (1 trade em 5 dias).
