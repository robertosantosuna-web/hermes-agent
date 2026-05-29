# Lições da Sessão 29/05/2026

## Regras Absolutas (NUNCA violar)
1. **RR 3:1 fixo** — Roberto recusou RR 2:1 explicitamente. Nunca sugerir reduzir.
2. **M15 é tempo mínimo de estrutura** — ATR e DMI devem ser calculados no M15 ou acima. M1 e M5 são apenas tempo de entrada.
3. **CRT é filtro adicional, NÃO substituto** — soma conhecimento, não substitui o bias multi-TF.
4. **Validar em backtest antes de aplicar** — `validate_before_apply.py` deve rodar antes de qualquer mudança no bot ao vivo.

## O que Funcionou (backtest comprovado)
- Multi-Agente (5 agentes) — 62% WR, +162R, PF 4.86 em 21 dias
- Modelo dual A+B — 55% WR, +11R, PF 2.50 em 5 dias
- FVG Quality Scoring — eliminou 92% dos trades ruins (threshold 55)
- DMI como filtro de tendência (alinhado com bias)
- ATR como SL dinâmico (2x ATR)

## O que NÃO Funcionou
- Engolfo como filtro — nunca coincide com FVG no M1
- 2 candles de confirmação — restritivo demais para M1
- RSI como filtro isolado — não fez diferença significativa
- ADX > 20 sem DMI — 22% WR, perde dinheiro

## Hierarquia de Timeframes (Centry Analyst + CRT)
```
Mensal → CHoCH Diário
Semanal → CHoCH H4
Diário → CHoCH H1
H4 → CHoCH M15
H1 → CHoCH M5
M15 → CHoCH M1/M5
```
Tempo mínimo para estrutura: M15. Abaixo disso é só entrada.

## Agentes (ordem de importância)
1. ESTRUTURA (peso 1.5x) — CRT + Order Block + Swing Points
2. PADRÃO (peso 1.2x) — FVG com scoring premium/discount
3. SESSÃO — Ásia como preditora de London
4. PERFIL — perfil do par por sessão
5. CONFLUÊNCIA — maioria decide, confiança mínima 30%

## Self-Learning
- Peso dos agentes ajustado por resultado real
- Quem acerta ganha peso (+5%), quem erra perde (-2%)
- Histórico salvo em agent_learning.json
- Módulo: self_learning.py
