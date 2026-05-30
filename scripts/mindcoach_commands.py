#!/usr/bin/env python3
"""
Neural Command Bridge — Hermes Agent → MindCoach Neural Link
Envia impulsos/comandos para o app e lê respostas do usuário.

Uso:
  python3 mindcoach_commands.py send "Abrir posição EURUSD?" "FVG+CRT detectado. RR 3:1. SL=5p TP=15p."
  python3 mindcoach_commands.py check    # Ver respostas pendentes
  python3 mindcoach_commands.py notify "Título" "Mensagem" [info|warn]
  python3 mindcoach_commands.py forex    # Atualiza dados forex no app
"""
import json, os, sys, time, urllib.request
from datetime import datetime
from pathlib import Path

API_BASE = os.environ.get('MINDCOACH_API', 'https://mindcoach-541659260074.us-central1.run.app')
AUTH_FILE = '/tmp/mindcoach_auth.json'  # Local if running on same VM, else API

def _post(endpoint, data):
    """POST JSON to API."""
    url = f"{API_BASE}{endpoint}"
    req = urllib.request.Request(url, 
        data=json.dumps(data).encode(),
        headers={'Content-Type': 'application/json'})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())
    except Exception as e:
        return {'error': str(e)}

def _get(endpoint):
    """GET JSON from API."""
    url = f"{API_BASE}{endpoint}"
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        return json.loads(resp.read())
    except Exception as e:
        return {'error': str(e)}

def send_command(title, body, from_entity="ENTIDADE", expires_minutes=30):
    """
    Envia um impulso/comando para aprovação do usuário.
    Retorna o ID do comando.
    """
    data = {
        'titulo': title,
        'msg': body,
        'from': from_entity,
        'status': 'pending',
        'actions': ['✅ Aprovar', '❌ Recusar'],
        'time': datetime.now().isoformat(),
    }
    if expires_minutes:
        from datetime import timedelta
        data['expires'] = (datetime.now() + timedelta(minutes=expires_minutes)).isoformat()
    
    result = _post('/auth', data)
    if result.get('ok'):
        print(f"[cmd] Impulso enviado: {result['id']} — {title}")
        return result['id']
    else:
        print(f"[cmd] ERRO: {result}", file=sys.stderr)
        return None

def check_responses():
    """Verifica respostas do usuário a comandos pendentes."""
    result = _get('/outbox')
    if result.get('error'):
        print(f"[cmd] ERRO: {result['error']}", file=sys.stderr)
        return []
    responses = result.get('responses', [])
    if responses:
        for r in responses:
            emoji = '✅' if r.get('action') == 'approve' else '❌'
            print(f"  {emoji} {r['id']}: {r.get('action')} — {r.get('titulo','')}")
    else:
        print("  (sem respostas novas)")
    return responses

def send_notification(title, message, tipo='info'):
    """Envia notificação para o app."""
    result = _post('/notify', {
        'titulo': title,
        'msg': message,
        'tipo': tipo,
    })
    if result.get('ok'):
        print(f"[notify] OK: {title}")
    else:
        print(f"[notify] ERRO: {result}")

def update_forex_data(data):
    """Atualiza dados forex no app (via notify)."""
    send_notification(
        '📊 Forex Update',
        f"Balance: ${data.get('balance','?')} | Equity: ${data.get('equity','?')} | "
        f"{data.get('positions',0)} posições | WR: {data.get('wr','?')}",
        'info'
    )

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso:")
        print("  send <titulo> <mensagem>     — Enviar impulso para aprovação")
        print("  check                        — Ver respostas pendentes")
        print("  notify <titulo> <msg> [tipo] — Enviar notificação")
        print("  forex                        — Atualizar dados forex")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'send':
        if len(sys.argv) < 4:
            print("ERRO: send <titulo> <mensagem>")
            sys.exit(1)
        send_command(sys.argv[2], ' '.join(sys.argv[3:]))
    
    elif cmd == 'check':
        check_responses()
    
    elif cmd == 'notify':
        if len(sys.argv) < 4:
            print("ERRO: notify <titulo> <msg> [tipo]")
            sys.exit(1)
        tipo = sys.argv[4] if len(sys.argv) > 4 else 'info'
        send_notification(sys.argv[2], sys.argv[3], tipo)
    
    elif cmd == 'forex':
        # Try to get MT5 status
        try:
            import subprocess
            result = subprocess.run(
                ['python3', str(Path.home()/'.hermes/scripts/hermes_mt5_bridge.py'), 'status'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                update_forex_data(data)
            else:
                send_notification('📊 Forex', 'MT5 offline ou bridge indisponível', 'warn')
        except Exception as e:
            send_notification('📊 Forex', f'Erro: {str(e)[:100]}', 'warn')
    
    else:
        print(f"Comando desconhecido: {cmd}")
        sys.exit(1)
