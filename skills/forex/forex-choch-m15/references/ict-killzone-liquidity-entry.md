# ICT Killzone Strategy — Entrada por Liquidez

> Absorvido de Roberto (26/05/2026) — Metodologia completa H1→M5→M1

## Regra Fundamental

**ENTRADA É POR TOMADA DE LIQUIDEZ. NUNCA ANTES DO ROMPIMENTO.**

Não se entra no toque do nível, no rompimento sem confirmação, nem no ChoCh
do timeframe superior sem o inferior confirmar. A espera é parte da estratégia.

## Alvos de Liquidez

| Nível | O que é | Força do Setup |
|-------|---------|---------------|
| Asia Session H/L | Máx/Mín da sessão asiática (20-00 UTC) | Base |
| London Session H/L | Máx/Mín da sessão de Londres (03-06 UTC) | Média |
| NY Session H/L | Máx/Mín da sessão de NY (08-11 UTC) | Média |
| Daily High/Low | Máx/Mín do dia anterior | Forte |
| Weekly High/Low | Máx/Mín da semana anterior | Muito Forte |
| Monthly High/Low | Máx/Mín do mês anterior | Máximo |

**Confluência = setup mais forte.** Dois ou mais níveis no mesmo preço → prioridade máxima.

## Procedimento Fractal (3 etapas de confirmação)

```
1. H1: Preço ROMPE nível de liquidez → aguardar
2. M5: ChoCh com DESLOCAMENTO (vela grande + FVG) → marcar premium/desconto
3. M1: Preço chega no POI (>50% premium/desconto) → ChoCh com deslocamento → ENTRAR
```

**Deslocamento = agressividade institucional.** ChoCh sem deslocamento = ignorar.

## Regras de Gestão

- **SL:** topo/fundo que originou o ChoCh de M1
- **TP:** 3:1 (SL × 3)
- **Skip:** SL > 15 pips → setup inválido
- **Horários:** London Open (03-06 UTC) + London Close (15-16 UTC) + NY Open (08-11 UTC)

## O que NÃO fazer

- ❌ Entrar antes do rompimento do nível
- ❌ Entrar no rompimento sem ChoCh M5
- ❌ Entrar no ChoCh M5 sem confirmação M1
- ❌ Entrar em ChoCh sem deslocamento (sem vela grande + FVG)

## Scripts Relacionados

- `ict_killzone_detector.py` — detecta níveis de liquidez multi-nível (Asia/Daily/Weekly/Monthly)
- `smc_fractal_detector.py` — pivôs 5+1, MSS, FVGs, OB

A metodologia completa está em `~/.hermes/forex/ict_killzone_h1_m5_m1.md`.
