#!/usr/bin/env python3
"""
MindCoach Motor — Monitoramento Permanente Multi-Dimensão
=========================================================
Bubble de consciência contínua integrada à Rede Neural.
Monitora: Psicológico, Emocional, Social, Financeiro, Comportamental, Saúde.

Arquitetura:
  Fontes → Coletores → Dimensões → Scores → NN-Sinapses → Dashboard
"""

import json, os, sys, time, re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

HERMES = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
MINDCOACH = HERMES / "mindcoach"
DIMENSIONS_DIR = MINDCOACH / "dimensions"
DATA_DIR = MINDCOACH / "data"
REPORTS_DIR = MINDCOACH / "reports"
NN_ENGINE = HERMES / "scripts" / "nn_engine.py"

NOW = lambda: datetime.now(timezone.utc)

DIMENSIONS = {
    "psychological": {
        "name": "Psicológico",
        "icon": "🧠",
        "weight": 1.0,
        "sources": ["email_tone", "message_patterns", "response_latency", "night_activity"],
        "threshold_warn": 0.4,
        "threshold_alert": 0.2
    },
    "emotional": {
        "name": "Emocional",
        "icon": "💙",
        "weight": 1.0,
        "sources": ["sentiment_analysis", "word_choice", "stress_markers", "interaction_frequency"],
        "threshold_warn": 0.4,
        "threshold_alert": 0.2
    },
    "social": {
        "name": "Social",
        "icon": "👥",
        "weight": 0.8,
        "sources": ["contact_frequency", "response_ratio", "isolation_index", "group_engagement"],
        "threshold_warn": 0.5,
        "threshold_alert": 0.3
    },
    "financial": {
        "name": "Financeiro",
        "icon": "💰",
        "weight": 1.2,
        "sources": ["forex_pnl", "freela_revenue", "banking_alerts", "spending_patterns"],
        "threshold_warn": 0.5,
        "threshold_alert": 0.3
    },
    "behavioral": {
        "name": "Comportamental",
        "icon": "⚡",
        "weight": 1.0,
        "sources": ["anti_pattern_violations", "task_completion", "morning_routine", "focus_sessions"],
        "threshold_warn": 0.5,
        "threshold_alert": 0.3
    },
    "health": {
        "name": "Saúde",
        "icon": "🫀",
        "weight": 0.9,
        "sources": ["water_intake", "meal_timing", "sleep_hours", "exercise_minutes"],
        "threshold_warn": 0.4,
        "threshold_alert": 0.2
    }
}


def load_state():
    """Carrega estado atual do MindCoach."""
    state_file = MINDCOACH / "state.json"
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {
        "version": "1.0.0",
        "created": NOW().isoformat(),
        "last_checkpoint": None,
        "checkpoints": [],
        "dimensions": {},
        "overall_score": 0.5,
        "trend": "stable",
        "alerts_active": []
    }


def save_state(state):
    """Salva estado do MindCoach."""
    state["last_checkpoint"] = NOW().isoformat()
    MINDCOACH.mkdir(parents=True, exist_ok=True)
    (MINDCOACH / "state.json").write_text(json.dumps(state, indent=2, ensure_ascii=False))


def collect_email_sentiment():
    """Coleta tom emocional de emails recentes."""
    # Placeholder - integração real via CDP ou IMAP
    return {
        "source": "email",
        "timestamp": NOW().isoformat(),
        "emails_scanned": 0,
        "positive_count": 0,
        "negative_count": 0,
        "neutral_count": 0,
        "avg_sentiment": 0.5,
        "stress_keywords_found": 0
    }


def collect_social_metrics():
    """Coleta métricas sociais."""
    return {
        "source": "social",
        "timestamp": NOW().isoformat(),
        "telegram_active": True,
        "whatsapp_active": True,
        "recent_contacts": 0,
        "unread_messages": 0,
        "response_ratio": 0.5,
        "isolation_score": 0.3  # 0 = isolated, 1 = highly social
    }


def collect_financial_metrics():
    """Coleta métricas financeiras do forex e freelas."""
    # Forex
    forex_pnl = 0.0
    signals_file = HERMES / "forex" / "signals_pending.json"
    if signals_file.exists():
        signals = json.loads(signals_file.read_text())
        forex_pnl = sum(s.get("result_pips", 0) for s in signals.get("executed", []))
    
    return {
        "source": "financial",
        "timestamp": NOW().isoformat(),
        "forex_active": True,
        "forex_pnl_today": forex_pnl,
        "freela_proposals": 0,
        "banking_alerts": 0,
        "revenue_this_month": 0.0
    }


def collect_behavioral_metrics():
    """Coleta métricas comportamentais."""
    # Anti-padrões
    ap_count = 0
    failure_log = HERMES / "failure_log.json"
    if failure_log.exists():
        try:
            logs = json.loads(failure_log.read_text())
            today = NOW().strftime("%Y-%m-%d")
            if isinstance(logs, list):
                ap_count = sum(1 for l in logs if isinstance(l, dict) and l.get("date", "") == today)
            elif isinstance(logs, dict):
                ap_count = len(logs.get("violations", []))
        except:
            pass
    
    return {
        "source": "behavioral",
        "timestamp": NOW().isoformat(),
        "anti_patterns_today": ap_count,
        "max_allowed": 3,
        "tasks_completed": 0,
        "focus_hours": 0,
        "morning_routine_done": False
    }


def collect_health_metrics():
    """Coleta métricas de saúde — integração com Huawei Watch + manual input."""
    health_file = MINDCOACH / "health_data.json"
    metrics = {
        "source": "health",
        "timestamp": NOW().isoformat(),
        "sleep_hours": 0,
        "resting_heart_rate": 0,
        "steps": 0,
        "water_liters": 0,
        "weight_kg": 0,
        "spo2": 0,
        "mood": 5,
        "target_water": 2.5,
        "target_sleep": 7,
        "target_steps": 8000,
    }
    
    if health_file.exists():
        try:
            data = json.loads(health_file.read_text())
            m = data.get("metrics", {})
            metrics["sleep_hours"] = m.get("sleep_hours", 0)
            metrics["resting_heart_rate"] = m.get("resting_heart_rate", 0)
            metrics["steps"] = m.get("steps", 0)
            metrics["water_liters"] = m.get("water_liters", 0)
            metrics["weight_kg"] = m.get("weight_kg", 0)
            metrics["spo2"] = m.get("spo2", 0)
            metrics["mood"] = m.get("mood", 5)
            metrics["source"] = data.get("source", "health")
        except Exception:
            pass
    
    return metrics


def compute_dimension_score(dimension_id, metrics):
    """Calcula score 0-1 para uma dimensão."""
    dim = DIMENSIONS[dimension_id]
    
    if dimension_id == "psychological":
        sentiment = metrics.get("avg_sentiment", 0.5)
        stress = metrics.get("stress_keywords_found", 0)
        score = sentiment * 0.6 + max(0, 1 - stress * 0.1) * 0.4
        return min(1.0, max(0.0, score))
    
    elif dimension_id == "emotional":
        sentiment = metrics.get("avg_sentiment", 0.5)
        return min(1.0, max(0.0, sentiment))
    
    elif dimension_id == "social":
        interaction = metrics.get("response_ratio", 0.5)
        isolation = 1 - metrics.get("isolation_score", 0.3)
        return min(1.0, max(0.0, (interaction + isolation) / 2))
    
    elif dimension_id == "financial":
        pnl = metrics.get("forex_pnl_today", 0)
        pnl_score = 0.5 + min(0.5, max(-0.5, pnl / 50))
        return min(1.0, max(0.0, pnl_score))
    
    elif dimension_id == "behavioral":
        ap = metrics.get("anti_patterns_today", 0)
        max_ap = metrics.get("max_allowed", 3)
        ap_score = max(0, 1 - ap / max_ap)
        return min(1.0, max(0.0, ap_score))
    
    elif dimension_id == "health":
        sleep = metrics.get("sleep_hours", 0) / metrics.get("target_sleep", 7)
        water = metrics.get("water_liters", 0) / metrics.get("target_water", 2.5)
        steps = metrics.get("steps", 0) / metrics.get("target_steps", 8000)
        mood = metrics.get("mood", 5) / 10  # 0-10 scale
        spo2_ok = 1.0 if metrics.get("spo2", 98) >= 95 else 0.5
        return min(1.0, max(0.0, (sleep * 0.3 + water * 0.2 + steps * 0.25 + mood * 0.25) * spo2_ok))
    
    return 0.5


def checkpoint():
    """Executa um checkpoint completo de todas as dimensões."""
    state = load_state()
    
    collectors = {
        "psychological": collect_email_sentiment,
        "emotional": collect_email_sentiment,
        "social": collect_social_metrics,
        "financial": collect_financial_metrics,
        "behavioral": collect_behavioral_metrics,
        "health": collect_health_metrics,
    }
    
    scores = {}
    all_metrics = {}
    
    for dim_id, collector in collectors.items():
        metrics = collector()
        score = compute_dimension_score(dim_id, metrics)
        scores[dim_id] = {
            "score": round(score, 2),
            "metrics": metrics,
            "timestamp": NOW().isoformat(),
            "icon": DIMENSIONS[dim_id]["icon"],
            "name": DIMENSIONS[dim_id]["name"]
        }
        all_metrics[dim_id] = metrics
    
    # Overall score (weighted average)
    total_weight = sum(DIMENSIONS[d]["weight"] for d in DIMENSIONS)
    overall = sum(scores[d]["score"] * DIMENSIONS[d]["weight"] for d in DIMENSIONS) / total_weight
    
    # Trend
    prev_overall = state.get("overall_score", 0.5)
    if overall > prev_overall + 0.05:
        trend = "improving"
    elif overall < prev_overall - 0.05:
        trend = "declining"
    else:
        trend = "stable"
    
    # Alerts
    alerts = []
    for dim_id, s in scores.items():
        dim = DIMENSIONS[dim_id]
        if s["score"] <= dim["threshold_alert"]:
            alerts.append(f"🔴 {dim['icon']} {dim['name']}: {s['score']:.2f} — CRÍTICO")
        elif s["score"] <= dim["threshold_warn"]:
            alerts.append(f"🟡 {dim['icon']} {dim['name']}: {s['score']:.2f} — Atenção")
    
    # Update state
    state["dimensions"] = scores
    state["overall_score"] = round(overall, 2)
    state["trend"] = trend
    state["alerts_active"] = alerts
    
    checkpoint_entry = {
        "timestamp": NOW().isoformat(),
        "overall": round(overall, 2),
        "trend": trend,
        "dimensions": {d: s["score"] for d, s in scores.items()},
        "alerts": len(alerts)
    }
    state["checkpoints"].append(checkpoint_entry)
    if len(state["checkpoints"]) > 168:  # Keep last 7 days (24*7)
        state["checkpoints"] = state["checkpoints"][-168:]
    
    save_state(state)
    
    # Sync with neural network
    sync_to_nn(scores, overall, trend)
    
    return state


def sync_to_nn(scores, overall, trend):
    """Sincroniza scores do MindCoach com a rede neural."""
    import subprocess
    
    # Add/update neurons for each dimension
    for dim_id, s in scores.items():
        dim = DIMENSIONS[dim_id]
        concept = f"mindcoach_{dim_id}"
        subprocess.run([
            "python3", str(NN_ENGINE), "add_neuron",
            "agent", concept
        ], capture_output=True)
        
        # Connect to relevant existing neurons
        domain_map = {
            "psychological": "mental_health",
            "emotional": "mental_health",
            "social": "communication",
            "financial": "forex_trading",
            "behavioral": "error_handling",
            "health": "system_health"
        }
        domain = domain_map.get(dim_id, "learning")
        
        subprocess.run([
            "python3", str(NN_ENGINE), "add_synapse",
            concept, domain, str(s["score"]), "agent"
        ], capture_output=True)
    
    # Learn the overall trend
    subprocess.run([
        "python3", str(NN_ENGINE), "learn", "agent",
        f"MindCoach checkpoint: overall={overall:.2f}, trend={trend}"
    ], capture_output=True)


def report(format="text"):
    """Gera relatório do estado atual."""
    state = load_state()
    
    if format == "json":
        return json.dumps(state, indent=2, ensure_ascii=False)
    
    lines = []
    lines.append("╔══════════════════════════════════════════╗")
    lines.append("║     🧿 MINDCOACH — Status Report         ║")
    lines.append("╠══════════════════════════════════════════╣")
    
    trend_icon = {"improving": "📈", "declining": "📉", "stable": "➡️"}
    lines.append(f"║  Overall: {state['overall_score']:.2f} {trend_icon.get(state['trend'], '➡️')} {state['trend']}")
    lines.append("╠══════════════════════════════════════════╣")
    
    for dim_id, dim in DIMENSIONS.items():
        s = state.get("dimensions", {}).get(dim_id, {})
        score = s.get("score", 0.0) if isinstance(s, dict) else 0.0
        bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
        status = "🟢" if score >= 0.7 else "🟡" if score >= 0.4 else "🔴"
        lines.append(f"║ {dim['icon']} {dim['name']:<16} {status} {bar} {score:.2f}")
    
    lines.append("╠══════════════════════════════════════════╣")
    
    if state.get("alerts_active"):
        lines.append("║  ⚠️  Alertas:")
        for alert in state["alerts_active"][:5]:
            lines.append(f"║    {alert[:55]}")
    else:
        lines.append("║  ✅ Sem alertas ativos")
    
    lines.append("╚══════════════════════════════════════════╝")
    
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: mindcoach.py [checkpoint|report|status]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "checkpoint":
        state = checkpoint()
        print(report())
    elif cmd == "report":
        print(report())
    elif cmd == "status":
        state = load_state()
        print(f"MindCoach v{state['version']}")
        print(f"Checkpoints: {len(state['checkpoints'])}")
        print(f"Último: {state.get('last_checkpoint', 'nunca')}")
        print(f"Overall: {state.get('overall_score', '?')}")
    elif cmd == "json":
        print(report(format="json"))
    else:
        print(f"Comando desconhecido: {cmd}")
