#!/usr/bin/env python3
"""
Lore — Local Memory Engine for Hermes
======================================
Armazenamento vetorial com namespaces separados.
  NVMe: ~/.hermes/lore/{agent,brain}/store/
  RAM:  numpy arrays (cache durante search)

Namespaces:
  agent  → conhecimento do Hermes Agent (MEMORY.md, decisões, contexto)
  brain  → conhecimento do Cérebro (brain_context.json, neural, forex)

Os dois NUNCA se misturam. Search pode cruzar ou isolar.

Usage:
  lore.py agent add "texto"           # Memória do agente
  lore.py brain add "texto"           # Memória do cérebro
  lore.py agent search "query" 5      # Busca só no agente
  lore.py brain search "query" 5      # Busca só no cérebro
  lore.py search "query" 5            # Busca em ambos (identificado)
  lore.py agent ingest                # Importa do MEMORY.md
  lore.py brain ingest                # Importa do brain_context.json
  lore.py agent stats                 # Estatísticas do agente
  lore.py brain stats                 # Estatísticas do cérebro
  lore.py stats                       # Estatísticas combinadas
"""

import json
import sqlite3
import numpy as np
import sys
import hashlib
from datetime import datetime
from pathlib import Path

LORE_DIR = Path.home() / ".hermes" / "lore"

NAMESPACES = {
    "agent": {
        "dir": LORE_DIR / "agent",
        "description": "Hermes Agent memory — decisões, contexto, ferramentas, preferências",
        "ingest_source": "memory.md",
    },
    "brain": {
        "dir": LORE_DIR / "brain",
        "description": "Cérebro autônomo — forex, neural, padrões, research, aprendizado",
        "ingest_source": "brain_context.json",
    },
}


def get_store(ns):
    """Get paths for a namespace."""
    d = NAMESPACES[ns]["dir"]
    d.mkdir(parents=True, exist_ok=True)
    store = d / "store"
    store.mkdir(exist_ok=True)
    return {
        "db": d / "lore.db",
        "embeddings": store / "embeddings.npy",
        "index": store / "index.json",
    }


def get_db(ns):
    """Get SQLite connection for namespace."""
    paths = get_store(ns)
    conn = sqlite3.connect(str(paths["db"]))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            tags TEXT,
            source TEXT,
            created_at TEXT,
            embedding_idx INTEGER,
            char_count INTEGER
        )
    """)
    return conn


def text_to_vector(text, dim=256):
    """Character n-gram hash → normalized vector. Zero deps além de numpy."""
    text = text.lower()
    vec = np.zeros(dim, dtype=np.float32)
    for i in range(len(text) - 1):
        vec[hash(text[i:i+2]) % dim] += 1
    for i in range(len(text) - 2):
        vec[hash(text[i:i+3]) % dim] += 0.5
    norm = np.linalg.norm(vec)
    return (vec / norm).astype(np.float32) if norm > 0 else vec


def add_memory(ns, content, tags=None, source="manual"):
    """Add entry to namespace."""
    paths = get_store(ns)
    conn = get_db(ns)
    
    mem_id = hashlib.md5((ns + content).encode()).hexdigest()[:12]
    
    existing = conn.execute("SELECT id FROM memories WHERE id=?", (mem_id,)).fetchone()
    if existing:
        conn.close()
        return {"status": "duplicate", "id": mem_id, "namespace": ns}
    
    vec = text_to_vector(content)
    
    # Load or init embeddings
    if paths["embeddings"].exists():
        embeddings = np.load(str(paths["embeddings"]))
    else:
        embeddings = np.array([], dtype=np.float32).reshape(0, 256)
    
    index_data = {}
    if paths["index"].exists():
        index_data = json.loads(paths["index"].read_text())
    
    idx = index_data.get("count", 0)
    
    if embeddings.size == 0:
        embeddings = vec.reshape(1, -1)
    else:
        embeddings = np.vstack([embeddings, vec.reshape(1, -1)])
    
    np.save(str(paths["embeddings"]), embeddings)
    index_data["ids"] = index_data.get("ids", []) + [mem_id]
    index_data["count"] = idx + 1
    paths["index"].write_text(json.dumps(index_data))
    
    conn.execute(
        "INSERT INTO memories (id, content, tags, source, created_at, embedding_idx, char_count) VALUES (?,?,?,?,?,?,?)",
        (mem_id, content, ",".join(tags) if tags else "", source,
         datetime.now().isoformat(), idx, len(content))
    )
    conn.commit()
    conn.close()
    
    return {"status": "ok", "id": mem_id, "namespace": ns, "idx": idx, "chars": len(content)}


def search_ns(ns, query, top_k=5, min_score=0.1):
    """Search within one namespace."""
    paths = get_store(ns)
    if not paths["embeddings"].exists():
        return []
    
    embeddings = np.load(str(paths["embeddings"]))
    if embeddings.size == 0:
        return []
    
    index_data = json.loads(paths["index"].read_text()) if paths["index"].exists() else {}
    ids = index_data.get("ids", [])
    
    query_vec = text_to_vector(query).reshape(1, -1)
    scores = np.dot(embeddings, query_vec.T).flatten()
    
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    conn = get_db(ns)
    results = []
    for idx in top_indices:
        score = float(scores[idx])
        if score < min_score or idx >= len(ids):
            continue
        row = conn.execute(
            "SELECT content, tags, source, created_at FROM memories WHERE id=?",
            (ids[idx],)
        ).fetchone()
        if row:
            results.append({
                "content": row[0][:200], "tags": row[1], "source": row[2],
                "created": row[3], "score": round(score, 4), "id": ids[idx],
                "namespace": ns,
            })
    conn.close()
    return results


def search_all(query, top_k=5, min_score=0.1):
    """Search across ALL namespaces, interleaved by score."""
    all_results = []
    for ns in NAMESPACES:
        all_results.extend(search_ns(ns, query, top_k=top_k, min_score=min_score))
    all_results.sort(key=lambda r: r["score"], reverse=True)
    return all_results[:top_k]


def ingest_agent():
    """Import from MEMORY.md → agent namespace."""
    mem_file = Path.home() / ".hermes" / "memories" / "MEMORY.md"
    if not mem_file.exists():
        return {"status": "error", "message": "MEMORY.md not found"}
    content = mem_file.read_text().strip()
    entries = [e.strip() for e in content.split("\n§\n") if e.strip()]
    added = 0
    for entry in entries:
        r = add_memory("agent", entry, tags=["memory_md"], source="memory.md")
        if r["status"] == "ok":
            added += 1
    return {"status": "ok", "namespace": "agent", "imported": added, "total": len(entries)}


def ingest_brain():
    """Import from brain_context.json → brain namespace."""
    brain_file = Path.home() / ".hermes" / "brain_context.json"
    if not brain_file.exists():
        return {"status": "error", "message": "brain_context.json not found"}
    ctx = json.loads(brain_file.read_text())
    added = 0
    for update in ctx.get("knowledge_updates", []):
        text = json.dumps(update, ensure_ascii=False)
        r = add_memory("brain", text[:1000], tags=["knowledge_update"], source="brain_context")
        if r["status"] == "ok":
            added += 1
    fx = ctx.get("forex_status", {})
    if fx:
        r = add_memory("brain", json.dumps(fx, ensure_ascii=False), tags=["forex_status"], source="brain_context")
        if r["status"] == "ok":
            added += 1
    return {"status": "ok", "namespace": "brain", "imported": added}


def stats_ns(ns=None):
    """Get stats for namespace(s)."""
    namespaces = [ns] if ns else list(NAMESPACES.keys())
    result = {}
    for n in namespaces:
        conn = get_db(n)
        total = conn.execute("SELECT COUNT(*), SUM(char_count) FROM memories").fetchone()
        paths = get_store(n)
        emb_size = paths["embeddings"].stat().st_size if paths["embeddings"].exists() else 0
        db_size = paths["db"].stat().st_size if paths["db"].exists() else 0
        result[n] = {
            "entries": total[0] or 0,
            "chars": total[1] or 0,
            "storage_kb": round((emb_size + db_size) / 1024, 1),
            "description": NAMESPACES[n]["description"],
        }
        conn.close()
    return result


# ═══════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        s = stats_ns()
        total_e = sum(v["entries"] for v in s.values())
        total_c = sum(v["chars"] for v in s.values())
        total_kb = sum(v["storage_kb"] for v in s.values())
        print(f"📚 Lore — {total_e} entries, {total_c:,} chars, {total_kb:.0f}KB")
        for ns, st in s.items():
            print(f"  {ns}: {st['entries']} entries, {st['chars']:,} chars, {st['storage_kb']}KB")
        print(f"\n  Use: lore.py [agent|brain] [add|search|ingest|stats]")
        sys.exit(0)
    
    # Parse namespace from first arg or default
    ns = sys.argv[1] if sys.argv[1] in NAMESPACES else None
    
    if ns:
        cmd = sys.argv[2] if len(sys.argv) > 2 else "stats"
        args = sys.argv[3:]
    else:
        cmd = sys.argv[1]
        args = sys.argv[2:]
    
    if cmd == "add":
        content = args[0] if args else sys.stdin.read().strip()
        if not content:
            print("❌ No content")
            sys.exit(1)
        r = add_memory(ns, content)
        print(json.dumps(r, indent=2))
    
    elif cmd == "search":
        query = args[0] if args else ""
        top_k = int(args[1]) if len(args) > 1 else 5
        if not query:
            print("❌ No query")
            sys.exit(1)
        if ns:
            results = search_ns(ns, query, top_k=top_k)
        else:
            results = search_all(query, top_k=top_k)
        for i, r in enumerate(results):
            tag = f"[{r['namespace']}]" if not ns else ""
            print(f"\n#{i+1} {tag} [{r['score']:.4f}]")
            print(f"   {r['content'][:150]}")
        if not results:
            print("No results.")
    
    elif cmd == "ingest":
        if ns == "agent":
            r = ingest_agent()
        elif ns == "brain":
            r = ingest_brain()
        else:
            r = {"error": "Use: lore.py agent ingest | lore.py brain ingest"}
        print(json.dumps(r, indent=2))
    
    elif cmd == "stats":
        s = stats_ns(ns)
        for n, st in s.items():
            print(f"📚 {n}: {st['entries']} entries, {st['chars']:,} chars, {st['storage_kb']}KB")
            print(f"   {st['description']}")
    
    else:
        print(f"Unknown: {cmd}")
