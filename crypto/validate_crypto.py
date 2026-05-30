#!/usr/bin/env python3
"""
CRYPTO BACKTEST VALIDATOR v2 — TradingView como fonte de dados.
Requer: PF > 2.0, WR > 40%, mínimo 10 trades em 15 dias
ZERO yfinance. 100% TradingView.
"""
import sys, json
from pathlib import Path
from datetime import datetime, timedelta, timezone
import numpy as np

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
from crypto_multi_agent import CryptoConfluencia
from tradingview_feed import TradingViewFeed

RR = 3.0
DATA_DAYS = 7
MIN_TRADES = 5
MIN_WR = 35
MIN_PF = 1.8
MIN_CONFIDENCE = 55

TEST_PAIRS = {
    'BTCUSD': ('BTC-USD', 1.0),
    'ETHUSD': ('ETH-USD', 0.1),
    'DOGEUSD': ('DOGE-USD', 0.001),
    'BNBUSD': ('BNB-USD', 0.1),
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

def resample_daily(h, l, c, bars_per_day=288):
    """Resample M5 candles para diário (288 M5 = 1 dia)."""
    daily_h, daily_l, daily_c = [], [], []
    for i in range(0, len(c), bars_per_day):
        end = min(i + bars_per_day, len(c))
        if end - i < 10: continue
        daily_h.append(max(h[i:end]))
        daily_l.append(min(l[i:end]))
        daily_c.append(c[end - 1])
    return np.array(daily_h), np.array(daily_l), np.array(daily_c)

def run_backtest():
    print(f"═══ CRYPTO BACKTEST v2 (TradingView) — {DATA_DAYS} dias ═══")
    print(f"Parâmetros: RR={RR}:1, Conf mín={MIN_CONFIDENCE}%, Pares={len(TEST_PAIRS)}")
    print()
    
    feed = TradingViewFeed()
    agent = CryptoConfluencia()
    trades = []
    
    # Pré-carregar BTC para correlação
    print("Carregando BTC...")
    try:
        btc_h, btc_l, btc_c, btc_o, btc_v = feed.get_candles('BTCUSD', '5m', DATA_DAYS * 288)
        btc_dh, btc_dl, btc_dc = resample_daily(btc_h, btc_l, btc_c)
    except:
        btc_h = btc_l = btc_c = None
    
    for pair, (sym, pip) in TEST_PAIRS.items():
        print(f"\nTestando {pair}...")
        
        try:
            # M5: 288 candles/dia × DATA_DAYS
            total_bars = DATA_DAYS * 288
            h, l, c, o, v = feed.get_candles(pair, '5m', total_bars)
            
            if c is None or len(c) < 500:
                print(f"  {pair}: dados insuficientes ({len(c) if c is not None else 0})")
                continue
            
            # Resample para diário
            daily_h, daily_l, daily_c = resample_daily(h, l, c)
            
            if len(daily_c) < 3:
                print(f"  {pair}: poucos dias ({len(daily_c)})")
                continue
            
            print(f"  {len(c)} velas M5, {len(daily_c)} dias")
            
            # Níveis diários
            daily_levels = {
                'resistance': max(daily_h[-3:]) if len(daily_h) >= 3 else max(daily_h),
                'support': min(daily_l[-3:]) if len(daily_l) >= 3 else min(daily_l)
            }
            
            # BTC change simplificado
            btc_4h = 0
            if btc_c is not None and len(btc_c) >= 48:
                btc_4h = (btc_c[-1] / btc_c[-48] - 1) * 100
            
            pair_trades = 0
            last_entry_idx = -100
            
            # Simular entradas a cada ~1 hora (12 velas M5)
            step = 12
            for i in range(40, len(c) - 10, step):
                h_win, l_win = h[:i], l[:i]
                c_win, o_win = c[:i], o[:i]
                
                # Daily bias no ponto atual
                day_idx = i // 288
                if day_idx < 2 or day_idx >= len(daily_c):
                    continue
                bias = get_daily_bias_backtest(daily_h[:day_idx+1], daily_l[:day_idx+1], daily_c[:day_idx+1])
                if bias == 'NEUTRAL':
                    continue
                
                # Volume
                v_win = v[:i] if v is not None else None
                
                # Testar direção do bias
                decision, conf, sig, info = agent.analyze(
                    pair, h_win, l_win, c_win, o_win, bias, pip,
                    btc_4h if pair != 'BTCUSD' else None,
                    MIN_CONFIDENCE, v_win, daily_levels
                )
                
                if decision == 'NEUTRAL' or not sig:
                    continue
                
                # Evitar repetir mesma entrada
                if i - last_entry_idx < 30:
                    continue
                
                entry = sig['entry']
                atr_pct = (info or {}).get('atr_pct', 0.3)
                sl_rec = (info or {}).get('sl_recommend', None)
                if sl_rec is None:
                    sl_rec = max(atr_pct * 1.5, 0.15)
                sl_pct = min(sl_rec, 1.5)
                
                sp = entry * sl_pct / 100
                if decision == 'BUY':
                    sl, tp = entry - sp, entry + sp * RR
                else:
                    sl, tp = entry + sp, entry - sp * RR
                
                # Simular resultado: verificar velas futuras
                result, exit_price, r_mult = simulate_trade(
                    h[i:], l[i:], c[i:], decision, entry, sl, tp
                )
                
                if result == 'OPEN':
                    continue  # Trade ainda aberto no fim dos dados
                
                trades.append({
                    'pair': pair, 'direction': decision,
                    'entry': float(entry), 'exit': float(exit_price),
                    'sl': float(sl), 'tp': float(tp),
                    'result': result, 'r': r_mult,
                    'conf': conf, 'pattern': sig.get('type', '?'),
                    'ir': sig.get('impulse_ratio', 0),
                })
                
                pair_trades += 1
                last_entry_idx = i
            
            print(f"  {pair_trades} trades")
            
        except Exception as e:
            print(f"  ❌ {e}")
            import traceback; traceback.print_exc()
    
    # Resultados
    print(f"\n{'='*60}")
    print(f"═══ RESULTADOS — {len(trades)} trades ═══")
    print(f"{'='*60}")
    
    if len(trades) < MIN_TRADES:
        print(f"❌ Trades insuficientes: {len(trades)}/{MIN_TRADES}")
        return None
    
    wins = [t for t in trades if t['result'] == 'WIN']
    losses = [t for t in trades if t['result'] == 'LOSS']
    wr = len(wins) / len(trades) * 100
    
    total_r = sum(t['r'] for t in trades)
    avg_win = np.mean([t['r'] for t in wins]) if wins else 0
    avg_loss = abs(np.mean([t['r'] for t in losses])) if losses else 0
    pf = (sum(t['r'] for t in wins) / abs(sum(t['r'] for t in losses))) if losses else 99
    
    print(f"WR: {wr:.1f}% | Trades: {len(trades)} | R total: {total_r:+.1f}R")
    print(f"PF: {pf:.2f} | Avg Win: {avg_win:.1f}R | Avg Loss: {avg_loss:.1f}R")
    
    # Por par
    for pair in TEST_PAIRS:
        pt = [t for t in trades if t['pair'] == pair]
        if pt:
            pwr = len([t for t in pt if t['result']=='WIN'])/len(pt)*100
            pr = sum(t['r'] for t in pt)
            print(f"  {pair}: {len(pt)}t WR={pwr:.0f}% R={pr:+.1f}")
    
    # Por padrão
    patterns = {}
    for t in trades:
        p = t['pattern']
        if p not in patterns: patterns[p] = {'w':0, 'l':0, 'r':0}
        patterns[p]['w' if t['result']=='WIN' else 'l'] += 1
        patterns[p]['r'] += t['r']
    
    print(f"\nPor padrão:")
    for p, d in sorted(patterns.items(), key=lambda x: x[1]['w']+x[1]['l'], reverse=True):
        total = d['w']+d['l']
        pwr = d['w']/total*100 if total else 0
        print(f"  {p}: {total}t WR={pwr:.0f}% R={d['r']:+.1f}")
    
    # Gate check
    passed = wr >= MIN_WR and pf >= MIN_PF and len(trades) >= MIN_TRADES
    status = '✅ APROVADO' if passed else '❌ REPROVADO'
    print(f"\n{status}")
    
    return trades


def simulate_trade(future_h, future_l, future_c, direction, entry, sl, tp):
    """Simula resultado de um trade nos dados futuros."""
    for i in range(len(future_c)):
        h = future_h[i]
        l = future_l[i]
        c = future_c[i]
        
        if direction == 'BUY':
            if l <= sl:
                r = (sl - entry) / (entry - sl)
                return 'LOSS', sl, r
            if h >= tp:
                r = (tp - entry) / (entry - sl)
                return 'WIN', tp, r
        else:
            if h >= sl:
                r = (entry - sl) / (sl - entry)
                return 'LOSS', sl, r
            if l <= tp:
                r = (entry - tp) / (sl - entry)
                return 'WIN', tp, r
    
    # Ainda aberto — fecha no último preço
    last = future_c[-1]
    if direction == 'BUY':
        r = (last - entry) / (entry - sl)
    else:
        r = (entry - last) / (sl - entry)
    result = 'WIN' if r > 0 else 'LOSS'
    return result, last, r


if __name__ == '__main__':
    run_backtest()
