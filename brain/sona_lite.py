#!/usr/bin/env python3
"""
SONALite — Motor de Aprendizado por Reforço (Q-Learning).
Observa trajetórias, julga resultados, destila lições e atualiza a Q-table.
Persiste padrões e Q-table em ~/.hermes/brain/sona_store.json
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import thalamus

import json
from collections import defaultdict
from datetime import datetime, timezone

STORE_PATH = os.path.expanduser("~/.hermes/brain/sona_store.json")
MAX_PATTERNS = 1000
ALPHA = 0.1
GAMMA = 0.9


class SONALite:
    """Motor de aprendizado com Q-Learning e memória de padrões."""

    def __init__(self):
        self.patterns = []          # [{lesson, domain, weight, successes, failures, last_seen}]
        self.q_table = {}           # {state_hash: {action: q_value}}
        self._load()

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------
    def _load(self):
        if os.path.exists(STORE_PATH):
            try:
                with open(STORE_PATH) as f:
                    data = json.load(f)
                self.patterns = data.get("patterns", [])
                self.q_table = data.get("q_table", {})
            except (json.JSONDecodeError, KeyError):
                self.patterns = []
                self.q_table = {}

    def _save(self):
        os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
        with open(STORE_PATH, "w") as f:
            json.dump({
                "patterns": self.patterns,
                "q_table": self.q_table,
                "updated": datetime.now(timezone.utc).isoformat(),
            }, f, indent=2, default=str)

    # ------------------------------------------------------------------
    # Core: observe
    # ------------------------------------------------------------------
    def observe(self, trajectory):
        """Entrada principal: observa uma trajetória completa.
        trajectory: dict com chaves state, action, next_state, pnl, domain, meta
        Retorna dict com resultado do ciclo."""
        similar = self.retrieve_similar(trajectory)
        judgement = self._judge(trajectory)
        lesson = self._distill(trajectory, similar)
        self._consolidate(lesson)
        self._update_q(trajectory, judgement)
        self._save()

        thalamus.log_event("sona_observe", "SONALite", {
            "domain": trajectory.get("domain", "unknown"),
            "judgement": judgement,
            "lesson": lesson.get("lesson", ""),
        })

        return {
            "judgement": judgement,
            "lesson": lesson,
            "similar_count": len(similar),
            "q_table_size": len(self.q_table),
        }

    # ------------------------------------------------------------------
    # retrieve_similar
    # ------------------------------------------------------------------
    def retrieve_similar(self, trajectory, top_k=5):
        """Recupera padrões similares por domínio e similaridade textual."""
        domain = trajectory.get("domain", "general")
        action = trajectory.get("action", "")
        candidates = [p for p in self.patterns if p.get("domain") == domain]
        if not candidates:
            candidates = self.patterns  # fallback: todos os padrões

        # Score simples: overlap de palavras no campo lesson
        action_words = set(str(action).lower().split())
        scored = []
        for p in candidates:
            lesson_words = set(str(p.get("lesson", "")).lower().split())
            overlap = len(action_words & lesson_words) if action_words else 0
            weight = p.get("weight", 0)
            scored.append((overlap + weight * 0.1, p))

        scored.sort(key=lambda x: -x[0])
        return [p for _, p in scored[:top_k]]

    # ------------------------------------------------------------------
    # _judge
    # ------------------------------------------------------------------
    def _judge(self, trajectory):
        """Julga resultado: pnl>0=success, pnl<0=failure, else=partial."""
        pnl = trajectory.get("pnl", 0)
        if pnl > 0:
            return "success"
        elif pnl < 0:
            return "failure"
        else:
            return "partial"

    # ------------------------------------------------------------------
    # _distill
    # ------------------------------------------------------------------
    def _distill(self, trajectory, similar):
        """Extrai lição (lesson string) e conta sucessos passados similares."""
        domain = trajectory.get("domain", "general")
        action = str(trajectory.get("action", ""))
        pnl = trajectory.get("pnl", 0)
        judgement = self._judge(trajectory)

        lesson = f"[{domain}] {action} -> {judgement} (pnl={pnl})"

        similar_past_success = sum(
            1 for p in similar if p.get("judgement") == "success"
        )

        return {
            "lesson": lesson,
            "domain": domain,
            "judgement": judgement,
            "similar_past_success": similar_past_success,
            "pnl": pnl,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # _consolidate
    # ------------------------------------------------------------------
    def _consolidate(self, lesson_data):
        """Deduplica por lesson string, reforça weight, cap em MAX_PATTERNS."""
        lesson_str = lesson_data.get("lesson", "")
        domain = lesson_data.get("domain", "general")
        judgement = lesson_data.get("judgement", "partial")

        # Procura existente
        for p in self.patterns:
            if p.get("lesson") == lesson_str:
                p["weight"] = min(p.get("weight", 1.0) + 0.1, 10.0)
                if judgement == "success":
                    p["successes"] = p.get("successes", 0) + 1
                elif judgement == "failure":
                    p["failures"] = p.get("failures", 0) + 1
                p["last_seen"] = datetime.now(timezone.utc).isoformat()
                self._prune()
                return

        # Novo padrão
        entry = {
            "lesson": lesson_str,
            "domain": domain,
            "weight": 1.0,
            "successes": 1 if judgement == "success" else 0,
            "failures": 1 if judgement == "failure" else 0,
            "judgement": judgement,
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }
        self.patterns.append(entry)
        self._prune()

    def _prune(self):
        """Remove padrões excedentes (os de menor weight mais antigos)."""
        if len(self.patterns) > MAX_PATTERNS:
            self.patterns.sort(key=lambda p: (p.get("weight", 0), p.get("last_seen", "")))
            self.patterns = self.patterns[-(MAX_PATTERNS):]

    # ------------------------------------------------------------------
    # _update_q
    # ------------------------------------------------------------------
    @staticmethod
    def _state_hash(state):
        """Hash determinístico de um estado (dict)."""
        if isinstance(state, dict):
            raw = json.dumps(state, sort_keys=True, default=str)
        else:
            raw = str(state)
        return raw

    def _update_q(self, trajectory, judgement):
        """Q(s,a) += alpha * [r + gamma * max(Q(s')) - Q(s,a)]"""
        state = trajectory.get("state", {})
        action = str(trajectory.get("action", ""))
        next_state = trajectory.get("next_state", {})

        s = self._state_hash(state)
        s_next = self._state_hash(next_state)

        # Recompensa
        if judgement == "success":
            reward = 1.0
        elif judgement == "failure":
            reward = -1.0
        else:
            reward = 0.0

        # Inicializa entradas se necessário
        if s not in self.q_table:
            self.q_table[s] = {}
        if action not in self.q_table[s]:
            self.q_table[s][action] = 0.0

        current_q = self.q_table[s][action]

        # max Q(s')
        max_q_next = 0.0
        if s_next in self.q_table and self.q_table[s_next]:
            max_q_next = max(self.q_table[s_next].values())

        # Atualização Q-Learning
        new_q = current_q + ALPHA * (reward + GAMMA * max_q_next - current_q)
        self.q_table[s][action] = new_q

    # ------------------------------------------------------------------
    # best_action
    # ------------------------------------------------------------------
    def best_action(self, state):
        """Retorna a melhor ação para um estado (argmax Q-table)."""
        s = self._state_hash(state)
        if s not in self.q_table or not self.q_table[s]:
            return None
        return max(self.q_table[s], key=self.q_table[s].get)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------
    def get_stats(self):
        """Retorna estatísticas do motor."""
        total = len(self.patterns)
        if total == 0:
            return {
                "total_patterns": 0,
                "success_rate": 0.0,
                "by_domain": {},
                "q_table_size": len(self.q_table),
            }

        successes = sum(p.get("successes", 0) for p in self.patterns)
        failures = sum(p.get("failures", 0) for p in self.patterns)
        success_rate = successes / max(successes + failures, 1)

        by_domain = defaultdict(lambda: {"count": 0, "successes": 0, "failures": 0})
        for p in self.patterns:
            d = p.get("domain", "unknown")
            by_domain[d]["count"] += 1
            by_domain[d]["successes"] += p.get("successes", 0)
            by_domain[d]["failures"] += p.get("failures", 0)

        return {
            "total_patterns": total,
            "success_rate": round(success_rate, 4),
            "by_domain": dict(by_domain),
            "q_table_size": len(self.q_table),
        }


# ----------------------------------------------------------------------
# Compatibility wrappers for n_accumbens, meta_observer, hippocampus
# (exposes simple function API over the class-based engine)
# ----------------------------------------------------------------------
_default_sona = None


def _get_sona():
    global _default_sona
    if _default_sona is None:
        _default_sona = SONALite()
    return _default_sona


def adjust_weight(key, new_value, old_value=None, lr=None):
    """EMA-adjusted weight (compat wrapper).
    Uses the class observe() with domain-based trajectories.
    """
    sona = _get_sona()
    # Store as Q-learning trajectory with key as domain
    if old_value is None:
        old_value = 0.5
    traj = {
        "state": {"key": key, "old_value": old_value},
        "action": f"adjust:{new_value:.3f}",
        "next_state": {"key": key, "new_value": new_value},
        "pnl": (new_value - old_value) * 10,  # scaled reward
        "domain": f"weight:{key}",
    }
    sona.observe(traj)
    # Return the EMA-adjusted value (simulated)
    alpha = lr if lr else 0.1
    return old_value + alpha * (new_value - old_value)


def batch_adjust(updates, lr=None):
    """Apply multiple adjustments."""
    results = {}
    for u in updates:
        if len(u) == 3:
            k, nv, ov = u
        elif len(u) == 2:
            k, nv = u
            ov = None
        else:
            continue
        results[k] = adjust_weight(k, nv, ov, lr)
    return results


def get_weight(key):
    """Get current weight from sona patterns (compat)."""
    sona = _get_sona()
    domain = f"weight:{key}"
    patterns = [p for p in sona.patterns if p.get("domain") == domain]
    if not patterns:
        return None
    # Return average weight of matching patterns
    return sum(p.get("weight", 1.0) for p in patterns) / len(patterns)


def get_all_weights():
    """Get all tracked weights (compat)."""
    sona = _get_sona()
    weights = {}
    for p in sona.patterns:
        domain = p.get("domain", "")
        if domain.startswith("weight:"):
            key = domain[7:]
            weights[key] = p.get("weight", 1.0)
    return weights


def apply_decay():
    """Apply decay to all weights (compat — no-op, class handles decay internally)."""
    sona = _get_sona()
    sona._prune()
    return get_all_weights()


def set_learning_rate(lr):
    """Set learning rate (compat — stored as global)."""
    global ALPHA
    ALPHA = max(0.0, min(1.0, lr))


def record_reward(signal, magnitude=0.1):
    """Record a reward/punishment signal (compat)."""
    sona = _get_sona()
    traj = {
        "state": {"signal": signal},
        "action": "reward",
        "next_state": {"signal": signal, "magnitude": magnitude},
        "pnl": signal * magnitude * 100,
        "domain": "reward_tracking",
    }
    sona.observe(traj)


def get_plasticity():
    """Get plasticity estimate (compat — based on pattern diversity)."""
    sona = _get_sona()
    stats = sona.get_stats()
    total = stats.get("total_patterns", 0)
    if total == 0:
        return 1.0
    domains = len(stats.get("by_domain", {}))
    return min(2.0, max(0.1, domains / max(total, 1) * 10))


def reset(key=None):
    """Reset weights (compat)."""
    sona = _get_sona()
    if key:
        domain = f"weight:{key}"
        sona.patterns = [p for p in sona.patterns if p.get("domain") != domain]
    else:
        sona.patterns = []
        sona.q_table = {}
    sona._save()


# ----------------------------------------------------------------------
# __main__
# ----------------------------------------------------------------------
if __name__ == "__main__":
    sona = SONALite()

    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        stats = sona.get_stats()
        print(json.dumps(stats, indent=2, default=str))

    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        # Teste rápido
        traj = {
            "state": {"price": 100, "trend": "up"},
            "action": "BUY",
            "next_state": {"price": 105, "trend": "up"},
            "pnl": 5,
            "domain": "forex",
        }
        result = sona.observe(traj)
        print("Observe result:", json.dumps(result, indent=2, default=str))

        traj2 = {
            "state": {"price": 100, "trend": "down"},
            "action": "BUY",
            "next_state": {"price": 95, "trend": "down"},
            "pnl": -5,
            "domain": "forex",
        }
        result2 = sona.observe(traj2)
        print("Observe result 2:", json.dumps(result2, indent=2, default=str))

        best = sona.best_action({"price": 100, "trend": "up"})
        print("Best action:", best)

        stats = sona.get_stats()
        print("Stats:", json.dumps(stats, indent=2, default=str))

    else:
        print(f"SONALite — {sona.get_stats()['total_patterns']} patterns, "
              f"Q-table: {sona.get_stats()['q_table_size']} entries")
        print("Usage: sona_lite.py [stats|test]")
