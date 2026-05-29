#!/usr/bin/env python3
"""
WorkingMemory — Memória de trabalho com TTL, LRU eviction e persistência.
Armazena pares (key, value) com expiração por tempo.
Persiste em ~/.hermes/brain/working_memory.json
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import thalamus

import json
import time
from datetime import datetime, timezone
from collections import OrderedDict

STORE_PATH = os.path.expanduser("~/.hermes/brain/working_memory.json")
MAX_ITEMS = 50


class WorkingMemory:
    """Memória de trabalho volátil com persistência em disco."""

    def __init__(self):
        self._store = OrderedDict()  # key -> {value, expires_at, last_access}
        self._load()

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------
    def _load(self):
        if os.path.exists(STORE_PATH):
            try:
                with open(STORE_PATH) as f:
                    data = json.load(f)
                for key, entry in data.get("items", {}).items():
                    # Só carrega itens não expirados
                    expires_at = entry.get("expires_at", 0)
                    if expires_at == 0 or time.time() < expires_at:
                        self._store[key] = {
                            "value": entry["value"],
                            "expires_at": expires_at,
                            "last_access": entry.get("last_access", time.time()),
                        }
                # Reconstrói ordem LRU
                sorted_items = sorted(
                    self._store.items(), key=lambda kv: kv[1].get("last_access", 0)
                )
                self._store = OrderedDict(sorted_items)
            except (json.JSONDecodeError, KeyError):
                self._store = OrderedDict()

    def _save(self):
        os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
        items = {}
        for key, entry in self._store.items():
            items[key] = {
                "value": entry["value"],
                "expires_at": entry["expires_at"],
                "last_access": entry["last_access"],
            }
        with open(STORE_PATH, "w") as f:
            json.dump({
                "items": items,
                "updated": datetime.now(timezone.utc).isoformat(),
            }, f, indent=2, default=str)

    # ------------------------------------------------------------------
    # Operações
    # ------------------------------------------------------------------
    def store(self, key, value, ttl_minutes=30):
        """Armazena um valor com TTL em minutos. TTL=0 significa sem expiração."""
        self.clear_expired()
        expires_at = 0 if ttl_minutes == 0 else time.time() + (ttl_minutes * 60)

        now = time.time()
        if key in self._store:
            # Atualiza existente — move para o fim (mais recente)
            self._store.move_to_end(key)
        else:
            # Evict se necessário
            if len(self._store) >= MAX_ITEMS:
                self._store.popitem(last=False)  # Remove o LRU (primeiro)

        self._store[key] = {
            "value": value,
            "expires_at": expires_at,
            "last_access": now,
        }
        self._save()

    def recall(self, key):
        """Recupera um valor. Retorna None se expirado ou não encontrado."""
        self.clear_expired()
        if key not in self._store:
            return None

        entry = self._store[key]
        entry["last_access"] = time.time()
        self._store.move_to_end(key)  # Marca como recentemente usado
        self._save()
        return entry["value"]

    def forget(self, key):
        """Remove uma chave da memória."""
        if key in self._store:
            del self._store[key]
            self._save()

    def get_context(self, max_items=20):
        """Retorna os itens mais recentes como contexto (dict)."""
        self.clear_expired()
        items = list(self._store.items())
        recent = items[-max_items:]  # Últimos N = mais recentes
        return {k: v["value"] for k, v in recent}

    def clear_expired(self):
        """Remove todos os itens expirados."""
        now = time.time()
        expired = [
            key for key, entry in self._store.items()
            if entry["expires_at"] > 0 and now >= entry["expires_at"]
        ]
        for key in expired:
            del self._store[key]
        if expired:
            self._save()

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------
    def __len__(self):
        return len(self._store)

    def keys(self):
        return list(self._store.keys())


# ----------------------------------------------------------------------
# Compatibility wrappers for meta_observer, hippocampus, etc.
# (exposes simple function API over the class-based engine)
# ----------------------------------------------------------------------
_default_wm = None


def _get_wm():
    global _default_wm
    if _default_wm is None:
        _default_wm = WorkingMemory()
    return _default_wm


def store_observation(domain, data, ttl=3600):
    """Store a short-term observation (ttl in seconds, converted to minutes)."""
    wm = _get_wm()
    key = f"obs:{domain}:{time.time()}"
    wm.store(key, {"domain": domain, "data": data, "timestamp": datetime.now(timezone.utc).isoformat()},
             ttl_minutes=max(1, int(ttl / 60)))
    return {"key": key, "domain": domain}


def get_recent_observations(domain=None, max_age=600):
    """Get recent observations within max_age seconds."""
    wm = _get_wm()
    cutoff = time.time() - max_age
    ctx = wm.get_context(max_items=50)
    results = []
    for key, val in ctx.items():
        if not key.startswith("obs:"):
            continue
        if isinstance(val, dict):
            obs_domain = val.get("domain", "")
            if domain is None or obs_domain == domain:
                ts_str = val.get("timestamp", "")
                try:
                    ts = datetime.fromisoformat(ts_str).timestamp()
                    if ts >= cutoff:
                        results.append(val)
                except (ValueError, TypeError):
                    results.append(val)
    return results


def add_pending_task(task_id, description, priority=0):
    """Add a pending task."""
    wm = _get_wm()
    task = {"id": task_id, "description": description, "priority": priority,
            "status": "pending", "created_at": datetime.now(timezone.utc).isoformat()}
    wm.store(f"task:{task_id}", task, ttl_minutes=0)
    return task


def complete_task(task_id):
    """Mark task as completed."""
    wm = _get_wm()
    task = wm.recall(f"task:{task_id}")
    if task:
        task["status"] = "completed"
        task["completed_at"] = datetime.now(timezone.utc).isoformat()
        wm.store(f"task:{task_id}", task, ttl_minutes=60)
        return True
    return False


def get_pending_tasks():
    """Get all pending tasks."""
    wm = _get_wm()
    ctx = wm.get_context(max_items=50)
    tasks = []
    for key, val in ctx.items():
        if key.startswith("task:") and isinstance(val, dict) and val.get("status") == "pending":
            tasks.append(val)
    return sorted(tasks, key=lambda t: -t.get("priority", 0))


def record_decision(domain, action, reasoning, confidence):
    """Record a decision."""
    wm = _get_wm()
    dec = {"domain": domain, "action": action, "reasoning": reasoning,
           "confidence": confidence, "timestamp": datetime.now(timezone.utc).isoformat()}
    wm.store(f"decision:{domain}:{time.time()}", dec, ttl_minutes=1440)
    return dec


def get_recent_decisions(max_age=3600):
    """Get decisions from the last max_age seconds."""
    wm = _get_wm()
    cutoff = time.time() - max_age
    ctx = wm.get_context(max_items=50)
    decisions = []
    for key, val in ctx.items():
        if key.startswith("decision:"):
            ts_str = val.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str).timestamp()
                if ts >= cutoff:
                    decisions.append(val)
            except (ValueError, TypeError):
                pass
    return decisions


def set_context(tags):
    """Set current context tags."""
    wm = _get_wm()
    wm.store("__context__", tags if isinstance(tags, list) else [tags], ttl_minutes=60)


def get_context():
    """Get current context tags."""
    wm = _get_wm()
    return wm.recall("__context__") or []


def flush():
    """Flush expired items."""
    wm = _get_wm()
    wm.clear_expired()
    return len(wm)


# ----------------------------------------------------------------------
# __main__
# ----------------------------------------------------------------------
if __name__ == "__main__":
    wm = WorkingMemory()

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        wm.store("last_query", "EURUSD analysis", ttl_minutes=5)
        wm.store("user_preference", "dark mode", ttl_minutes=0)
        wm.store("session_id", "abc123", ttl_minutes=30)

        print("Recall last_query:", wm.recall("last_query"))
        print("Context:", wm.get_context(max_items=10))
        print("Keys:", wm.keys())

        wm.forget("session_id")
        print("After forget, keys:", wm.keys())

    elif len(sys.argv) > 1 and sys.argv[1] == "clear":
        for key in wm.keys():
            wm.forget(key)
        print("Working memory cleared.")

    else:
        wm.clear_expired()
        print(f"WorkingMemory: {len(wm)} items")
        print("Keys:", wm.keys())
        print("Usage: working_memory.py [test|clear]")
