#!/usr/bin/env python3
"""META_OBSERVER — Self-Observation Engine (every 15min).
Monitors system health, calculates confidence by domain,
delegates decisions, detects anomalies, and estimates Phi (integration).

Integrates with:
  - thalamus: event inspection, meta_cognition, consciousness_phi
  - sona_lite: reinforcement of self-model weights
  - working_memory: recent observations and decisions
"""

import json
import os
import sys
import time as _time
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# --- Imports with graceful fallback -----------------------------------
try:
    import thalamus
    HAS_THALAMUS = True
except ImportError:
    HAS_THALAMUS = False
    print("[meta_observer] WARNING: thalamus module not found — running standalone.")

try:
    import sona_lite
    HAS_SONA = True
except ImportError:
    HAS_SONA = False
    print("[meta_observer] WARNING: sona_lite module not found — reinforcement disabled.")

try:
    import working_memory
    HAS_WM = True
except ImportError:
    HAS_WM = False
    print("[meta_observer] WARNING: working_memory module not found — limited context.")

# --- Paths -----------------------------------------------------------
META_STATE_PATH = os.path.expanduser("~/.hermes/brain/meta_state.json")


# ======================================================================
#  STATE MANAGEMENT
# ======================================================================
def _load_state():
    if os.path.exists(META_STATE_PATH):
        with open(META_STATE_PATH) as f:
            return json.load(f)
    return {
        "self_model": {"confidence_by_domain": {}, "overall_confidence": 0.5},
        "observation_history": [],
        "phi_history": [],
        "last_run": None,
        "cycle_count": 0,
    }


def _save_state(state):
    os.makedirs(os.path.dirname(META_STATE_PATH), exist_ok=True)
    with open(META_STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, default=str)


# ======================================================================
#  SUCCESS RATE CALCULATION
# ======================================================================
def observe_cycle():
    """Calculate success_rate from recent events in thalamus.

    Returns:
        dict with:
          - overall_success_rate: ratio of non-error events
          - confidence_by_domain: per-domain confidence estimates
          - recent_events_count: total events analyzed
    """
    confidence_by_domain = defaultdict(lambda: {"info": 0, "warning": 0, "error": 0, "total": 0})

    if HAS_THALAMUS:
        events = thalamus.get_recent_events(hours=4)
    else:
        events = []

    if not events:
        print("[meta_observer] No recent events found — using defaults.")
        return {
            "overall_success_rate": 0.5,
            "confidence_by_domain": {},
            "recent_events_count": 0,
        }

    for event in events:
        source = event.get("source", "unknown")
        severity = event.get("severity", "info")
        confidence_by_domain[source]["total"] += 1
        confidence_by_domain[source][severity] = (
            confidence_by_domain[source].get(severity, 0) + 1
        )

    # Calculate per-domain confidence: % of non-error, non-warning events
    domain_confidence = {}
    total_info = 0
    total_warn = 0
    total_error = 0
    total_all = 0

    for domain, stats in confidence_by_domain.items():
        total = stats["total"]
        errors = stats.get("error", 0)
        warnings = stats.get("warning", 0)
        # Confidence = proportion of clean (info) events, penalized by errors
        if total > 0:
            raw_conf = (stats.get("info", 0) / total)
            # Penalize errors more heavily than warnings
            penalty = (errors * 0.3 + warnings * 0.1) / total
            conf = max(0.05, raw_conf - penalty)
        else:
            conf = 0.5

        domain_confidence[domain] = round(conf, 3)
        total_info += stats.get("info", 0)
        total_warn += stats.get("warning", 0)
        total_error += stats.get("error", 0)
        total_all += total

    # Overall success rate
    if total_all > 0:
        overall = (total_info + total_warn * 0.5) / total_all
    else:
        overall = 0.5

    print(f"[meta_observer] Analyzed {total_all} events from {len(domain_confidence)} domains")
    print(f"  Info: {total_info}, Warning: {total_warn}, Error: {total_error}")
    print(f"  Overall success rate: {overall:.3f}")

    for domain, conf in sorted(domain_confidence.items(), key=lambda x: -x[1]):
        stats = confidence_by_domain[domain]
        print(f"    {domain:20s}: confidence={conf:.3f} "
              f"(total={stats['total']}, err={stats.get('error', 0)}, warn={stats.get('warning', 0)})")

    return {
        "overall_success_rate": round(overall, 3),
        "confidence_by_domain": domain_confidence,
        "recent_events_count": total_all,
    }


# ======================================================================
#  DELEGATION LOGIC
# ======================================================================
def should_delegate(domain, confidence_by_domain=None):
    """Determine action for a domain based on confidence level.

    Thresholds:
      confidence < 0.3  → DELEGATE (don't execute, pass to external)
      confidence < 0.6  → CONSULT   (ask before executing)
      confidence >= 0.6 → EXECUTE   (autonomous execution)

    Returns: str — 'delegate', 'consult', or 'execute'
    """
    if confidence_by_domain is None:
        confidence = 0.5  # default
    else:
        confidence = confidence_by_domain.get(domain, 0.5)

    if confidence < 0.3:
        return "delegate"
    elif confidence < 0.6:
        return "consult"
    else:
        return "execute"


# ======================================================================
#  ANOMALY DETECTION
# ======================================================================
def detect_anomalies():
    """Detect anomalies: error events in last 30min, failure patterns.

    Returns:
        list of anomaly dicts with: type, description, severity, evidence
    """
    anomalies = []

    if not HAS_THALAMUS:
        print("[meta_observer] No thalamus — skipping anomaly detection.")
        return anomalies

    # Get events from last 30 minutes
    cutoff = _time.time() - 1800  # 30 min
    all_events = thalamus.get_recent_events(hours=1)  # get 1h to be safe

    error_events = []
    warning_events = []
    for event in all_events:
        ts = datetime.fromisoformat(event["timestamp"]).timestamp()
        if ts >= cutoff:
            if event.get("severity") == "error":
                error_events.append(event)
            elif event.get("severity") == "warning":
                warning_events.append(event)

    # Anomaly: > 3 errors in 30 minutes
    if len(error_events) >= 3:
        sources = [e.get("source", "?") for e in error_events]
        anomalies.append({
            "type": "error_spike",
            "description": f"{len(error_events)} errors in last 30min from: {', '.join(set(sources))}",
            "severity": "critical",
            "evidence": len(error_events),
        })

    # Anomaly: errors from a single source repeating
    source_errors = defaultdict(list)
    for e in error_events:
        source_errors[e.get("source", "unknown")].append(e)
    for source, errs in source_errors.items():
        if len(errs) >= 2:
            anomalies.append({
                "type": "source_error_cluster",
                "description": f"Source '{source}' has {len(errs)} errors in 30min",
                "severity": "high",
                "evidence": [e.get("data", "") for e in errs],
            })

    # Anomaly: warning spike
    if len(warning_events) >= 5:
        anomalies.append({
            "type": "warning_spike",
            "description": f"{len(warning_events)} warnings in last 30min",
            "severity": "medium",
            "evidence": len(warning_events),
        })

    if anomalies:
        print(f"[meta_observer] Detected {len(anomalies)} anomalies:")
        for a in anomalies:
            print(f"  [{a['severity'].upper()}] {a['type']}: {a['description']}")
    else:
        print("[meta_observer] No anomalies detected.")

    return anomalies


# ======================================================================
#  PHI CALCULATION (Integration Estimate)
# ======================================================================
def calculate_phi(confidence_by_domain=None):
    """Estimate Phi (integration/consciousness measure).

    Simplified formula:
      Phi ≈ active_modules × avg_confidence

    Where:
      - active_modules: count of modules active in last hour
      - avg_confidence: mean of per-domain confidences

    Returns:
        float: Phi estimate (0.0 - N.0, higher = more integrated)
    """
    if not HAS_THALAMUS:
        return 0.0

    # Count active modules (sources in last 1h events)
    events = thalamus.get_recent_events(hours=1)
    active_sources = set()
    for event in events:
        source = event.get("source", "unknown")
        if source != "unknown":
            active_sources.add(source)

    active_modules = len(active_sources)
    if active_modules == 0:
        active_modules = 1  # at least self

    # Average confidence across domains
    if confidence_by_domain:
        confidences = list(confidence_by_domain.values())
        avg_confidence = sum(confidences) / len(confidences)
    else:
        avg_confidence = 0.5

    phi = active_modules * avg_confidence

    print(f"[meta_observer] Phi estimate: {phi:.3f} "
          f"(modules={active_modules}, avg_conf={avg_confidence:.3f})")

    return round(phi, 3)


# ======================================================================
#  MAIN OBSERVATION CYCLE
# ======================================================================
def run():
    """Main self-observation cycle."""
    print("=" * 60)
    print(f"[meta_observer] Self-observation cycle — {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    prev_state = _load_state()

    # 1. Observe cycle — calculate success rate / domain confidence
    obs = observe_cycle()
    confidence_by_domain = obs["confidence_by_domain"]
    overall_success = obs["overall_success_rate"]

    # 2. Update self_model
    prev_self_model = prev_state.get("self_model", {})
    prev_domain_conf = prev_self_model.get("confidence_by_domain", {})

    # Merge new confidences with old (EMA-like)
    updated_domain_conf = {}
    for domain, new_conf in confidence_by_domain.items():
        old_conf = prev_domain_conf.get(domain, new_conf)
        # SMA-like merge with 0.3 weight on new
        updated_domain_conf[domain] = round(old_conf * 0.7 + new_conf * 0.3, 3)

    # Keep domains from previous that weren't seen now (decay them)
    for domain, old_conf in prev_domain_conf.items():
        if domain not in updated_domain_conf:
            updated_domain_conf[domain] = round(old_conf * 0.95, 3)  # decay

    new_self_model = {
        "confidence_by_domain": updated_domain_conf,
        "overall_confidence": round(overall_success, 3),
        "domains_tracked": len(updated_domain_conf),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    # 3. Delegate check — for each tracked domain
    delegation_decisions = {}
    for domain in updated_domain_conf:
        action = should_delegate(domain, updated_domain_conf)
        if action != "execute":  # only log non-trivial decisions
            delegation_decisions[domain] = action

    if delegation_decisions:
        print(f"[meta_observer] Delegation decisions:")
        for domain, action in delegation_decisions.items():
            print(f"  {domain}: {action.upper()} (conf={updated_domain_conf[domain]:.3f})")

    # 4. Anomaly detection
    anomalies = detect_anomalies()

    # 5. Phi calculation
    phi = calculate_phi(updated_domain_conf)

    # 6. Publish to thalamus
    if HAS_THALAMUS:
        # Update meta_cognition
        meta_cog = {
            "confidence": overall_success,
            "self_model": new_self_model,
            "phi": phi,
            "anomalies_detected": len(anomalies),
            "delegation_decisions": delegation_decisions,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        # Directly write to state (thalamus.update_state replaces one key)
        thalamus.update_state("consciousness_phi", phi)

        # Update the full meta_cognition structure
        # We need to load/save manually since thalamus replaces the whole key
        state = thalamus._load()
        state["meta_cognition"] = meta_cog
        thalamus._save(state)

        # Log cycle event
        thalamus.log_event(
            event_type="meta_observer_cycle",
            source="meta_observer",
            data={
                "phi": phi,
                "overall_confidence": overall_success,
                "domains_tracked": len(updated_domain_conf),
                "anomalies": len(anomalies),
                "delegations": len(delegation_decisions),
            },
            severity="info",
        )

        # Raise alert for critical anomalies
        for anomaly in anomalies:
            if anomaly["severity"] in ("critical", "high"):
                thalamus.raise_alert(
                    level="critical" if anomaly["severity"] == "critical" else "warning",
                    title=f"Meta Observer: {anomaly['type']}",
                    description=anomaly["description"],
                    source="meta_observer",
                )

        # Broadcast if significant change
        prev_phi = prev_state.get("phi_history", [])
        if prev_phi:
            last_phi = prev_phi[-1] if isinstance(prev_phi[-1], (int, float)) else prev_phi[-1].get("value", 0)
            if abs(phi - last_phi) > 1.0:
                direction = "↑" if phi > last_phi else "↓"
                thalamus.broadcast_to_workspace(
                    content=f"Meta: Phi {direction} {last_phi:.2f} → {phi:.2f}",
                    priority=2,
                    source="meta_observer",
                )
    else:
        print("[meta_observer] Running standalone — no Tálamo publication.")

    # 7. Reinforcement via sona_lite
    if HAS_SONA:
        # Reinforce self-model confidence
        sona_lite.adjust_weight(
            key="self:overall_confidence",
            new_value=overall_success,
        )
        for domain, conf in updated_domain_conf.items():
            sona_lite.adjust_weight(
                key=f"self:{domain}",
                new_value=conf,
            )

    # 8. Store in working memory
    if HAS_WM:
        working_memory.store_observation(
            domain="meta",
            data={
                "phi": phi,
                "overall_confidence": overall_success,
                "anomalies": len(anomalies),
            },
            ttl=3600,
        )

    # 9. Save state
    phi_entry = {"value": phi, "timestamp": datetime.now(timezone.utc).isoformat()}
    phi_history = prev_state.get("phi_history", [])
    phi_history.append(phi_entry)
    if len(phi_history) > 200:
        phi_history = phi_history[-200:]

    new_state = {
        "self_model": new_self_model,
        "last_run": datetime.now(timezone.utc).isoformat(),
        "cycle_count": prev_state.get("cycle_count", 0) + 1,
        "phi_history": phi_history,
        "last_phi": phi,
        "last_anomalies": len(anomalies),
        "delegation_decisions": delegation_decisions,
    }
    _save_state(new_state)

    summary = {
        "phi": phi,
        "confidence": overall_success,
        "domains": len(updated_domain_conf),
        "anomalies": len(anomalies),
        "delegations": len(delegation_decisions),
    }
    print(f"\n[meta_observer] Cycle complete: {summary}")
    return summary


# ======================================================================
#  MAIN
# ======================================================================
if __name__ == "__main__":
    result = run()
    print(f"\n{'─' * 60}")
    print(f"Summary: {json.dumps(result, indent=2)}")
    print(f"State saved to: {META_STATE_PATH}")
