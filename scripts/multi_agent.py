#!/usr/bin/env python3
"""Sistema Multi-Agente de Análise Forex"""
import numpy as np
from datetime import datetime, timezone

class PerfilAgent:
    PERFIS = {
        'EURUSD': {'asia_wr':0.25,'london_wr':0.35,'ny_wr':0.25},
        'GBPUSD': {'asia_wr':0.20,'london_wr':0.30,'ny_wr':0.25},
        'USDJPY': {'asia_wr':0.35,'london_wr':0.20,'ny_wr':0.20},
        'XAUUSD': {'asia_wr':0.40,'london_wr':0.40,'ny_wr':0.35},
    }
    def analyze(self, pair, hour_utc):
        p = self.PERFIS.get(pair, {'asia_wr':0.2,'london_wr':0.25,'ny_wr':0.2})
        if 0 <= hour_utc < 7: sessao = 'Asia'; wr = p['asia_wr']
        elif 7 <= hour_utc < 15: sessao = 'London'; wr = p['london_wr']
        else: sessao = 'NY'; wr = p['ny_wr']
        if wr < 0.15: return 'NEUTRAL', 0, f'{sessao} WR baixo ({wr:.0%})'
        return 'NEUTRAL', int(wr*100), f'{pair} {sessao} WR~{wr:.0%}'

class SessaoAgent:
    def analyze(self, highs, lows, closes, pip_size):
        n = len(closes)
        if n < 40: return 'NEUTRAL', 0, 'Dados insuficientes'
        asia_n = min(240, n)
        asia_range = (max(highs[-asia_n:]) - min(lows[-asia_n:])) / pip_size
        pre_n = min(240, n - asia_n)
        if pre_n < 20: return 'NEUTRAL', 0, ''
        pre_range = (max(highs[-asia_n-pre_n:-asia_n]) - min(lows[-asia_n-pre_n:-asia_n])) / pip_size
        ratio = asia_range / max(pre_range, 1)
        if ratio < 0.5: return 'NEUTRAL', 60, f'Asia contraiu → breakout'
        return 'NEUTRAL', 30, f'Asia normal'

class EstruturaAgent:
    def analyze(self, highs, lows, closes, daily_bias):
        n = len(closes)
        if n < 20: return 'NEUTRAL', 0, ''
        score = 0; signals = []
        ranges = [highs[i]-lows[i] for i in range(-22, -2)]
        if ranges:
            avg = sum(ranges)/len(ranges)
            crt_h, crt_l = highs[-2], lows[-2]
            crt_range = crt_h - crt_l
            if crt_range > avg * 1.3:
                crt_close = closes[-2]
                sw_h, sw_l, sw_c = highs[-1], lows[-1], closes[-1]
                if crt_close < (crt_l + crt_range*0.5) and sw_l < crt_l and sw_c > crt_l:
                    if daily_bias == 'BUY': score += 40; signals.append('CRT')
                elif crt_close > (crt_l + crt_range*0.5) and sw_h > crt_h and sw_c < crt_h:
                    if daily_bias == 'SELL': score += 40; signals.append('CRT')
        if closes[-1] > closes[-n//2] and daily_bias == 'BUY': score += 30; signals.append('SWING')
        elif closes[-1] < closes[-n//2] and daily_bias == 'SELL': score += 30; signals.append('SWING')
        if score >= 40: return daily_bias, score, '+'.join(signals)
        return 'NEUTRAL', score, f'Score={score}'

class PadraoAgent:
    def analyze(self, highs, lows, closes, direction, pip_size, is_metal=False):
        n = len(closes)
        if n < 10: return 'NEUTRAL', 0, {}
        best_score = 0; best = None
        for i in range(6, n-1):
            if direction == 'BUY' and lows[i] > highs[i-2]:
                gap = (lows[i]-highs[i-2])/pip_size
                score = 30 if closes[i] < (max(highs[-20:])+min(lows[-20:]))/2 else 0
                score += 25 if sum(1 for j in range(1,min(10,i)) if closes[i-j]>closes[i-j-1]) > 5 else 0
                if not any(lows[j] <= highs[i-2] for j in range(i+1, min(i+10, n))): score += 20
                if score > best_score and gap >= (100 if is_metal else 1.0):
                    best_score = score; best = {'entry': closes[i], 'direction': 'BUY', 'idx': i, 'gap': gap}
            elif direction == 'SELL' and highs[i] < lows[i-2]:
                gap = (lows[i-2]-highs[i])/pip_size
                score = 30 if closes[i] > (max(highs[-20:])+min(lows[-20:]))/2 else 0
                score += 25 if sum(1 for j in range(1,min(10,i)) if closes[i-j]<closes[i-j-1]) > 5 else 0
                if not any(highs[j] >= lows[i-2] for j in range(i+1, min(i+10, n))): score += 20
                if score > best_score and gap >= (100 if is_metal else 1.0):
                    best_score = score; best = {'entry': closes[i], 'direction': 'SELL', 'idx': i, 'gap': gap}
        if best: return direction, best_score, best
        return 'NEUTRAL', 0, {}

class ConfluenciaAgent:
    def __init__(self):
        self.perfil = PerfilAgent()
        self.sessao = SessaoAgent()
        self.estrutura = EstruturaAgent()
        self.padrao = PadraoAgent()
        self.weights = {'perfil': 1.0, 'sessao': 1.0, 'estrutura': 1.5, 'padrao': 1.2}
    
    def analyze(self, pair, highs, lows, closes, daily_bias, pip_size, is_metal=False):
        hour = datetime.now(timezone.utc).hour
        p_vote, p_conf, p_msg = self.perfil.analyze(pair, hour)
        s_vote, s_conf, s_msg = self.sessao.analyze(highs, lows, closes, pip_size)
        e_vote, e_conf, e_msg = self.estrutura.analyze(highs, lows, closes, daily_bias)
        d_vote, d_conf, d_sig = self.padrao.analyze(highs, lows, closes, daily_bias, pip_size, is_metal)
        
        votes = {
            'perfil': {'vote': p_vote, 'conf': p_conf * self.weights['perfil']},
            'sessao': {'vote': s_vote, 'conf': s_conf * self.weights['sessao']},
            'estrutura': {'vote': e_vote, 'conf': e_conf * self.weights['estrutura']},
            'padrao': {'vote': d_vote, 'conf': d_conf * self.weights['padrao']},
        }
        
        buy_score = sum(v['conf'] for v in votes.values() if v['vote'] == 'BUY')
        sell_score = sum(v['conf'] for v in votes.values() if v['vote'] == 'SELL')
        total = sum(v['conf'] for v in votes.values())
        conf = max(buy_score, sell_score) / max(total, 1) * 100
        
        if buy_score > sell_score and conf >= 20:
            return 'BUY', conf, d_sig or {'entry': closes[-1], 'direction': 'BUY', 'idx': len(closes)-1}
        elif sell_score > buy_score and conf >= 20:
            return 'SELL', conf, d_sig or {'entry': closes[-1], 'direction': 'SELL', 'idx': len(closes)-1}
        return 'NEUTRAL', conf, None
