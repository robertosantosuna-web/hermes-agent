#!/usr/bin/env python3
"""Lobo Frontal — Planejador e Priorizador de Tarefas.
Execução: a cada 30 minutos. Lê agenda, coleta tarefas pendentes do Tálamo
e do agent_context, pontua por prioridade (keywords + idade), e publica
o plano diário com top 5 tarefas. Faz broadcast de eventos próximos.

Usa o Tálamo como canal único de publicação.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

# ── path setup ──────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.expanduser("~/.hermes/brain"))
import thalamus

# ── constants ───────────────────────────────────────────────────────────────
PLANNER_SOURCE = "lobo_frontal"
AGENDA_PATH = os.path.expanduser("~/.hermes/brain/agenda.json")
AGENT_CONTEXT_PATH = os.path.expanduser("~/.hermes/forex/agent_context.json")

# Priority keywords (higher score = more urgent)
KEYWORD_PRIORITY = {
    # Urgent / critical
    "urgente": 20, "urgent": 20, "crítico": 20, "critical": 20, "emergência": 20,
    "emergency": 20, "agora": 18, "now": 18, "imediato": 18, "immediate": 18,
    # Forex / trading
    "forex": 15, "trade": 15, "trading": 15, "mercado": 14, "market": 14,
    "sinal": 14, "signal": 14, "entrada": 13, "entry": 13, "posição": 13,
    "position": 13, "stop": 13, "loss": 13, "drawdown": 15, "balance": 15,
    # Freelas
    "freela": 16, "freelance": 16, "freelas": 16, "99freelas": 16, "proposta": 15,
    "proposal": 15, "cliente": 14, "client": 14, "projeto": 13, "project": 13,
    "prazo": 12, "deadline": 12, "entrega": 12, "delivery": 12,
    # System / maintenance
    "bug": 17, "erro": 17, "error": 17, "falha": 17, "crash": 17,
    "fix": 15, "corrigir": 15, "deploy": 14, "atualizar": 12, "update": 12,
    "backup": 13, "backtest": 13, "análise": 11, "analysis": 11,
    # Communication / email
    "email": 12, "telegram": 12, "mensagem": 11, "message": 11,
    # Daily / routine
    "daily": 10, "diário": 10, "rotina": 8, "routine": 8, "revisão": 9, "review": 9,
}

# Age bonus: +1 point per hour of age (capped at +24)
MAX_AGE_BONUS = 24


# ═══════════════════════════════════════════════════════════════════════════════
#  Data gathering
# ═══════════════════════════════════════════════════════════════════════════════

def get_calendar_today() -> dict:
    """Lê ~/.hermes/brain/agenda.json e retorna eventos de hoje + próximos."""
    if not os.path.exists(AGENDA_PATH):
        return {"today": datetime.now().strftime("%Y-%m-%d"), "appointments": [], "upcoming": {}}

    try:
        with open(AGENDA_PATH) as f:
            agenda = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"today": datetime.now().strftime("%Y-%m-%d"), "appointments": [], "upcoming": {}}

    return {
        "today": agenda.get("today", ""),
        "appointments": agenda.get("today_appointments", []),
        "upcoming": agenda.get("upcoming", {}),
        "conflicts": agenda.get("conflicts", []),
        "updated": agenda.get("updated", ""),
    }


def get_pending_tasks() -> list:
    """Coleta tarefas pendentes do Tálamo e de agent_context.json."""
    tasks = []

    # From thalamus
    state = {}
    try:
        state_path = os.path.expanduser("~/.hermes/brain/thalamus.json")
        if os.path.exists(state_path):
            with open(state_path) as f:
                state = json.load(f)
    except (json.JSONDecodeError, OSError):
        pass

    thalamus_tasks = state.get("tasks", [])
    for t in thalamus_tasks:
        if t.get("status") not in ("done", "cancelled", "archived"):
            tasks.append({
                "source": "thalamus",
                "id": t.get("id", "?"),
                "title": t.get("title", t.get("description", str(t.get("payload", ""))[:80])),
                "status": t.get("status", "pending"),
                "created": t.get("created_at") or t.get("timestamp", ""),
                "raw": t,
            })

    # From agent_context.json
    if os.path.exists(AGENT_CONTEXT_PATH):
        try:
            with open(AGENT_CONTEXT_PATH) as f:
                ctx = json.load(f)
            # Collect bugs, recommendations, etc.
            bugs = ctx.get("bugs_found", {})
            for severity in ("critical", "high"):
                for bug in bugs.get(severity, []):
                    tasks.append({
                        "source": "agent_context",
                        "id": f"bug-{severity}",
                        "title": f"[BUG/{severity}] {bug[:100]}",
                        "status": "pending",
                        "created": ctx.get("updated", ""),
                    })
            recs = ctx.get("neo_recommendations_applied", [])
            for rec in recs:
                tasks.append({
                    "source": "agent_context",
                    "id": f"neo-rec-{hash(rec) % 10000}",
                    "title": f"[NEO-REC] {rec[:100]}",
                    "status": "pending",
                    "created": ctx.get("updated", ""),
                })
            summary = ctx.get("session_summary", "")
            if summary:
                tasks.append({
                    "source": "agent_context",
                    "id": "session-summary",
                    "title": f"[SESSION] {summary[:100]}",
                    "status": "pending",
                    "created": ctx.get("updated", ""),
                })
        except (json.JSONDecodeError, OSError):
            pass

    # From thalamus alerts (unacknowledged become tasks)
    alerts = state.get("alerts", [])
    for a in alerts:
        if not a.get("acknowledged"):
            tasks.append({
                "source": "thalamus_alerts",
                "id": a.get("id", "?"),
                "title": f"[ALERT/{a.get('level','?')}] {a.get('title','')}: {a.get('description','')[:60]}",
                "status": "pending",
                "created": a.get("timestamp", ""),
            })

    return tasks


# ═══════════════════════════════════════════════════════════════════════════════
#  Scoring
# ═══════════════════════════════════════════════════════════════════════════════

def score_task(task: dict) -> float:
    """Pontua uma tarefa por keywords no título + idade.
    Score base = soma dos pesos de keywords encontradas.
    Age bonus = +1 por hora de idade, cap em MAX_AGE_BONUS.
    """
    title = (task.get("title") or "").lower()
    score = 0.0
    matched_keywords = []

    for kw, weight in KEYWORD_PRIORITY.items():
        # Use word boundary match to avoid partial matches
        if re.search(r'\b' + re.escape(kw) + r'\b', title):
            score += weight
            matched_keywords.append(kw)

    # Age bonus
    created = task.get("created", "")
    if created:
        try:
            ts = datetime.fromisoformat(created)
            age_hours = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
            score += min(age_hours, MAX_AGE_BONUS)
        except (ValueError, TypeError, OSError):
            pass

    # Source bonus
    source_bonus = {
        "agent_context": 5,   # came from real issues
        "thalamus_alerts": 4,  # unacknowledged alerts need attention
        "thalamus": 0,
    }
    score += source_bonus.get(task.get("source", ""), 0)

    return round(score, 1)


# ═══════════════════════════════════════════════════════════════════════════════
#  Orchestrator
# ═══════════════════════════════════════════════════════════════════════════════

def run() -> dict:
    """Prioriza tarefas, publica daily_plan no Tálamo, e faz broadcast de eventos próximos."""
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")

    # 1. Gather calendar
    calendar = get_calendar_today()

    # 2. Gather tasks
    tasks = get_pending_tasks()

    # 3. Score and sort
    scored = []
    for t in tasks:
        s = score_task(t)
        scored.append({**t, "score": s})

    scored.sort(key=lambda x: -x["score"])
    top5 = scored[:5]

    # 4. Build daily plan
    daily_plan = {
        "date": today_str,
        "generated_at": now.isoformat(),
        "calendar_appointments": calendar.get("appointments", []),
        "calendar_upcoming": calendar.get("upcoming", {}),
        "top_tasks": [
            {
                "rank": i + 1,
                "score": t["score"],
                "source": t["source"],
                "title": t["title"],
                "id": t.get("id"),
            }
            for i, t in enumerate(top5)
        ],
        "total_pending": len(tasks),
    }

    # 5. Publish to thalamus
    thalamus.update_state("daily_plan", daily_plan)

    # 6. Check for near upcoming events (within 2 hours)
    upcoming = calendar.get("upcoming", {})
    near_events = []
    if isinstance(upcoming, dict):
        for date_key, events in upcoming.items():
            if isinstance(events, list):
                for ev in events:
                    ev_time = ev.get("time") or ev.get("start") or ev.get("datetime", "")
                    if ev_time:
                        try:
                            ev_dt = datetime.fromisoformat(ev_time)
                            minutes_away = (ev_dt - now).total_seconds() / 60
                            if 0 <= minutes_away <= 120:
                                near_events.append({**ev, "minutes_away": int(minutes_away)})
                        except (ValueError, TypeError):
                            pass

    # Broadcast near events
    for ev in near_events[:3]:
        thalamus.broadcast_to_workspace(
            content=f"📅 Em {ev['minutes_away']}min: {ev.get('title', ev.get('summary', 'Evento'))}",
            priority=8,
            source=PLANNER_SOURCE,
        )

    # Broadcast daily plan summary
    plan_summary = f"📋 Plano diário ({today_str}): {len(top5)} tasks prioritárias, {len(tasks)} pendentes total"
    if top5:
        plan_summary += f" | Top: {top5[0]['title'][:80]}"
    thalamus.broadcast_to_workspace(
        content=plan_summary,
        priority=6,
        source=PLANNER_SOURCE,
    )

    # Log
    thalamus.log_event(
        event_type="lobo_frontal_plan",
        source=PLANNER_SOURCE,
        data={
            "tasks_total": len(tasks),
            "top5_scores": [t["score"] for t in top5],
            "near_events": len(near_events),
        },
        severity="info",
    )

    return {
        "daily_plan": daily_plan,
        "tasks_scored": len(scored),
        "top5": top5,
        "near_events": near_events,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  LOBO FRONTAL — Planejador e Priorizador")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    result = run()

    plan = result["daily_plan"]
    print(f"\n📅 Data: {plan['date']}")
    print(f"📋 Tarefas pendentes total: {plan['total_pending']}")

    # Calendar
    apps = plan.get("calendar_appointments", [])
    if apps:
        print(f"\n📆 Compromissos hoje ({len(apps)}):")
        for a in apps:
            print(f"   • {a.get('time','?')} — {a.get('title', a.get('summary','?'))}")
    else:
        print(f"\n📆 Sem compromissos hoje.")

    # Top 5 tasks
    print(f"\n🔝 Top 5 tarefas priorizadas:")
    for t in plan["top_tasks"]:
        print(f"   #{t['rank']} [{t['score']:.1f}] [{t['source']}] {t['title'][:90]}")

    # Near events
    near = result.get("near_events", [])
    if near:
        print(f"\n⏰ Eventos próximos (2h):")
        for ev in near:
            print(f"   • Em {ev['minutes_away']}min: {ev.get('title', ev.get('summary', 'Evento'))}")
    else:
        print(f"\n⏰ Nenhum evento nas próximas 2 horas.")

    print(f"\n✅ Plano diário publicado no Tálamo.")
