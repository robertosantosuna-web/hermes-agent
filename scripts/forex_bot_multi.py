#!/usr/bin/env python3
"""
Hermes Trading Bot — MULTI-STRATEGY V1 (3 estratégias × 6 pares, 24h)
Atualizado: 26/05/2026 — 3 estratégias simultâneas, sem killzone.

ESTRATÉGIAS:
  E1: FVG+CRT (M15/M30) — gap + CRT≥70%, RR 3:1
  E2: SMC Fractal H1 — MSS + Order Block, RR 2:1
  E3: S/R+FVG M15 — FVG próximo a swing levels, RR 3:1

BACKTEST 59d (todas estratégias combinadas, sem killzone):
  - 393 trades, 67.9% WR, +4056 pips
  - ~33 trades/dia, +1.72R/trade

CORRETORA: IC Markets Demo (MT5 display:0)
CONTA: Demo hedge (Raw Trading Ltd)
"""

from tv_data import fetch_ohlcv
import pandas as pd
import numpy as np
import json, time, os, sys, urllib.request
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/home/roberto/.hermes/scripts')
from mt5_direct import close_all as mt5_close_all
from hermes_mt5_bridge import send_order, get_status as mt5_get_status
from telegram_notify import notify_open
from trade_tracker import record_trade
from brain_bot_bridge import get_weekly_bias, get_macro_context, notify_trade, read_user_commands

# Multi-Agent System
try:
    from multi_agent import ConfluenciaAgent
    MULTI_AGENT = ConfluenciaAgent()
except:
    MULTI_AGENT = None

# ══════════════════════════════════════════
# CONFIGURAÇÃO
# ══════════════════════════════════════════
REAL_ACCOUNT = False
INITIAL_BALANCE = 334.89  # Fallback — será atualizado pelo MT5 no startup
RISK_PERCENT = 0.5                 # Risco fixo 0.5% por trade ( Roberto 29/05)
DAILY_STOP_PERCENT = 5.0
DRAWDOWN_ALERT_PERCENT = 3.0
MAX_DAILY_TRADES = 20               # MÁXIMO de ordens por dia (evita overtrading)
VOLUME = 0.01
MAX_POSITIONS = 4                  # Reduzido: $400 conta, 0.5% risco = 4 posições máx
RISK_PERCENT_BASE = 0.5            # % base do saldo por trade (fixo, sem dinâmico)
MIN_SL_PIPS = 10                    # Mínimo 10 pips — entrada M1 permite SL mais curto

# ══════════════════════════════════════════
# KILLZONE UNIVERSAL GATING (NEO Recomendação #2)
# ══════════════════════════════════════════
DEAD_ZONES_UTC = [(18, 23)]          # Horários PROIBIDOS (WR 0-37%)
LOW_QUALITY_ZONES_UTC = [(0, 6)]     # Horários de baixa qualidade (requer cautela)
MAX_SIGNAL_AGE = {                   # Idade máxima do sinal em candles
    'M1': 6, 'M5': 6, 'M15': 4, 'M30': 3, 'H1': 2, 'H4': 1
}

# Pip values per 0.01 lot (approximate, updated dynamically)
# XAUUSD: tick=0.01, 0.01 lot=1oz → $0.01/tick
PIP_VALUES = {
    'EURUSD': 0.10, 'GBPUSD': 0.10, 'USDCAD': 0.074,
    'USDJPY': 0.063, 'GBPJPY': 0.071, 'EURJPY': 0.067,
    'XAUUSD': 0.01,   # Ouro: $0.01 por tick (0.01 lote = 1oz)
}

def calculate_volume(balance, sl_pips, pair):
    """Volume com risco fixo 0.5% por trade ( Roberto 29/05)."""
    pip_val = PIP_VALUES.get(pair, 0.10)
    risk_pct = RISK_PERCENT  # Fixo 0.5%
    risk_dollar = balance * risk_pct / 100.0
    lots_001 = risk_dollar / (max(sl_pips, MIN_SL_PIPS) * pip_val)
    lots = max(0.01, round(lots_001 / 100, 2))
    return min(lots, 0.50), risk_pct  # máximo 0.50 lot (conta pequena)
# ══════════════════════════════════════════
# PARES — 2 modos: KZ (qualidade) + No-KZ (volume 24h)
# ══════════════════════════════════════════
BASE_PAIRS = {
    # ── COM Killzone (qualidade) ──
    'USDJPY_KZ':  {'sym': 'USDJPY=X', 'pip': 0.01,   'tf': '5m',  'killzone': [15,16], 'wr': 66.1},
    'GBPJPY_KZ':  {'sym': 'GBPJPY=X', 'pip': 0.01,   'tf': '15m', 'killzone': [6,7],   'wr': 67.6},
    'USDCAD_KZ':  {'sym': 'USDCAD=X', 'pip': 0.0001, 'tf': '15m', 'killzone': [15,16], 'wr': 90.0},
    'EURJPY_KZ':  {'sym': 'EURJPY=X', 'pip': 0.01,   'tf': '30m', 'killzone': [11,15], 'wr': 64.9},
    'GBPUSD_KZ':  {'sym': 'GBPUSD=X', 'pip': 0.0001, 'tf': '30m', 'killzone': [15,16], 'wr': 62.2},
    'EURUSD_KZ':  {'sym': 'EURUSD=X', 'pip': 0.0001, 'tf': '30m', 'killzone': [15,16], 'wr': 73.8},
    'XAUUSD_KZ':  {'sym': 'GC=F',     'pip': 0.01,   'tf': '30m', 'killzone': [0,1,2,3,4,5], 'wr': 77.0, 'metal': True},  # 🥇 Asia 77% WR
    # ── SEM Killzone (volume 24h) ──
    'USDJPY':     {'sym': 'USDJPY=X', 'pip': 0.01,   'tf': '5m',  'killzone': None,    'wr': 66.1},
    'GBPJPY':     {'sym': 'GBPJPY=X', 'pip': 0.01,   'tf': '15m', 'killzone': None,    'wr': 67.6},
    'USDCAD':     {'sym': 'USDCAD=X', 'pip': 0.0001, 'tf': '15m', 'killzone': None,    'wr': 90.0},
    'EURJPY':     {'sym': 'EURJPY=X', 'pip': 0.01,   'tf': '30m', 'killzone': None,    'wr': 64.9},
    'GBPUSD':     {'sym': 'GBPUSD=X', 'pip': 0.0001, 'tf': '30m', 'killzone': None,    'wr': 62.2},
    'EURUSD':     {'sym': 'EURUSD=X', 'pip': 0.0001, 'tf': '30m', 'killzone': None,    'wr': 73.8},
    'XAUUSD':     {'sym': 'GC=F',     'pip': 0.01,   'tf': '30m', 'killzone': None,    'wr': 67.1, 'metal': True},  # 🥇 24h 67.1% WR
}

# SL mínimo para metais (em ticks, 1 tick = $0.01 com 0.01 lote)
MIN_SL_METAL = 1200  # $12 — STOPLEVEL do ouro é ~$2-3, SL de $12 é 4-6× acima
MIN_WR_REAL = 55.0                 # WR mínimo (real) para operar o par (NEO Rec #4: ≥55% p/ expectância positiva)
MIN_SL_PIPS = 10                    # Mínimo 10 pips — entrada M1 permite SL mais curto
MAX_CORRELATED_PAIRS = 1            # Máx 1 par por moeda base ( Roberto 29/05)

TRADE_LOG_FILE = Path.home() / '.hermes' / 'forex' / 'trade_log.json'

def get_real_wr(pair=None, min_trades=5):
    """Calcula WR real da conta a partir do trade_log."""
    try:
        if TRADE_LOG_FILE.exists():
            data = json.loads(TRADE_LOG_FILE.read_text())
            trades = [t for t in data.get('trades', []) if t.get('status') == 'closed' and t.get('result')]
            if pair:
                # Normalize: remove _KZ suffix, remove / 
                pair_clean = pair.replace('_KZ','').replace('/','')
                trades = [t for t in trades if t.get('pair','').replace('_KZ','').replace('/','') == pair_clean]
            if len(trades) < min_trades:
                return None
            wins = sum(1 for t in trades if t.get('result') == 'WIN')
            return round(wins / len(trades) * 100, 1)
    except:
        pass
    return None

def should_trade_pair(pair):
    """Decide se deve operar um par baseado no WR real."""
    wr_real = get_real_wr(pair, min_trades=1)
    if wr_real is not None and wr_real < MIN_WR_REAL:
        print(f"[WR] {pair}: WR real={wr_real}% < {MIN_WR_REAL}% — BLOQUEADO")
        return False
    # Check aggregate WR
    wr_agg = get_real_wr(min_trades=3)
    if wr_agg is not None and wr_agg < 35.0:
        if wr_real is not None and wr_real < 50.0:
            print(f"[WR] {pair}: WR real={wr_real}%, agregado={wr_agg}% — BLOQUEADO")
            return False
    return True

# ══════════════════════════════════════════
# MULTI-TF BIAS + CRT Model (29/05/2026)
# Bias define direção, CRT soma confirmação extra
# ══════════════════════════════════════════

BIAS_LEVELS = [
    {'name': 'W',  'bias_tf': '1d', 'confirm_tf': '4h'},
    {'name': 'D',  'bias_tf': '1d', 'confirm_tf': '1h'},
    {'name': 'H4', 'bias_tf': '4h', 'confirm_tf': '15m'},
]

def get_tf_bias(highs, lows, closes):
    """Viés: candle -2 vs candle -3 (período anterior vs atual)."""
    if len(highs) < 3: return 'NEUTRAL'
    ph, pl = highs[-3], lows[-3]
    ch, cl, cc = highs[-2], lows[-2], closes[-2]
    if ch > ph and cc < ph: return 'SELL'
    if cl < pl and cc > pl: return 'BUY'
    if ch > ph and cc > ph: return 'BUY'
    if cl < pl and cc < pl: return 'SELL'
    return 'NEUTRAL'

def get_multi_tf_bias(sym):
    """Multi-TF bias: maioria dos níveis alinhados."""
    buy = sell = 0
    details = {}
    for lv in BIAS_LEVELS:
        df = fetch_ohlcv(sym, period='5d', interval=lv['bias_tf'])
        if df is None or len(df) < 3: continue
        # Normalizar colunas (yfinance retorna formatos variados)
        col_map = {}
        for c in df.columns:
            cl = c.lower()
            if cl in ('high', 'h'): col_map['h'] = c
            elif cl in ('low', 'l'): col_map['l'] = c
            elif cl in ('close', 'c'): col_map['c'] = c
        if not all(k in col_map for k in ('h','l','c')):
            continue  # colunas insuficientes
        h = df[col_map['h']].astype(float).values
        lo = df[col_map['l']].astype(float).values
        c = df[col_map['c']].astype(float).values
        bias = get_tf_bias(h, lo, c)
        if bias == 'BUY': buy += 1; details[lv['name']] = 'BUY✓'
        elif bias == 'SELL': sell += 1; details[lv['name']] = 'SELL✓'
        else: details[lv['name']] = 'NEUTRAL'
    if buy > sell: return 'BUY', details
    if sell > buy: return 'SELL', details
    return 'NEUTRAL', details

# ══════════════════════════════════════════
# CRT MODEL — filtro extra de qualidade
# ══════════════════════════════════════════

def detect_crt_setup(sym, pip_size):
    """
    Detecta setup CRT (Candle Range Theory) no H1.
    Retorna: dict com setup ou None
      {bias, crt_high, crt_low, sweep_high, sweep_low, sweep_close, sl_price}
    """
    try:
        df_h1 = fetch_ohlcv(sym, period='5d', interval='1h')
        if df_h1 is None or len(df_h1) < 25:
            return None
        
        highs = df_h1['High'].astype(float).values
        lows = df_h1['Low'].astype(float).values
        closes = df_h1['Close'].astype(float).values
        
        # Calcular range médio (últimas 20 velas, excluindo as 2 últimas)
        ranges = [highs[i] - lows[i] for i in range(-22, -2)]
        if not ranges:
            return None
        avg_range = sum(ranges) / len(ranges)
        
        # CRT candle = penúltima vela (índice -2)
        # Sweep candle = última vela (índice -1)
        crt_high = highs[-2]
        crt_low = lows[-2]
        crt_range = crt_high - crt_low
        crt_close = closes[-2]
        
        sweep_high = highs[-1]
        sweep_low = lows[-1]
        sweep_close = closes[-1]
        
        # CRT candle precisa ser grande (range > 1.3x média)
        if crt_range < avg_range * 1.3:
            return None
        
        # Determinar direção da vela CRT
        crt_bullish = crt_close > (crt_low + crt_range * 0.5)
        crt_bearish = crt_close < (crt_low + crt_range * 0.5)
        
        # ═══ SWEEP DE BAIXA (reversão altista) ═══
        # CRT é bearish → sweep varre o low da CRT → fecha dentro
        if crt_bearish:
            if sweep_low < crt_low and sweep_close > crt_low:
                sl_price = crt_low - (crt_range * 0.2)  # SL 20% abaixo do range
                return {
                    'bias': 'BUY',
                    'crt_high': crt_high, 'crt_low': crt_low,
                    'sweep_high': sweep_high, 'sweep_low': sweep_low,
                    'sweep_close': sweep_close,
                    'sl_price': sl_price,
                }
        
        # ═══ SWEEP DE ALTA (reversão baixista) ═══
        # CRT é bullish → sweep varre o high da CRT → fecha dentro
        if crt_bullish:
            if sweep_high > crt_high and sweep_close < crt_high:
                sl_price = crt_high + (crt_range * 0.2)  # SL 20% acima do range
                return {
                    'bias': 'SELL',
                    'crt_high': crt_high, 'crt_low': crt_low,
                    'sweep_high': sweep_high, 'sweep_low': sweep_low,
                    'sweep_close': sweep_close,
                    'sl_price': sl_price,
                }
        
        return None
    
    except:
        return None


def find_fvg_in_range(highs, lows, closes, pip_size, bias, range_low, range_high, is_metal=False):
    """
    Busca FVGs DENTRO do range da vela de sweep no M15.
    Retorna lista de FVGs ordenados por gap (maior primeiro).
    """
    n = len(closes)
    if n < 10:
        return []
    
    min_gap = 100 if is_metal else 1.0
    found = []
    
    for i in range(6, n - 1):
        entry_price = closes[i]
        
        # FVG precisa estar dentro do range do sweep
        if entry_price < range_low or entry_price > range_high:
            continue
        
        if bias == 'BUY':
            if lows[i] > highs[i-2]:
                gap = (lows[i] - highs[i-2]) / pip_size
                if gap >= min_gap:
                    sl_pips = abs(entry_price - range_low) / pip_size
                    found.append({
                        'direction': 'BUY',
                        'entry': closes[i],
                        'gap': gap,
                        'sl_pips': max(sl_pips, 10 if not is_metal else 200),
                        'index': i,
                    })
        else:  # SELL
            if highs[i] < lows[i-2]:
                gap = (lows[i-2] - highs[i]) / pip_size
                if gap >= min_gap:
                    sl_pips = abs(range_high - entry_price) / pip_size
                    found.append({
                        'direction': 'SELL',
                        'entry': closes[i],
                        'gap': gap,
                        'sl_pips': max(sl_pips, 10 if not is_metal else 200),
                        'index': i,
                    })
    
    # Ordenar por gap (maior primeiro)
    found.sort(key=lambda x: x['gap'], reverse=True)
    return found

STATE_FILE = Path.home() / '.hermes' / 'forex' / 'real_daily_state.json'
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

# ══════════════════════════════════════════
# UTILITÁRIOS
# ══════════════════════════════════════════

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {'balance': INITIAL_BALANCE, 'trades_today': 0, 'trade_log': [],
            'pnl_today': 0.0, 'last_trade_time': None}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))

def get_mt5_balance():
    try:
        status = mt5_get_status()
        if status and 'balance' in status:
            return float(status['balance'])
    except:
        pass
    return None

# ══════════════════════════════════════════
# EXECUÇÃO
# ══════════════════════════════════════════

def calculate_sl_tp(direction, entry, sl_pips, rr, pip_size, is_metal=False):
    """Calcula SL e TP baseado no gap/range."""
    if direction == 'BUY':
        sl = entry - sl_pips * pip_size
        tp = entry + sl_pips * rr * pip_size
    else:
        sl = entry + sl_pips * pip_size
        tp = entry - sl_pips * rr * pip_size
    # Metais (XAUUSD) precisam de precisão 2 decimais; forex 5
    decimals = 2 if is_metal else 5
    return round(sl, decimals), round(tp, decimals)

def execute_trade(pair, signal, strategy_name, pip_size, rr, balance=None):
    """Executa ordem no MT5 com volume dinâmico. Suporta CRT (crt_sl/crt_tp1)."""
    is_metal = 'XAU' in pair.upper() or 'GOLD' in pair.upper()
    
    # ═══ CRT: usar SL técnico se disponível ═══
    crt_sl = signal.get('crt_sl')
    
    if crt_sl is not None:
        sl = crt_sl
        sl_pips = abs(signal['entry'] - sl) / pip_size
        sl = round(sl, 2 if is_metal else 5)
        tp = calculate_sl_tp(signal['direction'], signal['entry'], sl_pips, rr, pip_size, is_metal)[1]
    else:
        # Fallback: cálculo padrão por sl_pips
        MIN_SL = 200 if is_metal else 10
        MAX_SL = 300 if is_metal else 20
        
        sl_pips_raw = signal.get('sl_pips', 0) or 0
        if sl_pips_raw <= 0:
            print(f"   ⛔ REJEITADO: SL={sl_pips_raw} — sem stop loss definido")
            return {'status': 'rejected', 'reason': 'SL=0'}
        
        sl_pips = max(MIN_SL, min(sl_pips_raw, MAX_SL))
        
        if sl_pips != sl_pips_raw:
            print(f"   🔧 SL ajustado: {sl_pips_raw:.1f} → {sl_pips:.1f} ({'ticks' if is_metal else 'pips'})")
        
        sl, tp = calculate_sl_tp(signal['direction'], signal['entry'], sl_pips, rr, pip_size, is_metal)
    
    # Volume dinâmico (recalculado com SL validado)
    if balance is None:
        balance = get_mt5_balance() or INITIAL_BALANCE
    volume, risk_pct = calculate_volume(balance, sl_pips, pair.replace('/','').replace('_KZ',''))
    
    symbol = pair.replace('/', '').replace('-', '').replace('_KZ', '')
    # Mapear símbolo do Yahoo → MT5
    if 'XAUUSD' in symbol:
        mt5_symbol = 'XAUUSD'
    elif symbol.endswith('JPY'):
        mt5_symbol = symbol  # USDJPY, GBPJPY, EURJPY
    else:
        mt5_symbol = symbol  # EURUSD, GBPUSD, USDCAD
    
    entry_fmt = 2 if is_metal else 5
    decimals = 2 if is_metal else 5
    print(f"\n📊 [{strategy_name}] {pair} {signal['direction']}")
    tp1_pips = sl_pips  # 1:1
    if signal['direction'] == 'BUY':
        tp1 = round(signal['entry'] + tp1_pips * pip_size, decimals)
    else:
        tp1 = round(signal['entry'] - tp1_pips * pip_size, decimals)
    
    print(f"   Entry: {signal['entry']:.{entry_fmt}f} | SL: {sl:.{entry_fmt}f} | TP1: {tp1:.{entry_fmt}f} (1:1) | TP2: {tp:.{entry_fmt}f} (3:1)")
    print(f"   Gap: {signal['gap']:.1f}p | SL pips: {signal['sl_pips']:.1f} | RR: 1:{rr}")
    
    # ═══ PARCIAL: 2 ordens (50% @1:1 + 50% @3:1) ═══
    half_vol = max(0.01, round(volume / 2, 2))
    if volume < 0.02:
        half_vol = volume  # Sem split se lote < 0.02
        use_partial = False
    else:
        use_partial = True
    
    print(f"   Vol: {volume:.2f} lot ({half_vol:.2f}×{'2' if use_partial else '1'}) | Risco: {risk_pct:.0f}% = ${balance*risk_pct/100:.2f}")
    
    def _send_one(vol, sl_price, tp_price, tag):
        """Envia 1 ordem para MT5."""
        try:
            r = send_order(mt5_symbol, signal['direction'], vol, sl_price, tp_price, comment=f'Hermes_{tag}')
            is_ok = r and (r.get('status') == 'ok' or r.get('retcode') == 10009 or r.get('ticket'))
            if is_ok:
                ticket = str(r.get('ticket') or r.get('order', ''))
                print(f"   ✅ {tag}: ticket={ticket} vol={vol}")
                return ticket, sl_price, tp_price
            return None, sl_price, tp_price
        except:
            try:
                from mt5_direct import place_order
                r = place_order(mt5_symbol, signal['direction'], vol, sl_price, tp_price)
                ticket = str(r.get('ticket', ''))
                print(f"   🔄 {tag} fallback: ticket={ticket}")
                return ticket, sl_price, tp_price
            except Exception as e:
                print(f"   ❌ {tag} falhou: {e}")
                return None, sl_price, tp_price
    
    tickets = []
    if use_partial:
        # Ordem 1: 50% @ TP1 (1:1) — mesmo SL
        t1, sl1, tp1_out = _send_one(half_vol, sl, tp1, f'{strategy_name}_TP1')
        if t1: tickets.append({'ticket': t1, 'sl': sl1, 'tp': tp1_out, 'tag': 'TP1', 'vol': half_vol})
        
        # Ordem 2: 50% @ TP2 (3:1) — mesmo SL
        t2, sl2, tp2_out = _send_one(half_vol, sl, tp, f'{strategy_name}_TP2')
        if t2: tickets.append({'ticket': t2, 'sl': sl2, 'tp': tp2_out, 'tag': 'TP2', 'vol': half_vol})
    else:
        # Lote pequeno — 1 ordem @ 3:1
        t1, sl1, tp1_out = _send_one(volume, sl, tp, strategy_name)
        if t1: tickets.append({'ticket': t1, 'sl': sl1, 'tp': tp1_out, 'tag': 'FULL', 'vol': volume})
    
    if not tickets:
        return {'status': 'failed', 'reason': 'Nenhuma ordem enviada'}
    
    # Salvar no open_trades.json para monitor
    for tk in tickets:
        _save_open_trade(tk['ticket'], mt5_symbol, signal['direction'],
                        signal['entry'], tk['sl'], tk['tp'], sl_pips, tk['vol'])
    
    # Notificar abertura
    mode = signal.get('mode', '24h')
    os.system(f"python3 {Path.home()}/.hermes/scripts/trade_notifier.py open "
             f"'{pair}' '{signal['direction']}' {signal['entry']:.5f} {sl:.5f} {tp:.5f} "
             f"'{strategy_name}' '{mode}' &")
    
    return {
        'status': 'executed',
        'tickets': tickets,
        'partial': use_partial,
        'tp1': tp1 if use_partial else None,
        'entry': signal['entry'],
        'sl': sl
    }

# ══════════════════════════════════════════
# OPEN TRADES TRACKING (2R/3R monitor)
# ══════════════════════════════════════════
OPEN_TRADES_FILE = Path.home() / '.hermes' / 'forex' / 'open_trades.json'

def _save_open_trade(ticket, symbol, direction, entry, sl, tp, sl_pips, volume):
    """Salva trade aberto para o monitor 2R/3R."""
    pip_val = PIP_VALUES.get(symbol, 0.10)
    lot_mult = volume / 0.01  # quantos 0.01 lots
    risk_dollar = sl_pips * lot_mult * pip_val
    
    trade = {
        'pair': symbol,
        'direction': direction,
        'entry': entry,
        'sl_initial': sl,
        'tp': tp,
        'sl_pips': sl_pips,
        'volume': volume,
        'risk_dollar': round(risk_dollar, 2),
        'time': datetime.now().isoformat(),
    }
    
    trades = {}
    if OPEN_TRADES_FILE.exists():
        try:
            trades = json.loads(OPEN_TRADES_FILE.read_text())
        except:
            pass
    
    trades[ticket] = trade
    OPEN_TRADES_FILE.write_text(json.dumps(trades, indent=2, default=str))


# ══════════════════════════════════════════
# DETECÇÃO M1: FVG + direção H1 ( Roberto 29/05)
# ══════════════════════════════════════════

def detect_fvg_m1(opens, highs, lows, closes, pip_size, h1_bias, is_metal=False):
    """FVG no M1 filtrado pela direção H1. SL curto (gap do M1)."""
    n = len(closes)
    if n < 10:
        return []
    
    min_sl = MIN_SL_METAL if is_metal else MIN_SL_PIPS
    min_gap = max(1.0, 100 if is_metal else 0)  # Ouro: mínimo $1.00 gap
    
    signals = []
    for i in range(8, n - 1):
        # Bullish FVG: low[i] > high[i-2]
        if lows[i] > highs[i-2]:
            gap = (lows[i] - highs[i-2]) / pip_size
            if gap >= (min_gap if is_metal else 1.0):
                if h1_bias == 'BUY':  # Só compra se H1 bullish
                    sl_pips = max(gap * 1.2, min_sl)  # Gap + 20% buffer
                    signals.append({
                        'direction': 'BUY',
                        'entry': closes[i],
                        'gap': gap,
                        'sl_pips': sl_pips,
                        'index': i,
                    })
        
        # Bearish FVG: high[i] < low[i-2]
        if highs[i] < lows[i-2]:
            gap = (lows[i-2] - highs[i]) / pip_size
            if gap >= (min_gap if is_metal else 1.0):
                if h1_bias == 'SELL':  # Só vende se H1 bearish
                    sl_pips = max(gap * 1.2, min_sl)
                    signals.append({
                        'direction': 'SELL',
                        'entry': closes[i],
                        'gap': gap,
                        'sl_pips': sl_pips,
                        'index': i,
                    })
    
    return signals


# ══════════════════════════════════════════
# MAIN LOOP
# ══════════════════════════════════════════

def main():
    print(f"Bot {datetime.now().strftime('%H:%M')} | ", end='')
    
    state = load_state()
    balance = get_mt5_balance() or state.get('balance', INITIAL_BALANCE)
    
    # ═══ CARREGAR WEIGHTS DINÂMICOS (N. Accumbens) ═══
    weights_file = Path.home() / '.hermes' / 'forex' / 'pair_weights_live.json'
    if weights_file.exists():
        try:
            live_weights = json.loads(weights_file.read_text())
            for pair_name in BASE_PAIRS:
                base = pair_name.replace('_KZ', '')
                if base in live_weights:
                    live_wr = live_weights[base].get('wr', 0)
                    if live_wr > 0:
                        old_wr = BASE_PAIRS[pair_name]['wr']
                        BASE_PAIRS[pair_name]['wr'] = round(
                            old_wr * 0.3 + live_wr * 0.7, 1)  # 70% live, 30% backtest
        except:
            pass  # Silencioso — usa backtest WR se falhar
    
    # ═══ SCAN ═══
    all_signals = []
    
    # ═══ KILLZONE UNIVERSAL GATING (NEO Rec #2) ═══
    utc_hour = datetime.utcnow().hour
    for start_h, end_h in DEAD_ZONES_UTC:
        if start_h <= utc_hour <= end_h:
            print(f"⛔ ZONA MORTA (UTC {utc_hour}h) — WR 0-37%. Nenhum trade.")
            return
    
    # ═══ CIRCUIT BREAKER (NEO Rec #3) ═══
    # Daily start balance — salvo em JSON, resetado a cada novo dia
    daily_state_file = Path.home() / '.hermes' / 'forex' / 'daily_state.json'
    today_str = datetime.now().strftime('%Y-%m-%d')
    daily_start = balance  # default
    if daily_state_file.exists():
        try:
            ds = json.loads(daily_state_file.read_text())
            if ds.get('date') == today_str:
                daily_start = ds.get('start_balance', balance)
        except:
            pass
    # Se novo dia ou arquivo não existe, salvar
    if not daily_state_file.exists() or json.loads(daily_state_file.read_text()).get('date') != today_str:
        daily_state_file.write_text(json.dumps({'date': today_str, 'start_balance': balance}))
        daily_start = balance
    
    if balance < daily_start * (1 - DAILY_STOP_PERCENT / 100):
        print(f"🛑 DAILY STOP: ${balance:.2f} ({(balance/daily_start-1)*100:.1f}%). BOT HALTED.")
        return
    
    # Verificar drawdown
    if balance < daily_start * (1 - DRAWDOWN_ALERT_PERCENT / 100):
        print(f"⚠️ DRAWDOWN ALERT: ${balance:.2f} ({(balance/daily_start-1)*100:.1f}%)")
    
    # Verificar limite diário de trades
    today = datetime.now().strftime('%Y-%m-%d')
    trades_hoje = 0
    if TRADE_LOG_FILE.exists():
        tlog_data = json.loads(TRADE_LOG_FILE.read_text())
        # FIX: bot_multi salva 'time', não 'timestamp'. Verificar ambos.
        trades_hoje = sum(1 for t in tlog_data.get('trades', []) 
                          if str(t.get('timestamp', t.get('time', ''))).startswith(today))
    if trades_hoje >= MAX_DAILY_TRADES:
        print(f"⛔ Limite diário atingido ({trades_hoje}/{MAX_DAILY_TRADES} trades). Parando.")
        return
    
    # Verificar posições abertas no MT5
    open_positions = 0
    open_symbols = set()
    try:
        status = mt5_get_status()
        open_positions = status.get('positions', 0) if status else 0
        # Coletar símbolos já abertos pra evitar duplicação
        for p in status.get('positions_data', []) if status else []:
            sym = p.get('symbol', '')
            if sym:
                open_symbols.add(sym)
    except:
        open_positions = len(state.get('trade_log', []))
    
    if open_positions >= MAX_POSITIONS:
        print(f"⛔ Máx posições atingido ({open_positions}/{MAX_POSITIONS}). Pulando scan.")
        return
    
    # Comandos do usuário
    cmds = read_user_commands()
    if isinstance(cmds, dict) and cmds.get("pause"):
        print("⏸️ Bot pausado por comando do usuário.")
        return
    
    # ═══ CARREGAR VIÉS SEMANAL ═══
    WEEKLY_BIAS = {}
    weekly_path = Path.home() / '.hermes' / 'forex' / 'weekly_analysis.json'
    if weekly_path.exists():
        try:
            with open(weekly_path) as f:
                weekly = json.load(f)
            for s in weekly.get('selected_pairs', []):
                WEEKLY_BIAS[s['pair']] = s['direction']
            if WEEKLY_BIAS:
                print(f"Viés semanal ({weekly.get('date','?')}):", 
                      ', '.join(f"{p} {d}" for p,d in WEEKLY_BIAS.items()))
        except:
            pass
    
    # ═══ SCAN: Multi-TF Bias + CRT filter → M1 FVG → RR 3:1 (29/05) ═══
    all_signals = []
    
    for pair_name, pair_cfg in BASE_PAIRS.items():
        sym = pair_cfg['sym']
        pip = pair_cfg['pip']
        
        # ═══ GATE 0: Viés semanal ═══
        if WEEKLY_BIAS:
            # Só opera pares da análise semanal
            if pair_name not in WEEKLY_BIAS:
                continue
            weekly_direction = WEEKLY_BIAS[pair_name]
        
        kz = pair_cfg.get('killzone')
        if kz is not None:
            if datetime.utcnow().hour not in kz:
                continue
        
        base_pair = pair_name.replace('_KZ', '')
        if not should_trade_pair(base_pair):
            continue
        
        is_metal = pair_cfg.get('metal', False)
        
        try:
            # ═══ PASSO 1: Multi-TF Bias ═══
            bias, tf_details = get_multi_tf_bias(sym)
            if bias == 'NEUTRAL':
                continue
            
            # ═══ PASSO 1.5: CRT filter (confirmação extra) ═══
            crt = detect_crt_setup(sym, pip)
            crt_aligned = False
            if crt and crt['bias'] == bias:
                crt_aligned = True  # CRT confirma o bias → sinal forte
            
            # ═══ PASSO 2: Entrada M1 com FVG ═══
            df_m1 = fetch_ohlcv(sym, period='5d', interval='1m')
            if df_m1 is None or len(df_m1) < 30:
                continue
            
            m1_opens = df_m1['Open'].astype(float).values
            m1_highs = df_m1['High'].astype(float).values
            m1_lows = df_m1['Low'].astype(float).values
            m1_closes = df_m1['Close'].astype(float).values
            
            m1_signals = detect_fvg_m1(m1_opens, m1_highs, m1_lows, m1_closes, 
                                       pip, bias, is_metal)
            
            # ═══ MULTI-AGENTE: Perfil + Sessão + Estrutura + Padrão ═══
            if MULTI_AGENT is None:
                continue
            
            decision, conf, ag_signal = MULTI_AGENT.analyze(
                base_pair, m1_highs, m1_lows, m1_closes, bias, pip, is_metal)
            
            if decision == 'NEUTRAL' or ag_signal is None:
                continue
            
            # ═══ GATE 0: Viés semanal — só opera na direção da semana ═══
            if WEEKLY_BIAS and pair_name in WEEKLY_BIAS:
                if decision != WEEKLY_BIAS[pair_name]:
                    continue  # direção contrária ao viés semanal
            
            # SL baseado no ATR do M1
            atr_pips = 2.0
            if len(m1_closes) >= 15:
                h=m1_highs[-15:]; l=m1_lows[-15:]; c=m1_closes[-15:]
                tr=np.maximum(h-l,np.maximum(abs(h-np.roll(c,1)),abs(l-np.roll(c,1))))
                tr[0]=h[0]-l[0]; atr_pips=np.mean(tr[-14:])/pip if len(tr)>=14 else np.mean(tr)/pip
            
            sl_pips = max(MIN_SL_PIPS, min(atr_pips*2.0, 30 if not is_metal else 300))
            
            # Label
            confirmed=[f'{k}={v}' for k,v in tf_details.items() if '✓' in str(v)]
            sep='|'
            bias_label=f'MA({conf:.0f}%) DB={bias}[{sep.join(confirmed)}]'
            
            all_signals.append(dict(
                direction=decision, entry=ag_signal['entry'], gap=ag_signal.get('gap',0),
                sl_pips=round(sl_pips,1), index=ag_signal.get('idx',0),
                pair=base_pair, strategy='MULTI_AGENT',
                strategy_name=f'MA {bias_label}',
                pip=pip, rf=3.0, mode='KZ' if kz else '24h',
                crt_aligned=False, crt_sl=None
            ))
        
        except Exception as e:
            print(f"  {pair_name}: ERRO - {e}")
            continue
    
    # ═══ SELECIONAR MELHORES SINAIS ═══
    if not all_signals:
        print("📭 Nenhum sinal encontrado.")
        return
    
    pass  # silent
    for s in all_signals:
        pass  # silent
    
    # Filtrar: priorizar maior gap + WR do par
    all_signals.sort(key=lambda s: s['gap'] * BASE_PAIRS[s['pair']]['wr'] / 100, reverse=True)
    
    # Limitar por MAX_POSITIONS
    slots = MAX_POSITIONS - open_positions
    selected = all_signals[:slots]
    
    # Evitar pares com mesma moeda BASE simultâneos (INCLUI posições já abertas)
    # GBP e XAU correlacionados (libra tem lastro em ouro)
    correlated_groups = {
        'USD':    ['USDJPY', 'USDCAD'],
        'EUR':    ['EURUSD', 'EURJPY'],
        'GBP_XAU': ['GBPUSD', 'GBPJPY', 'XAUUSD'],
    }
    
    # Mapear símbolo → grupo
    symbol_to_group = {}
    for group, symbols in correlated_groups.items():
        for s in symbols:
            symbol_to_group[s] = group
    
    # Contar posições existentes por grupo
    group_open = {g: 0 for g in correlated_groups}
    for p in (status.get('positions_data', []) if status else []):
        sym = p.get('symbol', '')
        g = symbol_to_group.get(sym)
        if g:
            group_open[g] += 1
    
    executed_pairs = set()
    final_trades = []
    
    for s in selected:
        if s['pair'] in executed_pairs:
            continue
        
        # ═══ ANTI-DUPLICATA: Pular par que já tem posição aberta no MT5 ═══
        pair_symbol = s['pair'].replace('/', '')  # GBP/JPY → GBPJPY
        if pair_symbol in open_symbols or s['pair'].replace('_KZ', '').replace('/', '') in open_symbols:
            continue
        
        # Verificar grupo de moeda base
        g = symbol_to_group.get(s['pair'])
        if g:
            # Contar existentes + já selecionados neste lote
            count = group_open[g] + sum(1 for ep in executed_pairs 
                                        if symbol_to_group.get(ep) == g)
            if count >= MAX_CORRELATED_PAIRS:
                continue  # Já tem par nesta moeda base
        
        result = execute_trade(s['pair'], s, s['strategy_name'], s['pip'], s['rf'], balance)
        final_trades.append({**s, 'result': result})
        executed_pairs.add(s['pair'])
    
    # ═══ ATUALIZAR ESTADO ═══
    if final_trades:
        state['trades_today'] = state.get('trades_today', 0) + len(final_trades)
        state['last_trade_time'] = datetime.now().isoformat()
        
        for t in final_trades:
            if t['result']['status'] in ('executed', 'executed_fallback'):
                entry = t['result'].get('entry', 0)
                sl = t['signal'].get('sl_price', 0)
                tp = t['signal'].get('tp_price', 0)
                notify_open(t['pair'], t['signal']['direction'], entry, sl, tp, t.get('volume', 0))
                state.setdefault("trade_log", []).append({
                    'pair': t['pair'],
                    'strategy': t['strategy_name'],
                    'direction': t['direction'],
                    'entry': t['entry'],
                    'sl': t['result'].get('sl'),
                    'tp': t['result'].get('tp'),
                    'time': datetime.now().isoformat(),
                    'status': 'open',
                })
                # Sincronizar com trade_log.json (N. Accumbens lê daqui)
                try:
                    record_trade(t['direction'], t['pair'], t['entry'],
                                t['result'].get('sl'), t['result'].get('tp'), 
                                volume=VOLUME)
                except Exception:
                    pass  # Silencioso — trade_log é secundário ao state
        
        save_state(state)
        print(f"\n✅ {len(final_trades)} ordens enviadas. Trades hoje: {state['trades_today']}")
    else:
        print(" 0 ordens", end="")

if __name__ == '__main__':
    main()
