#!/usr/bin/env python3
"""Amígdala — Detector de Ameaças e Urgências.
Execução: a cada 5 minutos. Monitora MT5 health, balance drawdown,
erros recentes e failure_log por pendências críticas.

Usa o Tálamo como canal único de alerta e broadcast.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

# ── path setup ──────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.expanduser("~/.hermes/brain"))
import thalamus

# ── constants ───────────────────────────────────────────────────────────────
MT5_STATE_PATH = os.path.expanduser("~/.hermes/forex/mt5_state.json")
FAILURE_LOG_PATH = os.path.expanduser("~/.hermes/failure_log.json")
ALERT_SOURCE = "amygdala"
MAX_MT5_AGE_S = 300          # 5 minutes
ERROR_SEVERITY_THRESHOLD = {"critical", "error", "high"}
CRITICAL_DRAWDOWN_PCT = 10.0
WARNING_DRAWDOWN_PCT = 5.0


# ═══════════════════════════════════════════════════════════════════════════════
#  Checks
# ═══════════════════════════════════════════════════════════════════════════════

def check_mt5_health() -> dict:
    """Lê mt5_state.json e verifica se o age é < MAX_MT5_AGE_S."""
    result = {"healthy": True, "age_s": None, "detail": ""}
    if not os.path.exists(MT5_STATE_PATH):
        result["healthy"] = False
        result["detail"] = "mt5_state.json not found"
        return result

    try:
        with open(MT5_STATE_PATH) as f:
            state = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        result["healthy"] = False
        result["detail"] = f"Failed to parse mt5_state.json: {e}"
        return result

    # Determine age — try 'updated', 'timestamp', or 'last_update' fields
    ts_str = state.get("updated") or state.get("timestamp") or state.get("last_update")
    if not ts_str:
        result["healthy"] = False
        result["detail"] = "No timestamp field found in mt5_state.json (checked: updated, timestamp, last_update)"
        return result

    try:
        ts = datetime.fromisoformat(ts_str)
    except ValueError:
        result["healthy"] = False
        result["detail"] = f"Unparseable timestamp: {ts_str}"
        return result

    age_s = (datetime.now(timezone.utc) - ts).total_seconds()
    result["age_s"] = age_s
    if age_s > MAX_MT5_AGE_S:
        result["healthy"] = False
        result["detail"] = f"MT5 state stale: {age_s:.0f}s old (max {MAX_MT5_AGE_S}s)"
    else:
        result["detail"] = f"MT5 state fresh ({age_s:.0f}s)"

    return result


def check_balance() -> dict:
    """Calcula drawdown a partir do balance disponível no mt5_state.json ou thalamus state."""
    result = {"drawdown_pct": 0.0, "balance": None, "initial_balance": None, "alert": None}

    # Try mt5_state.json first
    if os.path.exists(MT5_STATE_PATH):
        try:
            with open(MT5_STATE_PATH) as f:
                state = json.load(f)
            current = state.get("balance") or state.get("equity")
            initial = state.get("initial_balance") or state.get("starting_balance")
        except (json.JSONDecodeError, OSError):
            current, initial = None, None
    else:
        current, initial = None, None

    # Fallback: try thalamus state
    if current is None:
        thalamus_balance = thalamus.get_state("balance")
        if isinstance(thalamus_balance, dict):
            current = thalamus_balance.get("current") or thalamus_balance.get("equity")
            initial = thalamus_balance.get("initial") or thalamus_balance.get("starting")
        elif isinstance(thalamus_balance, (int, float)):
            current = thalamus_balance
            initial = thalamus.get_state("initial_balance")

    if current is None or initial is None or initial == 0:
        result["detail"] = "Insufficient balance data"
        return result

    result["balance"] = float(current)
    result["initial_balance"] = float(initial)
    result["drawdown_pct"] = round(((float(initial) - float(current)) / float(initial)) * 100, 2)

    if result["drawdown_pct"] >= CRITICAL_DRAWDOWN_PCT:
        result["alert"] = "critical"
    elif result["drawdown_pct"] >= WARNING_DRAWDOWN_PCT:
        result["alert"] = "warning"

    return result


def check_recent_errors() -> list:
    """Busca eventos de erro na última hora via thalamus.get_recent_events()."""
    events = thalamus.get_recent_events(hours=1)
    errors = []
    for e in events:
        sev = (e.get("severity") or "").lower()
        etype = (e.get("type") or "").lower()
        if sev in ERROR_SEVERITY_THRESHOLD or etype in ERROR_SEVERITY_THRESHOLD:
            errors.append(e)
    # Also check for error patterns in event data
    for e in events:
        data = e.get("data", "")
        if isinstance(data, str) and "error" in data.lower():
            if e not in errors:
                errors.append(e)
    return errors


def check_failure_log() -> list:
    """Lê failure_log.json e retorna falhas com status 'pending'."""
    if not os.path.exists(FAILURE_LOG_PATH):
        return []

    try:
        with open(FAILURE_LOG_PATH) as f:
            log = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    failures = log.get("failures", [])
    pending = [f for f in failures if f.get("status") == "pending"]
    return pending


# ═══════════════════════════════════════════════════════════════════════════════
#  Orchestrator
# ═══════════════════════════════════════════════════════════════════════════════

def run() -> dict:
    """Executa todos os checks, levanta alertas, e publica no workspace."""
    threats = []
    active_alerts = []

    # 1. MT5 health
    mt5 = check_mt5_health()
    if not mt5["healthy"]:
        threats.append(f"MT5_UNHEALTHY: {mt5['detail']}")
        thalamus.raise_alert(
            level="critical",
            title="MT5 Connection Stale",
            description=mt5["detail"],
            source=ALERT_SOURCE,
        )
        active_alerts.append("mt5_stale")
        thalamus.broadcast_to_workspace(
            content=f"⚠️ CRÍTICO: MT5 offline — {mt5['detail']}",
            priority=10,
            source=ALERT_SOURCE,
        )

    # 2. Balance drawdown
    bal = check_balance()
    if bal["alert"] == "critical":
        threats.append(f"DRAWDOWN_CRITICAL: {bal['drawdown_pct']}% (${bal['balance']} / ${bal['initial_balance']})")
        thalamus.raise_alert(
            level="critical",
            title=f"Drawdown Crítico: {bal['drawdown_pct']}%",
            description=f"Balance ${bal['balance']} vs initial ${bal['initial_balance']}",
            source=ALERT_SOURCE,
        )
        active_alerts.append("drawdown_critical")
        thalamus.broadcast_to_workspace(
            content=f"🚨 CRÍTICO: Drawdown {bal['drawdown_pct']}% — Circuit breaker deve ser acionado!",
            priority=10,
            source=ALERT_SOURCE,
        )
    elif bal["alert"] == "warning":
        threats.append(f"DRAWDOWN_WARNING: {bal['drawdown_pct']}%")
        thalamus.raise_alert(
            level="warning",
            title=f"Drawdown Atenção: {bal['drawdown_pct']}%",
            description=f"Balance ${bal['balance']} vs initial ${bal['initial_balance']}",
            source=ALERT_SOURCE,
        )
        active_alerts.append("drawdown_warning")

    # 3. Recent errors
    errors = check_recent_errors()
    if errors:
        error_summary = "; ".join(
            f"[{e.get('type', '?')}] {str(e.get('data', ''))[:80]}"
            for e in errors[:5]
        )
        threats.append(f"RECENT_ERRORS: {len(errors)} in last hour")
        thalamus.raise_alert(
            level="warning",
            title=f"{len(errors)} Recent Errors",
            description=error_summary[:200],
            source=ALERT_SOURCE,
        )
        active_alerts.append("recent_errors")
        if len(errors) >= 3:
            thalamus.broadcast_to_workspace(
                content=f"⚠️ {len(errors)} erros na última hora — investigar: {error_summary[:120]}",
                priority=7,
                source=ALERT_SOURCE,
            )

    # 4. Pending failures
    pending = check_failure_log()
    if pending:
        pend_summary = "; ".join(
            f"#{f['id']}: {f.get('error','?')[:60]}"
            for f in pending
        )
        threats.append(f"PENDING_FAILURES: {len(pending)} unresolved")
        thalamus.raise_alert(
            level="warning",
            title=f"{len(pending)} Unresolved Failures",
            description=pend_summary[:200],
            source=ALERT_SOURCE,
        )
        active_alerts.append("pending_failures")

    # 5. Update thalamus state
    threat_count = len(threats)
    thalamus.update_state("threats_active", threat_count)
    thalamus.log_event(
        event_type="amygdala_scan",
        source=ALERT_SOURCE,
        data={
            "threats": threats,
            "mt5_healthy": mt5["healthy"],
            "drawdown_pct": bal.get("drawdown_pct", 0),
            "error_count": len(errors),
            "pending_failures": len(pending),
        },
        severity="critical" if threat_count > 2 else ("warning" if threat_count > 0 else "info"),
    )

    return {
        "threats": threats,
        "active_alerts": active_alerts,
        "mt5": mt5,
        "balance": bal,
        "recent_errors": len(errors),
        "pending_failures": len(pending),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  AMÍGDALA — Detector de Ameaças")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    result = run()

    print(f"\n📊 Resumo:")
    print(f"   Ameaças ativas: {len(result['threats'])}")
    for t in result["threats"]:
        print(f"     ⚡ {t}")

    print(f"\n🔧 MT5 Health: {'✅' if result['mt5']['healthy'] else '❌'} {result['mt5']['detail']}")
    print(f"💰 Drawdown: {result['balance'].get('drawdown_pct', 'N/A')}%")
    print(f"🐛 Erros recentes (1h): {result['recent_errors']}")
    print(f"📋 Pendências failure_log: {result['pending_failures']}")

    if result["active_alerts"]:
        print(f"\n🚨 Alertas disparados: {result['active_alerts']}")
    else:
        print(f"\n✅ Nenhum alerta — tudo dentro do normal.")
