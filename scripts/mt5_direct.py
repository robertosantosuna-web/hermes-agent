#!/usr/bin/env python3
"""
MT5 Direct Executor v6 — Desktop Daemon + xdotool (visão XWayland).
- Encontra e foca MT5 via xdotool (DISPLAY=:0)
- Envia teclas via ydotool keycodes (daemon v3)
- Fecha janelas de ordem abertas antes de nova ordem
"""
import asyncio, json, time, sys

DAEMON = 'ws://localhost:9876'


async def _call(ws, action, params=None, delay=0):
    msg = {"action": action, "id": 0}
    if params: msg["params"] = params
    await ws.send(json.dumps(msg))
    resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
    if delay:
        await asyncio.sleep(delay)
    return resp


async def _close_order_windows(ws):
    """Fecha janelas 'Ordem:' abertas antes de abrir nova."""
    r = await _call(ws, "windows")
    for w in r.get("data", []):
        if 'ordem:' in w['name'].lower():
            # Fecha via Escape na janela de ordem
            await _call(ws, "focus", {"wid": w['id']}, delay=0.3)
            await _call(ws, "key", {"key": "escape"}, delay=0.5)


async def _order_async(symbol, direction, volume, sl, tp):
    import websockets
    async with websockets.connect(DAEMON, max_size=50*1024*1024) as ws:
        
        # 1. Fechar janelas de ordem existentes
        await _close_order_windows(ws)
        
        # 2. Encontrar e focar MT5 principal
        r = await _call(ws, "find_mt5")
        if not r['ok']:
            return {'status': 'error', 'error': 'MT5 não encontrado'}
        mt5 = r['data']
        await asyncio.sleep(0.3)
        
        # 3. F9 = New Order
        await _call(ws, "key", {"key": "f9"}, delay=2)
        
        # 4. Símbolo
        await _call(ws, "key", {"key": "ctrl+a"}, delay=0.1)
        await _call(ws, "type", {"text": symbol}, delay=0.5)
        await _call(ws, "key", {"key": "enter"}, delay=0.5)
        
        # 5. Volume
        await _call(ws, "key", {"key": "tab"}, delay=0.1)
        await _call(ws, "key", {"key": "tab"}, delay=0.1)
        await _call(ws, "key", {"key": "ctrl+a"}, delay=0.05)
        await _call(ws, "type", {"text": str(volume)}, delay=0.2)
        
        # 6. SL
        await _call(ws, "key", {"key": "tab"}, delay=0.1)
        await _call(ws, "key", {"key": "tab"}, delay=0.1)
        await _call(ws, "key", {"key": "ctrl+a"}, delay=0.05)
        await _call(ws, "type", {"text": f'{sl:.5f}'}, delay=0.2)
        
        # 7. TP
        await _call(ws, "key", {"key": "tab"}, delay=0.1)
        await _call(ws, "key", {"key": "ctrl+a"}, delay=0.05)
        await _call(ws, "type", {"text": f'{tp:.5f}'}, delay=0.3)
        
        # 8. BUY ou SELL
        key = "alt+b" if direction.upper() in ('BUY', 'LONG') else "alt+s"
        await _call(ws, "key", {"key": key}, delay=1.5)
        
        # 9. Fechar janela
        await _call(ws, "key", {"key": "escape"}, delay=0.5)
        
        # 10. Verificar se janela de ordem apareceu
        r = await _call(ws, "windows")
        order_windows = [w for w in r.get("data", []) if 'ordem:' in w['name'].lower() and symbol.upper() in w['name'].upper()]
        
        return {
            'status': 'sent',
            'symbol': symbol,
            'direction': direction.upper(),
            'volume': volume,
            'sl': round(sl, 5),
            'tp': round(tp, 5),
            'verified': len(order_windows) > 0,
            'mt5_window': mt5['name'][:50]
        }


def place_order(symbol, direction, volume, sl, tp):
    """Abre ordem no MT5 IC Markets. Síncrono."""
    try:
        return asyncio.run(_order_async(symbol, direction, volume, sl, tp))
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def place_choch_order(pair, direction, entry_price, fvg_pips, atr_pips):
    """Ordem CHoCH+FVG com RR 3:1."""
    symbols = {
        'GBP/USD': 'GBPUSD', 'AUD/USD': 'AUDUSD',
        'NZD/USD': 'NZDUSD', 'EUR/USD': 'EURUSD',
        'USD/JPY': 'USDJPY',
    }
    symbol = symbols.get(pair, pair.replace('/', ''))
    pip_v = 0.01 if 'JPY' in symbol else 0.0001
    sl_pips = max(fvg_pips, 2.0)
    tp_pips = sl_pips * 3
    
    if direction.upper() in ('BUY', 'LONG'):
        sl = entry_price - (sl_pips * pip_v)
        tp = entry_price + (tp_pips * pip_v)
    else:
        sl = entry_price + (sl_pips * pip_v)
        tp = entry_price - (tp_pips * pip_v)
    
    return place_order(symbol, direction, 0.01, sl, tp)


def close_all():
    """Fecha todas as posições."""
    try:
        async def _close():
            import websockets
            async with websockets.connect(DAEMON, max_size=50*1024*1024) as ws:
                await _call(ws, "find_mt5", delay=0.3)
                await _call(ws, "key", {"key": "ctrl+t"}, delay=1)
                await _call(ws, "mousemove", {"x": 500, "y": 400}, delay=0.2)
                await _call(ws, "click", {"x": 500, "y": 400, "button": 3}, delay=0.5)
                for _ in range(8):
                    await _call(ws, "key", {"key": "down"}, delay=0.05)
                await _call(ws, "key", {"key": "enter"}, delay=1)
        asyncio.run(_close())
        return {'status': 'close_all_sent'}
    except Exception as e:
        return {'error': str(e)}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'usage: <buy|sell|close_all> [symbol] [entry] [fvg] [atr]'}))
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'close_all':
        print(json.dumps(close_all()))
    elif cmd in ('buy', 'sell'):
        pair = sys.argv[2] if len(sys.argv) > 2 else 'EUR/USD'
        entry = float(sys.argv[3]) if len(sys.argv) > 3 else 0
        fvg = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0
        atr = float(sys.argv[5]) if len(sys.argv) > 5 else 5.0
        print(json.dumps(place_choch_order(pair, cmd, entry, fvg, atr)))
    else:
        print(json.dumps({'error': f'unknown command: {cmd}'}))
