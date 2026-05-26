#!/usr/bin/env python3
"""
Hermes Trading Bot — FVG ICT M15 V5 + Macro + Weekly Bias (IC MARKETS DEMO).
Atualizado: 25/05/2026 — parâmetros V5 com descobertas do cérebro (knowledge bridge).

ESTRATÉGIA V5 (25/05):
- FVG ICT M15, RR 3:1, filtros CRT + S/R Levels + gap≥5 + horários UTC
- VIÉS SEMANAL integrado (weekly_bias.json via Knowledge Bridge)
- VALIDAÇÃO MACRO: Iran deal/Fed/UMich sentiment scoring
- ALERTA VOLATILIDADE: gap médio tracking (FVG trend monitor)
- Backtest V5 (25/05): gap≥5 + horas[6,7,15,16] + CRT filter
  - CHoCH+FVG puro: 9 trades, 66.7% WR, +33.8p (30d M15)
  - CHoCH+FVG+CRT: 3 trades, 100% WR, +24.2p (CRT reduz -66% trades, zera perdas)
  - 10-trade SMC M5: GBPUSD London 49%WR/+89p, GBPUSD NY 44%WR/+86p
  - USDJPY: 73.3% WR | GBPUSD: 65.5% WR | EURUSD: 56.2% WR

CÉREBRO 25/05 — DESCOBERTAS INTEGRADAS:
- VIÉS SEMANAL 26-30 MAY: USDJPY BUY (Iran deal → risk-on carry), EURUSD NEUTRAL,
  GBPUSD BUY. Macro: Iran nuclear deal + Fed Warsh + UMich 44.8 bearish USD.
  Segunda-feira = feriado (no_trade_monday). Trading começa terça 27/05.
- FVG DATA: EURUSD 113 FVGs (gap médio 3.3p), GBPUSD 135 FVGs (gap médio 3.5p),
  USDJPY 57 FVGs (gap médio 2.3p), AUDUSD 186 FVGs (gap médio 2.9p).
  Dados repetidos (stale) — mercado fechado domingo. Atualiza na abertura.
- 3-LAYER DIRECTION: Order Flow (delta divergence + CVD), Market Structure (SMT divergence),
  Timing (Killzones + Time Cycles). Implementado como macro_score.
- CHART PATTERNS: 3454 padrões detectados em 7 pares (confirmam atividade do mercado).
- NOVAS FONTES (24/05): ICT Breaker/Turtle Soup/Mitigation, Order Flow delta divergence,
  CVD, SMT divergence. Adicionados aos filtros de validação.

CORRETORA: IC Markets Demo (MT5 display:0, execução via ydotool)
CONTA: Demo hedge (Raw Trading Ltd)
"""

from tv_data import fetch_ohlcv
import numpy as np
import json, time, os, sys, urllib.request
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/home/roberto/.hermes/scripts')
from mt5_direct import close_all as mt5_close_all
from hermes_mt5_bridge import send_order, get_status as mt5_get_status
from trade_tracker import record_trade
from brain_bot_bridge import get_weekly_bias, get_macro_context, notify_trade, read_user_commands

# ══════════════════════════════════════════
# CONFIGURAÇÃO IC MARKETS DEMO
# ══════════════════════════════════════════
REAL_ACCOUNT = False              # Demo account (IC Markets)
INITIAL_BALANCE = 10000.0         # Saldo demo padrão
RISK_PERCENT = 1.0                 # % da banca arriscada por trade (demo)
DAILY_STOP_PERCENT = 5.0
DRAWDOWN_ALERT_PERCENT = 3.0

VOLUME = 0.01                      # Microlote fixo
MAX_POSITIONS = 4                  # V5: setups são raros com filtros

# ══════════════════════════════════════════
# PARES V5 (validados 5059 padrões, 30 dias cada)
# ══════════════════════════════════════════
PAIRS = {
    'USD/JPY': {'sym': 'USDJPY=X', 'backtest_wr': 73.3, 'pip': 0.01},    # PRIMÁRIO #1
    'GBP/USD': {'sym': 'GBPUSD=X', 'backtest_wr': 65.5, 'pip': 0.0001},  # Primário #2
    'EUR/USD': {'sym': 'EURUSD=X', 'backtest_wr': 56.2, 'pip': 0.0001},  # Secundário #3
}
# AUD/USD e NZD/USD REMOVIDOS — confirmados inviáveis para FVG (45.7%, 44.3% WR)

# ══════════════════════════════════════════
# ESTRATÉGIA V5
# ══════════════════════════════════════════
MIN_FVG_PIPS = 5.0                 # V5: gap ≥ 5 pips (sobe WR +11pp, validado 25/05)
MIN_ATR_PIPS = 1.0
RR_RATIO = 3.0                     # SL × 3

# Filtros V5
CRT_ENABLED = True
CRT_RANGE_PERCENTILE = 0.8
SR_ENABLED = True
SR_PROXIMITY_PIPS = 5

# Horários V5 — UTC [6, 7, 15, 16] = London open + NY afternoon
TRADING_HOURS_UTC = [6, 7, 15, 16]
TRADING_DAYS = [0, 1, 2, 3, 4]     # Seg-Sex

# Timeout: 3 candles sem tocar o FVG → sair
FVG_TIMEOUT_CANDLES = 3

# Dedup: 1 trade por par+direção por dia
DEDUP_PER_DAY = True

# V5: Validação Macro (cérebro 25/05)
MACRO_VALIDATION_ENABLED = True     # Validar sinal contra contexto macro
MACRO_MIN_SCORE = 0.3               # Score macro mínimo para executar (0-1)

# ══════════════════════════════════════════
# EXECUÇÃO DE ORDENS — BRIDGE MQL5
# ══════════════════════════════════════════
def place_choch_order(pair, direction, entry_price, fvg_pips, atr_pips):
    """Envia ordem via bridge MQL5 (hermes_bridge EA).
    pair: 'EUR/USD' -> 'EURUSD'
    Calcula SL/TP com RR 3:1 baseado no FVG gap.
    """
    # Converter formato do par
    symbol = pair.replace('/', '')
    
    # SL = FVG gap em pips convertido para preco
    pip_val = PAIRS.get(pair, {}).get('pip', 0.0001)
    sl_distance = fvg_pips * pip_val
    tp_distance = fvg_pips * RR_RATIO * pip_val
    
    if direction == 'BUY':
        sl = round(entry_price - sl_distance, 5)
        tp = round(entry_price + tp_distance, 5)
    else:
        sl = round(entry_price + sl_distance, 5)
        tp = round(entry_price - tp_distance, 5)
    
    result = send_order(symbol, direction, VOLUME, sl, tp, timeout=10)
    
    if result.get('status') == 'ok':
        return {'sl': sl, 'tp': tp, 'ticket': result.get('ticket')}
    else:
        raise RuntimeError(f"OrderSend failed: {result.get('msg', 'unknown')} (retcode={result.get('retcode')})")

FOREX_DIR = Path.home() / '.hermes' / 'forex'
TRADE_LOG_PATH = str(FOREX_DIR / 'trade_log.json')
STATE_FILE = str(FOREX_DIR / 'real_state.json')
DAILY_STATE_FILE = str(FOREX_DIR / 'real_daily_state.json')
WEEKLY_BIAS_FILE = str(FOREX_DIR / 'weekly_bias.json')

# ══════════════════════════════════════════
# VIÉS SEMANAL (atualizado via Knowledge Bridge)
# ══════════════════════════════════════════
def load_weekly_bias():
    """Carrega viés semanal: 1) Brain Gateway (tempo real) 2) Arquivo JSON (cache)"""
    # 1. Tentar brain gateway (fonte primária, tempo real)
    try:
        bias_dict = get_weekly_bias()
        if bias_dict:
            return {'pairs': bias_dict, 'source': 'brain_gateway'}
    except:
        pass
    
    # 2. Fallback: arquivo JSON local
    try:
        if os.path.exists(WEEKLY_BIAS_FILE):
            with open(WEEKLY_BIAS_FILE) as f:
                bias = json.load(f)
            bias_date = datetime.fromisoformat(bias.get('week_start', '2000-01-01'))
            now = datetime.now()
            if (now - bias_date).days <= 7:
                return bias
    except:
        pass
    return None

def apply_bias(signal, bias):
    """Aplica viés semanal ao score do sinal. +10% aligned, -20% contra."""
    if not bias:
        return signal['score']
    pair_bias = bias.get('pairs', {}).get(signal['pair'], 'NEUTRAL')
    direction = signal['direction']
    if pair_bias == direction:
        return signal['score'] * 1.10
    elif pair_bias == ('SELL' if direction == 'BUY' else 'BUY'):
        return signal['score'] * 0.80
    return signal['score']


def macro_validation_score(signal, bias):
    """
    V5: Validação macro de 3 camadas (cérebro 25/05).
    Camada 1: Viés semanal (40%) — alinhamento com bias macro
    Camada 2: Catalisadores (35%) — Iran deal, Fed, dados econômicos
    Camada 3: Timing (25%) — hora UTC vs killzone ideal
    Retorna score 0-1 e motivo.
    """
    if not MACRO_VALIDATION_ENABLED:
        return 1.0, "macro disabled"
    
    score = 0.0
    reasons = []
    pair = signal['pair']
    direction = signal['direction']
    
    # Camada 1: Viés semanal (40%)
    if bias:
        pair_bias = bias.get('pairs', {}).get(pair, 'NEUTRAL')
        if pair_bias == direction:
            score += 0.40
            reasons.append(f"aligned bias {pair_bias}")
        elif pair_bias == 'NEUTRAL':
            score += 0.20
            reasons.append("neutral bias")
        else:
            # Contra viés — penaliza mas não zera
            score += 0.05
            reasons.append(f"CONTRA bias ({pair_bias})")
    
    # Camada 2: Catalisadores macro (35%)
    macro_drivers = bias.get('macro_drivers', []) if bias else []
    summary = bias.get('summary', '').lower() if bias else ''
    
    # Iran deal → risk-on → bullish for carry (USDJPY BUY, commodities UP)
    if 'iran' in summary or 'risk-on' in summary:
        if pair == 'USD/JPY' and direction == 'BUY':
            score += 0.35
            reasons.append("iran risk-on → JPY weak")
        elif pair in ('GBP/USD', 'EUR/USD') and direction == 'BUY':
            score += 0.20
            reasons.append("risk-on supports GBP/EUR")
        elif pair in ('GBP/USD', 'EUR/USD') and direction == 'SELL':
            score += 0.05
            reasons.append("risk-on CONTRÁRIO a SELL")
        else:
            score += 0.15
    
    # Fed hawkish → USD strength → BUY USD pairs, SELL others
    if 'fed' in summary or 'hawkish' in summary:
        if pair == 'USD/JPY' and direction == 'BUY':
            score += 0.10
            reasons.append("Fed hawkish → USD strong")
        elif pair in ('GBP/USD', 'EUR/USD') and direction == 'SELL':
            score += 0.10
            reasons.append("Fed hawkish → USD strong")
    
    # UMich sentiment miss → bearish USD
    if 'umich' in summary or 'bearish usd' in summary:
        if pair == 'USD/JPY' and direction == 'SELL':
            score += 0.10
            reasons.append("UMich miss → USD weak")
        elif pair in ('GBP/USD', 'EUR/USD') and direction == 'BUY':
            score += 0.10
            reasons.append("UMich miss → USD weak")
    
    # Camada 3: Timing / Killzone (25%)
    from datetime import datetime
    hour_utc = datetime.utcnow().hour
    if hour_utc in [6, 7]:  # London open
        score += 0.25
        reasons.append("London killzone")
    elif hour_utc in [15, 16]:  # NY afternoon
        score += 0.20
        reasons.append("NY killzone")
    else:
        score += 0.05
        reasons.append("fora killzone")
    
    return min(1.0, score), " | ".join(reasons)


def check_fvg_volatility_trend(pair):
    """
    V5: Monitora tendência de volatilidade dos FVGs (cérebro 25/05).
    Se gap médio está subindo, volatilidade aumenta → setups mais confiáveis.
    Se gap médio está caindo, mercado pode estar comprimindo → cuidado.
    """
    fvg_trend_file = FOREX_DIR / 'fvg_trend.json'
    try:
        if fvg_trend_file.exists():
            trend_data = json.loads(fvg_trend_file.read_text())
            pair_key = pair.replace('/', '')
            if pair_key in trend_data:
                return trend_data[pair_key]
    except:
        pass
    return None

# Telegram chat ID (mesmo configurado nos cron jobs)
TELEGRAM_CHAT_ID = "845735429"

# ══════════════════════════════════════════
# TELEGRAM ALERT
# ══════════════════════════════════════════
def send_telegram(msg):
    """Envia alerta via Telegram (usa gateway local do Hermes)."""
    try:
        # Usa o endpoint local do Hermes Agent para enviar mensagem
        webhook_url = "http://localhost:11434/telegram/send"
        payload = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "HTML"
        }).encode()
        req = urllib.request.Request(webhook_url, data=payload,
                                     headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        # Fallback: log para arquivo
        alert_log = FOREX_DIR / 'alerts.log'
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(alert_log, 'a') as f:
            f.write(f"[{ts}] {msg}\n")

# ══════════════════════════════════════════
# INDICADORES
# ══════════════════════════════════════════
def atr(candles, period=14):
    trs = []
    for i in range(1, len(candles)):
        h = float(candles.iloc[i]['High'])
        l = float(candles.iloc[i]['Low'])
        pc = float(candles.iloc[i-1]['Close'])
        trs.append(max(h-l, abs(h-pc), abs(l-pc)))
    n = min(period, len(trs))
    return sum(trs[-n:]) / n if trs else 0

def is_crt_candle(df, idx):
    if idx < 20: return False
    rng = abs(float(df.iloc[idx]['High']) - float(df.iloc[idx]['Low']))
    recent = [abs(float(df.iloc[i]['High']) - float(df.iloc[i]['Low'])) for i in range(idx-19, idx+1)]
    threshold = sorted(recent)[int(len(recent) * CRT_RANGE_PERCENTILE)]
    return rng >= threshold

def crt_confirmation(df, idx):
    if idx + 1 >= len(df): return False
    h1 = float(df.iloc[idx]['High'])
    l1 = float(df.iloc[idx]['Low'])
    c2 = float(df.iloc[idx+1]['Close'])
    return l1 <= c2 <= h1

def detect_choch_fvg(df, pip_val):
    df30 = df.iloc[-30:]
    base_idx = len(df) - 30

    highs = df30['High'].values.astype(float)
    lows = df30['Low'].values.astype(float)
    closes = df30['Close'].values.astype(float)

    sh, sl = [], []
    for i in range(2, len(highs)-2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            sh.append((i, highs[i]))
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            sl.append((i, lows[i]))

    signals = []

    if sh:
        last_sh_idx, last_sh_val = sh[-1]
        for i in range(last_sh_idx+1, len(closes)):
            if closes[i] > last_sh_val:
                for j in range(max(0,i-4), i-1):
                    if j+2 < len(highs) and highs[j] < lows[j+2]:
                        gap = (lows[j+2] - highs[j]) / pip_val
                        if gap >= MIN_FVG_PIPS:
                            entry = round(float(df30.iloc[j+2]['Low']), 5)
                            signals.append({'type': 'BUY', 'entry': entry, 'fvg_pips': gap, 'idx': base_idx + i})

    if sl:
        last_sl_idx, last_sl_val = sl[-1]
        for i in range(last_sl_idx+1, len(closes)):
            if closes[i] < last_sl_val:
                for j in range(max(0,i-4), i-1):
                    if j+2 < len(highs) and lows[j] > highs[j+2]:
                        gap = (lows[j] - highs[j+2]) / pip_val
                        if gap >= MIN_FVG_PIPS:
                            entry = round(float(df30.iloc[j+2]['High']), 5)
                            signals.append({'type': 'SELL', 'entry': entry, 'fvg_pips': gap, 'idx': base_idx + i})

    return signals

def near_sr_level(df, entry_price, direction, pip_val):
    h = df['High'].values.astype(float)[-100:]
    l = df['Low'].values.astype(float)[-100:]

    sh_vals, sl_vals = [], []
    for i in range(2, len(h)-2):
        if h[i]>h[i-1] and h[i]>h[i-2] and h[i]>h[i+1] and h[i]>h[i+2]: sh_vals.append(h[i])
        if l[i]<l[i-1] and l[i]<l[i-2] and l[i]<l[i+1] and l[i]<l[i+2]: sl_vals.append(l[i])

    threshold = SR_PROXIMITY_PIPS * pip_val

    if direction == 'BUY':
        for v in sl_vals[-5:]:
            if abs(entry_price - v) < threshold: return True
        if len(sh_vals) >= 2:
            for v in sh_vals[-5:-1]:
                if abs(entry_price - v) < threshold: return True
    else:
        for v in sh_vals[-5:]:
            if abs(entry_price - v) < threshold: return True
        if len(sl_vals) >= 2:
            for v in sl_vals[-5:-1]:
                if abs(entry_price - v) < threshold: return True
    return False

# ══════════════════════════════════════════
# GESTÃO DE RISCO (NOVO)
# ══════════════════════════════════════════
def get_balance():
    """Lê saldo do arquivo de estado diário ou retorna saldo inicial."""
    try:
        if os.path.exists(DAILY_STATE_FILE):
            ds = json.loads(open(DAILY_STATE_FILE).read())
            return ds.get('balance', INITIAL_BALANCE)
    except:
        pass
    return INITIAL_BALANCE

def update_balance(new_balance, pnl_today):
    """Atualiza saldo no arquivo de estado diário."""
    ds = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'balance': round(new_balance, 2),
        'pnl_today': round(pnl_today, 2),
        'updated': datetime.now().isoformat()
    }
    try:
        open(DAILY_STATE_FILE, 'w').write(json.dumps(ds, indent=2))
    except:
        pass

def get_real_wr(pair=None, min_trades=3):
    """Calcula WR real da conta. Se pair=None, retorna WR agregado de todos os pares."""
    try:
        if os.path.exists(TRADE_LOG_PATH):
            log = json.loads(open(TRADE_LOG_PATH).read())
            if pair:
                closed = [t for t in log.get('trades', [])
                          if t.get('status') == 'closed' and t.get('pair') == pair and t.get('pnl') is not None]
            else:
                closed = [t for t in log.get('trades', [])
                          if t.get('status') == 'closed' and t.get('pnl') is not None]
            if len(closed) < min_trades:
                return None, len(closed)
            wins = [t for t in closed if t.get('result') == 'WIN']
            wr = len(wins) / len(closed) * 100
            return round(wr, 1), len(closed)
    except:
        pass
    return None, 0

def should_trade_pair(pair):
    """Decide se deve operar um par baseado no WR real + agregado."""
    real_wr, n = get_real_wr(pair, min_trades=3)
    overall_wr, overall_n = get_real_wr(min_trades=10)
    
    # Se par tem 3+ trades E WR < 40% → BLOQUEAR
    if real_wr is not None and real_wr < 40:
        return False, real_wr, f"WR={real_wr}% ({n}t) < 40%"
    
    # Se par tem 2+ trades E WR ≥ 80% → PERMITIR mesmo com agregado ruim
    elite_wr, elite_n = get_real_wr(pair, min_trades=2)
    if elite_wr is not None and elite_wr >= 80:
        return True, elite_wr, f"WR={elite_wr}% ({elite_n}t) — exceção elite"
    
    # Se agregado tem 10+ trades E WR < 35% → BLOQUEAR pares com WR < 50%
    if overall_wr is not None and overall_wr < 35:
        if real_wr is None or real_wr < 50:
            return False, real_wr, f"WR agregado={overall_wr}% ({overall_n}t) — só pares com WR≥50%"
    
    # Se tem menos de 3 trades reais → PERMITIR (backtest_wr como referência)
    if real_wr is None:
        return True, None, f"insuficiente ({n}/3 trades) — usando backtest"
    
    return True, real_wr, f"WR={real_wr}% ({n}t)"

def check_daily_stop():
    """Verifica se atingiu stop diário (-5%). Retorna True se deve parar."""
    try:
        if os.path.exists(DAILY_STATE_FILE):
            ds = json.loads(open(DAILY_STATE_FILE).read())
            today = datetime.now().strftime('%Y-%m-%d')
            if ds.get('date') == today:
                pnl = ds.get('pnl_today', 0)
                balance = ds.get('balance', INITIAL_BALANCE)
                pnl_pct = (pnl / INITIAL_BALANCE) * 100
                if pnl_pct <= -DAILY_STOP_PERCENT:
                    return True, pnl, balance
                # Alerta de drawdown (não para, só avisa)
                if pnl_pct <= -DRAWDOWN_ALERT_PERCENT:
                    send_telegram(
                        f"⚠️ <b>ALERTA DRAWDOWN</b>\n"
                        f"P&L diário: <b>${pnl:.2f}</b> ({pnl_pct:.1f}%)\n"
                        f"Saldo: ${balance:.2f}\n"
                        f"Stop diário: -{DAILY_STOP_PERCENT}%"
                    )
    except:
        pass
    return False, 0, INITIAL_BALANCE

def calculate_max_risk_sl(balance, pip_val, volume=0.01):
    """Calcula SL máximo em pips baseado no risco % da banca."""
    risk_amount = balance * (RISK_PERCENT / 100.0)
    # volume 0.01 ≈ $0.10/pip para maioria dos pares
    # Para pares com JPY, pip_val = 0.01
    pip_dollar = volume * 100000 * pip_val  # ~$0.10 para EUR/USD etc
    max_sl_pips = risk_amount / pip_dollar
    return round(max_sl_pips, 1)

# ══════════════════════════════════════════
# MONITORAMENTO DE POSIÇÕES
# ══════════════════════════════════════════
def check_positions(now):
    """Verifica SL/TP dos trades abertos e atualiza P&L."""
    if not os.path.exists(STATE_FILE):
        return

    try:
        state = json.loads(open(STATE_FILE).read())
        active = state.get('active_trades', [])
    except:
        return

    if not active:
        return

    closed = []
    still_active = []

    for t in active:
        pair = t['pair']
        direction = t['direction']
        entry = t['entry']
        sl = t['sl']
        tp = t['tp']

        try:
            cfg = PAIRS.get(pair)
            if not cfg:
                still_active.append(t)
                continue

            ticker = fetch_ohlcv(cfg['sym'], period='1d', interval='5m')
            df = ticker
            if len(df) < 1:
                still_active.append(t)
                continue

            current = float(df.iloc[-1]['Close'])

            hit_tp = False
            hit_sl = False

            if direction == 'BUY':
                hit_tp = current >= tp
                hit_sl = current <= sl
            else:
                hit_tp = current <= tp
                hit_sl = current >= sl

            if hit_tp or hit_sl:
                pip_v = cfg['pip']
                if direction == 'BUY':
                    pnl_pips = (current - entry) / pip_v
                else:
                    pnl_pips = (entry - current) / pip_v

                pnl_pips = round(pnl_pips, 1)
                result = 'WIN' if pnl_pips > 0 else 'LOSS'

                # Atualizar trade_log
                try:
                    log = json.loads(open(TRADE_LOG_PATH).read())
                    for lt in log.get('trades', []):
                        if lt.get('id') == t.get('tid') and lt['status'] == 'open':
                            lt['status'] = 'closed'
                            lt['exit_price'] = round(current, 5)
                            lt['pnl'] = pnl_pips
                            lt['closed_at'] = now.isoformat()
                            lt['result'] = result
                            break
                    open(TRADE_LOG_PATH, 'w').write(json.dumps(log, indent=2))
                except:
                    pass

                closed.append({**t, 'pnl': pnl_pips, 'result': result, 'exit': current})
            else:
                still_active.append(t)

        except Exception:
            still_active.append(t)

    # Atualizar estado
    state['active_trades'] = still_active
    if closed:
        state.setdefault('history', [])
        state['history'].extend(closed)
    state['updated'] = now.isoformat()

    try:
        open(STATE_FILE, 'w').write(json.dumps(state, indent=2))
    except:
        pass

    # Atualizar P&L diário com trades fechados
    if closed:
        today_pnl = sum(c['pnl'] for c in closed)
        update_daily_pnl(today_pnl)

        for c in closed:
            print(f"[P&L] {c['pair']} {c['direction']} {c['result']} {c['pnl']:+}p @ {c['exit']:.5f}")

def update_daily_pnl(pnl_change):
    """Atualiza P&L diário acumulado."""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        if os.path.exists(DAILY_STATE_FILE):
            ds = json.loads(open(DAILY_STATE_FILE).read())
            if ds.get('date') != today:
                ds = {'date': today, 'balance': get_balance(), 'pnl_today': 0}
        else:
            ds = {'date': today, 'balance': get_balance(), 'pnl_today': 0}

        ds['pnl_today'] = round(ds.get('pnl_today', 0) + pnl_change, 2)
        ds['balance'] = round(ds.get('balance', INITIAL_BALANCE) + pnl_change, 2)
        ds['updated'] = datetime.now().isoformat()
        open(DAILY_STATE_FILE, 'w').write(json.dumps(ds, indent=2))
    except:
        pass

# ══════════════════════════════════════════
# LÓGICA PRINCIPAL
# ══════════════════════════════════════════
def should_trade():
    """Verifica condições de trading incluindo stop diário."""
    now = datetime.now()

    # Verificar stop diário
    stopped, pnl, balance = check_daily_stop()
    if stopped:
        print(f"[STOP] Daily stop atingido: P&L=${pnl:.2f}, Balance=${balance:.2f}")
        send_telegram(
            f"🛑 <b>STOP DIÁRIO ATINGIDO</b>\n"
            f"P&L diário: <b>${pnl:.2f}</b> (limite: -{DAILY_STOP_PERCENT}%)\n"
            f"Saldo: ${balance:.2f}\n"
            f"Bot pausado até próximo dia útil."
        )
        return False, "stop diário"

    if now.weekday() not in TRADING_DAYS:
        return False, "fim de semana"

    # Verificar feriados (weekly_bias.json)
    try:
        bias_path = Path.home() / '.hermes' / 'forex' / 'weekly_bias.json'
        if bias_path.exists():
            bias = json.loads(bias_path.read_text())
            if now.weekday() == 0 and bias.get('no_trade_monday'):
                return False, "segunda-feira feriado (weekly_bias)"
    except:
        pass

    # Sexta: não abrir novas posições após 14h
    if now.weekday() == 4 and now.hour >= 14:
        return False, "sexta pós 14h — só fecha"

    return True, "ok"

def count_active_positions():
    """Conta posições abertas atualmente."""
    try:
        if os.path.exists(STATE_FILE):
            state = json.loads(open(STATE_FILE).read())
            return len(state.get('active_trades', []))
    except:
        pass
    return 0

def run_analysis():
    """Análise completa e execução de ordens (conta real)."""
    now = datetime.now()
    
    # ── V5: Verificar comandos do Brain Gateway ──
    try:
        commands = read_user_commands()
        for cmd in commands:
            if cmd['action'] == 'pause':
                print("[BRAIN] ⏸️ Comando PAUSE recebido — pausando bot")
                return
            elif cmd['action'] == 'close_all':
                print("[BRAIN] 🔒 Comando CLOSE ALL recebido")
                mt5_close_all()
            elif cmd['action'] == 'status':
                print("[BRAIN] 📊 Comando STATUS recebido")
                # Notificar status via brain
                balance = get_balance()
                active = count_active_positions()
                notify_trade({'type': 'status', 'balance': balance, 'active_positions': active})
    except Exception as e:
        pass  # Brain gateway offline não bloqueia o bot
    
    # ── P&L: Verificar trades abertos (SL/TP) ──
    check_positions(now)

    # ── Verificar stop diário ──
    can_trade, reason = should_trade()
    if not can_trade:
        if reason == "stop diário":
            return  # Stop diário — não faz nada
        # Fim de semana / sexta tarde — ainda verifica posições mas não abre novas
        return

    # ── Verificar limite de posições ──
    active_count = count_active_positions()
    if active_count >= MAX_POSITIONS:
        print(f"[LIMIT] {active_count}/{MAX_POSITIONS} posições ativas — sem novas entradas")
        return

    signals_found = []

    # Verificar trades já executados hoje (dedup)
    traded_today = []
    try:
        if os.path.exists(TRADE_LOG_PATH):
            raw = open(TRADE_LOG_PATH).read().strip()
            if raw:
                trade_log = json.loads(raw)
                today = now.strftime('%Y-%m-%d')
                traded_today = [t['pair'] + t['direction'] for t in trade_log.get('trades', [])
                               if t['timestamp'].startswith(today) and t.get('status') != 'duplicate']
    except:
        pass

    # ── Análise de sinais ──
    for pair, cfg in PAIRS.items():
        try:
            ticker = fetch_ohlcv(cfg['sym'], period='5d', interval='15m')
            df = ticker
            if len(df) < 20:
                continue

            current = float(df.iloc[-1]['Close'])
            a = atr(df)
            atr_pips = round(a / cfg['pip'], 1)

            if atr_pips < MIN_ATR_PIPS:
                continue

            signals = detect_choch_fvg(df, cfg['pip'])

            if signals:
                buy_sigs = [s for s in signals if s['type'] == 'BUY']
                sell_sigs = [s for s in signals if s['type'] == 'SELL']

                for sig_list, direction in [(buy_sigs, 'BUY'), (sell_sigs, 'SELL')]:
                    if sig_list:
                        best = None
                        if CRT_ENABLED:
                            for s in reversed(sig_list):
                                if is_crt_candle(df, s['idx']) and crt_confirmation(df, s['idx']):
                                    best = s
                                    break
                        if best is None:
                            best = sig_list[-1]

                        trade_key = pair + direction
                        if trade_key in traded_today:
                            continue

                        if CRT_ENABLED:
                            idx = best['idx']
                            if not is_crt_candle(df, idx):
                                continue
                            if not crt_confirmation(df, idx):
                                continue

                        # ── VERIFICAÇÃO WR REAL ──
                        allowed, real_wr, wr_reason = should_trade_pair(pair)
                        if not allowed:
                            print(f"[WR] {pair}: {wr_reason} — pulando")
                            continue
                        # WR para decisão: usa real_wr se disponível, senão backtest
                        elite_wr, _ = get_real_wr(pair, min_trades=2)
                        decision_wr = real_wr if real_wr is not None else (elite_wr if elite_wr is not None else cfg['backtest_wr'])

                        if SR_ENABLED:
                            if not near_sr_level(df, best['entry'], direction, cfg['pip']):
                                continue

                        # ── VERIFICAÇÃO DE RISCO (NOVO) ──
                        balance = get_balance()
                        max_sl_pips = calculate_max_risk_sl(balance, cfg['pip'])
                        # O SL do FVG é tipicamente 1-5 pips, bem dentro do limite
                        # Mas verificamos por segurança
                        if best['fvg_pips'] > max_sl_pips:
                            print(f"[RISK] {pair} {direction} SL={best['fvg_pips']:.1f}p > max={max_sl_pips:.1f}p — pulando")
                            continue

                        score = decision_wr
                        active_count = count_active_positions()
                        remaining = MAX_POSITIONS - active_count

                        signals_found.append({
                            'pair': pair,
                            'direction': direction,
                            'entry': best['entry'],
                            'fvg_pips': best['fvg_pips'],
                            'atr_pips': atr_pips,
                            'wr': decision_wr,
                            'real_wr': real_wr,
                            'score': score,
                            'remaining_slots': remaining
                        })
        except Exception:
            pass

    # ── Executar sinais (limitado a MAX_POSITIONS) ──
    if signals_found:
        # Aplicar viés semanal
        weekly_bias = load_weekly_bias()
        if weekly_bias:
            print(f"[BIAS] Viés semanal carregado: {weekly_bias.get('summary', 'N/A')}")
            for sig in signals_found:
                sig['score'] = apply_bias(sig, weekly_bias)
        
        # V5: Validação macro (3 camadas)
        if MACRO_VALIDATION_ENABLED and weekly_bias:
            validated = []
            for sig in signals_found:
                macro_score, macro_reason = macro_validation_score(sig, weekly_bias)
                sig['macro_score'] = round(macro_score, 2)
                sig['macro_reason'] = macro_reason
                if macro_score >= MACRO_MIN_SCORE:
                    # Ajusta score final: 70% WR/bias + 30% macro
                    sig['score'] = sig['score'] * 0.70 + macro_score * 30  # macro carry weight
                    validated.append(sig)
                else:
                    print(f"[MACRO] {sig['pair']} {sig['direction']} REJEITADO (macro={macro_score:.2f}): {macro_reason}")
            signals_found = validated
        
        signals_found.sort(key=lambda s: (s['score'], s['wr']), reverse=True)

        executed = []
        state = {'active_trades': [], 'last_balance': None, 'updated': now.isoformat()}

        # Carregar estado anterior
        prev_state = {}
        try:
            if os.path.exists(STATE_FILE):
                prev_state = json.loads(open(STATE_FILE).read())
                state['active_trades'] = prev_state.get('active_trades', [])
        except:
            pass

        slots_available = MAX_POSITIONS - len(state['active_trades'])

        for sig in signals_found[:slots_available]:
            result = place_choch_order(sig['pair'], sig['direction'],
                                     sig['entry'], sig['fvg_pips'], sig['atr_pips'])
            tid = record_trade(sig['direction'], sig['pair'], sig['entry'],
                        result['sl'], result['tp'])
            executed.append({
                'pair': sig['pair'],
                'dir': sig['direction'],
                'wr': sig['wr'],
                'entry': sig['entry'],
                'sl': result['sl'],
                'tp': result['tp'],
                'tid': tid
            })
            state['active_trades'].append({
                'tid': tid,
                'pair': sig['pair'],
                'direction': sig['direction'],
                'entry': sig['entry'],
                'sl': result['sl'],
                'tp': result['tp'],
                'date': now.strftime('%Y-%m-%d'),
                'opened': now.isoformat(),
                'volume': VOLUME
            })
            time.sleep(2)

        # ── V5: Notificar cérebro sobre trades executados ──
        for e in executed:
            try:
                notify_trade({
                    'type': 'trade_opened',
                    'pair': e['pair'],
                    'direction': e['dir'],
                    'entry': e['entry'],
                    'sl': e['sl'],
                    'tp': e['tp'],
                    'wr': e['wr'],
                    'tid': e['tid']
                })
            except:
                pass

        # Salvar estado
        try:
            open(STATE_FILE, 'w').write(json.dumps(state, indent=2))
        except:
            pass

        # Saída e alerta Telegram
        if executed:
            active_total = len(state['active_trades'])
            balance = get_balance()
            lines = [f"⚡ <b>{len(executed)} trade(s) executado(s)</b> — Conta REAL"]
            lines.append(f"💰 Saldo: ${balance:.2f} | Posições: {active_total}/{MAX_POSITIONS}")
            for e in executed:
                lines.append(f"  • {e['pair']} {e['dir']} WR={e['wr']}% @ {e['entry']:.5f}")
                print(f"  {e['pair']} {e['dir']} WR={e['wr']}%")

            # Telegram: notificar novas posições
            send_telegram("\n".join(lines))
        else:
            print("Nenhum slot disponível para novos trades")

if __name__ == '__main__':
    run_analysis()
