#!/usr/bin/env python3
"""
MT5 Order Executor v3 — ydotool (kernel-level, funciona no Wayland/GNOME).
Envia ordens para MetaTrader 5 IC Markets Global no desktop do usuário.

Requisito: MT5 deve estar com foco antes da ordem.
Uso:
  python3 mt5_order_executor.py BUY EURUSD 0.01 --sl 1.1700 --tp 1.1580
  python3 mt5_order_executor.py SELL GBPUSD 0.02 --sl 1.3550 --tp 1.3400
  python3 mt5_order_executor.py --status
"""

import subprocess, sys, time, argparse, json
from pathlib import Path
from datetime import datetime, timezone

HERMES = Path.home() / ".hermes"
LOG_FILE = HERMES / "forex" / "mt5_execution_log.json"

def ydotool_key(keycode):
    """Pressiona tecla via ydotool (keycodes: 28=Enter, 15=Tab, 67=F9, 56=Alt, 48=B, 31=S, etc)."""
    subprocess.run(["ydotool", "key", keycode], timeout=2)

def ydotool_type(text, delay=30):
    """Digita texto via ydotool."""
    subprocess.run(["ydotool", "type", "--key-delay", str(delay), text], timeout=5)

def focus_mt5():
    """Alt+Tab para focar MT5 (funciona no Wayland via ydotool)."""
    ydotool_key("56:1 15:1 15:0 56:0")  # Alt+Tab
    time.sleep(0.5)

def place_order(order_type, symbol, volume, sl=None, tp=None):
    """Abre ordem no MT5 via F9 + teclas. MT5 precisa estar com foco."""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "order_type": order_type,
        "symbol": symbol,
        "volume": volume,
        "sl": sl,
        "tp": tp,
        "status": "attempted"
    }
    
    # Focar MT5 (Alt+Tab)
    focus_mt5()
    time.sleep(0.3)
    
    # F9 = New Order
    ydotool_key("67:1 67:0")
    time.sleep(1.5)
    
    # Limpar campo símbolo e digitar
    ydotool_key("29:1 31:1 31:0 29:0")  # Ctrl+A
    time.sleep(0.1)
    ydotool_type(symbol)
    time.sleep(0.3)
    ydotool_key("28:1 28:0")  # Enter
    time.sleep(0.5)
    
    # Tab 2x → Volume
    ydotool_key("15:1 15:0")
    time.sleep(0.1)
    ydotool_key("15:1 15:0")
    time.sleep(0.1)
    ydotool_key("29:1 31:1 31:0 29:0")
    time.sleep(0.05)
    ydotool_type(str(volume))
    time.sleep(0.2)
    
    # Tab 2x → SL
    ydotool_key("15:1 15:0")
    time.sleep(0.1)
    ydotool_key("15:1 15:0")
    time.sleep(0.1)
    if sl is not None:
        ydotool_key("29:1 31:1 31:0 29:0")
        time.sleep(0.05)
        ydotool_type(f'{sl:.5f}')
        time.sleep(0.2)
    
    # Tab → TP
    ydotool_key("15:1 15:0")
    time.sleep(0.1)
    if tp is not None:
        ydotool_key("29:1 31:1 31:0 29:0")
        time.sleep(0.05)
        ydotool_type(f'{tp:.5f}')
        time.sleep(0.2)
    
    # Enviar ordem: Alt+B (Buy) ou Alt+S (Sell)
    if order_type.upper() == "BUY":
        ydotool_key("56:1 48:1 48:0 56:0")  # Alt+B
    else:
        ydotool_key("56:1 31:1 31:0 56:0")  # Alt+S
    
    time.sleep(1.5)
    
    # Fechar diálogo
    ydotool_key("1:1 1:0")  # Escape
    time.sleep(0.5)
    
    log_entry["status"] = "executed"
    save_log(log_entry)
    return log_entry

def save_log(entry):
    logs = []
    if LOG_FILE.exists():
        try:
            logs = json.loads(LOG_FILE.read_text())
        except:
            pass
    logs.append(entry)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(json.dumps(logs, indent=2, ensure_ascii=False))

def check_mt5():
    result = subprocess.run(["pgrep", "-f", "terminal64.exe"], capture_output=True, text=True)
    pids = [p for p in result.stdout.strip().split('\n') if p]
    return {"mt5_running": len(pids) > 0, "instances": len(pids)}

def main():
    parser = argparse.ArgumentParser(description="MT5 Order Executor v3 (ydotool/Wayland)")
    parser.add_argument("order", nargs="?", choices=["BUY", "SELL"])
    parser.add_argument("symbol", nargs="?")
    parser.add_argument("volume", nargs="?", type=float, default=0.01)
    parser.add_argument("--sl", type=float)
    parser.add_argument("--tp", type=float)
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    
    if args.status:
        print(json.dumps(check_mt5()))
        return
    
    if not args.order:
        parser.print_help()
        return
    
    status = check_mt5()
    if not status["mt5_running"]:
        print(json.dumps({"error": "MT5 não rodando"}))
        sys.exit(1)
    
    print(f"📤 {args.order} {args.symbol} x{args.volume}")
    result = place_order(args.order.upper(), args.symbol.upper(), args.volume, args.sl, args.tp)
    print(f"✅ {result['status']}: {result['order_type']} {result['symbol']}")

if __name__ == "__main__":
    main()
