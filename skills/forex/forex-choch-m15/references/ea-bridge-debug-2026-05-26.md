# EA Bridge Debug — 26/05/2026

Sessão completa de diagnóstico e correção do bot forex + EA bridge.

## Timeline

1. **Bot não abria ordens** — 3 causas identificadas:
   - `trade_log.json` com trades de AUD/NZD (estratégia antiga) → WR agregado 33.3% bloqueava tudo
   - `real_daily_state.json` com balance $85.30 → `calculate_max_risk_sl` limitava SL a 0.1 pips
   - MT5 crashou (`terminal64.exe` não respondia)

2. **MT5 instável** — crashou e reconectou várias vezes:
   - Log mostrou `connection lost` → `authorized on ICMarketsSC-Demo` → `terminal synchronized`
   - Após reconexão, AutoTrading desligava e EA saía do chart

3. **EA Bridge bugs descobertos**:
   - `status` funciona sempre
   - `send_order` com SL/TP → retcode 10016 (Invalid stops) quando SL muito distante
   - `send_order` sem SL/TP → abre posição mas depois EA crasha
   - `close_all` → sempre timeout (EA lê comando, deleta arquivo, nunca responde)
   - Após crash em qualquer OrderSend, EA para de responder até ser removido/recolocado

4. **Correções aplicadas no `forex_bot_real.py`**:
   - `calculate_max_risk_sl`: `pip_dollar = volume * 10.0` (antes: `volume * 100000 * pip_val` — 100x off para JPY)
   - `place_choch_order`: não crasha mais, retorna `None` e loga falha
   - `place_choch_order`: fallback automático bridge→mt5_direct.py (ydotool)
   - Loop principal: ignora `result is None` (continua para próximo sinal)

5. **Compilação do EA**:
   - `MetaEditor64.exe` é case-sensitive no Wine/Linux
   - Requer Xvfb :99 rodando
   - Comando: `DISPLAY=:99 WINEPREFIX=~/.wine wine MetaEditor64.exe /compile:"MQL5/Experts/hermes_bridge.mq5" /log`
   - EA recompilado com `Print()` de debug adicionados ao `OnTimer`

6. **Conta é HEDGE**, não Netting como documentado anteriormente

## Retcodes MT5 encontrados
- **10016** = Invalid stops (SL/TP mal configurados ou fora do Stoplevel)
- **10027** = AutoTrading disabled
- **10030** = Unsupported filling mode

## Padrão de recuperação do EA
Quando o EA para de responder:
```bash
# 1. Limpar arquivos travados
rm -f ~/.wine/drive_c/users/roberto/AppData/Roaming/MetaQuotes/Terminal/Common/Files/hermes_*.json

# 2. No MT5: Remove EA do chart (botão direito → Remove)
# 3. Ctrl+N → arrastar hermes_bridge de volta → OK
# 4. Verificar AutoTrading verde
```

## Logs do MT5
Local: `~/.wine/drive_c/Program Files/MetaTrader 5 IC Markets Global/logs/YYYYMMDD.log`
Formato: UTF-16LE (usar `strings` para extrair texto legível)
