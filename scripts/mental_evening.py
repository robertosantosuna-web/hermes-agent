#!/usr/bin/env python3
"""
Mental Pillar — Evening Protocol (Tiny Habits Mode).
Fase Foundation: vitória do dia + celebration + preparar ambiente.
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
    today_entry = tracker.get(today, {"habits": {}, "thought_check": None, "intention": None, "win": None})
    
    habits = cfg["tiny_habits"]
    night_habits = [h for h in habits if h["time"] == "night"]
    
    print("🌙 PROTOCOLO NOTURNO — Mental Pillar\n")
    print(f"Fase: {cfg['phase']} | Semana {cfg['week']} | {today}")
    print("-" * 40)
    
    for h in night_habits:
        print(f"\n📍 {h['anchor']}")
        print(f"   ⚡ {h['behavior']}")
        print(f"   🎉 {h['celebration']}")
        print(f"   💡 {h['why']}")
    
    # 1 vitória do dia (Outlook + Identity)
    print(f"\n⭐ 1 VITÓRIA DO DIA:")
    print("   O que eu fiz hoje que meu 'eu do futuro' agradeceria?")
    print("   (Pode ser mínimo: 'respirei 3x', 'abri o WhatsApp', 'li 1 página')")
    
    # Habit tracker visual
    print(f"\n📊 HABIT TRACKER HOJE:")
    for h in habits:
        done = today_entry["habits"].get(h["id"], {}).get("done", False)
        mark = "✅" if done else "⬜"
        print(f"   {mark} {h['behavior']} ({h['time']})")
    
    # Celebration explícita
    print(f"\n🎉 CELEBRATION:")
    print("   Escolha 1 coisa — mínima que seja — e comemore.")
    print("   'NICE!' | Sorrir | Levantar o punho | 'Eu fiz isso'")
    print("   (Fogg: este é o passo MAIS importante. Dopamina crava o hábito.)")
    
    # Preparar ambiente
    print(f"\n🔧 PREPARAR AMANHÃ:")
    print("   O que posso deixar pronto agora para amanhã ser fácil?")
    print("   (Roupa separada? Água na mesa? App aberto?)")
    
    # Domingo = Review + Pre-commitment
    if datetime.now().weekday() == 6:  # Sunday
        print(f"\n{'='*40}")
        print("📅 DOMINGO: REVIEW + PRE-COMMITMENT")
        print(f"{'='*40}")
        print("REVIEW: O que funcionou esta semana? O que não funcionou?")
        print("PRE-COMMIT: 'Na próxima semana, eu vou...' (declare publicamente)")
        print("(Cialdini: compromisso declarado = consistência automática)")
    
    # Mark night habits
    for h in night_habits:
        today_entry["habits"][h["id"]] = {"prompted": True, "time": datetime.now().isoformat()}
    
    tracker[today] = today_entry
    save_tracker(tracker)
    
    print(f"\n✅ Check-in noturno registrado")

if __name__ == "__main__":
    main()
