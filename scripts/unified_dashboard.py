#!/usr/bin/env python3
"""
Dashboard Unificado — Mental + Comportamental + Social.
Gera score integrado e visão consolidada dos 3 eixos.
"""
import json, os
from datetime import datetime
from pathlib import Path

MENTAL = Path.home() / ".hermes" / "mental"
TRACKERS = {
    "mental": MENTAL / "tracker.json",
    "behavioral": MENTAL / "behavioral_tracker.json",
    "social": Path.home() / ".hermes" / "data" / "social" / "tracker.json"
}
DASHBOARD_PATH = MENTAL / "unified_dashboard.json"

def load_json(path):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            pass
    return {}

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    
    mental = load_json(TRACKERS["mental"])
    behavioral = load_json(TRACKERS["behavioral"])
    social = load_json(TRACKERS["social"])
    
    # Mental score
    m_today = mental.get(today, {}).get("habits", {})
    m_done = sum(1 for h in m_today.values() if isinstance(h, dict) and h.get("done"))
    m_total = max(len(m_today), 1)
    mental_score = (m_done / m_total) * 10
    
    # Behavioral score
    b_today = behavioral.get("daily_log", {}).get(today, {})
    behavioral_score = b_today.get("score", 10)
    
    # Social score
    s_today = social.get("daily_log", {}).get(today, {})
    social_points = 10
    if not s_today.get("clientes_respondidos"):
        social_points -= 2
    if s_today.get("clientes_pendentes", 0) > 3:
        social_points -= 2
    if not s_today.get("familia_respondida"):
        social_points -= 1
    if s_today.get("lote_09h_done") is False and s_today.get("lote_18h_done") is False:
        social_points -= 2
    social_score = max(0, social_points)
    
    integrated_score = round((mental_score + behavioral_score + social_score) / 3, 1)
    
    dashboard = {
        "date": today,
        "integrated_score": integrated_score,
        "eixos": {
            "mental": {"score": round(mental_score, 1), "habits_done": f"{m_done}/{m_total}"},
            "comportamental": {"score": behavioral_score, "violations": sum(b_today.get("violations", {}).values())},
            "social": {"score": social_score, "clientes_pendentes": s_today.get("clientes_pendentes", 0)}
        },
        "status": (
            "🏆 ELITE" if integrated_score >= 9 else
            "⚡ FORTE" if integrated_score >= 7 else
            "⚠️ ATENÇÃO" if integrated_score >= 5 else
            "🔴 CRÍTICO"
        ),
        "generated": datetime.now().isoformat()
    }
    
    DASHBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_PATH.write_text(json.dumps(dashboard, indent=2, ensure_ascii=False))
    
    print(f"📊 DASHBOARD UNIFICADO — {today}")
    print(f"{'='*40}")
    print(f"Score integrado: {integrated_score}/10 — {dashboard['status']}")
    print(f"  🧠 Mental: {mental_score:.1f} | ⚔️ Comportamental: {behavioral_score} | 🔗 Social: {social_score}")
    print(f"  Hábitos: {m_done}/{m_total} | Violações: {dashboard['eixos']['comportamental']['violations']} | Clientes pendentes: {s_today.get('clientes_pendentes', 0)}")

if __name__ == "__main__":
    main()
