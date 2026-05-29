#!/usr/bin/env python3
"""HIPPOCAMPUS — Consolidator of Patterns (every 6h).
Reads trade_log, failure_log, detects recurring patterns,
compares with previous execution, publishes discoveries via Tálamo.

Integrates with:
  - thalamus: for event logging, discoveries, state, broadcast
  - sona_lite: for pattern weight reinforcement
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# --- Paths -----------------------------------------------------------
TRADE_LOG_PATH = os.path.expanduser("~/.hermes/forex/trade_log.json")
FAILURE_LOG_PATH = os.path.expanduser("~/.hermes/forex/failure_log.json")
HIPPO_STATE_PATH = os.path.expanduser("~/.hermes/brain/hippocampus_state.json")
FOREX_DIR = os.path.expanduser("~/.hermes/forex")

# --- Imports with graceful fallback -----------------------------------
try:
    import thalamus  # expected in ~/.hermes/brain/
    HAS_THALAMUS = True
except ImportError:
    HAS_THALAMUS = False
    print("[hippocampus] WARNING: thalamus module not found — running standalone.")

try:
    import sona_lite
    HAS_SONA = True
except ImportError:
    HAS_SONA = False
    print("[hippocampus] WARNING: sona_lite module not found — reinforcement disabled.")


# ======================================================================
#  STATE MANAGEMENT
# ======================================================================
def _load_state():
    if os.path.exists(HIPPO_STATE_PATH):
        with open(HIPPO_STATE_PATH) as f:
            return json.load(f)
    return {"last_run": None, "cycle_count": 0,
            "wr_by_day": {}, "wr_by_pair": {}, "wr_by_hour": {},
            "failure_categories": {}, "discoveries_published": 0}


def _save_state(state):
    os.makedirs(os.path.dirname(HIPPO_STATE_PATH), exist_ok=True)
    with open(HIPPO_STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, default=str)


# ======================================================================
#  TRADE LOG ANALYSIS
# ======================================================================
def _parse_iso(ts_str):
    """Parse ISO timestamp, returning a datetime (naive, UTC)."""
    if not ts_str:
        return None
    try:
        # Handle 'Z' suffix
        ts_str = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except (ValueError, TypeError):
        return None


def _parse_trade_time(trade):
    """Extract timestamp from a trade dict, which may use 'timestamp',
    'time', 'closed_at', or 'exit_time'."""
    for key in ("timestamp", "time", "closed_at", "exit_time"):
        ts = trade.get(key)
        if ts:
            dt = _parse_iso(ts)
            if dt:
                return dt
    return None


def _parse_trade_pnl(trade):
    """Extract P&L from a trade dict — may be 'pnl' or 'pnl_pips'."""
    pnl = trade.get("pnl")
    if pnl is not None:
        return float(pnl)
    pnl_pips = trade.get("pnl_pips")
    if pnl_pips is not None:
        return float(pnl_pips)
    return 0.0


def _is_win(trade):
    """Check if trade is a WIN."""
    result = trade.get("result", "").upper()
    if result == "WIN":
        return True
    if result == "LOSS":
        return False
    # Fallback: PnL > 0 = win
    return _parse_trade_pnl(trade) > 0


def _normalize_pair(pair):
    """Normalize pair names (remove _KZ suffix, uppercase, remove '/')."""
    pair = pair.upper().replace("/", "").replace("_KZ", "")
    return pair


def analyze_trade_log():
    """Read trade_log.json and compute WR by day_of_week, pair, and hour."""
    if not os.path.exists(TRADE_LOG_PATH):
        print(f"[hippocampus] trade_log.json not found at {TRADE_LOG_PATH}")
        return None, None, None

    with open(TRADE_LOG_PATH) as f:
        data = json.load(f)

    trades = data.get("trades", []) if isinstance(data, dict) else data
    if not isinstance(trades, list):
        trades = []

    # Aggregators
    by_day = defaultdict(lambda: {"wins": 0, "total": 0, "pnl": 0.0})
    by_pair = defaultdict(lambda: {"wins": 0, "total": 0, "pnl": 0.0})
    by_hour = defaultdict(lambda: {"wins": 0, "total": 0, "pnl": 0.0})

    for trade in trades:
        pair = _normalize_pair(trade.get("pair", ""))
        if not pair:
            continue

        dt = _parse_trade_time(trade)
        if not dt:
            continue

        is_w = _is_win(trade)
        pnl = _parse_trade_pnl(trade)

        day_key = dt.strftime("%A")  # Monday, Tuesday, etc.
        hour_key = dt.hour

        by_day[day_key]["total"] += 1
        by_day[day_key]["pnl"] += pnl
        if is_w:
            by_day[day_key]["wins"] += 1

        by_pair[pair]["total"] += 1
        by_pair[pair]["pnl"] += pnl
        if is_w:
            by_pair[pair]["wins"] += 1

        by_hour[str(hour_key)]["total"] += 1
        by_hour[str(hour_key)]["pnl"] += pnl
        if is_w:
            by_hour[str(hour_key)]["wins"] += 1

    # Calculate WR percentages
    def _calc_wr(agg_dict):
        result = {}
        for k, v in agg_dict.items():
            wr = (v["wins"] / v["total"] * 100) if v["total"] > 0 else 0.0
            result[k] = {
                "wr": round(wr, 1),
                "trades": v["total"],
                "wins": v["wins"],
                "pnl": round(v["pnl"], 2),
            }
        return result

    wr_day = _calc_wr(by_day)
    wr_pair = _calc_wr(by_pair)
    wr_hour = _calc_wr(by_hour)

    print(f"[hippocampus] Analyzed {len(trades)} trades")
    print(f"  Days: {len(wr_day)} | Pairs: {len(wr_pair)} | Hours: {len(wr_hour)}")

    return wr_day, wr_pair, wr_hour


# ======================================================================
#  FAILURE ANALYSIS
# ======================================================================
def analyze_failures():
    """Read failure_log, detect recurring categories (>=3 failures)."""
    categories = defaultdict(list)

    if not os.path.exists(FAILURE_LOG_PATH):
        print(f"[hippocampus] failure_log.json not found — skipping failure analysis.")
        return {}

    with open(FAILURE_LOG_PATH) as f:
        failures = json.load(f)

    if isinstance(failures, dict):
        failures = failures.get("failures", failures.get("entries", []))
    if not isinstance(failures, list):
        return {}

    for failure in failures:
        category = failure.get("category", failure.get("type", "unknown"))
        categories[category].append(failure)

    # Filter: >=3 occurrences
    recurring = {
        cat: entries
        for cat, entries in categories.items()
        if len(entries) >= 3
    }

    result = {}
    for cat, entries in recurring.items():
        result[cat] = {
            "count": len(entries),
            "latest": entries[-1].get("timestamp", entries[-1].get("time", "unknown")),
            "sample_message": entries[-1].get("message", entries[-1].get("description", "")),
        }

    if result:
        print(f"[hippocampus] Found {len(result)} recurring failure categories (>=3):")
        for cat, info in result.items():
            print(f"  - {cat}: {info['count']} occurrences")
    else:
        print("[hippocampus] No recurring failure categories detected.")

    return result


# ======================================================================
#  PATTERN DETECTION
# ======================================================================
def detect_patterns(wr_day, wr_pair, wr_hour, failure_cats, prev_state):
    """Compare with previous execution, detect shifts, return discoveries."""
    discoveries = []

    # Compare WR by pair with previous
    prev_wr_pair = prev_state.get("wr_by_pair", {})
    for pair, info in wr_pair.items():
        prev_info = prev_wr_pair.get(pair, {})
        prev_wr = prev_info.get("wr", None)
        curr_wr = info["wr"]
        if prev_wr is not None:
            delta = curr_wr - prev_wr
            if abs(delta) >= 10:
                direction = "improved" if delta > 0 else "declined"
                discoveries.append(
                    {
                        "type": "wr_shift",
                        "detail": f"{pair} WR {direction} from {prev_wr:.1f}% to {curr_wr:.1f}% "
                                  f"({delta:+.1f}%, {info['trades']} trades)",
                        "confidence": min(0.9, abs(delta) / 50),
                    }
                )

    # Compare WR by day
    prev_wr_day = prev_state.get("wr_by_day", {})
    for day, info in wr_day.items():
        prev_info = prev_wr_day.get(day, {})
        prev_wr = prev_info.get("wr", None)
        curr_wr = info["wr"]
        if prev_wr is not None and abs(curr_wr - prev_wr) >= 15:
            direction = "improved" if curr_wr > prev_wr else "declined"
            discoveries.append(
                {
                    "type": "day_performance_shift",
                    "detail": f"{day} WR {direction} {prev_wr:.1f}% → {curr_wr:.1f}% ({info['trades']} trades)",
                    "confidence": 0.6,
                }
            )

    # Compare WR by hour
    prev_wr_hour = prev_state.get("wr_by_hour", {})
    for hour, info in wr_hour.items():
        prev_info = prev_wr_hour.get(hour, {})
        prev_wr = prev_info.get("wr", None)
        curr_wr = info["wr"]
        if prev_wr is not None and abs(curr_wr - prev_wr) >= 15 and info["trades"] >= 3:
            direction = "improved" if curr_wr > prev_wr else "declined"
            discoveries.append(
                {
                    "type": "hour_performance_shift",
                    "detail": f"Hour {hour}:00 WR {direction} {prev_wr:.1f}% → {curr_wr:.1f}% ({info['trades']} trades)",
                    "confidence": 0.55,
                }
            )

    # New or resolved failure categories
    prev_fail_cats = prev_state.get("failure_categories", {})
    for cat, info in failure_cats.items():
        if cat not in prev_fail_cats:
            discoveries.append(
                {
                    "type": "new_failure_pattern",
                    "detail": f"New recurring failure: '{cat}' ({info['count']} occurrences): {info['sample_message'][:120]}",
                    "confidence": 0.7,
                }
            )

    resolved = set(prev_fail_cats.keys()) - set(failure_cats.keys())
    for cat in resolved:
        if prev_fail_cats[cat].get("count", 0) >= 3:
            discoveries.append(
                {
                    "type": "resolved_failure_pattern",
                    "detail": f"Previously recurring failure '{cat}' no longer active",
                    "confidence": 0.5,
                }
            )

    print(f"[hippocampus] Detected {len(discoveries)} pattern changes")
    return discoveries


# ======================================================================
#  EVOLUTION GAPS
# ======================================================================
def detect_evolution_gaps():
    """Detect gaps — what's missing in the trading system that should evolve."""
    gaps = []

    # Check if trade_log has enough data
    if os.path.exists(TRADE_LOG_PATH):
        with open(TRADE_LOG_PATH) as f:
            data = json.load(f)
        trades = data.get("trades", []) if isinstance(data, dict) else data
        if len(trades) < 5:
            gaps.append("Insufficient trade data for robust pattern detection (<5 trades)")

    # Check for missing reference files
    for ref_file, label in [
        ("best_params.json", "Best params reference missing (no seed data)"),
        ("pair_weights_live.json", "Live pair weights file not found"),
    ]:
        ref_path = os.path.join(FOREX_DIR, ref_file)
        if not os.path.exists(ref_path):
            gaps.append(label)

    if gaps:
        print(f"[hippocampus] Evolution gaps detected: {len(gaps)}")
    else:
        print("[hippocampus] No evolution gaps detected.")

    return gaps


# ======================================================================
#  MAIN CONSOLIDATION CYCLE
# ======================================================================
def run():
    """Main consolidation cycle: trade patterns + failure patterns + evolution gaps."""
    print("=" * 60)
    print(f"[hippocampus] Consolidation cycle — {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    prev_state = _load_state()

    # 1. Trade pattern analysis
    wr_day, wr_pair, wr_hour = analyze_trade_log()

    # 2. Failure pattern analysis
    failure_cats = analyze_failures()

    # 3. Pattern detection (comparison with previous)
    discoveries = []
    if wr_pair and wr_day and wr_hour:
        discoveries = detect_patterns(wr_day, wr_pair, wr_hour, failure_cats, prev_state)

    # 4. Evolution gaps
    gaps = detect_evolution_gaps()
    for gap in gaps:
        discoveries.append(
            {"type": "evolution_gap", "detail": gap, "confidence": 0.4}
        )

    # 5. Publish via Tálamo
    if HAS_THALAMUS:
        for disc in discoveries:
            thalamus.add_discovery(
                domain=disc["type"],
                insight=disc["detail"],
                confidence=disc["confidence"],
                source="hippocampus",
            )

        # Update thalamus state with latest patterns
        thalamus.update_state("patterns", {
            "wr_by_day": wr_day,
            "wr_by_pair": wr_pair,
            "wr_by_hour": wr_hour,
            "failure_categories": failure_cats,
        })

        # Log cycle event
        thalamus.log_event(
            event_type="hippocampus_cycle",
            source="hippocampus",
            data={
                "trades_analyzed": sum(v["trades"] for v in wr_pair.values()) if wr_pair else 0,
                "discoveries": len(discoveries),
                "gaps": len(gaps),
                "failure_categories": len(failure_cats),
            },
            severity="info",
        )

        # Broadcast to global workspace
        if discoveries:
            thalamus.broadcast_to_workspace(
                content=f"Hippocampus: {len(discoveries)} new pattern insights consolidated",
                priority=3,
                source="hippocampus",
            )
    else:
        print("[hippocampus] Running standalone — no Tálamo publication.")
        for disc in discoveries:
            print(f"  DISCOVERY [{disc['type']}]: {disc['detail']}")

    # 6. Reinforcement via sona_lite
    if HAS_SONA and discoveries:
        for disc in discoveries:
            sona_lite.record_reward(signal=1.0 if "improved" in disc.get("detail", "") else -0.5,
                                   magnitude=0.05)

    # 7. Save updated state
    new_state = {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "cycle_count": prev_state.get("cycle_count", 0) + 1,
        "wr_by_day": wr_day,
        "wr_by_pair": wr_pair,
        "wr_by_hour": wr_hour,
        "failure_categories": failure_cats,
        "discoveries_published": prev_state.get("discoveries_published", 0) + len(discoveries),
        "evolution_gaps": gaps,
    }
    _save_state(new_state)

    print(f"[hippocampus] Cycle #{new_state['cycle_count']} complete: "
          f"{len(discoveries)} discoveries, {len(gaps)} gaps")
    return {"discoveries": len(discoveries), "gaps": len(gaps), "cycle": new_state["cycle_count"]}


# ======================================================================
#  MAIN
# ======================================================================
if __name__ == "__main__":
    result = run()
    print(f"\n{'─' * 60}")
    print(f"Summary: {result}")
    print(f"State saved to: {HIPPO_STATE_PATH}")
