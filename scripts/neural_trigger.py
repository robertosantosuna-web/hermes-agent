#!/usr/bin/env python3
"""
Neural Trigger Engine — Sistema de gatilhos da rede neural.
Substitui cron jobs fixos por ativação sob demanda.

Arquitetura:
  Evento detectado → write_trigger() → triggers.json
  Executive (*/5 min) → check_triggers() → dispara módulo → mark_done()

Zero tokens. Apenas I/O de arquivos e subprocess.
"""
import json, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

HERMES = Path.home() / '.hermes'
TRIGGERS_FILE = HERMES / 'neural_triggers.json'
SCRIPTS = HERMES / 'scripts'

# Módulos que respondem a triggers
TRIGGERABLE = {
    'amygdala':       {'script': 'amygdala.py',       'desc': 'Threat detection'},
    'n_accumbens':    {'script': 'n_accumbens.py',    'desc': 'Reinforcement learning'},
    'hippocampus':    {'script': 'hippocampus.py',    'desc': 'Pattern consolidation'},
    'brain_research': {'script': 'brain_research.py', 'desc': 'Auto-development'},
    'synapse_engine': {'script': 'synapse_engine.py', 'desc': 'Neural consolidation'},
}

def _now():
    return datetime.now(timezone.utc).isoformat()

def _load():
    if TRIGGERS_FILE.exists():
        try:
            return json.loads(TRIGGERS_FILE.read_text())
        except:
            pass
    return {'triggers': [], 'history': []}

def _save(data):
    TRIGGERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRIGGERS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))

def write_trigger(module, reason, urgency='normal'):
    """Escreve um gatilho para acordar um módulo."""
    if module not in TRIGGERABLE:
        return {'error': f'unknown module: {module}'}
    
    data = _load()
    trigger = {
        'id': f"trig_{int(datetime.now().timestamp())}",
        'module': module,
        'reason': reason[:200],
        'urgency': urgency,
        'created': _now(),
        'status': 'pending'
    }
    data['triggers'].append(trigger)
    _save(data)
    return {'status': 'ok', 'id': trigger['id']}

def check_triggers():
    """Executive chama: verifica gatilhos pendentes e dispara módulos."""
    data = _load()
    pending = [t for t in data.get('triggers', []) if t.get('status') == 'pending']
    
    results = []
    for trigger in pending:
        module = trigger['module']
        if module not in TRIGGERABLE:
            trigger['status'] = 'error'
            trigger['error'] = f'unknown module: {module}'
            continue
        
        script = TRIGGERABLE[module]['script']
        script_path = SCRIPTS / script
        
        if not script_path.exists():
            trigger['status'] = 'error'
            trigger['error'] = f'script not found: {script}'
            continue
        
        try:
            r = subprocess.run(
                ['python3', str(script_path)],
                capture_output=True, text=True, timeout=30
            )
            trigger['status'] = 'done' if r.returncode == 0 else 'error'
            trigger['output'] = r.stdout[:500]
            trigger['error'] = r.stderr[:200] if r.stderr else None
            trigger['processed_at'] = _now()
            results.append({'module': module, 'status': trigger['status']})
        except Exception as e:
            trigger['status'] = 'error'
            trigger['error'] = str(e)[:200]
            results.append({'module': module, 'status': 'error', 'error': str(e)[:100]})
    
    # Mover processados pro history
    done = [t for t in data['triggers'] if t.get('status') != 'pending']
    for t in done:
        data['history'].append(t)
    data['triggers'] = [t for t in data['triggers'] if t.get('status') == 'pending']
    
    # Limitar history
    if len(data['history']) > 500:
        data['history'] = data['history'][-500:]
    
    _save(data)
    return {'processed': len(done), 'results': results}

def stats():
    """Status do trigger engine."""
    data = _load()
    pending = [t for t in data.get('triggers', []) if t.get('status') == 'pending']
    return {
        'pending': len(pending),
        'total_history': len(data.get('history', [])),
        'modules': list(TRIGGERABLE.keys()),
        'pending_modules': list(set(t['module'] for t in pending))
    }

if __name__ == '__main__':
    if len(sys.argv) < 2:
        s = stats()
        print(f"⚡ Neural Trigger Engine")
        print(f"   Pendentes: {s['pending']}")
        print(f"   Histórico: {s['total_history']}")
        print(f"   Módulos: {', '.join(s['modules'])}")
    elif sys.argv[1] == 'check':
        r = check_triggers()
        print(json.dumps(r, indent=2))
    elif sys.argv[1] == 'trigger' and len(sys.argv) >= 4:
        r = write_trigger(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else 'normal')
        print(json.dumps(r, indent=2))
    elif sys.argv[1] == 'stats':
        print(json.dumps(stats(), indent=2))
