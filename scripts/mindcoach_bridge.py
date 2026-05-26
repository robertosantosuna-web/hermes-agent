#!/usr/bin/env python3
"""
MindCoach Bridge — Hermes Agent ↔ MindCoach Pro App
WebSocket server na porta 9877.
Hermes envia JSON de renderização, o app obedece.
App envia dados do usuário, Hermes processa.
v2 — Chat persistente + data cache
"""
import asyncio, json, os, sys, time
from datetime import datetime
from pathlib import Path

APP_DIR = Path.home() / '.hermes' / 'mindcoach-pro'
STATE_FILE = Path.home() / '.hermes' / 'mindcoach_state.json'
CHAT_HISTORY_FILE = Path.home() / '.hermes' / 'mindcoach_chat_history.json'
DATA_FILE = Path.home() / '.hermes' / 'mindcoach-pro' / 'data.json'

# Client connections
clients = {}
sw_clients = {}
chat_history = []
data_cache = {}

current_state = {
    'screen': 'dashboard',
    'pilar': 'dashboard',
    'theme': {'bg': '#0a0a1a', 'fg': '#e0e0f0', 'accent': '#6c5ce7', 'card': '#12122a'},
    'pilares': {
        'financeiro': {'saldo': '$399.93', 'receitas': 0, 'despesas': 0, 'forex_wr': '100%', 'forex_pnl': '+24.2p', 'forex_trades': 3, 'mt5': 'offline (domingo)', 'sinais_pendentes': 1},
        'saude': {'score': 'ativo', 'agua': '?', 'exercicio': '?', 'sono': '?', 'nota': 'sem tracking'},
        'mental': {'humor': 'foco/produtivo', 'ansiedade': 0, 'nota': 'sessão dev produtiva'},
        'social': {'email_nao_lidos': 10, 'trabalho_21maio+': 5, 'pessoal_2semanas': 10, 'respondidos_hoje': 0, 'destaque': 'Martin (99Freelas) respondeu!'},
        'produtividade': {'foco': 'MindCoach + dados pilares', 'pomodoros': 0, 'tarefas_ativas': 7, 'deploys_hoje': 4, 'bugs_corrigidos': 6},
        'tecnico': {'bots_ativos': 7, 'cron_jobs_ativos': 37, 'servidores': 1, 'descobertas_cerebro': 183, 'bridge_online': True, 'uptime': '2 dias', 'cpu_load': '0.37', 'disco': '55%', 'processos': 517},
        'espiritual': {'alinhamento': 'foco técnico', 'proposito': 'renda autônoma via forex+freelas'}
    },
    'alertas': [
        {'tipo': 'warn', 'titulo': '🔴 Martin respondeu!', 'msg': 'Nova mensagem no 99Freelas - Projeto Clínicas Radiológicas'},
        {'tipo': 'info', 'titulo': '📧 10 emails não lidos', 'msg': '5 de trabalho (21/05+), 10 pessoais (2 semanas)'},
        {'tipo': 'info', 'titulo': '📅 0 compromissos', 'msg': 'Google Calendar: próximos 7 dias livres'}
    ],
    'versao': 1
}

def load_chat_history():
    global chat_history
    try:
        if CHAT_HISTORY_FILE.exists():
            chat_history = json.loads(CHAT_HISTORY_FILE.read_text())
            print(f"[bridge] chat history loaded: {len(chat_history)} msgs")
    except:
        chat_history = []

def save_chat_history():
    try:
        CHAT_HISTORY_FILE.write_text(json.dumps(chat_history[-100:]))
    except:
        pass

def load_data_cache():
    global data_cache
    try:
        if DATA_FILE.exists():
            data_cache = json.loads(DATA_FILE.read_text())
            data_cache.pop('build_time', None)  # Remove campo grande
            print(f"[bridge] data loaded: {list(data_cache.keys())}")
    except:
        data_cache = {}

async def handle_client(websocket):
    cid = id(websocket)
    clients[cid] = websocket
    print(f"[app] conectado {cid}")
    
    try:
        load_chat_history()
        load_data_cache()
        # Sempre começa no dashboard para novas conexões
        current_state['screen'] = 'dashboard'
        current_state['pilar'] = 'dashboard'
        await websocket.send(json.dumps({
            'type': 'render',
            **current_state,
            'screen': current_state['screen'],
            'chat_history': chat_history[-30:],
            'data_cache': data_cache
        }))
        
        async for message in websocket:
            try:
                data = json.loads(message)
                await process_message(cid, data)
            except json.JSONDecodeError:
                pass
    except:
        pass
    finally:
        del clients[cid]
        print(f"[app] desconectado {cid}")

async def handle_sw(websocket):
    sid = id(websocket)
    sw_clients[sid] = websocket
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get('type') == 'sw_ready':
                    print(f"[sw] pronto {sid}")
            except:
                pass
    except:
        pass
    finally:
        del sw_clients[sid]

async def process_message(cid, data):
    msg_type = data.get('type', '')
    
    if msg_type in ('navigate', 'checkin', 'app_ready', 'chat_message'):
        if msg_type == 'navigate':
            pilar = data.get('pilar', 'dashboard')
            current_state['screen'] = 'pilar' if pilar != 'dashboard' else 'dashboard'
            current_state['pilar'] = pilar
            if pilar in current_state['pilares']:
                await send_to(cid, {
                    'type': 'render', 'screen': 'pilar', 'pilar': pilar,
                    'dados': current_state['pilares'][pilar], 'theme': current_state['theme'],
                    'data_cache': data_cache
                })
            else:
                await send_to(cid, {'type': 'render', **current_state, 'data_cache': data_cache})
        elif msg_type == 'checkin':
            pilar = data.get('pilar', 'mental')
            valores = data.get('valores', {})
            current_state['pilares'][pilar].update(valores)
            save_state()
            await broadcast({'type': 'render', **current_state, 'data_cache': data_cache})
        elif msg_type == 'app_ready':
            print(f"[app] pronto {cid}")
        elif msg_type == 'chat_message':
            texto = data.get('texto', '')
            ts = data.get('timestamp', '')
            print(f"[chat] app: {texto[:60]}")
            
            # Salvar no histórico persistente
            chat_history.append({'role': 'user', 'texto': texto, 'time': datetime.now().isoformat()})
            if len(chat_history) > 100:
                chat_history = chat_history[-100:]
            save_chat_history()
            
            # Echo + checkpoint
            await send_to(cid, {'type': 'chat_echo', 'texto': texto})
            await send_to(cid, {
                'type': 'render', 'screen': 'chat',
                'mensagens': [{'role': 'hermes', 'texto': '✓'}],
                'theme': current_state['theme']
            })
            
            # POST REST API
            try:
                import urllib.request as _ur
                data_post = json.dumps({"from": "assistant", "text": "✓"}).encode()
                req = _ur.Request('https://mindcoach-541659260074.us-central1.run.app/api/chat',
                                data=data_post, headers={"Content-Type": "application/json"})
                _ur.urlopen(req, timeout=5)
            except:
                pass
            
            # Acordar agente
            try:
                gateway_file = Path.home() / '.hermes' / 'gateway_checkpoint.json'
                if gateway_file.exists():
                    ck = json.loads(gateway_file.read_text())
                    ck['pending_chat'] = True
                    ck['last_chat_msg'] = texto[:200]
                    ck['last_chat_time'] = datetime.now().isoformat()
                    gateway_file.write_text(json.dumps(ck, indent=2))
            except:
                pass
    else:
        await hermes_command(data)
        ws = clients.get(cid)
        if ws:
            try:
                await ws.send(json.dumps({'type': 'render', **current_state, 'data_cache': data_cache}))
            except:
                pass

async def responder_chat(texto):
    try:
        print(f"[chat] resposta: {texto[:60]}")
        
        # Salvar no histórico
        chat_history.append({'role': 'hermes', 'texto': texto, 'time': datetime.now().isoformat()})
        if len(chat_history) > 100:
            chat_history = chat_history[-100:]
        save_chat_history()
        
        await broadcast({
            'type': 'render', 'screen': 'chat',
            'mensagens': [{'role': 'hermes', 'texto': texto}],
            'theme': current_state['theme']
        })
        
        # REST API
        try:
            import urllib.request as _ur
            data = json.dumps({"from": "assistant", "text": texto}).encode()
            req = _ur.Request('https://mindcoach-541659260074.us-central1.run.app/api/chat',
                            data=data, headers={"Content-Type": "application/json"})
            _ur.urlopen(req, timeout=5)
        except:
            pass
    except Exception as e:
        print(f"[chat] erro: {e}")

async def send_to(cid, data):
    ws = clients.get(cid)
    if ws:
        try:
            await ws.send(json.dumps(data))
        except:
            pass

async def broadcast(data):
    for ws in list(clients.values()):
        try:
            await ws.send(json.dumps(data))
        except:
            pass

async def broadcast_sw(data):
    for ws in list(sw_clients.values()):
        try:
            await ws.send(json.dumps(data))
        except:
            pass

def save_state():
    try:
        STATE_FILE.write_text(json.dumps({**current_state, 'updated': datetime.now().isoformat()}, indent=2))
    except:
        pass

async def hermes_command(command):
    cmd_type = command.get('type', '')
    
    if cmd_type == 'render':
        current_state.update({k: v for k, v in command.items() if k != 'type'})
        save_state()
        await broadcast({'type': 'render', **current_state, 'data_cache': data_cache})
    elif cmd_type == 'update_pilar':
        pilar = command.get('pilar')
        dados = command.get('dados', {})
        if pilar in current_state['pilares']:
            current_state['pilares'][pilar].update(dados)
            save_state()
        await broadcast({'type': 'render', **current_state, 'data_cache': data_cache})
    elif cmd_type == 'alerta':
        alerta = {'titulo': command.get('titulo', 'Alerta'), 'msg': command.get('msg', ''), 'tipo': command.get('tipo', 'info')}
        current_state.setdefault('alertas', []).insert(0, alerta)
        if len(current_state['alertas']) > 10:
            current_state['alertas'] = current_state['alertas'][:10]
        save_state()
        await broadcast({'type': 'render', **current_state, 'data_cache': data_cache})
        await broadcast({'type': 'bubble', 'alert': True, 'text': alerta['titulo']})
    elif cmd_type == 'theme':
        current_state['theme'].update(command.get('theme', {}))
        save_state()
        await broadcast({'type': 'theme', 'theme': current_state['theme']})
    elif cmd_type == 'bubble':
        await broadcast({'type': 'bubble', 'emoji': command.get('emoji', '⚡'), 'alert': command.get('alert', False), 'text': command.get('text', '')})
    elif cmd_type == 'chat_response':
        await responder_chat(command.get('texto', ''))
    elif cmd_type == 'refresh_data':
        load_data_cache()
        await broadcast({'type': 'data_update', 'data_cache': data_cache})

class MindCoachServer:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 9877
    
    async def start(self):
        import websockets
        print(f"[bridge] ws://{self.host}:{self.port}")
        async with websockets.serve(self.router, self.host, self.port):
            await asyncio.Future()
    
    async def router(self, websocket):
        path = websocket.path if hasattr(websocket, 'path') else ''
        if 'sw' in path:
            await handle_sw(websocket)
        else:
            await handle_client(websocket)

_server = None
_loop = None

def start_bridge():
    global _server, _loop
    _server = MindCoachServer()
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _loop.run_until_complete(_server.start())

def send_command(command: dict):
    if _loop:
        asyncio.run_coroutine_threadsafe(hermes_command(command), _loop)

if __name__ == '__main__':
    start_bridge()
