#!/usr/bin/env python3
"""
Codex Monitor — verificação do bot forex para o Codex CLI.
Gera um relatório JSON que o Codex analisa e decide se precisa agir.
"""
import json, subprocess, sys
from pathlib import Path
from datetime import datetime

H = Path.home() / '.hermes'

def run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        return r.stdout.strip()
    except:
        return None

# ═══ MT5 STATUS ═══
mt5_raw = run(f'python3 {H}/scripts/hermes_mt5_bridge.py status')
mt5 = json.loads(mt5_raw) if mt5_raw else {}

# ═══ TRADE LOG ═══
tlog = json.loads((H/'forex'/'trade_log.json').read_text()) if (H/'forex'/'trade_log.json').exists() else {'trades':[]}

# ═══ BOT LAST RUN ═══
cron_dir = H/'cron'/'output'/'ca8d82dc9fa5'
last_run = ''
if cron_dir.exists():
    files = sorted(cron_dir.glob('*'), key=lambda f: f.stat().st_mtime, reverse=True)
    if files:
        last_run = files[0].read_text()[-500:]

# ═══ COMPILE REPORT ═══
closed = [t for t in tlog['trades'] if t.get('status')=='closed']
wins = sum(1 for t in closed if t.get('result')=='WIN')
total_closed = len(closed)
wr = round(wins/total_closed*100,1) if total_closed else 0
total_pnl = sum(t.get('pnl',0) for t in closed)

report = {
    'timestamp': datetime.now().isoformat(),
    'mt5': {
        'balance': mt5.get('balance', 0),
        'equity': mt5.get('equity', 0),
        'positions': mt5.get('positions', 0),
        'positions_data': mt5.get('positions_data', []),
    },
    'performance': {
        'total_trades': total_closed,
        'wins': wins,
        'losses': total_closed - wins,
        'wr': wr,
        'total_pnl': total_pnl,
    },
    'risk': {
        'drawdown_pct': round((1 - mt5.get('equity',400)/400)*100, 2) if mt5.get('equity') else 0,
        'max_positions': 8,
        'current_positions': mt5.get('positions', 0),
    },
    'alerts': [],
}

# ═══ ALERTS ═══
if total_closed >= 3 and wr < 30:
    report['alerts'].append(f'⚠️ WR crítico: {wr}% em {total_closed} trades')

if report['risk']['drawdown_pct'] > 3:
    report['alerts'].append(f'⚠️ Drawdown: {report["risk"]["drawdown_pct"]}%')

if mt5.get('positions', 0) >= 7:
    report['alerts'].append(f'⚠️ {mt5["positions"]}/8 posições — próximo do limite')

# Count per pair
from collections import Counter
pair_count = Counter(p.get('symbol','') for p in mt5.get('positions_data',[]))
for pair, count in pair_count.items():
    if count >= 3:
        report['alerts'].append(f'⚠️ Concentração: {count}x {pair}')

# Output for Codex
print(json.dumps(report, indent=2, default=str))
