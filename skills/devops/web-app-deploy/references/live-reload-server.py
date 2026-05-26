#!/usr/bin/env python3
"""
MindCoach Desktop Server — HTTP + WebSocket Live Reload
Porta 9878: HTTP (serve arquivos estáticos)
Porta 9879: WebSocket (live reload)
Auto-rebuild data.json quando dados neurais mudam.

Systemd: /home/roberto/.config/systemd/user/mindcoach-http.service
"""
import http.server
import socketserver
import asyncio
import json
import os
import time
import threading
from pathlib import Path
from datetime import datetime

APP_DIR = Path.home() / '.hermes' / 'mindcoach-pro'
HERMES_DIR = Path.home() / '.hermes'
HTTP_PORT = 9878
WS_PORT = 9879

WATCH_PATHS = [
    HERMES_DIR / 'forex' / 'weekly_bias.json',
    HERMES_DIR / 'forex' / 'signals_pending.json',
    HERMES_DIR / 'mindcoach_state.json',
    HERMES_DIR / 'brain_context.json',
    HERMES_DIR / 'brain' / 'agenda.json',
    APP_DIR / 'index.html',
    APP_DIR / 'sw.js',
    APP_DIR / 'core' / 'main.js',
]

file_hashes = {}
ws_clients = set()
LOOP = None

def file_hash(path):
    """Usa mtime:size — NÃO content hash (touch não muda conteúdo)"""
    try:
        stat = path.stat()
        return f"{stat.st_mtime}:{stat.st_size}"
    except:
        return ''

def rebuild_data():
    script = APP_DIR / 'build_data.sh'
    if script.exists():
        os.system(f'bash {script} 2>/dev/null')
        return True
    return False

def watch_files():
    for p in WATCH_PATHS:
        if p.exists():
            file_hashes[str(p)] = file_hash(p)
    print(f'[watch] Monitorando {len(WATCH_PATHS)} arquivos...', flush=True)
    while True:
        time.sleep(3)
        changed = False
        for p in WATCH_PATHS:
            if not p.exists(): continue
            h = file_hash(p)
            if h and h != file_hashes.get(str(p), ''):
                print(f'[watch] Mudança: {p.name}', flush=True)
                file_hashes[str(p)] = h
                changed = True
        if changed:
            rebuild_data()
            notify_reload()

def notify_reload():
    if not ws_clients or not LOOP: return
    dead = set()
    for ws in list(ws_clients):
        try:
            asyncio.run_coroutine_threadsafe(
                ws.send(json.dumps({'type': 'reload'})), LOOP)
        except:
            dead.add(ws)
    ws_clients.difference_update(dead)
    print(f'[ws] Reload → {len(ws_clients)} cliente(s)', flush=True)

async def ws_handler(websocket):
    ws_clients.add(websocket)
    try:
        async for _ in websocket: pass
    except: pass
    finally:
        ws_clients.discard(websocket)

async def ws_server():
    global LOOP
    LOOP = asyncio.get_running_loop()
    import websockets
    print(f'[ws] ws://127.0.0.1:{WS_PORT}', flush=True)
    async with websockets.serve(ws_handler, '127.0.0.1', WS_PORT):
        await asyncio.Future()

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(APP_DIR), **kwargs)
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Service-Worker-Allowed', '/')
        if self.path.endswith(('.html','.js','.json')):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

def run_http():
    os.chdir(str(APP_DIR))
    with socketserver.TCPServer(('127.0.0.1', HTTP_PORT), Handler) as httpd:
        print(f'[http] http://127.0.0.1:{HTTP_PORT}', flush=True)
        httpd.serve_forever()

def main():
    import sys
    print('═' * 50, flush=True)
    print('  MindCoach Desktop Server — Live Reload', flush=True)
    print(f'  App: http://127.0.0.1:{HTTP_PORT}', flush=True)
    print(f'  WS:  ws://127.0.0.1:{WS_PORT}', flush=True)
    print('═' * 50, flush=True)
    rebuild_data()
    threading.Thread(target=watch_files, daemon=True).start()
    threading.Thread(target=run_http, daemon=True).start()
    asyncio.run(ws_server())

if __name__ == '__main__':
    main()
