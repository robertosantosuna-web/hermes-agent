#!/usr/bin/env python3
"""
CRYPTO MULTI-AGENT SYSTEM — 5 agentes especializados para criptomoedas
Adaptado para mercado 24/7, alta volatilidade, sem sessões fixas
"""
import numpy as np
from datetime import datetime, timezone

class VolatilidadeAgent:
    """Analisa volatilidade e regime de mercado crypto."""
    
    def analyze(self, highs, lows, closes, pip_size):
        n = len(closes)
        if n < 20: return 'NEUTRAL', 0, ''
        
        # ATR(14)
        tr = [max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1])) 
              for i in range(1, min(20, n))]
        atr = sum(tr[-14:]) / len(tr[-14:]) if len(tr) >= 14 else sum(tr) / len(tr)
        atr_pct = atr / closes[-1] * 100  # ATR como % do preço
        
        # Classificar regime
        if atr_pct > 0.5:
            regime = 'ALTA_VOL'
            conf = 80
        elif atr_pct > 0.2:
            regime = 'MEDIA_VOL'  
            conf = 60
        else:
            regime = 'BAIXA_VOL'
            conf = 30
        
        return 'NEUTRAL', conf, f'ATR={atr_pct:.2f}% {regime}'


class TendenciaAgent:
    """Analisa tendência de curto e médio prazo em crypto."""
    
    def analyze(self, highs, lows, closes):
        n = len(closes)
        if n < 50: return 'NEUTRAL', 0, ''
        
        score = 0
        signals = []
        
        # EMA crosses (20/50)
        ema20 = sum(closes[-20:]) / 20
        ema50 = sum(closes[-min(50,n):]) / min(50,n)
        
        if ema20 > ema50 and closes[-1] > ema20:
            score += 35; signals.append('EMA↑')
            direction = 'BUY'
        elif ema20 < ema50 and closes[-1] < ema20:
            score += 35; signals.append('EMA↓')
            direction = 'SELL'
        else:
            direction = 'NEUTRAL'
        
        # Momentum (últimas 10 velas vs 10 anteriores)
        recent = sum(closes[-10:]) / 10
        prior = sum(closes[-20:-10]) / 10
        mom = (recent - prior) / prior * 100
        
        if mom > 2.0 and direction in ('BUY', 'NEUTRAL'):
            score += 25; signals.append(f'Mom+{mom:.1f}%')
            direction = 'BUY'
        elif mom < -2.0 and direction in ('SELL', 'NEUTRAL'):
            score += 25; signals.append(f'Mom{mom:.1f}%')
            direction = 'SELL'
        elif abs(mom) > 1.0:
            score += 10
        
        # Suporte/Resistência (últimas 50 velas)
        hh = max(highs[-50:])
        ll = min(lows[-50:])
        pos = (closes[-1] - ll) / (hh - ll) if hh > ll else 0.5
        
        if direction == 'BUY' and pos < 0.4:
            score += 20; signals.append('Suporte')
        elif direction == 'SELL' and pos > 0.6:
            score += 20; signals.append('Resistência')
        
        if direction != 'NEUTRAL' and score >= 40:
            return direction, score, '+'.join(signals)
        return 'NEUTRAL', score, f'Score={score}'


class PadraoAgent:
    """Detecta padrões de candle e FVG em crypto."""
    
    def analyze(self, highs, lows, closes, opens, direction, pip_size):
        n = len(closes)
        if n < 10: return 'NEUTRAL', 0, {}
        
        best_score = 0; best = None
        
        for i in range(6, n-1):
            # FVG com tamanho mínimo (% do preço)
            min_gap_pct = 0.05  # 0.05% mínimo
            
            if direction == 'BUY' and lows[i] > highs[i-2]:
                gap_pct = (lows[i] - highs[i-2]) / closes[i] * 100
                if gap_pct >= min_gap_pct:
                    score = 50  # FVG encontrado = 50pts base
                    
                    # Premium/Discount (Fibonacci 0.5)
                    hh = max(highs[max(0,i-50):i+1])
                    ll = min(lows[max(0,i-50):i+1])
                    eq = (hh + ll) / 2
                    if closes[i] < eq: score += 25  # Discount zone
                    
                    # Volume (tamanho do candle)
                    body = abs(closes[i] - opens[i])
                    avg_body = np.mean([abs(closes[j]-opens[j]) for j in range(max(0,i-20), i)])
                    if body > avg_body * 1.3: score += 15
                    
                    # Não mitigado
                    mitigated = any(lows[j] <= highs[i-2] for j in range(i+1, min(i+10, n)))
                    if not mitigated: score += 10
                    
                    if score > best_score:
                        best_score = score
                        best = {'entry': closes[i], 'direction': 'BUY', 'idx': i, 
                                'gap_pct': round(gap_pct, 3)}
            
            elif direction == 'SELL' and highs[i] < lows[i-2]:
                gap_pct = (lows[i-2] - highs[i]) / closes[i] * 100
                if gap_pct >= min_gap_pct:
                    score = 50
                    
                    hh = max(highs[max(0,i-50):i+1])
                    ll = min(lows[max(0,i-50):i+1])
                    eq = (hh + ll) / 2
                    if closes[i] > eq: score += 25
                    
                    body = abs(closes[i] - opens[i])
                    avg_body = np.mean([abs(closes[j]-opens[j]) for j in range(max(0,i-20), i)])
                    if body > avg_body * 1.3: score += 15
                    
                    mitigated = any(highs[j] >= lows[i-2] for j in range(i+1, min(i+10, n)))
                    if not mitigated: score += 10
                    
                    if score > best_score:
                        best_score = score
                        best = {'entry': closes[i], 'direction': 'SELL', 'idx': i,
                                'gap_pct': round(gap_pct, 3)}
        
        if best:
            return direction, best_score, best
        return 'NEUTRAL', 0, {}


class FluxoAgent:
    """Analisa fluxo de capital — crypto específico (BTC domina, ETH segue)."""
    
    def analyze(self, pair, btc_change_pct=None):
        """
        Se BTC está subindo forte, alts seguem.
        Se BTC está caindo, alts caem mais.
        """
        if pair == 'BTCUSD':
            return 'NEUTRAL', 50, 'BTC par base'
        
        if btc_change_pct is None:
            return 'NEUTRAL', 30, 'Sem dados BTC'
        
        if btc_change_pct > 3.0:
            return 'BUY', 70, f'BTC +{btc_change_pct:.1f}% → alts seguem'
        elif btc_change_pct < -3.0:
            return 'SELL', 70, f'BTC {btc_change_pct:.1f}% → alts caem'
        elif btc_change_pct > 1.0:
            return 'BUY', 40, f'BTC leve alta +{btc_change_pct:.1f}%'
        elif btc_change_pct < -1.0:
            return 'SELL', 40, f'BTC leve queda {btc_change_pct:.1f}%'
        
        return 'NEUTRAL', 20, 'BTC estável'


class CryptoConfluencia:
    """Integra votos dos 4 agentes crypto e decide entrada."""
    
    def __init__(self):
        self.volatilidade = VolatilidadeAgent()
        self.tendencia = TendenciaAgent()
        self.padrao = PadraoAgent()
        self.fluxo = FluxoAgent()
        self.weights = {'volatilidade': 1.0, 'tendencia': 1.5, 'padrao': 1.5, 'fluxo': 1.0}
    
    def analyze(self, pair, highs, lows, closes, opens, daily_bias, pip_size, 
                btc_change_pct=None):
        """
        Análise completa crypto.
        Retorna: (decisão, confiança, sinal_dict)
        """
        hour = datetime.now(timezone.utc).hour
        
        v_vote, v_conf, v_msg = self.volatilidade.analyze(highs, lows, closes, pip_size)
        t_vote, t_conf, t_msg = self.tendencia.analyze(highs, lows, closes)
        p_vote, p_conf, p_sig = self.padrao.analyze(highs, lows, closes, opens, daily_bias, pip_size)
        f_vote, f_conf, f_msg = self.fluxo.analyze(pair, btc_change_pct)
        
        votes = {
            'volatilidade': {'vote': v_vote, 'conf': v_conf * self.weights['volatilidade']},
            'tendencia': {'vote': t_vote, 'conf': t_conf * self.weights['tendencia']},
            'padrao': {'vote': p_vote, 'conf': p_conf * self.weights['padrao']},
            'fluxo': {'vote': f_vote, 'conf': f_conf * self.weights['fluxo']},
        }
        
        buy_score = sum(v['conf'] for v in votes.values() if v['vote'] == 'BUY')
        sell_score = sum(v['conf'] for v in votes.values() if v['vote'] == 'SELL')
        total = sum(v['conf'] for v in votes.values())
        conf = max(buy_score, sell_score) / max(total, 1) * 100
        
        # Confiança mínima menor para crypto (mais volátil = mais oportunidades)
        if buy_score > sell_score and conf >= 25:
            return 'BUY', conf, p_sig or {'entry': closes[-1], 'direction': 'BUY', 'idx': len(closes)-1}
        elif sell_score > buy_score and conf >= 25:
            return 'SELL', conf, p_sig or {'entry': closes[-1], 'direction': 'SELL', 'idx': len(closes)-1}
        return 'NEUTRAL', conf, None
