#!/usr/bin/env python3
"""Monitor 2R/3R — Breakeven + Trailing Stop"""
import json, os, time, fcntl
from pathlib import Path

FILES = os.path.expanduser('~/.wine/drive_c/users/roberto/AppData/Roaming/MetaQuotes/Terminal/Common/Files')
CMD = os.path.join(FILES, 'hermes_cmd.json')
RESP = os.path.join(FILES, 'hermes_resp.json')
LOCK = os.path.join(FILES, '.monitor_lock')
OPEN_TRADES = Path.home() / '.hermes' / 'forex' / 'open_trades.json'
RR = 3.0; POLL = 3

def acquire_lock():
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except: return None

def release_lock(fd):
    try: fcntl.flock(fd, fcntl.LOCK_UN); os.close(fd)
    except: pass

def mt5_cmd(action, **kw):
    fd = acquire_lock()
    if not fd: return None
    try:
        if os.path.exists(RESP): os.remove(RESP)
        with open(CMD, 'w') as f: f.write(json.dumps({'action': action, **kw}))
        for _ in range(30):
            time.sleep(0.1)
            if os.path.exists(RESP):
                try: return json.loads(open(RESP).read())
                except: pass
        return None
    finally: release_lock(fd)

def status(): return mt5_cmd('status')
def close_sym(sym): return mt5_cmd('close_symbol', symbol=sym)
def modify(ticket, sl, tp=0): return mt5_cmd('modify_position', ticket=int(ticket), sl=sl, tp=tp)
def load_open_trades():
    if OPEN_TRADES.exists():
        try: return json.loads(OPEN_TRADES.read_text())
        except: pass
    return {}

be_done = set(); trail_done = set()
print(f"Monitor 2R/3R — {time.strftime('%H:%M:%S')}")

while True:
    try:
        s = status()
        if not s or s.get('status') != 'ok': time.sleep(POLL); continue
        open_trades = load_open_trades()
        active = set()
        for p in s.get('positions_data', []):
            ticket = str(p.get('ticket', '')); sym = p.get('symbol', '')
            profit = p.get('profit', 0); entry = p.get('entry', 0)
            sl = p.get('sl', 0); typ = p.get('type', '')
            if not ticket or not entry: continue
            active.add(ticket)
            trade = open_trades.get(ticket, {})
            risk = trade.get('risk_dollar', 0)
            if risk <= 0: continue
            if profit < -risk * 0.8: close_sym(sym); continue
            if ticket not in be_done and profit >= risk * 2.0:
                if abs(sl - entry) > 0.00001:
                    r = modify(ticket, sl=entry)
                    if r and r.get('status') == 'ok': be_done.add(ticket)
            if ticket not in trail_done and profit >= risk * 3.0:
                sl_pips = trade.get('sl_pips', 15)
                tick = 0.01 if 'JPY' in sym else (0.01 if 'XAU' in sym else 0.0001)
                new_sl = round(entry + sl_pips * 1.5 * tick, 5) if typ == 'BUY' else round(entry - sl_pips * 1.5 * tick, 5)
                r = modify(ticket, sl=new_sl)
                if r and r.get('status') == 'ok': trail_done.add(ticket)
        stale = [t for t in open_trades if t not in active]
        if stale:
            for t in stale: del open_trades[t]; be_done.discard(t); trail_done.discard(t)
            OPEN_TRADES.write_text(json.dumps(open_trades, indent=2))
        time.sleep(POLL)
    except KeyboardInterrupt: break
    except Exception as e: time.sleep(POLL)
