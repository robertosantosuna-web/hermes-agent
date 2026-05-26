#!/usr/bin/env python3
"""
Knowledge Bridge — Arquivo compartilhado entre Agente e Cérebro.
Ambos leem e escrevem descobertas. NÃO mistura logs — cada um tem seu próprio.
Este arquivo é só para CONFRONTO e ABSORÇÃO de conhecimento.

Uso:
  python3 knowledge_bridge.py write agent "Descoberta: USDJPY formou CHoCH..."
  python3 knowledge_bridge.py write brain "Descoberta: FVG 8 pips em EURUSD..."
  python3 knowledge_bridge.py read              # Lê todas as descobertas
  python3 knowledge_bridge.py read --source agent  # Lê só do agente
  python3 knowledge_bridge.py read --since 2026-05-23  # Desde data
  python3 knowledge_bridge.py absorb           # Absorve conhecimento (consolida)
"""
import json, sys, argparse
from datetime import datetime, timezone, date
from pathlib import Path

BRIDGE_FILE = Path.home() / ".hermes" / "forex" / "knowledge_bridge.json"

def load():
    if BRIDGE_FILE.exists():
        return json.loads(BRIDGE_FILE.read_text())
    return {"discoveries": [], "absorbed": [], "meta": {"version": "1.0"}}

def save(data):
    BRIDGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    BRIDGE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))

def cmd_write(source, content):
    bridge = load()
    entry = {
        "id": f"disc-{len(bridge['discoveries'])+1:04d}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,  # "agent" ou "brain"
        "content": content,
        "absorbed_by_other": False
    }
    bridge["discoveries"].append(entry)
    save(bridge)
    
    # Atualiza também o contexto do outro
    update_other_context(source, content)
    
    print(f"✅ {source}: descoberta registrada ({entry['id']})")

def update_other_context(source, content):
    """Notifica o outro lado sobre nova descoberta."""
    hermes = Path.home() / ".hermes"
    
    if source == "agent":
        # Atualizar brain_context
        ctx_file = hermes / "brain_context.json"
    else:
        ctx_file = hermes / "agent_context.json"
    
    if ctx_file.exists():
        ctx = json.loads(ctx_file.read_text())
        if "knowledge_updates" not in ctx:
            ctx["knowledge_updates"] = []
        ctx["knowledge_updates"].append({
            "from": source,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": content[:200]
        })
        # Manter só últimos 20
        ctx["knowledge_updates"] = ctx["knowledge_updates"][-20:]
        ctx_file.write_text(json.dumps(ctx, indent=2, ensure_ascii=False))

def cmd_read(source=None, since=None):
    bridge = load()
    discoveries = bridge["discoveries"]
    
    if source:
        discoveries = [d for d in discoveries if d["source"] == source]
    if since:
        discoveries = [d for d in discoveries if d["timestamp"][:10] >= since]
    
    if not discoveries:
        print("📭 Nenhuma descoberta.")
        return
    
    print(f"🧠 Knowledge Bridge — {len(discoveries)} descobertas\n")
    
    for d in discoveries:
        emoji = "🤖" if d["source"] == "agent" else "🧠"
        absorbed = " [ABSORVIDO]" if d.get("absorbed_by_other") else ""
        print(f"{emoji} [{d['timestamp'][:16]}] {d['content'][:200]}{absorbed}")
    
    # Mostrar também o que já foi absorvido
    if bridge.get("absorbed"):
        print(f"\n📚 Conhecimento absorvido: {len(bridge['absorbed'])} itens")
        for a in bridge["absorbed"][-5:]:
            print(f"   ✅ {a['summary'][:150]}")

def cmd_absorb(source):
    """Marca descobertas do outro como absorvidas e gera resumo."""
    bridge = load()
    other = "brain" if source == "agent" else "agent"
    
    unabsorbed = [d for d in bridge["discoveries"] 
                  if d["source"] == other and not d.get("absorbed_by_other")]
    
    if not unabsorbed:
        print(f"📭 Nada novo para absorver do {other}.")
        return
    
    summary = f"{source} absorveu {len(unabsorbed)} descobertas do {other} em {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
    
    bridge["absorbed"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "from": other,
        "count": len(unabsorbed),
        "discoveries": [d["id"] for d in unabsorbed],
        "summary": summary
    })
    
    for d in unabsorbed:
        d["absorbed_by_other"] = True
    
    save(bridge)
    print(f"✅ {summary}")

def main():
    parser = argparse.ArgumentParser(description="Knowledge Bridge Agent↔Brain")
    sub = parser.add_subparsers(dest="cmd")
    
    w = sub.add_parser("write")
    w.add_argument("source", choices=["agent", "brain"])
    w.add_argument("content")
    
    r = sub.add_parser("read")
    r.add_argument("--source", choices=["agent", "brain"])
    r.add_argument("--since")
    
    a = sub.add_parser("absorb")
    a.add_argument("source", choices=["agent", "brain"])
    
    args = parser.parse_args()
    
    if args.cmd == "write":
        cmd_write(args.source, args.content)
    elif args.cmd == "read":
        cmd_read(args.source, args.since)
    elif args.cmd == "absorb":
        cmd_absorb(args.source)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
