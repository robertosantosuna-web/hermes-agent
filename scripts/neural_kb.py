#!/usr/bin/env python3
"""
Neural Knowledge Base — Memória compartilhada da rede neural.
Inicializa e mantém a estrutura de conhecimento que todos os módulos
do cérebro podem ler e escrever.

Cada módulo escreve suas descobertas. O Synapse Engine cruza tudo.
"""
import json, os
from pathlib import Path
from datetime import datetime, timezone

HERMES = Path(os.path.expanduser('~/.hermes'))
KB_PATH = HERMES / 'neural_knowledge_base.json'

def init_kb():
    """Initialize or load the shared knowledge base."""
    if KB_PATH.exists():
        try:
            return json.loads(KB_PATH.read_text())
        except:
            pass
    
    kb = {
        "_meta": {
            "version": "1.0",
            "created": datetime.now(timezone.utc).isoformat(),
            "last_consolidation": None,
            "total_synapses": 0,
            "total_updates": 0,
        },
        "global_state": {
            "market_regime": "unknown",
            "market_regime_confidence": 0.0,
            "dominant_trend": "unknown",
            "volatility_level": "unknown",
            "risk_level": "normal",
            "brain_health": "operational",
            "active_modules": 0,
        },
        "modules": {
            "amygdala": {
                "active_threats": [],
                "threat_level": "normal",
                "last_scan": None,
                "recent_alerts": [],
            },
            "n_accumbens": {
                "pair_weights": {},
                "learning_observations": [],
                "strategy_recommendations": [],
                "last_learning": None,
            },
            "hippocampus": {
                "recurring_patterns": [],
                "weekly_insights": {},
                "trade_behavior_patterns": {},
                "failure_heatmap": {},
                "last_consolidation": None,
            },
            "cerebellum": {
                "validation_failures": [],
                "module_health": {},
                "last_validation": None,
            },
            "chart_patterns": {
                "dominant_patterns": [],
                "pattern_quality_by_pair": {},
                "high_quality_setups": [],
                "last_scan": None,
            },
            "research_collector": {
                "key_topics": [],
                "new_concepts": [],
                "sources_collected": 0,
                "last_collection": None,
            },
            "weekly_analyzer": {
                "insights": [],
                "alerts": [],
                "recommendations": [],
                "last_analysis": None,
            },
            "brain_research": {
                "gaps_detected": [],
                "evolution_proposals": [],
                "component_health": {},
                "last_cycle": None,
            },
        },
        "synapses": [],
        "cross_insights": {
            "pattern_to_performance": [],
            "research_to_strategy": [],
            "threats_to_risk": [],
            "health_to_priority": [],
        },
        "evolution": {
            "learned_behaviors": [],
            "strategy_adjustments": [],
            "confirmed_hypotheses": [],
            "rejected_hypotheses": [],
        },
    }
    
    KB_PATH.parent.mkdir(parents=True, exist_ok=True)
    KB_PATH.write_text(json.dumps(kb, indent=2))
    return kb

def load_kb():
    """Load the knowledge base."""
    if not KB_PATH.exists():
        return init_kb()
    try:
        return json.loads(KB_PATH.read_text())
    except:
        return init_kb()

def save_kb(kb):
    """Save the knowledge base."""
    kb["_meta"]["total_updates"] += 1
    KB_PATH.write_text(json.dumps(kb, indent=2))

def module_write(module_name, data, merge=True):
    """Write module data to the shared KB."""
    kb = load_kb()
    
    if module_name not in kb["modules"]:
        kb["modules"][module_name] = {}
    
    if merge:
        kb["modules"][module_name].update(data)
    else:
        kb["modules"][module_name] = data
    
    kb["_meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_kb(kb)
    return kb

def module_read(module_name, key=None):
    """Read module data from shared KB."""
    kb = load_kb()
    mod = kb["modules"].get(module_name, {})
    if key:
        return mod.get(key)
    return mod

def add_synapse(from_module, to_module, insight, confidence, evidence=None):
    """Create a synaptic connection between two modules."""
    kb = load_kb()
    
    synapse = {
        "id": f"syn-{kb['_meta']['total_synapses'] + 1:04d}",
        "from": from_module,
        "to": to_module,
        "insight": insight,
        "confidence": confidence,
        "evidence": evidence or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "applied": False,
    }
    
    kb["synapses"].append(synapse)
    kb["_meta"]["total_synapses"] += 1
    
    # Keep last 200 synapses
    if len(kb["synapses"]) > 200:
        kb["synapses"] = kb["synapses"][-200:]
    
    save_kb(kb)
    return synapse

def get_relevant_insights(module_name, limit=5):
    """Get insights from other modules relevant to this module."""
    kb = load_kb()
    
    relevant = []
    for syn in kb["synapses"]:
        if syn["to"] == module_name and not syn.get("applied"):
            relevant.append(syn)
    
    # Sort by confidence and recency
    relevant.sort(key=lambda s: (s["confidence"], s["timestamp"]), reverse=True)
    return relevant[:limit]

def get_global_state():
    """Get current global brain state."""
    kb = load_kb()
    return kb["global_state"]

def update_global_state(updates):
    """Update global state from any module."""
    kb = load_kb()
    kb["global_state"].update(updates)
    kb["global_state"]["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_kb(kb)
    return kb["global_state"]

def query(question_type):
    """High-level query interface for modules to ask the network."""
    kb = load_kb()
    
    if question_type == "what_to_trade":
        weights = kb["modules"]["n_accumbens"].get("pair_weights", {})
        patterns = kb["modules"]["chart_patterns"].get("pattern_quality_by_pair", {})
        regime = kb["global_state"].get("market_regime", "unknown")
        return {"weights": weights, "patterns": patterns, "regime": regime}
    
    elif question_type == "risk_level":
        threats = kb["modules"]["amygdala"].get("active_threats", [])
        health = kb["modules"]["cerebellum"].get("module_health", {})
        return {"threats": len(threats), "health_failures": sum(1 for v in health.values() if v != "ok")}
    
    elif question_type == "learning_opportunities":
        gaps = kb["modules"]["brain_research"].get("gaps_detected", [])
        research = kb["modules"]["research_collector"].get("new_concepts", [])
        return {"gaps": gaps, "new_concepts": research}
    
    elif question_type == "strategy_health":
        insights = kb["cross_insights"].get("pattern_to_performance", [])
        evo = kb["evolution"].get("strategy_adjustments", [])
        return {"insights": insights[-3:], "adjustments": evo[-3:]}
    
    return {"error": "unknown_question_type"}

# ─── CLI ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    
    if '--init' in sys.argv:
        kb = init_kb()
        print(json.dumps({"_meta": kb["_meta"]}, indent=2))
    elif '--summary' in sys.argv:
        kb = load_kb()
        print(f"Modules: {len(kb['modules'])}")
        print(f"Synapses: {kb['_meta']['total_synapses']}")
        print(f"Updates: {kb['_meta']['total_updates']}")
        print(f"Global state: {json.dumps(kb['global_state'], indent=2)}")
        for name, data in kb['modules'].items():
            if data:
                keys = [k for k, v in data.items() if v]
                print(f"  {name}: {len(keys)} active fields")
    else:
        kb = init_kb()
        print(f"Neural KB initialized: {KB_PATH}")
        print(f"Ready for synaptic connections.")
