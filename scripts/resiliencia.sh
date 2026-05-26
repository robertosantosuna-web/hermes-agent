#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  RESILIÊNCIA ENTIDADE — Auto-repair & Health Check         ║
# ║  Roda a cada 30 min para garantir capacidades operacionais ║
# ╚══════════════════════════════════════════════════════════════╝

STATUS_FILE="$HOME/.hermes/estado/resiliencia.json"
mkdir -p "$(dirname "$STATUS_FILE")"

# ═══════════════════════════════════════════
# 1. EDGE CDP (porta 9222)
# ═══════════════════════════════════════════
CDP_OK=false
if ss -tlnp 2>/dev/null | grep -q '127.0.0.1:9222'; then
    CDP_OK=true
    CDP_PAGES=$(curl -s http://localhost:9222/json 2>/dev/null | python3 -c "import sys,json; print(len(json.loads(sys.stdin.read())))" 2>/dev/null || echo "?")
else
    # Tentar abrir Brave com CDP (não Edge)
    nohup brave-browser --remote-debugging-port=9222 --remote-allow-origins=* > /dev/null 2>&1 &
    sleep 3
    if ss -tlnp 2>/dev/null | grep -q '127.0.0.1:9222'; then
        CDP_OK=true
        CDP_PAGES="restarted"
    fi
fi

# ═══════════════════════════════════════════
# 2. INPUT (wtype, ydotool)
# ═══════════════════════════════════════════
WTYPE_OK=false
YDOTOOLD_OK=false

which wtype >/dev/null 2>&1 && WTYPE_OK=true
systemctl --user is-active ydotool.service >/dev/null 2>&1 && YDOTOOLD_OK=true

# ═══════════════════════════════════════════
# 3. TELEGRAM SESSION
# ═══════════════════════════════════════════
TELEGRAM_OK=false
if [ -f "$HOME/roberto3.session" ]; then
    SIZE=$(stat -c%s "$HOME/roberto3.session" 2>/dev/null || echo "0")
    if [ "$SIZE" -gt 1000 ]; then
        TELEGRAM_OK=true
    fi
fi

# ═══════════════════════════════════════════
# 4. CRON JOBS ATIVOS
# ═══════════════════════════════════════════
CRON_COUNT=$(hermes cron list 2>/dev/null | grep -c '✅\|active\|scheduled' || echo "?")

# ═══════════════════════════════════════════
# 5. DISK & MEMORY
# ═══════════════════════════════════════════
DISK_PCT=$(df -h / | awk 'NR==2{print $5}' | tr -d '%')
MEM_PCT=$(free | awk 'NR==2{printf "%.0f", $3/$2*100}')

# ═══════════════════════════════════════════
# OUTPUT
# ═══════════════════════════════════════════
cat > "$STATUS_FILE" << JSONEND
{
  "timestamp": "$(date -Iseconds)",
  "cdp": {"ok": $CDP_OK, "pages": "$CDP_PAGES"},
  "input": {"wtype": $WTYPE_OK, "ydotoold": $YDOTOOLD_OK},
  "telegram": {"session_ok": $TELEGRAM_OK},
  "system": {"disk_pct": $DISK_PCT, "mem_pct": $MEM_PCT, "cron_jobs": "$CRON_COUNT"}
}
JSONEND

# Reportar problemas
ISSUES=""
$CDP_OK || ISSUES="$ISSUES ⚠️EdgeCDP"
$WTYPE_OK || ISSUES="$ISSUES ⚠️Wtype"
[ "$DISK_PCT" -gt 85 ] && ISSUES="$ISSUES ⚠️Disk(${DISK_PCT}%)"
[ "$MEM_PCT" -gt 85 ] && ISSUES="$ISSUES ⚠️Mem(${MEM_PCT}%)"

if [ -n "$ISSUES" ]; then
    echo "❌ RESILIÊNCIA:$ISSUES"
else
    echo "✅ RESILIÊNCIA: Todos sistemas OK | CDP:$CDP_PAGES pgs | Disk:${DISK_PCT}% | Mem:${MEM_PCT}%"
fi
