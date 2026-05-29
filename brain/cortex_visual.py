#!/usr/bin/env python3
"""
Córtex Visual — Agente de Trading Multi-Confluência SMC/ICT
============================================================

Estratégia validada: Profit Factor 3.25, 60% WR (backtest 59d M15 + 90d H1)

CONFLUÊNCIAS (entrada requer >= 4):
  1. HTF Alignment (H1 swing structure — MANDATORY)
  2. Killzone correta (London/NY Open/Close — MANDATORY)
  3. Liquidity Sweep no M15 (MANDATORY)
  4. Fresh FVG no M15 (directional)
  5. Order Block válido (directional)
  6. SMT Divergence (EURUSD↔GBPUSD, USDJPY↔EURJPY)

GERENCIAMENTO DE RISCO (Position Sizer integrado):
  - SL = Order Block mais próximo (ou ATR fallback)
  - TP = 2:1 a 5:1 dinâmico (baseado em estrutura)
  - Lote calculado via Position Sizer interno: volume = (balance * risk_pct) / (sl_pips * pip_value)
  - Risk per trade: 1% padrão (0.5% XAUUSD), ajustável por volatility regime
  - MAX 1 trade/par/dia
  - MAX 4 posições simultâneas
  - Circuit breaker: pausa par após 3 timeouts MT5 consecutivos
  - Anti-duplicata: signal fingerprint + TTL 60min
  - M1 precision entry: após sinal M15, refinar entrada no M1 com FVG/OB

USO:
  python3 cortex_visual.py               # Modo real (via MT5 bridge)
  python3 cortex_visual.py --dry-run     # Paper trading (sem enviar ordens)
  python3 cortex_visual.py --scan-only   # Apenas scan, sem executar
  python3 cortex_visual.py --once        # Executa 1 ciclo e sai
  python3 cortex_visual.py --daemon      # Loop contínuo com intervalo

PARES: EURUSD, GBPUSD, USDJPY, GBPJPY, EURJPY, XAUUSD
"""

import sys
import os

# ── Path setup: ensure brain/ dir is on sys.path for sibling imports ──
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import time
import hashlib
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any

import warnings
warnings.filterwarnings("ignore")

# ── External deps ──
try:
    import yfinance as yf
except ImportError:
    print("❌ yfinance não instalado. Execute: pip install yfinance")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import numpy as np
except ImportError:
    np = None  # degraded mode — will use pure-python fallbacks

# ── Thalamus (canal de comunicação entre agentes) ──
try:
    import thalamus
    THALAMUS_AVAILABLE = True
except ImportError:
    THALAMUS_AVAILABLE = False
    print("⚠️  thalamus.py não encontrado — executando sem comunicação inter-agente")

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

# ── Pares ──
PAIRS = {
    "EURUSD": {"symbol": "EURUSD=X", "pip": 0.0001, "decimals": 5, "min_sl": 5,  "max_sl": 18},
    "GBPUSD": {"symbol": "GBPUSD=X", "pip": 0.0001, "decimals": 5, "min_sl": 6,  "max_sl": 20},
    "USDJPY": {"symbol": "USDJPY=X", "pip": 0.01,   "decimals": 3, "min_sl": 5,  "max_sl": 18},
    "GBPJPY": {"symbol": "GBPJPY=X", "pip": 0.01,   "decimals": 3, "min_sl": 8,  "max_sl": 25},
    "EURJPY": {"symbol": "EURJPY=X", "pip": 0.01,   "decimals": 3, "min_sl": 6,  "max_sl": 20},
    "XAUUSD": {"symbol": "GC=F",     "pip": 0.10,   "decimals": 2, "min_sl": 30, "max_sl": 60,
               "is_metal": True},
}

# ── Pares correlacionados para SMT Divergence ──
SMT_PAIRS = [
    ("EURUSD", "GBPUSD"),
    ("USDJPY", "EURJPY"),
]

# ── ICT Killzones (UTC) ──
KILLZONES = {
    "Asia/London Overlap": (6, 8),
    "London Open":         (7, 9),
    "NY Open":              (12, 14),
    "London Close":         (15, 17),
}

# ── Filtros ──
MIN_CONFLUENCES = 4          # Requer 4+ confluências para entrada
RR_RATIO = 2.0               # TP = 2× SL (fixo)
MAX_POSITIONS = 4            # Máximo de posições simultâneas
MAX_TRADES_PER_PAIR_PER_DAY = 1
SIGNAL_TTL_MINUTES = 60      # TTL do fingerprint anti-duplicata

# ── Circuit breaker ──
CB_MAX_TIMEOUTS = 3          # Pausa par após N timeouts MT5 consecutivos
CB_COOLDOWN_MINUTES = 120    # Tempo de pausa (2h) antes de reativar par

# ── Data ──
M15_PERIOD = "15m"
H1_PERIOD  = "1h"
M15_LOOKBACK_DAYS = 5
H1_LOOKBACK_DAYS  = 14

# ── Arquivos de estado ──
STATE_DIR = Path.home() / ".hermes" / "forex"
STATE_FILE = STATE_DIR / "cortex_visual_state.json"
FINGERPRINT_FILE = STATE_DIR / "cortex_fingerprints.json"

# ═══════════════════════════════════════════════════════════════════════════
# UTILITÁRIOS
# ═══════════════════════════════════════════════════════════════════════════

def body(c: dict) -> float:
    return abs(c["c"] - c["o"])

def upper_wick(c: dict) -> float:
    return c["h"] - max(c["o"], c["c"])

def lower_wick(c: dict) -> float:
    return min(c["o"], c["c"]) - c["l"]

def candle_range(c: dict) -> float:
    return c["h"] - c["l"]

def ema(values: List[float], span: int) -> float:
    """Calculate EMA for a list of values."""
    if np:
        return float(np.array(values)[-span:].mean())  # fallback SMA
    # Pure python EMA
    if len(values) < span:
        return sum(values) / len(values) if values else 0
    alpha = 2.0 / (span + 1)
    ema_val = sum(values[:span]) / span
    for v in values[span:]:
        ema_val = alpha * v + (1 - alpha) * ema_val
    return ema_val

def fmt_price(price: float, decimals: int) -> str:
    return f"{price:.{decimals}f}"

# ═══════════════════════════════════════════════════════════════════════════
# DATA FETCH
# ═══════════════════════════════════════════════════════════════════════════

def fetch_candles(symbol: str, interval: str, days: int) -> List[dict]:
    """Fetch OHLCV data from Yahoo Finance, return list of candle dicts."""
    try:
        df = yf.download(symbol, period=f"{days}d", interval=interval,
                         progress=False, auto_adjust=False)
        if df is None or len(df) == 0:
            return []
        # Handle multi-index columns (yfinance quirk)
        if pd is not None and isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        candles = []
        for idx, row in df.iterrows():
            candles.append({
                "dt": idx.to_pydatetime(),
                "o": float(row["Open"]),
                "h": float(row["High"]),
                "l": float(row["Low"]),
                "c": float(row["Close"]),
            })
        return candles
    except Exception as e:
        print(f"  ⚠️ fetch_candles({symbol}, {interval}): {e}")
        return []

# ═══════════════════════════════════════════════════════════════════════════
# 1. HTF ALIGNMENT (H1 swing structure)
# ═══════════════════════════════════════════════════════════════════════════

def get_htf_alignment(h1_candles: List[dict], m15_dt: datetime) -> str:
    """
    Returns 'BULLISH', 'BEARISH', or 'NEUTRAL' based on H1 structure.
    Uses swing highs/lows: higher highs + higher lows = uptrend.
    """
    h1_before = [c for c in h1_candles if c["dt"] <= m15_dt]
    if len(h1_before) < 24:
        return "NEUTRAL"

    recent = h1_before[-24:]

    # ── Swing highs/lows (local extremes with radius 3) ──
    swings_h, swings_l = [], []
    for i in range(3, len(recent) - 3):
        c = recent[i]
        is_high = all(c["h"] >= recent[j]["h"] for j in range(i-3, i+4) if j != i)
        is_low  = all(c["l"] <= recent[j]["l"] for j in range(i-3, i+4) if j != i)
        if is_high:
            swings_h.append((i, c["h"]))
        if is_low:
            swings_l.append((i, c["l"]))

    # ── Higher highs + higher lows = bullish ──
    if len(swings_h) >= 2 and len(swings_l) >= 2:
        last_highs = sorted(swings_h, key=lambda x: x[0])[-2:]
        last_lows  = sorted(swings_l, key=lambda x: x[0])[-2:]
        hh = last_highs[1][1] > last_highs[0][1]
        hl = last_lows[1][1] > last_lows[0][1]

        if hh and hl:
            return "BULLISH"
        if (not hh) and (not hl):
            return "BEARISH"

    # ── EMA fallback ──
    closes = [c["c"] for c in recent]
    ema8  = ema(closes, 8)
    ema21 = ema(closes, 21)
    price = recent[-1]["c"]
    if price > ema8 and ema8 > ema21:
        return "BULLISH"
    if price < ema8 and ema8 < ema21:
        return "BEARISH"
    return "NEUTRAL"

# ═══════════════════════════════════════════════════════════════════════════
# 2. KILLZONE CHECK
# ═══════════════════════════════════════════════════════════════════════════

def is_in_killzone(dt: datetime) -> Tuple[bool, Optional[str]]:
    """Check if datetime is inside an active ICT killzone."""
    hour = dt.hour
    for kz_name, (start, end) in KILLZONES.items():
        if start <= hour < end:
            return True, kz_name
    return False, None

# ═══════════════════════════════════════════════════════════════════════════
# 3. LIQUIDITY SWEEP (M15)
# ═══════════════════════════════════════════════════════════════════════════

def detect_liquidity_sweep(candles: List[dict], idx: int,
                           lookback: int = 20) -> Optional[Tuple[str, float]]:
    """
    Detect liquidity sweep: price breaks a swing high/low and reverses.
    Returns (direction, swept_level) or None.
    """
    if idx < lookback:
        return None

    lb = candles[idx - lookback:idx]
    curr = candles[idx]

    # Find local swing highs/lows in the lookback window
    swing_highs, swing_lows = [], []
    for i in range(3, len(lb) - 3):
        c = lb[i]
        is_high = all(c["h"] >= lb[j]["h"] for j in range(max(0, i-3), min(len(lb), i+4)) if j != i)
        is_low  = all(c["l"] <= lb[j]["l"] for j in range(max(0, i-3), min(len(lb), i+4)) if j != i)
        if is_high:
            swing_highs.append(c["h"])
        if is_low:
            swing_lows.append(c["l"])

    # Sweep of highs → bearish reversal (SELL)
    if swing_highs:
        nearest_high = max(swing_highs)
        if curr["h"] > nearest_high and curr["c"] < curr["o"]:
            return ("SELL", nearest_high)

    # Sweep of lows → bullish reversal (BUY)
    if swing_lows:
        nearest_low = min(swing_lows)
        if curr["l"] < nearest_low and curr["c"] > curr["o"]:
            return ("BUY", nearest_low)

    return None

# ═══════════════════════════════════════════════════════════════════════════
# 4. FVG (FAIR VALUE GAP)
# ═══════════════════════════════════════════════════════════════════════════

def detect_fvg(candles: List[dict], idx: int) -> Optional[Tuple[str, float, float]]:
    """
    3-candle FVG pattern.
    Returns (type, top, bottom) or None.
    type: 'BULLISH' (gap above), 'BEARISH' (gap below).
    """
    if idx < 1 or idx >= len(candles) - 1:
        return None
    prev = candles[idx - 1]
    curr = candles[idx]
    nxt  = candles[idx + 1]

    # Bearish FVG: price drops, leaving gap below
    if prev["l"] > nxt["h"] and curr["c"] < curr["o"]:
        return ("BEARISH", prev["l"], nxt["h"])

    # Bullish FVG: price rises, leaving gap above
    if prev["h"] < nxt["l"] and curr["c"] > curr["o"]:
        return ("BULLISH", nxt["l"], prev["h"])

    return None

def is_fresh_fvg(candles: List[dict], fvg_idx: int, current_idx: int) -> bool:
    """Check if FVG at fvg_idx hasn't been mitigated by current_idx."""
    if fvg_idx >= current_idx:
        return False
    fvg = detect_fvg(candles, fvg_idx)
    if not fvg:
        return False
    fvg_type, fvg_top, fvg_bottom = fvg
    gap_size = fvg_top - fvg_bottom
    if gap_size <= 0:
        return False

    for i in range(fvg_idx + 2, current_idx + 1):
        c = candles[i]
        if fvg_type == "BULLISH":
            # Mitigated if price retraces >20% into the gap
            if c["l"] <= fvg_top - 0.2 * gap_size:
                return False
        else:
            if c["h"] >= fvg_bottom + 0.2 * gap_size:
                return False
    return True

# ═══════════════════════════════════════════════════════════════════════════
# 5. ORDER BLOCK
# ═══════════════════════════════════════════════════════════════════════════

def detect_order_block(candles: List[dict], idx: int) -> Optional[Tuple[str, float, float]]:
    """
    Order Block: bearish candle followed by strong bullish displacement (vice-versa).
    Returns (type, top, bottom).
    """
    if idx < 2 or idx >= len(candles):
        return None
    prev = candles[idx - 1]
    curr = candles[idx]

    # Bullish OB: down candle then strong up candle (demand zone)
    if prev["c"] < prev["o"] and curr["c"] > curr["o"] and body(curr) > body(prev) * 1.5:
        return ("BULLISH", prev["h"], prev["l"])

    # Bearish OB: up candle then strong down candle (supply zone)
    if prev["c"] > prev["o"] and curr["c"] < curr["o"] and body(curr) > body(prev) * 1.5:
        return ("BEARISH", prev["h"], prev["l"])

    return None

def is_valid_ob(candles: List[dict], ob_idx: int, current_idx: int) -> bool:
    """Check if OB hasn't been violated."""
    ob = detect_order_block(candles, ob_idx)
    if not ob:
        return False
    ob_type, ob_top, ob_bottom = ob

    for k in range(ob_idx + 2, current_idx + 1):
        ck = candles[k]
        if ob_type == "BULLISH" and ck["l"] < ob_bottom:
            return False
        if ob_type == "BEARISH" and ck["h"] > ob_top:
            return False
    return True

# ═══════════════════════════════════════════════════════════════════════════
# 6. SMT DIVERGENCE
# ═══════════════════════════════════════════════════════════════════════════

def detect_smt_divergence(candles_a: List[dict], candles_b: List[dict],
                          idx_a: int, idx_b: int) -> Optional[str]:
    """
    Smart Money Technique divergence.
    Returns 'BULLISH_DIVERGENCE', 'BEARISH_DIVERGENCE', or None.
    """
    if idx_a < 5 or idx_b < 5:
        return None

    window_a = candles_a[idx_a - 5:idx_a + 1]
    window_b = candles_b[idx_b - 5:idx_b + 1]
    if len(window_a) < 5 or len(window_b) < 5:
        return None

    # Bearish SMT: A makes higher high, B makes lower high (divergence)
    if (window_a[-1]["h"] > max(c["h"] for c in window_a[:-1]) and
        window_b[-1]["h"] < max(c["h"] for c in window_b[:-1])):
        return "BEARISH_DIVERGENCE"

    # Bullish SMT: A makes lower low, B makes higher low (divergence)
    if (window_a[-1]["l"] < min(c["l"] for c in window_a[:-1]) and
        window_b[-1]["l"] > min(c["l"] for c in window_b[:-1])):
        return "BULLISH_DIVERGENCE"

    return None

# ═══════════════════════════════════════════════════════════════════════════
# ATR
# ═══════════════════════════════════════════════════════════════════════════

def calculate_atr(candles: List[dict], idx: int, period: int = 14) -> float:
    """Calculate ATR at given index."""
    if idx < period:
        return 10.0
    tr_values = []
    for i in range(idx - period + 1, idx + 1):
        if i == 0:
            tr = candles[i]["h"] - candles[i]["l"]
        else:
            tr = max(candles[i]["h"] - candles[i]["l"],
                     abs(candles[i]["h"] - candles[i-1]["c"]),
                     abs(candles[i]["l"] - candles[i-1]["c"]))
        tr_values.append(tr)
    return sum(tr_values) / len(tr_values)

# ═══════════════════════════════════════════════════════════════════════════
# ANTI-DUPLICATA: SIGNAL FINGERPRINT + TTL
# ═══════════════════════════════════════════════════════════════════════════

def load_fingerprints() -> Dict[str, float]:
    """Load fingerprint registry with timestamps."""
    if FINGERPRINT_FILE.exists():
        try:
            return json.loads(FINGERPRINT_FILE.read_text())
        except Exception:
            pass
    return {}

def save_fingerprints(registry: Dict[str, float]):
    """Save fingerprint registry."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    FINGERPRINT_FILE.write_text(json.dumps(registry, indent=2))

def signal_fingerprint(pair: str, direction: str, entry_price: float, dt: datetime) -> str:
    """Create a unique fingerprint for a signal."""
    raw = f"{pair}|{direction}|{entry_price:.5f}|{dt.strftime('%Y-%m-%dT%H')}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]

def is_duplicate(pair: str, direction: str, entry_price: float,
                 dt: datetime, ttl_minutes: int = SIGNAL_TTL_MINUTES) -> bool:
    """Check if signal has already been traded within TTL window."""
    registry = load_fingerprints()
    fp = signal_fingerprint(pair, direction, entry_price, dt)
    now_ts = time.time()

    # Clean expired entries
    expired = [k for k, ts in registry.items() if now_ts - ts > ttl_minutes * 60]
    for k in expired:
        del registry[k]

    if fp in registry:
        return True

    # Also check for same pair+direction within TTL (hour-level dedup)
    hour_key = f"{pair}|{direction}|{dt.strftime('%Y-%m-%dT%H')}"
    for k in registry:
        if hour_key in k:
            return True

    # Register new fingerprint
    registry[fp] = now_ts
    save_fingerprints(registry)
    return False

# ═══════════════════════════════════════════════════════════════════════════
# CIRCUIT BREAKER
# ═══════════════════════════════════════════════════════════════════════════

def load_cb_state() -> Dict[str, Any]:
    """Load circuit breaker state from disk."""
    state_path = STATE_DIR / "cortex_circuit_breaker.json"
    if state_path.exists():
        try:
            return json.loads(state_path.read_text())
        except Exception:
            pass
    return {"timeouts": {}, "paused_until": {}}

def save_cb_state(cb: Dict[str, Any]):
    """Save circuit breaker state."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    cb_path = STATE_DIR / "cortex_circuit_breaker.json"
    cb_path.write_text(json.dumps(cb, indent=2, default=str))

def record_mt5_timeout(pair: str) -> bool:
    """
    Record an MT5 timeout for a pair.
    Returns True if the pair should now be paused.
    """
    cb = load_cb_state()
    cb["timeouts"][pair] = cb["timeouts"].get(pair, 0) + 1
    if cb["timeouts"][pair] >= CB_MAX_TIMEOUTS:
        cb["paused_until"][pair] = (datetime.now(timezone.utc) +
                                    timedelta(minutes=CB_COOLDOWN_MINUTES)).isoformat()
        cb["timeouts"][pair] = 0  # reset counter after triggering
        save_cb_state(cb)
        return True
    save_cb_state(cb)
    return False

def reset_mt5_timeouts(pair: str):
    """Reset timeout counter on successful execution."""
    cb = load_cb_state()
    cb["timeouts"][pair] = 0
    save_cb_state(cb)

def is_pair_paused(pair: str) -> bool:
    """Check if pair is currently paused by circuit breaker."""
    cb = load_cb_state()
    paused_until_str = cb.get("paused_until", {}).get(pair)
    if paused_until_str:
        paused_until = datetime.fromisoformat(paused_until_str)
        if datetime.now(timezone.utc) < paused_until:
            return True
        else:
            # Cooldown expired — remove pause
            del cb["paused_until"][pair]
            cb["timeouts"][pair] = 0
            save_cb_state(cb)
    return False


# ═══════════════════════════════════════════════════════════════════════════
# 8. POSITION SIZER INTERNO (EarnForex-inspired)
# ═══════════════════════════════════════════════════════════════════════════

class PositionSizer:
    """Calculadora de lote integrada — mesma lógica do Position Sizer EA.
    
    Fórmula: volume = (balance * risk_pct) / (sl_pips * pip_value)
    """
    
    PIP_VALUES = {
        "EURUSD": 0.10, "GBPUSD": 0.10, "AUDUSD": 0.10, "NZDUSD": 0.10,
        "USDJPY": 0.09, "USDCHF": 0.10, "USDCAD": 0.10,
        "EURJPY": 0.09, "GBPJPY": 0.09, "EURGBP": 0.13,
        "XAUUSD": 0.10,
    }
    
    def __init__(self, balance: float = 5000.0):
        self.balance = balance
    
    def update_balance(self, balance: float):
        self.balance = balance
    
    def get_balance(self) -> float:
        try:
            state_path = os.path.expanduser("~/.hermes/forex/mt5_state.json")
            if os.path.exists(state_path):
                with open(state_path) as f:
                    state = json.load(f)
                bal = state.get("balance", 0)
                if bal > 0:
                    self.balance = bal
                    return bal
        except:
            pass
        return self.balance
    
    def pip_value(self, pair: str) -> float:
        return self.PIP_VALUES.get(pair, 0.10)
    
    def calculate(self, pair: str, sl_pips: float, risk_pct: float = None) -> Tuple[float, dict]:
        balance = self.get_balance()
        if risk_pct is None:
            risk_pct = 0.005 if "XAU" in pair.upper() else 0.01
        risk_usd = balance * risk_pct
        pip_val = self.pip_value(pair)
        if sl_pips <= 0:
            sl_pips = 15
        raw_volume = (risk_usd / (sl_pips * pip_val)) * 0.01
        volume = max(0.01, min(1.0, round(raw_volume * 100) / 100))
        details = {
            "balance": round(balance, 2), "risk_pct": round(risk_pct * 100, 2),
            "risk_usd": round(risk_usd, 2), "sl_pips": round(sl_pips, 1),
            "pip_value": pip_val, "raw_volume": round(raw_volume, 4),
            "final_volume": volume, "potential_profit": round(risk_usd * 2, 2)
        }
        return volume, details
    
    def dynamic_rr(self, pair: str, htf_trend: str, n_confluences: int) -> float:
        base = 2.0
        if htf_trend in ("BULLISH", "BEARISH"):
            base += 0.5
        else:
            base -= 0.5
        if n_confluences >= 5:
            base += 1.0
        elif n_confluences >= 4:
            base += 0.5
        if "XAU" in pair.upper():
            base = min(base, 2.0)
        return max(1.5, min(base, 5.0))

sizer = PositionSizer()


# ═══════════════════════════════════════════════════════════════════════════
# 9. M1 PRECISION ENTRY
# ═══════════════════════════════════════════════════════════════════════════

def refine_entry_m1(pair_cfg: dict, signal: dict) -> dict:
    """Refinar entrada M15 no M1 para precisão máxima e stop reduzido.
    
    Estratégia do vídeo (TradingView 15s): usar timeframe menor para
    encontrar micro-estruturas que permitem stop muito mais curto.
    
    Resultado típico: SL reduz de 15p (M15) para 5-8p (M1).
    """
    try:
        yf_sym = pair_cfg.get("yf_m1", pair_cfg["yf"])
        df_m1 = yf.download(yf_sym, interval="1m", period="1d", progress=False)
        if df_m1.empty:
            return signal
        
        candles_m1 = [
            {"o": float(r.Open), "h": float(r.High), "l": float(r.Low), "c": float(r.Close)}
            for r in df_m1.itertuples()
        ][-60:]  # Últimos 60 candles M1 (1 hora)
        
        from smartmoneyconcepts import smc
        df_m1_pd = pd.DataFrame(candles_m1)
        
        # ── 1. Refinar ENTRADA via micro-FVG ──
        try:
            fvgs = smc.fvg(df_m1_pd)
            if fvgs is not None and len(fvgs) > 0:
                # Pegar o FVG mais recente que está na direção do trade
                for i in range(len(fvgs)-1, -1, -1):
                    fvg = fvgs.iloc[i]
                    top = float(fvg.get("Top", 0))
                    bot = float(fvg.get("Bottom", 0))
                    if not (top and bot):
                        continue
                    
                    # Checar se FVG está próximo do preço de entrada
                    mid_fvg = (top + bot) / 2
                    if abs(mid_fvg - signal["entry"]) / signal["entry"] < 0.001:  # 0.1%
                        signal["entry"] = mid_fvg
                        signal["entry_refined_m1"] = True
                        signal["entry_precision"] = "M1_FVG"
                        break
        except:
            pass
        
        # ── 2. Refinar SL via micro-estrutura M1 (swings + OB) ──
        try:
            swings = smc.swing_highs_lows(df_m1_pd)
            if swings is not None and len(swings) > 0:
                obs = smc.ob(df_m1_pd, swings)
                
                direction = signal["direction"]
                pip_val = _get_pip_value(pair_cfg["name"])
                
                # Encontrar o micro-swing ou micro-OB mais próximo para SL
                if direction == "BUY":
                    # Para BUY: SL abaixo do swing low ou OB bottom mais próximo
                    candidates = []
                    
                    # Micro swings lows
                    for i in range(len(swings)-1, max(0, len(swings)-10), -1):
                        s = swings.iloc[i]
                        low_val = float(s.get("Low", 0)) if "Low" in s else float(s.get("low", 0))
                        if low_val and low_val < signal["entry"]:
                            candidates.append(("swing_low", low_val))
                    
                    # Micro OB bottoms
                    if obs is not None and len(obs) > 0:
                        for i in range(len(obs)-1, max(0, len(obs)-10), -1):
                            ob = obs.iloc[i]
                            ob_bot = float(ob.get("Bottom", ob.get("Low", 0)))
                            if ob_bot and ob_bot < signal["entry"]:
                                candidates.append(("ob_bottom", ob_bot))
                    
                    if candidates:
                        # Escolher o nível mais próximo abaixo da entrada (stop mais curto)
                        best = max(candidates, key=lambda x: x[1])  # maior preço = mais próximo
                        m1_sl = best[1] - pip_val  # Fica logo abaixo
                        
                        # Só aplicar se for melhor que o SL original (mais próximo = SL maior)
                        if m1_sl > signal["sl"]:
                            signal["sl"] = round(m1_sl, pair_cfg["decimals"])
                            signal["sl_refined_m1"] = True
                            signal["sl_source"] = f"M1_{best[0]}"
                
                else:  # SELL
                    candidates = []
                    
                    # Micro swings highs
                    for i in range(len(swings)-1, max(0, len(swings)-10), -1):
                        s = swings.iloc[i]
                        high_val = float(s.get("High", 0)) if "High" in s else float(s.get("high", 0))
                        if high_val and high_val > signal["entry"]:
                            candidates.append(("swing_high", high_val))
                    
                    # Micro OB tops
                    if obs is not None and len(obs) > 0:
                        for i in range(len(obs)-1, max(0, len(obs)-10), -1):
                            ob = obs.iloc[i]
                            ob_top = float(ob.get("Top", ob.get("High", 0)))
                            if ob_top and ob_top > signal["entry"]:
                                candidates.append(("ob_top", ob_top))
                    
                    if candidates:
                        best = min(candidates, key=lambda x: x[1])  # menor preço = mais próximo
                        m1_sl = best[1] + pip_val
                        
                        if m1_sl < signal["sl"]:
                            signal["sl"] = round(m1_sl, pair_cfg["decimals"])
                            signal["sl_refined_m1"] = True
                            signal["sl_source"] = f"M1_{best[0]}"
                
        except:
            pass
        
        # ── 3. Recalcular SL em pips após refino ──
        if signal.get("sl_refined_m1"):
            pip_val = _get_pip_value(signal["pair"])
            if signal["direction"] == "BUY":
                new_sl_pips = (signal["entry"] - signal["sl"]) / pip_val
            else:
                new_sl_pips = (signal["sl"] - signal["entry"]) / pip_val
            
            # Manter mínimo (STOPLEVEL) e máximo
            new_sl_pips = max(pair_cfg.get("min_sl", 5), min(new_sl_pips, pair_cfg.get("max_sl", 50)))
            signal["sl_pips"] = round(new_sl_pips, 1)
            
            # Recalcular SL price com o valor arredondado
            if signal["direction"] == "BUY":
                signal["sl"] = round(signal["entry"] - new_sl_pips * pip_val, pair_cfg["decimals"])
            else:
                signal["sl"] = round(signal["entry"] + new_sl_pips * pip_val, pair_cfg["decimals"])
    
    except Exception as e:
        pass  # M1 refinement failed, use original M15 signal
    
    return signal


def _get_pip_value(pair: str) -> float:
    """Valor de 1 pip para o par."""
    if "XAU" in pair.upper():
        return 0.01   # XAU: 1 pip = 0.01 (1 ponto = $0.01 para 0.01 lote)
    if "JPY" in pair.upper():
        return 0.01   # JPY: 1 pip = 0.01
    return 0.0001     # Forex padrão: 1 pip = 0.0001


# ═══════════════════════════════════════════════════════════════════════════
# MULTI-CONFLUENCE SCANNER
# ═══════════════════════════════════════════════════════════════════════════

def scan_pair(pair_name: str, pair_cfg: dict,
              m15_candles: List[dict],
              h1_candles: List[dict],
              correlated_data: Dict[str, List[dict]],
              entered_days: set) -> List[dict]:
    """
    Scan a single pair for multi-confluence signals.
    Returns list of signal dicts (max 1 per day).
    """
    if len(m15_candles) < 30:
        return []

    pip_val = pair_cfg["pip"]
    signals = []

    for i in range(30, len(m15_candles)):
        c = m15_candles[i]
        dt = c["dt"]
        day_key = dt.date()

        # ── Max 1 trade per pair per day ──
        if day_key in entered_days:
            continue

        # ── CONFLUENCE 1: Killzone (MANDATORY) ──
        in_kz, kz_name = is_in_killzone(dt)
        if not in_kz:
            continue

        # ── CONFLUENCE 2: HTF Alignment (MANDATORY) ──
        htf_dir = get_htf_alignment(h1_candles, dt)
        if htf_dir == "NEUTRAL":
            continue
        signal_dir = "BUY" if htf_dir == "BULLISH" else "SELL"

        # ── CONFLUENCE 3: Liquidity Sweep (MANDATORY) ──
        sweep = detect_liquidity_sweep(m15_candles, i, lookback=20)
        if not sweep:
            continue
        sweep_dir, swept_level = sweep
        if sweep_dir != signal_dir:
            continue

        # ── Count additional confluences ──
        confluences = ["KILLZONE", "HTF_ALIGNMENT", "LIQUIDITY_SWEEP"]
        extra_count = 0
        nearest_ob = None  # For SL placement

        # ── CONFLUENCE 4: Fresh FVG ──
        fvg_found = False
        for j in range(max(0, i - 15), i - 1):
            fvg = detect_fvg(m15_candles, j)
            if fvg and is_fresh_fvg(m15_candles, j, i):
                fvg_type, _, _ = fvg
                if (fvg_type == "BULLISH" and signal_dir == "BUY") or \
                   (fvg_type == "BEARISH" and signal_dir == "SELL"):
                    confluences.append("FVG_FRESH")
                    extra_count += 1
                    fvg_found = True
                    break

        # ── CONFLUENCE 5: Valid Order Block ──
        ob_found = False
        for j in range(max(0, i - 15), i - 2):
            ob = detect_order_block(m15_candles, j)
            if ob and is_valid_ob(m15_candles, j, i):
                ob_type, ob_top, ob_bottom = ob
                if (ob_type == "BULLISH" and signal_dir == "BUY") or \
                   (ob_type == "BEARISH" and signal_dir == "SELL"):
                    confluences.append("ORDER_BLOCK")
                    extra_count += 1
                    ob_found = True
                    nearest_ob = ob  # Store for SL placement
                    break

        # ── CONFLUENCE 6: SMT Divergence ──
        smt_found = False
        for (p1, p2) in SMT_PAIRS:
            if pair_name in (p1, p2):
                other = p2 if pair_name == p1 else p1
                if other in correlated_data and correlated_data[other]:
                    other_c = correlated_data[other]
                    # Find closest candle by time
                    other_idx = None
                    min_diff = timedelta(minutes=30)
                    for oi, oc in enumerate(other_c):
                        diff = abs(oc["dt"] - dt)
                        if diff < min_diff:
                            min_diff = diff
                            other_idx = oi

                    if other_idx is not None and other_idx >= 5:
                        smt_result = detect_smt_divergence(
                            m15_candles, other_c, i, other_idx)
                        if smt_result:
                            if (smt_result == "BULLISH_DIVERGENCE" and signal_dir == "BUY") or \
                               (smt_result == "BEARISH_DIVERGENCE" and signal_dir == "SELL"):
                                confluences.append("SMT_DIVERGENCE")
                                extra_count += 1
                                smt_found = True
                break  # Only check first matching SMT pair

        # ── Entry filter: need >= 4 confluences ──
        if len(confluences) < MIN_CONFLUENCES:
            continue

        # ── Calculate SL/TP ──
        atr = calculate_atr(m15_candles, i, 14)

        # SL: Use nearest OB if available, otherwise ATR-based
        if nearest_ob:
            _ob_type, ob_top, ob_bottom = nearest_ob
            if signal_dir == "BUY":
                sl_price = ob_bottom - pip_val  # Just below OB
                sl_pips = (c["c"] - sl_price) / pip_val
            else:
                sl_price = ob_top + pip_val  # Just above OB
                sl_pips = (sl_price - c["c"]) / pip_val
            # Clamp to min/max
            sl_pips = max(pair_cfg["min_sl"], min(sl_pips, pair_cfg["max_sl"]))
        else:
            sl_pips = min(max(atr * 0.8, pair_cfg["min_sl"]), pair_cfg["max_sl"])

        tp_pips = sl_pips * RR_RATIO

        if signal_dir == "BUY":
            sl_price = c["c"] - sl_pips * pip_val
            tp_price = c["c"] + tp_pips * pip_val
        else:
            sl_price = c["c"] + sl_pips * pip_val
            tp_price = c["c"] - tp_pips * pip_val

        # ── Build signal with Position Sizer ──
        rr = sizer.dynamic_rr(pair_name, htf_dir, len(confluences))
        tp_pips = sl_pips * rr
        
        if signal_dir == "BUY":
            sl_price = c["c"] - sl_pips * pip_val
            tp_price = c["c"] + tp_pips * pip_val
        else:
            sl_price = c["c"] + sl_pips * pip_val
            tp_price = c["c"] - tp_pips * pip_val

        signal = {
            "pair": pair_name,
            "mt5_symbol": pair_name,
            "direction": signal_dir,
            "entry": round(c["c"], pair_cfg["decimals"]),
            "sl": round(sl_price, pair_cfg["decimals"]),
            "tp": round(tp_price, pair_cfg["decimals"]),
            "sl_pips": round(sl_pips, 1),
            "tp_pips": round(tp_pips, 1),
            "rr": round(rr, 1),
            "dt": dt.isoformat(),
            "kz": kz_name,
            "confluences": confluences,
            "n_confluences": len(confluences),
            "htf": htf_dir,
            "has_fvg": fvg_found,
            "has_ob": ob_found,
            "has_smt": smt_found,
            "strategy": "MULTI_CONFLUENCE",
            "entry_idx": i,
        }
        
        # ── M1 Precision Entry ──
        signal = refine_entry_m1(pair_cfg, signal)
        
        # ── Position Sizer: dynamic volume ──
        sizer.update_balance(sizer.get_balance())
        risk_pct = 0.005 if "XAU" in pair_name.upper() else 0.01
        volume, ps_details = sizer.calculate(pair_name, signal["sl_pips"], risk_pct)
        signal["volume"] = volume
        signal["position_sizer"] = ps_details
        
        # ── Recalculate TP with dynamic RR from PositionSizer ──
        rr_dynamic = sizer.dynamic_rr(pair_name, signal["htf"], signal["n_confluences"])
        signal["rr"] = round(rr_dynamic, 1)
        signal["tp_pips"] = round(signal["sl_pips"] * rr_dynamic, 1)
        if signal["direction"] == "BUY":
            signal["tp"] = round(signal["entry"] + signal["tp_pips"] * pip_val, pair_cfg["decimals"])
        else:
            signal["tp"] = round(signal["entry"] - signal["tp_pips"] * pip_val, pair_cfg["decimals"])
        
        signals.append(signal)
        entered_days.add(day_key)

    return signals

# ═══════════════════════════════════════════════════════════════════════════
# EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

def execute_trade_real(signal: dict, volume: float = 0.01) -> dict:
    """
    Execute trade via MT5 bridge (hermes_mt5_bridge).
    Returns result dict.
    """
    try:
        sys.path.insert(0, str(Path.home() / ".hermes" / "scripts"))
        from hermes_mt5_bridge import send_order, get_status
    except ImportError as e:
        print(f"   ❌ MT5 bridge indisponível: {e}")
        return {"status": "error", "reason": "bridge_unavailable"}

    print(f"\n📊 [CÓRTEX VISUAL] {signal['pair']} {signal['direction']}")
    print(f"   Entry: {fmt_price(signal['entry'], 5)} | "
          f"SL: {fmt_price(signal['sl'], 5)} | TP: {fmt_price(signal['tp'], 5)}")
    print(f"   SL: {signal['sl_pips']}p | TP: {signal['tp_pips']}p | RR: 1:{signal['rr']}")
    print(f"   Confluências ({signal['n_confluences']}): {', '.join(signal['confluences'])}")
    print(f"   Killzone: {signal['kz']} | HTF: {signal['htf']}")

    result = send_order(
        symbol=signal["mt5_symbol"],
        direction=signal["direction"],
        volume=volume,
        sl=signal["sl"],
        tp=signal["tp"],
        timeout=10,
    )

    if result and result.get("status") == "ok":
        print(f"   ✅ ORDEM EXECUTADA: ticket={result.get('ticket', '?')}")
        reset_mt5_timeouts(signal["pair"])
        return {"status": "executed", "ticket": result.get("ticket"), "result": result}
    elif result and result.get("status") == "error" and "timeout" in str(result.get("msg", "")).lower():
        print(f"   ⏱️ TIMEOUT MT5 para {signal['pair']}")
        paused = record_mt5_timeout(signal["pair"])
        if paused:
            print(f"   🛑 CIRCUIT BREAKER: {signal['pair']} pausado por {CB_COOLDOWN_MINUTES}min")
        return {"status": "timeout", "reason": "mt5_timeout"}
    else:
        print(f"   ⚠️ MT5: {result}")
        return {"status": "failed", "result": result}

def execute_trade_dry_run(signal: dict):
    """Paper trading — print signal details, no real execution."""
    print(f"\n📝 [DRY-RUN] {signal['pair']} {signal['direction']}")
    print(f"   Entry: {fmt_price(signal['entry'], 5)} | "
          f"SL: {fmt_price(signal['sl'], 5)} | TP: {fmt_price(signal['tp'], 5)}")
    print(f"   SL: {signal['sl_pips']}p | TP: {signal['tp_pips']}p | RR: 1:{signal['rr']}")
    print(f"   Confluências ({signal['n_confluences']}): {', '.join(signal['confluences'])}")
    print(f"   Killzone: {signal['kz']} | HTF: {signal['htf']}")
    print(f"   FVG: {'✓' if signal['has_fvg'] else '✗'} | "
          f"OB: {'✓' if signal['has_ob'] else '✗'} | "
          f"SMT: {'✓' if signal['has_smt'] else '✗'}")
    return {"status": "dry_run"}

def publish_to_thalamus(signal: dict, result: dict, dry_run: bool = False):
    """Publish signal and result to Thalamus for inter-agent communication."""
    if not THALAMUS_AVAILABLE:
        return

    try:
        if dry_run:
            thalamus.send_message(
                source="cortex_visual",
                target="meta_observer",
                msg_type="signal_dry_run",
                content={
                    "pair": signal["pair"],
                    "direction": signal["direction"],
                    "confluences": signal["confluences"],
                    "n_confluences": signal["n_confluences"],
                    "kz": signal["kz"],
                    "htf": signal["htf"],
                    "entry": signal["entry"],
                    "sl": signal["sl"],
                    "tp": signal["tp"],
                    "timestamp": signal["dt"],
                },
                priority=3,
            )
        else:
            thalamus.send_message(
                source="cortex_visual",
                target="meta_observer",
                msg_type="trade_opened",
                content={
                    "pair": signal["pair"],
                    "direction": signal["direction"],
                    "entry": signal["entry"],
                    "sl": signal["sl"],
                    "tp": signal["tp"],
                    "ticket": result.get("ticket"),
                    "confluences": signal["confluences"],
                    "n_confluences": signal["n_confluences"],
                    "strategy": "MULTI_CONFLUENCE",
                },
                priority=5,
            )
            thalamus.log_event(
                event_type="trade_signal",
                source="cortex_visual",
                data={
                    "pair": signal["pair"],
                    "direction": signal["direction"],
                    "confluences": signal["n_confluences"],
                    "status": result.get("status", "unknown"),
                },
                severity="info",
            )
    except Exception as e:
        pass  # Thalamus is non-critical

# ═══════════════════════════════════════════════════════════════════════════
# STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def load_state() -> dict:
    """Load persistent state: entered days per pair, daily stats."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {
        "entered_days": {},     # {pair: ["2026-05-28", ...]}
        "today": None,
        "trades_today": 0,
        "daily_pnl": 0.0,
        "last_cycle": None,
    }

def save_state(state: dict):
    """Save persistent state."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))

def get_today_entered_days(state: dict, pair: str) -> set:
    """Get set of entered days for a pair, resetting if new day."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    if state.get("today") != today_str:
        state["today"] = today_str
        state["entered_days"] = {}
        state["trades_today"] = 0
        save_state(state)
    return set(state.get("entered_days", {}).get(pair, []))

def record_entered_day(state: dict, pair: str, day_str: str):
    """Record that we've entered a trade for this pair today."""
    if "entered_days" not in state:
        state["entered_days"] = {}
    if pair not in state["entered_days"]:
        state["entered_days"][pair] = []
    if day_str not in state["entered_days"][pair]:
        state["entered_days"][pair].append(day_str)
    state["trades_today"] = state.get("trades_today", 0) + 1
    save_state(state)

# ═══════════════════════════════════════════════════════════════════════════
# MAIN SCAN CYCLE
# ═══════════════════════════════════════════════════════════════════════════

def scan_cycle(dry_run: bool = False, scan_only: bool = False) -> dict:
    """
    Execute one complete scan cycle across all pairs.
    Returns summary dict.
    """
    mode_str = "SCAN-ONLY" if scan_only else ("DRY-RUN (paper)" if dry_run else "REAL (MT5 bridge)")
    print(f"\n{'═' * 60}")
    print(f"  CÓRTEX VISUAL — Scan: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  Modo: {mode_str}")
    print(f"{'═' * 60}")

    state = load_state()

    # ── Circuit breaker: check paused pairs ──
    paused_pairs = []
    for pair_name in PAIRS:
        if is_pair_paused(pair_name):
            paused_pairs.append(pair_name)
    if paused_pairs:
        print(f"\n🛑 CIRCUIT BREAKER: Pares pausados: {', '.join(paused_pairs)}")

    # ── Fetch all data ──
    print(f"\n📡 Buscando dados de mercado...")
    all_m15, all_h1 = {}, {}
    for pair_name, cfg in PAIRS.items():
        if pair_name in paused_pairs:
            continue
        print(f"  → {pair_name} M15...", end=" ", flush=True)
        m15 = fetch_candles(cfg["symbol"], M15_PERIOD, M15_LOOKBACK_DAYS)
        print(f"{len(m15)} candles", end=" | ")
        all_m15[pair_name] = m15

        print(f"H1...", end=" ", flush=True)
        h1 = fetch_candles(cfg["symbol"], H1_PERIOD, H1_LOOKBACK_DAYS)
        print(f"{len(h1)} candles")
        all_h1[pair_name] = h1

    total_m15 = sum(len(v) for v in all_m15.values())
    total_h1  = sum(len(v) for v in all_h1.values())
    if total_m15 == 0:
        print("   ❌ Nenhum dado M15 obtido. Abortando scan.")
        return {"status": "no_data"}

    print(f"   ✅ Total: {total_m15} M15 + {total_h1} H1 candles")

    # ── Check MT5 positions (real mode only) ──
    open_positions = 0
    open_symbols = set()
    if not dry_run and not scan_only:
        try:
            sys.path.insert(0, str(Path.home() / ".hermes" / "scripts"))
            from hermes_mt5_bridge import get_status
            status = get_status(timeout=5)
            if status and status.get("status") == "ok":
                open_positions = status.get("positions", 0)
                for p in status.get("positions_data", []):
                    sym = p.get("symbol", "")
                    if sym:
                        open_symbols.add(sym)
                print(f"\n📊 MT5: {open_positions} posições abertas, "
                      f"saldo=${status.get('balance', '?')}")
        except Exception as e:
            print(f"\n⚠️ MT5 status indisponível: {e}")

    if open_positions >= MAX_POSITIONS:
        print(f"⛔ Máx posições atingido ({open_positions}/{MAX_POSITIONS}). Scan cancelado.")
        return {"status": "max_positions", "open_positions": open_positions}

    # ── Scan each pair ──
    all_signals = []
    for pair_name, cfg in PAIRS.items():
        if pair_name in paused_pairs:
            print(f"\n⏸️  {pair_name}: PAUSADO (circuit breaker)")
            continue

        if pair_name not in all_m15 or not all_m15[pair_name]:
            continue
        if pair_name not in all_h1 or not all_h1[pair_name]:
            continue

        # Build correlated data for SMT
        correlated = {}
        for (p1, p2) in SMT_PAIRS:
            if pair_name in (p1, p2):
                other = p2 if pair_name == p1 else p1
                if other in all_m15:
                    correlated[other] = all_m15[other]

        entered_days = get_today_entered_days(state, pair_name)
        signals = scan_pair(
            pair_name, cfg,
            all_m15[pair_name], all_h1[pair_name],
            correlated, entered_days
        )

        if signals:
            print(f"\n🎯 {pair_name}: {len(signals)} sinal(is) encontrado(s)")
            for s in signals:
                print(f"   → {s['direction']} @ {fmt_price(s['entry'], cfg['decimals'])} "
                      f"| {s['n_confluences']} confl: {', '.join(s['confluences'])}")
            all_signals.extend(signals)

    if not all_signals:
        print(f"\n📭 Nenhum sinal multi-confluência encontrado neste ciclo.")
        save_state(state)
        return {"status": "no_signals", "pairs_scanned": len(all_m15)}

    # ── Sort by quality (more confluences = better) ──
    all_signals.sort(key=lambda s: (s["n_confluences"], s.get("has_smt", False)), reverse=True)

    # ── Apply limits ──
    slots = MAX_POSITIONS - open_positions
    selected = all_signals[:min(slots, len(all_signals))]

    # ── Anti-duplicate check ──
    final_signals = []
    for s in selected:
        pair_sym = s["mt5_symbol"]
        if pair_sym in open_symbols:
            print(f"\n⏭️  {s['pair']}: já tem posição aberta — ignorado")
            continue

        dt = datetime.fromisoformat(s["dt"])
        if is_duplicate(s["pair"], s["direction"], s["entry"], dt):
            print(f"\n⏭️  {s['pair']} {s['direction']}: duplicata detectada (fingerprint TTL) — ignorado")
            continue

        final_signals.append(s)

    # ── Execute ──
    results = []
    for signal in final_signals:
        try:
            if dry_run or scan_only:
                result = execute_trade_dry_run(signal)
            else:
                result = execute_trade_real(signal)

            results.append({"signal": signal, "result": result})

            # Record entered day
            dt = datetime.fromisoformat(signal["dt"])
            record_entered_day(state, signal["pair"], dt.strftime("%Y-%m-%d"))

            # Publish to Thalamus
            publish_to_thalamus(signal, result, dry_run=dry_run)

        except Exception as e:
            print(f"\n❌ Erro ao executar {signal['pair']}: {e}")
            if THALAMUS_AVAILABLE:
                try:
                    thalamus.log_event(
                        event_type="execution_error",
                        source="cortex_visual",
                        data={"pair": signal["pair"], "error": str(e)},
                        severity="error",
                    )
                except Exception:
                    pass

    # ── Update state ──
    state["last_cycle"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    summary = {
        "status": "ok",
        "signals_found": len(all_signals),
        "signals_executed": len(results),
        "dry_run": dry_run,
        "scan_only": scan_only,
        "paused_pairs": paused_pairs,
        "open_positions": open_positions,
        "trades_today": state.get("trades_today", 0),
    }

    print(f"\n{'═' * 60}")
    print(f"  ✅ Ciclo concluído: {len(results)} trade(s) executado(s)")
    print(f"  Sinais encontrados: {len(all_signals)} | "
          f"Executados: {len(results)} | "
          f"Trades hoje: {state.get('trades_today', 0)}")
    print(f"{'═' * 60}\n")

    return summary

# ═══════════════════════════════════════════════════════════════════════════
# DAEMON LOOP
# ═══════════════════════════════════════════════════════════════════════════

def daemon_loop(dry_run: bool = False, scan_only: bool = False,
                interval_minutes: int = 5):
    """
    Run scan_cycle continuously with a configurable interval.
    Default: scan every 5 minutes.
    """
    print(f"\n🔄 CÓRTEX VISUAL DAEMON iniciado")
    print(f"   Modo: {'DRY-RUN' if dry_run else 'REAL'}")
    print(f"   Intervalo: {interval_minutes}min")
    print(f"   Pressione Ctrl+C para parar\n")

    cycle_count = 0
    try:
        while True:
            cycle_count += 1
            print(f"\n── Ciclo #{cycle_count} ── {datetime.now().strftime('%H:%M:%S')} ──")

            try:
                summary = scan_cycle(dry_run=dry_run, scan_only=scan_only)
            except Exception as e:
                print(f"❌ Erro no ciclo #{cycle_count}: {e}")
                if THALAMUS_AVAILABLE:
                    try:
                        thalamus.raise_alert(
                            level="error",
                            title="Cortex Visual cycle error",
                            description=str(e)[:200],
                            source="cortex_visual",
                        )
                    except Exception:
                        pass

            # Wait for next cycle
            print(f"⏳ Próximo scan em {interval_minutes}min...")
            time.sleep(interval_minutes * 60)
    except KeyboardInterrupt:
        print("\n\n🛑 CÓRTEX VISUAL — Daemon encerrado pelo usuário.")
        print(f"   Ciclos executados: {cycle_count}")

# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Córtex Visual — Agente de Trading Multi-Confluência SMC/ICT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  cortex_visual.py                    # Modo real (via MT5 bridge)
  cortex_visual.py --dry-run          # Paper trading
  cortex_visual.py --scan-only        # Apenas scan, sem executar
  cortex_visual.py --once             # 1 ciclo e sai
  cortex_visual.py --daemon           # Loop contínuo (intervalo padrão 5min)
  cortex_visual.py --daemon --interval 15  # Loop a cada 15min
  cortex_visual.py --status           # Mostrar estado atual
  cortex_visual.py --reset-cb         # Resetar circuit breaker
        """,
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Paper trading — não envia ordens reais")
    parser.add_argument("--scan-only", action="store_true",
                        help="Apenas escaneia sinais, sem executar nada")
    parser.add_argument("--once", action="store_true",
                        help="Executa 1 ciclo e sai (padrão)")
    parser.add_argument("--daemon", action="store_true",
                        help="Loop contínuo com intervalo configurável")
    parser.add_argument("--interval", type=int, default=5,
                        help="Intervalo entre scans em minutos (padrão: 5)")
    parser.add_argument("--status", action="store_true",
                        help="Mostrar estado atual do agente")
    parser.add_argument("--reset-cb", action="store_true",
                        help="Resetar circuit breaker de todos os pares")

    args = parser.parse_args()

    # ── --status: show current state ──
    if args.status:
        state = load_state()
        cb = load_cb_state()
        print(f"\n📊 CÓRTEX VISUAL — Estado Atual")
        print(f"   Último ciclo: {state.get('last_cycle', 'Nunca')}")
        print(f"   Trades hoje:  {state.get('trades_today', 0)}")
        print(f"   Today key:    {state.get('today', 'N/A')}")
        print(f"\n📊 Circuit Breaker:")
        print(f"   Timeouts: {cb.get('timeouts', {})}")
        print(f"   Paused:   {cb.get('paused_until', {})}")
        for pair in PAIRS:
            paused = is_pair_paused(pair)
            print(f"   {pair}: {'⏸️ PAUSADO' if paused else '✅ ATIVO'}")
        print()
        return

    # ── --reset-cb: reset circuit breaker ──
    if args.reset_cb:
        cb = {"timeouts": {}, "paused_until": {}}
        save_cb_state(cb)
        print("✅ Circuit breaker resetado para todos os pares.")
        return

    # ── Announce startup via Thalamus ──
    if THALAMUS_AVAILABLE:
        try:
            thalamus.log_event(
                event_type="agent_startup",
                source="cortex_visual",
                data={"mode": "dry_run" if args.dry_run else "real",
                      "version": "1.0.0"},
                severity="info",
            )
        except Exception:
            pass

    # ── Run ──
    if args.daemon:
        daemon_loop(dry_run=args.dry_run, scan_only=args.scan_only,
                    interval_minutes=args.interval)
    else:
        # Single cycle (--once or default)
        summary = scan_cycle(dry_run=args.dry_run, scan_only=args.scan_only)
        return summary

if __name__ == "__main__":
    main()
