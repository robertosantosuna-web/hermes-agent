#!/usr/bin/env python3
"""
Hippocampus — Pattern Consolidator (no_agent, zero tokens).
Consolidates patterns from logs: trade behavior, failure recurrence,
thalamus event patterns, self-evolution tracking.

Runs weekly (Sunday 10:00 BRT). Complements existing Weekly Memory Consolidation cron.
"""
import json, os
from pathlib import Path
from datetime import datetime, timezone, timedelta

HERMES = Path(os.path.expanduser('~/.hermes'))
HIPPOCAMPUS_OUT = HERMES / 'cron' / 'output' / 'hippocampus'
PATTERNS_FILE = HERMES / 'hippocampus_patterns.json'

def load_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except:
        return None

def analyze_trade_patterns():
    """Analyze trade log for patterns."""
    trade_log = load_json(HERMES / 'forex' / 'trade_log.json')
    if not trade_log:
        return None
    
    trades = trade_log.get('trades', [])
    if len(trades) < 3:
        return None
    
    patterns = {
        'total': len(trades),
        'wins': sum(1 for t in trades if t.get('result') == 'WIN'),
        'losses': sum(1 for t in trades if t.get('result') in ('LOSS', 'BE')),
        'by_day': {},
        'by_session': {},
        'avg_pnl_win': 0,
        'avg_pnl_loss': 0,
    }
    
    win_pnls = []
    loss_pnls = []
    
    for t in trades:
        result = t.get('result', '').upper()
        pnl = t.get('pnl', 0) or 0
        ts = t.get('timestamp', '') or t.get('entry_time', '')
        
        if result == 'WIN':
            win_pnls.append(pnl)
        elif result in ('LOSS', 'BE'):
            loss_pnls.append(pnl)
        
        # Day of week
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            dow = dt.strftime('%A')
            patterns['by_day'][dow] = patterns['by_day'].get(dow, {'trades': 0, 'wins': 0})
            patterns['by_day'][dow]['trades'] += 1
            if result == 'WIN':
                patterns['by_day'][dow]['wins'] += 1
        except:
            pass
    
    if win_pnls:
        patterns['avg_pnl_win'] = round(sum(win_pnls) / len(win_pnls), 1)
    if loss_pnls:
        patterns['avg_pnl_loss'] = round(sum(loss_pnls) / len(loss_pnls), 1)
    
    return patterns

def analyze_failure_patterns():
    """Analyze failure log for recurring categories."""
    failures = load_json(HERMES / 'failure_log.json')
    if not failures:
        return None
    
    by_category = {}
    for f in failures.get('failures', []):
        cat = f.get('category', 'unknown')
        by_category[cat] = by_category.get(cat, 0) + 1
    
    # Find categories with 3+ failures
    recurring = {k: v for k, v in by_category.items() if v >= 3}
    
    return {
        'total_failures': len(failures.get('failures', [])),
        'by_category': by_category,
        'recurring': recurring,
        'open': sum(1 for f in failures.get('failures', []) if f.get('status') == 'pending'),
    }

def analyze_evolution():
    """Check self-evolution cycle completion."""
    evo = load_json(HERMES / 'self_evolution_log.json')
    if not evo:
        return None
    
    cycles = evo.get('cycles', [])
    completed = [c for c in cycles if c.get('status') == 'completed']
    in_progress = [c for c in cycles if c.get('status') == 'in_progress']
    
    return {
        'total_cycles': len(cycles),
        'completed': len(completed),
        'in_progress': len(in_progress),
        'recent_topic': cycles[-1].get('research_topic') if cycles else None,
    }

def main():
    now = datetime.now(timezone.utc)
    
    patterns = {
        'timestamp': now.isoformat(),
        'component': 'hippocampus',
        'trade_patterns': analyze_trade_patterns(),
        'failure_patterns': analyze_failure_patterns(),
        'evolution_status': analyze_evolution(),
    }
    
    # Save patterns
    HIPPOCAMPUS_OUT.mkdir(parents=True, exist_ok=True)
    
    # Load previous patterns to detect changes
    prev = load_json(PATTERNS_FILE)
    
    # Always save current
    PATTERNS_FILE.write_text(json.dumps(patterns, ensure_ascii=False, indent=2))
    
    # Check if anything changed
    trade = patterns.get('trade_patterns')
    fail = patterns.get('failure_patterns')
    evo = patterns.get('evolution_status')
    
    has_content = trade or fail or evo
    
    if not has_content:
        return  # Silent
    
    # Output summary
    out_file = HIPPOCAMPUS_OUT / f"consolidation_{now.strftime('%Y%m%d_%H%M%S')}.json"
    out_file.write_text(json.dumps(patterns, ensure_ascii=False, indent=2))
    
    print(f"🧠 Hippocampus: Consolidação semanal")
    if trade:
        wr = round(trade['wins'] / max(trade['total'], 1) * 100, 1)
        print(f"  Trading: {trade['total']} trades, WR={wr}%, avg P&L win={trade['avg_pnl_win']} loss={trade['avg_pnl_loss']}")
        if trade['by_day']:
            best_day = max(trade['by_day'].items(), key=lambda x: x[1]['trades'])
            print(f"  Melhor dia: {best_day[0]} ({best_day[1]['trades']} trades)")
    if fail:
        print(f"  Falhas: {fail['total_failures']} total, {fail['open']} abertas")
        if fail['recurring']:
            print(f"  Recorrentes: {fail['recurring']}")
    if evo:
        print(f"  Evolução: {evo['completed']}/{evo['total_cycles']} ciclos completos")

if __name__ == '__main__':
    main()
