#!/usr/bin/env python3
"""
Mental Pillar — Morning Protocol (Tiny Habits Mode).
Fase Foundation (Semanas 1-2): só âncoras microscópicas. Zero pressão.
"""
import json, os
from datetime import datetime
from pathlib import Path

MENTAL_DIR = Path.home() / ".hermes" / "mental"
CONFIG_PATH = MENTAL_DIR / "config.json"
TRACKER_PATH = MENTAL_DIR / "tracker.json"

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def load_tracker():
    if TRACKER_PATH.exists():
        with open(TRACKER_PATH) as f:
            return json.load(f)
    return {}

def save_tracker(data):
    MENTAL_DIR.mkdir(parents=True, exist_ok=True)
    with open(TRACKER_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    cfg = load_config()
    tracker = load_tracker()
    today = datetime.now().strftime("%Y-%m-%d")
    today_entry = tracker.get(today, {"habits": {}, "thought_check": None, "intention": None})
    
    habits = cfg["tiny_habits"]
    morning_habits = [h for h in habits if h["time"] == "morning"]
    
    print("🌅 PROTOCOLO MATINAL — Mental Pillar\n")
    print(f"Fase: {cfg['phase']} | Semana {cfg['week']} | {today}")
    print("-" * 40)
    
    for h in morning_habits:
        print(f"\n📍 {h['anchor']}")
        print(f"   ⚡ {h['behavior']}")
        print(f"   🎉 {h['celebration']}")
        print(f"   💡 {h['why']}")
    
    # Thought check (CBT lite)
    print(f"\n🧠 THOUGHT CHECK:")
    print("   1. Algum pensamento automático negativo agora?")
    print("   2. Qual distorção cognitiva se aplica?")
    print("      (Tudo-ou-Nada | Catastrofização | Rotulação | Adivinhação | Deveria | etc)")
    print("   3. Evidência contrária?")
    
    # Intention
    print(f"\n🎯 INTENÇÃO DO DIA:")
    print("   'Hoje eu escolho focar em...' (1 frase)")
    
    # Mark habits as prompted
    for h in morning_habits:
        today_entry["habits"][h["id"]] = {"prompted": True, "time": datetime.now().isoformat()}
    
    tracker[today] = today_entry
    save_tracker(tracker)
    
    print(f"\n✅ Check-in matinal registrado")

if __name__ == "__main__":
    main()
