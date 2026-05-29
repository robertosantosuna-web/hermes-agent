#!/usr/bin/env python3
"""
N. Accumbens — Reinforcement Learner (no_agent, zero tokens).
Learns from WIN/LOSS outcomes, dynamically adjusts pair weight scores.
Replaces static backtest WR with live performance data.

Runs daily at 18:00 BRT (after daily review).
Only outputs when weights change or new trades exist.
"""
import json, os
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

HERMES = Path(os.path.expanduser('~/.hermes'))
FOREX_DIR = HERMES / 'forex'
TRADE_LOG = FOREX_DIR / 'trade_log.json'
WEIGHTS_FILE = FOREX_DIR / 'pair_weights_live.json'
ACCUMBENS_OUT = HERMES / 'cron' / 'output' / 'n_accumbens'
STATE_FILE = FOREX_DIR / 'accumbens_state.json'

def load_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except:
        return None

def compute_weights(trades):
    """Compute win rates and P&L per pair from trade log."""
    pair_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0.0, 'total_rr': 0.0})
    
    for t in trades:
        pair = t.get('pair', 'UNKNOWN')
        pnl = t.get('pnl', 0) or 0
        result = t.get('result', '').upper()
        
        pair_stats[pair]['pnl'] += pnl
        
        if result == 'WIN':
            pair_stats[pair]['wins'] += 1
        elif result in ('LOSS', 'BE'):
            pair_stats[pair]['losses'] += 1
        
        # Track R:R if available
        rr = t.get('risk_reward') or t.get('rr')
        if rr:
            try:
                pair_stats[pair]['total_rr'] += float(rr)
            except:
                pass
    
    weights = {}
    for pair, stats in pair_stats.items():
        total = stats['wins'] + stats['losses']
        if total == 0:
            continue
        
        wr = round(stats['wins'] / total * 100, 1)
        avg_rr = round(stats['total_rr'] / total, 2) if stats['total_rr'] > 0 else None
        
        # Recommendation based on real performance
        if wr >= 65:
            rec = 'PRIORITY'
        elif wr >= 55:
            rec = 'ACTIVE'
        elif wr >= 45:
            rec = 'WATCH'
        else:
            rec = 'PAUSE'
        
        weights[pair] = {
            'wr': wr,
            'trades': total,
            'wins': stats['wins'],
            'losses': stats['losses'],
            'pnl': round(stats['pnl'], 1),
            'avg_rr': avg_rr,
            'recommendation': rec,
        }
    
    return weights

def compare_weights(old_w, new_w):
    """Return pairs whose recommendation changed."""
    changed = []
    for pair in set(list(old_w.keys()) + list(new_w.keys())):
        old_rec = old_w.get(pair, {}).get('recommendation')
        new_rec = new_w.get(pair, {}).get('recommendation')
        if old_rec != new_rec:
            changed.append({
                'pair': pair,
                'old': old_rec or 'NEW',
                'new': new_rec or 'REMOVED',
                'wr': new_w.get(pair, {}).get('wr'),
            })
    return changed

def main():
    data = load_json(TRADE_LOG)
    if not data:
        return  # Silent — no data
    
    trades = [t for t in data.get('trades', []) if t.get('result')]
    
    if len(trades) < 5:
        # ── SEED FROM BACKTEST ──
        # Use backtest WR to bootstrap live weights when no real trades yet
        backtest_wr = {
            'USDJPY': 66.1, 'GBPJPY': 67.6, 'USDCAD': 90.0,
            'EURJPY': 64.9, 'GBPUSD': 62.2, 'EURUSD': 73.8,
            'XAUUSD': 67.1,
        }
        weights = {}
        for pair, wr in backtest_wr.items():
            weights[pair] = {
                'wr': wr, 'trades': 0, 'wins': 0, 'losses': 0,
                'pnl': 0.0, 'avg_rr': None,
                'recommendation': 'PRIORITY' if wr >= 65 else ('ACTIVE' if wr >= 55 else 'WATCH'),
                'source': 'backtest_seed',
            }
        weight_data = {
            'updated': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
            'total_trades': 0,
            'pairs': weights,
            'seeded_from_backtest': True,
        }
        WEIGHTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        WEIGHTS_FILE.write_text(__import__('json').dumps(weight_data, ensure_ascii=False, indent=2))
        
        # Also save state
        ACCUMBENS_OUT.mkdir(parents=True, exist_ok=True)
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(__import__('json').dumps({
            'last_run': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
            'trades_processed': 0,
            'pairs_tracked': len(weights),
            'seeded': True,
        }, ensure_ascii=False, indent=2))
        print(f"🧠 N. Accumbens: Seeded {len(weights)} pairs from backtest WR")
        return
    
    new_weights = compute_weights(trades)
    old_weights = load_json(WEIGHTS_FILE)
    old_weights = old_weights.get('pairs', {}) if old_weights else {}
    
    # Only output when there are changes
    changed = compare_weights(old_weights, new_weights)
    
    # Always save updated weights
    weight_data = {
        'updated': datetime.now(timezone.utc).isoformat(),
        'total_trades': len(trades),
        'pairs': new_weights,
    }
    WEIGHTS_FILE.write_text(json.dumps(weight_data, ensure_ascii=False, indent=2))
    
    # Save state
    state = {
        'last_run': datetime.now(timezone.utc).isoformat(),
        'trades_processed': len(trades),
        'pairs_tracked': len(new_weights),
        'changes': changed,
    }
    ACCUMBENS_OUT.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    
    # ── Neural KB Integration ──
    try:
        from kb_bridge import write as kb_write, read as kb_read, query as kb_query
        # Write learning to shared KB
        kb_write('n_accumbens', {
            'pair_weights': new_weights,
            'learning_observations': changed,
            'last_learning': datetime.now(timezone.utc).isoformat(),
            'total_trades_processed': len(trades),
        })
        # Read market regime to adjust recommendations
        regime = kb_query('market_regime')
        if regime and regime != 'unknown':
            # Create synapse: learning correlates with market regime
            from kb_bridge import synapse
            active_pairs = [p for p, w in new_weights.items() if w.get('recommendation') in ('PRIORITY', 'ACTIVE')]
            if active_pairs:
                synapse('n_accumbens', 'chart_patterns',
                    f'Pairs {active_pairs} are active in {regime} regime — validate pattern quality',
                    confidence=0.7, evidence={'regime': regime, 'active_pairs': active_pairs})
    except ImportError:
        pass  # KB not available yet, no problem
    
    if changed:
        out = ACCUMBENS_OUT / f"learn_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        out.write_text(json.dumps({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'component': 'n_accumbens',
            'total_trades': len(trades),
            'pairs': new_weights,
            'changes': changed,
        }, ensure_ascii=False, indent=2))
        
        print(f"🧠 N. Accumbens: {len(new_weights)} pares rastreados, {len(changed)} mudanças")
        for c in changed:
            print(f"  {c['pair']}: {c['old']} → {c['new']} (WR: {c['wr']}%)")
    # else: silent — no changes

if __name__ == '__main__':
    main()
