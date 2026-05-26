#!/usr/bin/env python3
"""
MindCoach Chat Responder — usado pelo Hermes Agent para responder mensagens.
Uso: python3 chat_respond.py [check|reply <msg_id> <texto>]
"""
import json, sys, os, urllib.request
from pathlib import Path

CHAT_URL = os.environ.get('MINDCOACH_URL', 'https://mindcoach-541659260074.us-central1.run.app')
CHAT_API = f'{CHAT_URL}/api/chat'

def check():
    """Verifica mensagens pendentes do usuário"""
    try:
        resp = urllib.request.urlopen(f'{CHAT_API}?since=0', timeout=10)
        data = json.loads(resp.read())
        msgs = data.get('messages', [])
        user_msgs = [m for m in msgs if m.get('from') == 'user']
        
        if not user_msgs:
            print('📭 Nenhuma mensagem pendente')
            return
        
        print(f'📬 {len(user_msgs)} mensagem(ns) do MindCoach:')
        for m in user_msgs:
            print(f'  [{m["id"]}] {m.get("time","")[:16]} — {m.get("text","")}')
    except Exception as e:
        print(f'❌ Erro: {e}')

def reply(text):
    """Envia resposta do Hermes"""
    try:
        data = json.dumps({'from': 'hermes', 'text': text}).encode()
        req = urllib.request.Request(CHAT_API, data=data, 
                                       headers={'Content-Type': 'application/json'},
                                       method='POST')
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        if result.get('ok'):
            print(f'✅ Resposta enviada (id={result.get("id")})')
        else:
            print(f'❌ Erro: {result}')
    except Exception as e:
        print(f'❌ Erro: {e}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: chat_respond.py check | reply '<texto>'")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == 'check':
        check()
    elif cmd == 'reply':
        if len(sys.argv) < 3:
            print("Uso: chat_respond.py reply '<texto>'")
            sys.exit(1)
        reply(sys.argv[2])
    else:
        print(f'Comando desconhecido: {cmd}')
