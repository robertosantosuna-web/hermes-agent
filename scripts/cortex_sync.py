#!/usr/bin/env python3
"""
Córtex ↔ Neural KB — Bridge bidirecional.
O Córtex (Hermes Agent) lê o estado da rede neural e escreve
insights gerados durante as sessões de volta para a KB.

Uso pela ENTIDADE em sessão:
  python3 scripts/cortex_sync.py --read     # Lê estado atual da rede
  python3 scripts/cortex_sync.py --write "insight"  # Escreve insight na KB
  python3 scripts/cortex_sync.py --summary  # Resumo de 1 linha
"""
import json, os, sys
from pathlib import Path
from datetime import datetime, timezone

HERMES = Path(os.path.expanduser('~/.hermes'))
KB_PATH = HERMES / 'neural_knowledge_base.json'
CORTEX_LOG = HERMES / 'cortex_synapses.jsonl'

def load_kb():
    if not KB_PATH.exists():
        return None
    try:
        return json.loads(KB_PATH.read_text())
    except:
        return None

def save_kb(kb):
    KB_PATH.write_text(json.dumps(kb, indent=2))

def read_state():
    """Lê estado atual da rede neural para o Córtex."""
    kb = load_kb()
    if not kb:
        return {"status": "no_kb", "message": "Neural KB not initialized yet"}
    
    modules = kb.get('modules', {})
    module_summary = {}
    for name, data in modules.items():
        if data:
            active_keys = [k for k, v in data.items() if v]
            module_summary[name] = {
                'active_fields': len(active_keys),
                'keys': active_keys[:5],
            }
    
    return {
        'status': 'ok',
        'global_state': kb.get('global_state', {}),
        'total_synapses': kb.get('_meta', {}).get('total_synapses', 0),
        'last_consolidation': kb.get('_meta', {}).get('last_consolidation'),
        'modules': module_summary,
        'recent_synapses': kb.get('synapses', [])[-5:],
        'market_regime': kb.get('global_state', {}).get('market_regime', 'unknown'),
        'risk_level': kb.get('global_state', {}).get('risk_level', 'normal'),
        'active_threats': len(kb.get('modules', {}).get('amygdala', {}).get('active_threats', [])),
        'pair_recommendations': kb.get('modules', {}).get('n_accumbens', {}).get('pair_weights', {}),
    }

def write_insight(insight_text, category='general', confidence=0.8):
    """Escreve um insight do Córtex na Neural KB."""
    kb = load_kb()
    if not kb:
        return {"status": "no_kb"}
    
    now = datetime.now(timezone.utc)
    
    # Create synapse from cortex to relevant modules
    synapse = {
        'id': f"syn-cortex-{kb['_meta']['total_synapses'] + 1:04d}",
        'from': 'cortex',
        'to': category,
        'insight': insight_text,
        'confidence': confidence,
        'evidence': {'source': 'hermes_session', 'timestamp': now.isoformat()},
        'timestamp': now.isoformat(),
        'applied': False,
    }
    
    kb['synapses'].append(synapse)
    kb['_meta']['total_synapses'] += 1
    
    # Also log to cortex-specific log
    with open(CORTEX_LOG, 'a') as f:
        f.write(json.dumps({
            'timestamp': now.isoformat(),
            'insight': insight_text,
            'category': category,
            'confidence': confidence,
        }) + '\n')
    
    save_kb(kb)
    
    return {
        'status': 'ok',
        'synapse_id': synapse['id'],
        'total_synapses': kb['_meta']['total_synapses'],
    }

def write_decision(decision_type, details, outcome=None):
    """Registra decisão do Córtex para aprendizado futuro."""
    kb = load_kb()
    if not kb:
        return {"status": "no_kb"}
    
    now = datetime.now(timezone.utc)
    
    entry = {
        'timestamp': now.isoformat(),
        'type': decision_type,
        'details': details,
        'outcome': outcome,
    }
    
    if 'decisions' not in kb:
        kb['decisions'] = []
    kb['decisions'].append(entry)
    
    # Keep last 100 decisions
    if len(kb['decisions']) > 100:
        kb['decisions'] = kb['decisions'][-100:]
    
    save_kb(kb)
    return {'status': 'ok', 'decisions_total': len(kb['decisions'])}

def summary():
    """Resumo de 1 linha para o Córtex."""
    state = read_state()
    if state['status'] != 'ok':
        return "Rede neural não inicializada"
    
    regime = state.get('market_regime', '?')
    synapses = state.get('total_synapses', 0)
    threats = state.get('active_threats', 0)
    risk = state.get('risk_level', '?')
    
    pairs = state.get('pair_recommendations', {})
    active = [p for p, w in pairs.items() if w.get('recommendation') in ('PRIORITY', 'ACTIVE')]
    
    return (
        f"🧠 Rede: {synapses} sinapses | Regime: {regime} | Risco: {risk} | "
        f"Ameaças: {threats} | Pares ativos: {len(active)} ({', '.join(active[:3]) or 'nenhum'})"
    )

# ─── CLI ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if '--read' in sys.argv:
        print(json.dumps(read_state(), indent=2, default=str))
    elif '--write' in sys.argv:
        idx = sys.argv.index('--write')
        insight = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ''
        category = sys.argv[sys.argv.index('--category') + 1] if '--category' in sys.argv else 'general'
        confidence = float(sys.argv[sys.argv.index('--confidence') + 1]) if '--confidence' in sys.argv else 0.8
        print(json.dumps(write_insight(insight, category, confidence), indent=2))
    elif '--summary' in sys.argv:
        print(summary())
    elif '--status' in sys.argv:
        s = read_state()
        print(f"Sinapses: {s.get('total_synapses', 0)}")
        print(f"Regime: {s.get('market_regime', '?')}")
        print(f"Risco: {s.get('risk_level', '?')}")
        print(f"Ameaças: {s.get('active_threats', 0)}")
        pairs = s.get('pair_recommendations', {})
        for p, w in pairs.items():
            print(f"  {p}: WR={w.get('wr')}% {w.get('recommendation')}")
    else:
        print(summary())
