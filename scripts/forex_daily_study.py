#!/usr/bin/env python3
"""
ROTINA DIÁRIA FOREX — Estudo + Simulação + Aprendizado
Executa 1x/dia, ~25 minutos.
Não abre ordens reais — apenas estuda, simula e aprimora parâmetros.
"""
import json, urllib.request, os, sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Config
DATA_DIR = os.path.expanduser("~/.hermes/forex/study")
STUDY_LOG = os.path.expanduser("~/.hermes/forex/study_log.jsonl")
PARAMS_FILE = os.path.expanduser("~/.hermes/forex/best_params.json")

os.makedirs(DATA_DIR, exist_ok=True)

# ============================================================
# FASE 1: COLETA DE DADOS (~3 min)
# ============================================================

def download_pair(pair, days=30):
    """Baixa dados M5 do Yahoo Finance"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{pair}=X?range={days}d&interval=5m"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        result = data['chart']['result'][0]
        timestamps = result['timestamp']
        quotes = result['indicators']['quote'][0]
        candles = []
        for i, ts in enumerate(timestamps):
            o, h, l, c = quotes['open'][i], quotes['high'][i], quotes['low'][i], quotes['close'][i]
            if None not in (o, h, l, c):
                candles.append({'time': datetime.utcfromtimestamp(ts), 'o': o, 'h': h, 'l': l, 'c': c})
        return candles
    except Exception as e:
        print(f"  Download error {pair}: {e}")
        return []

def pip_m(pair):
    return 100 if 'JPY' in pair else 10000

# ============================================================
# FASE 2: ANÁLISE DE PARÂMETROS (~10 min)
# ============================================================

def detect_structure(candles):
    """Detecta HH/HL e LH/LL (market structure)"""
    swings_high = []
    swings_low = []
    
    for i in range(2, len(candles) - 2):
        # Swing High
        if candles[i]['h'] > candles[i-1]['h'] and candles[i]['h'] > candles[i-2]['h'] \
           and candles[i]['h'] > candles[i+1]['h'] and candles[i]['h'] > candles[i+2]['h']:
            swings_high.append({'idx': i, 'price': candles[i]['h'], 'time': candles[i]['time']})
        # Swing Low
        if candles[i]['l'] < candles[i-1]['l'] and candles[i]['l'] < candles[i-2]['l'] \
           and candles[i]['l'] < candles[i+1]['l'] and candles[i]['l'] < candles[i+2]['l']:
            swings_low.append({'idx': i, 'price': candles[i]['l'], 'time': candles[i]['time']})
    
    return swings_high, swings_low

def detect_bos_choch(candles, swings_high, swings_low):
    """Detecta Break of Structure e Change of Character"""
    events = []
    
    # Bullish BOS: price breaks above previous swing high
    for i, sh in enumerate(swings_high):
        if i >= 2:
            prev_high = swings_high[i-1]['price']
            prev2_high = swings_high[i-2]['price']
            # Higher High in uptrend
            if sh['price'] > prev_high and prev_high > prev2_high:
                events.append({'idx': sh['idx'], 'type': 'BOS_BULL', 'price': sh['price'], 'time': sh['time']})
    
    # Bearish BOS: price breaks below previous swing low
    for i, sl in enumerate(swings_low):
        if i >= 2:
            prev_low = swings_low[i-1]['price']
            prev2_low = swings_low[i-2]['price']
            if sl['price'] < prev_low and prev_low < prev2_low:
                events.append({'idx': sl['idx'], 'type': 'BOS_BEAR', 'price': sl['price'], 'time': sl['time']})
    
    return events

def detect_sweeps(candles, swings_high, swings_low):
    """Detecta liquidity sweeps"""
    sweeps = []
    
    for i in range(3, len(candles) - 1):
        c = candles[i]
        prev = candles[i-1]
        
        # Sweep of previous swing low (hunting sell-side liquidity)
        for sl in swings_low:
            if sl['idx'] < i - 2 and c['l'] < sl['price'] and c['c'] > sl['price']:
                sweeps.append({'idx': i, 'type': 'SWEEP_LOW', 'time': c['time'], 'level': sl['price']})
                break
        
        # Sweep of previous swing high (hunting buy-side liquidity)
        for sh in swings_high:
            if sh['idx'] < i - 2 and c['h'] > sh['price'] and c['c'] < sh['price']:
                sweeps.append({'idx': i, 'type': 'SWEEP_HIGH', 'time': c['time'], 'level': sh['price']})
                break
    
    return sweeps

def detect_fvg(candles):
    """Detecta Fair Value Gaps"""
    fvgs = []
    
    for i in range(1, len(candles) - 1):
        c0, c1, c2 = candles[i-1], candles[i], candles[i+1]
        
        # Bullish FVG: gap between c0 high and c2 low
        if c0['h'] < c2['l']:
            fvgs.append({'idx': i, 'type': 'FVG_BULL', 'top': c2['l'], 'bottom': c0['h'], 'time': c1['time']})
        
        # Bearish FVG: gap between c0 low and c2 high
        if c0['l'] > c2['h']:
            fvgs.append({'idx': i, 'type': 'FVG_BEAR', 'top': c0['l'], 'bottom': c2['h'], 'time': c1['time']})
    
    return fvgs

def backtest_params(candles, pair, rr_ratios=[2.0, 2.5, 3.0, 3.5], atr_factors=[0.08, 0.10, 0.12, 0.15]):
    """Testa combinações de parâmetros e retorna as melhores"""
    pm = pip_m(pair)
    swings_high, swings_low = detect_structure(candles)
    sweeps = detect_sweeps(candles, swings_high, swings_low)
    fvgs = detect_fvg(candles)
    
    results = []
    
    for rr in rr_ratios:
        for atr_f in atr_factors:
            trades = simulate_strategy(candles, sweeps, swings_high, swings_low, pm, rr, atr_f, pair)
            
            if len(trades) >= 5:
                wins = [t for t in trades if t['result'] == 'TP']
                losses = [t for t in trades if t['result'] == 'SL']
                wr = len(wins) / len(trades) * 100
                pnl = sum(t['pnl'] for t in trades)
                
                results.append({
                    'pair': pair, 'rr': rr, 'atr_factor': atr_f,
                    'trades': len(trades), 'wins': len(wins), 'losses': len(losses),
                    'win_rate': round(wr, 1), 'pnl': round(pnl, 1),
                    'score': round(wr * pnl / 100, 1) if pnl > 0 else 0
                })
    
    return results

def simulate_strategy(candles, sweeps, swings_high, swings_low, pm, rr, atr_f, pair):
    """Simula trades baseado em sweeps + estrutura"""
    trades = []
    
    # ATR calculation
    atr_values = []
    for i in range(1, len(candles)):
        tr = max(candles[i]['h'] - candles[i]['l'],
                 abs(candles[i]['h'] - candles[i-1]['c']),
                 abs(candles[i]['l'] - candles[i-1]['c']))
        atr_values.append(tr)
    
    for sweep in sweeps:
        if sweep['idx'] >= len(candles) - 3:
            continue
        
        c = candles[sweep['idx']]
        next_c = candles[sweep['idx'] + 1]
        
        # ATR do momento
        atr_idx = sweep['idx'] - 1
        if atr_idx < 13:
            continue
        curr_atr = sum(atr_values[atr_idx-13:atr_idx+1]) / 14
        
        if sweep['type'] == 'SWEEP_LOW':
            # Long setup: sweep low + bullish CHoCH
            if next_c['c'] > c['h']:  # CHoCH bullish
                entry = next_c['c']
                sl = c['l'] - curr_atr * atr_f
                tp = entry + (entry - sl) * rr
                
                # Forward test
                for j in range(sweep['idx'] + 2, min(sweep['idx'] + 50, len(candles))):
                    fc = candles[j]
                    if fc['l'] <= sl:
                        trades.append({'result': 'SL', 'pnl': round((sl - entry) * pm, 1)})
                        break
                    if fc['h'] >= tp:
                        trades.append({'result': 'TP', 'pnl': round((tp - entry) * pm, 1)})
                        break
                else:
                    last = candles[min(sweep['idx'] + 49, len(candles) - 1)]
                    trades.append({'result': 'TIME', 'pnl': round((last['c'] - entry) * pm, 1)})
        
        elif sweep['type'] == 'SWEEP_HIGH':
            # Short setup
            if next_c['c'] < c['l']:  # CHoCH bearish
                entry = next_c['c']
                sl = c['h'] + curr_atr * atr_f
                tp = entry - (sl - entry) * rr
                
                for j in range(sweep['idx'] + 2, min(sweep['idx'] + 50, len(candles))):
                    fc = candles[j]
                    if fc['h'] >= sl:
                        trades.append({'result': 'SL', 'pnl': round((entry - sl) * pm, 1)})
                        break
                    if fc['l'] <= tp:
                        trades.append({'result': 'TP', 'pnl': round((entry - tp) * pm, 1)})
                        break
                else:
                    last = candles[min(sweep['idx'] + 49, len(candles) - 1)]
                    trades.append({'result': 'TIME', 'pnl': round((entry - last['c']) * pm, 1)})
    
    return trades

# ============================================================
# FASE 3: CONSOLIDAÇÃO (~5 min)
# ============================================================

def find_best_params(all_results):
    """Encontra os melhores parâmetros globais"""
    if not all_results:
        return None
    
    # Filtrar resultados positivos
    positive = [r for r in all_results if r['pnl'] > 0]
    if not positive:
        positive = all_results
    
    # Ordenar por score (win_rate * pnl)
    positive.sort(key=lambda x: x['score'], reverse=True)
    
    # Agrupar por RR
    by_rr = defaultdict(list)
    for r in positive:
        by_rr[r['rr']].append(r)
    
    best = {}
    for rr, results in by_rr.items():
        results.sort(key=lambda x: x['score'], reverse=True)
        best[f"RR_{rr}"] = results[0]
    
    return best

def main():
    print("=" * 60)
    print("ROTINA DIÁRIA FOREX — ESTUDO DE PARÂMETROS")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'EURJPY', 'AUDUSD']
    all_results = []
    
    # FASE 1: Download
    print("\n📥 FASE 1: Coletando dados...")
    for pair in pairs:
        candles = download_pair(pair, 30)
        if candles:
            print(f"  {pair}: {len(candles)} candles")
            
            # FASE 2: Análise
            results = backtest_params(candles, pair)
            all_results.extend(results)
            
            # Melhor resultado do par
            if results:
                best = max(results, key=lambda x: x['score'])
                print(f"    Melhor: RR={best['rr']} ATRf={best['atr_factor']} WR={best['win_rate']}% PnL={best['pnl']}pips Score={best['score']}")
    
    # FASE 3: Consolidação
    print("\n📊 FASE 3: Melhores parâmetros globais...")
    best_params = find_best_params(all_results)
    
    if best_params:
        # Salvar
        Path(PARAMS_FILE).write_text(json.dumps(best_params, indent=2, default=str))
        
        print("\n🏆 PARÂMETROS ÓTIMOS:")
        for key, params in sorted(best_params.items()):
            print(f"  {key}: WR={params['win_rate']}% PnL={params['pnl']}pips pair={params['pair']}")
    
    # Log
    log_entry = {
        'date': datetime.now().isoformat(),
        'pairs_tested': len(pairs),
        'total_simulations': len(all_results),
        'best_params': best_params,
    }
    
    with open(STUDY_LOG, 'a') as f:
        f.write(json.dumps(log_entry, default=str) + '\n')
    
    print(f"\n✅ Estudo concluído. Log: {STUDY_LOG}")
    print(f"✅ Parâmetros: {PARAMS_FILE}")

if __name__ == "__main__":
    main()
