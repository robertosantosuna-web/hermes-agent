# Deploy Conta Real — Checklist

> Data: 2026-05-21 | Script: `~/.hermes/scripts/forex_bot_real_deploy.sh`

## Pré-requisitos

1. ✅ Bot script: `~/.hermes/scripts/forex_bot_real.py`
2. ✅ Python3 + yfinance + numpy
3. ✅ MT5 direct executor: `~/.hermes/scripts/mt5_direct.py`
4. ✅ Trade tracker: `~/.hermes/scripts/trade_tracker.py`
5. ✅ Xvfb :99 rodando
6. ✅ MT5 detectado no Xvfb :99
7. ✅ xdotool disponível
8. ❌ **Conta OANDA real** — PENDENTE (criar em oanda.com)

## Parâmetros da Conta Real

- Banca inicial: $100
- Volume: 0.01 (microlote, ~$0.10/pip)
- Risco: 3% por trade ($3 com $100)
- Stop diário: -5% ($5)
- Max posições simultâneas: 3
- Pares: GBP/USD, AUD/USD, NZD/USD, EUR/USD
- Horário: 24h Seg-Sex (fecha tudo sexta 16h BRT)

## Comandos

```bash
cd ~/.hermes/scripts

# Verificar pré-requisitos
./forex_bot_real_deploy.sh check

# Simular (sem ordens reais)
./forex_bot_real_deploy.sh dry-run

# Ativar conta real
./forex_bot_real_deploy.sh deploy

# Ver status
./forex_bot_real_deploy.sh status

# Pausar
./forex_bot_real_deploy.sh stop

# Reset diário
./forex_bot_real_deploy.sh reset
```

## O que falta para ligar

1. Criar conta real OANDA em https://www.oanda.com
2. Depositar $100
3. Conectar MT5 ao servidor `OANDA_Global-Live` (login + senha real)
4. Atualizar `~/.hermes/forex/brokers.json` com credenciais reais
5. Rodar `./forex_bot_real_deploy.sh deploy`
