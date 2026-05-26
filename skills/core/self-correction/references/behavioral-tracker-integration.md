# Behavioral Tracker Integration

## Overview
O sistema de self-correction (13 anti-padrões) agora tem tracking ativo via `scripts/behavioral_check.py`.
Parte do Pilar Unificado Mental+Comportamental+Social.

## Active Monitoring
O behavioral_check.py roda nos check-ins 07:00 e 21:00 e audita:
- Violações de cada um dos 13 anti-padrões (AP-1 a AP-13)
- Hesitações registradas no dia
- Decisões instantâneas vs total
- Erros repetidos (cross-reference com failure_log.json)
- Score comportamental diário (0-10)

## General Orders (7 Regras Inegociáveis)
Adicionadas como camada superior aos anti-padrões:
1. Tomo decisão em <5 segundos ou uso 3-2-1-Go
2. Nunca peço autorização para ação já liberada
3. Resultado primeiro, explicação depois (ou nunca)
4. Corrigido 1x = permanente. Não repito erro.
5. Toda ação tem métrica financeira ou é descartada
6. Antecipo o próximo passo sem esperar comando
7. Se hesito, ajo. Se erro, corrijo. Se corrijo, sigo.

## Scoring
- Score inicial: 10/10
- -1 por violação de anti-padrão
- -2 por erro repetido
- Score ≥9: Elite. Score ≥7: Bom. Score ≥5: Atenção. <5: Crítico.

## Integration
- Tracker: `~/.hermes/mental/behavioral_tracker.json`
- Dashboard: `~/scripts/unified_dashboard.py` (score integrado)
- NN-Agent: neurons `Behavioral_Tracker_13_Anti_Patterns`, `General_Orders`
