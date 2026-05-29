#!/usr/bin/env python3
"""
CRYPTO MULTI-AGENT v5 — Pattern Detector Integrado
Novo: Market Structure, Order Block, Breaker Block, Liquidity Sweep
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from pattern_detector import AdvancedPatternDetector
import numpy as np
from datetime import datetime, timezone

class VolatilidadeAgent:
    """Analisa volatilidade e regime (filtro data-driven: BAIXA_VOL = 51% WR)."""
    
    def analyze(self, highs, lows, closes, pip_size):
        n = len(closes)
        if n < 20: return 'NEUTRAL', 0, {'regime': 'DESCONHECIDO', 'atr_pct': 0}
        
        tr = [max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1])) 
              for i in range(1, min(20, n))]
        atr = sum(tr[-14:]) / len(tr[-14:]) if len(tr) >= 14 else sum(tr) / len(tr)
        atr_pct = atr / closes[-1] * 100
        
        # Classificação data-driven
        if atr_pct > 0.6:
            regime, conf, sl_rec = 'ALTA_VOL', 85, 0.6
        elif atr_pct > 0.20:
            regime, conf, sl_rec = 'MEDIA_VOL', 60, 0.3
        elif atr_pct > 0.08:
            regime, conf, sl_rec = 'NORMAL', 40, 0.2
        else:
            regime, conf, sl_rec = 'BAIXA_VOL', 20, 0.12  # melhor WR histórico
        
        return 'NEUTRAL', conf, {
            'regime': regime, 'atr_pct': round(atr_pct, 3),
            'sl_recommend': min(sl_rec, 1.5),
            'is_low_vol': regime == 'BAIXA_VOL'
        }


class TendenciaAgent:
    """Tendência multi-TF com alinhamento M15+M5 obrigatório. M1 opcional."""
    
    def analyze_tf(self, closes, period, label):
        if len(closes) < period * 2: return 'NEUTRAL', 0, []
        
        half = period // 2
        ema_fast = sum(closes[-half:]) / half
        ema_slow = sum(closes[-period:]) / period
        
        if closes[-1] > ema_fast > ema_slow:
            direction, score = 'BUY', 35 if label == 'M15' else 25
            return direction, score, [f'{label}↑']
        elif closes[-1] < ema_fast < ema_slow:
            direction, score = 'SELL', 35 if label == 'M15' else 25
            return direction, score, [f'{label}↓']
        return 'NEUTRAL', 0, []
    
    def analyze(self, highs, lows, closes):
        if len(closes) < 100: return 'NEUTRAL', 0, ''
        
        m15_dir, m15_score, m15_sig = self.analyze_tf(closes, 50, 'M15')
        if m15_dir == 'NEUTRAL': return 'NEUTRAL', 0, 'M15 neutro'
        
        m5_dir, m5_score, m5_sig = self.analyze_tf(closes[-80:] if len(closes)>=80 else closes, 20, 'M5')
        if m5_dir != m15_dir:
            return 'NEUTRAL', 0, f'M5 diverge'
        
        total_score = m15_score + m5_score
        signals = m15_sig + m5_sig
        
        # M1 timing (bônus, não obrigatório)
        m1_dir, m1_score, m1_sig = self.analyze_tf(closes[-40:] if len(closes)>=40 else closes, 10, 'M1')
        if m1_dir == m15_dir:
            total_score += 15
            signals.append('⏱M1')
        
        # S/R favorável
        window = closes[-100:]
        hh, ll = max(window), min(window)
        pos = (closes[-1] - ll) / (hh - ll) if hh > ll else 0.5
        
        if m15_dir == 'BUY' and pos < 0.50:
            total_score += 15; signals.append('Discount')
        elif m15_dir == 'SELL' and pos > 0.50:
            total_score += 15; signals.append('Premium')
        
        if total_score >= 55:
            return m15_dir, total_score, '|'.join(signals)
        return 'NEUTRAL', total_score, f'Score={total_score}'


class PadraoAgent:
    """Padrões ICT avançados: OB com Fibonacci, Breaker, Market Structure Gate."""
    
    def __init__(self):
        self.detector = AdvancedPatternDetector()
    
    def analyze(self, highs, lows, closes, opens, direction, pip_size):
        if len(closes) < 30: return 'NEUTRAL', 0, {}
        
        best, score = self.detector.find_best_pattern(highs, lows, closes, opens, direction)
        
        if best and score >= 50:
            # Adicionar contexto de mercado
            ctx = self.detector.get_market_context(highs, lows, closes)
            best['market_structure'] = ctx['structure']
            best['choch'] = ctx.get('choch')
            best['position'] = ctx.get('position', 0.5)
            return direction, score, best
        
        return 'NEUTRAL', 0, {}


class SessaoAgent:
    """Horários de pico."""
    HIGH_VOL_HOURS = {
        'NY_OPEN': list(range(13, 21)),
        'ASIA_OPEN': list(range(0, 8)),
        'LONDON': list(range(8, 13)),
    }
    
    def get_hour_bonus(self):
        hour = datetime.now(timezone.utc).hour
        if hour in self.HIGH_VOL_HOURS['NY_OPEN']: return 1.0
        elif hour in self.HIGH_VOL_HOURS['ASIA_OPEN']: return 0.85
        elif hour in self.HIGH_VOL_HOURS['LONDON']: return 0.7
        return 0.5
    
    def analyze(self):
        hour = datetime.now(timezone.utc).hour
        if hour in self.HIGH_VOL_HOURS['NY_OPEN']:
            return 'BUY', 75, 'NY Open'
        elif hour in self.HIGH_VOL_HOURS['ASIA_OPEN']:
            return 'BUY', 60, 'Asia'
        elif hour in self.HIGH_VOL_HOURS['LONDON']:
            return 'BUY', 55, 'London'
        return 'NEUTRAL', 25, 'Off-peak'


class FluxoAgent:
    """Correlação BTC/Altcoins."""
    def analyze(self, pair, btc_change_pct=None):
        if pair == 'BTCUSD': return 'NEUTRAL', 50, 'BTC base'
        if btc_change_pct is None: return 'NEUTRAL', 15, 'Sem dados'
        
        abs_chg = abs(btc_change_pct)
        direction = 'BUY' if btc_change_pct > 0 else 'SELL'
        
        if abs_chg > 4.0: return direction, 85, f'BTC {btc_change_pct:+.1f}%'
        elif abs_chg > 2.0: return direction, 65, f'BTC {btc_change_pct:+.1f}%'
        elif abs_chg > 1.0: return direction, 45, f'BTC {btc_change_pct:+.1f}%'
        elif abs_chg > 0.3: return direction, 30, f'BTC {btc_change_pct:+.1f}%'
        return 'NEUTRAL', 35, 'BTC estável'


class CryptoConfluencia:
    """v4: Data-driven filters. BAIXA_VOL = 51% WR, first-touch FVG, min_conf=55%."""
    
    def __init__(self):
        self.volatilidade = VolatilidadeAgent()
        self.tendencia = TendenciaAgent()
        self.padrao = PadraoAgent()
        self.sessao = SessaoAgent()
        self.fluxo = FluxoAgent()
        
        self.weights = {
            'volatilidade': 0.8,
            'tendencia': 2.5,
            'padrao': 2.0,
            'sessao': 0.5,
            'fluxo': 1.0
        }
    
    def analyze(self, pair, highs, lows, closes, opens, daily_bias, pip_size,
                btc_change_pct=None, min_confidence=55):
        
        # Gate 1: Volatilidade
        v_vote, v_conf, v_info = self.volatilidade.analyze(highs, lows, closes, pip_size)
        
        # Gate 2: Tendência (M15+M5 alinhados)
        t_vote, t_conf, t_msg = self.tendencia.analyze(highs, lows, closes)
        if t_vote == 'NEUTRAL':
            return 'NEUTRAL', 0, None, v_info
        
        # Gate 3: Padrão (OB/Breaker com Fibonacci + Market Structure gate)
        p_vote, p_conf, p_sig = self.padrao.analyze(highs, lows, closes, opens, t_vote, pip_size)
        if not p_sig or p_sig.get('quality', 0) < 55:
            return 'NEUTRAL', 0, None, v_info
        
        # Bônus por Market Structure alinhada
        ms_structure = p_sig.get('market_structure', '')
        if ms_structure == 'BULLISH' and t_vote == 'BUY':
            p_conf += 25
        elif ms_structure == 'BEARISH' and t_vote == 'SELL':
            p_conf += 25
        elif ms_structure == 'CHoCH':
            choch = p_sig.get('choch', {})
            if isinstance(choch, dict) and choch.get('type') == t_vote:
                p_conf += 35  # CHoCH alinhado = bônus máximo
        
        # Sessão e Fluxo
        s_vote, s_conf, s_msg = self.sessao.analyze()
        hour_bonus = self.sessao.get_hour_bonus()
        f_vote, f_conf, f_msg = self.fluxo.analyze(pair, btc_change_pct)
        
        # Votação
        votes = {
            'tendencia': {'vote': t_vote, 'conf': t_conf * self.weights['tendencia']},
            'padrao': {'vote': p_vote, 'conf': p_conf * self.weights['padrao']},
            'fluxo': {'vote': f_vote, 'conf': f_conf * self.weights['fluxo']},
            'sessao': {'vote': s_vote, 'conf': s_conf * self.weights['sessao'] * hour_bonus},
        }
        
        buy_score = sum(v['conf'] for v in votes.values() if v['vote'] == 'BUY')
        sell_score = sum(v['conf'] for v in votes.values() if v['vote'] == 'SELL')
        total = sum(v['conf'] for v in votes.values())
        
        if total == 0: return 'NEUTRAL', 0, None, v_info
        
        conf = max(buy_score, sell_score) / total * 100
        conf = conf * (0.6 + hour_bonus * 0.4)
        
        if buy_score > sell_score and conf >= min_confidence:
            return 'BUY', conf, p_sig, v_info
        elif sell_score > buy_score and conf >= min_confidence:
            return 'SELL', conf, p_sig, v_info
        
        return 'NEUTRAL', conf, None, v_info
    
    def analyze_simple(self, pair, highs, lows, closes, opens, daily_bias, pip_size,
                       btc_change_pct=None):
        decision, conf, signal, info = self.analyze(
            pair, highs, lows, closes, opens, daily_bias, pip_size, btc_change_pct
        )
        return decision, conf, signal
