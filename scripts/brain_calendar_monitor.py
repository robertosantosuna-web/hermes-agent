#!/usr/bin/python3
"""
Brain Calendar Monitor — Agenda e Compromissos (no_agent, zero tokens).
Fontes: WhatsApp CDP, Telegram, Google Calendar (quando auth pronto).
Output: ~/.hermes/brain/agenda.json + alertas no KB.
"""
import json, os, re, subprocess, urllib.request, time
from datetime import datetime, timedelta, date
from pathlib import Path
from collections import defaultdict

BRAIN_DIR = Path.home() / ".hermes" / "brain"
AGENDA_PATH = BRAIN_DIR / "agenda.json"
KB_PATH = Path.home() / ".hermes" / "forex" / "knowledge_bridge.json"
WHATSAPP_CDP = "http://localhost:9224"

# ─── UTILS ────────────────────────────────────

def cdp_command(method, params=None, tab_url_filter="whatsapp"):
    """Envia comando CDP para o Edge WhatsApp."""
    try:
        # Get tabs
        resp = urllib.request.urlopen(f"{WHATSAPP_CDP}/json", timeout=5)
        tabs = json.loads(resp.read())
        wa_tab = None
        for t in tabs:
            if tab_url_filter in t.get("url", "").lower():
                wa_tab = t
                break
        if not wa_tab:
            return None
        
        ws_url = wa_tab["webSocketDebuggerUrl"]
        # REST não suporta WebSocket nativo. Usar HTTP CDP endpoint.
        payload = json.dumps({"method": method, "params": params or {}}).encode()
        req = urllib.request.Request(
            f"{WHATSAPP_CDP}/cdp/{wa_tab['id']}",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())
    except Exception as e:
        return None

def extract_dates_from_text(text):
    """Extrai menções de datas/horários de texto natural."""
    today = date.today()
    found = []
    
    patterns = [
        # "amanhã às 14h"
        (r'amanh[ãaã]\s+(às?\s+)?(\d{1,2})[:h](\d{2})?', lambda m: (
            today + timedelta(days=1),
            f"{int(m.group(2)):02d}:{m.group(3) or '00'}"
        )),
        # "segunda-feira às 10h" / "segunda 10h"
        (r'(segunda|ter[cç]a|quarta|quinta|sexta|s[áa]bado|domingo)[-\s]?(feira)?\s+(às?\s+)?(\d{1,2})[:h](\d{2})?', 
         lambda m: (next_weekday(m.group(1)), f"{int(m.group(4)):02d}:{m.group(5) or '00'}")),
        # "dia 25 às 15h" ou "25/05 às 15h"
        (r'dia\s+(\d{1,2})\s+(às?\s+)?(\d{1,2})[:h](\d{2})?', lambda m: (
            date(today.year, today.month, int(m.group(1))),
            f"{int(m.group(3)):02d}:{m.group(4) or '00'}"
        )),
        # "25/05 15:00" ou "25/05 às 15h"
        (r'(\d{1,2})/(\d{1,2})\s+(às?\s+)?(\d{1,2})[:h](\d{2})?', lambda m: (
            date(today.year, int(m.group(2)), int(m.group(1))),
            f"{int(m.group(4)):02d}:{m.group(5) or '00'}"
        )),
        # "hoje às 20h"
        (r'hoje\s+(às?\s+)?(\d{1,2})[:h](\d{2})?', lambda m: (
            today,
            f"{int(m.group(2)):02d}:{m.group(3) or '00'}"
        )),
    ]
    
    for pattern, fn in patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            try:
                d, t = fn(m)
                found.append({"date": d.isoformat(), "time": t, "source_text": m.group(0)})
            except:
                pass
    
    return found

def next_weekday(day_name):
    """Calcula a próxima ocorrência do dia da semana."""
    days = {
        "segunda": 0, "terça": 1, "terca": 1, "quarta": 2,
        "quinta": 3, "sexta": 4, "sábado": 5, "sabado": 5, "domingo": 6
    }
    target = days.get(day_name.lower(), 0)
    today = date.today()
    days_ahead = target - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)

# ─── WHATSAPP SCAN ────────────────────────────

def scan_whatsapp():
    """Scaneia conversas recentes do WhatsApp por compromissos."""
    try:
        result = cdp_command("Runtime.evaluate", {
            "expression": """
            (function() {
                var chats = [];
                var items = document.querySelectorAll('div[role="row"]');
                for (var i = 0; i < Math.min(items.length, 30); i++) {
                    var title = items[i].querySelector('span[title]');
                    var subtitle = items[i].querySelector('span[dir="auto"]');
                    if (title && subtitle) {
                        chats.push({
                            contact: title.getAttribute('title') || title.textContent,
                            last_msg: subtitle.textContent,
                            unread: items[i].querySelector('span[aria-label*="não lida"]') !== null
                        });
                    }
                }
                return JSON.stringify(chats);
            })()
            """,
            "returnByValue": True
        })
        if result and "result" in result:
            chats = json.loads(result["result"]["result"]["value"])
            appointments = []
            for chat in chats:
                dates = extract_dates_from_text(chat.get("last_msg", ""))
                for d in dates:
                    appointments.append({
                        "source": "whatsapp",
                        "contact": chat.get("contact", "?"),
                        "date": d["date"],
                        "time": d["time"],
                        "text": d["source_text"],
                        "unread": chat.get("unread", False)
                    })
            return appointments
    except Exception as e:
        pass
    return []

# ─── GOOGLE CALENDAR (via browser CDP session) ───

GCAL_CDP = "http://localhost:9222"

def scan_gcalendar():
    """Extrai eventos do Google Calendar usando a sessão do Brave CDP."""
    try:
        import urllib.request as ur
        # Get tabs
        resp = ur.urlopen(f"{GCAL_CDP}/json", timeout=5)
        tabs = json.loads(resp.read())
        
        # Find or create Google Calendar tab
        cal_tab = None
        for t in tabs:
            if "calendar.google.com" in t.get("url", ""):
                cal_tab = t
                break
        
        if not cal_tab:
            # Need to navigate to Calendar - use any tab
            for t in tabs:
                if "google.com" in t.get("url", ""):
                    cal_tab = t
                    break
        
        if not cal_tab:
            return []
        
        # Use websocket to interact
        import websocket
        ws_url = cal_tab["webSocketDebuggerUrl"]
        ws = websocket.create_connection(ws_url, timeout=10)
        
        # Navigate to calendar week view if not there
        if "calendar.google.com" not in cal_tab.get("url", ""):
            ws.send(json.dumps({"id": 1, "method": "Page.navigate", 
                "params": {"url": "https://calendar.google.com/calendar/u/0/r/week"}}))
            time.sleep(3)
            ws.settimeout(2)
            try:
                while True:
                    ws.recv()
            except:
                pass
        
        # Extract events from DOM (TreeWalker approach for Google Calendar SPA)
        ws.send(json.dumps({"id": 10, "method": "Runtime.evaluate", 
            "params": {"expression": """
(function() {
    var main = document.querySelector('[role=\"main\"]') || document.body;
    var result = [];
    var walker = document.createTreeWalker(main, NodeFilter.SHOW_TEXT);
    var node;
    while (node = walker.nextNode()) {
        var txt = node.textContent.trim();
        if (txt.length > 10 && txt.length < 300 && 
            (txt.includes('tarefa:') || txt.includes('evento:') || 
             txt.includes('Check-in') || txt.includes('Rotina') ||
             txt.match(/\\d+ eventos?,\\s*(segunda|terça|quarta|quinta|sexta|s[áa]bado|domingo)/i))) {
            result.push(txt);
        }
    }
    return JSON.stringify(result.slice(0, 50));
})()
""", "returnByValue": True}}))
        
        time.sleep(2)
        ws.settimeout(3)
        raw_events = []
        try:
            while True:
                msg = json.loads(ws.recv())
                if msg.get("id") == 10:
                    raw_events = json.loads(msg["result"]["result"]["value"])
                    break
        except:
            pass
        
        ws.close()
        
        # Parse Google Calendar events
        appointments = []
        today = date.today()
        
        # Parse text like "tarefa: Check-in Biológico: Água e Proteína (Acordar), Não concluída, 24 de maio de 2026, 10am"
        for ev in raw_events:
            match = re.search(r'(?:tarefa|evento):\s*(.+?),\s*(?:Não concluída|Concluída)?,?\s*(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4}),?\s*(\d{1,2})(?:am|pm)?', ev, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                day = int(match.group(2))
                month_str = match.group(3).lower()
                year = int(match.group(4))
                hour = int(match.group(5))
                
                meses = {"janeiro":1,"fevereiro":2,"março":3,"marco":3,"abril":4,"maio":5,
                         "junho":6,"julho":7,"agosto":8,"setembro":9,"outubro":10,
                         "novembro":11,"dezembro":12}
                month = meses.get(month_str, today.month)
                
                try:
                    ev_date = date(year, month, day)
                    if ev_date >= today:
                        appointments.append({
                            "source": "gcalendar",
                            "title": title,
                            "date": ev_date.isoformat(),
                            "time": f"{hour:02d}:00",
                            "type": "task"
                        })
                except:
                    pass
            else:
                # Try "N eventos, dia da semana, D de mês"
                m2 = re.search(r'(\d+)\s+eventos?,\s*(segunda|terça|quarta|quinta|sexta|sábado|domingo)', ev, re.IGNORECASE)
                if m2:
                    appointments.append({
                        "source": "gcalendar",
                        "title": f"{m2.group(1)} eventos",
                        "date": today.isoformat(),
                        "time": "",
                        "type": "summary"
                    })
        
        return appointments
    except Exception as e:
        import traceback
        print(f"[GCAL ERROR] {e}", file=__import__('sys').stderr)
    
    return []

# ─── MAIN ─────────────────────────────────────

def main():
    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    
    print("🧠 BRAIN CALENDAR MONITOR\n")
    
    # Coletar de todas as fontes
    wa = scan_whatsapp()
    gc = scan_gcalendar()
    
    all_appointments = wa + gc
    
    # Organizar por data
    agenda = defaultdict(list)
    for a in all_appointments:
        agenda[a["date"]].append(a)
    
    # Filtrar próximos 7 dias
    upcoming = {}
    for i in range(7):
        d = (date.today() + timedelta(days=i)).isoformat()
        if d in agenda:
            upcoming[d] = sorted(agenda[d], key=lambda x: x.get("time", "00:00"))
    
    # Hoje
    today_appointments = upcoming.get(today, [])
    
    print(f"📅 HOJE ({today}):")
    if today_appointments:
        for a in today_appointments:
            icon = "📱" if a["source"] == "whatsapp" else "📅"
            extra = f" — {a.get('contact', a.get('title', '?'))}" 
            print(f"  {icon} {a['time']}{extra}")
            if a.get("location"):
                print(f"     📍 {a['location']}")
    else:
        print("  (sem compromissos detectados)")
    
    # Próximos dias
    print(f"\n📆 PRÓXIMOS 7 DIAS:")
    total = 0
    for d, apps in sorted(upcoming.items()):
        if d == today:
            continue
        day_name = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"][date.fromisoformat(d).weekday()]
        print(f"  {day_name} {d[5:]}: {len(apps)} compromisso(s)")
        for a in apps:
            icon = "📱" if a["source"] == "whatsapp" else "📅"
            print(f"    {icon} {a['time']} — {a.get('contact', a.get('title', '?'))}")
        total += len(apps)
    
    if total == 0 and not today_appointments:
        print("  (nenhum compromisso detectado)")
    
    # Alertas
    conflicts = []
    for d, apps in upcoming.items():
        times = [a["time"] for a in apps]
        if len(times) != len(set(times)):
            conflicts.append(d)
    
    if conflicts:
        print(f"\n⚠️  CONFLITOS: {len(conflicts)} dia(s) com horários sobrepostos")
        for d in conflicts:
            print(f"  🔴 {d}")
    
    # Salvar agenda
    agenda_data = {
        "updated": datetime.now().isoformat(),
        "today": today,
        "today_appointments": today_appointments,
        "upcoming": {d: apps for d, apps in upcoming.items()},
        "conflicts": conflicts,
        "sources": {
            "whatsapp": len(wa),
            "gcalendar": len(gc)
        }
    }
    AGENDA_PATH.write_text(json.dumps(agenda_data, indent=2, ensure_ascii=False))
    
    # Escrever no KB se houver compromisso HOJE
    real_appointments = [a for a in today_appointments if a.get("type") != "summary"]
    if real_appointments:
        lines = "\\n".join(f"  {a.get('time','')} - {a.get('title','?')}" for a in real_appointments)
        kb_cmd = f"cd ~/.hermes/scripts && python3 -c \"from knowledge_bridge import cmd_write; cmd_write('brain', 'AGENDA: {len(real_appointments)} compromisso(s) hoje:\\n{lines}')\""
        os.system(kb_cmd + " 2>/dev/null")
    
    print(f"\n✅ Agenda salva em {AGENDA_PATH}")

if __name__ == "__main__":
    main()
