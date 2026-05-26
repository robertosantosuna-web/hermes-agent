#!/usr/bin/env python3
"""
Córtex Bridge — Comunicação Interna entre Lobos
================================================
Ponte bidirecional entre Lobo Esquerdo (Hermes/DeepSeek) e Lobo Direito (Codex/GPT-5.5).

Arquivo compartilhado: ~/.hermes/cortex_sync.json

Fluxos:
  LEFT → RIGHT: consulta, delega tarefa, pede análise
  RIGHT → LEFT: resposta, resultado, alerta, descoberta

Comandos:
  cortex_bridge.py ask "pergunta"           → Left pergunta ao Right
  cortex_bridge.py answer "resposta" --id X → Right responde
  cortex_bridge.py delegate "tarefa"        → Left delega ao Right  
  cortex_bridge.py done "resultado" --id X  → Right entrega
  cortex_bridge.py notify "alerta"          → Qualquer lobo notifica
  cortex_bridge.py read                     → Lê mensagens não lidas
  cortex_bridge.py status                   → Status da ponte
  cortex_bridge.py consult "tópico"         → Left consulta Right (ask + wait)
"""

import json, sys, time
from datetime import datetime, timezone
from pathlib import Path

SYNC_FILE = Path.home() / ".hermes" / "cortex_sync.json"

def _now():
    return datetime.now(timezone.utc).isoformat()

def _load():
    if SYNC_FILE.exists():
        return json.loads(SYNC_FILE.read_text())
    return {
        "version": "1.0",
        "created": _now(),
        "messages": [],
        "pending_tasks": [],
        "shared_state": {},
        "stats": {"left_queries": 0, "right_answers": 0, "delegations": 0}
    }

def _save(data):
    SYNC_FILE.parent.mkdir(parents=True, exist_ok=True)
    SYNC_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))

def _next_id(data):
    return f"ctx-{len(data['messages'])+1:04d}"

# ══════════════════════════════════════════
# LEFT → RIGHT (Hermes consulta Codex)
# ══════════════════════════════════════════

def left_ask(question, context=None):
    """Lobo Esquerdo pergunta ao Lobo Direito."""
    data = _load()
    msg = {
        "id": _next_id(data),
        "direction": "LEFT→RIGHT",
        "type": "query",
        "content": question,
        "context": context,
        "sent_at": _now(),
        "status": "pending",
        "response": None
    }
    data["messages"].append(msg)
    data["stats"]["left_queries"] += 1
    _save(data)
    return msg["id"]

def left_delegate(task, context=None):
    """Lobo Esquerdo delega tarefa ao Lobo Direito."""
    data = _load()
    task_obj = {
        "id": _next_id(data),
        "direction": "LEFT→RIGHT",
        "type": "delegation",
        "content": task,
        "context": context,
        "sent_at": _now(),
        "status": "pending",
        "result": None
    }
    data["pending_tasks"].append(task_obj)
    data["messages"].append(task_obj)
    data["stats"]["delegations"] += 1
    _save(data)
    return task_obj["id"]

# ══════════════════════════════════════════
# RIGHT → LEFT (Codex responde ao Hermes)
# ══════════════════════════════════════════

def right_answer(msg_id, response):
    """Lobo Direito responde a uma pergunta do Lobo Esquerdo."""
    data = _load()
    for msg in data["messages"]:
        if msg["id"] == msg_id:
            msg["response"] = response
            msg["status"] = "answered"
            msg["answered_at"] = _now()
            data["stats"]["right_answers"] += 1
            _save(data)
            return True
    return False

def right_done(task_id, result):
    """Lobo Direito entrega resultado de tarefa delegada."""
    data = _load()
    for task in data["pending_tasks"]:
        if task["id"] == task_id:
            task["result"] = result
            task["status"] = "completed"
            task["completed_at"] = _now()
            _save(data)
            return True
    return False

# ══════════════════════════════════════════
# BIDIRECIONAL
# ══════════════════════════════════════════

def notify(lobe, alert):
    """Qualquer lobo notifica o outro."""
    data = _load()
    msg = {
        "id": _next_id(data),
        "direction": f"{lobe}→OTHER",
        "type": "notification",
        "content": alert,
        "sent_at": _now(),
        "status": "unread"
    }
    data["messages"].append(msg)
    _save(data)
    return msg["id"]

def read_unread(lobe=None):
    """Lê mensagens não lidas (filtradas por direção se lobe especificado)."""
    data = _load()
    unread = [m for m in data["messages"] if m.get("status") in ("pending", "unread")]
    
    if lobe == "left":
        unread = [m for m in unread if "RIGHT→" in m.get("direction", "")]
    elif lobe == "right":
        unread = [m for m in unread if "LEFT→" in m.get("direction", "")]
    
    return unread

def status():
    """Status completo da ponte."""
    data = _load()
    unread = read_unread()
    pending = [t for t in data.get("pending_tasks", []) if t["status"] == "pending"]
    
    return {
        "version": data["version"],
        "total_messages": len(data["messages"]),
        "unread": len(unread),
        "pending_tasks": len(pending),
        "pending_queries": len([m for m in unread if m.get("type") == "query"]),
        "stats": data["stats"],
        "last_activity": data["messages"][-1]["sent_at"] if data["messages"] else None
    }

def update_shared_state(key, value):
    """Atualiza estado compartilhado entre lobos."""
    data = _load()
    data["shared_state"][key] = {
        "value": value,
        "updated_at": _now()
    }
    _save(data)

def get_shared_state(key=None):
    """Lê estado compartilhado."""
    data = _load()
    if key:
        return data["shared_state"].get(key, {}).get("value")
    return data["shared_state"]

# ══════════════════════════════════════════
# CONSULTA (ask + wait pattern)
# ══════════════════════════════════════════

def consult(question, context=None, timeout=120):
    """Left consulta Right e espera resposta (modo síncrono)."""
    msg_id = left_ask(question, context)
    
    start = time.time()
    while time.time() - start < timeout:
        data = _load()
        for msg in data["messages"]:
            if msg["id"] == msg_id and msg.get("response"):
                return msg["response"]
        time.sleep(5)
    
    return None  # timeout


# ══════════════════════════════════════════
# CLI
# ══════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Córtex Bridge — Lobo Esquerdo ↔ Lobo Direito")
    sub = parser.add_subparsers(dest="cmd")
    
    ask = sub.add_parser("ask", help="Left→Right: pergunta")
    ask.add_argument("question")
    ask.add_argument("--context")
    
    answer = sub.add_parser("answer", help="Right→Left: responde")
    answer.add_argument("response")
    answer.add_argument("--id", required=True)
    
    delegate = sub.add_parser("delegate", help="Left→Right: delega tarefa")
    delegate.add_argument("task")
    delegate.add_argument("--context")
    
    done = sub.add_parser("done", help="Right→Left: entrega resultado")
    done.add_argument("result")
    done.add_argument("--id", required=True)
    
    notify_p = sub.add_parser("notify", help="Notifica outro lobo")
    notify_p.add_argument("lobe", choices=["LEFT", "RIGHT"])
    notify_p.add_argument("alert")
    
    read_p = sub.add_parser("read", help="Lê mensagens não lidas")
    read_p.add_argument("--lobe", choices=["left", "right"])
    
    status_p = sub.add_parser("status", help="Status da ponte")
    
    state_set = sub.add_parser("state-set", help="Atualiza estado compartilhado")
    state_set.add_argument("key")
    state_set.add_argument("value")
    
    state_get = sub.add_parser("state-get", help="Lê estado compartilhado")
    state_get.add_argument("key", nargs="?")
    
    consult_p = sub.add_parser("consult", help="Left consulta Right (ask + wait)")
    consult_p.add_argument("question")
    consult_p.add_argument("--context")
    consult_p.add_argument("--timeout", type=int, default=120)
    
    args = parser.parse_args()
    
    if args.cmd == "ask":
        mid = left_ask(args.question, args.context)
        print(json.dumps({"status": "asked", "id": mid}))
    
    elif args.cmd == "answer":
        ok = right_answer(args.id, args.response)
        print(json.dumps({"status": "ok" if ok else "not_found"}))
    
    elif args.cmd == "delegate":
        tid = left_delegate(args.task, args.context)
        print(json.dumps({"status": "delegated", "id": tid}))
    
    elif args.cmd == "done":
        ok = right_done(args.id, args.result)
        print(json.dumps({"status": "ok" if ok else "not_found"}))
    
    elif args.cmd == "notify":
        mid = notify(args.lobe, args.alert)
        print(json.dumps({"status": "sent", "id": mid}))
    
    elif args.cmd == "read":
        msgs = read_unread(args.lobe)
        if msgs:
            for m in msgs:
                direction = m["direction"]
                content = m.get("content", "")[:200]
                response = m.get("response", "")
                result = m.get("result", "")
                print(f"[{m['id']}] {direction} | {m['type']}")
                print(f"  Q: {content}")
                if response:
                    print(f"  R: {response[:200]}")
                if result:
                    print(f"  ✓: {result[:200]}")
                print()
        else:
            print("📭 Nenhuma mensagem pendente.")
    
    elif args.cmd == "status":
        s = status()
        print(f"🧠 Ponte Córtex Bi-Hemisférico")
        print(f"  Total: {s['total_messages']} mensagens")
        print(f"  Pendentes: {s['unread']} (queries: {s['pending_queries']})")
        print(f"  Tarefas ativas: {s['pending_tasks']}")
        print(f"  Stats: {s['stats']}")
        if s['last_activity']:
            print(f"  Última atividade: {s['last_activity'][:19]}")
    
    elif args.cmd == "state-set":
        update_shared_state(args.key, args.value)
        print(json.dumps({"status": "ok", "key": args.key}))
    
    elif args.cmd == "state-get":
        val = get_shared_state(args.key)
        print(json.dumps(val, indent=2, ensure_ascii=False))
    
    elif args.cmd == "consult":
        result = consult(args.question, args.context, args.timeout)
        if result:
            print(result)
        else:
            print(json.dumps({"status": "timeout", "note": "Right lobe não respondeu"}))
    
    else:
        parser.print_help()
