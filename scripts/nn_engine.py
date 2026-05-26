#!/usr/bin/env python3
"""
NN Engine — 3 Redes Neurais (Cérebro, Agente, Compartilhada)
=============================================================
Arquitetura de aprendizado contínuo com backpropagation, cross-pollination,
pruning e consolidação. Cada rede é um grafo de neurônios (conceitos) + 
sinapses (conexões com pesos e métricas).

Uso:
  nn_engine.py feed_forward  <network>           # Propaga conhecimento
  nn_engine.py backprop      <network>           # Corrige pesos por erro
  nn_engine.py cross_pollinate                    # Transfere sinapses entre redes
  nn_engine.py consolidate   <network>           # Mescla sinapses similares
  nn_engine.py prune         <network>           # Remove sinapses fracas/falhas
  nn_engine.py status                            # Status das 3 redes
  nn_engine.py add_neuron    <network> <concept> # Adiciona neurônio
  nn_engine.py add_synapse   <source> <target> <weight> <network> # Conecta
  nn_engine.py learn         <network> <fact>    # Aprende fato novo
  nn_engine.py absorb                               # Absorve knowledge bridge → redes
"""

import json
import os
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
NN_DIR = HERMES_HOME / "neural"
NN_BRAIN = NN_DIR / "nn_brain.json"
NN_AGENT = NN_DIR / "nn_agent.json"
NN_SHARED = NN_DIR / "nn_shared.json"
BRIDGE_FILE = HERMES_HOME / "forex" / "knowledge_bridge.json"
AGENT_MEMORY = HERMES_HOME / "forex" / "agent_context.json"

DOMAINS = [
    "forex_trading",
    "freelancing",
    "automation",
    "research",
    "mental_health",
    "system_health",
    "communication",
    "learning",
    "error_handling",
    "pipeline_optimization",
]

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def load_json(path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def init_network(name, description):
    """Initialize a neural network structure."""
    return {
        "name": name,
        "description": description,
        "version": "1.0.0",
        "created": now_iso(),
        "neurons": {},           # {neuron_id: {concept, domain, layer, created, strength}}
        "synapses": {},          # {synapse_id: {source, target, weight, confidence, created, hits, misses, last_used}}
        "layers": {              # Camadas por domínio
            d: {"neurons": [], "synapse_count": 0}
            for d in DOMAINS
        },
        "history": [],           # [{timestamp, action, detail}]
        "anti_patterns": [],     # Padrões que falharam
        "error_corrections": [], # Correções aplicadas via backprop
        "metrics": {
            "total_neurons": 0,
            "total_synapses": 0,
            "avg_weight": 0.0,
            "avg_confidence": 0.0,
            "assertiveness": 0.0,  # hits / (hits + misses)
            "cross_pollinations": 0,
            "prunes": 0,
            "last_consolidation": None,
            "last_backprop": None,
        }
    }

def neuron_id(concept):
    """Hash concept to create neuron ID."""
    return f"n{hashlib.md5(concept.encode()).hexdigest()[:8]}"

def synapse_id(source, target):
    """Create synapse ID from source+target."""
    return f"s{hashlib.md5(f'{source}->{target}'.encode()).hexdigest()[:8]}"

def get_network(name):
    paths = {"brain": NN_BRAIN, "agent": NN_AGENT, "shared": NN_SHARED}
    path = paths.get(name)
    if not path or not path.exists():
        print(f"❌ Rede '{name}' não encontrada")
        return None
    return load_json(path)

def save_network(name, net):
    paths = {"brain": NN_BRAIN, "agent": NN_AGENT, "shared": NN_SHARED}
    save_json(paths[name], net)

# ═══════════════════════════════════════════════════════════════
# COMANDOS
# ═══════════════════════════════════════════════════════════════

def cmd_init():
    """Initialize all 3 networks."""
    NN_DIR.mkdir(parents=True, exist_ok=True)
    
    networks = {
        "brain": ("NN-Brain", "Rede Neural do Cérebro — forex, trading, análise técnica, padrões, sinais"),
        "agent": ("NN-Agent", "Rede Neural do Agente — automação, freelas, comunicação, pipelines, correções"),
        "shared": ("NN-Shared", "Rede Neural Compartilhada — sinapses cruzadas, conhecimento híbrido, meta-aprendizado"),
    }
    
    for name, (full_name, desc) in networks.items():
        paths = {"brain": NN_BRAIN, "agent": NN_AGENT, "shared": NN_SHARED}
        path = paths[name]
        
        if path.exists():
            print(f"⚠️  {full_name} já existe — pulando")
        else:
            net = init_network(full_name, desc)
            save_json(path, net)
            print(f"✅ {full_name} inicializada")
    
    print("3 redes neurais prontas.")

def cmd_add_neuron(network, concept, domain="learning", layer=1):
    """Add a neuron (concept) to a network."""
    net = get_network(network)
    if not net:
        return
    
    nid = neuron_id(concept)
    if nid in net["neurons"]:
        print(f"⚠️  Neurônio '{concept}' já existe em {network} (id={nid})")
        return
    
    net["neurons"][nid] = {
        "concept": concept,
        "domain": domain,
        "layer": layer,
        "created": now_iso(),
        "strength": 1.0,
        "activations": 0,
    }
    
    if domain in net["layers"]:
        net["layers"][domain]["neurons"].append(nid)
    
    net["metrics"]["total_neurons"] = len(net["neurons"])
    net["history"].append({"timestamp": now_iso(), "action": "add_neuron", "detail": f"{nid}: {concept}"})
    save_network(network, net)
    print(f"✅ Neurônio '{concept}' (id={nid}) adicionado à {net['name']}")

def cmd_add_synapse(source_concept, target_concept, weight, network, confidence=0.5):
    """Connect two concepts with a weighted synapse."""
    net = get_network(network)
    if not net:
        return
    
    # Ensure neurons exist
    src_id = neuron_id(source_concept)
    tgt_id = neuron_id(target_concept)
    
    for nid, concept, domain in [(src_id, source_concept, "learning"), (tgt_id, target_concept, "learning")]:
        if nid not in net["neurons"]:
            net["neurons"][nid] = {
                "concept": concept,
                "domain": domain,
                "layer": 1,
                "created": now_iso(),
                "strength": 1.0,
                "activations": 0,
            }
            if domain in net["layers"]:
                net["layers"][domain]["neurons"].append(nid)
    
    sid = synapse_id(src_id, tgt_id)
    weight = float(weight)
    
    if sid in net["synapses"]:
        # Update existing
        old_weight = net["synapses"][sid]["weight"]
        net["synapses"][sid]["weight"] = (old_weight + weight) / 2  # Moving average
        net["synapses"][sid]["confidence"] = min(1.0, net["synapses"][sid]["confidence"] + 0.05)
        net["synapses"][sid]["last_used"] = now_iso()
        print(f"🔄 Sinapse {sid} atualizada: weight {old_weight:.2f} → {net['synapses'][sid]['weight']:.2f}")
    else:
        net["synapses"][sid] = {
            "source": src_id,
            "target": tgt_id,
            "source_concept": source_concept,
            "target_concept": target_concept,
            "weight": weight,
            "confidence": confidence,
            "created": now_iso(),
            "last_used": now_iso(),
            "hits": 0,
            "misses": 0,
        }
        
        # Update layer counts
        src_neuron = net["neurons"][src_id]
        if src_neuron["domain"] in net["layers"]:
            net["layers"][src_neuron["domain"]]["synapse_count"] += 1
        
        print(f"✅ Sinapse {sid}: '{source_concept}' → '{target_concept}' (w={weight:.2f}) criada em {network}")
    
    net["metrics"]["total_neurons"] = len(net["neurons"])
    net["metrics"]["total_synapses"] = len(net["synapses"])
    net["history"].append({"timestamp": now_iso(), "action": "add_synapse", "detail": f"{sid}: {source_concept}→{target_concept} w={weight}"})
    save_network(network, net)

def cmd_learn(network, fact):
    """Learn a new fact: adds neuron + auto-detects domain + connects to related concepts."""
    net = get_network(network)
    if not net:
        return
    
    # Detect domain from keywords
    domain_keywords = {
        "forex_trading": ["forex", "trade", "pip", "candle", "FVG", "CHoCH", "order flow", "wyckoff", "ICT", "MT5", "tradingview", "par", "USD", "EUR", "GBP"],
        "freelancing": ["freela", "99", "fiverr", "cliente", "proposta", "martin", "clínica", "lead"],
        "automation": ["CDP", "ydotool", "daemon", "browser", "click", "type", "DOM", "React", "Cloudflare", "kernel"],
        "research": ["fonte", "RSS", "YouTube", "artigo", "pesquisa", "estudo"],
        "error_handling": ["falhou", "falha", "erro", "loop", "preso", "ATR", "bug", "corrigir"],
        "pipeline_optimization": ["pipeline", "fluxo", "otimiz", "eficiência", "tokens", "assertividade"],
    }
    
    domain = "learning"
    for d, keywords in domain_keywords.items():
        if any(kw.lower() in fact.lower() for kw in keywords):
            domain = d
            break
    
    # Add neuron
    nid = neuron_id(fact)
    if nid not in net["neurons"]:
        net["neurons"][nid] = {
            "concept": fact,
            "domain": domain,
            "layer": 1,
            "created": now_iso(),
            "strength": 1.0,
            "activations": 1,
        }
        if domain in net["layers"]:
            net["layers"][domain]["neurons"].append(nid)
    
    # Find related concepts and auto-connect
    connections = 0
    fact_lower = fact.lower()
    for other_id, other in net["neurons"].items():
        if other_id == nid:
            continue
        other_lower = other["concept"].lower()
        # Simple word overlap
        fact_words = set(fact_lower.split())
        other_words = set(other_lower.split())
        overlap = fact_words & other_words - {"de", "do", "da", "em", "no", "na", "o", "a", "e", "que", "um", "uma"}
        if len(overlap) >= 2:
            sid = synapse_id(nid, other_id)
            if sid not in net["synapses"]:
                net["synapses"][sid] = {
                    "source": nid,
                    "target": other_id,
                    "source_concept": fact,
                    "target_concept": other["concept"],
                    "weight": min(1.0, len(overlap) * 0.2),
                    "confidence": 0.3 + len(overlap) * 0.1,
                    "created": now_iso(),
                    "last_used": now_iso(),
                    "hits": 0,
                    "misses": 0,
                }
                connections += 1
    
    net["metrics"]["total_neurons"] = len(net["neurons"])
    net["metrics"]["total_synapses"] = len(net["synapses"])
    net["history"].append({"timestamp": now_iso(), "action": "learn", "detail": f"Fato aprendido: {fact[:80]}... (domain={domain}, connections={connections})"})
    save_network(network, net)
    print(f"✅ {net['name']}: fato aprendido (domain={domain}, auto-connections={connections})")

def cmd_backprop(network):
    """Backpropagation: corrige pesos de sinapses baseado em erros registrados."""
    net = get_network(network)
    if not net:
        return
    
    corrections = 0
    for sid, syn in list(net["synapses"].items()):
        total = syn["hits"] + syn["misses"]
        if total == 0:
            continue
        
        hit_rate = syn["hits"] / total
        if hit_rate < 0.3:
            # Sinapse está errando muito — reduzir peso
            old_w = syn["weight"]
            syn["weight"] = max(0.05, syn["weight"] * 0.5)
            syn["confidence"] = max(0.1, syn["confidence"] - 0.2)
            net["error_corrections"].append({
                "timestamp": now_iso(),
                "synapse": sid,
                "old_weight": old_w,
                "new_weight": syn["weight"],
                "reason": f"hit_rate={hit_rate:.2f} (hits={syn['hits']}, misses={syn['misses']})"
            })
            corrections += 1
        elif hit_rate > 0.8:
            # Sinapse está acertando — reforçar
            syn["weight"] = min(1.0, syn["weight"] * 1.1)
            syn["confidence"] = min(1.0, syn["confidence"] + 0.05)
    
    net["metrics"]["last_backprop"] = now_iso()
    net["history"].append({"timestamp": now_iso(), "action": "backprop", "detail": f"{corrections} sinapses corrigidas"})
    
    # Recalculate metrics
    weights = [s["weight"] for s in net["synapses"].values()]
    confs = [s["confidence"] for s in net["synapses"].values()]
    hits_sum = sum(s["hits"] for s in net["synapses"].values())
    misses_sum = sum(s["misses"] for s in net["synapses"].values())
    
    net["metrics"]["avg_weight"] = sum(weights) / len(weights) if weights else 0
    net["metrics"]["avg_confidence"] = sum(confs) / len(confs) if confs else 0
    net["metrics"]["assertiveness"] = hits_sum / (hits_sum + misses_sum) if (hits_sum + misses_sum) > 0 else 0
    
    save_network(network, net)
    print(f"✅ Backprop em {net['name']}: {corrections} correções | assertividade={net['metrics']['assertiveness']:.1%}")

def cmd_prune(network):
    """Prune: remove sinapses com weight < 0.1 ou confidence < 0.1."""
    net = get_network(network)
    if not net:
        return
    
    removed = 0
    for sid, syn in list(net["synapses"].items()):
        if syn["weight"] < 0.1 or syn["confidence"] < 0.1:
            # Very weak — remove
            del net["synapses"][sid]
            removed += 1
        elif syn["weight"] < 0.2 and syn["confidence"] < 0.3:
            # Weak and low confidence — remove
            del net["synapses"][sid]
            removed += 1
    
    # Also remove neurons with 0 synapses
    connected = set()
    for syn in net["synapses"].values():
        connected.add(syn["source"])
        connected.add(syn["target"])
    
    orphan_removed = 0
    for nid in list(net["neurons"].keys()):
        if nid not in connected and len(net["neurons"]) > 10:  # Don't prune too aggressively
            del net["neurons"][nid]
            orphan_removed += 1
    
    net["metrics"]["total_neurons"] = len(net["neurons"])
    net["metrics"]["total_synapses"] = len(net["synapses"])
    net["metrics"]["prunes"] += removed + orphan_removed
    net["history"].append({"timestamp": now_iso(), "action": "prune", "detail": f"{removed} sinapses + {orphan_removed} neurônios removidos"})
    save_network(network, net)
    print(f"✅ Prune em {net['name']}: {removed} sinapses + {orphan_removed} neurônios removidos")

def cmd_consolidate(network):
    """Consolidate: merge sinapses muito similares."""
    net = get_network(network)
    if not net:
        return
    
    merged = 0
    syns = list(net["synapses"].items())
    
    for i, (sid1, syn1) in enumerate(syns):
        for sid2, syn2 in syns[i+1:]:
            if sid2 not in net["synapses"]:
                continue
            # Same direction similarity
            if syn1["source"] == syn2["source"] and syn1["target"] == syn2["target"]:
                # Merge: average weights, take max confidence
                syn1["weight"] = (syn1["weight"] + syn2["weight"]) / 2
                syn1["confidence"] = max(syn1["confidence"], syn2["confidence"])
                syn1["hits"] += syn2["hits"]
                syn1["misses"] += syn2["misses"]
                syn1["last_used"] = max(syn1["last_used"], syn2["last_used"])
                del net["synapses"][sid2]
                merged += 1
    
    net["metrics"]["total_synapses"] = len(net["synapses"])
    net["metrics"]["last_consolidation"] = now_iso()
    net["history"].append({"timestamp": now_iso(), "action": "consolidate", "detail": f"{merged} sinapses mescladas"})
    save_network(network, net)
    print(f"✅ Consolidate em {net['name']}: {merged} sinapses mescladas")

def cmd_cross_pollinate():
    """Cross-pollinate: transfere sinapses de alta confiança entre redes."""
    brain = get_network("brain")
    agent = get_network("agent")
    shared = get_network("shared")
    
    if not all([brain, agent, shared]):
        print("❌ Todas as 3 redes precisam existir")
        return
    
    transferred = 0
    
    # Brain → Shared (forex knowledge)
    for sid, syn in brain["synapses"].items():
        if syn["confidence"] >= 0.6 and syn["weight"] >= 0.5:
            if sid not in shared["synapses"]:
                shared["synapses"][sid] = {**syn, "origin": "brain", "crossed_at": now_iso()}
                transferred += 1
    
    # Agent → Shared (automation knowledge)
    for sid, syn in agent["synapses"].items():
        if syn["confidence"] >= 0.6 and syn["weight"] >= 0.5:
            if sid not in shared["synapses"]:
                shared["synapses"][sid] = {**syn, "origin": "agent", "crossed_at": now_iso()}
                transferred += 1
    
    # Shared → Brain (only automation/pipeline concepts relevant to brain)
    for sid, syn in shared["synapses"].items():
        if syn.get("origin") == "agent" and syn["confidence"] >= 0.7:
            if sid not in brain["synapses"]:
                brain["synapses"][sid] = {**syn, "cross_pollinated": True, "crossed_at": now_iso()}
    
    # Shared → Agent (only forex concepts relevant to agent)
    for sid, syn in shared["synapses"].items():
        if syn.get("origin") == "brain" and syn["confidence"] >= 0.7:
            if sid not in agent["synapses"]:
                agent["synapses"][sid] = {**syn, "cross_pollinated": True, "crossed_at": now_iso()}
    
    # Update metrics
    for net, name in [(brain, "brain"), (agent, "agent"), (shared, "shared")]:
        net["metrics"]["total_synapses"] = len(net["synapses"])
        net["metrics"]["cross_pollinations"] = net["metrics"].get("cross_pollinations", 0) + transferred
    
    shared["metrics"]["total_synapses"] = len(shared["synapses"])
    
    for net, name in [(brain, "brain"), (agent, "agent"), (shared, "shared")]:
        save_network(name, net)
    
    print(f"✅ Cross-pollinate: {transferred} sinapses transferidas → rede compartilhada")

def cmd_absorb():
    """Absorb knowledge from knowledge_bridge.json into all 3 networks."""
    bridge = load_json(BRIDGE_FILE)
    if not bridge:
        print("❌ knowledge_bridge.json não encontrado")
        return
    
    discoveries = bridge.get("discoveries", [])
    absorbed_count = {"brain": 0, "agent": 0, "shared": 0}
    
    for disc in discoveries:
        if disc.get("absorbed_by_other", False):
            continue  # Já foi absorvido
        
        source = disc["source"]  # "brain" or "agent"
        content = disc["content"]
        
        # Route to correct network
        if source == "brain":
            cmd_learn("brain", content)
            cmd_learn("shared", content)  # Also goes to shared
            absorbed_count["brain"] += 1
            absorbed_count["shared"] += 1
        elif source == "agent":
            cmd_learn("agent", content)
            cmd_learn("shared", content)
            absorbed_count["agent"] += 1
            absorbed_count["shared"] += 1
        
        # Mark as absorbed
        disc["absorbed_by_other"] = True
    
    save_json(BRIDGE_FILE, bridge)
    
    # Also cross-pollinate after absorbing
    cmd_cross_pollinate()
    
    print(f"✅ Absorb concluído: Brain={absorbed_count['brain']}, Agent={absorbed_count['agent']}, Shared={absorbed_count['shared']}")

def cmd_feed_forward(network):
    """Feed-forward: simula ativação de neurônios e reforça sinapses usadas."""
    net = get_network(network)
    if not net:
        return
    
    activations = 0
    for sid, syn in net["synapses"].items():
        source_n = net["neurons"].get(syn["source"])
        target_n = net["neurons"].get(syn["target"])
        if source_n and target_n:
            source_n["activations"] += 1
            target_n["activations"] += 1
            syn["last_used"] = now_iso()
            activations += 1
    
    # Recalculate strengths based on activations
    max_act = max((n["activations"] for n in net["neurons"].values()), default=1)
    for n in net["neurons"].values():
        n["strength"] = min(1.0, n["activations"] / max(max_act, 1))
    
    net["history"].append({"timestamp": now_iso(), "action": "feed_forward", "detail": f"{activations} ativações propagadas"})
    save_network(network, net)
    print(f"✅ Feed-forward em {net['name']}: {activations} sinapses ativadas, {len(net['neurons'])} neurônios reforçados")

def cmd_status():
    """Show status of all 3 networks."""
    networks = {}
    for name, path in [("brain", NN_BRAIN), ("agent", NN_AGENT), ("shared", NN_SHARED)]:
        if path.exists():
            net = load_json(path)
            networks[name] = {
                "name": net["name"],
                "neurons": len(net["neurons"]),
                "synapses": len(net["synapses"]),
                "assertiveness": f"{net['metrics']['assertiveness']:.1%}",
                "avg_weight": f"{net['metrics']['avg_weight']:.3f}",
                "avg_confidence": f"{net['metrics']['avg_confidence']:.3f}",
                "prunes": net["metrics"]["prunes"],
                "cross_pollinations": net["metrics"].get("cross_pollinations", 0),
                "last_backprop": net["metrics"].get("last_backprop"),
                "domains": {d: len(n["neurons"]) for d, n in net["layers"].items() if n["neurons"]},
            }
        else:
            networks[name] = None
    
    print(f"\n{'═'*60}")
    print(f"  STATUS DAS 3 REDES NEURAIS")
    print(f"{'═'*60}\n")
    
    for name, info in networks.items():
        if info is None:
            print(f"  {name}: ❌ Não inicializada")
        else:
            icon = "🧠" if name == "brain" else "🤖" if name == "agent" else "🔗"
            print(f"  {icon} {info['name']}")
            print(f"     Neurônios: {info['neurons']} | Sinapses: {info['synapses']}")
            print(f"     Assertividade: {info['assertiveness']} | Peso médio: {info['avg_weight']}")
            print(f"     Confiança: {info['avg_confidence']} | Poda: {info['prunes']} | Cross: {info['cross_pollinations']}")
            if info["last_backprop"]:
                print(f"     Último backprop: {info['last_backprop'][:19]}")
            if info["domains"]:
                top_domains = sorted(info["domains"].items(), key=lambda x: x[1], reverse=True)[:3]
                print(f"     Top domínios: {', '.join(f'{d}({n})' for d,n in top_domains)}")
        print()
    
    # Check bridge
    bridge = load_json(BRIDGE_FILE)
    if bridge:
        unabsorbed = sum(1 for d in bridge.get("discoveries", []) if not d.get("absorbed_by_other", False))
        print(f"  Knowledge Bridge: {len(bridge['discoveries'])} descobertas ({unabsorbed} não absorvidas)")
    
    print(f"{'═'*60}\n")

def cmd_register_error(network, error_desc, failed_approach, correct_approach):
    """Register an error: marks synapse as miss, adds anti-pattern."""
    net = get_network(network)
    if not net:
        return
    
    # Find or create synapse for the failed approach
    cmd_add_synapse(failed_approach, "FAILED", 0.1, network, confidence=0.1)
    
    # Mark as miss in the related synapse
    for sid, syn in net["synapses"].items():
        if failed_approach in syn.get("source_concept", "") or failed_approach in syn.get("target_concept", ""):
            syn["misses"] += 1
            syn["confidence"] = max(0.1, syn["confidence"] - 0.1)
    
    # Add anti-pattern
    net["anti_patterns"].append({
        "timestamp": now_iso(),
        "error": error_desc,
        "failed_approach": failed_approach,
        "correct_approach": correct_approach,
    })
    
    # Add correct approach as high-weight synapse
    cmd_add_synapse(correct_approach, "SUCCESS", 0.9, network, confidence=0.8)
    
    net["history"].append({"timestamp": now_iso(), "action": "register_error", "detail": f"Erro: {error_desc[:80]}"})
    save_network(network, net)
    print(f"✅ Erro registrado em {net['name']}: {error_desc[:80]}...")
    
    # Auto backprop after error
    cmd_backprop(network)

def cmd_register_success(network, approach, context=""):
    """Register a successful approach: marks hits, increases confidence."""
    net = get_network(network)
    if not net:
        return
    
    # Mark hits on related synapses
    for sid, syn in net["synapses"].items():
        if approach.lower() in syn.get("source_concept", "").lower() or approach.lower() in syn.get("target_concept", "").lower():
            syn["hits"] += 1
            syn["confidence"] = min(1.0, syn["confidence"] + 0.1)
            syn["last_used"] = now_iso()
    
    net["history"].append({"timestamp": now_iso(), "action": "register_success", "detail": f"Sucesso: {approach[:80]}"})
    save_network(network, net)
    print(f"✅ Sucesso registrado em {net['name']}: {approach[:80]}...")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        cmd_status()
        return
    
    cmd = sys.argv[1]
    
    if cmd == "init":
        cmd_init()
    
    elif cmd == "status":
        cmd_status()
    
    elif cmd == "add_neuron":
        network, concept = sys.argv[2], sys.argv[3]
        domain = sys.argv[4] if len(sys.argv) > 4 else "learning"
        cmd_add_neuron(network, concept, domain)
    
    elif cmd == "add_synapse":
        source, target, weight, network = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
        confidence = float(sys.argv[6]) if len(sys.argv) > 6 else 0.5
        cmd_add_synapse(source, target, weight, network, confidence)
    
    elif cmd == "learn":
        network, fact = sys.argv[2], sys.argv[3]
        cmd_learn(network, fact)
    
    elif cmd == "absorb":
        cmd_absorb()
    
    elif cmd == "feed_forward":
        network = sys.argv[2] if len(sys.argv) > 2 else "all"
        if network == "all":
            for n in ["brain", "agent", "shared"]:
                cmd_feed_forward(n)
        else:
            cmd_feed_forward(network)
    
    elif cmd == "backprop":
        network = sys.argv[2] if len(sys.argv) > 2 else "all"
        if network == "all":
            for n in ["brain", "agent", "shared"]:
                cmd_backprop(n)
        else:
            cmd_backprop(network)
    
    elif cmd == "cross_pollinate":
        cmd_cross_pollinate()
    
    elif cmd == "consolidate":
        network = sys.argv[2] if len(sys.argv) > 2 else "all"
        if network == "all":
            for n in ["brain", "agent", "shared"]:
                cmd_consolidate(n)
        else:
            cmd_consolidate(network)
    
    elif cmd == "prune":
        network = sys.argv[2] if len(sys.argv) > 2 else "all"
        if network == "all":
            for n in ["brain", "agent", "shared"]:
                cmd_prune(n)
        else:
            cmd_prune(network)
    
    elif cmd == "register_error":
        network, error, failed, correct = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
        cmd_register_error(network, error, failed, correct)
    
    elif cmd == "register_success":
        network, approach = sys.argv[2], sys.argv[3]
        context = sys.argv[4] if len(sys.argv) > 4 else ""
        cmd_register_success(network, approach, context)
    
    else:
        print(f"❌ Comando desconhecido: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
