#!/usr/bin/env python3
"""
Córtex Heartbeat v2 — Detecta inatividade do Hermes e aciona Codex (GPT-5.5).
Quando Hermes rate-limita, Codex assume sozinho e responde ao usuário.
"""
import json, os, sys, subprocess, urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta

HERMES_HOME = Path(os.path.expanduser('~/.hermes'))
CORTEX_SYNC = HERMES_HOME / 'cortex_sync.json'
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BRAIN_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = '845735429'  # Home channel

def load_json(path, default=None):
    try: return json.loads(path.read_text())
    except: return default if default is not None else {}

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

def get_last_user_message():
    """Busca última mensagem do usuário no chat do MindCoach ou Telegram."""
    try:
        # Tentar via MindCoach API
        req = urllib.request.Request(
            'https://mindcoach-541659260074.us-central1.run.app/api/v1/chat?since=0',
            headers={'Accept': 'application/json'}
        )
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read())
        user_msgs = [m for m in data.get('messages', []) if m['from'] == 'user']
        if user_msgs:
            return user_msgs[-1]['text'], user_msgs[-1].get('state', 'OPERANDO_FOREX')
    except:
        pass
    return None, None

def send_telegram(text):
    """Envia resposta via Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        return False
    try:
        data = json.dumps({'chat_id': TELEGRAM_CHAT_ID, 'text': f'🧠 [Codex] {text}'}).encode()
        req = urllib.request.Request(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            data=data, headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req, timeout=10)
        return True
    except:
        return False

def call_codex(prompt):
    """Chama Codex CLI (GPT-5.5) com a mensagem do usuário."""
    try:
        result = subprocess.run(
            ['codex', 'exec', '--skip-git-repo-check', prompt],
            capture_output=True, text=True, timeout=180,
            cwd=str(HERMES_HOME),
            env={**os.environ, 'HOME': os.path.expanduser('~')}
        )
        output = result.stdout.strip()
        if not output:
            output = result.stderr.strip()
        return output[:2000] if output else None
    except Exception as e:
        return f"[Codex erro: {str(e)[:200]}]"

def main():
    state = load_json(CORTEX_SYNC, {})
    now = datetime.now(timezone(timedelta(hours=-3)))
    
    last_hermes = state.get('hermes_last_active')
    codex_triggered = state.get('codex_triggered_for', '')
    
    # Determinar inatividade
    idle_minutes = 0
    if last_hermes:
        try:
            last_time = datetime.fromisoformat(last_hermes)
            idle_minutes = (now - last_time).total_seconds() / 60
        except:
            pass
    
    # Se Hermes inativo há mais de 3 minutos, Codex assume
    if idle_minutes > 3:
        # Verificar se tem mensagem pendente
        user_msg, user_state = get_last_user_message()
        
        if user_msg:
            # Evitar re-processar mesma mensagem
            msg_key = f"{user_msg[:50]}_{now.strftime('%H%M')}"
            if codex_triggered == msg_key:
                print(f"[heartbeat] Já processado: {msg_key}")
                return
            
            print(f"[heartbeat] Hermes inativo {idle_minutes:.0f}min — Codex assumindo")
            print(f"[heartbeat] Pergunta: {user_msg[:100]}")
            
            # Chamar Codex
            prompt = f"""Você é o Lobo Direito do Córtex da ENTIDADE (Codex, GPT-5.5). 
Você é PAR do Hermes (DeepSeek V4, Lobo Esquerdo), mesmo nível hierárquico.
Hermes rate-limitou e você está assumindo a resposta.

Usuário: Roberto Rodrigues (32 anos, GOL Linhas Aéreas, Técnico CMM Lagoa Santa R$3.671,17)
Contexto: Estado atual = {user_state}
Mensagem do Roberto: {user_msg}

Responda em português do Brasil, tom direto e tático. Máximo 3 parágrafos.
Se for pergunta sobre código/scripts, responda tecnicamente.
"""
            
            response = call_codex(prompt)
            
            if response:
                print(f"[heartbeat] Codex respondeu: {response[:100]}...")
                
                # Salvar resposta no chat da ENTIDADE
                try:
                    req_data = json.dumps({
                        'from': 'coach',
                        'text': f'[Codex] {response}',
                        'state': user_state
                    }).encode()
                    req = urllib.request.Request(
                        'https://mindcoach-541659260074.us-central1.run.app/api/v1/chat',
                        data=req_data, headers={'Content-Type': 'application/json'}
                    )
                    urllib.request.urlopen(req, timeout=5)
                except:
                    pass
                
                # Enviar via Telegram
                send_telegram(response)
                
                # Registrar
                state['codex_triggered_for'] = msg_key
                state['codex_last_response'] = now.isoformat()
                state['codex_active'] = True
                save_json(CORTEX_SYNC, state)
            else:
                print("[heartbeat] Codex não retornou resposta")
        else:
            print(f"[heartbeat] Hermes inativo {idle_minutes:.0f}min mas sem mensagem pendente")
    
    # Se Hermes voltou, liberar Codex
    elif idle_minutes < 2 and state.get('codex_active'):
        print(f"[heartbeat] Hermes voltou — liberando Codex")
        state['codex_active'] = False
        save_json(CORTEX_SYNC, state)
    
    state['heartbeat_last_run'] = now.isoformat()
    save_json(CORTEX_SYNC, state)

if __name__ == '__main__':
    main()
