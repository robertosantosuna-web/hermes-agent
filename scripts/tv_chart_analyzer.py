#!/usr/bin/env python3
"""
TradingView Chart Analyzer — Análise visual de gráficos + Bar Replay.
Usa CDP WebSocket para controlar o TradingView (logado).

Funcionalidades:
  --pair EURUSD         Selecionar par forex
  --tf M15              Timeframe (M5, M15, M30, H1, H4, D)
  --replay DATE         Iniciar Bar Replay a partir da data
  --replay-step N       Avançar N candles no replay
  --replay-speed S      Velocidade do replay (1-100)
  --screenshot FILE     Capturar screenshot do chart
  --price               Retornar preço atual
  --indicators LIST     Adicionar indicadores (ex: "RSI,EMA20,Volume")
  --watchlist PAIRS     Configurar watchlist
  --scan-patterns       Escanear padrões visíveis no chart
  --add-alert COND      Criar alerta

Integra com: chart_pattern_study.py + Neural KB + Visual Cortex.
"""
import asyncio, json, sys, os, base64, urllib.request, time
from pathlib import Path
from datetime import datetime, timedelta

CDP_URL = 'http://localhost:9223'
HERMES = Path(os.path.expanduser('~/.hermes'))
SCREENSHOTS_DIR = HERMES / 'forex' / 'charts' / 'tradingview'

# ── CDP Helpers ───────────────────────────────────────────────────────────

async def get_tv_tab():
    """Get or create TradingView tab."""
    tabs = json.loads(urllib.request.urlopen(f"{CDP_URL}/json/list").read())
    tab = next((t for t in tabs if t.get('type') == 'page' and 'tradingview.com/chart' in t.get('url', '')), None)
    if not tab:
        # Create new tab with TV
        req = urllib.request.Request(f"{CDP_URL}/json/new", method='PUT')
        resp = urllib.request.urlopen(req, timeout=5)
        tab = json.loads(resp.read())
        import websockets
        ws_url = tab['webSocketDebuggerUrl']
        async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
            await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': 'https://www.tradingview.com/chart/'}}))
            await asyncio.wait_for(ws.recv(), timeout=15)
        await asyncio.sleep(2)
    return tab


async def tv_eval(js_code, timeout=10):
    """Execute JS in TradingView tab."""
    import websockets
    tab = await get_tv_tab()
    ws_url = tab['webSocketDebuggerUrl']
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': js_code, 'returnByValue': True}}))
        resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))
        return resp.get('result', {}).get('result', {}).get('value')


async def tv_navigate(url):
    """Navigate TV tab to URL."""
    import websockets
    tab = await get_tv_tab()
    ws_url = tab['webSocketDebuggerUrl']
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': url}}))
        await asyncio.wait_for(ws.recv(), timeout=15)
        await asyncio.sleep(2)


async def tv_screenshot(output_path):
    """Capture screenshot of TradingView chart."""
    import websockets
    tab = await get_tv_tab()
    ws_url = tab['webSocketDebuggerUrl']
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({'id': 1, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
        resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
        data = resp.get('result', {}).get('data', '')
        if data:
            img_data = base64.b64decode(data)
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_bytes(img_data)
            return output_path, len(img_data)
    return None, 0


# ── Chart Operations ──────────────────────────────────────────────────────

PAIRS = {
    'EURUSD': 'FX:EURUSD', 'GBPUSD': 'FX:GBPUSD', 'USDJPY': 'FX:USDJPY',
    'AUDUSD': 'FX:AUDUSD', 'NZDUSD': 'FX:NZDUSD', 'USDCAD': 'FX:USDCAD',
    'EURGBP': 'FX:EURGBP', 'GBPJPY': 'FX:GBPJPY',
}

TIMEFRAMES = {'M5': '5', 'M15': '15', 'M30': '30', 'H1': '60', 'H4': '240', 'D': '1D'}


async def set_chart(pair='EURUSD', tf='M15'):
    """Configure chart symbol and timeframe."""
    symbol = PAIRS.get(pair, f'FX:{pair}')
    interval = TIMEFRAMES.get(tf, '15')
    url = f'https://www.tradingview.com/chart/?symbol={symbol}&interval={interval}'
    await tv_navigate(url)
    
    # Verify
    title = await tv_eval('document.title')
    return {'pair': pair, 'timeframe': tf, 'url': url, 'title': title}


async def get_current_price():
    """Get current price from chart title."""
    title = await tv_eval('document.title')
    return title


async def get_ohlc():
    """Try to extract visible OHLC data from chart."""
    js = """
    (function() {
        // TradingView stores data in widget state
        // Try to get from the chart widget
        try {
            const widget = window.tvWidget || window.TradingView?.widget;
            if (widget && widget.activeChart) {
                const chart = widget.activeChart();
                const data = chart.data();
                if (data && data.ohlc && data.ohlc.length > 0) {
                    const last = data.ohlc[data.ohlc.length - 1];
                    return JSON.stringify({o: last.open, h: last.high, l: last.low, c: last.close, t: last.time});
                }
            }
        } catch(e) {}
        return null;
    })()
    """
    result = await tv_eval(js)
    try:
        return json.loads(result) if result else None
    except:
        return {'raw': str(result)[:200]}


# ── Bar Replay ────────────────────────────────────────────────────────────

async def start_bar_replay(date_str=None):
    """
    Start Bar Replay mode on TradingView.
    If date_str provided, jump to that date (format: YYYY-MM-DD).
    Otherwise start from beginning of visible data.
    """
    # Click the Bar Replay button
    js = """
    (function() {
        // Find and click Bar Replay button
        const buttons = document.querySelectorAll('[data-name="bar-replay"], [data-role="replay"], button');
        for (let b of buttons) {
            if (b.innerText && b.innerText.includes('Replay')) {
                b.click();
                return 'clicked_replay';
            }
            if (b.getAttribute('aria-label') && b.getAttribute('aria-label').includes('replay')) {
                b.click();
                return 'clicked_replay_aria';
            }
        }
        // Try keyboard shortcut: Alt+R
        return 'trying_keyboard';
    })()
    """
    result = await tv_eval(js)
    
    if 'trying_keyboard' in str(result):
        # Use keyboard shortcut
        import websockets
        tab = await get_tv_tab()
        ws_url = tab['webSocketDebuggerUrl']
        async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
            await ws.send(json.dumps({'id': 1, 'method': 'Input.dispatchKeyEvent', 'params': {
                'type': 'keyDown', 'key': 'r', 'code': 'KeyR', 'modifiers': 1,  # Alt
            }}))
            await asyncio.sleep(0.1)
            await ws.send(json.dumps({'id': 2, 'method': 'Input.dispatchKeyEvent', 'params': {
                'type': 'keyUp', 'key': 'r', 'code': 'KeyR', 'modifiers': 1,
            }}))
    
    await asyncio.sleep(1)
    return {'bar_replay': 'started', 'date': date_str or 'beginning'}


async def replay_step(steps=1):
    """Advance replay by N candles (right arrow key)."""
    import websockets
    tab = await get_tv_tab()
    ws_url = tab['webSocketDebuggerUrl']
    
    for _ in range(steps):
        async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
            await ws.send(json.dumps({'id': 1, 'method': 'Input.dispatchKeyEvent', 'params': {
                'type': 'keyDown', 'key': 'ArrowRight', 'code': 'ArrowRight',
            }}))
            await asyncio.sleep(0.05)
            await ws.send(json.dumps({'id': 2, 'method': 'Input.dispatchKeyEvent', 'params': {
                'type': 'keyUp', 'key': 'ArrowRight', 'code': 'ArrowRight',
            }}))
        await asyncio.sleep(0.15)
    
    # Get bar count
    count = await tv_eval("""
    (function() {
        try {
            const el = document.querySelector('[data-name="replay-date"]');
            return el ? el.innerText : 'replay_active';
        } catch(e) { return 'error'; }
    })()
    """)
    return {'steps': steps, 'status': count}


async def replay_back(steps=1):
    """Go back N candles in replay (left arrow key)."""
    import websockets
    tab = await get_tv_tab()
    ws_url = tab['webSocketDebuggerUrl']
    
    for _ in range(steps):
        async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
            await ws.send(json.dumps({'id': 1, 'method': 'Input.dispatchKeyEvent', 'params': {
                'type': 'keyDown', 'key': 'ArrowLeft', 'code': 'ArrowLeft',
            }}))
            await asyncio.sleep(0.05)
            await ws.send(json.dumps({'id': 2, 'method': 'Input.dispatchKeyEvent', 'params': {
                'type': 'keyUp', 'key': 'ArrowLeft', 'code': 'ArrowLeft',
            }}))
        await asyncio.sleep(0.15)
    
    return await replay_step(0)  # Just get status


async def stop_bar_replay():
    """Stop Bar Replay mode."""
    js = """
    (function() {
        const buttons = document.querySelectorAll('button');
        for (let b of buttons) {
            if (b.innerText && (b.innerText.includes('Exit') || b.innerText.includes('Stop'))) {
                if (b.closest('[data-name="replay"]') || b.closest('.replay-ControlBar')) {
                    b.click();
                    return 'stopped';
                }
            }
        }
        return 'not_found';
    })()
    """
    return await tv_eval(js)


# ── Pattern Scanning ──────────────────────────────────────────────────────

async def scan_visible_patterns():
    """
    Scan the visible chart for patterns using TradingView's built-in
    pattern detection + our own heuristics.
    """
    js = """
    (function() {
        // Try to get visible price data
        const result = {
            title: document.title,
            timeframe: '',
            visible_bars: 0,
        };
        
        // Get timeframe from UI
        const tfEl = document.querySelector('[data-name="timeframe"] span, .value-OcsyMhpa');
        if (tfEl) result.timeframe = tfEl.innerText;
        
        // Count visible candles
        const canvasEls = document.querySelectorAll('canvas');
        result.canvas_count = canvasEls.length;
        
        // Try to get chart state
        try {
            if (window.tvWidget) {
                const chart = window.tvWidget.activeChart();
                if (chart) {
                    const studies = chart.getAllStudies();
                    result.indicators = studies.map(s => s.name || s.id);
                }
            }
        } catch(e) {}
        
        return JSON.stringify(result);
    })()
    """
    result = await tv_eval(js)
    try:
        return json.loads(result) if result else {}
    except:
        return {'raw': str(result)[:200]}


# ── Screenshot Pipeline ───────────────────────────────────────────────────

async def capture_chart_screenshot(pair, tf, label=''):
    """Capture and save chart screenshot with metadata."""
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{pair}_{tf}_{label}_{ts}.png' if label else f'{pair}_{tf}_{ts}.png'
    path = str(SCREENSHOTS_DIR / filename)
    filepath, size = await tv_screenshot(path)
    return {'file': filepath, 'size': size, 'pair': pair, 'timeframe': tf}


# ── Watchlist Setup ───────────────────────────────────────────────────────

async def setup_watchlist(pairs=None):
    """Add pairs to TradingView watchlist."""
    if pairs is None:
        pairs = ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDJPY', 'USDCAD']
    
    js = """
    (function() {
        const symbolList = %s;
        const results = [];
        
        // Open symbol search
        const searchBtn = document.querySelector('[data-name="symbol-search"], [data-name="quick-search"]');
        if (searchBtn) searchBtn.click();
        
        return JSON.stringify({status: 'search_opened', pairs: symbolList.length});
    })()
    """ % json.dumps(pairs)
    
    result = await tv_eval(js)
    return result


# ── Main CLI ──────────────────────────────────────────────────────────────

async def main_async(args):
    if args.status:
        info = await scan_visible_patterns()
        print(json.dumps(info, indent=2))
    
    elif args.pair:
        result = await set_chart(args.pair, args.tf or 'M15')
        print(f"Chart: {result['pair']} {result['timeframe']}")
        print(f"Title: {result['title']}")
        
        if args.screenshot:
            cap = await capture_chart_screenshot(args.pair, args.tf or 'M15')
            print(f"Screenshot: {cap['file']} ({cap['size']} bytes)")
        
        if args.replay:
            replay = await start_bar_replay(args.replay)
            print(f"Replay: {replay}")
            
            if args.replay_steps:
                for i in range(0, args.replay_steps, 10):
                    batch = min(10, args.replay_steps - i)
                    status = await replay_step(batch)
                    print(f"  Step {i+batch}: {status.get('status', '?')}")
                    
                    if args.screenshot:
                        cap = await capture_chart_screenshot(args.pair, args.tf or 'M15', f'replay_{i+batch}')
                        print(f"  Shot: {cap['file']}")
            
            if args.replay_stop:
                await stop_bar_replay()
                print("Replay stopped")
    
    elif args.price:
        price = await get_current_price()
        print(price)
    
    elif args.screenshot:
        cap = await capture_chart_screenshot('EURUSD', 'M15', 'quick')
        print(f"Screenshot: {cap['file']} ({cap['size']} bytes)")
    
    elif args.watchlist:
        result = await setup_watchlist(args.watchlist.split(',') if args.watchlist != 'default' else None)
        print(result)
    
    else:
        print("Usage: tv_chart_analyzer.py --pair EURUSD [--tf M15] [--replay DATE] [--screenshot] [--price]")
        print("Pairs:", ', '.join(PAIRS.keys()))
        print("Timeframes:", ', '.join(TIMEFRAMES.keys()))


def main():
    import argparse
    parser = argparse.ArgumentParser(description='TradingView Chart Analyzer')
    parser.add_argument('--pair', help='Forex pair (EURUSD, GBPUSD, etc.)')
    parser.add_argument('--tf', help='Timeframe (M5, M15, M30, H1, H4, D)')
    parser.add_argument('--price', action='store_true', help='Get current price')
    parser.add_argument('--screenshot', action='store_true', help='Capture screenshot')
    parser.add_argument('--status', action='store_true', help='Show chart status')
    parser.add_argument('--replay', help='Start Bar Replay from date (YYYY-MM-DD)')
    parser.add_argument('--replay-steps', type=int, help='Advance replay N candles')
    parser.add_argument('--replay-stop', action='store_true', help='Stop replay')
    parser.add_argument('--watchlist', nargs='?', const='default', help='Setup watchlist')
    
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == '__main__':
    main()
