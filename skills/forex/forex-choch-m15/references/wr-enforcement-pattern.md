# WR Enforcement Pattern (22/05/2026)

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
