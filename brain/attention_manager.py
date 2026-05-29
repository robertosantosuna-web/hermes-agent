#!/usr/bin/env python3
"""
AttentionManager — Gerenciador de atenção com fila de prioridade (heapq).
Submete itens com pesos (novelty, urgency, relevance, reward) e retorna
o de maior prioridade. Suporta interrupção (insere no topo).
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import thalamus

import heapq
import time
from datetime import datetime, timezone


# Pesos ajustáveis para scoring
WEIGHTS = {
    "novelty": 0.20,
    "urgency": 0.35,
    "relevance": 0.30,
    "reward": 0.15,
}

# Tipos de eventos e suas urgências base
URGENCY_MAP = {
    "forex_drawdown": 9,
    "deadline": 8,
    "system_failure": 10,
    "alert": 7,
    "user_message": 5,
    "reminder": 4,
    "background_task": 2,
    "unknown": 1,
}


class AttentionItem:
    """Item na fila de atenção. Suporte a heapq com score negativo (max-heap)."""

    def __init__(self, item_id, content, novelty, urgency, relevance, reward, meta=None):
        self.id = item_id
        self.content = content
        self.novelty = novelty
        self.urgency = urgency
        self.relevance = relevance
        self.reward = reward
        self.meta = meta or {}
        self.created_at = time.time()
        self.score = self._compute_score()

    def _compute_score(self):
        return (
            WEIGHTS["novelty"] * self.novelty +
            WEIGHTS["urgency"] * self.urgency +
            WEIGHTS["relevance"] * self.relevance +
            WEIGHTS["reward"] * self.reward
        )

    def __lt__(self, other):
        # heapq é min-heap; invertemos para max-heap (maior score = menor no heap)
        return self.score > other.score

    def __repr__(self):
        return f"AttentionItem({self.id}, score={self.score:.2f}, content={str(self.content)[:40]})"


class AttentionManager:
    """Gerenciador de atenção com fila de prioridade."""

    def __init__(self):
        self._heap = []          # [(neg_score, counter, item)]
        self._counter = 0        # Tie-breaker para heapq (FIFO em caso de empate)
        self._by_id = {}         # id -> item lookup
        self._history = []       # Itens já processados (últimos 200)

    # ------------------------------------------------------------------
    # Submit
    # ------------------------------------------------------------------
    def submit(self, item_id, content, novelty=5, urgency=5, relevance=5, reward=5, meta=None):
        """Submete um item à fila de atenção. Retorna o item criado."""
        item = AttentionItem(
            item_id=item_id, content=content,
            novelty=novelty, urgency=urgency, relevance=relevance, reward=reward,
            meta=meta,
        )
        self._push(item)

        thalamus.broadcast_to_workspace(
            content=f"Attention: {content}", priority=int(item.score * 10), source="attention_manager"
        )

        return item

    def _push(self, item):
        """Empurra item para o heap."""
        heapq.heappush(self._heap, (item.score, self._counter, item))
        self._counter += 1
        self._by_id[item.id] = item

    # ------------------------------------------------------------------
    # next
    # ------------------------------------------------------------------
    def next(self):
        """Retorna o item de maior prioridade e o remove da fila."""
        while self._heap:
            score, _, item = heapq.heappop(self._heap)
            if item.id in self._by_id:
                del self._by_id[item.id]
                self._history.append(item)
                if len(self._history) > 200:
                    self._history = self._history[-200:]
                return item
        return None

    # ------------------------------------------------------------------
    # interrupt
    # ------------------------------------------------------------------
    def interrupt(self, item_id, content, priority=10, meta=None):
        """Insere um item de interrupção no topo da fila (prioridade máxima)."""
        item = AttentionItem(
            item_id=item_id, content=content,
            novelty=priority, urgency=priority, relevance=priority, reward=priority,
            meta=meta,
        )
        # Força score máximo
        item.score = priority
        self._push(item)

        thalamus.log_event("attention_interrupt", "AttentionManager", {
            "item_id": item_id, "content": str(content)[:100], "priority": priority,
        })

        return item

    # ------------------------------------------------------------------
    # Scoring helpers
    # ------------------------------------------------------------------
    @staticmethod
    def score_urgency(event_type):
        """Calcula score de urgência para um tipo de evento."""
        return URGENCY_MAP.get(event_type, URGENCY_MAP["unknown"])

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------
    def peek(self):
        """Olha o próximo item sem remover."""
        if self._heap:
            return self._heap[0][2]
        return None

    def pending_count(self):
        return len(self._heap)

    def get_recent_history(self, n=10):
        return self._history[-n:]

    def clear(self):
        """Limpa toda a fila."""
        self._heap.clear()
        self._by_id.clear()
        self._counter = 0


# ----------------------------------------------------------------------
# __main__
# ----------------------------------------------------------------------
if __name__ == "__main__":
    am = AttentionManager()

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Submete itens normais
        am.submit("t1", "Check forex EURUSD", novelty=3, urgency=5, relevance=7, reward=4)
        am.submit("t2", "System health check", novelty=2, urgency=8, relevance=6, reward=3)
        am.submit("t3", "Read news feed", novelty=7, urgency=3, relevance=5, reward=6)

        print(f"Pending: {am.pending_count()}")
        print(f"Peek: {am.peek()}")

        # Interrompe
        am.interrupt("int1", "CRITICAL: Drawdown alert", priority=10)
        print(f"After interrupt, pending: {am.pending_count()}")
        print(f"Peek: {am.peek()}")

        # Processa tudo
        while am.pending_count() > 0:
            item = am.next()
            print(f"Processing: {item}")

        print("Urgency scores:")
        for etype in ["forex_drawdown", "deadline", "system_failure", "alert", "user_message"]:
            print(f"  {etype}: {am.score_urgency(etype)}")

    else:
        print(f"AttentionManager: {am.pending_count()} pending")
        if am.peek():
            print(f"Next: {am.peek()}")
        print("Usage: attention_manager.py test")
