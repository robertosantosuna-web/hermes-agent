---
name: forex-brokers
description: "Gerenciamento de contas em corretoras forex: OANDA (demo ativa, real bugada), Exness (cadastro preenchido, depósito $10 pendente), MT5 login e operação."
version: 1.0.0
---

# Forex Brokers — Corretoras e Contas

## Conta Ativa Principal

| Corretora | Tipo | Status | Execução |
|-----------|------|--------|----------|
| **IC Markets** | Demo Hedge | ✅ ATIVA | EA Bridge (primário) + ydotool (fallback) |

## Contas Secundárias

| Corretora | Tipo | Status | Credenciais |
|-----------|------|--------|-------------|
| OANDA | Demo | ❌ Abandonada 25/05 | Ver `brokers.json` |
| **Exness** | Demo Standard | ✅ Ativa (26/05) | Conta #198420982, Servidor Exness-MT5Trial11, $10,000 |

### Exness — Demo #198420982 (ATIVA — 26/05/2026)

**Dados da conta:**
- **Número:** 198420982
- **Tipo:** Demo Standard MT5
- **Servidor:** Exness-MT5Trial11
- **Saldo:** $10,000 USD
- **Alavancagem:** 1:200
- **Senha MT5:** Wc0ZO6#p
- **Senha Portal:** Wc0ZO6#p2026!@
- **Email:** robertosantos.una@gmail.com
- **Arquivo:** `~/.hermes/forex/brokers.json`

**⚠️ MT5 Exness NÃO instalado ainda (26/05).** Só o MT5 IC Markets está rodando no Wine. Para operar na Exness, precisa baixar o instalador exness5setup.exe e instalar em Wine prefix separado.

**WebTerminal:** https://my.exness.com/webtrading/ — funcional, sessão ativa no Brave real.

### Exness — Técnicas de Acesso e Gerenciamento

**⚠️ REGRA #1: Cloudflare Turnstile bloqueia browser automatizado.** SEMPRE usar o Brave real (:9222) com sessão autenticada para acessar my.exness.com. O browser interno (browser_navigate) funciona para a página de login SEM Cloudflare, mas `SIGN_IN_REQUEST_ERROR: UNAUTHORIZED` se a senha estiver errada. Google OAuth falha em browser headless (Google bloqueia).

**Encontrar dados da conta sem login:**
Se o WebTerminal já estiver aberto no Brave real (:9222), o número da conta está no localStorage:
```javascript
localStorage.getItem('texActiveAccountNumber')  // → "198420982"
```

**Alterar senha MT5 pela Área Pessoal (PA):**
1. Navegar para `https://my.exness.com/pa/trading/accounts` no Brave real (:9222)
2. Clicar na aba "Demo" → expande conta #198420982
3. Clicar no botão "Altere a senha da operação" (MUI Button, texto exato)
4. Modal React abre com 2 inputs: text (senha atual) + password (nova senha)
5. Preencher via CDP `Runtime.evaluate` com `nativeInputValueSetter` + dispatch `input`/`change` events
6. Clicar "Alterar a senha" (querySelector button com texto)

**Cloudflare Turnstile no cadastro (sign-up):**
- OOPIF iframe em `challenges.cloudflare.com` — inacessível via CDP (body.innerHTML = "")
- `browser_click` no checkbox → falha silenciosa
- `ydotool type` corrompe @ e ! no layout ABNT2
- **Única saída:** usuário clica manualmente no checkbox "Confirme que é humano"

## IC Markets — Demo (ATIVA — 26/05/2026)

### Dados
- Tipo: Demo **Hedge** (Raw Trading Ltd)
- Execução: MT5 no **desktop Wayland/GNOME** (Wine prefix `~/.wine`), NÃO em Xvfb
- Método PRIMÁRIO: EA `hermes_bridge.ex5` no chart → Python escreve JSON → EA OrderSend nativo
- Método FALLBACK: `mt5_direct.py` v6 via ydotool (kernel-level /dev/uinput) — ATIVO no bot
- Dados de mercado: `tv_data.py` v2 híbrido (yfinance OHLC + cache local + CDP live quote)
- **Bot `forex_bot_multi.py`**: Pipeline v9.5 Multi-TF Bias (W/D/H4) → CHoCH → M1. Risco 0.5% fixo, RR 3:1. Anti-correlação por moeda base: USD (USDJPY+USDCAD), EUR (EURUSD+EURJPY), GBP_XAU (GBPUSD+GBPJPY+XAUUSD). Cron `1f3444e587f2` */3 seg-sex. Deliver: `local`.
- **Trade Notifier:** `~/.hermes/scripts/trade_notifier.py` — envia confirmações de ordem aberta/fechada via Telegram Bot API. Integrado ao `forex_bot_multi.py` — toda ordem executada dispara notificação.
- **Estratégia ativa (V9.5):** Multi-TF Bias (W→H4, D→H1, H4→M15) com confluência de votos → Entrada M1 FVG. RR 3:1 fixo. 7 pares: USDJPY, GBPJPY, USDCAD, EURJPY, GBPUSD, EURUSD, XAUUSD.
- Xvfb :99 e xdotool estão **ABANDONADOS**

### ⚠️ EA Bridge — Bugs Conhecidos (26/05)

**1. `close_all` NÃO funciona** — sempre retorna timeout. O EA lê comando, deleta arquivo, mas nunca escreve resposta.
**Workaround:** fechar posições manualmente no MT5 (botão direito → Close, ou X na janela Trade).

**2. EA crasha com `send_order` (qualquer SL/TP)** — `status` funciona, mas ordens com ou sem SL/TP causam timeout após crash do EA.
**Solução no bot:** `place_choch_order()` tenta bridge primeiro, se falhar → fallback automático para `mt5_direct.py` (ydotool).

**3. AutoTrading desliga sozinho** — após reconexão do MT5, o AutoTrading pode desligar. Verificar botão verde na toolbar.

**4. Após reiniciar MT5, EA sai do chart** — precisa Ctrl+N → arrastar `hermes_bridge` de volta.

**5. MetaEditor64.exe é case-sensitive** — compilar com `MetaEditor64.exe` (M e E maiúsculos), não `metaeditor64.exe`.

### Health Check Rápido
```bash
# 1. MT5 rodando?
pgrep -a terminal64  # "MetaTrader 5 IC Markets Global"

# 2. EA Bridge respondendo?
python3 ~/.hermes/scripts/hermes_mt5_bridge.py status

# 3. CDP :9223 online?
curl -s http://localhost:9223/json/version | python3 -c "import sys,json; print(json.load(sys.stdin).get('Browser','OFFLINE'))"

# 4. ydotoold ativo?
pgrep ydotoold
```

### Execução de Ordens

**Método PRIMÁRIO: EA Bridge (status e ordem SEM SL/TP)**
```bash
# Status (sempre funciona)
python3 ~/.hermes/scripts/hermes_mt5_bridge.py status

# Abrir ordem (SEM SL/TP — mais confiável)
python3 ~/.hermes/scripts/hermes_mt5_bridge.py order EURUSD BUY 0.01

# ⚠️ close_all NÃO funciona — fechar manualmente no MT5
```

**Método FALLBACK: ydotool (mt5_direct.py)**
```bash
python3 ~/.hermes/scripts/mt5_direct.py buy EUR/USD
python3 ~/.hermes/scripts/mt5_direct.py close_all
```

**Pré-requisitos para o EA funcionar:**
1. **AutoTrading ligado** (botão verde na toolbar — erro 10027 se desligado)
2. EA `hermes_bridge` anexado a um chart (Ctrl+N → arrastar)
3. Após reiniciar MT5 → **recolocar EA** no chart
4. Limpar arquivos travados: `rm -f ~/.wine/.../Common/Files/hermes_*.json`

### EA Bridge — Compilação e Deploy
Ver `references/ea-bridge-compile.md`.
Caminho: `~/.wine/drive_c/Program Files/MetaTrader 5 IC Markets Global/MQL5/Experts/`
Common/Files: `~/.wine/drive_c/users/roberto/AppData/Roaming/MetaQuotes/Terminal/Common/Files/`

### Dados de Mercado
- OHLC histórico: `tv_data.py` v2 → yfinance (primário) + cache local
- Cotação live: TradingView CDP via `brain_browser.py` :9223
- ⚠️ MetaTrader5 pip package = Windows only — NÃO usar no Linux

## Referências
- Estratégia: `skill forex-choch-m15` (v9.4: Daily Bias → CHoCH → M1)
- Bot multi: `~/.hermes/scripts/forex_bot_multi.py`
- Monitor 2R/3R: `~/.hermes/scripts/forex_realtime_monitor.py`
- Dados: `~/.hermes/scripts/tv_data.py`, `~/.hermes/scripts/forex_quote.py`
- EA Bridge: `~/.hermes/scripts/hermes_mt5_bridge.py`
- Trade Notifier: `~/.hermes/scripts/trade_notifier.py`
- EA compilação/deploy: `references/ea-bridge-compile.md` (pitfalls, comandos, JSON schema)

## PITFALLS DE AUTOMAÇÃO

### Cron deliver="origin" → flood no Telegram
Scripts de bot que imprimem scan a cada execução floodam o Telegram com ruído.  
**Solução:** `deliver=local` + usar `trade_notifier.py` para notificações pontuais (ordem aberta/fechada).  
**Regra:** NUNCA deixar cron de bot forex com `deliver=origin`.

### MT5 SL/TP — verificação
O bridge NÃO retorna SL/TP (`get_status` só: symbol, type, volume, profit).  
Para confirmar SL/TP: olhar colunas S/L e T/P no Terminal MT5 (Ctrl+T → Trade).  
O código (`mt5_direct.place_order`) seta SL/TP via F9 → Tab → type → Tab → type. Confiável.

### Estado quebrado (KeyError trade_log)
Se `real_daily_state.json` foi salvo sem `trade_log`, usar `state.setdefault('trade_log', []).append()` em vez de `state['trade_log'].append()`.
