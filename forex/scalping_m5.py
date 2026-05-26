#!/usr/bin/python3
"""
SCALPING PIPELINE — Curto Prazo (M5/M15)
==========================================
- Dados intraday via Yahoo Finance (5m, 15m)
- Stops apertados: 5-15 pips
- Alavancagem 50x com gestão 1:3
- Análise por microestrutura (momentum, rompimento)
"""

import requests
import statistics
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

# ═══════════════════════ CONFIG ═══════════════════════
PAIRS = {
    'EUR/USD': 'EURUSD=X',
    'GBP/USD': 'GBPUSD=X',
    'USD/JPY': 'JPY=X',
    'AUD/USD': 'AUDUSD=X',
    'EUR/GBP': 'EURGBP=X',
    'EUR/JPY': 'EURJPY=X',
}

CAPITAL = 1000.0
ALAVANCAGEM = 50
RISCO_PCT = 1.0          # 1% por trade
RELACAO_RR = 3.0          # 1:3
STOP_ATR_MULT = 1.0       # Stop = 1×ATR (bem mais apertado pra M5)
MIN_SCORE_ENTRY = 2.0     # Score mínimo pra entrar

# ═══════════════════ DATA FETCH ═══════════════════════

def fetch_intraday(symbol, interval='5m', hours=6):
    """Busca dados intraday M5 ou M15 do Yahoo Finance."""
    end = int(datetime.now().timestamp())
    start = int((datetime.now() - timedelta(hours=hours)).timestamp())
    url = (f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'
           f'?period1={start}&period2={end}&interval={interval}')
    
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        data = r.json()['chart']['result'][0]
        quotes = data['indicators']['quote'][0]
        closes = [c for c in quotes['close'] if c is not None]
        highs  = [h for h in quotes['high'] if h is not None]
        lows   = [l for l in quotes['low'] if l is not None]
        opens  = [o for o in quotes['open'] if o is not None]
        volumes = [v for v in quotes['volume'] if v is not None]
        return {'opens': opens, 'highs': highs, 'lows': lows, 'closes': closes, 'volumes': volumes}
    except Exception as e:
        return {'error': str(e)}

# ═══════════════════ ANÁLISE TÉCNICA M5 ═══════════════════════

def ema(data, period):
    if len(data) < period:
        return data[-1]
    mult = 2 / (period + 1)
    val = sum(data[:period]) / period
    for p in data[period:]:
        val = (p - val) * mult + val
    return val

def rsi(closes, period=9):  # RSI mais rápido (9 em vez de 14)
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, period + 1):
        diff = closes[-(period + 1) + i] - closes[-(period + 1) + i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0: return 100.0
    return round(100 - (100 / (1 + avg_gain / avg_loss)), 2)

def atr_m5(highs, lows, closes, period=14):
    """ATR para timeframe curto."""
    if len(closes) < period + 1:
        return (max(highs[-5:]) - min(lows[-5:])) / 5 if highs else 0.0001
    trs = []
    for i in range(-period, 0):
        h, l = highs[i], lows[i]
        c_prev = closes[i - 1] if i > -period else closes[i]
        trs.append(max(h - l, abs(h - c_prev), abs(l - c_prev)))
    return sum(trs) / period

def detect_momentum(closes, period=5):
    """Força do momentum nos últimos N candles."""
    if len(closes) < period + 1:
        return 0
    recent = closes[-(period+1):]
    changes = [(recent[i+1] - recent[i]) / recent[i] * 10000 for i in range(period)]
    return sum(changes)  # soma dos ticks de movimento

def detect_breakout(highs, lows, closes, lookback=10):
    """Detecta rompimento de range recente."""
    if len(closes) < lookback:
        return None
    recent_high = max(highs[-lookback:-1])
    recent_low = min(lows[-lookback:-1])
    current = closes[-1]
    
    range_size = recent_high - recent_low
    if range_size == 0:
        return None
    
    if current > recent_high:
        return {'type': 'BREAKOUT_ALTA', 'level': recent_high, 'range': range_size}
    elif current < recent_low:
        return {'type': 'BREAKOUT_BAIXA', 'level': recent_low, 'range': range_size}
    return None

def analyze_m5(pair_name, data):
    """Análise completa para timeframe curto."""
    if 'error' in data or len(data['closes']) < 20:
        return None
    
    closes = data['closes']
    highs = data['highs']
    lows = data['lows']
    
    current = closes[-1]
    prev = closes[-2] if len(closes) >= 2 else current
    atr_val = atr_m5(highs, lows, closes, 14)
    
    # Indicadores
    ema9 = ema(closes, 9)
    ema21 = ema(closes, 21)
    rsi9 = rsi(closes, 9)
    momentum = detect_momentum(closes, 5)
    breakout = detect_breakout(highs, lows, closes, 10)
    
    # Determinar direção
    score = 0.0
    signals = []
    
    # 1. EMA cruzamento (peso 2)
    if ema9 > ema21:
        score += 2.0
        signals.append('EMA9>EMA21')
    else:
        score -= 2.0
        signals.append('EMA9<EMA21')
    
    # 2. RSI (peso 1.5)
    if rsi9 < 35:
        score += 1.5
        signals.append(f'RSI={rsi9:.0f} sobrevendido')
    elif rsi9 > 65:
        score -= 1.5
        signals.append(f'RSI={rsi9:.0f} sobrecomprado')
    elif rsi9 > 50:
        score += 0.5
        signals.append(f'RSI={rsi9:.0f} bullish')
    else:
        score -= 0.5
        signals.append(f'RSI={rsi9:.0f} bearish')
    
    # 3. Momentum (peso 1.5)
    if momentum > 2:  # 2+ pips de momentum
        score += 1.5
        signals.append(f'Mom={momentum:.1f}pips↑')
    elif momentum < -2:
        score -= 1.5
        signals.append(f'Mom={momentum:.1f}pips↓')
    else:
        signals.append(f'Mom={momentum:.1f}pips flat')
    
    # 4. Volume (peso 0.5) - se disponível
    if data.get('volumes') and len(data['volumes']) >= 3:
        recent_vol = [v for v in data['volumes'][-3:] if v and v > 0]
        if recent_vol:
            avg_vol = statistics.mean(recent_vol)
            current_vol = recent_vol[-1] if recent_vol else 0
            ratio = current_vol / avg_vol if avg_vol > 0 else 1
            if current_vol > 0 and ratio > 1.5:
                score += 0.5 if momentum > 0 else -0.5
                signals.append(f'Vol↑ ({ratio:.1f}x)')
    
    # Decisão
    if score >= MIN_SCORE_ENTRY:
        direction = 'COMPRA'
        strength = 'FORTE' if score >= 3.5 else 'MODERADO'
    elif score <= -MIN_SCORE_ENTRY:
        direction = 'VENDA'
        strength = 'FORTE' if score <= -3.5 else 'MODERADO'
    else:
        direction = 'NEUTRO'
        strength = 'FRACO'
    
    # Stops e Targets (baseado em ATR do M5)
    if direction != 'NEUTRO':
        stop_distance = STOP_ATR_MULT * atr_val
        target_distance = stop_distance * RELACAO_RR
        
        if direction == 'COMPRA':
            stop = current - stop_distance
            target = current + target_distance
        else:
            stop = current + stop_distance
            target = current - target_distance
        
        # Pips
        pips_factor = 100 if 'JPY' in pair_name else 10000
        stop_pips = stop_distance * pips_factor
        target_pips = target_distance * pips_factor
    else:
        stop = target = stop_pips = target_pips = None
    
    # Breakout
    breakout_signal = None
    if breakout:
        breakout_signal = breakout['type']
        signals.append(breakout['type'])
    
    return {
        'pair': pair_name,
        'timeframe': 'M5',
        'price': round(current, 5),
        'change_1candle': round((current - prev) / prev * 100, 4),
        'score': round(score, 2),
        'direction': direction,
        'strength': strength,
        'signals': signals,
        'indicators': {
            'ema9': round(ema9, 5),
            'ema21': round(ema21, 5),
            'rsi9': round(rsi9, 1),
            'atr': round(atr_val, 6),
            'momentum_pips': round(momentum, 1),
        },
        'trade': {
            'entry': round(current, 5),
            'stop': round(stop, 5) if stop else None,
            'target': round(target, 5) if target else None,
            'stop_pips': round(stop_pips, 1) if stop_pips else None,
            'target_pips': round(target_pips, 1) if target_pips else None,
        },
        'breakout': breakout_signal,
        'timestamp': datetime.now().isoformat(),
        'candles_analyzed': len(closes)
    }

# ═══════════════════ MAIN ═══════════════════════

if __name__ == '__main__':
    print(f"╔{'═'*58}╗")
    print(f"║  ⚡ SCALPING M5 — Análise Curto Prazo")
    print(f"║  {datetime.now().strftime('%d/%m/%Y %H:%M')} BRT | Alavancagem {ALAVANCAGEM}x | RR 1:{RELACAO_RR:.0f}")
    print(f"╚{'═'*58}╝\n")
    
    all_signals = []
    
    for pair, symbol in PAIRS.items():
        data = fetch_intraday(symbol, '5m', hours=6)
        result = analyze_m5(pair, data)
        
        if result is None:
            print(f"  ❌ {pair}: dados insuficientes")
            continue
        
        all_signals.append(result)
        
        dir_icon = {'COMPRA': '🟢', 'VENDA': '🔴', 'NEUTRO': '⚪'}
        icon = dir_icon.get(result['direction'], '⚪')
        
        print(f"  {icon} {pair}: {result['price']} | {result['direction']} ({result['strength']}) | Score={result['score']}")
        print(f"     EMA9={result['indicators']['ema9']} EMA21={result['indicators']['ema21']} | "
              f"RSI={result['indicators']['rsi9']} | Mom={result['indicators']['momentum_pips']} pips")
        
        if result['breakout']:
            print(f"     ⚡ {result['breakout']}")
        
        if result['trade']['stop']:
            print(f"     🎯 Entry={result['price']} | Stop={result['trade']['stop']} ({result['trade']['stop_pips']}p) | "
                  f"Target={result['trade']['target']} ({result['trade']['target_pips']}p)")
        
        if result['direction'] != 'NEUTRO':
            risco = RISCO_PCT
            ganho = RISCO_PCT * RELACAO_RR
            print(f"     💰 Risco: {risco}% (R${CAPITAL*risco/100:.0f}) → Alvo: {ganho}% (R${CAPITAL*ganho/100:.0f})")
        
        print()
    
    # Resumo
    buys = sum(1 for s in all_signals if s['direction'] == 'COMPRA')
    sells = sum(1 for s in all_signals if s['direction'] == 'VENDA')
    neut = sum(1 for s in all_signals if s['direction'] == 'NEUTRO')
    
    print(f"  {'─'*58}")
    print(f"  📊 Sinais: 🟢{buys} COMPRA | 🔴{sells} VENDA | ⚪{neut} NEUTRO")
    if buys + sells > 0:
        print(f"  ⚡ Pares ativos: {buys + sells}/6 — foco nos FORTES")
    print(f"  {'─'*58}")
