# EA Bridge History Command — v1.2 (28/05/2026)

## Nova funcionalidade: extração de histórico de ordens

Adicionado comando `history` ao EA `hermes_bridge.mq5` que retorna deals e ordens do histórico do MT5 via `HistorySelect()`, `HistoryDealsTotal()`, `HistoryOrderGetTicket()`, etc.

## Comandos suportados (v1.2)

```json
{"action":"history", "days": 30}
{"action":"history", "from": "2026-05-01", "to": "2026-05-28"}
```

## Resposta

```json
{
  "status": "ok",
  "action": "history",
  "from": "2026.04.29 00:25:16",
  "to": "2026.05.29 00:25:16",
  "total_deals": 456,
  "total_orders": 454,
  "deals": [{
    "ticket": 1379519269,
    "order": 1670000000,
    "symbol": "EURUSD",
    "type": "BUY",
    "volume": 0.01,
    "price": 1.16409,
    "profit": 0.00,
    "commission": -0.04,
    "swap": 0.00,
    "time": "2026.05.25 09:38:30"
  }],
  "orders": [{
    "ticket": 1670301896,
    "symbol": "USDJPY",
    "type": "BUY",
    "volume": 0.05,
    "price_open": 159.167,
    "sl": 159.102,
    "tp": 159.843,
    "time_setup": "2026.05.27 12:00:53",
    "time_done": "2026.05.27 12:05:06",
    "state": "ORDER_STATE_FILLED"
  }]
}
```

## Script de extração

```bash
python3 ~/.hermes/brain/mt5_history_extractor.py --days 30
```

Salva em `~/.hermes/forex/mt5_history.json`.

## ⚠️ PITFALL: escaping no MQL5

Ao editar o arquivo `.mq5`, NUNCA usar triple-escape (`\\\"`). O patch tool do Hermes pode introduzir escaping duplicado. Sempre verificar com `xxd` ou `python3 -c "open(...)"` se os bytes estão corretos.

Correto em MQL5:
```cpp
return "{\"status\":\"error\",\"msg\":\"unknown action: " + action + "\"}";
```

Bytes corretos: `5c 22` (backslash + quote), NÃO `5c 5c 5c 22` (3 backslashes + quote).

## ⚠️ PITFALL: compilação requer .ex5 deletado

O MetaEditor64 NÃO sobrescreve .ex5 existente. Sempre deletar antes de compilar:
```bash
rm -f "MQL5/Experts/hermes_bridge.ex5"
```

E verificar se o .ex5 foi criado após compilar:
```bash
ls -la "MQL5/Experts/hermes_bridge.ex5"
```

## ⚠️ PITFALL: DPI Wine

Para ajustar a resolução/DPI do MT5 no Wine:
```bash
# Ver DPI atual
grep "LogPixels" ~/.wine/user.reg

# Ajustar (0x60=96dpi 100%, 0x78=120dpi 125%, 0xc0=192dpi 200%)
sed -i 's/"LogPixels"=dword:000000c0/"LogPixels"=dword:00000060/g' ~/.wine/user.reg

# Reiniciar MT5 para aplicar
```
