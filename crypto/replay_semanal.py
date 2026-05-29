#!/usr/bin/env python3
"""
REPLAY COM PRÉ-ANÁLISE SEMANAL — Backtest usando pares e direções da weekly_analysis
Compara: com viés semanal vs sem viés (neutro)
"""
import sys, json, subprocess, os
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

sys.path.insert(0, str(Path.home() / '.hermes' / 'scripts'))
from multi_agent import PerfilAgent, SessaoAgent, EstruturaAgent, PadraoAgent, ConfluenciaAgent

VENV_PYTHON = os.path.expanduser('~/.hermes/hermes-agent/venv/bin/python')

def get_tv_data(symbol, exchange='FX_IDC', n_bars=4000):
    code = f"""
from tvDatafeed import TvDatafeed, Interval
tv = TvDatafeed()
data = tv.get_hist(symbol='{symbol}', exchange='{exchange}', interval=Interval.in_15_minute, n_bars={n_bars})
import json
if len(data) == 0: print('EMPTY')
else:
    r = {{'high': data['high'].values.tolist(), 'low': data['low'].values.tolist(),
         'close': data['close'].values.tolist(), 'open': data['open'].values.tolist()}}
    print(json.dumps(r))
"""
    r = subprocess.run([VENV_PYTHON, '-c', code], capture_output=True, text=True, timeout=30)
    if r.returncode != 0 or r.stdout.strip() == 'EMPTY': return None
    return json.loads(r.stdout.strip())

def load_weekly():
    path = Path.home() / '.hermes' / 'forex' / 'weekly_analysis.json'
    if not path.exists(): return None
    with open(path) as f: return json.load(f)

# ═══ CONFIG ═══
RR = 3.0
PIP_SIZES = {'EURUSD': 0.0001, 'GBPUSD': 0.0001, 'USDJPY': 0.01, 'AUDUSD': 0.0001,
             'NZDUSD': 0.0001, 'USDCAD': 0.0001, 'USDCHF': 0.0001,
             'AUDJPY': 0.01, 'EURJPY': 0.01, 'GBPJPY': 0.01, 'EURGBP': 0.0001}

def simulate_trade(h, l, c, direction, entry, sl_pips, idx):
    if direction == 'BUY':
        sl = entry - sl_pips; tp = entry + sl_pips * RR
    else:
        sl = entry + sl_pips; tp = entry - sl_pips * RR
    
    for j in range(idx, min(idx + 500, len(c))):
        if direction == 'BUY':
            if l[j] <= sl: return {'result': 'LOSS', 'rr': -1}
            if h[j] >= tp: return {'result': 'WIN', 'rr': RR}
        else:
            if h[j] >= sl: return {'result': 'LOSS', 'rr': -1}
            if l[j] <= tp: return {'result': 'WIN', 'rr': RR}
    return None

def run_backtest(pair, weekly_direction, pip_size):
    """Backtest com viés semanal."""
    data = get_tv_data(pair, 'FX_IDC', 4000)
    if data is None: return []
    
    h = np.array(data['high']); l = np.array(data['low'])
    c = np.array(data['close']); o = np.array(data['open'])
    
    # Agentes
    perfil = PerfilAgent(); sessao = SessaoAgent()
    estrutura = EstruturaAgent(); padrao = PadraoAgent()
    confluencia = ConfluenciaAgent()
    
    trades_bias = []     # com viés semanal
    trades_neutral = []  # sem viés
    
    sl_pips = 15 * pip_size
    hour_now = datetime.now(timezone.utc).hour
    
    for idx in range(100, len(c) - 200, 4):
        hw, lw, cw = h[:idx], l[:idx], c[:idx]
        if len(cw) < 50: continue
        
        # Daily bias
        daily_bias = 'BUY' if len(cw) >= 96 and cw[-1] > cw[-96] else 'SELL'
        
        # Análise dos agentes
        e_dir, _, _ = estrutura.analyze(hw, lw, cw, daily_bias)
        pat_dir, _, pat_sig = padrao.analyze(hw, lw, cw, 
            e_dir if e_dir != 'NEUTRAL' else daily_bias, pip_size)
        
        if pat_dir == 'NEUTRAL' or not pat_sig: continue
        
        entry = pat_sig.get('entry', cw[-1])
        
        # ═══ COM VIÉS SEMANAL ═══
        if weekly_direction:
            # Só opera na direção da análise semanal
            if pat_dir == weekly_direction:
                r = simulate_trade(h, l, c, pat_dir, entry, sl_pips, idx)
                if r: trades_bias.append({'direction': pat_dir, 'result': r['result'], 'rr': r['rr']})
        else:
            r = simulate_trade(h, l, c, pat_dir, entry, sl_pips, idx)
            if r: trades_bias.append({'direction': pat_dir, 'result': r['result'], 'rr': r['rr']})
        
        # ═══ SEM VIÉS (controle) ═══
        r = simulate_trade(h, l, c, pat_dir, entry, sl_pips, idx)
        if r: trades_neutral.append({'direction': pat_dir, 'result': r['result'], 'rr': r['rr']})
    
    return trades_bias, trades_neutral


# ═══ MAIN ═══
print(f"═══ REPLAY COM PRÉ-ANÁLISE SEMANAL ═══")
print()

weekly = load_weekly()
if not weekly:
    print("Rodando análise semanal primeiro...")
    import weekly_analysis
    weekly = weekly_analysis.run_weekly_analysis()

if not weekly or not weekly.get('selected_pairs'):
    print("Sem análise semanal disponível")
    sys.exit(1)

selected = weekly['selected_pairs'][:4]  # top 4 pares

print(f"Data: {weekly['date']}")
print(f"Força: {', '.join(f'{k} {v:+.1f}%' for k,v in sorted(weekly['strength'].items(), key=lambda x:x[1], reverse=True))}")
print()
print(f"{'Par':<10s} {'Viés':<8s} {'Trades':>8s} {'WR':>8s} {'R':>8s} | {'Trades(N)':>10s} {'WR(N)':>8s} {'R(N)':>8s}")
print(f"{'─'*78}")

all_bias = []
all_neutral = []

for s in selected:
    pair = s['pair']
    direction = s['direction']
    pip = PIP_SIZES.get(pair, 0.0001)
    
    print(f"{pair:<10s} {direction:<8s}", end=' ', flush=True)
    
    trades_bias, trades_neutral = run_backtest(pair, direction, pip)
    
    if trades_bias:
        w = sum(1 for t in trades_bias if t['result'] == 'WIN')
        wr = w / len(trades_bias) * 100
        rr = sum(t['rr'] for t in trades_bias)
        print(f"{len(trades_bias):8d} {wr:7.1f}% {rr:+8.1f}R", end=' |')
        all_bias.extend(trades_bias)
    else:
        print(f"{'─':>8s} {'─':>7s} {'─':>8s}", end=' |')
    
    if trades_neutral:
        w = sum(1 for t in trades_neutral if t['result'] == 'WIN')
        wr = w / len(trades_neutral) * 100
        rr = sum(t['rr'] for t in trades_neutral)
        print(f" {len(trades_neutral):10d} {wr:7.1f}% {rr:+8.1f}R")
        all_neutral.extend(trades_neutral)
    else:
        print(f" {'─':>10s} {'─':>7s} {'─':>8s}")

print(f"{'─'*78}")

# Consolidado
if all_bias:
    w = sum(1 for t in all_bias if t['result'] == 'WIN')
    wr = w / len(all_bias) * 100
    rr = sum(t['rr'] for t in all_bias)
    print(f"{'COM VIÉS':<18s} {len(all_bias):8d} {wr:7.1f}% {rr:+8.1f}R")

if all_neutral:
    w = sum(1 for t in all_neutral if t['result'] == 'WIN')
    wr = w / len(all_neutral) * 100
    rr = sum(t['rr'] for t in all_neutral)
    print(f"{'SEM VIÉS':<18s} {len(all_neutral):8d} {wr:7.1f}% {rr:+8.1f}R")

print()
diff_trades = len(all_bias) - len(all_neutral) if all_bias and all_neutral else 0
if all_bias and all_neutral:
    wr_bias = sum(1 for t in all_bias if t['result']=='WIN')/len(all_bias)*100
    wr_neutral = sum(1 for t in all_neutral if t['result']=='WIN')/len(all_neutral)*100
    print(f"Impacto do viés: {diff_trades:+d} trades, WR {wr_bias-wr_neutral:+.1f}pp")
