#!/usr/bin/env python3
"""
CHoCH+FVG @ M15 — Simulacao pos-killzone
Estrategia validada em backtest 30 dias, 168 combinacoes.
Substitui Sweep+M5 (4-17% WR) por CHoCH+M15 (55-78% WR).

Pares: GBP/USD, AUD/USD, EUR/USD, NZD/USD
RR: 3:1 | FVG min: 1 pip | Sessoes: London AM, Lond+NY Overlap, NY PM
Dias: Ter-Qui (Seg/Sex ignorados)
"""
import json
import urllib.request
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# ═══════════════════════════════════════
# CONFIG — Validada em backtest 30d
# ═══════════════════════════════════════
PAIRS = {
    'GBP/USD': 'GBPUSD=X',
    'AUD/USD': 'AUDUSD=X',
    'EUR/USD': 'EURUSD=X',
    'NZD/USD': 'NZDUSD=X',
}

RR = 3.0
FVG_MIN_PIPS = 1.0
ATR_MIN_PIPS = 1.0
LOOKBACK_HOURS = 8  # horas de dados para analise

# Horarios ouro (melhores WR no backtest)
GOLDEN_HOURS = {7, 10, 14, 16}

def pip_val(pair):
    return 0.01 if 'JPY' in pair else 0.0001

def atr(candles, period=14):
    if len(candles) < 2: return 0
    trs = []
    for i in range(1, len(candles)):
        h, l, pc = candles[i]['h'], candles[i]['l'], candles[i-1]['c']
        trs.append(max(h-l, abs(h-pc), abs(l-pc)))
    n = min(period, len(trs))
    return sum(trs[-n:])/n if n > 0 else 0

def detect_swings(candles):
    highs, lows = [], []
    for i in range(3, len(candles)-3):
        h, l = candles[i]['h'], candles[i]['l']
        left_h = max(c['h'] for c in candles[i-3:i])
        right_h = max(c['h'] for c in candles[i+1:i+4])
        left_l = min(c['l'] for c in candles[i-3:i])
        right_l = min(c['l'] for c in candles[i+1:i+4])
        if h > left_h and h > right_h:
            highs.append({'idx': i, 'price': h, 'time': candles[i]['time']})
        if l < left_l and l < right_l:
            lows.append({'idx': i, 'price': l, 'time': candles[i]['time']})
    return highs, lows

def find_fvgs(candles):
    fvgs = []
    for i in range(1, len(candles)-1):
        prev, curr = candles[i-1], candles[i]
        if curr['l'] > prev['h']:
            fvgs.append({'type': 'BULLISH', 'top': curr['l'], 'bottom': prev['h'], 'time': curr['time']})
        elif curr['h'] < prev['l']:
            fvgs.append({'type': 'BEARISH', 'top': prev['l'], 'bottom': curr['h'], 'time': curr['time']})
    return fvgs

def fetch_m15(symbol):
    """Busca candles M15 via Yahoo Finance (ultimas 8h)."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=15m"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())['chart']['result'][0]
        candles = []
        for i, ts in enumerate(data['timestamp']):
            q = data['indicators']['quote'][0]
            o, h, l, c = q['open'][i], q['high'][i], q['low'][i], q['close'][i]
            if None not in (o, h, l, c):
                dt = datetime.utcfromtimestamp(ts) - timedelta(hours=3)  # BRT
                candles.append({'time': dt, 'o': o, 'h': h, 'l': l, 'c': c})
        # Filtrar ultimas N horas
        if candles:
            cutoff = candles[-1]['time'] - timedelta(hours=LOOKBACK_HOURS)
            candles = [c for c in candles if c['time'] >= cutoff]
        return candles
    except Exception as e:
        print(f"  ⚠️ Erro {symbol}: {e}", file=sys.stderr)
        return []

def analyze_pair(pair_name, symbol):
    """Analisa um par com CHoCH+FVG @ M15."""
    pv = pip_val(pair_name)
    candles = fetch_m15(symbol)
    if not candles:
        return None
    
    atr_val = atr(candles, 14)
    atr_pips = atr_val / pv
    
    if atr_pips < ATR_MIN_PIPS:
        return None
    
    swings_h, swings_l = detect_swings(candles)
    if len(swings_h) < 2 or len(swings_l) < 2:
        return None
    
    # CHoCH detection (break of structure)
    last_c = candles[-1]
    ch = last_c['time'].hour
    
    direction = None
    if last_c['c'] > swings_h[-2]['price']:
        direction = 'LONG'
    elif last_c['c'] < swings_l[-2]['price']:
        direction = 'SHORT'
    
    if not direction:
        return None
    
    # FVG
    fvgs = find_fvgs(candles[-8:])
    valid_fvg = None
    if direction == 'SHORT':
        for f in reversed(fvgs):
            if f['type'] == 'BEARISH':
                valid_fvg = f; break
    else:
        for f in reversed(fvgs):
            if f['type'] == 'BULLISH':
                valid_fvg = f; break
    
    if not valid_fvg:
        return None
    
    # Entry + SL
    if direction == 'SHORT':
        entry = valid_fvg['bottom']
        fvg_sl = valid_fvg['top']
    else:
        entry = valid_fvg['top']
        fvg_sl = valid_fvg['bottom']
    
    fvg_width_pips = abs(entry - fvg_sl) / pv
    if fvg_width_pips < FVG_MIN_PIPS:
        return None
    
    sl_pips = fvg_width_pips
    tp_pips = sl_pips * RR
    
    if direction == 'SHORT':
        sl_price = entry + sl_pips * pv
        tp_price = entry - tp_pips * pv
    else:
        sl_price = entry - sl_pips * pv
        tp_price = entry + tp_pips * pv
    
    # Score: penaliza fora de golden hours, premia dentro
    golden_bonus = 1.3 if ch in GOLDEN_HOURS else 0.8
    score = (fvg_width_pips / max(atr_pips, 0.01)) * golden_bonus
    
    return {
        'pair': pair_name,
        'direction': direction,
        'entry': round(entry, 5),
        'sl': round(sl_price, 5),
        'tp': round(tp_price, 5),
        'sl_pips': round(sl_pips, 1),
        'tp_pips': round(tp_pips, 1),
        'atr_pips': round(atr_pips, 1),
        'fvg_pips': round(fvg_width_pips, 1),
        'score': round(score, 2),
        'golden': ch in GOLDEN_HOURS,
        'hour': ch,
    }

# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════
def main():
    now = datetime.now()
    brt = now - timedelta(hours=0)  # system already BRT
    
    # Skip Seg/Sex
    dow = now.weekday()
    if dow in (0, 4):
        print("[SILENT]")
        return
    
    # Skip outside trading hours (04:00-17:00 BRT)
    hour = now.hour
    if hour < 4 or hour > 17:
        print("[SILENT]")
        return
    
    print(f"┌────────────────────────────────────────┐")
    print(f"│ 📊 CHoCH+FVG @ M15 | RR 3:1")
    print(f"│ {now.strftime('%d/%m %H:%M')} BRT | {'⭐ GOLDEN HOUR' if hour in GOLDEN_HOURS else 'Hora normal'}")
    print(f"├────────────────────────────────────────┤")
    
    setups = []
    for pair_name, symbol in PAIRS.items():
        result = analyze_pair(pair_name, symbol)
        if result:
            setups.append(result)
            star = '⭐' if result['golden'] else '  '
            print(f"│ {star} {result['direction']:5s} {pair_name:<10} "
                  f"entry={result['entry']} sl={result['sl_pips']}p tp={result['tp_pips']}p "
                  f"score={result['score']}")
        else:
            print(f"│    —     {pair_name:<10} sem setup")
    
    print(f"├────────────────────────────────────────┤")
    
    if setups:
        # Dedup: keep only best score per direction
        long_setups = [s for s in setups if s['direction'] == 'LONG']
        short_setups = [s for s in setups if s['direction'] == 'SHORT']
        
        best_long = max(long_setups, key=lambda s: s['score']) if long_setups else None
        best_short = max(short_setups, key=lambda s: s['score']) if short_setups else None
        
        active = []
        if best_long:
            active.append(best_long)
        if best_short:
            active.append(best_short)
        
        total_pips = sum(s['tp_pips'] for s in active)
        avg_score = sum(s['score'] for s in active) / len(active) if active else 0
        
        print(f"│ ✅ {len(active)} setup(s) ativo(s) (dedup: {len(setups)}→{len(active)})")
        print(f"│ RR: 3:1 | Score medio: {avg_score:.1f}")
        print(f"│ ⚠️ SIMULACAO — Nenhuma ordem real aberta")
        print(f"└────────────────────────────────────────┘")
    else:
        print(f"│ ⚠️ Nenhum setup CHoCH+FVG detectado")
        print(f"└────────────────────────────────────────┘")

if __name__ == '__main__':
    main()
