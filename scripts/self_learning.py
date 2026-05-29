#!/usr/bin/env python3
"""
SELF-LEARNING ENGINE — Aprimoramento contínuo do Multi-Agente
Analisa resultados de trades e ajusta pesos dos agentes.
"""
import json, os
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

LEARNING_FILE = Path.home() / '.hermes' / 'forex' / 'agent_learning.json'

class SelfLearning:
    """Aprende com resultados e ajusta confiança dos agentes."""
    
    def __init__(self):
        self.weights = {
            'perfil': 1.0,
            'sessao': 1.0,
            'estrutura': 1.5,   # CRT/OB pesa mais
            'padrao': 1.2,      # FVG scoring
        }
        self.history = []
        self.load()
    
    def load(self):
        if LEARNING_FILE.exists():
            try:
                data = json.loads(LEARNING_FILE.read_text())
                self.weights = data.get('weights', self.weights)
                self.history = data.get('history', [])
            except:
                pass
    
    def save(self):
        LEARNING_FILE.parent.mkdir(parents=True, exist_ok=True)
        LEARNING_FILE.write_text(json.dumps({
            'weights': self.weights,
            'history': self.history[-500:],  # últimas 500
            'updated': datetime.now().isoformat()
        }, indent=2))
    
    def record_trade(self, agent_votes, result_r, pair, direction):
        """
        Registra resultado de trade.
        agent_votes: dict com voto de cada agente {'perfil': 'BUY', ...}
        result_r: R múltiplo (+3 = WIN com RR 3:1, -1 = LOSS)
        """
        entry = {
            'time': datetime.now().isoformat(),
            'pair': pair,
            'direction': direction,
            'result_r': result_r,
            'votes': agent_votes,
        }
        self.history.append(entry)
        
        # Ajustar pesos baseado no resultado
        for agent, vote in agent_votes.items():
            if vote == direction:
                # Agente acertou → aumentar peso
                if result_r > 0:
                    self.weights[agent] = min(3.0, self.weights[agent] * 1.05)
                else:
                    # Agente votou certo mas trade perdeu → reduzir levemente
                    self.weights[agent] = max(0.3, self.weights[agent] * 0.98)
            elif vote and vote != 'NEUTRAL':
                # Agente votou errado → reduzir peso
                self.weights[agent] = max(0.3, self.weights[agent] * 0.95)
        
        self.save()
    
    def get_weighted_confidence(self, agent_votes):
        """Calcula confiança ponderada baseada no aprendizado."""
        total_weight = sum(self.weights.values())
        weighted_score = 0
        
        for agent, vote in agent_votes.items():
            w = self.weights.get(agent, 1.0)
            if vote == 'BUY':
                weighted_score += w
            elif vote == 'SELL':
                weighted_score -= w
        
        # Normalizar para 0-100
        confidence = min(100, abs(weighted_score) / total_weight * 100)
        return confidence
    
    def get_stats(self):
        """Retorna estatísticas de aprendizado."""
        if not self.history:
            return {'trades': 0, 'wr': 0, 'r_total': 0}
        
        recent = self.history[-100:]
        wins = sum(1 for t in recent if t['result_r'] > 0)
        total = len(recent)
        r_total = sum(t['result_r'] for t in recent)
        
        return {
            'trades': total,
            'wr': wins/total*100 if total > 0 else 0,
            'r_total': round(r_total, 1),
            'weights': self.weights
        }
    
    def get_best_agents(self):
        """Retorna ranking dos melhores agentes."""
        if not self.history:
            return []
        
        agent_scores = {}
        for agent in self.weights:
            correct = 0
            total = 0
            for t in self.history:
                vote = t.get('votes', {}).get(agent)
                if vote and vote != 'NEUTRAL':
                    total += 1
                    if (vote == t['direction'] and t['result_r'] > 0) or \
                       (vote != t['direction'] and t['result_r'] < 0):
                        correct += 1
            if total > 0:
                agent_scores[agent] = correct/total*100
        
        return sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)


# Singleton
engine = SelfLearning()

def record_trade_result(agent_votes, result_r, pair, direction):
    """API pública para registrar trade."""
    engine.record_trade(agent_votes, result_r, pair, direction)

def get_weights():
    return engine.weights

def get_stats():
    return engine.get_stats()
