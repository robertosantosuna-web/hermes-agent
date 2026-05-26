# Corretoras Forex com API Trading — Pesquisa 18/05/2026

## Ranking

### 🥇 OANDA — Melhor API REST
- **API**: REST v20, biblioteca `oandapyV20` (Python)
- **Conta demo**: Gratuita com dados reais
- **Regulação**: FCA (UK) + CFTC (US) + MAS (Singapura)
- **Endpoint practice**: `https://api-fxpractice.oanda.com`
- **Spreads**: ~1.0 pip EUR/USD (Standard)
- **Alavancagem**: 50:1 (US) / 30:1 (UK)
- **Token**: Gerado em Manage API Access após criar conta
- **Pitfall**: Cadastro via web requer interação manual (formulário React, Cloudflare)

### 🥈 Interactive Brokers — Melhor regulação
- **API**: REST Web API + TWS API, biblioteca `ib_insync` (Python)
- **Regulação**: SEC + FINRA + FCA (Tier-1 máximo)
- **Spreads**: 0.1 pip (interbancário de 17 dealers)
- **Comissão**: 0.20-0.08 bp, mín $2-$1

### 🥉 IC Markets — Melhores spreads
- **API**: MetaTrader 5 (mt5linux Python)
- **Spreads raw**: EUR/USD 0.01 pip
- **Alavancagem**: Até 500:1
- **Regulação**: FSA Seychelles (⚠️ não Tier-1)

### Outras testadas
- **Pepperstone**: FIX API (apenas institucional AUD$250M+), MT5 para retail
- **Deriv (Binary.com)**: WebSocket API, criação de conta virtual bloqueada (Permission Denied)
- **FXCM**: API Python `fxcmpy`, Cloudflare bloqueou acesso ao site
- **XM**: Sem REST API, apenas MT4/MT5

## Estratégia recomendada
- Desenvolvimento/testes: **OANDA demo** (REST mais simples)
- Produção: **Interactive Brokers** (segurança máxima) ou OANDA (FCA)
- Spread baixo: **IC Markets** MT5 (mas regulação offshore)

## Configuração OANDA
```json
// ~/.hermes/forex/oanda_config.json
{
  "practice": true,
  "token": "SEU_TOKEN_AQUI",
  "account_id": "SEU_ACCOUNT_ID_AQUI",
  "environment": "practice"
}
```

Comandos: `python3 oanda_client.py status|quote|trade|close_all`
