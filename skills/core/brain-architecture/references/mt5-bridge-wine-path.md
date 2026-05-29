# MT5 Bridge — Caminho Correto (Wine)

## PITFALL: O motor local lia o arquivo errado

O `motor_local.py` inicial lia `~/.hermes/forex/mt5_state.json` que NUNCA existia.
O arquivo real da bridge EA esta em:

```
~/.wine/drive_c/users/roberto/AppData/Roaming/MetaQuotes/Terminal/Common/Files/hermes_resp.json
```

## Caminhos importantes

| Arquivo | Caminho |
|---------|---------|
| EA Bridge source | `~/.wine/.../MQL5/Experts/hermes_bridge.mq5` |
| EA Bridge compiled | `~/.wine/.../MQL5/Experts/hermes_bridge.ex5` |
| Command file | `~/.wine/.../Common/Files/hermes_cmd.json` |
| Response file | `~/.wine/.../Common/Files/hermes_resp.json` |

## Exemplo de resposta

```json
{"status":"ok","balance":335.28,"equity":335.28,"margin":0.00,"positions":0,"positions_data":[]}
```

## History command (v1.2)

```json
{"action":"history","days":30}
```

Retorna deals e orders do historico do MT5.
Script extrator: `~/.hermes/brain/mt5_history_extractor.py`
