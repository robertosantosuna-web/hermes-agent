#!/usr/bin/env python3
"""
Hermes MT5 Bridge — Envia ordens ao MT5 via EA hermes_bridge.ex5.

Protocolo:
  Python → JSON → Common/Files/hermes_cmd.json
  EA lê, executa OrderSend(), escreve hermes_resp.json
  Python lê resposta

Uso:
  from hermes_mt5_bridge import send_order, get_status, close_all
  result = send_order('EURUSD', 'BUY', 0.01, 1.16405, 1.16505)
"""
import json, os, time
from pathlib import Path

# Common Files folder (where EA reads/writes)
MT5_COMMON = Path.home() / '.wine' / 'drive_c' / 'users' / 'roberto' / 'AppData' / 'Roaming' / 'MetaQuotes' / 'Terminal' / 'Common' / 'Files'
CMD_FILE = MT5_COMMON / 'hermes_cmd.json'
RESP_FILE = MT5_COMMON / 'hermes_resp.json'


def _write_cmd(cmd: dict):
    """Write command JSON to MT5 Common/Files."""
    MT5_COMMON.mkdir(parents=True, exist_ok=True)
    # Delete old response
    if RESP_FILE.exists():
        RESP_FILE.unlink()
    CMD_FILE.write_text(json.dumps(cmd))


def _read_resp(timeout: float = 5.0) -> dict:
    """Wait for response file and return parsed JSON."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if RESP_FILE.exists():
            try:
                return json.loads(RESP_FILE.read_text())
            except json.JSONDecodeError:
                time.sleep(0.05)
                continue
        time.sleep(0.05)
    return {"status": "error", "msg": "timeout"}


def send_order(symbol: str, direction: str, volume: float,
               sl: float = 0, tp: float = 0, timeout: float = 10) -> dict:
    """
    Envia ordem de mercado via EA hermes_bridge.
    
    Args:
        symbol: 'EURUSD', 'GBPUSD', 'USDJPY', etc
        direction: 'BUY' ou 'SELL'
        volume: lotes (ex: 0.01)
        sl: Stop Loss (0 = sem SL)
        tp: Take Profit (0 = sem TP)
        timeout: segundos para esperar resposta
    
    Returns:
        dict: {'status': 'ok', 'ticket': 12345, ...} ou {'status': 'error', ...}
    """
    cmd = {
        "action": "order",
        "symbol": symbol.upper(),
        "direction": direction.upper(),
        "volume": volume,
        "sl": round(sl, 5) if sl else 0,
        "tp": round(tp, 5) if tp else 0,
    }
    _write_cmd(cmd)
    return _read_resp(timeout)


def close_all(timeout: float = 10) -> dict:
    """Fecha todas as posições abertas."""
    _write_cmd({"action": "close_all"})
    return _read_resp(timeout)


def get_status(timeout: float = 5) -> dict:
    """Obtém status da conta (saldo, equity, posições)."""
    _write_cmd({"action": "status"})
    return _read_resp(timeout)


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: hermes_mt5_bridge.py <order|status|close_all> [symbol] [dir] [vol] [sl] [tp]")
        print()
        print("Exemplos:")
        print("  python3 hermes_mt5_bridge.py status")
        print("  python3 hermes_mt5_bridge.py order EURUSD BUY 0.01 1.16405 1.16505")
        print("  python3 hermes_mt5_bridge.py close_all")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == 'status':
        resp = get_status()
        print(json.dumps(resp, indent=2))
    
    elif action == 'close_all':
        resp = close_all()
        print(json.dumps(resp, indent=2))
    
    elif action == 'order':
        if len(sys.argv) < 5:
            print("Erro: order precisa de symbol direction volume [sl] [tp]")
            sys.exit(1)
        symbol = sys.argv[2]
        direction = sys.argv[3]
        volume = float(sys.argv[4])
        sl = float(sys.argv[5]) if len(sys.argv) > 5 else 0
        tp = float(sys.argv[6]) if len(sys.argv) > 6 else 0
        resp = send_order(symbol, direction, volume, sl, tp)
        print(json.dumps(resp, indent=2))
    
    else:
        print(f"Ação desconhecida: {action}")
        sys.exit(1)
