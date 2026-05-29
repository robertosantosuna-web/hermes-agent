# Bot Troubleshooting — 26/05/2026

Sessão de debug: "Porque nao abriu ordem no mt5 icmarkt"

## Diagnóstico

Bot `forex_bot_real.py` (cron `21f7caf29606`, */15 seg-sex) não abria ordens.
Causa: **3 problemas em cascata**, nenhum era falta de sinais.

## Problema 1: WR enforcement bloqueando todos os pares

`trade_log.json` continha 12 trades antigos (20-22/05) de pares removidos da estratégia V7:
- AUD/USD: 1W/3L = 25%
- NZD/USD: 2W/0L = 100% (mas par removido)
- GBP/USD: 1W/3L = 25%
- EUR/USD: 0W/2L = 0%

WR agregado = 33.3% → `should_trade_pair()` bloqueava pares com WR < 50%.

**Solução:** Resetar trade_log.json (estratégia V7 é nova, pares diferentes).

## Problema 2: real_daily_state.json com balance stale

Arquivo `real_daily_state.json` tinha `balance: 85.30` de 22/05 (dia de loss).
`calculate_max_risk_sl()`: `risk_amount = 85.30 * 0.01 = 0.853`, `max_sl_pips = 0.853 / 10 ≈ 0.1 pips`.
Resultado: `[RISK] GBP/JPY BUY SL=3.0p > max=0.1p — pulando` para todos os pares.

**Solução:** Atualizar balance para $399.84 (real do MT5 via EA bridge).

## Problema 3: MT5 crash

Após resolver os bloqueios, o bot tentou abrir ordem mas:
- Primeiro: `retcode=10016` (Invalid stops) — SL/TP de teste estavam a 430 pips do preço
- Depois: timeout — MT5 havia crashado/reiniciado

Log do MT5 mostrava desconexão às 09:50 UTC e reconexão. `terminal64.exe` não estava mais rodando.

**Solução:** Usuário precisa reiniciar MT5, ligar AutoTrading, e colocar EA no chart.

## EA Bridge — Comportamento

- `get_status()` → ✅ funciona (retorna balance, equity, positions) — ÚNICO comando 100% confiável
- `send_order()` com SL=0, TP=0 → ⚠️ funciona na primeira vez, EA pode crashar depois
- `send_order()` com SL/TP → ❌ EA crasha (lê comando, deleta arquivo, nunca escreve resposta)
- `close_all()` → ❌ EA crasha (mesmo padrão: deleta arquivo, sem resposta)
- Timeout ocorre quando: MT5 offline, EA removido do chart, AutoTrading desligado, ou EA crashou
- **EA crasha com QUALQUER comando que chame `OrderSend()`** — após crash, nem `status` responde

### Padrão de crash do EA
1. Comando `order` ou `close_all` é escrito → EA lê e deleta `hermes_cmd.json`
2. EA chama `OrderSend()` → **crash** antes de `WriteResponse()`
3. Arquivo `hermes_resp.json` NUNCA é gerado → Python vê timeout
4. EA para de processar QUALQUER comando até ser removido e recolocado no chart

### Fallback no bot (implementado 26/05)
`place_choch_order()` tenta bridge primeiro, se falhar usa `mt5_direct.py` (ydotool):
```python
result = send_order(...)  # bridge
if result.get('status') == 'ok':
    return {...}
# Fallback
from mt5_direct import place_order
r2 = place_order(symbol, direction, VOLUME, sl, tp)
if r2 and r2.get('status') in ('sent', 'ok'):
    return {...}
```

### Correção: `calculate_max_risk_sl` para JPY (26/05)
Fórmula antiga: `pip_dollar = volume * 100000 * pip_val`
- EURUSD (pip_val=0.0001): 0.01 * 100000 * 0.0001 = $0.10/pip ✅
- GBPJPY (pip_val=0.01): 0.01 * 100000 * 0.01 = $10.00/pip ❌ (100x maior)

**Corrigido:** `pip_dollar = volume * 10.0` (~$0.10/pip para micro lote, todos os pares)

## MT5 Retcodes (IC Markets Hedge)

| Retcode | Significado | Ação |
|---------|-------------|------|
| 10009 | Done | ✅ Ordem executada |
| 10016 | Invalid stops | SL/TP muito longe ou invertidos |
| 10027 | AutoTrading disabled | Ligar botão verde na toolbar |
| 10030 | Unsupported filling mode | Usar ORDER_FILLING_IOC |

## Estado final da sessão

- ✅ trade_log.json resetado
- ✅ real_daily_state.json atualizado ($399.84)
- ✅ CDP :9223 iniciado
- ❌ MT5 precisa ser reiniciado pelo usuário (desktop Wayland)
- ❌ EA `hermes_bridge` precisa ser recolocado no chart
