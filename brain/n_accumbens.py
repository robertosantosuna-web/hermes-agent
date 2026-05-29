#!/usr/bin/env python3
"""N_ACCUMBENS — Reinforcement Learning Engine (every 4h).
Calculates pair weights from trade history, classifies pairs by win rate,
seeds from backtest when data is sparse, and estimates market regime.

Integrates with:
  - thalamus: updates pair_weights, market_regime state
  - sona_lite: reinforcement-based weight adjustment
"""

import json
import os
import sys
import math
from datetime import datetime, timezone
from collections import defaultdict

# --- Paths -----------------------------------------------------------
TRADE_LOG_PATH = os.path.expanduser("~/.hermes/forex/trade_log.json")
BEST_PARAMS_PATH = os.path.expanduser("~/.hermes/forex/best_params.json")
ACCUMBENS_STATE_PATH = os.path.expanduser("~/.hermes/forex/accumbens_state.json")
OHLCV_CACHE_DIR = os.path.expanduser("~/.hermes/forex/ohlcv_cache")

# --- Imports with graceful fallback -----------------------------------
try:
    import thalamus
    HAS_THALAMUS = True
except ImportError:
    HAS_THALAMUS = False
    print("[n_accumbens] WARNING: thalamus module not found.")

try:
    import sona_lite
    HAS_SONA = True
except ImportError:
    HAS_SONA = False
    print("[n_accumbens] WARNING: sona_lite module not found.")


# ======================================================================
#  UTILITIES
# ======================================================================
def _normalize_pair(pair):
    """Normalize pair names (remove _KZ, /, uppercase)."""
    return pair.upper().replace("/", "").replace("_KZ", "")


def _parse_iso(ts_str):
    if not ts_str:
        return None
    try:
        ts_str = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except (ValueError, TypeError):
        return None


def _parse_trade_pnl(trade):
    pnl = trade.get("pnl")
    if pnl is not None:
        return float(pnl)
    pnl_pips = trade.get("pnl_pips")
    if pnl_pips is not None:
        return float(pnl_pips)
    return 0.0


def _is_win(trade):
    result = trade.get("result", "").upper()
    if result == "WIN":
        return True
    if result == "LOSS":
        return False
    return _parse_trade_pnl(trade) > 0


# ======================================================================
#  PAIR WEIGHT CALCULATION
# ======================================================================
def calculate_pair_weights():
    """Read trade_log, calculate WR/P&L per pair, classify into tiers.

    Classification tiers:
      PRIORITY  — WR >= 65%
      ACTIVE    — WR >= 55%
      WATCH     — WR >= 45%
      PAUSE     — WR <  45%
    """
    if not os.path.exists(TRADE_LOG_PATH):
        print(f"[n_accumbens] trade_log.json not found.")
        return {"weights": {}, "classifications": {}, "trades_processed": 0}

    with open(TRADE_LOG_PATH) as f:
        data = json.load(f)

    trades = data.get("trades", []) if isinstance(data, dict) else data
    if not isinstance(trades, list):
        trades = []

    pair_data = defaultdict(lambda: {"wins": 0, "total": 0, "pnl": 0.0,
                                      "first_trade": None, "last_trade": None})

    for trade in trades:
        pair = _normalize_pair(trade.get("pair", ""))
        if not pair:
            continue
        dt = _parse_iso(trade.get("timestamp") or trade.get("time") or trade.get("closed_at"))
        is_w = _is_win(trade)
        pnl = _parse_trade_pnl(trade)

        pd = pair_data[pair]
        pd["total"] += 1
        pd["pnl"] += pnl
        if is_w:
            pd["wins"] += 1
        if dt:
            if pd["first_trade"] is None or dt < pd["first_trade"]:
                pd["first_trade"] = dt
            if pd["last_trade"] is None or dt > pd["last_trade"]:
                pd["last_trade"] = dt

    # Build weights and classifications
    weights = {}
    classifications = {}
    for pair, pd in pair_data.items():
        wr = (pd["wins"] / pd["total"] * 100) if pd["total"] > 0 else 0.0

        if wr >= 65:
            tier = "PRIORITY"
        elif wr >= 55:
            tier = "ACTIVE"
        elif wr >= 45:
            tier = "WATCH"
        else:
            tier = "PAUSE"

        weights[pair] = {
            "wr": round(wr, 1),
            "trades": pd["total"],
            "wins": pd["wins"],
            "pnl": round(pd["pnl"], 2),
            "score": round(wr * math.log(max(pd["total"], 1) + 1), 1),
        }
        classifications[pair] = tier

    total_trades = sum(pd["total"] for pd in pair_data.values())

    print(f"[n_accumbens] Processed {total_trades} trades across {len(pair_data)} pairs")
    for pair, tier in sorted(classifications.items()):
        wr = weights[pair]["wr"]
        print(f"  {pair:12s} → {tier:8s}  (WR: {wr:.1f}%, {weights[pair]['trades']} trades, P&L: {weights[pair]['pnl']:+.2f})")

    return {
        "weights": weights,
        "classifications": classifications,
        "trades_processed": total_trades,
    }


# ======================================================================
#  SEED FROM BACKTEST
# ======================================================================
def seed_from_backtest(existing_weights, min_trades=5):
    """If a pair has fewer than min_trades real trades, seed its weight from best_params.json."""
    if not os.path.exists(BEST_PARAMS_PATH):
        print("[n_accumbens] best_params.json not found — cannot seed.")
        return existing_weights

    with open(BEST_PARAMS_PATH) as f:
        best_params = json.load(f)

    seeded = 0
    for key, params in best_params.items():
        pair = _normalize_pair(params.get("pair", ""))
        if not pair:
            continue

        current = existing_weights.get(pair, {})
        current_trades = current.get("trades", 0)

        if current_trades < min_trades:
            # Seed from backtest win_rate
            backtest_wr = params.get("win_rate", 0)
            backtest_pnl = params.get("pnl", 0)
            backtest_trades = params.get("trades", 0)

            existing_weights[pair] = {
                "wr": round(backtest_wr, 1),
                "trades": current_trades,
                "wins": current.get("wins", 0),
                "pnl": round(backtest_pnl, 2),
                "score": round(backtest_wr * math.log(max(backtest_trades, 1) + 1), 1),
                "seeded": True,
                "seed_source": "best_params",
                "backtest_trades": backtest_trades,
            }
            seeded += 1
            print(f"[n_accumbens] Seeded {pair} from backtest: WR={backtest_wr:.1f}% "
                  f"(only {current_trades} real trades)")

    if seeded:
        print(f"[n_accumbens] Seeded {seeded} pairs from backtest")
    else:
        print("[n_accumbens] No pairs needed seeding (all have >=5 real trades)")

    return existing_weights


# ======================================================================
#  REINFORCEMENT APPLICATION
# ======================================================================
def apply_reinforcement(old_weights, new_weights):
    """Compare with previous weights, apply reinforcement via sona_lite."""
    if not HAS_SONA:
        return new_weights

    changes = []
    for pair, info in new_weights.items():
        old_info = old_weights.get(pair, {})
        old_wr = old_info.get("wr", 0)
        new_wr = info.get("wr", 0)

        # Adjust weight via sona_lite EMA
        adjusted = sona_lite.adjust_weight(
            key=f"pair:{pair}",
            new_value=new_wr / 100.0,  # normalize 0-1
            old_value=old_wr / 100.0 if old_wr else None,
        )

        # Only track meaningful changes
        if abs(new_wr - old_wr) >= 3.0 and old_wr > 0:
            changes.append(
                {
                    "pair": pair,
                    "old_wr": round(old_wr, 1),
                    "new_wr": round(new_wr, 1),
                    "adjusted_weight": round(adjusted, 3),
                }
            )
            sona_lite.record_reward(
                signal=1.0 if new_wr > old_wr else -0.8,
                magnitude=abs(new_wr - old_wr) / 200,
            )

    if changes:
        print(f"[n_accumbens] Reinforcement applied: {len(changes)} weight adjustments")
        for ch in changes:
            print(f"  {ch['pair']:12s}: {ch['old_wr']:.1f}% → {ch['new_wr']:.1f}% "
                  f"(adjusted: {ch['adjusted_weight']:.3f})")

    return new_weights


# ======================================================================
#  MARKET REGIME DETECTION
# ======================================================================
def get_market_regime():
    """Estimate market regime (trending/ranging/choppy) using simplified
    ATR and ADX from cached OHLCV data. Falls back to 'unknown' if no data.
    """
    regimes = {}

    if not os.path.isdir(OHLCV_CACHE_DIR):
        print("[n_accumbens] No OHLCV cache directory — regime unknown.")
        return {"overall": "unknown", "pairs": {}}

    for fname in sorted(os.listdir(OHLCV_CACHE_DIR)):
        if not fname.endswith(".json"):
            continue

        # Extract pair from filename, e.g., "EURUSD_15m.json"
        pair = fname.split("_")[0].upper()
        fpath = os.path.join(OHLCV_CACHE_DIR, fname)

        try:
            with open(fpath) as f:
                candles = json.load(f)

            if not isinstance(candles, list) or len(candles) < 20:
                regimes[pair] = "unknown"
                continue

            # Compute simple ATR (Average True Range) over last 14 candles
            atr = _compute_simple_atr(candles[-20:])
            # Compute simple ADX approximation over last 14 candles
            adx = _compute_simple_adx(candles[-20:])

            if adx is None or atr is None:
                regimes[pair] = "unknown"
                continue

            # Classification logic
            if adx > 25:
                regimes[pair] = "trending"
            elif adx > 15:
                regimes[pair] = "ranging" if atr < _median_atr(candles[-20:]) * 1.2 else "choppy"
            else:
                regimes[pair] = "ranging" if atr < _median_atr(candles[-20:]) * 1.5 else "choppy"

        except (json.JSONDecodeError, IOError, KeyError):
            regimes[pair] = "unknown"

    # Overall regime: majority vote
    if regimes:
        mode = max(set(regimes.values()), key=list(regimes.values()).count)
        overall = mode if mode != "unknown" else "ranging"
    else:
        overall = "unknown"

    print(f"[n_accumbens] Market regime: overall={overall}, pairs={len(regimes)}")
    for pair, regime in sorted(regimes.items()):
        if regime != "unknown":
            print(f"  {pair}: {regime}")

    return {"overall": overall, "pairs": regimes}


def _compute_simple_atr(candles, period=14):
    """Compute simplified ATR from OHLCV candles."""
    if len(candles) < period + 1:
        return None
    tr_values = []
    for i in range(1, min(len(candles), period + 1)):
        c = candles[-i]
        prev = candles[-(i + 1)]
        h = float(c.get("high", c.get("h", 0)))
        l = float(c.get("low", c.get("l", 0)))
        prev_c = float(prev.get("close", prev.get("c", 0)))
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        tr_values.append(tr)
    return sum(tr_values) / len(tr_values) if tr_values else None


def _compute_simple_adx(candles, period=14):
    """Compute simplified ADX from OHLCV candles."""
    if len(candles) < period + 1:
        return None

    plus_dm = []
    minus_dm = []
    tr_values = []

    for i in range(1, min(len(candles), period + 1)):
        c = candles[-i]
        prev = candles[-(i + 1)]
        h = float(c.get("high", c.get("h", 0)))
        l = float(c.get("low", c.get("l", 0)))
        prev_h = float(prev.get("high", prev.get("h", 0)))
        prev_l = float(prev.get("low", prev.get("l", 0)))
        prev_c = float(prev.get("close", prev.get("c", 0)))

        up = h - prev_h
        down = prev_l - l

        plus_dm.append(up if up > down and up > 0 else 0)
        minus_dm.append(down if down > up and down > 0 else 0)

        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        tr_values.append(tr)

    if not tr_values or sum(tr_values) == 0:
        return None

    smooth_tr = sum(tr_values) / len(tr_values)
    smooth_plus = sum(plus_dm) / len(plus_dm)
    smooth_minus = sum(minus_dm) / len(minus_dm)

    di_plus = (smooth_plus / smooth_tr * 100) if smooth_tr > 0 else 0
    di_minus = (smooth_minus / smooth_tr * 100) if smooth_tr > 0 else 0

    dx_denom = di_plus + di_minus
    if dx_denom == 0:
        return 0

    dx = abs(di_plus - di_minus) / dx_denom * 100
    return dx


def _median_atr(candles):
    """Helper: median TR of candles for comparison baseline."""
    trs = []
    for i in range(1, len(candles)):
        c = candles[-i]
        prev = candles[-(i + 1)]
        h = float(c.get("high", c.get("h", 0)))
        l = float(c.get("low", c.get("l", 0)))
        prev_c = float(prev.get("close", prev.get("c", 0)))
        trs.append(max(h - l, abs(h - prev_c), abs(l - prev_c)))
    if not trs:
        return 0.001
    trs.sort()
    mid = len(trs) // 2
    return trs[mid] if len(trs) % 2 == 1 else (trs[mid - 1] + trs[mid]) / 2


# ======================================================================
#  STATE PERSISTENCE
# ======================================================================
def _load_prev_state():
    if os.path.exists(ACCUMBENS_STATE_PATH):
        with open(ACCUMBENS_STATE_PATH) as f:
            return json.load(f)
    return {"weights": {}, "classifications": {}, "last_run": None}


def _save_state(state):
    os.makedirs(os.path.dirname(ACCUMBENS_STATE_PATH), exist_ok=True)
    with open(ACCUMBENS_STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, default=str)


# ======================================================================
#  MAIN CYCLE
# ======================================================================
def run():
    """Main reinforcement cycle: pair weights + seed + reinforcement + regime."""
    print("=" * 60)
    print(f"[n_accumbens] Reinforcement cycle — {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    prev_state = _load_prev_state()
    prev_weights = prev_state.get("weights", {})

    # 1. Calculate fresh weights
    result = calculate_pair_weights()
    weights = result["weights"]
    classifications = result["classifications"]
    trades_processed = result["trades_processed"]

    # 2. Seed from backtest if sparse data
    weights = seed_from_backtest(weights)

    # 3. Apply reinforcement
    weights = apply_reinforcement(prev_weights, weights)

    # 4. Market regime detection
    regime = get_market_regime()

    # 5. Publish via thalamus
    if HAS_THALAMUS:
        thalamus.update_state("pair_weights", {
            "weights": weights,
            "classifications": classifications,
            "trades_processed": trades_processed,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        thalamus.update_state("market_regime", regime)

        thalamus.log_event(
            event_type="n_accumbens_cycle",
            source="n_accumbens",
            data={
                "pairs_analyzed": len(weights),
                "trades_processed": trades_processed,
                "market_regime": regime["overall"],
                "priority_pairs": sum(1 for v in classifications.values() if v == "PRIORITY"),
                "pause_pairs": sum(1 for v in classifications.values() if v == "PAUSE"),
            },
            severity="info",
        )

        # Alert if many pairs in PAUSE
        pause_count = sum(1 for v in classifications.values() if v == "PAUSE")
        if pause_count >= 3:
            thalamus.raise_alert(
                level="warning",
                title="Multiple pairs in PAUSE",
                description=f"{pause_count} pairs have WR < 45%. Consider reducing exposure.",
                source="n_accumbens",
            )

    else:
        print("[n_accumbens] Running standalone — no Tálamo publication.")

    # 6. Persist state
    state = {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "weights": weights,
        "classifications": classifications,
        "market_regime": regime,
        "trades_processed": trades_processed,
        "cycle": prev_state.get("cycle", 0) + 1,
    }
    _save_state(state)

    summary = {
        "pairs": len(weights),
        "trades_processed": trades_processed,
        "regime": regime["overall"],
        "priority": sum(1 for v in classifications.values() if v == "PRIORITY"),
        "active": sum(1 for v in classifications.values() if v == "ACTIVE"),
        "watch": sum(1 for v in classifications.values() if v == "WATCH"),
        "pause": sum(1 for v in classifications.values() if v == "PAUSE"),
    }
    print(f"\n[n_accumbens] Cycle complete: {summary}")
    return summary


# ======================================================================
#  MAIN
# ======================================================================
if __name__ == "__main__":
    result = run()
    print(f"\n{'─' * 60}")
    print(f"Summary: {json.dumps(result, indent=2)}")
    print(f"State saved to: {ACCUMBENS_STATE_PATH}")
