#!/usr/bin/env python3
"""
BACKTEST v9.5 — Multi-TF Bias + FVG M15 — 30 dias
Estratégia: Bias H4/D → FVG M15 → RR 3:1
"""
import sys, os
from datetime import datetime
import numpy as np

sys.path.insert(0, '/home/roberto/.hermes/scripts')
from tv_data import fetch_ohlcv

# ═══ CONFIG ═══
RR = 3.0
MIN_SL = 10
MAX_SL = 20

PAIRS = {
    'USDJPY':  {'sym': 'USDJPY=X', 'pip': 0.01},
    'GBPJPY':  {'sym': 'GBPJPY=X', 'pip': 0.01},
    'USDCAD':  {'sym': 'USDCAD=X', 'pip': 0.0001},
    'EURJPY':  {'sym': 'EURJPY=X', 'pip': 0.01},
    'GBPUSD':  {'sym': 'GBPUSD=X', 'pip': 0.0001},
    'EURUSD':  {'sym': 'EURUSD=X', 'pip': 0.0001},
    'XAUUSD':  {'sym': 'GC=F',     'pip': 0.01, 'metal': True},
}

def get_bias_daily(highs, lows, closes):
    """Bias: candle -2 vs candle -3 (ontem vs anteontem)."""
    if len(highs) < 3:
        return 'NEUTRAL'
    ph, pl = highs[-3], lows[-3]
    ch, cl, cc = highs[-2], lows[-2], closes[-2]
    if ch > ph and cc < ph: return 'SELL'
    if cl < pl and cc > pl: return 'BUY'
    if ch > ph and cc > ph: return 'BUY'
    if cl < pl and cc < pl: return 'SELL'
    return 'NEUTRAL'

def detect_fvg(highs, lows, closes, direction, pip_size, is_metal=False):
    """FVG: gap entre low[i] e high[i-2]."""
    n = len(closes)
    if n < 10:
        return []
    min_gap = 100 if is_metal else 1.0
    out = []
    for i in range(6, n - 1):
        if lows[i] > highs[i-2]:
            gap = (lows[i] - highs[i-2]) / pip_size
            if gap >= min_gap and direction == 'BUY':
                out.append({'dir': 'BUY', 'entry': closes[i], 'gap': gap,
                           'sl_pips': max(gap * 1.2, MIN_SL), 'idx': i})
        if highs[i] < lows[i-2]:
            gap = (lows[i-2] - highs[i]) / pip_size
            if gap >= min_gap and direction == 'SELL':
                out.append({'dir': 'SELL', 'entry': closes[i], 'gap': gap,
                           'sl_pips': max(gap * 1.2, MIN_SL), 'idx': i})
    return out

# ═══ MAIN ═══
print("=" * 60)
print("BACKTEST v9.5 — 30 dias — Multi-TF Bias + FVG M15")
print(f"{datetime.now().strftime('%d/%m/%Y %H:%M')}")
print("=" * 60)

all_trades = []

for name, cfg in PAIRS.items():
    sym = cfg['sym']
    pip = cfg['pip']
    metal = cfg.get('metal', False)
    
    print(f"\n--- {name} ---")
    
    try:
        df_d = fetch_ohlcv(sym, period='30d', interval='1d')
        df_15m = fetch_ohlcv(sym, period='30d', interval='15m')
        df_4h = fetch_ohlcv(sym, period='30d', interval='4h')
        
        if df_15m is None or len(df_15m) < 200:
            print("  Sem dados M15")
            continue
        if df_d is None or len(df_d) < 5:
            print("  Sem dados diários")
            continue
        
        h15 = df_15m['High'].astype(float).values
        l15 = df_15m['Low'].astype(float).values
        c15 = df_15m['Close'].astype(float).values
        o15 = df_15m['Open'].astype(float).values
        t15 = df_15m.index
        
        h_d = df_d['High'].astype(float).values
        l_d = df_d['Low'].astype(float).values
        c_d = df_d['Close'].astype(float).values
        t_d = df_d.index
        
        # Mapear cada candle M15 ao seu dia
        m15_day = [t.date() for t in t15]
        days = sorted(set(m15_day))
        
        trades = []
        last_trade_day = None
        
        # Para cada dia (a partir do dia 5)
        for day_idx in range(5, len(days)):
            day = days[day_idx]
            
            # Encontrar candles M15 deste dia
            day_candles = [j for j, d in enumerate(m15_day) if d == day]
            if len(day_candles) < 16:  # Pelo menos 4h de dados
                continue
            
            # Índice do dia no dataframe diário
            day_d_idx = None
            for d in range(len(t_d)):
                if t_d[d].date() == day:
                    day_d_idx = d
                    break
            if day_d_idx is None or day_d_idx < 2:
                continue
            
            # ═══ DAILY BIAS ═══
            # Usar dados diários até ONTEM (day_d_idx - 1)
            d_slice_highs = h_d[:day_d_idx+1]
            d_slice_lows = l_d[:day_d_idx+1]
            d_slice_closes = c_d[:day_d_idx+1]
            
            if len(d_slice_highs) < 3:
                continue
            
            bias_d = get_bias_daily(d_slice_highs, d_slice_lows, d_slice_closes)
            
            # ═══ H4 BIAS (se daily neutro, tentar H4) ═══
            if bias_d == 'NEUTRAL' and df_4h is not None and len(df_4h) >= 3:
                h4_h = df_4h['High'].astype(float).values
                h4_l = df_4h['Low'].astype(float).values
                h4_c = df_4h['Close'].astype(float).values
                h4_t = df_4h.index
                # Último candle H4 antes do dia atual
                h4_slice = [j for j, t in enumerate(h4_t) if t.date() < day]
                if len(h4_slice) >= 3:
                    idx = h4_slice[-1] + 1
                    bias_d = get_bias_daily(h4_h[:idx], h4_l[:idx], h4_c[:idx])
            
            if bias_d == 'NEUTRAL':
                continue
            
            # ═══ ENTRADA: FVG no M15 do dia ═══
            # Varrer candles do dia em busca de FVG
            for candle_offset in range(8, len(day_candles) - 1):
                i = day_candles[candle_offset]
                
                if last_trade_day == day:
                    continue  # Só 1 trade por dia
                
                local_h = h15[max(0,i-12):i+1]
                local_l = l15[max(0,i-12):i+1]
                local_c = c15[max(0,i-12):i+1]
                local_o = o15[max(0,i-12):i+1]
                
                fvgs = detect_fvg(local_h, local_l, local_c, bias_d, pip, metal)
                if not fvgs:
                    continue
                
                s = fvgs[-1]
                sl_pips = max(MIN_SL, min(s['sl_pips'], MAX_SL if not metal else 300))
                entry = s['entry']
                
                if s['dir'] == 'BUY':
                    sl_price = entry - sl_pips * pip
                    tp_price = entry + sl_pips * RR * pip
                else:
                    sl_price = entry + sl_pips * pip
                    tp_price = entry - sl_pips * RR * pip
                
                # Simular candles seguintes (resto do dia + próximo dia)
                result = 'OPEN'
                exit_price = 0
                candles_held = 0
                
                for j in range(i + 1, min(i + 400, len(h15))):
                    candles_held += 1
                    if s['dir'] == 'BUY':
                        if h15[j] >= tp_price:
                            result = 'WIN'; exit_price = tp_price; break
                        if l15[j] <= sl_price:
                            result = 'LOSS'; exit_price = sl_price; break
                    else:
                        if l15[j] <= tp_price:
                            result = 'WIN'; exit_price = tp_price; break
                        if h15[j] >= sl_price:
                            result = 'LOSS'; exit_price = sl_price; break
                
                if result in ('WIN', 'LOSS'):
                    trades.append({
                        'pair': name, 'day': str(day), 'bias': bias_d,
                        'dir': s['dir'], 'entry': round(entry, 5),
                        'sl': round(sl_price, 5), 'tp': round(tp_price, 5),
                        'sl_pips': sl_pips, 'gap': round(s['gap'], 1),
                        'result': result, 'exit': round(exit_price, 5),
                        'candles': candles_held,
                        'r': RR if result == 'WIN' else -1.0,
                    })
                    last_trade_day = day
                    break  # Próximo dia
        
        if trades:
            wins = sum(1 for t in trades if t['result'] == 'WIN')
            wr = wins / len(trades) * 100
            r_tot = sum(t['r'] for t in trades)
            print(f"  {len(trades)} trades | WR: {wr:.1f}% | R: {r_tot:+.1f}")
            for t in trades[-5:]:
                e = '✅' if t['result'] == 'WIN' else '❌'
                print(f"  {e} {t['day']} {t['dir']:4s} {t['bias']:4s} "
                      f"SL={t['sl_pips']:.0f}p → {t['result']} ({t['candles']}v)")
            all_trades.extend(trades)
        else:
            print("  0 trades")
    
    except Exception as e:
        print(f"  ERRO: {e}")
        import traceback
        traceback.print_exc()

# ═══ CONSOLIDADO ═══
print("\n" + "=" * 60)
print("CONSOLIDADO FINAL")
print("=" * 60)

if all_trades:
    wins = sum(1 for t in all_trades if t['result'] == 'WIN')
    total = len(all_trades)
    wr = wins / total * 100
    r_total = sum(t['r'] for t in all_trades)
    
    win_r = sum(t['r'] for t in all_trades if t['r'] > 0)
    loss_r = abs(sum(t['r'] for t in all_trades if t['r'] < 0))
    pf = win_r / loss_r if loss_r > 0 else float('inf')
    
    print(f"Total:    {total} trades")
    print(f"Win Rate: {wr:.1f}%")
    print(f"R total:  {r_total:+.1f}R")
    print(f"Profit F: {pf:.2f}")
    
    # Por par
    print(f"\n{'Par':8s} {'Trades':>6s} {'WR':>6s} {'R':>6s}")
    print("-" * 30)
    for p in sorted(set(t['pair'] for t in all_trades)):
        pt = [t for t in all_trades if t['pair'] == p]
        pw = sum(1 for t in pt if t['result'] == 'WIN')
        pr = sum(t['r'] for t in pt)
        print(f"{p:8s} {len(pt):6d} {pw/len(pt)*100:5.1f}% {pr:+5.1f}R")
    
    # Por direção
    for d in ['BUY', 'SELL']:
        dt = [t for t in all_trades if t['dir'] == d]
        if dt:
            dw = sum(1 for t in dt if t['result'] == 'WIN')
            dr = sum(t['r'] for t in dt)
            print(f"\n{d}: {len(dt)} trades, {dw/len(dt)*100:.1f}% WR, {dr:+.1f}R")
    
    # Drawdown
    eq = 0
    peak = 0
    max_dd = 0
    for t in all_trades:
        eq += t['r']
        peak = max(peak, eq)
        max_dd = max(max_dd, peak - eq)
    print(f"\nMax DD:   {max_dd:.1f}R")
    print(f"Equity:   {eq:+.1f}R")
    
    # Risco simulado com 0.5%
    print(f"\nRisco 0.5% por trade:")
    print(f"  Ganho total: {r_total * 0.5:.1f}% da conta")
    print(f"  Max DD:      {max_dd * 0.5:.1f}% da conta")
else:
    print("Nenhum trade.")

print("\n=== FIM ===")
