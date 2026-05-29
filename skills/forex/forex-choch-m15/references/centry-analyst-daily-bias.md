# Centry Analyst — Daily Bias Methodology

Fonte: PDF "Daily Bias - Centry Analyst.pdf" (29/05/2026)

## Conceito Central

Usar **PDH/PDL** (Previous Day High/Low) e **PWH/PWL** (Previous Week High/Low) como níveis de liquidez para determinar viés diário.

## Glossário

| Sigla | Significado |
|-------|-------------|
| PDH | Previous Day High (máxima do dia anterior) |
| PDL | Previous Day Low (mínima do dia anterior) |
| PWH | Previous Week High (máxima da semana anterior) |
| PWL | Previous Week Low (mínima da semana anterior) |

## Padrões

### Reversão (Reversal)
- Candle diário toma PDH ou PDL
- **Fecha DENTRO do range**
- Indica: reversão na direção contrária ao rompimento
- Ex: rompe PDH mas fecha abaixo → short (venda)

### Continuação (Continuation)
- Candle diário toma PDH ou PDL
- **Fecha FORA do range** (em continuação)
- Indica: continuação na direção do rompimento
- Ex: rompe PDL e fecha abaixo → short (venda)

## Níveis Semanais

Mesma lógica aplicada ao timeframe semanal:
- PWH/PWL como níveis de liquidez semanal
- Candle semanal que toma PWH/PWL e fecha dentro → reversão semanal
- Candle semanal que toma PWH/PWL e fecha fora → continuação semanal

## Aplicação no Bot

Integrar como filtro de **daily bias** antes de abrir trades:
1. No início do dia, calcular PDH e PDL
2. Monitorar o candle diário atual (D1)
3. Se houve rompimento de PDH/PDL, verificar fechamento
4. Daily bias = direção inferida do padrão
5. Só abrir trades alinhados com o daily bias

Combina com a estratégia H1→M1: H1 já dá a direção intradiária, o daily bias confirma o viés macro do dia.

## Referência

- YouTube: https://www.youtube.com/@CentryAnalyst
- Twitter: https://twitter.com/CentryAnalyst
- Discord: https://discord.gg/N3Qfa6pV
