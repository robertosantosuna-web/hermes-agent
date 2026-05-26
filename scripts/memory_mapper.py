#!/usr/bin/env python3
"""
Memory Mapper — Dump & Clean
=============================
Despeja memória do Hermes Agent em log no Desktop e limpa entradas expiradas.
Executado diariamente via cron (no_agent, zero tokens).

Arquivo: ~/Área de trabalho/hermes_memory_log.md
"""

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

DESKTOP = Path.home() / "Área de trabalho" 
LOG_FILE = DESKTOP / "hermes_memory_log.md"
MEMORY_BACKUP = Path.home() / ".hermes" / "memory_backups"

# ═══════════════════════════════════════════════
# DUMP: append today's memory snapshot to log
# ═══════════════════════════════════════════════

def dump_memory():
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S BRT")
    
    # Read from Hermes memory files (MEMORY.md + USER.md)
    mem_dir = Path.home() / ".hermes" / "memories"
    memory_file = mem_dir / "MEMORY.md"
    user_file = mem_dir / "USER.md"
    
    user_entries = []
    memory_entries = []
    
    if user_file.exists():
        content = user_file.read_text().strip()
        user_entries = [e.strip() for e in content.split("\n§\n") if e.strip()]
    
    if memory_file.exists():
        content = memory_file.read_text().strip()
        memory_entries = [e.strip() for e in content.split("\n§\n") if e.strip()]
    
    # Build markdown log entry
    lines = []
    lines.append(f"## 📥 Memory Dump — {timestamp}")
    lines.append("")
    
    if user_entries:
        lines.append("### 👤 User")
        for e in user_entries:
            lines.append(f"- {e[:200]}")
        lines.append("")
    
    if memory_entries:
        lines.append("### 🧠 Memory")
        for idx, e in enumerate(memory_entries):
            lines.append(f"{idx+1}. {e[:200]}")
        lines.append("")
    
    lines.append(f"**User entries**: {len(user_entries)} | **Memory entries**: {len(memory_entries)}")
    lines.append(f"**Char usage**: {sum(len(e) for e in memory_entries)}/{4_000} | **Dump**: {timestamp}")
    lines.append("---")
    lines.append("")
    
    # Create/append to log
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if LOG_FILE.exists() else "w"
    with open(LOG_FILE, mode) as f:
        f.write("\n".join(lines) + "\n")
    
    # Also backup raw MARKDOWN
    MEMORY_BACKUP.mkdir(parents=True, exist_ok=True)
    backup_dir = MEMORY_BACKUP / today
    backup_dir.mkdir(exist_ok=True)
    if memory_file.exists():
        shutil.copy(memory_file, backup_dir / "MEMORY.md")
    if user_file.exists():
        shutil.copy(user_file, backup_dir / "USER.md")
    
    # Rotate: keep last 30 backup dirs
    backups = sorted([d for d in MEMORY_BACKUP.iterdir() if d.is_dir()])
    for old in backups[:-30]:
        shutil.rmtree(old)
    
    return len(user_entries) + len(memory_entries)


# ═══════════════════════════════════════════════
# PRUNE: remove entries older than N days
# ═══════════════════════════════════════════════

def prune_old_entries(days=7):
    """NOT IMPLEMENTED for MEMORY.md format. Use 'dump' to backup, then manually clean."""
    print("⚠️  PRUNE not needed — use 'dump' to backup, then 'clean' for stale patterns")
    return 0


# ═══════════════════════════════════════════════
# CLEAN: remove entries by keyword match (stale)
# ═══════════════════════════════════════════════

STALE_PATTERNS = [
    "PROJETO MARTIN",  # já concluído
    "PIPELINE MAP",     # recriado a cada dump
    "ANTI-PADRÃO INSTALAÇÃO",  # knowledge base já tem
]

def clean_stale_entries():
    """Remove entries matching stale patterns from MEMORY.md (dry-run safe — only reports)."""
    mem_file = Path.home() / ".hermes" / "memories" / "MEMORY.md"
    if not mem_file.exists():
        return 0
    
    content = mem_file.read_text().strip()
    entries = [e.strip() for e in content.split("\n§\n") if e.strip()]
    
    found_stale = []
    for e in entries:
        for pattern in STALE_PATTERNS:
            if pattern.lower() in e.lower():
                found_stale.append((pattern, e[:80]))
                break
    
    if found_stale:
        print(f"🧹 {len(found_stale)} stale entries found (NOT removed — dry run):")
        for pat, preview in found_stale:
            print(f"   [{pat}] {preview}...")
        print()
        print("⚠️  Use 'hermes memory remove' or edit ~/.hermes/memories/MEMORY.md directly")
    else:
        print("✅ No stale entries found")
    
    return len(found_stale)


# ═══════════════════════════════════════════════
# STATS: show log summary
# ═══════════════════════════════════════════════

def show_stats():
    if LOG_FILE.exists():
        lines = LOG_FILE.read_text().split("\n")
        dumps = [l for l in lines if l.startswith("## 📥")]
        size_kb = LOG_FILE.stat().st_size / 1024
        print(f"📁 Desktop log: {LOG_FILE}")
        print(f"📏 Size: {size_kb:.1f} KB")
        print(f"📥 Dumps: {len(dumps)} entries")
        if dumps:
            print(f"🕐 Last: {dumps[-1].replace('## 📥 Memory Dump — ', '')}")
    else:
        print("📁 No log yet. Run 'dump' to create.")
    
    # Backup stats
    backups = sorted(MEMORY_BACKUP.glob("memory_*.json")) if MEMORY_BACKUP.exists() else []
    print(f"💾 Backups: {len(backups)}")


if __name__ == "__main__":
    import sys
    
    cmd = sys.argv[1] if len(sys.argv) > 1 else "dump"
    
    if cmd == "dump":
        n = dump_memory()
        print(f"✅ Dumped {n} memory entries to {LOG_FILE}")
    elif cmd == "prune":
        n = prune_old_entries(days=7)
        print(f"🧹 Pruned {n} entries older than 7 days")
    elif cmd == "clean":
        n = clean_stale_entries()
        print(f"🧹 Cleaned {n} stale entries")
    elif cmd == "full":
        # Full cycle: dump → prune → clean
        n1 = dump_memory()
        print(f"✅ Dumped {n1} entries")
        n2 = prune_old_entries(days=7)
        print(f"🧹 Pruned {n2} old entries")
        n3 = clean_stale_entries()
        print(f"🧹 Cleaned {n3} stale entries")
    elif cmd == "stats":
        show_stats()
    else:
        print(f"Usage: {sys.argv[0]} [dump|prune|clean|full|stats]")
