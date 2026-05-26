#!/usr/bin/env python3
"""
Social Tracker — Rastreia métricas sociais, conversas pendentes, outreach.
Parte do Pilar Mental-Comportamental-Social unificado.
Executar nos lotes 09h e 18h + domingo (auditoria).
"""
import json, os
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path.home() / ".hermes" / "data" / "social"
TRACKER_PATH = BASE / "tracker.json"

def load_tracker():
    if TRACKER_PATH.exists():
        return json.loads(TRACKER_PATH.read_text())
    return {
        "daily_log": {},
        "contacts_state": {},
        "outreach_log": [],
        "groups_monitor": {}
    }

def save_tracker(data):
    BASE.mkdir(parents=True, exist_ok=True)
    TRACKER_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))

def main():
    tracker = load_tracker()
    today = datetime.now().strftime("%Y-%m-%d")
    weekday = datetime.now().weekday()
    
    today_entry = tracker["daily_log"].get(today, {
        "lote_09h_done": False,
        "lote_18h_done": False,
        "clientes_respondidos": 0,
        "clientes_pendentes": 0,
        "familia_respondida": False,
        "outreach_feito": False,
        "grupo_abandonado": False
    })
    
    print("🔗 AUDITORIA SOCIAL\n")
    print(f"Dia: {today} | {'Seg-Sex' if weekday < 5 else 'Fim de semana'}")
    print("-" * 50)
    
    # Lotes
    print("\n📬 LOTES DE RESPOSTA:")
    hora = datetime.now().hour
    lote_manha = 7 <= hora <= 10
    lote_tarde = 17 <= hora <= 20
    
    if lote_manha:
        print("   🌅 LOTE 09h — ABRIR WhatsApp, responder pendências (máx 15 min)")
        print("   ⚠️  Fechar WhatsApp após o lote.")
    elif lote_tarde:
        print("   🌆 LOTE 18h — ABRIR WhatsApp, responder pendências (máx 15 min)")
        print("   ⚠️  Fechar WhatsApp após o lote.")
    else:
        print("   🔒 Fora do horário de lote. WhatsApp deve estar fechado.")
    
    # Pendências
    print(f"\n📊 MÉTRICAS:")
    print(f"   Clientes respondidos hoje: {today_entry.get('clientes_respondidos', 0)}")
    print(f"   Clientes pendentes: {today_entry.get('clientes_pendentes', 0)}")
    print(f"   Família respondida: {'✅' if today_entry.get('familia_respondida') else '⬜'}")
    print(f"   Outreach feito: {'✅' if today_entry.get('outreach_feito') else '⬜'}")
    
    # Outreach semanal (segunda-feira)
    if weekday == 0:
        print(f"\n📞 OUTREACH SEGUNDA-FEIRA:")
        print(f"   Meta: retomar 1 contato abandonado")
        print(f"   Sugestões: Germanio Pai (206d), Mãe TG (565d)")
        print(f"   ⚡ 3-2-1-Go: abrir chat e mandar 'Oi, quanto tempo! Tudo bem?'")
    
    # Grupos (quarta-feira)
    if weekday == 2:
        print(f"\n🧹 FAXINA DE GRUPOS (QUARTA):")
        print(f"   Meta: sair de 1 grupo inativo")
        print(f"   Regra: se não leu nos últimos 30 dias → sair ou silenciar")
    
    # Domingo: auditoria completa
    if weekday == 6:
        print(f"\n{'='*50}")
        print("📅 DOMINGO: AUDITORIA SOCIAL COMPLETA")
        print(f"{'='*50}")
        print("1. Conversas não lidas (meta: <50)")
        print("2. Grupos ativos (meta: <5)")
        print("3. Relações recuperadas este mês (meta: >2)")
        print("4. Planejar outreach da semana")
        print("5. Faxina: arquivar/silenciar conversas mortas")
    
    # Registrar
    tracker["daily_log"][today] = today_entry
    save_tracker(tracker)
    
    print(f"\n✅ Auditoria social registrada")

if __name__ == "__main__":
    main()
