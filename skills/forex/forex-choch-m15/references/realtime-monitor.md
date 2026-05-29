# Monitor Tempo Real — Arquitetura e Operação

**Script:** `scripts/forex_realtime_monitor.py`  
**Início:** 26/05/2026 23:00 BRT  
**Polling:** 3 segundos  
**Tokens:** Zero (script no_agent)  
**Watchdog:** `fc2ef7b2b599` (*/1 minuto, script: `monitor_watchdog.sh`)

## Funcionalidades

### 1. Breakeven Automático
- **Forex:** Move SL para entry quando lucro ≥ $1.50 (~1R com 0.01 lote, SL 15p)
- **Metal (XAU):** Move SL para entry quando lucro ≥ $10.00 (~1R com 0.01 lote, SL $12)
- **Regra:** Só ativa uma vez por posição (evita spam de comandos)

### 2. Trailing Stop
- **Forex:** Ativa quando lucro ≥ $3.00 (~2R). Mantém 75% do lucro.
- **Metal:** Ativa quando lucro ≥ $20.00 (~2R). Mantém 75% do lucro.
- **Frequência:** Só move SL se melhoria > 3 pips da posição anterior
- **Direção:** BUY: SL sobe. SELL: SL desce.

### 3. Proteção de Perda
- **Forex:** Fecha posição se perda > $2.00
- **Metal:** Fecha posição se perda > $10.00
- **Thresholds alinhados com o AutoPilot** (cdbae3c13baa)

## Arquitetura de Comunicação

```
Monitor (Python, 3s loop)
    │
    ├── fcntl.flock(LOCK_EX) → .monitor_lock
    ├── Escreve JSON → Common/Files/hermes_cmd.json
    ├── Aguarda resposta → Common/Files/hermes_resp.json
    └── fcntl.flock(LOCK_UN)
         │
         ▼
    EA hermes_bridge.ex5 (MQL5, 250ms timer)
         │
         ├── Leitura: FileOpen(hermes_cmd.json, FILE_COMMON)
         ├── Processa: DoStatus / DoModifyPosition / DoCloseSymbol
         └── Resposta: FileWrite(hermes_resp.json)
```

## Estrutura de Arquivos

| Arquivo | Propósito |
|---------|-----------|
| `Common/Files/hermes_cmd.json` | Comando (escrito pelo Python, deletado pelo EA) |
| `Common/Files/hermes_resp.json` | Resposta (escrito pelo EA, lido pelo Python) |
| `Common/Files/.monitor_lock` | Lock file (fcntl) — previne conflitos |

## ⚠️ PITFALLS

### Conflito de Comandos
O EA bridge usa arquivos únicos. Se dois processos escrevem `hermes_cmd.json` simultaneamente, um sobrescreve o outro. O monitor usa `fcntl.flock(LOCK_EX | LOCK_NB)` para serializar acesso. **Comandos manuais devem pausar o monitor primeiro** (`pkill -STOP -f forex_realtime_monitor`).

### EA Precisa Estar Atualizado
O monitor requer **EA v1.1+** (com `modify_position` e `entry/sl/tp` no status). Se o EA for versão antiga:
- `entry`, `sl`, `tp` retornam 0 → monitor não age
- `modify_position` retorna "unknown action" → breakeven/trailing falham

### Entry Price Necessário
O monitor só funciona se o status do EA retornar `entry` (preço de abertura da posição). Sem entry, não é possível calcular breakeven ou trailing.

## Iniciar/Parar

```bash
# Iniciar (background)
python3 ~/.hermes/scripts/forex_realtime_monitor.py &

# Verificar se está rodando
pgrep -af forex_realtime_monitor

# Parar
pkill -f forex_realtime_monitor.py

# Watchdog (cron */1) garante reinício se cair
```

## Thresholds por Par

| Par | Breakeven | Trailing | Loss Limit |
|-----|-----------|----------|------------|
| EURUSD | $1.50 | $3.00 | -$2.00 |
| GBPUSD | $1.50 | $3.00 | -$2.00 |
| USDJPY | $1.50 | $3.00 | -$2.00 |
| GBPJPY | $1.50 | $3.00 | -$2.00 |
| EURJPY | $1.50 | $3.00 | -$2.00 |
| USDCAD | $1.50 | $3.00 | -$2.00 |
| **XAUUSD** | **$10.00** | **$20.00** | **-$10.00** |
