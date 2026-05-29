#!/usr/bin/env python3
"""
⚡ Monitor de Posições — 2R/3R (29/05/2026)
- 2R: SL → entry (breakeven, garante o stop)
- 3R: SL → +1.5R (trava lucro, deixa correr)
Usa LOCK FILE para não conflitar com comandos manuais.
"""
import json, os, time, fcntl
from datetime import datetime
from pathlib import Path

FILES = os.path.expanduser('~/.wine/drive_c/users/roberto/AppData/Roaming/MetaQuotes/Terminal/Common/Files')
CMD = os.path.join(FILES, 'hermes_cmd.json')
RESP = os.path.join(FILES, 'hermes_resp.json')
LOCK = os.path.join(FILES, '.monitor_lock')

OPEN_TRADES = Path.home() / '.hermes' / 'forex' / 'open_trades.json'

# ═══ CONFIG ═══
POLL = 3  # segundos entre verificações
LOSS_LIMIT_MULT = 0.8  # fecha se perder 80% do risco (stop protetor)

def acquire_lock():
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except:
        return None

def release_lock(fd):
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
    except:
        pass

def mt5_cmd(action, **kw):
    fd = acquire_lock()
    if not fd:
        return None
    try:
        if os.path.exists(RESP):
            os.remove(RESP)
        j = json.dumps({'action': action, **kw})
        with open(CMD, 'w') as f:
            f.write(j)
        for _ in range(30):
            time.sleep(0.1)
            if os.path.exists(RESP):
                try:
                    return json.loads(open(RESP).read())
                except:
                    pass
        return None
    finally:
        release_lock(fd)

def status():
    return mt5_cmd('status')

def close_sym(symbol):
    return mt5_cmd('close_symbol', symbol=symbol)

def modify(ticket, sl, tp=0):
    return mt5_cmd('modify_position', ticket=int(ticket), sl=sl, tp=tp)

def load_open_trades():
    """Carrega dicionário de trades abertos com risco."""
    if OPEN_TRADES.exists():
        try:
            return json.loads(OPEN_TRADES.read_text())
        except:
            pass
    return {}

def save_open_trades(trades):
    OPEN_TRADES.write_text(json.dumps(trades, indent=2, default=str))

# ═══ ESTADO ═══
be_done = set()     # tickets que já fizeram breakeven (2R)
trail_done = set()  # tickets que já fizeram trail (3R)

print(f"⚡ Monitor 2R/3R — {datetime.now().strftime('%H:%M:%S')} — {POLL}s")

while True:
    try:
        s = status()
        if not s or s.get('status') != 'ok':
            time.sleep(POLL)
            continue
        
        open_trades = load_open_trades()
        active_tickets = set()
        
        for p in s.get('positions_data', []):
            ticket = str(p.get('ticket', ''))
            sym = p.get('symbol', '')
            typ = p.get('type', '')
            profit = p.get('profit', 0)
            entry = p.get('entry', 0)
            sl = p.get('sl', 0)
            
            if not ticket or not entry:
                continue
            
            active_tickets.add(ticket)
            
            # Buscar risco do trade
            trade_info = open_trades.get(ticket, {})
            risk_dollar = trade_info.get('risk_dollar', 0)
            
            if risk_dollar <= 0:
                # Fallback: risco desconhecido, pular
                continue
            
            # ═══ LOSS LIMIT: fecha se perder 80% do risco ═══
            if profit < -risk_dollar * LOSS_LIMIT_MULT:
                print(f"🔴 {sym} #{ticket}: -${abs(profit):.2f} ({profit/risk_dollar*100:.0f}%R) — FECHANDO")
                close_sym(sym)
                continue
            
            # ═══ 2R: SL → entry (breakeven) ═══
            if ticket not in be_done and profit >= risk_dollar * 2.0:
                if abs(sl - entry) > 0.00001:
                    r = modify(ticket, sl=entry)
                    if r and r.get('status') == 'ok':
                        print(f"🟢 {sym} #{ticket}: 2R BREAKEVEN SL→{entry:.5f} | +${profit:.2f}")
                        be_done.add(ticket)
            
            # ═══ 3R: SL → +1.5R (trava lucro) ═══
            if ticket not in trail_done and profit >= risk_dollar * 3.0:
                metal = 'XAU' in sym.upper()
                if 'JPY' in sym:
                    tick_sz = 0.01
                elif metal:
                    tick_sz = 0.01
                else:
                    tick_sz = 0.0001
                
                trail_pips = 1.5 * risk_dollar  # em dólares
                if typ == 'BUY':
                    new_sl = entry + trail_pips * tick_sz / (tick_sz * 10)  # aprox
                    # Simplificado: new_sl = entry + (1.5R em preço)
                    # 1.5R em preço = 1.5 * risk_dollar / (volume * tick_value)
                    # Vamos usar sl_pips * 1.5
                    sl_pips = trade_info.get('sl_pips', 15)
                    new_sl = round(entry + sl_pips * 1.5 * tick_sz, 5 if not metal else 2)
                else:
                    sl_pips = trade_info.get('sl_pips', 15)
                    new_sl = round(entry - sl_pips * 1.5 * tick_sz, 5 if not metal else 2)
                
                r = modify(ticket, sl=new_sl)
                if r and r.get('status') == 'ok':
                    print(f"🚀 {sym} #{ticket}: 3R TRAIL SL→{new_sl:.5f} | +${profit:.2f}")
                    trail_done.add(ticket)
        
        # ═══ LIMPAR trades fechados ═══
        stale = [t for t in open_trades if t not in active_tickets]
        if stale:
            for t in stale:
                del open_trades[t]
                be_done.discard(t)
                trail_done.discard(t)
            save_open_trades(open_trades)
        
        time.sleep(POLL)
        
    except KeyboardInterrupt:
        print("\n⏹️ Parado.")
        break
    except Exception as e:
        print(f"⚠️ {e}")
        time.sleep(POLL)
