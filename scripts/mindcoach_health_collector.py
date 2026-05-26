#!/usr/bin/env python3
"""
MindCoach Health Connector - Free Edition
Multi-source: Google Fit API + Gmail + WhatsApp + Telegram manual input

Usage:
  python3 mindcoach_health_collector.py collect     # Try all sources, save results
  python3 mindcoach_health_collector.py parse "sono 7h hr 72 passos 8500"  # Manual input
  python3 mindcoach_health_collector.py scan-email   # Scan recent emails for health data
  python3 mindcoach_health_collector.py scan-whatsapp # Scan WhatsApp for health data
"""

import json
import os
import re
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

HEALTH_DIR = Path.home() / ".hermes" / "mindcoach"
HEALTH_DATA_PATH = HEALTH_DIR / "health_data.json"
MANUAL_INPUT_PATH = HEALTH_DIR / "manual_inputs.json"
CREDS_FILE = Path.home() / ".hermes" / "vault" / "mindcoach_oauth_client.json"


# ═══════════════════════════════════════════════════════════
# Mode 3: Email Scanner (Gmail via himalaya)
# ═══════════════════════════════════════════════════════════

# Health-related keywords in email subjects/bodies (PT + EN)
HEALTH_EMAIL_SENDERS = [
    "huawei health", "google fit", "samsung health", "strava",
    "myfitnesspal", "fitbit", "garmin", "withings",
    "dr. consulta", "laboratorio", "exame", "farmacia",
    "academia", "smartfit", "gympass", "wellhub",
    "psicologo", "terapeuta", "nutricionista",
    "health", "fitness", "workout", "treino", "medico"
]

HEALTH_EMAIL_KEYWORDS = [
    # PT
    "saúde", "saude", "exercício", "exercicio", "treino", "academia",
    "sono", "dormir", "passos", "batimentos", "cardíaco", "cardiaco",
    "peso", "calorias", "imc", "pressão", "pressao", "oxigenação",
    "exame", "consulta", "médico", "medico", "receita", "farmácia",
    "psicólogo", "terapia", "bem-estar", "meditação", "meditacao",
    # EN
    "steps", "sleep", "heart rate", "workout", "exercise",
    "calories", "weight", "blood pressure", "lab results",
    "appointment", "prescription", "pharmacy", "mental health",
    # Smartwatch reports
    "weekly report", "relatório semanal", "health report",
    "activity summary", "resumo de atividades",
    "huawei health", "health kit"
]


def scan_email_health():
    """Scan recent emails (24h) for health-related data using IMAP directly."""
    import imaplib
    import email
    from email.header import decode_header
    
    results = []
    
    try:
        # Connect to Gmail IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login("robertosantos.una@gmail.com", "exnlrvfswckioces")
        mail.select("INBOX")
        
        # Search emails from last 24h
        since_date = (datetime.now() - timedelta(hours=24)).strftime("%d-%b-%Y")
        status, msg_ids = mail.search(None, f'(SINCE "{since_date}")')
        
        if status != "OK" or not msg_ids[0]:
            mail.logout()
            return {"source": "email", "health_emails_found": 0, "senders": []}
        
        email_ids = msg_ids[0].split()[-50:]  # Last 50 emails
        
        for eid in email_ids:
            status, msg_data = mail.fetch(eid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])")
            if status != "OK":
                continue
            
            for part in msg_data:
                if isinstance(part, tuple):
                    msg = email.message_from_bytes(part[1])
                    subject = decode_email_header(msg.get("Subject", ""))
                    from_addr = decode_email_header(msg.get("From", ""))
                    combined = (subject + " " + from_addr).lower()
                    
                    is_health = False
                    matched = None
                    
                    for sender in HEALTH_EMAIL_SENDERS:
                        if sender in combined:
                            is_health = True
                            matched = sender
                            break
                    
                    if not is_health:
                        for kw in HEALTH_EMAIL_KEYWORDS:
                            if kw in combined:
                                is_health = True
                                matched = kw
                                break
                    
                    if is_health:
                        # Extract numbers from subject (steps, hours, etc.)
                        parsed = extract_metrics_from_text(subject)
                        results.append({
                            "from": from_addr,
                            "subject": subject[:150],
                            "matched": matched,
                            "extracted": parsed
                        })
        
        mail.logout()
        
        return {
            "source": "email",
            "timestamp": datetime.now().isoformat(),
            "health_emails_found": len(results),
            "emails": results[:10],
        }
        
    except Exception as e:
        return {"source": "email", "error": str(e)[:100], "health_emails_found": 0}


def decode_email_header(header):
    """Decode email header (handles =?UTF-8?B?...?= encoding)."""
    if not header:
        return ""
    try:
        from email.header import decode_header
        parts = decode_header(header)
        decoded = ""
        for part, charset in parts:
            if isinstance(part, bytes):
                decoded += part.decode(charset or "utf-8", errors="replace")
            else:
                decoded += part
        return decoded
    except:
        return str(header)


def extract_metrics_from_text(text):
    """Try to extract health metrics from email subjects/bodies."""
    return parse_manual_input(text)


# ═══════════════════════════════════════════════════════════
# Mode 4: WhatsApp Scanner
# ═══════════════════════════════════════════════════════════

WHATSAPP_HEALTH_KEYWORDS = [
    "sono", "dormi", "dormir", "passos", "steps",
    "treino", "academia", "corrida", "caminhada",
    "batimento", "heart", "bpm", "peso", "kg",
    "saúde", "saude", "exercício", "exercicio",
    "meditação", "meditacao", "yoga", "crossfit",
    "água", "agua", "calorias", "dieta", "jejum",
]


def scan_whatsapp_health():
    """Scan WhatsApp messages for health-related data."""
    results = []
    
    # WhatsApp message DB location (if using WhatsApp Web session)
    wa_paths = [
        Path.home() / ".hermes" / "whatsapp" / "messages.json",
        Path.home() / ".hermes" / "whatsapp" / "chat_history.json",
        Path.home() / ".hermes" / "data" / "whatsapp_messages.json",
    ]
    
    for wa_path in wa_paths:
        if wa_path.exists():
            try:
                messages = json.loads(wa_path.read_text())
                if isinstance(messages, dict):
                    messages = list(messages.values())
                if isinstance(messages, list):
                    today = datetime.now().strftime("%Y-%m-%d")
                    for msg in messages:
                        if isinstance(msg, dict):
                            text = msg.get("text", msg.get("body", msg.get("content", "")))
                            ts = msg.get("timestamp", msg.get("date", msg.get("time", "")))
                            if isinstance(text, str):
                                text_lower = text.lower()
                                for kw in WHATSAPP_HEALTH_KEYWORDS:
                                    if kw in text_lower:
                                        results.append({
                                            "text": text[:200],
                                            "timestamp": ts,
                                            "matched_keyword": kw
                                        })
                                        break
            except Exception:
                pass
    
    # Also try scanning from WhatsApp contact data
    contact_files = search_files_whatsapp()
    for cf in contact_files:
        try:
            data = json.loads(cf.read_text()) if cf.exists() else {}
            if isinstance(data, list):
                for msg in data:
                    text = str(msg.get("text", msg.get("body", ""))).lower()
                    if any(kw in text for kw in WHATSAPP_HEALTH_KEYWORDS):
                        results.append({"text": text[:200], "source": str(cf)})
        except:
            pass
    
    return {
        "source": "whatsapp",
        "timestamp": datetime.now().isoformat(),
        "health_messages_found": len(results),
        "messages": results[:10],
    }


def search_files_whatsapp():
    """Find WhatsApp-related data files."""
    paths = []
    whatsapp_dir = Path.home() / ".hermes" / "whatsapp"
    if whatsapp_dir.exists():
        for f in whatsapp_dir.glob("*.json"):
            paths.append(f)
    return paths


# ═══════════════════════════════════════════════════════════
# Mode 1: Google Fit REST API
# ═══════════════════════════════════════════════════════════

def get_access_token():
    """Get a fresh Google access token using gcloud."""
    if not CREDS_FILE.exists():
        return None
    try:
        r = subprocess.run(
            ["gcloud", "auth", "application-default", "print-access-token"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return None


def query_fit_datatype(access_token, data_type_name, date_str):
    """Query a single data type from Google Fit REST API (free tier)."""
    start_dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)

    body = json.dumps({
        "aggregateBy": [{"dataTypeName": data_type_name}],
        "bucketByTime": {"durationMillis": 86400000},
        "startTimeMillis": start_ms,
        "endTimeMillis": end_ms
    }).encode()

    req = urllib.request.Request(
        "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate",
        data=body,
        headers={
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            buckets = result.get("bucket", [])
            if buckets:
                points = buckets[0].get("dataset", [])
                if points:
                    values = points[0].get("point", [])
                    if values:
                        val = values[0].get("value", [])
                        if val:
                            v = val[0]
                            return v.get("fpVal") or v.get("intVal", 0)
            return 0
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()[:200]
        return {"error": e.code, "message": err_body}
    except Exception as e:
        return {"error": str(e)[:100]}


def get_google_fit_data(date_str=None):
    """Pull sleep, heart rate, steps, calories from Google Fit."""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    token = get_access_token()
    if not token:
        return {"status": "unavailable", "reason": "No OAuth credentials or gcloud not configured"}

    metrics = {}

    # Steps (delta)
    steps = query_fit_datatype(token, "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps", date_str)
    metrics["steps"] = steps

    # Heart rate (resting)
    hr = query_fit_datatype(token, "derived:com.google.heart_rate.bpm:com.google.android.gms:resting_heart_rate", date_str)
    metrics["resting_heart_rate"] = hr

    # Calories
    cal = query_fit_datatype(token, "derived:com.google.calories.expended:com.google.android.gms:calories_burned", date_str)
    metrics["calories_burned"] = cal

    # Sleep
    sleep = query_fit_datatype(token, "derived:com.google.sleep.segment:com.google.android.gms:sleep", date_str)
    metrics["sleep_minutes"] = sleep

    return {
        "status": "ok",
        "source": "google_fit_api",
        "date": date_str,
        **metrics
    }


# ═══════════════════════════════════════════════════════════
# Mode 2: Telegram Manual Input Parser
# ═══════════════════════════════════════════════════════════

def parse_manual_input(text):
    """
    Parse free-form health data from user messages.
    Examples:
      "sono 7h hr 72 passos 8500 peso 82"
      "dormi 6:30 batimentos 68"
      "sleep 7.5 heart 70 steps 10000 agua 2"
    """
    text = text.lower()
    result = {}

    # Sleep (hours)
    m = re.search(r'(?:sono|dormi|sleep|dormir)[\s:]*(\d+[.,:]?\d*)\s*(?:h|horas?)?', text)
    if m:
        val = m.group(1).replace(',', '.').replace(':', '.')
        try:
            result["sleep_hours"] = float(val)
        except ValueError:
            pass

    # Heart rate
    m = re.search(r'(?:hr|heart|batimentos?|bpm|pulso)[\s:]*(\d+)', text)
    if m:
        result["resting_heart_rate"] = int(m.group(1))

    # Steps
    m = re.search(r'(?:passos|steps|caminhada)[\s:]*(\d+)', text)
    if m:
        result["steps"] = int(m.group(1))

    # Weight
    m = re.search(r'(?:peso|weight)[\s:]*(\d+[.,]?\d*)', text)
    if m:
        result["weight_kg"] = float(m.group(1).replace(',', '.'))

    # Water
    m = re.search(r'(?:agua|água|water)[\s:]*(\d+[.,]?\d*)', text)
    if m:
        result["water_liters"] = float(m.group(1).replace(',', '.'))

    # SpO2
    m = re.search(r'(?:spo2|oxigen|oxig[eê]n|satura[cç][aã]o)[\s:]*(\d+)', text)
    if m:
        result["spo2"] = int(m.group(1))

    # Mood (1-10)
    m = re.search(r'(?:humor|mood|animo|ânimo)[\s:]*(\d+)', text)
    if m:
        result["mood"] = int(m.group(1))

    return result if result else None


def save_manual_input(parsed_data):
    """Save manual health data to today's bucket."""
    today = datetime.now().strftime("%Y-%m-%d")
    MANUAL_INPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if MANUAL_INPUT_PATH.exists():
        existing = json.loads(MANUAL_INPUT_PATH.read_text())
    if today not in existing:
        existing[today] = {}
    existing[today].update(parsed_data)
    existing[today]["updated_at"] = datetime.now().isoformat()
    MANUAL_INPUT_PATH.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
    return existing[today]


# ═══════════════════════════════════════════════════════════
# Main: Collect
# ═══════════════════════════════════════════════════════════

def collect():
    """Try all sources: Google Fit, Gmail, WhatsApp, manual inputs. Save."""
    data = {"timestamp": datetime.now().isoformat(), "source": "none", "metrics": {}, "raw_sources": {}}

    # Step 1: Try Google Fit API
    fit = get_google_fit_data()
    if fit.get("status") == "ok":
        data["source"] = "google_fit"
        data["metrics"] = {k: v for k, v in fit.items()
                           if k not in ("status", "source", "date")
                           and not isinstance(v, dict)}

    # Step 2: Scan email for health data
    email_data = scan_email_health()
    data["raw_sources"]["email"] = email_data
    if email_data.get("health_emails_found", 0) > 0:
        data["source"] = data["source"] + "+email" if data["source"] != "none" else "email"
        # Merge any extracted metrics from emails
        for em in email_data.get("emails", []):
            extracted = em.get("extracted")
            if extracted and isinstance(extracted, dict):
                data["metrics"].update({k: v for k, v in extracted.items()
                                        if k not in data["metrics"]})

    # Step 3: Scan WhatsApp for health data
    wa_data = scan_whatsapp_health()
    data["raw_sources"]["whatsapp"] = wa_data
    if wa_data.get("health_messages_found", 0) > 0:
        data["source"] = data["source"] + "+whatsapp" if data["source"] != "none" else "whatsapp"

    # Step 4: Merge manual inputs (highest priority)
    today = datetime.now().strftime("%Y-%m-%d")
    if MANUAL_INPUT_PATH.exists():
        manual = json.loads(MANUAL_INPUT_PATH.read_text())
        if today in manual:
            if data["source"] == "none":
                data["source"] = "manual"
            else:
                data["source"] += "+manual"
            data["metrics"].update({k: v for k, v in manual[today].items()
                                    if k != "updated_at"})

    # Save
    HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    HEALTH_DATA_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return data


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        result = collect()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif sys.argv[1] == "collect":
        result = collect()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif sys.argv[1] == "parse":
        text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else sys.stdin.read().strip()
        result = parse_manual_input(text)
        if result:
            saved = save_manual_input(result)
            print(json.dumps({"status": "saved", "parsed": result, "today": saved}))
        else:
            print(json.dumps({"status": "no_data", "message": "Could not parse health data"}))
    elif sys.argv[1] == "scan-email":
        result = scan_email_health()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif sys.argv[1] == "scan-whatsapp":
        result = scan_whatsapp_health()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif sys.argv[1] == "status":
        if HEALTH_DATA_PATH.exists():
            print(HEALTH_DATA_PATH.read_text())
        else:
            print(json.dumps({"status": "no_data_yet"}))
