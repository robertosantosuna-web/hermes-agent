#!/usr/bin/env python3
"""
Brain Browser Controller v2 — WebSocket CDP para Brave/Chromium headless.
Usa Chrome DevTools Protocol via WebSocket na porta 9222 (Brave real).
Dependências: websockets (pip install websockets)

Uso pelos scripts do cérebro:
  python3 scripts/brain_browser.py --navigate 'https://...' --content
  python3 scripts/brain_browser.py --status
  python3 scripts/brain_browser.py --screenshot /tmp/chart.png
"""

import asyncio, json, sys, os, base64, urllib.request
from pathlib import Path

CDP_URL = 'http://localhost:9222'  # Brain browser (Brave real, :9222)

# ── Core CDP Functions ────────────────────────────────────────────────────

async def _cdp_command(method, params=None, timeout=15):
    """Send a CDP command via WebSocket and return result."""
    import websockets
    
    # Get active tab
    tabs = json.loads(urllib.request.urlopen(f"{CDP_URL}/json/list").read())
    tab = next((t for t in tabs if t.get('type') == 'page'), None)
    if not tab:
        # Create new tab
        req = urllib.request.Request(f"{CDP_URL}/json/new", method='PUT')
        resp = urllib.request.urlopen(req, timeout=5)
        tab = json.loads(resp.read())
    
    ws_url = tab['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({'id': 1, 'method': method, 'params': params or {}}))
        resp = await asyncio.wait_for(ws.recv(), timeout=timeout)
        return json.loads(resp)


async def cleanup_tabs():
    """Fecha todas as abas extras, mantendo apenas 1 página."""
    try:
        tabs = json.loads(urllib.request.urlopen(f"{CDP_URL}/json/list").read())
        page_tabs = [t for t in tabs if t.get('type') == 'page']
        if len(page_tabs) <= 1:
            return len(page_tabs)
        
        # Mantém a primeira, fecha o resto
        closed = 0
        for t in page_tabs[1:]:
            try:
                urllib.request.urlopen(
                    urllib.request.Request(f"{CDP_URL}/json/close/{t['id']}"),
                    timeout=3
                )
                closed += 1
            except:
                pass
        return closed
    except Exception as e:
        return f"cleanup error: {e}"


async def navigate(url, reuse=True):
    """Navigate to URL. Reuses existing page tab by default (no new tabs)."""
    import websockets
    
    tab = None
    if reuse:
        # Find existing page tab to reuse
        tabs = json.loads(urllib.request.urlopen(f"{CDP_URL}/json/list").read())
        for t in tabs:
            if t.get('type') == 'page':
                tab = t
                break
    
    if not tab:
        # Create fresh tab only if no existing tab to reuse
        req = urllib.request.Request(f"{CDP_URL}/json/new", method='PUT')
        resp = urllib.request.urlopen(req, timeout=5)
        tab = json.loads(resp.read())
    
    ws_url = tab['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        # Navigate
        await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': url}}))
        resp = await asyncio.wait_for(ws.recv(), timeout=15)
        nav_result = json.loads(resp).get('result', {})
        
        # Wait for page to load
        await asyncio.sleep(3)
        
        # Get title
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate',
            'params': {'expression': 'document.title', 'returnByValue': True}}))
        resp = await asyncio.wait_for(ws.recv(), timeout=10)
        title = json.loads(resp).get('result', {}).get('result', {}).get('value', '')
        
        return {
            'tab_id': tab['id'],
            'title': title,
            'url': url,
            'frame_id': nav_result.get('frameId', ''),
            'loader_id': nav_result.get('loaderId', ''),
        }


async def evaluate(js_code):
    """Execute JavaScript in the active page."""
    result = await _cdp_command('Runtime.evaluate', {
        'expression': js_code,
        'returnByValue': True,
    })
    return result.get('result', {}).get('result', {})


async def get_title():
    """Get page title."""
    result = await evaluate('document.title')
    return {'title': result.get('value', '')}


async def get_content():
    """Get page text content."""
    result = await evaluate('document.body ? document.body.innerText.substring(0, 15000) : ""')
    return {'text': result.get('value', '')}


async def screenshot(output_path=None):
    """Capture page screenshot as PNG."""
    result = await _cdp_command('Page.captureScreenshot', {'format': 'png'}, timeout=15)
    data = result.get('result', {}).get('data', '')
    
    if data:
        img_data = base64.b64decode(data)
        out = output_path or '/tmp/brain_screenshot.png'
        Path(out).write_bytes(img_data)
        return {'screenshot': out, 'size': len(img_data)}
    return {'error': 'No screenshot data'}


async def click_element(selector):
    """Click element by CSS selector."""
    js = f"""
    (function() {{
        const el = document.querySelector('{selector}');
        if (!el) return JSON.stringify({{error: 'NOT_FOUND', selector: '{selector}'}});
        el.click();
        return JSON.stringify({{clicked: true, tag: el.tagName, text: (el.innerText||'').substring(0, 50)}});
    }})()
    """
    result = await evaluate(js)
    try:
        return json.loads(result.get('value', '{}'))
    except:
        return {'raw': result.get('value', '')}


async def type_text(selector, text):
    """Type text into input element."""
    js = f"""
    (function() {{
        const el = document.querySelector('{selector}');
        if (!el) return JSON.stringify({{error: 'NOT_FOUND'}});
        el.focus();
        el.value = {json.dumps(text)};
        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
        return JSON.stringify({{typed: true}});
    }})()
    """
    result = await evaluate(js)
    try:
        return json.loads(result.get('value', '{}'))
    except:
        return {'raw': result.get('value', '')}


async def get_status():
    """Check browser health."""
    try:
        version = json.loads(urllib.request.urlopen(f"{CDP_URL}/json/version").read())
        tabs = json.loads(urllib.request.urlopen(f"{CDP_URL}/json/list").read())
        page_tabs = [t for t in tabs if t.get('type') == 'page']
        
        return {
            'online': True,
            'browser': version.get('Browser', '?'),
            'tabs': len(page_tabs),
            'cdp_url': CDP_URL,
            'active_tab': page_tabs[-1].get('title', '') if page_tabs else 'none',
        }
    except Exception as e:
        return {'online': False, 'error': str(e)}


async def get_tabs():
    """List all open tabs."""
    try:
        tabs = json.loads(urllib.request.urlopen(f"{CDP_URL}/json/list").read())
        return {'tabs': [
            {'id': t.get('id', ''), 'title': t.get('title', ''), 'url': t.get('url', ''), 'type': t.get('type', '')}
            for t in tabs
        ]}
    except Exception as e:
        return {'error': str(e)}


# ── Main CLI ──────────────────────────────────────────────────────────────

import fcntl, time

def main():
    import argparse
    
    # FILE LOCK: previne múltiplas instâncias simultâneas
    lockfile = Path('/tmp/brain_browser.lock')
    lockfile.touch(exist_ok=True)
    lock_fd = open(lockfile, 'w')
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("BUSY: another brain_browser instance is running", file=sys.stderr)
        sys.exit(0)
    
    parser = argparse.ArgumentParser(description='Brain Browser Controller v2')
    parser.add_argument('--navigate', help='URL to navigate to')
    parser.add_argument('--screenshot', nargs='?', const='/tmp/brain_screenshot.png', help='Capture screenshot')
    parser.add_argument('--content', action='store_true', help='Extract page text')
    parser.add_argument('--title', action='store_true', help='Get page title')
    parser.add_argument('--eval', help='JavaScript to evaluate')
    parser.add_argument('--click', help='CSS selector to click')
    parser.add_argument('--type', nargs=2, metavar=('SELECTOR', 'TEXT'), help='Type text into element')
    parser.add_argument('--status', action='store_true', help='Check browser status')
    parser.add_argument('--tabs', action='store_true', help='List open tabs')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    async def run():
        # Cleanup tabs antes de qualquer operação
        cleaned = await cleanup_tabs()
        if isinstance(cleaned, int) and cleaned > 0:
            print(f"CLEANUP: {cleaned} abas fechadas", file=sys.stderr)
        
        if args.status:
            return await get_status()
        elif args.tabs:
            return await get_tabs()
        elif args.navigate:
            result = await navigate(args.navigate)
            if args.content:
                content = await get_content()
                result['content'] = content.get('text', '')[:800]
            if args.title:
                title = await get_title()
                result['title'] = title.get('title', '')
            return result
        elif args.content:
            return await get_content()
        elif args.title:
            return await get_title()
        elif args.screenshot:
            path = args.screenshot if isinstance(args.screenshot, str) else '/tmp/brain_screenshot.png'
            return await screenshot(path)
        elif args.eval:
            result = await evaluate(args.eval)
            return {'result': result}
        elif args.click:
            return await click_element(args.click)
        elif args.type:
            return await type_text(args.type[0], args.type[1])
        else:
            parser.print_help()
            return None
    
    result = asyncio.run(run())
    
    if result is None:
        return
    
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    elif isinstance(result, dict):
        if 'error' in result:
            print(f"ERROR: {result['error']}")
        elif 'online' in result:
            status = 'ONLINE' if result['online'] else 'OFFLINE'
            print(f"Browser: {status}")
            for k, v in result.items():
                if k != 'online':
                    print(f"  {k}: {v}")
        elif 'text' in result:
            print(result['text'][:1000])
        elif 'screenshot' in result:
            print(f"Screenshot: {result['screenshot']} ({result.get('size', 0)} bytes)")
        elif 'tabs' in result:
            for t in result['tabs']:
                print(f"  [{t['type']}] {t['title'][:60]} — {t['url'][:60]}")
        else:
            print(json.dumps(result, indent=2, default=str))
    else:
        print(str(result))


if __name__ == '__main__':
    main()
