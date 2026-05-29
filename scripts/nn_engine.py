#!/usr/bin/env python3
"""
NN ENGINE — Feed-Forward Diário + Backpropagation.
Ativa as 3 redes neurais (brain, agent, shared) com dados frescos.
Cross-pollination entre redes. Consolida sinapses.

Roda 1x/dia às 02:00 BRT.
Zero tokens (no_agent, script puro).
"""
import json, os, sys
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

H = Path(os.path.expanduser('~/.hermes'))
NEURAL_DIR = H / 'neural'
BRAIN_FILE = NEURAL_DIR / 'nn_brain.json'
AGENT_FILE = NEURAL_DIR / 'nn_agent.json'
SHARED_FILE = NEURAL_DIR / 'nn_shared.json'
TRADE_LOG = H / 'forex' / 'trade_log.json'
KB_FILE = H / 'neural_knowledge_base.json'
OUT_DIR = H / 'cron' / 'output' / 'nn_engine'
OUT_DIR.mkdir(parents=True, exist_ok=True)

def load(path):
    if path.exists():
        try: return json.loads(path.read_text())
        except: pass
    return None

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))

def feed_forward(network, inputs):
    """Ativa neurônios com base em inputs frescos. Sem inputs = ativação basal."""
    neurons = network.get('neurons', {})
    if not isinstance(neurons, dict):
        return 0
    activated = 0
    
    # Normalize all strengths to float (some may be str from prior broken runs)
    for nid, neuron in neurons.items():
        try:
            neuron['strength'] = float(neuron.get('strength', 0.3))
        except (ValueError, TypeError):
            neuron['strength'] = 0.3
    
    # Basal activation: if no meaningful inputs, reinforce all neurons with strength >= 0.3
    meaningful = any(
        isinstance(v, list) and len(v) > 0 
        for v in inputs.values()
    ) if inputs else False
    
    if not inputs or not meaningful:
        for nid, neuron in neurons.items():
            if neuron.get('strength', 0) >= 0.3:
                neuron['strength'] = min(1.0, neuron['strength'] + 0.05)
                neuron['activations'] = int(neuron.get('activations', 0)) + 1
                activated += 1
        return activated
    
    for nid, neuron in neurons.items():
        concept = neuron.get('concept', '').lower()
        domain = neuron.get('domain', '').lower()
        for inp_key, inp_val in inputs.items():
            key_lower = str(inp_key).lower()
            # Match by concept, domain, or input key fragments
            if key_lower in concept or key_lower in domain:
                neuron['strength'] = min(1.0, neuron['strength'] + 0.15)
                neuron['activations'] = int(neuron.get('activations', 0)) + 1
                activated += 1
                break
            if isinstance(inp_val, list):
                for v in inp_val:
                    v_str = str(v).lower()
                    if v_str in concept or v_str in domain:
                        neuron['strength'] = min(1.0, neuron['strength'] + 0.15)
                        neuron['activations'] = int(neuron.get('activations', 0)) + 1
                        activated += 1
                        break
    return activated

def cross_pollinate(source, target, source_name):
    """Compartilha neurônios entre redes."""
    s_neurons = source.get('neurons', {})
    t_neurons = target.get('neurons', {})
    if not isinstance(s_neurons, dict) or not isinstance(t_neurons, dict):
        return 0
    new_synapses = 0
    for nid, neuron in s_neurons.items():
        domain = neuron.get('domain', '')
        concept = neuron.get('concept', '')
        # Só copia neurônios com força > 0.5 que não existem na target
        strength = float(neuron.get('strength', 0))
        if strength > 0.5:
            exists = any(
                n.get('concept', '') == concept 
                for n in t_neurons.values()
            )
            if not exists:
                new_id = f"cp_{source_name}_{nid}"
                t_neurons[new_id] = {
                    'concept': concept,
                    'domain': domain,
                    'layer': 'cross_pollinated',
                    'created': datetime.now(timezone.utc).isoformat(),
                    'strength': round(strength * 0.7, 4),
                    'activations': 0,
                    'source': source_name,
                }
                new_synapses += 1
    return new_synapses

def backprop(network, outcomes):
    """Ajusta pesos baseado em resultados de trades."""
    neurons = network.get('neurons', {})
    if not isinstance(neurons, dict):
        return 0
    adjusted = 0
    for nid, neuron in neurons.items():
        concept = neuron.get('concept', '').lower()
        try:
            strength = float(neuron.get('strength', 0.3))
        except (ValueError, TypeError):
            strength = 0.3
        for pair, score in outcomes.items():
            pair_lower = pair.lower().replace('/', '').replace('-', '')
            if pair_lower in concept.replace('/', '').replace('-', ''):
                if score > 0:  # WIN → reforçar
                    neuron['strength'] = min(1.0, strength + 0.1)
                else:  # LOSS → enfraquecer
                    neuron['strength'] = max(0.1, strength - 0.05)
                adjusted += 1
                break
    return adjusted

def compute_activity(network):
    neurons = network.get('neurons', {})
    if not isinstance(neurons, dict):
        return {'active_neurons': 0, 'total_neurons': 0, 'total_synapses': 0, 'activity_pct': 0}
    total = len(neurons)
    def _get_strength(n):
        try: return float(n.get('strength', 0))
        except: return 0.3
    active = sum(1 for n in neurons.values() if _get_strength(n) > 0.3)
    syns = network.get('synapses', [])
    total_syns = len(syns) if isinstance(syns, list) else len(syns) if isinstance(syns, dict) else 0
    return {
        'active_neurons': active,
        'total_neurons': total,
        'total_synapses': total_syns,
        'activity_pct': round(active / max(total, 1) * 100, 1),
    }

def main():
    output = []
    output.append(f"# 🧬 NN Engine — Feed-Forward {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    brain = load(BRAIN_FILE) or {'neurons': {}, 'synapses': []}
    agent = load(AGENT_FILE) or {'neurons': {}, 'synapses': []}
    shared = load(SHARED_FILE) or {'neurons': {}, 'synapses': []}
    
    # Coletar inputs frescos
    inputs = {}
    kb = load(KB_FILE)
    if kb:
        domains = kb.get('domains', {})
        inputs['kb_domains'] = list(domains.keys())
    
    tlog = load(TRADE_LOG)
    if tlog:
        trades = tlog.get('trades', [])
        inputs['recent_trades'] = str(len(trades))
        pairs_traded = set(t.get('pair', '').replace('_KZ', '') for t in trades)
        inputs['pairs_active'] = list(pairs_traded)
    
    # Feed-forward
    a_brain = feed_forward(brain, inputs)
    a_agent = feed_forward(agent, inputs)
    a_shared = feed_forward(shared, inputs)
    output.append(f"\n## Feed-Forward\n- 🧠 Brain: {a_brain} | 🤖 Agent: {a_agent} | 🔗 Shared: {a_shared}")
    
    # Cross-pollination
    cp1 = cross_pollinate(brain, agent, 'brain')
    cp2 = cross_pollinate(agent, brain, 'agent')
    cp3 = cross_pollinate(brain, shared, 'brain')
    cp4 = cross_pollinate(agent, shared, 'agent')
    output.append(f"\n## Cross-Pollination\n- Brain→Agent: +{cp1} | Agent→Brain: +{cp2} | →Shared: +{cp3+cp4}")
    
    # Backpropagation
    outcomes = {}
    if tlog:
        for t in tlog.get('trades', []):
            pair = t.get('pair', '').replace('_KZ', '')
            result = 1 if t.get('result') == 'WIN' else -1
            outcomes[pair] = outcomes.get(pair, 0) + result
    
    bp_total = sum(backprop(net, outcomes) for net in [brain, agent, shared])
    output.append(f"\n## Backpropagation\n- {bp_total} neurônios ajustados")
    
    # Atividade
    for name, net in [('Brain', brain), ('Agent', agent), ('Shared', shared)]:
        act = compute_activity(net)
        output.append(f"- {name}: {act['activity_pct']}% ({act['active_neurons']}/{act['total_neurons']} N, {act['total_synapses']} S)")
    
    # Salvar
    now_ts = datetime.now(timezone.utc).isoformat()
    brain['last_feed_forward'] = now_ts
    agent['last_feed_forward'] = now_ts
    shared['last_feed_forward'] = now_ts
    save(BRAIN_FILE, brain)
    save(AGENT_FILE, agent)
    save(SHARED_FILE, shared)
    
    out_file = OUT_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.md"
    out_file.write_text('\n'.join(output))
    print('\n'.join(output))

if __name__ == '__main__':
    main()
