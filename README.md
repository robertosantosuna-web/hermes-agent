# Hermes Agent — Forex Multi-Agente v12

Sistema autônomo de trading forex com 5 agentes especializados + self-learning.

## Instalação (PC novo)

```bash
git clone git@github.com:robertosantosuna-web/hermes-agent.git ~/.hermes
bash ~/.hermes/bootstrap.sh
```

## Iniciar

```bash
cd ~/.hermes/scripts
python3 forex_realtime_monitor.py &   # Monitor 2R/3R
python3 forex_bot_multi.py            # Bot principal
```

## Estrutura

```
scripts/
  forex_bot_multi.py      ← Bot principal (scan + execução)
  multi_agent.py          ← 5 agentes (Perfil, Sessão, Estrutura, Padrão, Confluência)
  fvg_quality.py          ← Scoring de qualidade FVG
  self_learning.py        ← Aprendizado contínuo (ajuste de pesos)
  forex_realtime_monitor.py ← Gestão 2R/3R (breakeven + trailing)
  validate_before_apply.py ← Validação pré-aplicação

brain/                    ← Cérebro neural (crons autônomos)
skills/                   ← Documentação e referências
cron/                     ← Jobs agendados
```

## Validar mudanças

```bash
python3 validate_before_apply.py
# Só aplica se: PF > 2.0 + WR > 45% + mínimo 5 trades
```

## Backtest

```bash
python3 _bt_agent.py     # Multi-agente 30 dias
```
