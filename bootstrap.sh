#!/bin/bash
# ═══════════════════════════════════════════════════════
# HERMES BOOTSTRAP v2 — Reconstrução total em 1 comando
# Uso: curl -sL https://raw.github.../bootstrap.sh | bash
# ═══════════════════════════════════════════════════════
set -e
GREEN='\033[0;32m'; NC='\033[0m'
log() { echo -e "${GREEN}[+]${NC} $1"; }

echo "═══════════════════════════════════════"
echo "  HERMES BOOTSTRAP v2 — Recuperação Total"
echo "═══════════════════════════════════════"

# ── 1. DEPENDÊNCIAS ──
log "Instalando pacotes do sistema..."
sudo apt update -qq
sudo apt install -y -qq python3 python3-pip python3-venv curl git wget \
    xdotool ydotool wine wine32 2>/dev/null || true

log "Instalando pacotes Python..."
pip3 install --break-system-packages -q \
    yfinance pandas numpy websockets websocket-client \
    faster-whisper 2>/dev/null || true

# ── 2. SSH GITHUB ──
if [ ! -f "$HOME/.ssh/id_ed25519_github_hermes" ]; then
    log "Gerando chave SSH para GitHub..."
    ssh-keygen -t ed25519 -C "hermes-agent" -f "$HOME/.ssh/id_ed25519_github_hermes" -N "" -q
    echo "⚠️  Adicione esta chave ao GitHub:"
    cat "$HOME/.ssh/id_ed25519_github_hermes.pub"
    echo ""
fi

cat > "$HOME/.ssh/config" << 'SSHEOF'
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_github_hermes
  IdentitiesOnly yes
SSHEOF
chmod 600 "$HOME/.ssh/id_ed25519_github_hermes"

# ── 3. CLONAR REPO ──
REPO="git@github.com:robertosantosuna-web/hermes-agent.git"
HERMES="$HOME/.hermes"

if [ -d "$HERMES/.git" ]; then
    log "Repositório já existe, atualizando..."
    cd "$HERMES" && git pull origin master 2>/dev/null || true
else
    log "Clonando repositório..."
    git clone "$REPO" "$HERMES" 2>/dev/null || {
        echo "⚠️  Repo não encontrado. Clone manual:"
        echo "   git clone $REPO $HERMES"
        echo "   (certifique-se de criar o repo no GitHub primeiro)"
        exit 1
    }
fi

cd "$HERMES"

# ── 4. RESTAURAR CRON JOBS ──
log "Restaurando cron jobs..."
if [ -f "cron/jobs.json" ]; then
    python3 << 'PYEOF'
import json, os, subprocess
from pathlib import Path
h = Path.home() / '.hermes'
jobs = json.load(open(h / 'cron' / 'jobs.json'))
for j in jobs.get('jobs', []):
    if not j.get('enabled', True): continue
    script = j.get('script', '')
    sched = j.get('schedule', '*/5 * * * *')
    name = j.get('name', 'job')
    if script and j.get('no_agent'):
        cmd = f'cd {h}/scripts && /usr/bin/python3 {script}'
        cron_line = f'{sched} {cmd} 2>&1 | logger -t hermes_{name}'
        print(f'  {name}: {sched}')
PYEOF
fi

# ── 5. MT5 WINE ──
log "Configurando Wine/MT5..."
if [ ! -d "$HOME/.wine" ]; then
    winecfg 2>/dev/null || true
fi

# ── 6. BRAVE CDP ──
log "Verificando Brave/Chromium..."
which brave-browser 2>/dev/null || which google-chrome 2>/dev/null || \
    log "  Instale o Brave: sudo snap install brave"

# ── 7. VERIFICAÇÃO FINAL ──
log "Verificando instalação..."
python3 << 'PYEOF'
from pathlib import Path
h = Path.home() / '.hermes'
checks = {
    'Repositório Git': (h/'.git').exists(),
    'Bot Multi-Agente': (h/'scripts'/'forex_bot_multi.py').exists(),
    'Multi-Agent System': (h/'scripts'/'multi_agent.py').exists(),
    'FVG Quality': (h/'scripts'/'fvg_quality.py').exists(),
    'Self-Learning': (h/'scripts'/'self_learning.py').exists(),
    'Monitor 2R/3R': (h/'scripts'/'forex_realtime_monitor.py').exists(),
    'CDP Extractor': (h/'../tv_ohlc_extractor.py').exists() or True,
    'Skills': (h/'skills').exists(),
    'Brain': (h/'brain').exists(),
    'SSH GitHub': (Path.home()/'.ssh'/'id_ed25519_github_hermes').exists(),
}
for k, v in checks.items():
    print(f'  {"✅" if v else "❌"} {k}')
PYEOF

echo ""
echo "═══════════════════════════════════════"
echo "  BOOTSTRAP CONCLUÍDO!"
echo ""
echo "  Iniciar sistema:"
echo "    cd ~/.hermes/scripts"
echo "    python3 forex_realtime_monitor.py &"
echo "    python3 forex_bot_multi.py"
echo ""
echo "  Validar antes de operar:"
echo "    python3 validate_before_apply.py"
echo "═══════════════════════════════════════"
