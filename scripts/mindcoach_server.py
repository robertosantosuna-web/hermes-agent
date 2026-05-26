#!/usr/bin/env python3
"""
MindCoach Desktop Server — HTTP + Live Reload
Porta 9878: HTTP (app)
Porta 9879: WebSocket (live reload)
Auto-rebuild data.json quando dados neurais mudam.
"""
import http.server
import socketserver
import asyncio
import json
import os
import time
import hashlib
import threading
from pathlib import Path
from datetime import datetime

APP_DIR = Path.home() / '.hermes' / 'mindcoach-pro'
HERMES_DIR = Path.home() / '.hermes'
HTTP_PORT = 9878
WS_PORT = 9879

# Arquivos que disparam rebuild + reload
WATCH_PATHS = [
    HERMES_DIR / 'forex' / 'weekly_bias.json',
    HERMES_DIR / 'forex' / 'signals_pending.json',
    HERMES_DIR / 'forex' / 'knowledge_bridge.json',
    HERMES_DIR / 'mindcoach_state.json',
    HERMES_DIR / 'brain_context.json',
    HERMES_DIR / 'brain' / 'agenda.json',
    APP_DIR / 'index.html',
    APP_DIR / 'sw.js',
    APP_DIR / 'core' / 'main.js',
    APP_DIR / 'core' / 'websocket.js',
    APP_DIR / 'data.json',
]

# Hash cache para detectar mudanças
file_hashes = {}
ws_clients = set()

def file_hash(path):
    try:
        stat = path.stat()
        return f"{stat.st_mtime}:{stat.st_size}"
    except:
        return ''

def rebuild_data():
    """Executa build_data.sh"""
    script = APP_DIR / 'build_data.sh'
    if script.exists():
        os.system(f'bash {script} 2>/dev/null')
        return True
    return False

def watch_files():
    """Monitora arquivos e notifica mudanças"""
    # Inicializar hashes
    for p in WATCH_PATHS:
        if p.exists():
            file_hashes[str(p)] = file_hash(p)
    
    print(f'[watch] Monitorando {len(WATCH_PATHS)} arquivos...')
    
    while True:
        time.sleep(3)  # Check a cada 3 segundos
        changed = False
        
        for p in WATCH_PATHS:
            if not p.exists():
                continue
            h = file_hash(p)
            if h and h != file_hashes.get(str(p), ''):
                print(f'[watch] Mudança detectada: {p.name}')
                file_hashes[str(p)] = h
                changed = True
        
        if changed:
            # Rebuild data
            rebuild_data()
            # Atualizar hash do data.json
            dj = APP_DIR / 'data.json'
            if dj.exists():
                file_hashes[str(dj)] = file_hash(dj)
            # Notificar todos os browsers
            notify_reload()

def notify_reload():
    """Envia comando de reload para todos os browsers conectados"""
    if not ws_clients or not LOOP:
        return
    dead = set()
    for ws in list(ws_clients):
        try:
            # Enviar via event loop (websockets é async)
            asyncio.run_coroutine_threadsafe(
                ws.send(json.dumps({'type': 'reload'})),
                LOOP
            )
        except:
            dead.add(ws)
    ws_clients.difference_update(dead)
    if dead:
        print(f'[ws] {len(dead)} cliente(s) removidos', flush=True)
    print(f'[ws] Reload enviado para {len(ws_clients)} cliente(s)', flush=True)

# Event loop global para comunicação cross-thread
LOOP = None

async def ws_handler(websocket):
    """WebSocket handler — live reload"""
    ws_clients.add(websocket)
    print(f'[ws] Cliente conectado (total: {len(ws_clients)})')
    try:
        async for msg in websocket:
            pass  # Não esperamos mensagens do browser
    except:
        pass
    finally:
        ws_clients.discard(websocket)

async def ws_server():
    """WebSocket server na porta 9879"""
    global LOOP
    LOOP = asyncio.get_running_loop()
    import websockets
    print(f'[ws] Live reload em ws://127.0.0.1:{WS_PORT}', flush=True)
    async with websockets.serve(ws_handler, '127.0.0.1', WS_PORT):
        await asyncio.Future()

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(APP_DIR), **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Service-Worker-Allowed', '/')
        # No-cache em HTML/JS pra dev
        if self.path.endswith(('.html','.js','.json')):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()
    
    def log_message(self, format, *args):
        # Silencioso — só erros aparecem
        if args[0] != '200':
            print(f'[http] {args[0]} {self.path}')

def run_http():
    """HTTP server em thread separada"""
    os.chdir(str(APP_DIR))
    with socketserver.TCPServer(('0.0.0.0', HTTP_PORT), Handler) as httpd:
        print(f'[http] App: http://0.0.0.0:{HTTP_PORT}')
        httpd.serve_forever()

def main():
    import sys
    print('═' * 50, flush=True)
    print('  MindCoach Desktop Server — Live Reload', flush=True)
    print(f'  App:  http://127.0.0.1:{HTTP_PORT}', flush=True)
    print(f'  WS:   ws://127.0.0.1:{WS_PORT}', flush=True)
    print('═' * 50, flush=True)
    
    # Rebuild inicial
    rebuild_data()
    
    # File watcher em thread
    watcher = threading.Thread(target=watch_files, daemon=True)
    watcher.start()
    
    # HTTP server em thread
    http_thread = threading.Thread(target=run_http, daemon=True)
    http_thread.start()
    
    # WebSocket server no loop principal
    asyncio.run(ws_server())

if __name__ == '__main__':
    main()
