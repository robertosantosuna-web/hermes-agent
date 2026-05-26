#!/usr/bin/env python3
"""
Envia solicitação de autorização para o app MindCoach.
Uso: python3 auth_request.py "Título" "Mensagem" [--expires ISO_TIME]

O app mostra a solicitação na aba 🔐 Autorizações.
Roberto aprova/recusa e a resposta fica disponível via GET /auth?since=ID
"""
import json, sys, urllib.request, os
from datetime import datetime, timedelta

APP_URL = os.environ.get('MINDCOACH_URL', 'https://mindcoach-541659260074.us-central1.run.app')

def send_auth(titulo, msg, expires_hours=24):
    """Envia pedido de autorização para o app"""
    expires = (datetime.utcnow() + timedelta(hours=expires_hours)).isoformat()
    payload = {
        'titulo': titulo,
        'msg': msg,
        'from': 'hermes',
        'expires': expires
    }
    url = f'{APP_URL}/chat_api/auth'
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    resp = urllib.request.urlopen(req, timeout=10)
    result = json.loads(resp.read())
    return result

def check_response(request_id=None):
    """Verifica resposta de uma autorização pendente"""
    url = f'{APP_URL}/chat_api/auth'
    resp = urllib.request.urlopen(url, timeout=10)
    data = json.loads(resp.read())
    
    # Se não é mais pending, a resposta chegou
    for req in data.get('requests', []):
        if request_id and req['id'] != request_id:
            continue
        if req.get('status') != 'pending':
            return req
    
    return None

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Uso: auth_request.py 'Título' 'Mensagem'")
        print("     auth_request.py --check [ID]")
        sys.exit(1)
    
    if sys.argv[1] == '--check':
        req_id = sys.argv[2] if len(sys.argv) > 2 else None
        resp = check_response(req_id)
        if resp:
            print(json.dumps(resp, indent=2, ensure_ascii=False))
        else:
            print('{"status": "still_pending"}')
    else:
        titulo = sys.argv[1]
        msg = sys.argv[2]
        result = send_auth(titulo, msg)
        print(f"OK id={result['id']}")
