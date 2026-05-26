#!/usr/bin/env python3
"""
SSC Full Strategy — CRT + Sweep + FVG com multi-timeframe
Baseado nos 16 vídeos transcritos do canal SSC.
Filtros: Tendência (H1) → Range CRT (M15) → Sweep (M15) → FVG (M15)
"""
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import json, sys

PAIRS = {
    'GBP/USD': {'sym': 'GBPUSD=X', 'pip': 0.0001},
    'AUD/USD': {'sym': 'AUDUSD=X', 'pip': 0.0001},
    'NZD/USD': {'sym': 'NZDUSD=X', 'pip': 0.0001},
    'EUR/USD': {'sym': 'EURUSD=X', 'pip': 0.0001},
}

# ═══ CONFIG SSC ═══
RR = 3.0
MIN_FVG_PIPS = 1.0
CRT_RANGE_PERCENTILE = 0.8
EMA_PERIOD = 20

# Killzones SSC (BRT): 5-6h (Asia sweep), 9-10h (London sweep)
KILLZONES_BRT = [(5, 6), (9, 10)]  # (start_hour, end_hour)

def get_h1_trend(df_h1):
    """Filtro 1: Tendência dominante no H1 via EMA20 + swing structure"""
    if len(df_h1) < EMA_PERIOD + 5:
        return None
    
    closes = df_h1['Close'].values.astype(float)
    
    # EMA20
    ema = np.zeros(len(closes))
    alpha = 2.0 / (EMA_PERIOD + 1)
    ema[0] = closes[0]
    for i in range(1, len(closes)):
        ema[i] = alpha * closes[i] + (1 - alpha) * ema[i-1]
    
    # Swing highs/lows
    highs = df_h1['High'].values.astype(float)[-20:]
    lows = df_h1['Low'].values.astype(float)[-20:]
    closes20 = closes[-20:]
    
    sh = []
    sl = []
    for i in range(2, len(highs)-2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            sh.append(i)
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            sl.append(i)
    
    # Tendência: preço atual vs EMA + higher highs/lows
    current = closes[-1]
    ema_current = ema[-1]
    
    if current > ema_current and sh and (len(sh) < 2 or sh[-1] > sh[-2]):
        return 'BULLISH'
    elif current < ema_current and sl and (len(sl) < 2 or sl[-1] > sl[-2]):
        return 'BEARISH'
    
    return None  # Range/sem tendência clara

def detect_sweep(df_m15, trend, pip_val):
    """Filtro 2: Sweep de liquidez — candle11 rompe extremo do range e reverte"""
    if len(df_m15) < 20:
        return None
    
    df20 = df_m15.iloc[-20:]
    highs = df20['High'].values.astype(float)
    lows = df20['Low'].values.astype(float)
    closes = df20['Close'].values.astype(float)
    
    # Range das últimas 15 velas
    range_high = max(highs[-15:-3])
    range_low = min(lows[-15:-3])
    
    # Procurar sweep: candle quebra extremo e fecha de volta
    for i in range(len(df20)-5, len(df20)):
        candle_high = float(df20.iloc[i]['High'])
        candle_low = float(df20.iloc[i]['Low'])
        candle_close = float(df20.iloc[i]['Close'])
        candle_open = float(df20.iloc[i]['Open'])
        
        if trend == 'BULLISH':
            # Sweep de baixa: rompe low do range e reverte (stop hunt)
            if candle_low < range_low and candle_close > range_low:
                # Candle de rejeição (pavio inferior grande)
                body = abs(candle_close - candle_open)
                lower_wick = min(candle_open, candle_close) - candle_low
                if lower_wick > body * 1.5:
                    return {'type': 'BUY', 'idx': i + len(df_m15) - 20,
                            'level': range_low, 'candle_idx': i}
        
        elif trend == 'BEARISH':
            # Sweep de alta: rompe high do range e reverte
            if candle_high > range_high and candle_close < range_high:
                body = abs(candle_close - candle_open)
                upper_wick = candle_high - max(candle_open, candle_close)
                if upper_wick > body * 1.5:
                    return {'type': 'SELL', 'idx': i + len(df_m15) - 20,
                            'level': range_high, 'candle_idx': i}
    
    return None

def detect_crt_range(df_m15, trend, sweep):
    """Filtro 3: Intervalo CRT — range de velas opostas à tendência"""
    if sweep is None:
        return None
    
    # Pegar velas ANTES do sweep (acumulação)
    sweep_local_idx = sweep['candle_idx']
    df_before = df_m15.iloc[max(0, sweep['idx']-15):sweep['idx']]
    
    if len(df_before) < 5:
        return None
    
    highs = df_before['High'].values.astype(float)
    lows = df_before['Low'].values.astype(float)
    
    crt_high = max(highs)
    crt_low = min(lows)
    crt_range = crt_high - crt_low
    
    # CRT válido: range mínimo de 3 pips
    pip_val = 0.0001  # será substituído pelo cfg
    if crt_range < 3 * pip_val:
        return None
    
    return {
        'high': crt_high,
        'low': crt_low,
        'range_pips': crt_range / pip_val,
        'candles': len(df_before)
    }

def detect_fvg_ict(df_m15, pip_val, sweep_idx):
    """Filtro 4: FVG ICT após sweep"""
    df_after = df_m15.iloc[sweep_idx:sweep_idx+10]
    if len(df_after) < 5:
        return None
    
    h = df_after['High'].values.astype(float)
    l = df_after['Low'].values.astype(float)
    
    # Procurar FVG de 3 velas
    for j in range(len(h)-2):
        # Bullish FVG: candle[j].high < candle[j+2].low
        if h[j] < l[j+2]:
            gap = (l[j+2] - h[j]) / pip_val
            if gap >= MIN_FVG_PIPS:
                return {'type': 'BUY', 'entry': l[j+2], 'gap': gap}
        
        # Bearish FVG: candle[j].low > candle[j+2].high
        if l[j] > h[j+2]:
            gap = (l[j] - h[j+2]) / pip_val
            if gap >= MIN_FVG_PIPS:
                return {'type': 'SELL', 'entry': h[j+2], 'gap': gap}
    
    return None

def in_killzone(dt_brt):
    """Verifica se o horário está numa killzone SSC"""
    hour = dt_brt.hour
    for start, end in KILLZONES_BRT:
        if start <= hour < end:
            return True
    return False

def is_crt_candle(df, idx):
    """CRT candle: range grande relativo às últimas 20 velas"""
    if idx < 20:
        return False
    rng = abs(float(df.iloc[idx]['High']) - float(df.iloc[idx]['Low']))
    recent = sorted([abs(float(df.iloc[i]['High']) - float(df.iloc[i]['Low'])) 
                    for i in range(idx-19, idx+1)])
    threshold = recent[int(len(recent) * CRT_RANGE_PERCENTILE)]
    return rng >= threshold

def crt_confirmation(df, idx):
    """Confirmação CRT: vela seguinte fecha dentro do range da CRT"""
    if idx + 1 >= len(df):
        return False
    h1 = float(df.iloc[idx]['High'])
    l1 = float(df.iloc[idx]['Low'])
    c2 = float(df.iloc[idx+1]['Close'])
    return l1 <= c2 <= h1

def simulate(df, sig_idx, sig_type, entry, fvg_pips, pip_val):
    """Simula trade: verifica TP/SL"""
    sl_pips = max(fvg_pips, 2.0)
    tp_pips = sl_pips * RR
    
    if sig_type == 'BUY':
        sl = entry - sl_pips * pip_val
        tp = entry + tp_pips * pip_val
    else:
        sl = entry + sl_pips * pip_val
        tp = entry - tp_pips * pip_val
    
    for i in range(sig_idx + 1, len(df)):
        lo = float(df.iloc[i]['Low'])
        hi = float(df.iloc[i]['High'])
        if sig_type == 'BUY':
            if lo <= sl:
                return 'LOSS', -sl_pips
            if hi >= tp:
                return 'WIN', tp_pips
        else:
            if hi >= sl:
                return 'LOSS', -sl_pips
            if lo <= tp:
                return 'WIN', tp_pips
    
    return 'OPEN', 0

# ═══════════════════════════════════════════
# BACKTEST
# ═══════════════════════════════════════════

def backtest_full(pair, cfg, days=30):
    """Backtest SSC completo: tendência H1 + sweep + CRT + FVG"""
    pip_val = cfg['pip']
    
    # Baixar dados M15
    df_m15 = yf.Ticker(cfg['sym']).history(period=f'{days}d', interval='15m')
    if len(df_m15) < 100:
        return None
    
    # Baixar H1 para tendência
    df_h1 = yf.Ticker(cfg['sym']).history(period=f'{days}d', interval='1h')
    
    results = {'pair': pair, 'signals': [], 'wins': 0, 'losses': 0, 'pnl': 0}
    
    # Janela deslizante: analisar a cada 15 min
    step = 4  # A cada 1 hora (4 candles de 15m)
    
    for start_idx in range(100, len(df_m15) - 30, step):
        window = df_m15.iloc[:start_idx+30]
        current_time = window.index[-1]
        
        # Converter para BRT (GMT-3)
        dt_brt = current_time - timedelta(hours=3)
        
        # Killzone filter
        if not in_killzone(dt_brt):
            continue
        
        # Filtro 1: Tendência H1
        h1_window = df_h1[df_h1.index <= current_time]
        trend = get_h1_trend(h1_window)
        if trend is None:
            continue
        
        # Filtro 2: Sweep
        sweep = detect_sweep(window, trend, pip_val)
        if sweep is None:
            continue
        
        # Filtro 3: CRT Range
        crt_range = detect_crt_range(window, trend, sweep)
        if crt_range is None:
            continue
        
        # Filtro 4: FVG
        fvg = detect_fvg_ict(window, pip_val, sweep['idx'])
        if fvg is None:
            continue
        
        # Direção deve bater com tendência e sweep
        if fvg['type'] != sweep['type']:
            continue
        
        # Simular trade
        result, pnl = simulate(df_m15, sweep['idx'], fvg['type'], 
                               fvg['entry'], fvg['gap'], pip_val)
        
        if result != 'OPEN':
            time_str = dt_brt.strftime('%d/%m %H:%M')
            results['signals'].append({
                'time': time_str,
                'type': fvg['type'],
                'entry': round(fvg['entry'], 5),
                'fvg_gap': round(fvg['gap'], 1),
                'result': result,
                'pnl': round(pnl, 1)
            })
            if result == 'WIN':
                results['wins'] += 1
            else:
                results['losses'] += 1
            results['pnl'] += pnl
    
    return results

# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

if __name__ == '__main__':
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    print(f"═" * 65)
    print(f"  BACKTEST SSC COMPLETO — {days} dias")
    print(f"  Tendência H1 → Range CRT → Sweep → FVG")
    print(f"═" * 65)
    
    all_signals = []
    total = {'wins': 0, 'losses': 0, 'pnl': 0}
    
    for pair, cfg in PAIRS.items():
        print(f"\n{pair}...")
        r = backtest_full(pair, cfg, days)
        if r and r['signals']:
            wr = r['wins']/(r['wins']+r['losses'])*100
            print(f"  {len(r['signals'])} trades | {r['wins']}W/{r['losses']}L | WR={wr:.0f}% | PnL={r['pnl']:+.1f}p")
            for s in r['signals'][-5:]:
                print(f"    {s['time']} {s['type']:5s} @{s['entry']:.5f} gap={s['fvg_gap']:.1f}p → {s['result']:4s} {s['pnl']:+.1f}p")
            total['wins'] += r['wins']
            total['losses'] += r['losses']
            total['pnl'] += r['pnl']
            all_signals.extend(r['signals'])
        else:
            print(f"  Sem sinais")
    
    total_t = total['wins'] + total['losses']
    if total_t > 0:
        wr = total['wins'] / total_t * 100
        print(f"\n{'═' * 65}")
        print(f"  TOTAL: {total_t} trades | {total['wins']}W/{total['losses']}L | WR={wr:.1f}% | PnL={total['pnl']:+.1f}p")
        print(f"{'═' * 65}")
    else:
        print(f"\n  ⚠️ ZERO sinais nos 4 pares")
