# ⚠️ PITFALL: WR enforcement ausente (corrigido 26/05)

O bot `forex_bot_multi.py` definia `MIN_WR_REAL = 50.0` mas **nunca chamava** a função de verificação. Os trades eram abertos usando o `backtest_wr` hardcoded (~67%) em vez do WR real da conta.

**Sintoma:** Bot abrindo ordens mesmo com WR real de 14.3% (1W/6L).

**Corrigido:** Adicionado `should_trade_pair(pair)` que:
- Lê `trade_log.json` e calcula WR real por par
- Bloqueia pares com WR < 50%
- Bloqueia pares com WR < 50% quando WR agregado < 35%

```python
def should_trade_pair(pair):
    wr_real = get_real_wr(pair, min_trades=3)
    if wr_real is not None and wr_real < MIN_WR_REAL:
        return False  # BLOQUEADO
    wr_agg = get_real_wr(min_trades=5)
    if wr_agg is not None and wr_agg < 35.0:
        if wr_real is not None and wr_real < 50.0:
            return False
    return True
```

Chamado no loop de scan antes de detectar sinais:
```python
if not should_trade_pair(base_pair):
    continue
```

---

# ⚠️ PITFALL: Filtro de correlação só checava trades NOVOS (corrigido 26/05)

O limite `MAX_CORRELATED_PAIRS = 2` só contava os trades sendo adicionados na execução atual, ignorando posições já abertas no MT5. Resultado: 4 USDCAD simultâneos.

**Corrigido:** Agora conta posições existentes via `status.get('positions_data')` do MT5:
```python
jpy_open = sum(1 for p in status.get('positions_data', [])
               if p.get('symbol') in correlated_groups['JPY'])
usd_open = sum(1 for p in status.get('positions_data', [])
               if p.get('symbol') in correlated_groups['USD'])
# Depois: jpy_count = jpy_open + sum(... novos ...)
```

---

# ⚠️ PITFALL: real_daily_state.json com balance stale

**Sintoma:** `calculate_max_risk_sl()` calcula SL máximo minúsculo (ex: 0.1 pips) e bloqueia entradas.

**Solução:** Atualizar com balance real do MT5:
```bash
python3 ~/.hermes/scripts/hermes_mt5_bridge.py status  # pega balance
cat > ~/.hermes/forex/real_daily_state.json << EOF
{"date": "$(date +%Y-%m-%d)", "balance": 399.0, "equity": 400.49, "pnl_today": 0, "updated": "$(date -Iseconds)", "trades_today": 0, "trade_log": []}
EOF
```

## Problem
Bot used hardcoded `cfg['wr']` from backtest (~67%) instead of real WR from trade_log. Results: opened orders despite real WR of 33% with -39.7 pips loss.

## Solution

```python
def get_real_wr(pair=None, min_trades=3):
    """Calculate real WR from trade_log.json. pair=None returns aggregate."""
    if os.path.exists(TRADE_LOG_PATH):
        log = json.loads(open(TRADE_LOG_PATH).read())
        if pair:
            closed = [t for t in log.get('trades', [])
                      if t.get('status') == 'closed' and t.get('pair') == pair 
                      and t.get('pnl') is not None]
        else:
            closed = [t for t in log.get('trades', [])
                      if t.get('status') == 'closed' and t.get('pnl') is not None]
        if len(closed) < min_trades:
            return None, len(closed)
        wins = [t for t in closed if t.get('result') == 'WIN']
        return round(len(wins) / len(closed) * 100, 1), len(closed)
    return None, 0

def should_trade_pair(pair):
    """Decide trading permission based on real + aggregate WR."""
    real_wr, n = get_real_wr(pair, min_trades=3)
    overall_wr, overall_n = get_real_wr(min_trades=10)
    
    # Rule 1: Pair has 3+ trades AND WR < 40% → BLOCK
    if real_wr is not None and real_wr < 40:
        return False, real_wr, f"WR={real_wr}% ({n}t) < 40%"
    
    # Rule 2: Pair has 2+ trades AND WR ≥ 80% → ALLOW (elite exception)
    elite_wr, elite_n = get_real_wr(pair, min_trades=2)
    if elite_wr is not None and elite_wr >= 80:
        return True, elite_wr, f"WR={elite_wr}% ({elite_n}t) — elite"
    
    # Rule 3: Aggregate 10+ trades AND WR < 35% → BLOCK pairs with WR < 50%
    if overall_wr is not None and overall_wr < 35:
        if real_wr is None or real_wr < 50:
            return False, real_wr, f"WR agg={overall_wr}% — need WR≥50%"
    
    # Rule 4: Less than 3 trades → ALLOW (use backtest as reference)
    if real_wr is None:
        return True, None, f"insufficient ({n}/3 trades)"
    
    return True, real_wr, f"WR={real_wr}% ({n}t)"
```

## Key Lesson
NEVER use backtest WR for live trading decisions. backtest_wr is a reference only. Self-learning was never implemented — it was just an intention. Real WR must come from trade_log.json, calculated fresh each cycle.
