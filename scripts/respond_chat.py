#!/usr/bin/env python3
"""
Envia resposta do agente (Hermes) para o app MindCoach.
Uso: python3 respond_chat.py "Mensagem de resposta"

A resposta aparece no app na tela de chat.
"""
import json, sys, urllib.request, os, asyncio, websockets

APP_URL = os.environ.get('MINDCOACH_URL', 'https://mindcoach-541659260074.us-central1.run.app')
WS_URL = 'ws://127.0.0.1:9877'

async def send_via_ws(texto):
    """Envia resposta via WebSocket (bridge local)"""
    try:
        async with websockets.connect(WS_URL) as ws:
            await ws.send(json.dumps({
                'type': 'chat',
                'mensagens': [{'role': 'hermes', 'texto': texto}]
            }))
            return True
    except Exception as e:
        print(f"WS erro: {e}", file=sys.stderr)
        return False

def send_via_rest(texto):
    """Envia resposta via REST API (Cloud Run)"""
    try:
        data = json.dumps({"from": "assistant", "text": texto}).encode()
        req = urllib.request.Request(
            f'{APP_URL}/api/chat',
            data=data,
            headers={"Content-Type": "application/json"},
            method='POST'
        )
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"REST erro: {e}", file=sys.stderr)
        return False

def send(texto):
    """Envia resposta — tenta WS primeiro, fallback REST"""
    # Tenta WebSocket local
    try:
        loop = asyncio.get_event_loop()
    except:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    ok = loop.run_until_complete(send_via_ws(texto))
    if not ok:
        # Fallback REST
        send_via_rest(texto)
    else:
        # Também manda REST pra sincronizar
        send_via_rest(texto)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: respond_chat.py 'Mensagem de resposta'")
        sys.exit(1)
    
    texto = sys.argv[1]
    send(texto)
    print(f"OK: {texto[:60]}...")
