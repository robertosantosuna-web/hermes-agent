#!/usr/bin/env python3
"""
Auto-Trigger Writer — Escreve gatilhos na rede neural automaticamente.
Chamado por: knowledge_bridge, brain_signal_generator, thalamus, trade_tracker.

Uso:
  auto_trigger.py trade WIN EURUSD    → acorda N. Accumbens
  auto_trigger.py fvg new             → acorda Hippocampus  
  auto_trigger.py threat disk_full    → acorda Amygdala
  auto_trigger.py research proposal   → acorda Brain Research
  auto_trigger.py day_end             → acorda Synapse Engine
"""
import sys, json
from pathlib import Path
from datetime import datetime, timezone

HERMES = Path.home() / '.hermes'
TRIGGERS_FILE = HERMES / 'neural_triggers.json'

TRIGGER_MAP = {
    'trade':      'n_accumbens',     # WIN/LOSS → reinforcement
    'fvg':        'hippocampus',     # New FVG data → consolidation
    'threat':     'amygdala',        # System threat → detection
    'research':   'brain_research',  # New findings → development
    'day_end':    'synapse_engine',  # End of day → consolidation
    'week_end':   'synapse_engine',  # End of week → consolidation
}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: auto_trigger.py <tipo> [detalhe]")
        sys.exit(1)
    
    trigger_type = sys.argv[1]
    detail = sys.argv[2] if len(sys.argv) > 2 else ''
    
    module = TRIGGER_MAP.get(trigger_type)
    if not module:
        print(f"Tipo desconhecido: {trigger_type}")
        print(f"Válidos: {list(TRIGGER_MAP.keys())}")
        sys.exit(1)
    
    # Carregar triggers
    data = {'triggers': [], 'history': []}
    if TRIGGERS_FILE.exists():
        try:
            data = json.loads(TRIGGERS_FILE.read_text())
        except:
            pass
    
    # Evitar duplicatas: mesmo módulo + mesma razão nas últimas 4h
    now = datetime.now(timezone.utc)
    for existing in data.get('triggers', []):
        if existing.get('module') == module and existing.get('reason') == detail:
            created = datetime.fromisoformat(existing['created'])
            if (now - created).total_seconds() < 14400:  # 4h
                print(f"⏭️ Trigger duplicado ignorado: {module}/{detail}")
                sys.exit(0)
    
    trigger = {
        'id': f"auto_{int(datetime.now().timestamp())}",
        'module': module,
        'reason': f"[{trigger_type}] {detail}"[:200],
        'urgency': 'high' if trigger_type == 'threat' else 'normal',
        'created': now.isoformat(),
        'status': 'pending'
    }
    data['triggers'].append(trigger)
    
    # Limitar triggers pendentes
    if len(data['triggers']) > 20:
        # Mover mais antigos pro history
        overflow = data['triggers'][:-20]
        data['triggers'] = data['triggers'][-20:]
        for t in overflow:
            t['status'] = 'overflow'
        data.setdefault('history', []).extend(overflow)
    
    TRIGGERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRIGGERS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"⚡ Trigger: {module} ← {detail}")
