# EA Bridge — Compilação, Deploy e Pitfalls

## Arquivos

| Arquivo | Local | Função |
|---------|-------|--------|
| `hermes_bridge.mq5` | `MQL5/Experts/` | Código fonte MQL5 |
| `hermes_bridge.ex5` | `MQL5/Experts/` | Compilado (EA) |
| `hermes_cmd.json` | `MQL5/Files/` (FILE_COMMON) | Comando do agente → EA |
| `hermes_resp.json` | `MQL5/Files/` (FILE_COMMON) | Resposta do EA → agente |
| `hermes_mt5_bridge.py` | `~/.hermes/scripts/` | Script Python que escreve/lê JSON |

## Caminho base MQL5

```
~/.wine/drive_c/Program Files/MetaTrader 5 IC Markets Global/MQL5/
```

## Compilar

```bash
DISPLAY=:99 WINEPREFIX=~/.wine wine \
  "C:\\Program Files\\MetaTrader 5 IC Markets Global\\metaeditor64.exe" \
  /compile:"MQL5\\Experts\\hermes_bridge.mq5" /log
```

Verificar resultado:
```bash
cat "MQL5/Experts/hermes_bridge.log" | strings | grep -E "error|warning|Result"
# Esperado: "Result: 0 errors, 0 warnings"
```

## Pitfalls conhecidos

### 1. ORDER_FILLING_FOK → retcode 10030 "Unsupported filling mode"
IC Markets conta Demo **Netting** não suporta `ORDER_FILLING_FOK`.
**Solução:** usar `ORDER_FILLING_IOC` (Immediate or Cancel).

### 2. AutoTrading disabled → retcode 10027
Botão "AutoTrading" na toolbar do MT5 precisa estar **verde** (clicar para ativar).
Sem isso, qualquer `OrderSend()` do EA retorna erro 10027.

### 3. EA não recarrega após recompilar
Após recompilar o `.ex5`, o MT5 **NÃO** recarrega automaticamente.
**Procedimento:**
1. Clique direito no chart → Expert Advisors → Remove
2. Ctrl+N (Navigator) → arrastar `hermes_bridge` de volta ao chart
3. Confirmar OK (manter configs padrão)

### 4. Caminho do MT5 mudou
O MT5 ativo está em `MetaTrader 5 IC Markets Global` (não `MetaTrader 5` ou `MetaTrader 5 IC Markets`).
Verificar com: `find ~/.wine -name terminal64.exe`

### 5. EA escreve em FILE_COMMON
Os arquivos de comando/resposta usam `FILE_COMMON`, que no Wine mapeia para:
```
~/.wine/drive_c/Program Files/MetaTrader 5 IC Markets Global/MQL5/Files/
```
O script Python (`hermes_mt5_bridge.py`) precisa escrever/ler nesse diretório.

## Estrutura do comando JSON

```json
{"action":"order","symbol":"EURUSD","direction":"BUY","volume":0.01,"sl":1.16000,"tp":1.17000}
{"action":"close_all"}
{"action":"status"}
```

## Resposta

```json
{"status":"ok","ticket":123456,"symbol":"EURUSD","direction":"BUY","volume":0.01,"price":1.16420}
{"status":"error","msg":"OrderSend failed","retcode":10027,"comment":"AutoTrading disabled by client"}
```
