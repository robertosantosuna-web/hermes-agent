# MT5 Bridge History Extraction via MQL5 EA
## Técnica: Extrair histórico de ordens do MT5 usando EA bridge + comando "history"

### Contexto
O MT5 armazena histórico de ordens em arquivos binários proprietários (.dat).
Em vez de fazer engenharia reversa do formato binário, estendemos o EA bridge
(`hermes_bridge.mq5`) para responder ao comando `{"action":"history"}`.

### Arquitetura
```
Python → hermes_cmd.json → EA (MQL5) → MT5 API → hermes_resp.json → Python
         (Common/Files)    (OnTimer)   (History*)
```

### Localização dos arquivos
- **EA source**: `~/.wine/.../MQL5/Experts/hermes_bridge.mq5` (594 linhas)
- **EA compiled**: `~/.wine/.../MQL5/Experts/hermes_bridge.ex5`
- **Common Files**: `~/.wine/.../Terminal/Common/Files/hermes_cmd.json`
- **Response**: `~/.wine/.../Terminal/Common/Files/hermes_resp.json`

### Comandos suportados pelo EA
| Comando | Descrição |
|---------|-----------|
| `{"action":"status"}` | Saldo, equity, margem, posições abertas |
| `{"action":"order","symbol":"EURUSD","direction":"BUY","volume":0.01,"sl":X,"tp":Y}` | Abrir trade |
| `{"action":"close_all"}` | Fechar todas posições |
| `{"action":"close_symbol","symbol":"EURUSD"}` | Fechar posições de um símbolo |
| `{"action":"history","days":30}` | **NOVO — Histórico de ordens (30 dias)** |
| `{"action":"history","from":"2026-05-01","to":"2026-05-28"}` | **NOVO — Histórico por data** |
| `{"action":"symbol_info","symbol":"EURUSD"}` | Info do símbolo (spread, stoplevel) |
| `{"action":"modify_position","ticket":X,"sl":Y,"tp":Z}` | Modificar SL/TP |

### DoHistory() — MQL5 Implementation
A função foi adicionada ao `hermes_bridge.mq5` em 28/05/2026 (~130 linhas).
Usa as APIs nativas do MT5:
- `HistorySelect(from_date, to_date)` — seleciona período
- `HistoryDealsTotal()`, `HistoryDealGetTicket(i)` — itera deals
- `HistoryDealGetDouble(ticket, DEAL_PROFIT)` — P&L
- `HistoryDealGetInteger(ticket, DEAL_TIME)` — timestamp
- `HistoryOrdersTotal()`, `HistoryOrderGetTicket(j)` — itera ordens
- `HistoryOrderGetDouble(order, ORDER_PRICE_OPEN)` — preço entry

### Pitfalls da compilação MQL5
- **Escaping de strings**: No MQL5, `\"` é aspa escapada dentro de string. O patch tool do Hermes pode introduzir double-escaping (`\\\"` ao invés de `\"`). Verificar com `xxd` se necessário.
- **Correção binária**: Se o escaping estiver errado, substituir bytes `5c 5c 22` (três backslashes + quote) por `5c 22` (um backslash + quote).
- **StringFormat multi-linha**: MQL5 concatena strings adjacentes automaticamente (como C). Válido quebrar StringFormat em múltiplas linhas.
- **Compilação**: `F7` no MetaEditor. O EA recarrega automaticamente se 0 erros.
- **DPI do Wine**: Interface MT5 gigante = `LogPixels` alto no `user.reg`. Ajustar para `0x60` (96 DPI = 100%).

### DPI do Wine (issue relacionado)
- Arquivo: `~/.wine/user.reg`
- Chave: `"LogPixels"=dword:00000060` (96 DPI, 100% escala)
- Valores: `0x60`=96, `0x78`=120, `0xc0`=192
- Requer reinício do MT5 para aplicar
- Backup: `~/.wine/user.reg.bak`

### Script Python de extração
`~/.hermes/brain/mt5_history_extractor.py` — envia comando history e processa resposta.
- `--days 30` — últimos N dias
- `--from 2026-05-01 --to 2026-05-28` — período específico
- Output: `~/.hermes/forex/mt5_history.json`

### Resultado da extração (28/05/2026)
- 456 deals, 454 orders em 30 dias
- Saldo: $335.28 (IC Markets demo)
- WR: 22.6% (103W / 118L)
- P&L líquido: +$413.52
