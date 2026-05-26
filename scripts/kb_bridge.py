"""
KB Bridge — Helper para módulos lerem/escreverem na Neural Knowledge Base.
Importe em qualquer script: from kb_bridge import write, read, query
"""
import json, os, sys
from pathlib import Path

# Add parent to path so scripts can import this
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from neural_kb import module_write, module_read, get_global_state, add_synapse, query as kb_query
except ImportError:
    # Fallback: direct file access
    HERMES = Path(os.path.expanduser('~/.hermes'))
    KB_PATH = HERMES / 'neural_knowledge_base.json'
    
    def _load():
        if not KB_PATH.exists():
            return {}
        try:
            return json.loads(KB_PATH.read_text())
        except:
            return {}
    
    def _save(kb):
        KB_PATH.write_text(json.dumps(kb, indent=2))
    
    def module_write(name, data, merge=True):
        kb = _load()
        if name not in kb.get('modules', {}):
            if 'modules' not in kb:
                kb['modules'] = {}
            kb['modules'][name] = {}
        if merge:
            kb['modules'][name].update(data)
        else:
            kb['modules'][name] = data
        _save(kb)
    
    def module_read(name, key=None):
        kb = _load()
        mod = kb.get('modules', {}).get(name, {})
        return mod.get(key) if key else mod
    
    def get_global_state():
        kb = _load()
        return kb.get('global_state', {})
    
    def add_synapse(frm, to, insight, confidence, evidence=None):
        kb = _load()
        syn = {
            'id': f"syn-{kb.get('_meta', {}).get('total_synapses', 0) + 1:04d}",
            'from': frm, 'to': to, 'insight': insight,
            'confidence': confidence, 'evidence': evidence or {},
            'timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
            'applied': False,
        }
        if 'synapses' not in kb:
            kb['synapses'] = []
        kb['synapses'].append(syn)
        if '_meta' not in kb:
            kb['_meta'] = {}
        kb['_meta']['total_synapses'] = kb['_meta'].get('total_synapses', 0) + 1
        _save(kb)
        return syn
    
    def kb_query(qtype):
        kb = _load()
        if qtype == 'risk_level':
            threats = kb.get('modules', {}).get('amygdala', {}).get('active_threats', [])
            return {'threats': len(threats)}
        elif qtype == 'market_regime':
            return kb.get('global_state', {}).get('market_regime', 'unknown')
        return {}

# Public API
write = module_write
read = module_read
global_state = get_global_state
synapse = add_synapse
query = kb_query
