#!/usr/bin/env python3
"""MT5 History Extractor — Extrai histórico real de ordens do MT5 via EA Bridge.
Envia comando {"action":"history","days":30} e processa a resposta JSON.

Uso:
  python3 mt5_history_extractor.py          # últimos 30 dias
  python3 mt5_history_extractor.py --days 90 # últimos 90 dias
  python3 mt5_history_extractor.py --from 2026-05-01 --to 2026-05-28
"""

import json, os, sys, time
from pathlib import Path
from datetime import datetime, timezone

MT5_COMMON = Path.home() / ".wine/drive_c/users/roberto/AppData/Roaming/MetaQuotes/Terminal/Common/Files"
CMD_FILE = MT5_COMMON / "hermes_cmd.json"
RESP_FILE = MT5_COMMON / "hermes_resp.json"
OUTPUT = Path.home() / ".hermes/forex/mt5_history.json"

def send_command(action: dict, timeout: float = 3.0) -> dict:
    """Envia comando ao EA bridge e aguarda resposta."""
    # Limpar resposta anterior
    if RESP_FILE.exists():
        RESP_FILE.unlink()
    
    # Escrever comando
    with open(CMD_FILE, 'w') as f:
        json.dump(action, f)
    
    # Aguardar resposta (EA lê a cada 250ms)
    start = time.time()
    while time.time() - start < timeout:
        if RESP_FILE.exists():
            time.sleep(0.1)  # aguardar escrita completa
            try:
                with open(RESP_FILE) as f:
                    return json.load(f)
            except:
                pass
        time.sleep(0.1)
    
    return {"status": "timeout", "msg": "EA não respondeu"}

def extract_history(days: int = 30, from_date: str = None, to_date: str = None):
    """Extrai histórico de ordens do MT5."""
    
    print(f"📡 Conectando ao MT5 via EA Bridge...")
    
    # 1. Verificar se EA está ativo
    status = send_command({"action": "status"})
    if status.get("status") != "ok":
        print(f"❌ EA offline: {status}")
        return None
    
    print(f"✅ EA online | Bal: ${status.get('balance',0):.2f} | Eq: ${status.get('equity',0):.2f} | Pos: {status.get('positions',0)}")
    
    # 2. Solicitar histórico
    cmd = {"action": "history", "days": days}
    if from_date:
        cmd["from"] = from_date
    if to_date:
        cmd["to"] = to_date
    
    print(f"📊 Solicitando histórico ({days} dias)...")
    resp = send_command(cmd, timeout=5.0)
    
    if resp.get("status") != "ok":
        print(f"❌ Erro: {resp}")
        # Se falhou, pode ser que o EA ainda não foi recompilado
        if "unknown action" in str(resp.get("msg", "")):
            print("💡 O EA precisa ser recompilado no MetaEditor (F7)")
            print("   Arquivo: MQL5/Experts/hermes_bridge.mq5")
        return None
    
    deals = resp.get("deals", [])
    orders = resp.get("orders", [])
    
    print(f"\n=== HISTÓRICO DE ORDENS MT5 ===")
    print(f"Deals: {resp.get('total_deals', 0)} | Orders: {resp.get('total_orders', 0)}")
    print(f"Período: {resp.get('from','?')} → {resp.get('to','?')}")
    print()
    
    if deals:
        print("── DEALS (execuções) ──")
        for d in deals:
            pnl = d.get('profit', 0)
            s = '+' if pnl > 0 else ''
            print(f"  #{d.get('ticket')} | {d.get('time','?')[:19]} | "
                  f"{d.get('symbol','?'):10s} {d.get('type','?'):4s} | "
                  f"Vol:{d.get('volume',0)} | "
                  f"P:{d.get('price',0)} | "
                  f"P&L: {s}${pnl:.2f} | "
                  f"Comm:${d.get('commission',0):.2f} Swap:${d.get('swap',0):.2f}")
    
    if orders:
        print("\n── ORDERS (aberturas) ──")
        for o in orders:
            print(f"  #{o.get('ticket')} | {o.get('symbol','?'):10s} {o.get('type','?'):4s} | "
                  f"Vol:{o.get('volume',0)} | "
                  f"Entry:{o.get('price_open',0)} | "
                  f"SL:{o.get('sl',0)} TP:{o.get('tp',0)} | "
                  f"Setup:{str(o.get('time_setup','?'))[:19]} | "
                  f"State:{o.get('state','?')}")
    
    # 3. Salvar
    history = {
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "account": status.get("balance", 0),
        "period": {"from": resp.get("from"), "to": resp.get("to")},
        "total_deals": resp.get("total_deals", 0),
        "total_orders": resp.get("total_orders", 0),
        "deals": deals,
        "orders": orders
    }
    
    with open(OUTPUT, 'w') as f:
        json.dump(history, f, indent=2, default=str)
    
    # Stats
    if deals:
        wins = sum(1 for d in deals if d.get('profit', 0) > 0)
        losses = sum(1 for d in deals if d.get('profit', 0) < 0)
        total_pnl = sum(d.get('profit', 0) for d in deals)
        total_comm = sum(d.get('commission', 0) for d in deals)
        total_swap = sum(d.get('swap', 0) for d in deals)
        
        print(f"\n── RESUMO ──")
        print(f"Deals: {len(deals)} | Wins: {wins} | Losses: {losses}")
        print(f"WR: {wins/max(len(deals),1)*100:.1f}%")
        print(f"P&L Bruto: ${total_pnl:+.2f}")
        print(f"Comissões: ${total_comm:.2f}")
        print(f"Swap: ${total_swap:+.2f}")
        print(f"P&L Líquido: ${total_pnl - total_comm + total_swap:+.2f}")
    
    print(f"\n✅ Salvo em: {OUTPUT}")
    return history

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="MT5 History Extractor via EA Bridge")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--from", dest="from_date")
    p.add_argument("--to", dest="to_date")
    args = p.parse_args()
    
    extract_history(args.days, args.from_date, args.to_date)
