# ICT Killzone Strategy — Regras de Ouro

## Princípio Central
**Entrada é POR TOMADA DE LIQUIDEZ. NUNCA ANTES.**

## Pipeline Completo

### Níveis de Liquidez (em ordem de força)
| Nível | O que é | Força |
|-------|---------|-------|
| 🌙 Asia Session H/L | High/Low da Ásia (20-00 UTC) | Base |
| 📅 Daily High/Low | Máx/Mín do dia anterior | Médio |
| 🕐 London Session H/L | Máx/Mín de Londres do dia anterior | Médio |
| 🕐 NY Session H/L | Máx/Mín de NY do dia anterior | Médio |
| 📅📅 Weekly High/Low | Máx/Mín da semana anterior | Forte |
| 📅📅📅 Monthly High/Low | Máx/Mín do mês anterior | Muito forte |

### Procedimento
1. H1: Preço se aproxima do nível de liquidez → ROMPE → liquidez TOMADA
2. M5: ChoCh com DESLOCAMENTO (vela grande + FVG = agressividade)
3. M5: Marcar Premium (>50% range) e Discount (<50% range)
4. M1: Marcar POIs (OB + FVG) na zona de premium (SELL) ou discount (BUY)
5. M1: Aguardar chegar no POI + ChoCh com deslocamento (fractal)
6. ENTRAR após ChoCh M1 confirmado
7. SL: topo/fundo que originou o ChoCh M1
8. TP: 3:1 (SL × 3)

### O que NUNCA fazer
- ❌ Entrar no toque do nível (sem rompimento)
- ❌ Entrar no rompimento sem ChoCh M5
- ❌ Entrar no ChoCh M5 sem confirmação M1
- ❌ Entrar sem deslocamento (vela pequena = sem instituição)

## Pares
- ✅ GBPJPY — funciona (57% WR simulação)
- ⚠️ EURJPY — marginal (37% WR)
- ❌ USDCAD — NÃO funciona com ICT

## Fontes
- Guia completo: ~/.hermes/forex/ict_killzone_h1_m5_m1.md
- Detector: scripts/ict_killzone_detector.py
- Simulador: scripts/ict_simulation.py
