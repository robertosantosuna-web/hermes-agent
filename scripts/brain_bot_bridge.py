#!/usr/bin/env python3
"""
Brain ↔ Bot Bridge — Conecta o forex_bot_real.py ao cérebro autônomo.
Lê brain_outbox.json para sinais/viés/macro e brain_gateway_inbox.json 
para comandos do usuário. Publica trades executados no brain_inbox.json.
"""
import json, os, time
from pathlib import Path
from datetime import datetime, timezone

HERMES = Path.home() / '.hermes'
BRAIN_OUTBOX = HERMES / 'brain_outbox.json'
BRAIN_INBOX = HERMES / 'brain_inbox.json'
GATEWAY_INBOX = HERMES / 'brain_gateway_inbox.json'
NEURAL_SYNC = HERMES / 'neural_sync.json'
FOREX_DIR = HERMES / 'forex'

def read_brain_signals():
    """Lê o outbox do cérebro e extrai sinais de trading."""
    if not BRAIN_OUTBOX.exists():
        return None
    
    try:
        with open(BRAIN_OUTBOX) as f:
            data = json.load(f)
    except:
        return None
    
    signals = {
        'weekly_bias': {},
        'macro_context': '',
        'alerts': [],
        'timestamp': None
    }
    
    for msg in data.get('messages', []):
        content = msg.get('content', '')
        ts = msg.get('sent_at', '')
        signals['timestamp'] = ts
        
        # Extrair viés semanal
        if 'Viés Semanal' in content or 'weekly_bias' in str(msg.get('topics', [])):
            for line in content.split('\n'):
                if 'BUY' in line.upper() and ('USD' in line.upper() or 'GBP' in line.upper() or 'EUR' in line.upper()):
                    # Parse "USD/JPY: BUY" ou "• USD/JPY: BUY"
                    for pair in ['USD/JPY', 'GBP/USD', 'EUR/USD', 'USDJPY', 'GBPUSD', 'EURUSD']:
                        if pair.replace('/','') in line.replace('/','').replace(' ','').upper():
                            signals['weekly_bias'][pair] = 'BUY' if 'BUY' in line.upper() else 'SELL'
        
        # Extrair contexto macro
        if any(w in content.lower() for w in ['iran', 'fed', 'umich', 'macro', 'warsh']):
            signals['macro_context'] += content[:500] + '\n'
        
        # Extrair alertas
        if 'ALERT' in content or 'alert' in content:
            signals['alerts'].append(content[:200])
    
    return signals if (signals['weekly_bias'] or signals['macro_context']) else None


def read_user_commands():
    """Lê comandos do usuário no gateway inbox."""
    if not GATEWAY_INBOX.exists():
        return []
    
    try:
        with open(GATEWAY_INBOX) as f:
            data = json.load(f)
    except:
        return []
    
    commands = []
    for msg in data.get('messages', []):
        if msg.get('read'):
            continue
        content = msg.get('content', '').lower()
        
        # Comandos de trading
        if any(cmd in content for cmd in ['parar bot', 'stop bot', 'pausar', 'pause']):
            commands.append({'action': 'pause', 'source': msg.get('from', 'user')})
        elif any(cmd in content for cmd in ['iniciar bot', 'start bot', 'reativar', 'resume']):
            commands.append({'action': 'resume', 'source': msg.get('from', 'user')})
        elif any(cmd in content for cmd in ['fechar tudo', 'close all', 'zerar']):
            commands.append({'action': 'close_all', 'source': msg.get('from', 'user')})
        elif 'status' in content or 'status' in content:
            commands.append({'action': 'status', 'source': msg.get('from', 'user')})
    
    return commands


def notify_trade(trade_info):
    """Notifica o cérebro sobre trade executado."""
    msg = {
        'id': f"bot_{int(time.time())}",
        'from': 'forex_bot',
        'content': json.dumps(trade_info),
        'sent_at': datetime.now(timezone.utc).isoformat(),
        'type': 'trade_executed'
    }
    
    # Adicionar ao brain inbox para o gateway processar
    inbox = []
    if BRAIN_INBOX.exists():
        try:
            inbox = json.loads(BRAIN_INBOX.read_text())
        except:
            pass
    
    inbox.append(msg)
    
    # Manter só últimas 50 mensagens
    if len(inbox) > 50:
        inbox = inbox[-50:]
    
    BRAIN_INBOX.write_text(json.dumps(inbox, indent=2, ensure_ascii=False))
    
    # Também escrever no neural_sync para assimilação
    sync_data = {'last_trade': trade_info, 'timestamp': msg['sent_at']}
    NEURAL_SYNC.write_text(json.dumps(sync_data, indent=2, ensure_ascii=False))


def get_weekly_bias():
    """Retorna viés semanal do cérebro (cache 1h)."""
    signals = read_brain_signals()
    if signals and signals['weekly_bias']:
        return signals['weekly_bias']
    return None


def get_macro_context():
    """Retorna contexto macro do cérebro."""
    signals = read_brain_signals()
    if signals and signals['macro_context']:
        return signals['macro_context']
    return ''


if __name__ == '__main__':
    # Teste
    signals = read_brain_signals()
    if signals:
        print("✅ Sinais do cérebro:")
        print(f"  Viés: {signals['weekly_bias']}")
        print(f"  Macro: {signals['macro_context'][:200]}")
        print(f"  Alertas: {len(signals['alerts'])}")
    else:
        print("⚠️  Nenhum sinal ativo no brain_outbox.json")
    
    cmds = read_user_commands()
    if cmds:
        print(f"📋 Comandos pendentes: {len(cmds)}")
        for c in cmds:
            print(f"  → {c}")
