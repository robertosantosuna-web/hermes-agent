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

def left_ask(question, context=None):
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

def right_answer(msg_id, response):
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
    data = _load()
    for task in data["pending_tasks"]:
        if task["id"] == task_id:
            task["result"] = result
            task["status"] = "completed"
            task["completed_at"] = _now()
            _save(data)
            return True
    return False

def notify(lobe, alert):
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
    data = _load()
    unread = [m for m in data["messages"] if m.get("status") in ("pending", "unread")]
    if lobe == "left":
        unread = [m for m in unread if "RIGHT→" in m.get("direction", "")]
    elif lobe == "right":
        unread = [m for m in unread if "LEFT→" in m.get("direction", "")]
    return unread

def status():
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
    data = _load()
    data["shared_state"][key] = {"value": value, "updated_at": _now()}
    _save(data)

def get_shared_state(key=None):
    data = _load()
    if key: return data["shared_state"].get(key, {}).get("value")
    return data["shared_state"]

def consult(question, context=None, timeout=120):
    msg_id = left_ask(question, context)
    start = time.time()
    while time.time() - start < timeout:
        data = _load()
        for msg in data["messages"]:
            if msg["id"] == msg_id and msg.get("response"):
                return msg["response"]
        time.sleep(5)
    return None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Córtex Bridge — Lobo Esquerdo ↔ Lobo Direito")
    sub = parser.add_subparsers(dest="cmd")
    for name, args_list, help_text in [
        ("ask", [("question",), ("--context",)], "Left→Right: pergunta"),
        ("delegate", [("task",), ("--context",)], "Left→Right: delega tarefa"),
        ("consult", [("question",), ("--context",), ("--timeout", int, 120)], "Left consulta Right (ask+wait)"),
    ]:
        p = sub.add_parser(name, help=help_text)
        for a in args_list:
            if isinstance(a, tuple) and len(a) == 3:
                p.add_argument(a[0], type=a[1], default=a[2])
            elif isinstance(a, tuple):
                p.add_argument(a[0])
    answer = sub.add_parser("answer", help="Right→Left: responde"); answer.add_argument("response"); answer.add_argument("--id", required=True)
    done = sub.add_parser("done", help="Right→Left: entrega"); done.add_argument("result"); done.add_argument("--id", required=True)
    notify_p = sub.add_parser("notify"); notify_p.add_argument("lobe", choices=["LEFT","RIGHT"]); notify_p.add_argument("alert")
    read_p = sub.add_parser("read"); read_p.add_argument("--lobe", choices=["left","right"])
    sub.add_parser("status")
    state_set = sub.add_parser("state-set"); state_set.add_argument("key"); state_set.add_argument("value")
    state_get = sub.add_parser("state-get"); state_get.add_argument("key", nargs="?")
    args = parser.parse_args()
    
    actions = {
        "ask": lambda: print(json.dumps({"status":"asked","id":left_ask(args.question, args.context)})),
        "answer": lambda: print(json.dumps({"status":"ok" if right_answer(args.id, args.response) else "not_found"})),
        "delegate": lambda: print(json.dumps({"status":"delegated","id":left_delegate(args.task, args.context)})),
        "done": lambda: print(json.dumps({"status":"ok" if right_done(args.id, args.result) else "not_found"})),
        "notify": lambda: print(json.dumps({"status":"sent","id":notify(args.lobe, args.alert)})),
        "read": lambda: ([print(f"[{m['id']}] {m['direction']} | {m['type']}\n  Q: {m.get('content','')[:200]}\n  R: {m.get('response','')[:200]}{m.get('result','')[:200]}") for m in read_unread(args.lobe)] if read_unread(args.lobe) else print("📭 Nenhuma mensagem pendente.")),
        "status": lambda: print(f"🧠 Ponte Córtex\n  Total: {(s:=status())['total_messages']} | Pendentes: {s['unread']} | Stats: {s['stats']}"),
        "state-set": lambda: (update_shared_state(args.key, args.value), print(json.dumps({"status":"ok"}))),
        "state-get": lambda: print(json.dumps(get_shared_state(args.key), indent=2, ensure_ascii=False)),
        "consult": lambda: print(consult(args.question, args.context, args.timeout) or json.dumps({"status":"timeout"})),
    }
    actions.get(args.cmd, lambda: parser.print_help())()
