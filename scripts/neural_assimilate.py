#!/usr/bin/env python3
"""
Neural Sync — Agent Assimilation
=================================
Lê neural_sync.json e assimila interações Brain↔Usuário no Agent.
Chamado pelo Agent durante ciclo de sincronismo.

Usage:
  neural_assimilate.py            → assimila interações não lidas
  neural_assimilate.py status    → status da sync
  neural_assimilate.py feed "msg" → alimenta diretamente na NN-Shared
"""

import json
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERMES = Path.home() / ".hermes"
NEURAL_SYNC = HERMES / "neural_sync.json"
ASSIMILATED_LOG = HERMES / "assimilated.json"
NN_ENGINE = HERMES / "scripts" / "nn_engine.py"
LOREBRAIN = HERMES / "lore" / "brain" / "store"


def _load(path):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            pass
    return {}


def _save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _now():
    return datetime.now(timezone.utc).isoformat()


def assimilate():
    """Read neural_sync.json, process unread interactions, feed to NN + Lore."""
    sync = _load(NEURAL_SYNC)
    interactions = sync.get("interactions", [])
    
    if not interactions:
        return {"status": "empty", "message": "No interactions to assimilate"}
    
    # Track what's been assimilated
    assimilated = _load(ASSIMILATED_LOG)
    seen_ids = set(assimilated.get("seen_ids", []))
    
    new_count = 0
    for interaction in interactions:
        msg_id = interaction.get("message_id", "")
        if msg_id in seen_ids:
            continue
        
        # 1. Feed to NN-Shared
        try:
            subprocess.run([
                "python3", str(NN_ENGINE), "learn", "shared",
                f"Brain interaction: user asked '{interaction.get('user_message', '')[:150]}' "
                f"about {','.join(interaction.get('topics', []))}"
            ], capture_output=True, timeout=10)
        except:
            pass
        
        # 2. Store in Lore (brain namespace, as reference for Agent)
        try:
            lore_entry = (
                f"User→Brain: {interaction.get('user_message', '')}\n"
                f"Brain→User: {interaction.get('brain_response', '')}"
            )
            subprocess.run([
                "python3", str(HERMES / "scripts" / "lore.py"),
                "brain", "add", lore_entry
            ], capture_output=True, timeout=10)
        except:
            pass
        
        seen_ids.add(msg_id)
        new_count += 1
    
    # Update assimilated log
    assimilated["seen_ids"] = list(seen_ids)[-500:]  # Keep last 500
    assimilated["last_assimilation"] = _now()
    assimilated["total_assimilated"] = len(seen_ids)
    _save(ASSIMILATED_LOG, assimilated)
    
    return {
        "status": "ok",
        "assimilated": new_count,
        "total": len(interactions),
        "topics_seen": list(set(
            t for i in interactions[-new_count:]
            for t in i.get("topics", [])
        )) if new_count > 0 else [],
    }


def feed_direct(message):
    """Feed a message directly into NN-Shared network."""
    try:
        r = subprocess.run([
            "python3", str(NN_ENGINE), "learn", "shared", message
        ], capture_output=True, text=True, timeout=10)
        return {"status": "ok", "output": r.stdout[:200]}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def status():
    """Show sync status."""
    sync = _load(NEURAL_SYNC)
    assimilated = _load(ASSIMILATED_LOG)
    
    total = len(sync.get("interactions", []))
    seen = len(assimilated.get("seen_ids", []))
    
    print(f"🔗 Neural Sync Status")
    print(f"   Total interactions: {total}")
    print(f"   Assimilated: {seen}")
    print(f"   Pending: {total - seen}")
    print(f"   Last sync: {sync.get('last_updated', 'never')}")
    print(f"   Last assimilation: {assimilated.get('last_assimilation', 'never')}")
    
    # Show recent interactions
    if total > 0:
        recent = sync["interactions"][-3:]
        print(f"\n   Recentes:")
        for i, interaction in enumerate(recent):
            msg = interaction.get("user_message", "")[:80]
            topics = ",".join(interaction.get("topics", []))
            print(f"   {i+1}. [{topics}] {msg}...")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        result = assimilate()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif sys.argv[1] == "assimilate":
        result = assimilate()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif sys.argv[1] == "status":
        status()
    elif sys.argv[1] == "feed":
        message = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else sys.stdin.read().strip()
        if message:
            result = feed_direct(message)
            print(json.dumps(result, indent=2))
        else:
            print("❌ No message to feed")
    else:
        print("Usage: neural_assimilate.py [assimilate|status|feed]")
