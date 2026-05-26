#!/usr/bin/env python3
"""
MindCoach Collectors — Coletores reais de dados das fontes integradas.
Alimenta o motor com métricas concretas de email, social, financeiro, etc.
"""
import json, os, sys, re
from datetime import datetime, timezone as tz
from pathlib import Path

HERMES = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
MINDCOACH_DATA = HERMES / "mindcoach" / "data"
NOW = lambda: datetime.now(tz.utc).isoformat()

def collect_email_activity():
    """Coleta atividade de email — última checagem do monitor.py."""
    wake_file = HERMES / "monitor" / "wake.txt"
    last_check = HERMES / "monitor" / "last_check.json"
    
    result = {
        "source": "email_activity",
        "timestamp": NOW(),
        "emails_checked": 0,
        "high_priority": 0,
        "last_wake": None
    }
    
    if wake_file.exists():
        result["last_wake"] = wake_file.read_text().strip()[:200]
    
    if last_check.exists():
        try:
            data = json.loads(last_check.read_text())
            result["emails_checked"] = data.get("checked", 0)
            result["high_priority"] = data.get("high_priority", 0)
        except:
            pass
    
    return result


def collect_forex_status():
    """Coleta status atual do forex."""
    signals_file = HERMES / "forex" / "signals_pending.json"
    state_file = HERMES / "forex" / "brain_signal_state.json"
    
    result = {
        "source": "forex",
        "timestamp": NOW(),
        "signals_pending": 0,
        "trades_executed": 0,
        "market_open": True,  # Seg-Sex
        "pnl_day": 0.0
    }
    
    if signals_file.exists():
        try:
            signals = json.loads(signals_file.read_text())
            result["signals_pending"] = len(signals.get("pending", []))
            result["trades_executed"] = len(signals.get("executed", []))
        except:
            pass
    
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
            result["pnl_day"] = state.get("pnl_today", 0)
        except:
            pass
    
    return result


def collect_social_presence():
    """Coleta presença social — Telegram e WhatsApp."""
    telegram_file = HERMES / "telegram" / "last_scan.json"
    
    result = {
        "source": "social",
        "timestamp": NOW(),
        "telegram_chats": 0,
        "whatsapp_chats": 0,
        "unread_total": 0,
        "last_interaction": None
    }
    
    if telegram_file.exists():
        try:
            data = json.loads(telegram_file.read_text())
            result["telegram_chats"] = data.get("chats", 0)
            result["unread_total"] = data.get("unread", 0)
        except:
            pass
    
    return result


def collect_all():
    """Executa todos os coletores e salva dados."""
    MINDCOACH_DATA.mkdir(parents=True, exist_ok=True)
    
    collectors = {
        "email": collect_email_activity,
        "forex": collect_forex_status,
        "social": collect_social_presence,
    }
    
    all_data = {}
    for name, collector in collectors.items():
        try:
            data = collector()
            all_data[name] = data
        except Exception as e:
            all_data[name] = {"error": str(e), "timestamp": NOW()}
    
    # Save
    data_file = MINDCOACH_DATA / f"collect_{datetime.now(tz.utc).strftime('%Y%m%d_%H%M')}.json"
    data_file.write_text(json.dumps(all_data, indent=2, ensure_ascii=False))
    
    # Also save latest
    (MINDCOACH_DATA / "latest.json").write_text(json.dumps(all_data, indent=2, ensure_ascii=False))
    
    return all_data


if __name__ == "__main__":
    data = collect_all()
    print(json.dumps(data, indent=2, ensure_ascii=False))
