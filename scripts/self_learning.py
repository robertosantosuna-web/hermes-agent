#!/usr/bin/env python3
"""Self-Learning Engine — Ajuste dinâmico de pesos dos agentes"""
import json
from datetime import datetime
from pathlib import Path
import numpy as np

LEARNING_FILE = Path.home() / '.hermes' / 'forex' / 'agent_learning.json'

class SelfLearning:
    def __init__(self):
        self.weights = {'perfil': 1.0, 'sessao': 1.0, 'estrutura': 1.5, 'padrao': 1.2}
        self.history = []
        self.load()
    def load(self):
        if LEARNING_FILE.exists():
            try:
                data = json.loads(LEARNING_FILE.read_text())
                self.weights = data.get('weights', self.weights)
                self.history = data.get('history', [])
            except: pass
    def save(self):
        LEARNING_FILE.parent.mkdir(parents=True, exist_ok=True)
        LEARNING_FILE.write_text(json.dumps({'weights': self.weights, 'history': self.history[-500:], 'updated': datetime.now().isoformat()}, indent=2))
    def record_trade(self, agent_votes, result_r, pair, direction):
        self.history.append({'time': datetime.now().isoformat(), 'pair': pair, 'direction': direction, 'result_r': result_r, 'votes': agent_votes})
        for agent, vote in agent_votes.items():
            if vote == direction:
                self.weights[agent] = min(3.0, self.weights[agent] * (1.05 if result_r > 0 else 0.98))
            elif vote and vote != 'NEUTRAL':
                self.weights[agent] = max(0.3, self.weights[agent] * 0.95)
        self.save()
    def get_stats(self):
        if not self.history: return {'trades': 0, 'wr': 0, 'r_total': 0}
        recent = self.history[-100:]
        wins = sum(1 for t in recent if t['result_r'] > 0)
        return {'trades': len(recent), 'wr': wins/len(recent)*100, 'r_total': sum(t['result_r'] for t in recent), 'weights': self.weights}
