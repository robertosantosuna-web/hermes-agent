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
    """Tendência multi-TF: M15 principal + H1/M5 bônus + M1 timing."""
    
    def _aggregate(self, closes, period):
        if len(closes) < period: return None
        n = len(closes) // period
        if n < 2: return None
        return np.array([closes[i*period:(i+1)*period][-1] for i in range(n)])
    
    def analyze_tf(self, closes, period, label):
        if len(closes) < period * 2: return 'NEUTRAL', 0, []
        half = period // 2
        ema_fast = sum(closes[-half:]) / half
        ema_slow = sum(closes[-period:]) / period
        if closes[-1] > ema_fast > ema_slow:
            return 'BUY', 35, [f'{label}↑']
        elif closes[-1] < ema_fast < ema_slow:
            return 'SELL', 35, [f'{label}↓']
        return 'NEUTRAL', 0, []
    
    def analyze(self, highs, lows, closes):
        if len(closes) < 200: return 'NEUTRAL', 0, ''
        
        # M15 principal (período reduzido: 30 velas M1 = 30 min)
        m15_dir, m15_score, m15_sig = self.analyze_tf(closes, 30, 'M15')
        if m15_dir == 'NEUTRAL':
            # Fallback: usar H1 se M15 neutro
            h1_c = self._aggregate(closes, 60)
            if h1_c is not None and len(h1_c) >= 10:
                h1_dir, h1_score, h1_sig = self.analyze_tf(h1_c, 24, 'H1')
                if h1_dir != 'NEUTRAL':
                    m15_dir, m15_score, m15_sig = h1_dir, h1_score, h1_sig
                else:
                    return 'NEUTRAL', 0, 'M15+H1 neutros'
        
        # H1 bônus
        h1_c = self._aggregate(closes, 60)
        h1_dir = 'NEUTRAL'
        if h1_c is not None and len(h1_c) >= 10:
            h1_dir, _, _ = self.analyze_tf(h1_c, 24, 'H1')
        
        # M5 confirmação (bônus, não gate)
        m5_dir, m5_score, m5_sig = self.analyze_tf(closes[-80:], 20, 'M5')
        
        total_score = m15_score
        signals = m15_sig
        
        if m5_dir == m15_dir:
            total_score += m5_score; signals += m5_sig; signals.append('✅M5')
        # M5 divergindo não bloqueia, só não dá bônus
        
        if h1_dir == m15_dir: total_score += 20; signals.append('✅H1')
        if m5_dir == m15_dir: total_score += 10; signals.append('✅M5')
        
        # M1 timing
        m1_dir, m1_score, _ = self.analyze_tf(closes[-40:], 10, 'M1')
        if m1_dir == m15_dir: total_score += 10; signals.append('⏱M1')
        
        # S/R
        w = closes[-200:]
        hh, ll = max(w), min(w)
        pos = (closes[-1] - ll) / (hh - ll) if hh > ll else 0.5
        if m15_dir == 'BUY' and pos < 0.50:
            total_score += 15; signals.append('Discount')
        elif m15_dir == 'SELL' and pos > 0.50:
            total_score += 15; signals.append('Premium')
        
        if total_score >= 55:
            return m15_dir, total_score, '|'.join(signals)
        return 'NEUTRAL', total_score, f'S={total_score}'


class PadraoAgent:
    """Padrões ICT avançados: OB com Fibonacci, Breaker, Market Structure Gate."""
    
    def __init__(self):
        self.detector = AdvancedPatternDetector()
        self.last_signal_idx = -50  # deduplicação: não repetir mesmo OB
    
    def analyze(self, highs, lows, closes, opens, direction, pip_size, volumes=None, daily_levels=None):
        if len(closes) < 30: return 'NEUTRAL', 0, {}
        
        best, score = self.detector.find_best_pattern(highs, lows, closes, opens, direction, volumes, daily_levels)
        
        if best and score >= 50:
            # Deduplicação: não repetir mesmo OB
            sig_idx = best.get('idx', 0)
            if abs(sig_idx - self.last_signal_idx) < 20:
                return 'NEUTRAL', 0, {}
            self.last_signal_idx = sig_idx
            
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
                btc_change_pct=None, min_confidence=55, volumes=None, daily_levels=None):
        
        # Gate 1: Volatilidade
        v_vote, v_conf, v_info = self.volatilidade.analyze(highs, lows, closes, pip_size)
        
        # Gate 2: Tendência — se todos timeframes neutros, modo scalper com IR>=1.0
        t_vote, t_conf, t_msg = self.tendencia.analyze(highs, lows, closes)
        
        # Modo scalper: se tendência NEUTRAL mas IR muito forte, permitir
        scalper_mode = False
        if t_vote == 'NEUTRAL':
            # Verificar se há OB com IR>=1.0 antes de desistir
            p_dir, p_conf_test, p_sig_test = self.padrao.analyze(
                highs, lows, closes, opens, 'BUY', pip_size, volumes, daily_levels)
            if not p_sig_test or p_sig_test.get('impulse_ratio', 0) < 1.0:
                p_dir, p_conf_test, p_sig_test = self.padrao.analyze(
                    highs, lows, closes, opens, 'SELL', pip_size, volumes, daily_levels)
            if p_sig_test and p_sig_test.get('impulse_ratio', 0) >= 1.0:
                scalper_mode = True
                t_vote = p_dir
                t_conf = 30  # confiança reduzida
                self.padrao.last_signal_idx = -50  # reset para não bloquear Gate 3
            else:
                return 'NEUTRAL', 0, None, v_info
        
        # Gate 3: Padrão (OB com quality≥50 + impulse ratio≥0.8)
        p_vote, p_conf, p_sig = self.padrao.analyze(highs, lows, closes, opens, t_vote, pip_size, volumes, daily_levels)
        if not p_sig or p_sig.get('quality', 0) < 50:
            return 'NEUTRAL', 0, None, v_info
        
        # ⚡ GATE: Impulse Ratio mínimo (fator mais discriminativo: +7.9pp WR)
        impulse_ratio = p_sig.get('impulse_ratio', 0)
        if impulse_ratio < 0.8:
            return 'NEUTRAL', 0, None, v_info
        
        # ⚡ GATE v10: Backtest realista — filtros por par+direção
        # SELL = 60-83% WR → mantém IR≥0.8
        # BUY varia muito por par:
        #   BTCUSD BUY = 39% WR (TÓXICO) → BLOQUEADO totalmente
        #   DOGEUSD BUY = 49% WR → IR≥1.5
        #   BNBUSD BUY = 56% WR → IR≥1.3
        #   ETHUSD BUY = 70% WR → IR≥1.2
        if t_vote == 'BUY':
            if pair == 'BTCUSD':
                return 'NEUTRAL', 0, None, v_info  # Bloqueado — 39% WR
            elif pair == 'DOGEUSD':
                if impulse_ratio < 1.5:
                    return 'NEUTRAL', 0, None, v_info
            elif pair == 'BNBUSD':
                if impulse_ratio < 1.3:
                    return 'NEUTRAL', 0, None, v_info
            else:  # ETHUSD e outros
                if impulse_ratio < 1.2:
                    return 'NEUTRAL', 0, None, v_info
        
        # ⚡ GATE: Não operar em RANGE a menos que IR seja muito forte (>=1.0)
        ms_structure = p_sig.get('market_structure', '')
        if ms_structure == 'RANGE' and impulse_ratio < 1.0:
            return 'NEUTRAL', 0, None, v_info
        
        # Bônus por Market Structure alinhada
        if ms_structure == 'BULLISH' and t_vote == 'BUY':
            p_conf += 25
        elif ms_structure == 'BEARISH' and t_vote == 'SELL':
            p_conf += 30  # BEARISH é mais confiável (79.4% vs 64.4%)
        elif ms_structure == 'CHoCH':
            choch = p_sig.get('choch', {})
            if isinstance(choch, dict) and choch.get('type') == t_vote:
                p_conf += 35
        
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
