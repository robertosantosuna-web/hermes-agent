#!/usr/bin/env python3
"""
Neural Triggers — Dispara módulos cerebrais baseado em eventos da rede neural.
Substitui ciclos cron fixos por execução reativa a mudanças no conhecimento.
"""
import json, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

HERMES = Path.home() / '.hermes'
SCRIPTS = HERMES / 'scripts'
KB_FILE = HERMES / 'neural_knowledge_base.json'
CONTEXT_FILE = HERMES / 'brain_context.json'
STATE_FILE = HERMES / 'neural_trigger_state.json'

def load_state():
    if STATE_FILE.exists():
        try: return json.loads(STATE_FILE.read_text())
        except: pass
    return {
        'last_synapse_count': 0,
        'last_kb_update': None,
        'last_threat_level': 'normal',
        'last_market_regime': None,
        'modules_triggered': {}
    }

def save_state(s):
    STATE_FILE.write_text(json.dumps(s, indent=2, ensure_ascii=False))

def trigger_module(module_name, script_name, reason):
    """Dispara um módulo cerebral se necessário."""
    print(f"⚡ [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {module_name}: {reason}")
    try:
        r = subprocess.run(
            [sys.executable, str(SCRIPTS / script_name)],
            capture_output=True, text=True, timeout=30
        )
        if r.stdout.strip():
            print(f"   {r.stdout.strip()[:200]}")
        return True
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def check_triggers():
    """Verifica eventos na rede neural e dispara módulos reativos."""
    state = load_state()
    triggered = []
    
    # 1. Verificar Neural KB — novas sinapses?
    if KB_FILE.exists():
        try:
            kb = json.loads(KB_FILE.read_text())
            synapses = kb.get('synapses', [])
            current_count = len(synapses)
            
            if current_count > state['last_synapse_count']:
                new_syns = current_count - state['last_synapse_count']
                # Novas sinapses → disparar N. Accumbens (reforço) + Hippocampus (consolidação)
                trigger_module('N. Accumbens', 'n_accumbens.py', f'{new_syns} novas sinapses')
                trigger_module('Hippocampus', 'hippocampus.py', f'{new_syns} novas sinapses')
                triggered.extend(['n_accumbens', 'hippocampus'])
                state['last_synapse_count'] = current_count
        except: pass
    
    # 2. Verificar Brain Context — mudança de regime de mercado?
    if CONTEXT_FILE.exists():
        try:
            ctx = json.loads(CONTEXT_FILE.read_text())
            current_state = ctx.get('current_state', {})
            regime = current_state.get('market_regime', current_state.get('status'))
            
            if regime != state.get('last_market_regime'):
                # Mudança de regime → disparar Brain Research
                trigger_module('Brain Research', 'brain_research.py', f'regime: {regime}')
                triggered.append('brain_research')
                state['last_market_regime'] = regime
            
            # Verificar módulos com status offline → disparar Executive
            mods = ctx.get('modules_status', {})
            offline = [k for k,v in mods.items() if isinstance(v, dict) and v.get('status') == 'offline']
            if offline:
                trigger_module('Executive', 'executive/brain.py', f'módulos offline: {offline}')
                triggered.append('executive')
        except: pass
    
    # 3. Brain Gateway inbox não lido → disparar Gateway
    gw_inbox = HERMES / 'brain_gateway_inbox.json'
    if gw_inbox.exists():
        try:
            inbox = json.loads(gw_inbox.read_text())
            unread = [m for m in inbox.get('messages', []) if not m.get('read')]
            if unread:
                trigger_module('Brain Gateway', 'brain_gateway.py process', f'{len(unread)} msgs não lidas')
                triggered.append('gateway')
        except: pass
    
    # 4. Knowledge Bridge — novos itens?
    kb_file = HERMES / 'knowledge_bridge_log.json'
    if kb_file.exists():
        try:
            kb_log = json.loads(kb_file.read_text())
            last_entry = kb_log[-1] if kb_log else {}
            last_ts = last_entry.get('timestamp', '')
            if last_ts != state.get('last_kb_update'):
                trigger_module('Neural Assimilate', 'neural_assimilate.py', 'novo conhecimento')
                triggered.append('neural_assimilate')
                state['last_kb_update'] = last_ts
        except: pass
    
    # 5. Sempre rodar Amygdala + Cerebellum (segurança contínua)
    trigger_module('Amygdala', 'amygdala.py', 'verificação de segurança')
    trigger_module('Cerebellum', 'cerebellum.py', 'validação de comandos')
    triggered.extend(['amygdala', 'cerebellum'])
    
    state['modules_triggered'][datetime.now(timezone.utc).isoformat()] = triggered
    save_state(state)
    
    return triggered

if __name__ == '__main__':
    triggered = check_triggers()
    print(f"\n✅ {len(triggered)} módulos disparados: {triggered}")
