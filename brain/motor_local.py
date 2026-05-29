#!/usr/bin/env python3
"""Motor Local — Leitura do MT5 + alimentação do Tálamo.
Roda a cada 60s. Lê estado do MT5, publica no Tálamo,
alimenta o Córtex Visual com dados atualizados.
"""

import sys, os, json, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "brain"))
import thalamus

FOREX_DIR = Path.home() / ".hermes" / "forex"
MT5_STATE = FOREX_DIR / "mt5_state.json"
TRADE_LOG = FOREX_DIR / "trade_log.json"

# MT5 bridge via Wine — EA escreve na Common/Files do MT5
MT5_COMMON = Path.home() / ".wine" / "drive_c" / "users" / "roberto" / "AppData" / "Roaming" / "MetaQuotes" / "Terminal" / "Common" / "Files"
MT5_RESP = MT5_COMMON / "hermes_resp.json"
MT5_CMD = MT5_COMMON / "hermes_cmd.json"

def read_mt5_state():
    """Lê estado do MT5 via EA bridge (Wine Common/Files)."""
    # 1. Tentar bridge EA (caminho real)
    if MT5_RESP.exists():
        try:
            with open(MT5_RESP) as f:
                data = json.load(f)
            # Verificar se resposta é recente (< 30s)
            age = time.time() - MT5_RESP.stat().st_mtime
            if age < 30:
                data["status"] = "online"
                data["bridge"] = "ea_wine"
                return data
            else:
                return {"status": "stale", "reason": f"Resposta antiga ({age:.0f}s)", "data": data}
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    # 2. Fallback: mt5_state.json local
    if MT5_STATE.exists():
        try:
            with open(MT5_STATE) as f:
                return json.load(f)
        except:
            pass
    
    return {"status": "offline", "reason": "Nenhuma bridge encontrada"}

def read_trade_log():
    """Lê últimas trades."""
    if TRADE_LOG.exists():
        try:
            with open(TRADE_LOG) as f:
                trades = json.load(f)
            if isinstance(trades, list):
                return trades[-10:]  # últimas 10
        except:
            pass
    return []

def run():
    """Ciclo do motor local."""
    now = datetime.now(timezone.utc)
    
    # 1. Ler MT5
    mt5 = read_mt5_state()
    
    # 2. Publicar no Tálamo
    if mt5.get("status") != "offline":
        thalamus.update_state("mt5_balance", mt5.get("balance", 0))
        thalamus.update_state("mt5_equity", mt5.get("equity", 0))
        thalamus.update_state("mt5_positions", mt5.get("positions", 0))
        thalamus.update_state("mt5_last_update", now.isoformat())
        
        # Log só se mudou
        prev_balance = thalamus.get_state("mt5_balance") or 0
        if mt5.get("balance", 0) != prev_balance and prev_balance > 0:
            thalamus.log_event("balance_change", "motor_local",
                              {"from": prev_balance, "to": mt5["balance"]})
        
        # Alertas
        if mt5.get("equity", 0) < mt5.get("balance", 0) * 0.90:
            thalamus.raise_alert("warning", "drawdown_10pct",
                                f"Equity {mt5['equity']} < 90% balance {mt5['balance']}", "motor_local")
    else:
        thalamus.update_state("mt5_status", "offline")
    
    # 3. Ler trades recentes
    trades = read_trade_log()
    open_trades = [t for t in trades if t.get("status") == "open"]
    
    if open_trades:
        thalamus.update_state("open_positions", len(open_trades))
        for t in open_trades:
            thalamus.log_event("position_open", "motor_local",
                              {"pair": t.get("symbol"), "pnl": t.get("pnl", 0)})
    
    # 4. Publicar resumo
    summary = {
        "mt5": "online" if mt5.get("status") != "offline" else "offline",
        "balance": mt5.get("balance", 0),
        "equity": mt5.get("equity", 0),
        "positions": mt5.get("positions", 0) or len(open_trades),
        "timestamp": now.isoformat()
    }
    thalamus.update_state("motor_summary", summary)
    
    return summary

if __name__ == "__main__":
    result = run()
    status = "🟢" if result["mt5"] == "online" else "🔴"
    print(f"Motor Local {status} | MT5: {result['mt5']} | "
          f"Bal: ${result['balance']} | Eq: ${result['equity']} | "
          f"Pos: {result['positions']} | {result['timestamp'][:19]}")
