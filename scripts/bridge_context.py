#!/usr/bin/env python3
"""Bridge entre agent_context.json e brain_context.json — consulta cruzada para estudo."""
import json
import sys
from pathlib import Path

HERMES = Path.home() / ".hermes"

def load_json(path):
    with open(path) as f:
        return json.load(f)

def show_agent_context():
    agent = load_json(HERMES / "agent_context.json")
    print("\n=== AGENT CONTEXT (o que o agente está fazendo) ===")
    print(f"Status: {agent['current_state']['status']}")
    print(f"Tarefas ativas: {len(agent['active_tasks'])}")
    for t in agent['active_tasks']:
        print(f"  [{t['status']}] {t['description']} — fase: {t['phase']}")
        print(f"    Steps pendentes: {t['steps_pending']}")

def show_brain_context():
    brain = load_json(HERMES / "brain_context.json")
    print("\n=== BRAIN CONTEXT (estado do cérebro local) ===")
    print(f"Status: {brain['current_state']['status']}")
    for mod, data in brain['modules_status'].items():
        print(f"  {mod}: {data['status']}")

def show_cross():
    print("\n=== CROSS-REFERENCE ===")
    agent = load_json(HERMES / "agent_context.json")
    brain = load_json(HERMES / "brain_context.json")
    print(f"Agent last action: {agent['current_state']['last_action']}")
    print(f"Brain last cycle: {brain['current_state']['last_cycle']}")
    print(f"Agent active tasks: {len(agent['active_tasks'])}")
    print(f"Brain active modules: {len([m for m,d in brain['modules_status'].items() if d['status']=='running'])}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "agent":
            show_agent_context()
        elif cmd == "brain":
            show_brain_context()
        elif cmd == "cross":
            show_cross()
        else:
            print(f"Uso: {sys.argv[0]} [agent|brain|cross]")
    else:
        show_cross()
