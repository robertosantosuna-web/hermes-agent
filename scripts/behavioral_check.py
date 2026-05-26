#!/usr/bin/env python3
"""
Behavioral Tracker — Rastreia anti-padrões, hesitação, erros repetidos.
Parte do Pilar Mental-Comportamental-Social unificado.
"""
import json, os
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path.home() / ".hermes" / "mental"
TRACKER_PATH = BASE / "behavioral_tracker.json"
FAILURE_LOG = Path.home() / ".hermes" / "failure_log.json"

ANTI_PATTERNS = {
    "AP-1": "Pedir autorização repetida",
    "AP-2": "Repetir abordagem que falhou",
    "AP-3": "Adivinhar URLs",
    "AP-4": "Mencionar valor/prazo em propostas",
    "AP-5": "Desenvolver features antes de renda",
    "AP-6": "Gastar tokens sem retorno",
    "AP-7": "Comunicação com ruído",
    "AP-9": "Confiar em valor hardcoded",
    "AP-10": "Navegação cega sem confirmação",
    "AP-11": "Comandos perigosos sem detecção",
    "AP-12": "Código Python sem validação",
    "AP-13": "Perder contexto entre sessões"
}

def load_tracker():
    if TRACKER_PATH.exists():
        return json.loads(TRACKER_PATH.read_text())
    return {"daily_log": {}, "streaks": {}, "totals": {"violations": 0, "errors_repeated": 0}}

def load_failure_log():
    if FAILURE_LOG.exists():
        try:
            return json.loads(FAILURE_LOG.read_text())
        except:
            pass
    return []

def save_tracker(data):
    BASE.mkdir(parents=True, exist_ok=True)
    TRACKER_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))

def main():
    tracker = load_tracker()
    failures = load_failure_log()
    today = datetime.now().strftime("%Y-%m-%d")
    
    today_entry = tracker["daily_log"].get(today, {
        "violations": {},
        "hesitations": 0,
        "errors_repeated": 0,
        "decisions_instant": 0,
        "decisions_total": 0,
        "score": 10
    })
    
    print("⚔️  AUDITORIA COMPORTAMENTAL — Anti-Padrões\n")
    print(f"Dia: {today} | Score inicial: {today_entry.get('score', 10)}/10")
    print("-" * 50)
    
    # Checklist de anti-padrões
    print("\n📋 Checklist de violações hoje:")
    for ap_id, desc in ANTI_PATTERNS.items():
        count = today_entry["violations"].get(ap_id, 0)
        mark = "🔴" if count > 0 else "✅"
        extra = f" (x{count})" if count > 0 else ""
        print(f"   {mark} {ap_id}: {desc}{extra}")
    
    # Hesitação
    print(f"\n⏱️  Hesitações registradas hoje: {today_entry.get('hesitations', 0)}")
    print(f"   Decisões instantâneas: {today_entry.get('decisions_instant', 0)}/{today_entry.get('decisions_total', 1)}")
    if today_entry.get('decisions_total', 0) > 0:
        pct = today_entry['decisions_instant'] / max(today_entry['decisions_total'], 1) * 100
        print(f"   Taxa: {pct:.0f}% (alvo: >80%)")
    
    # Erros repetidos (do failure_log)
    print(f"\n🔄 Erros repetidos esta semana:")
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    recent_failures = [f for f in failures if isinstance(f, dict) and f.get("date", "0") >= week_ago[:10]]
    repeated = {}
    for f in recent_failures:
        key = f.get("error", "")[:60]
        repeated[key] = repeated.get(key, 0) + 1
    for err, count in repeated.items():
        if count > 1:
            print(f"   🔴 Repetido {count}x: {err}")
    if not any(c > 1 for c in repeated.values()):
        print(f"   ✅ Nenhum erro repetido")
    
    # General Orders check
    print(f"\n🫡 GENERAL ORDERS (7 regras inegociáveis):")
    orders = [
        "1. Tomo decisão em <5 segundos ou uso 3-2-1-Go",
        "2. Nunca peço autorização para ação já liberada",
        "3. Resultado primeiro, explicação depois (ou nunca)",
        "4. Corrigido 1x = permanente. Não repito erro.",
        "5. Toda ação tem métrica financeira ou é descartada",
        "6. Antecipo o próximo passo sem esperar comando",
        "7. Se hesito, ajo. Se erro, corrijo. Se corrijo, sigo."
    ]
    for o in orders:
        print(f"   {o}")
    
    # Score final
    violations_today = sum(today_entry["violations"].values())
    score = max(0, 10 - violations_today - today_entry.get("errors_repeated", 0) * 2)
    today_entry["score"] = score
    
    tracker["daily_log"][today] = today_entry
    tracker["totals"]["violations"] = tracker["totals"].get("violations", 0) + violations_today
    save_tracker(tracker)
    
    print(f"\n{'='*50}")
    print(f"📊 SCORE COMPORTAMENTAL HOJE: {score}/10")
    if score >= 9:
        print("🏆 Elite. Disciplina de aço.")
    elif score >= 7:
        print("⚡ Bom. Pequenos ajustes.")
    elif score >= 5:
        print("⚠️  Atenção. Violações acumulando.")
    else:
        print("🔴 Crítico. Revisar General Orders imediatamente.")

if __name__ == "__main__":
    main()
