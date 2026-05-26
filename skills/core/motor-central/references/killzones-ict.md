# ICT Killzones — Horários e Estratégia CRT

## 3 Momentos de Pico (30 min cada)

| Killzone | BRT | GMT | Pares | Estratégia |
|----------|-----|-----|-------|------------|
| London Open | 04:00-04:30 | 07:00-07:30 | EUR/USD, GBP/USD, EUR/GBP | Sweep da Ásia + reversão |
| NY Open | **09:30**-10:00 | 12:30-13:00 | EUR/USD, GBP/USD, USD/JPY | Sweep de Londres + trend |
| London Close | 12:00-12:30 | 15:00-15:30 | Todos majors | Falso rompimento range/dia |

> ⚠️ NY Open é 09:30 BRT (NYSE open), não 10:00 BRT (FX desk). A abertura da bolsa de NY gera o pico real de volume.

## CRT — Candle Range Theory

### Detecção de Sweep
- Vela com pavio > 1.5× body que rompe high/low da vela anterior
- Sweep de alta: `h_cur > h1 AND upper_wick > body * 1.5 AND c < h_cur`
- Sweep de baixa: `l_cur < l1 AND lower_wick > body * 1.5 AND c > l_cur`

### Confirmação
- Sweep de alta + vela atual fecha acima do sweep → **VENDA** (stop hunt = sobe)
- Sweep de baixa + vela atual fecha abaixo do sweep → **COMPRA** (stop hunt = desce)

### Range Expansion (NR4/NR7)
- Range atual > 1.3× média dos últimos 5 candles → expansão explosiva
- NR4: range atual é o menor das últimas 4 velas → compressão antes de explosão

### Inside Bar
- `h_cur <= h1 AND l_cur >= l1` → indecisão
- Rompimento da máxima = COMPRA, rompimento da mínima = VENDA

## Parâmetros Validados (Simulação 18/05/2026)

| Parâmetro | Valor | Motivo |
|-----------|-------|--------|
| Stop mínimo | 5 pips | Stops < 5 = 75% loss por ruído |
| RR | 1:2 | Nenhum target 1:3 atingido |
| Alavancagem | 30x | Segurança nos picos |
| CRT stop | 50% do range da vela de sweep | 5-15 pips típico |
| CRT target | 150% do range | RR 1:2-1:3 |
| Score mínimo | 2.0 | CRT score combinado |
| Score forte | 3.5 | Sweep confirmado + expansão |

## Fontes (Grupo Sociedade Secreta do Cifrão)

- Série educacional completa (24 episódios): fundamentos forex, velas, sessões, killzones, liquidez, OBs, FVG, breakers, CRT
- Mentoria Mauricio Campos: análises mensais, vídeos de entradas reais, psicotrading
- CRT Theory: 10+ vídeos dedicados (CRT 5AM, 9AM, teoria 2025, turtle soup)
- Mark Douglas — Trading In The Zone (PDF, psicologia do trading)
