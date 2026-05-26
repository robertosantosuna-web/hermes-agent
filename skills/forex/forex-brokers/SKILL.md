---
name: forex-brokers
description: "Gerenciamento de contas em corretoras forex: OANDA (demo ativa, real bugada), Exness (cadastro preenchido, depósito $10 pendente), MT5 login e operação."
version: 1.0.0
---

# Forex Brokers — Corretoras e Contas

## Conta Ativa Principal

| Corretora | Tipo | Status | Execução |
|-----------|------|--------|----------|
| **IC Markets** | Demo | ✅ ATIVA | MT5 display:0, ydotool |

## Contas Abandonadas

| Corretora | Motivo |
|-----------|--------|
| OANDA | Abandonada 25/05 — usar apenas IC Markets. Demo #1715539800 desativada. |
| Exness | Nunca ativada. Depósito $10 nunca feito. |

## IC Markets — Demo (ATIVA)

### Dados
- Tipo: Demo **Netting** (Raw Trading Ltd — verificado 25/05 no título da janela)
- Execução: MT5 no Xvfb **display :99** (Wine prefix ~/.wine_mt5)
- Orders: `mt5_order_executor.py` / `mt5_direct.py` via **xdotool** (F9 + Alt+B/S) no :99
- Fonte de dados: TradingView CDP (brain_browser.py :9223 IPv6 headless), NÃO Yahoo Finance
- Pipeline: `brain_signal_generator.py` → `signals_pending.json` → agente valida → `mt5_order_executor.py`

### Status atual (25/05)
- MT5 rodando no Xvfb :99 via Wine, sessão persiste
- Xvfb NÃO persiste reboot — precisa iniciar manualmente
- Bot forex_bot_real.py funcional (TradingView CDP, zero Yahoo Finance)
- Yahoo Finance REMOVIDO de todos os scripts ativos (brain_gateway, forex_bot, forex_bot_real)
- CRT filter obrigatório (backtest: 87.5% WR vs 61.1% sem)

## MT5 — Operação Técnica

### Localização (ATUALIZADO 25/05)
O MT5 ativo está em **dois Wine prefixes**:
- **IC Markets Global** (principal, conta demo Netting): `~/.wine/drive_c/Program Files/MetaTrader 5 IC Markets Global/terminal64.exe`
- **MetaTrader 5** (genérico, possivelmente antigo): `~/.wine_mt5/drive_c/Program Files/MetaTrader 5/terminal64.exe`

### Inicialização
```bash
# 1. Xvfb (se não estiver rodando)
Xvfb :99 -screen 0 1280x900x24 &

# 2. MT5 IC Markets via Wine
DISPLAY=:99 WINEPREFIX=~/.wine wine "C:\\Program Files\\MetaTrader 5 IC Markets Global\\terminal64.exe" &

# 3. Verificar
DISPLAY=:99 xdotool search --name "MetaTrader"
DISPLAY=:99 xdotool getwindowname <ID>
```

### Execução de Ordens — EA Bridge (MÉTODO PRIMÁRIO)
**xdotool está OBSOLETO.** Usar o EA `hermes_bridge.ex5` + script Python:

```bash
# Enviar ordem (SL/TP opcionais)
python3 ~/.hermes/scripts/hermes_mt5_bridge.py order EURUSD BUY 0.01
python3 ~/.hermes/scripts/hermes_mt5_bridge.py order EURUSD SELL 0.01 1.16000 1.17000

# Status da conta
python3 ~/.hermes/scripts/hermes_mt5_bridge.py status

# Fechar todas as posições
python3 ~/.hermes/scripts/hermes_mt5_bridge.py close_all
```

**Pré-requisitos para o EA funcionar:**
1. **AutoTrading ligado** no MT5 (botão verde na toolbar — erro 10027 se desligado)
2. EA anexado a um chart (arrastar do Navigator)
3. Após recompilar o `.ex5`, **remover e recolocar** o EA no chart (MT5 não recarrega automaticamente)

### EA Bridge — Compilação e Deploy
Ver `references/ea-bridge-compile.md` para o guia completo.
Caminho MQL5: `~/.wine/drive_c/Program Files/MetaTrader 5 IC Markets Global/MQL5/Experts/`

### Dados de Mercado
⚠️ MetaTrader5 pip package NÃO funciona no Linux (Windows-only).
Dados OHLCV vêm do TradingView CDP via `brain_browser.py` (9223 IPv6, headless).
Cotações em tempo real via `forex_quote.py`.
Drop-in replacement do yfinance: `tv_data.py` (retorna pandas DataFrame compatível).

## Referências
- Estratégia: `skill forex-choch-m15`
- Bot paper: `~/.hermes/scripts/forex_bot.py`
- Bot real: `~/.hermes/scripts/forex_bot_real.py`
- Dados: `~/.hermes/scripts/tv_data.py`, `~/.hermes/scripts/forex_quote.py`
- EA Bridge: `~/.hermes/scripts/hermes_mt5_bridge.py`
- EA compilação/deploy: `references/ea-bridge-compile.md` (pitfalls, comandos, JSON schema)
