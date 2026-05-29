#!/usr/bin/env python3
"""
CRYPTO MULTI-AGENT v2 — 5 agentes + pair selector + multi-TF
Novo: Order Block, Breaker Block, horários de pico, volatilidade ajustável
"""
import numpy as np
from datetime import datetime, timezone

class VolatilidadeAgent:
    """Analisa volatilidade e ajusta parâmetros de risco automaticamente."""
    
    def analyze(self, highs, lows, closes, pip_size):
        n = len(closes)
        if n < 20: return 'NEUTRAL', 0, {'regime': 'DESCONHECIDO', 'atr_pct': 0, 'sl_recommend': 0.5}
        
        # ATR(14) como % do preço
        tr = [max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1])) 
              for i in range(1, min(20, n))]
        atr = sum(tr[-14:]) / len(tr[-14:]) if len(tr) >= 14 else sum(tr) / len(tr)
        atr_pct = atr / closes[-1] * 100
        
        # Classificar regime (thresholds ajustados para crypto)
        if atr_pct > 0.6:
            regime, conf, sl_rec = 'ALTA_VOL', 85, 0.6
        elif atr_pct > 0.20:
            regime, conf, sl_rec = 'MEDIA_VOL', 60, 0.3
        elif atr_pct > 0.08:
            regime, conf, sl_rec = 'NORMAL', 40, 0.2
        else:
            regime, conf, sl_rec = 'BAIXA_VOL', 20, 0.12
        
        return 'NEUTRAL', conf, {
            'regime': regime, 'atr_pct': round(atr_pct, 3),
            'sl_recommend': sl_rec,
            'tp_recommend': sl_rec * 3
        }


class TendenciaAgent:
    """Analisa tendência hierárquica: M15 direção, M5 confirmação, M1 entrada."""
    
    def __init__(self):
        self.timeframes = {
            'M15': {'period': 50, 'weight': 2.0, 'min_conf': 60},
            'M5':  {'period': 20, 'weight': 1.5, 'min_conf': 45},
            'M1':  {'period': 10, 'weight': 1.0, 'min_conf': 0},
        }
    
    def analyze_tf(self, closes, period, label):
        """Analisa um timeframe individual."""
        if len(closes) < period * 2: return 'NEUTRAL', 0, []
        
        score = 0
        signals = []
        
        # EMAs
        ema_fast = sum(closes[-period//2:]) / (period//2)
        ema_slow = sum(closes[-period:]) / period
        
        if closes[-1] > ema_fast > ema_slow:
            score += 40 if label == 'M15' else 30 if label == 'M5' else 20
            signals.append(f'{label}↑')
            direction = 'BUY'
        elif closes[-1] < ema_fast < ema_slow:
            score += 40 if label == 'M15' else 30 if label == 'M5' else 20
            signals.append(f'{label}↓')
            direction = 'SELL'
        else:
            direction = 'NEUTRAL'
        
        # Momentum
        recent = sum(closes[-period//4:]) / (period//4)
        prior = sum(closes[-period//2:-period//4]) / (period//4)
        mom = (recent - prior) / prior * 100
        
        if abs(mom) > 0.1:
            score += min(abs(mom) * 3, 25)
            if mom > 0 and direction != 'SELL':
                direction = 'BUY'
                signals.append(f'M+{mom:.2f}%')
            elif mom < 0 and direction != 'BUY':
                direction = 'SELL'
                signals.append(f'M{mom:.2f}%')
        
        return direction, min(score, 100), signals
    
    def analyze(self, highs, lows, closes):
        """Análise multi-TF hierárquica."""
        if len(closes) < 100: return 'NEUTRAL', 0, ''
        
        results = {}
        final_direction = None
        total_score = 0
        all_signals = []
        
        # M15 primeiro (define direção principal)
        m15_dir, m15_score, m15_sig = self.analyze_tf(closes, 50, 'M15')
        results['M15'] = (m15_dir, m15_score * 2.0)
        all_signals.extend(m15_sig)
        
        if m15_dir == 'NEUTRAL':
            return 'NEUTRAL', 0, 'M15 sem direção'
        
        # M5 confirma
        m5_dir, m5_score, m5_sig = self.analyze_tf(closes[-80:] if len(closes) >= 80 else closes, 20, 'M5')
        results['M5'] = (m5_dir, m5_score * 1.5)
        all_signals.extend(m5_sig)
        
        if m5_dir != m15_dir and m5_dir != 'NEUTRAL':
            # M5 discorda de M15 — sinal fraco
            total_score = m15_score * 1.5  # só M15 conta
        else:
            total_score = m15_score * 2.0 + m5_score * 1.5
        
        # M1 timing
        m1_dir, m1_score, m1_sig = self.analyze_tf(closes[-40:] if len(closes) >= 40 else closes, 10, 'M1')
        results['M1'] = (m1_dir, m1_score * 1.0)
        all_signals.extend(m1_sig)
        
        if m1_dir == m15_dir:
            total_score += m1_score * 1.2  # bônus timing
            all_signals.append('⏱M1')
        
        # Suporte/Resistência nas últimas 100 velas
        window = closes[-100:] if len(closes) >= 100 else closes
        hh, ll = max(window), min(window)
        pos = (closes[-1] - ll) / (hh - ll) if hh > ll else 0.5
        
        if m15_dir == 'BUY' and pos < 0.45:
            total_score += 20; all_signals.append('Suporte')
        elif m15_dir == 'SELL' and pos > 0.55:
            total_score += 20; all_signals.append('Rstência')
        elif m15_dir == 'BUY' and pos > 0.80:
            total_score -= 15  # comprar no topo é ruim
        elif m15_dir == 'SELL' and pos < 0.20:
            total_score -= 15  # vender no fundo é ruim
        
        total_score = max(0, total_score)
        if total_score >= 60:
            return m15_dir, total_score, '|'.join(all_signals)
        return 'NEUTRAL', total_score, f'Score={total_score:.0f}|' + '|'.join(all_signals)


class PadraoAgent:
    """Detecta FVG, Order Block e Breaker Block."""
    
    def find_fvg(self, highs, lows, closes, direction, pip_pct=0.02):
        """Encontra FVG com quality scoring — apenas FVGs recentes (últimas 200 velas)."""
        n = len(highs)
        if n < 10: return None, 0
        
        best, best_score = None, 0
        # Só busca nos últimos 200 candles + os mais recentes primeiro
        search_start = max(6, n - 200)
        
        for i in range(n-2, search_start, -1):  # mais recentes primeiro
            # FVG bullish (gap para cima)
            if direction == 'BUY' and lows[i] > highs[i-2]:
                gap_pct = (lows[i] - highs[i-2]) / closes[i] * 100
                if gap_pct < pip_pct: continue
                
                score = 50  # base
                
                # Premium/Discount (Fibonacci 0.5)
                window_h = max(highs[max(0,i-50):i+1])
                window_l = min(lows[max(0,i-50):i+1])
                eq = (window_h + window_l) / 2
                if closes[i] < eq: score += 30  # discount → melhor compra
                elif closes[i] < closes[i] * 1.01: score += 15  # próximo ao EQ
                
                # Gap size bonus
                score += min(gap_pct / pip_pct * 5, 20)
                
                # Volume do candle
                body = abs(closes[i] - closes[max(0,i-1)])
                avg_body = np.mean([abs(closes[j]-closes[j-1]) for j in range(max(0,i-20), i)])
                if body > avg_body * 1.4: score += 15
                
                # Não mitigado nas últimas velas
                mitigated = any(lows[j] <= highs[i-2] for j in range(i+1, min(i+15, n)))
                if not mitigated: score += 10
                
                if score > best_score:
                    best_score = score
                    best = {'type': 'FVG', 'entry': closes[i], 'direction': 'BUY',
                            'idx': i, 'gap_pct': round(gap_pct, 3), 'quality': score}
            
            # FVG bearish
            elif direction == 'SELL' and highs[i] < lows[i-2]:
                gap_pct = (lows[i-2] - highs[i]) / closes[i] * 100
                if gap_pct < pip_pct: continue
                
                score = 50
                
                window_h = max(highs[max(0,i-50):i+1])
                window_l = min(lows[max(0,i-50):i+1])
                eq = (window_h + window_l) / 2
                if closes[i] > eq: score += 30
                elif closes[i] > closes[i] * 0.99: score += 15
                
                score += min(gap_pct / pip_pct * 5, 20)
                
                body = abs(closes[i] - closes[max(0,i-1)])
                avg_body = np.mean([abs(closes[j]-closes[j-1]) for j in range(max(0,i-20), i)])
                if body > avg_body * 1.4: score += 15
                
                mitigated = any(highs[j] >= lows[i-2] for j in range(i+1, min(i+15, n)))
                if not mitigated: score += 10
                
                if score > best_score:
                    best_score = score
                    best = {'type': 'FVG', 'entry': closes[i], 'direction': 'SELL',
                            'idx': i, 'gap_pct': round(gap_pct, 3), 'quality': score}
        
        return best, best_score
    
    def find_order_block(self, highs, lows, closes, direction):
        """Encontra Order Block: última vela oposta antes do impulso."""
        n = len(highs)
        if n < 5: return None, 0
        
        # Procurar impulso seguido de pullback ao OB
        for i in range(n-4, 4, -1):
            if direction == 'BUY':
                # Impulso: candle forte de alta
                impulse = closes[i] - closes[i-1]
                if impulse <= 0: continue
                # Pullback: candle seguinte toca área da abertura do impulso
                if lows[i+1] <= closes[i-1] * 1.001 and lows[i+1] >= closes[i-1] * 0.997:
                    return {'type': 'OB', 'entry': closes[i-1], 'direction': 'BUY',
                            'idx': i, 'quality': 60}, 60
            else:
                impulse = closes[i-1] - closes[i]
                if impulse <= 0: continue
                if highs[i+1] >= closes[i-1] * 0.999 and highs[i+1] <= closes[i-1] * 1.003:
                    return {'type': 'OB', 'entry': closes[i-1], 'direction': 'SELL',
                            'idx': i, 'quality': 60}, 60
        
        return None, 0
    
    def analyze(self, highs, lows, closes, opens, direction, pip_size):
        """Detecta o melhor padrão disponível."""
        if len(closes) < 10: return 'NEUTRAL', 0, {}
        
        # 1. FVG (prioridade)
        fvg, fvg_score = self.find_fvg(highs, lows, closes, direction)
        
        # 2. Order Block (se FVG não for bom)
        ob, ob_score = None, 0
        if not fvg or fvg_score < 60:
            ob, ob_score = self.find_order_block(highs, lows, closes, direction)
        
        # Melhor padrão
        if fvg and fvg_score >= 60:
            return direction, fvg_score, fvg
        elif ob and ob_score >= 55:
            return direction, ob_score, ob
        elif fvg:
            return direction, fvg_score, fvg
        
        return 'NEUTRAL', 0, {}


class SessaoAgent:
    """Analisa horário de pico de volume crypto."""
    
    # Horários de maior volume (UTC): NY open, London open, Asia open
    HIGH_VOL_HOURS = {
        'NY_OPEN':   list(range(13, 21)),  # 13-20 UTC
        'ASIA_OPEN': list(range(0, 8)),     # 0-7 UTC
        'LONDON':    list(range(8, 13)),    # 8-12 UTC
    }
    
    def analyze(self):
        """Verifica se estamos em horário de alta liquidez."""
        hour = datetime.now(timezone.utc).hour
        
        if hour in self.HIGH_VOL_HOURS['NY_OPEN']:
            return 'BUY', 75, 'NY Open — alta liquidez'
        elif hour in self.HIGH_VOL_HOURS['ASIA_OPEN']:
            return 'BUY', 60, 'Asia Open — liquidez média'
        elif hour in self.HIGH_VOL_HOURS['LONDON']:
            return 'BUY', 55, 'London — transição'
        else:
            return 'NEUTRAL', 25, 'Fora de pico — baixa liquidez'
    
    def get_hour_bonus(self):
        """Bônus de confiança por horário."""
        hour = datetime.now(timezone.utc).hour
        if hour in self.HIGH_VOL_HOURS['NY_OPEN']:
            return 1.0  # confiança total
        elif hour in self.HIGH_VOL_HOURS['ASIA_OPEN']:
            return 0.85
        elif hour in self.HIGH_VOL_HOURS['LONDON']:
            return 0.7
        else:
            return 0.5  # metade da confiança fora de pico


class FluxoAgent:
    """Analisa correlação BTC/Altcoins e dominância."""
    
    def analyze(self, pair, btc_change_pct=None):
        if pair == 'BTCUSD':
            return 'NEUTRAL', 50, 'BTC par base'
        
        if btc_change_pct is None:
            return 'NEUTRAL', 20, 'Sem dados BTC'
        
        abs_chg = abs(btc_change_pct)
        direction = 'BUY' if btc_change_pct > 0 else 'SELL'
        
        if abs_chg > 4.0:
            return direction, 85, f'BTC {btc_change_pct:+.1f}% — arrastando alts'
        elif abs_chg > 2.0:
            return direction, 65, f'BTC {btc_change_pct:+.1f}% — influenciando'
        elif abs_chg > 1.0:
            return direction, 45, f'BTC {btc_change_pct:+.1f}% — leve'
        elif abs_chg > 0.3:
            return direction, 30, f'BTC {btc_change_pct:+.1f}% — fraco'
        else:
            return 'NEUTRAL', 40, 'BTC estável — alts livres'


class CryptoConfluencia:
    """Integra 5 agentes (v2) com multi-TF e pair selector."""
    
    def __init__(self):
        self.volatilidade = VolatilidadeAgent()
        self.tendencia = TendenciaAgent()
        self.padrao = PadraoAgent()
        self.sessao = SessaoAgent()
        self.fluxo = FluxoAgent()
        
        # Pesos calibrados para crypto
        self.weights = {
            'volatilidade': 1.0,
            'tendencia': 2.0,
            'padrao': 1.8,
            'sessao': 0.7,
            'fluxo': 1.2
        }
    
    def analyze(self, pair, highs, lows, closes, opens, daily_bias, pip_size,
                btc_change_pct=None, min_confidence=40):
        """Análise completa com todos os agentes."""
        
        # Volatilidade (regime + SL recomendado)
        v_vote, v_conf, v_info = self.volatilidade.analyze(highs, lows, closes, pip_size)
        votes = {
            'volatilidade': {
                'vote': v_vote, 
                'conf': v_conf * self.weights['volatilidade'],
                'info': v_info
            }
        }
        
        # Se volatilidade extremamente baixa (< 0.05% ATR), nem continua
        if v_info.get('regime') == 'BAIXA_VOL' and v_info.get('atr_pct', 0) < 0.05:
            return 'NEUTRAL', 0, None, v_info
        
        # Tendência multi-TF (principal)
        t_vote, t_conf, t_msg = self.tendencia.analyze(highs, lows, closes)
        votes['tendencia'] = {
            'vote': t_vote,
            'conf': t_conf * self.weights['tendencia'],
            'msg': t_msg
        }
        
        if t_vote == 'NEUTRAL':
            return 'NEUTRAL', 0, None, v_info
        
        # Padrão (FVG, OB)
        p_vote, p_conf, p_sig = self.padrao.analyze(highs, lows, closes, opens, t_vote, pip_size)
        votes['padrao'] = {
            'vote': p_vote,
            'conf': p_conf * self.weights['padrao'],
            'sig': p_sig
        }
        
        # Se não encontrou padrão, não entra
        if not p_sig:
            return 'NEUTRAL', t_conf * 0.3, None, v_info
        
        # Sessão (horário)
        s_vote, s_conf, s_msg = self.sessao.analyze()
        hour_bonus = self.sessao.get_hour_bonus()
        votes['sessao'] = {
            'vote': s_vote,
            'conf': s_conf * self.weights['sessao'] * hour_bonus,
            'msg': s_msg
        }
        
        # Fluxo BTC
        f_vote, f_conf, f_msg = self.fluxo.analyze(pair, btc_change_pct)
        votes['fluxo'] = {
            'vote': f_vote,
            'conf': f_conf * self.weights['fluxo'],
            'msg': f_msg
        }
        
        # 🔥 Votação ponderada
        buy_score = sum(v['conf'] for v in votes.values() if v['vote'] == 'BUY')
        sell_score = sum(v['conf'] for v in votes.values() if v['vote'] == 'SELL')
        total = sum(v['conf'] for v in votes.values())
        conf = max(buy_score, sell_score) / max(total, 1) * 100
        
        # Aplicar hour bonus
        conf = conf * (0.7 + hour_bonus * 0.3)
        
        # Decisão final
        if buy_score > sell_score and conf >= min_confidence:
            return 'BUY', conf, p_sig, v_info
        elif sell_score > buy_score and conf >= min_confidence:
            return 'SELL', conf, p_sig, v_info
        
        return 'NEUTRAL', conf, None, v_info
    
    def analyze_simple(self, pair, highs, lows, closes, opens, daily_bias, pip_size,
                       btc_change_pct=None):
        """Versão simplificada que retorna (decision, confidence, signal)."""
        decision, conf, signal, info = self.analyze(
            pair, highs, lows, closes, opens, daily_bias, pip_size, btc_change_pct
        )
        return decision, conf, signal
