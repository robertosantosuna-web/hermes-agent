#!/usr/bin/env python3
"""Tálamo — Canal único de comunicação entre agentes cerebrais.
Substitui 8 bridges: brain_inbox, brain_outbox, brain_gateway_inbox,
cortex_sync, neural/bridge_inbox, neural/bridge_outbox,
forex/knowledge_bridge, neural_sync.
"""

import json, os, time, hashlib
from datetime import datetime, timezone

THALAMUS_PATH = os.path.expanduser("~/.hermes/brain/thalamus.json")
MAX_EVENTS = 500
MAX_MESSAGES = 200

def _load():
    if os.path.exists(THALAMUS_PATH):
        with open(THALAMUS_PATH) as f:
            return json.load(f)
    return _empty_state()

def _empty_state():
    return {
        "messages": {"user_brain": [], "brain_user": [], "inter_agent": [], "external": []},
        "events": [],
        "alerts": [],
        "state": {"market_regime": "unknown", "risk_level": "low", "health_score": 100,
                  "active_modules": [], "consciousness_phi": 0.0, "last_cycle": None},
        "discoveries": [],
        "patterns": {},
        "weights": {},
        "validations": [],
        "tasks": [],
        "global_workspace": {"current_focus": None, "attention_queue": [], "broadcast_history": []},
        "meta_cognition": {"confidence": 0.85, "self_model": {}, "performance_log": []}
    }

def _save(state):
    os.makedirs(os.path.dirname(THALAMUS_PATH), exist_ok=True)
    with open(THALAMUS_PATH, 'w') as f:
        json.dump(state, f, indent=2, default=str)

def send_message(source, target, msg_type, content, priority=0):
    state = _load()
    msg = {"id": hashlib.md5(f"{source}{target}{time.time()}".encode()).hexdigest()[:8],
           "source": source, "target": target, "type": msg_type,
           "content": content, "priority": priority, "timestamp": datetime.now(timezone.utc).isoformat()}
    state["messages"]["inter_agent"].append(msg)
    if len(state["messages"]["inter_agent"]) > MAX_MESSAGES:
        state["messages"]["inter_agent"] = state["messages"]["inter_agent"][-MAX_MESSAGES:]
    _save(state)
    return msg["id"]

def read_messages(target, mark_read=True):
    state = _load()
    msgs = [m for m in state["messages"]["inter_agent"] if m["target"] == target]
    if mark_read:
        state["messages"]["inter_agent"] = [m for m in state["messages"]["inter_agent"] if m["target"] != target]
        _save(state)
    return msgs

def log_event(event_type, source, data, severity="info"):
    state = _load()
    event = {"id": hashlib.md5(f"{event_type}{source}{time.time()}".encode()).hexdigest()[:8],
             "type": event_type, "source": source, "data": data, "severity": severity,
             "timestamp": datetime.now(timezone.utc).isoformat()}
    state["events"].append(event)
    if len(state["events"]) > MAX_EVENTS:
        state["events"] = state["events"][-MAX_EVENTS:]
    _save(state)
    return event["id"]

def get_recent_events(hours=24, event_type=None):
    state = _load()
    cutoff = time.time() - (hours * 3600)
    recent = []
    for e in state["events"]:
        ts = datetime.fromisoformat(e["timestamp"]).timestamp()
        if ts >= cutoff and (event_type is None or e["type"] == event_type):
            recent.append(e)
    return recent

def raise_alert(level, title, description, source):
    state = _load()
    alert = {"id": hashlib.md5(f"{title}{time.time()}".encode()).hexdigest()[:8],
             "level": level, "title": title, "description": description,
             "source": source, "timestamp": datetime.now(timezone.utc).isoformat(),
             "acknowledged": False}
    state["alerts"].append(alert)
    if len(state["alerts"]) > 100:
        state["alerts"] = state["alerts"][-100:]
    _save(state)
    return alert["id"]

def get_active_alerts():
    state = _load()
    return [a for a in state["alerts"] if not a.get("acknowledged")]

def update_state(key, value):
    state = _load()
    state["state"][key] = value
    state["state"]["last_cycle"] = datetime.now(timezone.utc).isoformat()
    _save(state)

def get_state(key=None):
    state = _load()
    if key:
        return state["state"].get(key)
    return state["state"]

def add_discovery(domain, insight, confidence, source):
    state = _load()
    disc = {"id": hashlib.md5(f"{domain}{insight}{time.time()}".encode()).hexdigest()[:8],
            "domain": domain, "insight": insight, "confidence": confidence,
            "source": source, "timestamp": datetime.now(timezone.utc).isoformat()}
    state["discoveries"].append(disc)
    _save(state)

def broadcast_to_workspace(content, priority=0, source="master"):
    state = _load()
    entry = {"content": content, "priority": priority, "source": source,
             "timestamp": datetime.now(timezone.utc).isoformat()}
    state["global_workspace"]["attention_queue"].append(entry)
    state["global_workspace"]["attention_queue"].sort(key=lambda x: -x["priority"])
    state["global_workspace"]["broadcast_history"].append(entry)
    if len(state["global_workspace"]["broadcast_history"]) > 100:
        state["global_workspace"]["broadcast_history"] = state["global_workspace"]["broadcast_history"][-100:]
    _save(state)

def get_workspace_focus():
    state = _load()
    return state["global_workspace"]["current_focus"]

def run():
    """Ciclo de sincronização do Tálamo."""
    state = _load()
    cutoff = time.time() - (7 * 86400)
    state["events"] = [e for e in state["events"]
                       if datetime.fromisoformat(e["timestamp"]).timestamp() >= cutoff]
    cutoff24 = time.time() - 86400
    state["alerts"] = [a for a in state["alerts"]
                       if not a.get("acknowledged") or
                       datetime.fromisoformat(a["timestamp"]).timestamp() >= cutoff24]
    active_alerts = len([a for a in state["alerts"] if not a.get("acknowledged")])
    state["state"]["health_score"] = max(0, 100 - (active_alerts * 10))
    state["state"]["active_modules"] = list(set(
        e.get("source", "unknown") for e in state["events"]
        if datetime.fromisoformat(e["timestamp"]).timestamp() >= time.time() - 3600
    ))
    state["state"]["last_cycle"] = datetime.now(timezone.utc).isoformat()
    _save(state)
    return {"alerts": active_alerts, "health": state["state"]["health_score"]}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        state = _load()
        print(f"Health: {state['state']['health_score']}%")
        print(f"Active: {state['state']['active_modules']}")
        print(f"Alerts: {len([a for a in state['alerts'] if not a.get('acknowledged')])}")
    elif len(sys.argv) > 1 and sys.argv[1] == "alerts":
        for a in get_active_alerts():
            print(f"[{a['level'].upper()}] {a['title']}: {a['description']}")
    else:
        result = run()
        print(f"Tálamo sync: {result}")
