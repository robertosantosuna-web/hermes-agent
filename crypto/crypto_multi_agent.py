#!/usr/bin/env python3
"""
CRYPTO MULTI-AGENT v4 — Data-driven filters
Base: v2 (477 trades, 45.7% WR) + filtros que COMPROVADAMENTE discriminam:
  - BAIXA_VOL regime: 51% WR (vs NORMAL 42%)
  - BNBUSD: 56% WR, SOLUSD: 38% WR
  - First-touch FVG
  - Confiança mínima 55%
"""
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
    """FVG com first-touch only e idade máxima 20 velas."""
    
    def find_fvg(self, highs, lows, closes, direction, pip_pct=0.02):
        n = len(highs)
        if n < 10: return None, 0
        
        best, best_score = None, 0
        
        for i in range(n-2, max(6, n-200), -1):
            if direction == 'BUY':
                if lows[i] <= highs[i-2]: continue
                gap_pct = (lows[i] - highs[i-2]) / closes[i] * 100
                if gap_pct < pip_pct: continue
                
                # First touch: não pode ter sido tocado
                if any(lows[j] <= highs[i-2] for j in range(i+1, n)): continue
                
                # Idade máxima: 20 velas (20 min)
                if n - i > 20: continue
                
                score = 50
                
                # Premium/Discount
                window_h = max(highs[max(0,i-50):i+1])
                window_l = min(lows[max(0,i-50):i+1])
                eq = (window_h + window_l) / 2
                if closes[i] < eq: score += 25
                
                # Gap size
                score += min(gap_pct / pip_pct * 5, 20)
                
                # Volume do candle
                body = abs(closes[i] - closes[max(0,i-1)])
                avg_body = np.mean([abs(closes[j]-closes[j-1]) for j in range(max(0,i-20), i)])
                if body > avg_body * 1.4: score += 15
                
                if score > best_score:
                    best_score = score
                    best = {'type': 'FVG', 'entry': closes[i], 'direction': 'BUY',
                            'idx': i, 'gap_pct': round(gap_pct, 3), 'quality': score}
            
            else:  # SELL
                if highs[i] >= lows[i-2]: continue
                gap_pct = (lows[i-2] - highs[i]) / closes[i] * 100
                if gap_pct < pip_pct: continue
                
                if any(highs[j] >= lows[i-2] for j in range(i+1, n)): continue
                if n - i > 20: continue
                
                score = 50
                
                window_h = max(highs[max(0,i-50):i+1])
                window_l = min(lows[max(0,i-50):i+1])
                eq = (window_h + window_l) / 2
                if closes[i] > eq: score += 25
                
                score += min(gap_pct / pip_pct * 5, 20)
                
                body = abs(closes[i] - closes[max(0,i-1)])
                avg_body = np.mean([abs(closes[j]-closes[j-1]) for j in range(max(0,i-20), i)])
                if body > avg_body * 1.4: score += 15
                
                if score > best_score:
                    best_score = score
                    best = {'type': 'FVG', 'entry': closes[i], 'direction': 'SELL',
                            'idx': i, 'gap_pct': round(gap_pct, 3), 'quality': score}
        
        return best, best_score
    
    def analyze(self, highs, lows, closes, opens, direction, pip_size):
        if len(closes) < 10: return 'NEUTRAL', 0, {}
        
        fvg, fvg_score = self.find_fvg(highs, lows, closes, direction)
        
        if fvg and fvg_score >= 55:
            return direction, fvg_score, fvg
        
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
        
        # Gate 3: Padrão (first-touch FVG com quality mínimo 80)
        p_vote, p_conf, p_sig = self.padrao.analyze(highs, lows, closes, opens, t_vote, pip_size)
        if not p_sig or p_sig.get('quality', 0) < 80:
            return 'NEUTRAL', 0, None, v_info
        
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
