#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Hermes Forex Bot — DEPLOY CONTA REAL OANDA ($100)
# ═══════════════════════════════════════════════════════════
# Este script prepara e ativa o bot de trading na conta real.
#
# PRÉ-REQUISITOS:
#   1. Conta OANDA real criada (https://www.oanda.com)
#   2. $100 depositados
#   3. MT5 conectado à conta real (servidor OANDA_Global-Live)
#   4. Xvfb :99 rodando com MT5
#   5. Python 3 com dependências: yfinance, numpy
#
# USO:
#   chmod +x forex_bot_real_deploy.sh
#   ./forex_bot_real_deploy.sh [check|dry-run|deploy|stop|status]
# ═══════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_DIR="$HOME/.hermes"
FOREX_DIR="$HERMES_DIR/forex"
SCRIPTS_DIR="$HERMES_DIR/scripts"
BOT_SCRIPT="$SCRIPTS_DIR/forex_bot_real.py"
STATE_FILE="$FOREX_DIR/real_state.json"
DAILY_STATE="$FOREX_DIR/real_daily_state.json"
TRADE_LOG="$FOREX_DIR/trade_log.json"
ALERT_LOG="$FOREX_DIR/alerts.log"
DEPLOY_MARKER="$FOREX_DIR/.real_deployed"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log()  { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1"; }
ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; }

# ═══════════════════════════════════════════════
# CHECK: Verificar todos os pré-requisitos
# ═══════════════════════════════════════════════
check_prerequisites() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 VERIFICAÇÃO DE PRÉ-REQUISITOS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    FAIL=0

    # 1. Bot script
    if [ -f "$BOT_SCRIPT" ]; then
        ok "Bot script: $BOT_SCRIPT"
    else
        err "Bot script NÃO encontrado: $BOT_SCRIPT"
        FAIL=1
    fi

    # 2. Python3
    if command -v python3 &>/dev/null; then
        PYVER=$(python3 --version 2>&1)
        ok "Python: $PYVER"
    else
        err "Python3 não encontrado"
        FAIL=1
    fi

    # 3. Dependências Python
    python3 -c "import yfinance" 2>/dev/null && ok "yfinance" || { warn "yfinance não instalado — rode: pip install yfinance"; FAIL=1; }
    python3 -c "import numpy" 2>/dev/null && ok "numpy" || { warn "numpy não instalado — rode: pip install numpy"; FAIL=1; }

    # 4. MT5 direto
    if [ -f "$SCRIPTS_DIR/mt5_direct.py" ]; then
        ok "MT5 direct executor: $SCRIPTS_DIR/mt5_direct.py"
    else
        err "mt5_direct.py não encontrado"
        FAIL=1
    fi

    # 5. Trade tracker
    if [ -f "$SCRIPTS_DIR/trade_tracker.py" ]; then
        ok "Trade tracker: $SCRIPTS_DIR/trade_tracker.py"
    else
        err "trade_tracker.py não encontrado"
        FAIL=1
    fi

    # 6. Xvfb :99
    if pgrep -f "Xvfb.*:99" > /dev/null 2>&1; then
        ok "Xvfb :99 rodando"
    else
        warn "Xvfb :99 NÃO detectado — MT5 precisa de display virtual"
        warn "   Inicie com: Xvfb :99 -screen 0 1920x1080x24 &"
    fi

    # 7. MT5 janela
    if DISPLAY=:99 xdotool search --name "MetaTrader" 2>/dev/null | grep -q .; then
        ok "MT5 detectado no Xvfb :99"
    else
        warn "MT5 NÃO detectado no Xvfb :99"
        warn "   Inicie o MT5 no Wine: DISPLAY=:99 wine 'C:\Program Files\MetaTrader 5\terminal64.exe' &"
    fi

    # 8. xdotool
    if command -v xdotool &>/dev/null; then
        ok "xdotool disponível"
    else
        err "xdotool não encontrado — sudo apt install xdotool"
        FAIL=1
    fi

    # 9. Conta OANDA real
    if grep -q "OANDA_Global-Live" "$FOREX_DIR/brokers.json" 2>/dev/null; then
        ok "Conta OANDA real configurada em brokers.json"
    else
        warn "Conta REAL OANDA NÃO configurada em brokers.json"
        warn "   ⚠️  AINDA NÃO EXISTE CONTA REAL — veja instruções abaixo"
    fi

    # 10. Arquivos de estado
    [ -f "$STATE_FILE" ] && ok "State file: $STATE_FILE" || warn "State file não existe (será criado)"
    [ -f "$DAILY_STATE" ] && ok "Daily state: $DAILY_STATE" || warn "Daily state não existe (será criado)"

    echo ""
    if [ $FAIL -eq 0 ]; then
        ok "TODOS os pré-requisitos OK!"
    else
        err "$FAIL pré-requisito(s) falhou(ram)"
    fi
    echo ""

    return $FAIL
}

# ═══════════════════════════════════════════════
# DRY-RUN: Simulação sem executar ordens
# ═══════════════════════════════════════════════
dry_run() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🧪 DRY RUN — Análise sem execução"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Simulando uma execução do bot..."
    echo ""

    python3 -c "
import json, os, sys
sys.path.insert(0, '$SCRIPTS_DIR')

# Load config do bot
exec(open('$BOT_SCRIPT').read().split(\"if __name__\")[0])

from datetime import datetime
now = datetime.now()

print(f'📅 Data: {now.strftime(\"%d/%m/%Y %H:%M\")} BRT')
print(f'💰 Saldo: \${get_balance():.2f}')
print(f'📊 Risco/trade: {RISK_PERCENT}%')
print(f'🛑 Stop diário: -{DAILY_STOP_PERCENT}%')
print(f'📈 Max posições: {MAX_POSITIONS}')
print(f'📐 Volume: {VOLUME} (microlote)')
print()

# Verificar stop diário
stopped, pnl, bal = check_daily_stop()
if stopped:
    print(f'⛔ STOP DIÁRIO ATIVO — P&L: \${pnl:.2f}')
    sys.exit(0)

# Verificar trading day
can_trade, reason = should_trade()
if not can_trade:
    print(f'⏸️  Trading pausado: {reason}')
    sys.exit(0)

active = count_active_positions()
print(f'📊 Posições ativas: {active}/{MAX_POSITIONS}')

if active >= MAX_POSITIONS:
    print('🛑 Limite de posições atingido')
    sys.exit(0)

# Análise de sinais (sem executar)
print()
print('🔍 Buscando sinais...')
import yfinance as yf
found_any = False
for pair, cfg in PAIRS.items():
    try:
        ticker = yf.Ticker(cfg['sym'])
        df = ticker.history(period='5d', interval='15m')
        if len(df) < 20: continue

        current = float(df.iloc[-1]['Close'])
        a = atr(df)
        atr_pips = round(a / cfg['pip'], 1)

        if atr_pips < MIN_ATR_PIPS: continue

        signals = detect_choch_fvg(df, cfg['pip'])
        if signals:
            for s in signals[-2:]:
                print(f'  📶 {pair} {s[\"type\"]} E={s[\"entry\"]:.5f} FVG={s[\"fvg_pips\"]:.1f}p ATR={atr_pips}p WR={cfg[\"wr\"]}%')
                found_any = True
    except: pass

if not found_any:
    print('  (nenhum sinal no momento)')

print()
print('✅ Dry-run concluído — sem ordens executadas')
print('   Para ativar: ./forex_bot_real_deploy.sh deploy')
"
}

# ═══════════════════════════════════════════════
# DEPLOY: Ativar o bot
# ═══════════════════════════════════════════════
deploy() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 DEPLOY CONTA REAL OANDA"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Verificar pré-requisitos primeiro
    if ! check_prerequisites; then
        echo ""
        err "Pré-requisitos falharam. Corrija antes de continuar."
        echo ""
        echo "⚠️  CONTA REAL: Ainda não existe conta real OANDA configurada."
        echo "   Para criar:"
        echo "   1. Acesse https://www.oanda.com"
        echo "   2. Clique em 'Start Trading' → 'Live Account'"
        echo "   3. Preencha cadastro (nome, email: robertosantos.una@gmail.com)"
        echo "   4. Faça depósito de \$100 (mínimo OANDA: \$1)"
        echo "   5. Conecte o MT5 ao servidor OANDA_Global-Live"
        echo "   6. Atualize brokers.json com os dados da conta real"
        echo ""
        return 1
    fi

    echo ""
    echo "⚠️  CONFIRMAÇÃO FINAL ⚠️"
    echo "   Você está prestes a ativar o bot na CONTA REAL com \$100."
    echo "   Parâmetros:"
    echo "   • Volume: 0.01 (microlote, ~\$0.10/pip)"
    echo "   • Risco: ${RISK_PERCENT:-3}% por trade"
    echo "   • Stop diário: -${DAILY_STOP_PERCENT:-5}%"
    echo "   • Max posições: ${MAX_POSITIONS:-3}"
    echo ""
    read -p "   Digite 'SIM' para confirmar: " confirm
    if [ "$confirm" != "SIM" ]; then
        echo "   Deploy cancelado."
        return 0
    fi

    # Criar arquivos de estado iniciais
    if [ ! -f "$DAILY_STATE" ]; then
        cat > "$DAILY_STATE" <<EOF
{
  "date": "$(date +%Y-%m-%d)",
  "balance": 100.00,
  "pnl_today": 0.00,
  "updated": "$(date -Iseconds)"
}
EOF
        ok "Daily state inicializado: \$100.00"
    fi

    if [ ! -f "$STATE_FILE" ]; then
        echo '{"active_trades": [], "last_balance": 100.00, "history": []}' > "$STATE_FILE"
        ok "State file inicializado"
    fi

    # Marcar deploy
    date -Iseconds > "$DEPLOY_MARKER"
    ok "Deploy marker criado: $(cat $DEPLOY_MARKER)"

    # Testar execução única via cron (simula o que o cron faria)
    echo ""
    log "Executando primeira análise..."
    python3 "$BOT_SCRIPT" 2>&1

    echo ""
    ok "✅ Bot REAL deploy concluído!"
    echo ""
    echo "📋 Próximos passos:"
    echo "   1. Configure um cron job para rodar a cada 5 min:"
    echo "      */5 * * * 1-5 python3 $BOT_SCRIPT >> $FOREX_DIR/bot_real.log 2>&1"
    echo ""
    echo "   2. Monitore: tail -f $FOREX_DIR/bot_real.log"
    echo "   3. Verifique saldo: cat $DAILY_STATE"
    echo "   4. Alerta Telegram configurado para chat ID $TELEGRAM_CHAT_ID"
}

# ═══════════════════════════════════════════════
# STOP: Pausar/desativar bot
# ═══════════════════════════════════════════════
stop_bot() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⏸️  PARANDO BOT REAL"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ -f "$DEPLOY_MARKER" ]; then
        rm "$DEPLOY_MARKER"
        ok "Deploy marker removido"
    fi

    # Criar flag de pause
    date -Iseconds > "$FOREX_DIR/.real_paused"
    ok "Bot pausado. Flag criada em $FOREX_DIR/.real_paused"
    echo ""
    echo "   Para reativar: ./forex_bot_real_deploy.sh deploy"
    echo "   Para fechar todas posições: python3 $SCRIPTS_DIR/mt5_direct.py close_all"
}

# ═══════════════════════════════════════════════
# STATUS: Ver estado atual
# ═══════════════════════════════════════════════
show_status() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 STATUS CONTA REAL"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Deploy status
    if [ -f "$DEPLOY_MARKER" ]; then
        echo "Status: 🟢 DEPLOYED — $(cat $DEPLOY_MARKER)"
    elif [ -f "$FOREX_DIR/.real_paused" ]; then
        echo "Status: 🟡 PAUSED — $(cat $FOREX_DIR/.real_paused)"
    else
        echo "Status: ⚪ NÃO DEPLOYADO"
    fi

    echo ""

    # Saldo
    if [ -f "$DAILY_STATE" ]; then
        echo "── Estado Diário ──"
        cat "$DAILY_STATE" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(f'  Saldo: \${d[\"balance\"]:.2f}')
print(f'  P&L hoje: \${d[\"pnl_today\"]:.2f}')
print(f'  Data: {d[\"date\"]}')
print(f'  Atualizado: {d[\"updated\"]}')
"
    else
        echo "  Daily state: não inicializado"
    fi

    echo ""

    # Posições ativas
    if [ -f "$STATE_FILE" ]; then
        echo "── Posições Ativas ──"
        python3 -c "
import json
state = json.load(open('$STATE_FILE'))
active = state.get('active_trades', [])
print(f'  Total: {len(active)}')
for t in active:
    print(f'  • {t[\"pair\"]} {t[\"direction\"]} E={t[\"entry\"]:.5f} SL={t[\"sl\"]:.5f} TP={t[\"tp\"]:.5f}')
if not active:
    print('  (nenhuma)')
"
    fi

    echo ""

    # Histórico recente
    if [ -f "$STATE_FILE" ]; then
        echo "── Histórico Recente (últimos 5) ──"
        python3 -c "
import json
state = json.load(open('$STATE_FILE'))
history = state.get('history', [])
for t in history[-5:]:
    pnl = t.get('pnl', 0)
    result = t.get('result', '?')
    emoji = '✅' if result == 'WIN' else '❌'
    print(f'  {emoji} {t[\"pair\"]} {t[\"direction\"]} {result} {pnl:+}p')
if not history:
    print('  (sem histórico)')
"
    fi

    echo ""

    # Alertas
    if [ -f "$ALERT_LOG" ]; then
        echo "── Últimos Alertas ──"
        tail -5 "$ALERT_LOG" 2>/dev/null || echo "  (vazio)"
    fi

    echo ""
    echo "── Configuração do Bot ──"
    python3 -c "
exec(open('$BOT_SCRIPT').read().split(\"if __name__\")[0])
print(f'  Risco/trade: {RISK_PERCENT}%')
print(f'  Stop diário: -{DAILY_STOP_PERCENT}%')
print(f'  Max posições: {MAX_POSITIONS}')
print(f'  Volume: {VOLUME}')
print(f'  CRT: {\"ON\" if CRT_ENABLED else \"OFF\"}')
print(f'  S/R: {\"ON\" if SR_ENABLED else \"OFF\"}')
"
}

# ═══════════════════════════════════════════════
# RESET: Resetar estado diário (novo dia)
# ═══════════════════════════════════════════════
reset_daily() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔄 RESET DIÁRIO"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    today=$(date +%Y-%m-%d)
    if [ -f "$DAILY_STATE" ]; then
        cur_balance=$(python3 -c "import json; print(json.load(open('$DAILY_STATE'))['balance'])" 2>/dev/null || echo "100.00")
    else
        cur_balance="100.00"
    fi

    cat > "$DAILY_STATE" <<EOF
{
  "date": "$today",
  "balance": $cur_balance,
  "pnl_today": 0.00,
  "updated": "$(date -Iseconds)"
}
EOF
    ok "Daily state resetado para $today — Saldo: \$$cur_balance"
}

# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════
CMD="${1:-status}"

case "$CMD" in
    check)
        check_prerequisites
        ;;
    dry-run|dryrun)
        dry_run
        ;;
    deploy|start)
        deploy
        ;;
    stop|pause)
        stop_bot
        ;;
    status|info)
        show_status
        ;;
    reset)
        reset_daily
        ;;
    *)
        echo "Uso: $0 {check|dry-run|deploy|stop|status|reset}"
        echo ""
        echo "  check    — Verificar pré-requisitos"
        echo "  dry-run  — Simular análise (sem ordens)"
        echo "  deploy   — Ativar bot na conta real"
        echo "  stop     — Pausar/desativar bot"
        echo "  status   — Ver estado atual (default)"
        echo "  reset    — Resetar P&L diário (usar em novo dia)"
        exit 1
        ;;
esac
