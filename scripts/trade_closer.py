#!/usr/bin/env python3
"""
Trade Closer + MT5 Health — sincroniza estado e verifica saúde do MT5.
Ações: health (status MT5), close (sync P&L de posições abertas).
"""
import subprocess, time, os, sys, json
from datetime import datetime

DISPLAY = ':99'
STATE_FILE = '/home/roberto/.hermes/forex/real_state.json'
TRADE_LOG = '/home/roberto/.hermes/forex/trade_log.json'
PIP_VAL = 0.0001

def xdo(*args):
    r = subprocess.run(['xdotool'] + list(args),
                       env={**os.environ, 'DISPLAY': DISPLAY},
                       capture_output=True, text=True, timeout=5)
    return r.stdout.strip()

def mt5_health():
    """Verifica se MT5 está rodando e responsivo."""
    try:
        out = xdo('search', '--name', 'MetaTrader')
        if not out:
            return {'status': 'dead', 'error': 'MT5 window not found'}
        wid = out.split('\n')[0]
        xdo('windowfocus', wid)
        xdo('getwindowname', wid)
        return {'status': 'ok', 'window_id': wid}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def fetch_current_price(pair):
    """Preço atual via Yahoo Finance (fallback: arquivo de estado)."""
    import yfinance as yf
    syms = {'GBP/USD': 'GBPUSD=X', 'AUD/USD': 'AUDUSD=X',
            'NZD/USD': 'NZDUSD=X', 'EUR/USD': 'EURUSD=X'}
    sym = syms.get(pair)
    if not sym:
        return None
    try:
        df = yf.Ticker(sym).history(period='1d', interval='5m')
        if len(df) > 0:
            return float(df.iloc[-1]['Close'])
    except:
        pass
    return None

def sync_positions(now=None):
    """Sincroniza P&L: verifica SL/TP das posições abertas vs preço atual."""
    if now is None:
        now = datetime.now()

    if not os.path.exists(STATE_FILE):
        return {'status': 'no_state'}

    try:
        state = json.loads(open(STATE_FILE).read())
    except:
        return {'status': 'error', 'error': 'corrupt state file'}

    active = state.get('active_trades', [])
    if not active:
        return {'status': 'ok', 'open': 0, 'closed': 0}

    still_active = []
    closed_trades = []

    for t in active:
        pair = t['pair']
        entry = t['entry']
        sl = t['sl']
        tp = t['tp']
        direction = t['direction']
        tid = t.get('tid', '')

        current = fetch_current_price(pair)
        if current is None:
            still_active.append(t)
            continue

        hit_tp = (direction == 'BUY' and current >= tp) or \
                 (direction == 'SELL' and current <= tp)
        hit_sl = (direction == 'BUY' and current <= sl) or \
                 (direction == 'SELL' and current >= sl)

        if hit_tp or hit_sl:
            if direction == 'BUY':
                pnl_pips = round((current - entry) / PIP_VAL, 1)
            else:
                pnl_pips = round((entry - current) / PIP_VAL, 1)

            result = 'WIN' if pnl_pips > 0 else 'LOSS'

            # Update trade_log
            try:
                if os.path.exists(TRADE_LOG):
                    log = json.loads(open(TRADE_LOG).read())
                    for lt in log.get('trades', []):
                        if lt.get('id') == tid and lt['status'] == 'open':
                            lt['status'] = 'closed'
                            lt['exit_price'] = round(current, 5)
                            lt['pnl'] = pnl_pips
                            lt['closed_at'] = now.isoformat()
                            lt['result'] = result
                            break
                    open(TRADE_LOG, 'w').write(json.dumps(log, indent=2))
            except:
                pass

            closed_trades.append({
                'pair': pair, 'direction': direction,
                'pnl': pnl_pips, 'result': result,
                'exit': current, 'tid': tid
            })
        else:
            still_active.append(t)

    # Update state
    state['active_trades'] = still_active
    if closed_trades:
        state.setdefault('history', [])
        # Find original entries for history
        original = {orig['tid']: orig for orig in active if 'tid' in orig}
        for ct in closed_trades:
            orig = original.get(ct['tid'], {})
            state['history'].append({
                'tid': ct['tid'],
                'pair': ct['pair'],
                'direction': ct['direction'],
                'entry': orig.get('entry', 0),
                'pnl': ct['pnl'],
                'result': ct['result'],
                'exit': ct['exit'],
                'date': now.strftime('%Y-%m-%d'),
                'opened': orig.get('opened', ''),
                'volume': orig.get('volume', 0.01)
            })
    state['updated'] = now.isoformat()

    try:
        open(STATE_FILE, 'w').write(json.dumps(state, indent=2))
    except:
        pass

    return {
        'status': 'ok',
        'open': len(still_active),
        'closed': len(closed_trades),
        'details': [f"{c['pair']} {c['direction']} {c['result']} {c['pnl']:+}p" for c in closed_trades]
    }

# ── CLI ──
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'usage: health|close'}))
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'health':
        print(json.dumps(mt5_health()))
    elif cmd == 'close':
        result = sync_positions()
        print(json.dumps(result))
        # Exit code signals if something closed (for delivery trigger)
        if result.get('closed', 0) > 0:
            sys.exit(0)
    else:
        print(json.dumps({'error': f'unknown: {cmd}'}))
        sys.exit(1)
