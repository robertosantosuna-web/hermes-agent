#!/usr/bin/env python3
"""
CRYPTO BACKTEST v9 — TradingView Feed, Multi-TF nativo H4+H1+M15
Período: 30 dias com M1 nativo (via tvDatafeed)
"""
import sys, json
from pathlib import Path
from datetime import datetime, timedelta, timezone
import numpy as np
from tradingview_feed import TradingViewFeed

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
from crypto_multi_agent import CryptoConfluencia
from tradingview_feed import TradingViewFeed

RR = 3.0
DATA_DAYS = 30
TIMEFRAME = '15m'  # M15 nativo (30d = ~2880 velas, cabe nos 5000 do TV gratuito)
MIN_TRADES = 20
MIN_WR = 50
MIN_PF = 2.0
MIN_CONFIDENCE = 55

TEST_PAIRS = {
    'BTCUSD': ('BTCUSDT', 'BINANCE', 1.0),
    'ETHUSD': ('ETHUSDT', 'BINANCE', 0.1),
    'DOGEUSD': ('DOGEUSDT', 'BINANCE', 0.001),
    'BNBUSD': ('BNBUSDT', 'BINANCE', 0.1),
}

def get_daily_bias_backtest(highs, lows, closes):
    if len(highs) < 3: return 'NEUTRAL'
    ph, pl = highs[-3], lows[-3]
    ch, cl, cc = highs[-2], lows[-2], closes[-2]
    if ch > ph and cc > ph: return 'BUY'
    if cl < pl and cc < pl: return 'SELL'
    if ch > ph and cc < ph: return 'SELL'
    if cl < pl and cc > pl: return 'BUY'
    if cc > closes[-3]: return 'BUY'
    if cc < closes[-3]: return 'SELL'
    return 'NEUTRAL'

def simulate_trade(highs, lows, closes, direction, entry, sl, tp):
    for i in range(len(closes)):
        if direction == 'BUY':
            if lows[i] <= sl: return {'result': 'LOSS', 'rr': -1, 'exit': max(sl, lows[i])}
            if highs[i] >= tp: return {'result': 'WIN', 'rr': RR, 'exit': tp}
        else:
            if highs[i] >= sl: return {'result': 'LOSS', 'rr': -1, 'exit': min(sl, highs[i])}
            if lows[i] <= tp: return {'result': 'WIN', 'rr': RR, 'exit': tp}
    last = closes[-1]
    if direction == 'BUY': rr = (last - entry) / (entry - sl)
    else: rr = (entry - last) / (sl - entry)
    return {'result': 'OPEN', 'rr': rr, 'exit': last}


def run_backtest():
    feed = TradingViewFeed()
    agent = CryptoConfluencia()
    
    print(f"═══ CRYPTO BACKTEST v9 (TradingView) — {DATA_DAYS} dias {TIMEFRAME} ═══")
    print(f"RR={RR}:1 Conf≥{MIN_CONFIDENCE}% Pares={len(TEST_PAIRS)}")
    print()
    
    trades = []
    
    for pair, (sym, exchange, pip) in TEST_PAIRS.items():
        print(f"Testando {pair}...")
        
        try:
            # Dados via TradingView
            n_bars = min(DATA_DAYS * 24 * 4, 5000)  # M15: 4 velas/hora
            h, l, c, o, v = feed.get_candles(pair, TIMEFRAME, n_bars)
            
            if c is None or len(c) < 200:
                print(f"  {pair}: dados insuficientes ({len(c) if c is not None else 0})")
                continue
            
            print(f"  {pair}: {len(c)} velas {TIMEFRAME} (~{len(c)//(24*4)} dias)")
            
            # Daily bias via resample das velas M15 (96 M15 = 1 dia)
            n_daily = len(c) // 96
            db_h, db_l, db_c = [], [], []
            for d in range(n_daily):
                s, e = d * 96, min((d+1) * 96, len(c))
                if e - s < 10: continue
                db_h.append(max(h[s:e]))
                db_l.append(min(l[s:e]))
                db_c.append(c[e-1])
            
            if len(db_c) < 3:
                print(f"  {pair}: poucos dias de dados"); continue
            
            daily_levels = {
                'resistance': max(db_h[-10:]) if len(db_h) >= 10 else max(db_h),
                'support': min(db_l[-10:]) if len(db_l) >= 10 else min(db_l)
            }
            
            pair_trades = 0
            last_entry_idx = -100
            
            # Escanear a cada 2 velas M15 (30 min)
            step = 2
            min_start = 60  # precisa de velas para H1 via agregação
            
            for i in range(min_start, len(c) - 5, step):
                h_win, l_win = h[:i], l[:i]
                c_win, o_win = c[:i], o[:i]
                v_win = v[:i] if v is not None else None
                
                # Daily bias
                day_idx = min(len(db_h)-2, max(0, i // 1440))
                if day_idx < 2: continue
                bias = get_daily_bias_backtest(db_h[:day_idx+1], db_l[:day_idx+1], db_c[:day_idx+1])
                if bias == 'NEUTRAL': continue
                
                # BTC change
                btc_chg = 0
                if pair != 'BTCUSD' and len(c_win) >= 60:
                    btc_chg = (c_win[-1] / c_win[-60] - 1) * 100 if c_win[-60] > 0 else 0
                
                # Análise multi-agente com Multi-TF do TradingView
                decision, conf, signal, v_info = agent.analyze(
                    pair, h_win, l_win, c_win, o_win, bias, pip,
                    btc_chg, MIN_CONFIDENCE, v_win, daily_levels
                )
                
                if decision == 'NEUTRAL' or not signal:
                    continue
                
                sig_idx = signal.get('idx', i)
                if abs(sig_idx - last_entry_idx) < 30:
                    continue
                last_entry_idx = sig_idx
                
                entry = signal['entry']
                atr_pct = (v_info or {}).get('atr_pct', 0.5)
                sl_rec = (v_info or {}).get('sl_recommend', None)
                sl_pct = sl_rec or max(atr_pct * 1.5, 0.15)
                
                if decision == 'BUY':
                    sl = entry * (1 - sl_pct/100)
                    tp = entry * (1 + sl_pct*RR/100)
                else:
                    sl = entry * (1 + sl_pct/100)
                    tp = entry * (1 - sl_pct*RR/100)
                
                result = simulate_trade(h[i:], l[i:], c[i:], decision, entry, sl, tp)
                
                if result:
                    trades.append({
                        'pair': pair, 'direction': decision, 'entry': entry,
                        'sl': sl, 'tp': tp, 'sl_pct': sl_pct,
                        'result': result['result'], 'rr': result['rr'],
                        'exit': result['exit'], 'conf': conf,
                        'pattern': signal.get('type', '?'),
                        'quality': signal.get('quality', 0),
                        'market_structure': signal.get('market_structure', '?'),
                        'regime': (v_info or {}).get('regime', '?'),
                        'impulse_ratio': signal.get('impulse_ratio', 0),
                    })
                    pair_trades += 1
            
            print(f"  {pair}: {pair_trades} trades")
        
        except Exception as e:
            print(f"  {pair}: ERRO — {e}")
            import traceback
            traceback.print_exc()
    
    print()
    return trades


def analyze_results(trades):
    if not trades:
        return {'passed': False, 'reason': 'Nenhum trade'}
    
    wins = [t for t in trades if t['result'] == 'WIN']
    losses = [t for t in trades if t['result'] == 'LOSS']
    opens = [t for t in trades if t['result'] == 'OPEN']
    
    total = len(trades)
    wr = len(wins) / max(total, 1) * 100
    total_r = sum(t['rr'] for t in trades)
    gross_win = sum(t['rr'] for t in wins) if wins else 0
    gross_loss = abs(sum(t['rr'] for t in losses)) if losses else 1
    pf = gross_win / gross_loss if gross_loss > 0 else 999
    
    print(f"═══ RESULTADOS — {DATA_DAYS} dias {TIMEFRAME} (TradingView) ═══")
    print(f"Total trades:  {total}")
    print(f"Wins:          {len(wins)} ({wr:.1f}%)")
    print(f"Losses:        {len(losses)}")
    print(f"Open:          {len(opens)}")
    print(f"Total R:       {total_r:+.1f}R")
    print(f"Profit Factor: {pf:.2f}")
    
    # Por par
    print(f"\nPor par:")
    for pair in sorted(set(t['pair'] for t in trades)):
        pt = [t for t in trades if t['pair'] == pair]
        pw = [t for t in pt if t['result'] == 'WIN']
        pwr = len(pw)/max(len(pt),1)*100
        pr = sum(t['rr'] for t in pt)
        print(f"  {pair:8s}: {len(pt):4d} trades, WR={pwr:.0f}%, {pr:+.1f}R")
    
    # Por estrutura
    structures = {}
    for t in trades:
        s = t.get('market_structure', '?')
        if s not in structures: structures[s] = {'t':0,'w':0,'r':0}
        structures[s]['t'] += 1
        structures[s]['r'] += t['rr']
        if t['result'] == 'WIN': structures[s]['w'] += 1
    
    print(f"\nPor Market Structure:")
    for s, st in sorted(structures.items()):
        if st['t'] < 3: continue
        swr = st['w']/st['t']*100
        print(f"  {s:10s}: {st['t']:4d}t, WR={swr:.0f}%, {st['r']:+.1f}R")
    
    # Validação
    print(f"\n═══ VALIDAÇÃO ═══")
    checks = [
        (f"≥{MIN_TRADES} trades", total >= MIN_TRADES, f"{total}"),
        (f"WR ≥{MIN_WR}%", wr >= MIN_WR, f"{wr:.1f}%"),
        (f"PF ≥{MIN_PF}", pf >= MIN_PF, f"{pf:.2f}"),
    ]
    all_pass = True
    for check, result, value in checks:
        status = "✅" if result else "❌"
        if not result: all_pass = False
        print(f"  {status} {check}: {value}")
    
    return {'passed': all_pass, 'total': total, 'wr': wr, 'pf': pf,
            'total_r': total_r, 'wins': len(wins), 'losses': len(losses)}


if __name__ == '__main__':
    print(f"Iniciando backtest v9 em {datetime.now().strftime('%d/%m %H:%M')} UTC")
    trades = run_backtest()
    result = analyze_results(trades)
    
    if result['passed']:
        print(f"\n✅ SISTEMA APROVADO — TradingView + Multi-TF completo")
    else:
        print(f"\n❌ REPROVADO")
    
    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'parameters': {'rr': RR, 'days': DATA_DAYS, 'feed': 'tradingview', 'timeframe': 'M1'},
        'results': result,
        'trades': trades
    }
    outfile = Path.home() / '.hermes' / 'crypto' / 'backtest_v9_30d.json'
    with open(outfile, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nSalvo: {outfile}")
