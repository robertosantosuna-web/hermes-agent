#!/usr/bin/env python3
"""
SISTEMA MULTI-AGENTE DE ANÁLISE FOREX
Cada agente é especialista em um aspecto da análise.
Votos combinados determinam entrada.

Agentes:
  1. PERFIL      — perfil do par (volatilidade, liquidez, horários ótimos)
  2. SESSÃO      — análise da sessão asiática como preditora
  3. ESTRUTURA   — CRT, Order Block, Swing Points
  4. PADRÃO      — FVG com scoring (premium/discount, gap size)
  5. CONFLUÊNCIA — integra todos os votos
"""
import numpy as np
from datetime import datetime, timezone

class PerfilAgent:
    """Analisa o perfil individual de cada par."""
    
    # Perfis por par (baseado em backtest 30 dias)
    PERFIS = {
        'EURUSD': {'volatilidade': 'media', 'liquidez': 'alta', 
                    'melhor_sessao': 'London', 'asia_wr': 0.15, 'london_wr': 0.28},
        'GBPUSD': {'volatilidade': 'alta', 'liquidez': 'alta',
                    'melhor_sessao': 'London', 'asia_wr': 0.10, 'london_wr': 0.25},
        'USDJPY': {'volatilidade': 'media', 'liquidez': 'alta',
                    'melhor_sessao': 'Asia+London', 'asia_wr': 0.35, 'london_wr': 0.20},
        'GBPJPY': {'volatilidade': 'alta', 'liquidez': 'media',
                    'melhor_sessao': 'London', 'asia_wr': 0.12, 'london_wr': 0.22},
        'EURJPY': {'volatilidade': 'media', 'liquidez': 'media',
                    'melhor_sessao': 'Asia+London', 'asia_wr': 0.20, 'london_wr': 0.25},
        'USDCAD': {'volatilidade': 'baixa', 'liquidez': 'baixa',
                    'melhor_sessao': 'NY', 'asia_wr': 0.05, 'london_wr': 0.15},
        'XAUUSD': {'volatilidade': 'muito_alta', 'liquidez': 'alta',
                    'melhor_sessao': 'London+NY', 'asia_wr': 0.40, 'london_wr': 0.45},
    }
    
    def analyze(self, pair, hour_utc):
        """Retorna voto: BUY, SELL, ou NEUTRAL + score de confiança 0-100."""
        perfil = self.PERFIS.get(pair, {})
        
        # Determinar sessão atual
        if 0 <= hour_utc < 7:
            sessao = 'Asia'
            wr_ref = perfil.get('asia_wr', 0.15)
        elif 7 <= hour_utc < 15:
            sessao = 'London'
            wr_ref = perfil.get('london_wr', 0.25)
        else:
            sessao = 'NY'
            wr_ref = perfil.get('london_wr', 0.20)
        
        # Se WR da sessão é muito baixa, recomendar NEUTRAL
        if wr_ref < 0.12:
            return 'NEUTRAL', 0, f'Sessão {sessao} com WR histórico {wr_ref:.0%} — evitar'
        
        # Confiança baseada no perfil do par
        confianca = int(wr_ref * 100)
        return 'NEUTRAL', confianca, f'Perfil {pair}: {sessao} (WR~{wr_ref:.0%})'
    
    def get_best_session(self, pair):
        """Retorna melhor sessão para operar o par."""
        p = self.PERFIS.get(pair, {})
        return p.get('melhor_sessao', 'London')


class SessaoAgent:
    """Analisa a sessão asiática como preditora dos próximos mercados."""
    
    def analyze(self, highs, lows, closes, pip_size):
        """
        Se a Ásia foi lateralizada (range estreito), London tende a explodir.
        Se a Ásia teve tendência, London tende a continuar ou reverter na abertura.
        """
        n = len(closes)
        if n < 40:  # ~10h de M1 (sessão asiática completa)
            return 'NEUTRAL', 0, 'Dados insuficientes da Ásia'
        
        # Dividir: candles da Ásia (últimas 6-8h) vs resto
        asia_candles = min(240, n)  # ~4h de M1 para Ásia
        asia_high = max(highs[-asia_candles:])
        asia_low = min(lows[-asia_candles:])
        asia_range = (asia_high - asia_low) / pip_size
        
        # Range pré-Asia
        pre_asia_candles = min(240, n - asia_candles)
        if pre_asia_candles < 20:
            return 'NEUTRAL', 0, 'Sem referência pré-Asia'
        
        pre_high = max(highs[-asia_candles-pre_asia_candles:-asia_candles])
        pre_low = min(lows[-asia_candles-pre_asia_candles:-asia_candles])
        pre_range = (pre_high - pre_low) / pip_size if (pre_high - pre_low) > 0 else asia_range
        
        # Range asiático vs pré-asiático
        ratio = asia_range / max(pre_range, 1)
        
        if ratio < 0.5:
            # Ásia contraiu → London deve expandir (breakout)
            return 'NEUTRAL', 70, f'Ásia contraiu ({asia_range:.0f}p vs {pre_range:.0f}p) → London breakout provável'
        elif ratio > 1.5:
            # Ásia expandiu → London pode continuar
            asia_direction = closes[-1] - closes[-asia_candles]
            if asia_direction > 0:
                return 'BUY', 40, f'Ásia expandiu altista ({asia_range:.0f}p) → possibilidade continuação'
            else:
                return 'SELL', 40, f'Ásia expandiu baixista ({asia_range:.0f}p) → possibilidade continuação'
        else:
            return 'NEUTRAL', 20, f'Ásia normal (ratio={ratio:.1f})'


class EstruturaAgent:
    """Analisa CRT, Order Blocks, e Swing Points."""
    
    def analyze(self, highs, lows, closes, daily_bias):
        """Detecta CRT setup e Order Blocks na direção do daily bias."""
        n = len(closes)
        if n < 20:
            return 'NEUTRAL', 0, ''
        
        score = 0
        signals = []
        
        # 1. CRT Detection (H1)
        crt = self._detect_crt(highs, lows, closes)
        if crt and crt['bias'] == daily_bias:
            score += 40
            signals.append('CRT')
        
        # 2. Order Block
        ob = self._detect_order_block(highs, lows, closes, daily_bias)
        if ob:
            score += 30
            signals.append('OB')
        
        # 3. Swing structure (Higher High/Low ou Lower High/Low)
        if self._is_structured(highs, lows, closes, daily_bias):
            score += 30
            signals.append('SWING')
        
        if score >= 40:
            return daily_bias, score, '+'.join(signals)
        return 'NEUTRAL', score, f'Estrutura fraca ({score}pts)'
    
    def _detect_crt(self, highs, lows, closes):
        """CRT: candle grande + sweep + fecha dentro."""
        if len(closes) < 22: return None
        ranges = [highs[i]-lows[i] for i in range(-22, -2)]
        if not ranges: return None
        avg = sum(ranges)/len(ranges)
        crt_h, crt_l = highs[-2], lows[-2]
        crt_range = crt_h - crt_l
        if crt_range < avg * 1.3: return None
        crt_close = closes[-2]
        sw_h, sw_l, sw_c = highs[-1], lows[-1], closes[-1]
        crt_bull = crt_close > (crt_l + crt_range*0.5)
        crt_bear = crt_close < (crt_l + crt_range*0.5)
        if crt_bear and sw_l < crt_l and sw_c > crt_l:
            return {'bias': 'BUY', 'sl': crt_l - crt_range*0.2}
        if crt_bull and sw_h > crt_h and sw_c < crt_h:
            return {'bias': 'SELL', 'sl': crt_h + crt_range*0.2}
        return None
    
    def _detect_order_block(self, highs, lows, closes, direction):
        """OB: último candle oposto antes do rompimento."""
        n = len(closes)
        if n < 5: return None
        # Simplificado: procura candle oposto nas últimas 5 velas
        for i in range(n-2, max(n-7, -1), -1):
            if direction == 'BUY' and closes[i] < closes[i-1] and closes[i] < closes[i-2]:
                return {'level': highs[i], 'idx': i}
            if direction == 'SELL' and closes[i] > closes[i-1] and closes[i] > closes[i-2]:
                return {'level': lows[i], 'idx': i}
        return None
    
    def _is_structured(self, highs, lows, closes, direction):
        """Verifica se o mercado está fazendo HH/HL ou LH/LL."""
        n = len(closes)
        if n < 10: return False
        # Encontrar swings simplificados
        mid = n // 2
        if direction == 'BUY':
            return highs[-1] > highs[-mid] and lows[-1] > lows[-mid]
        else:
            return highs[-1] < highs[-mid] and lows[-1] < lows[-mid]


class PadraoAgent:
    """Analisa FVG com sistema de scoring (premium/discount, gap, mitigação)."""
    
    def analyze(self, highs, lows, closes, direction, pip_size, is_metal=False):
        """Busca FVGs de qualidade no array."""
        from fvg_quality import is_fvg_valid
        
        n = len(closes)
        if n < 10:
            return 'NEUTRAL', 0, {}
        
        best_score = 0
        best_signal = None
        
        for i in range(6, n-1):
            if direction == 'BUY' and lows[i] > highs[i-2]:
                valid, det = is_fvg_valid(highs, lows, closes, i, 'BUY', pip_size, is_metal, 35)
                if valid and det.get('score', 0) > best_score:
                    best_score = det['score']
                    best_signal = {'entry': closes[i], 'direction': 'BUY', 
                                   'idx': i, 'details': det}
            elif direction == 'SELL' and highs[i] < lows[i-2]:
                valid, det = is_fvg_valid(highs, lows, closes, i, 'SELL', pip_size, is_metal, 35)
                if valid and det.get('score', 0) > best_score:
                    best_score = det['score']
                    best_signal = {'entry': closes[i], 'direction': 'SELL',
                                   'idx': i, 'details': det}
        
        if best_signal:
            return direction, best_score, best_signal
        return 'NEUTRAL', 0, {}


class ConfluenciaAgent:
    """Integra votos de todos os agentes e decide entrada."""
    
    def __init__(self):
        self.perfil = PerfilAgent()
        self.sessao = SessaoAgent()
        self.estrutura = EstruturaAgent()
        self.padrao = PadraoAgent()
    
    def analyze(self, pair, highs_m1, lows_m1, closes_m1, daily_bias, pip_size, is_metal=False):
        """
        Análise completa multi-agente.
        Retorna: (decisão, confiança, sinal_dict)
          decisão: 'BUY', 'SELL', ou 'NEUTRAL'
          confiança: 0-100
          sinal_dict: entry, sl, tp, etc (None se NEUTRAL)
        """
        now_utc = datetime.now(timezone.utc).hour
        votes = {}
        
        # Agente 1: Perfil do par
        p_vote, p_conf, p_msg = self.perfil.analyze(pair, now_utc)
        votes['perfil'] = {'vote': p_vote, 'conf': p_conf, 'msg': p_msg}
        
        # Agente 2: Sessão asiática
        s_vote, s_conf, s_msg = self.sessao.analyze(highs_m1, lows_m1, closes_m1, pip_size)
        votes['sessao'] = {'vote': s_vote, 'conf': s_conf, 'msg': s_msg}
        
        # Agente 3: Estrutura (CRT + OB + Swing)
        e_vote, e_conf, e_msg = self.estrutura.analyze(highs_m1, lows_m1, closes_m1, daily_bias)
        votes['estrutura'] = {'vote': e_vote, 'conf': e_conf, 'msg': e_msg}
        
        # Agente 4: Padrão (FVG scoring)
        d_vote, d_conf, d_signal = self.padrao.analyze(highs_m1, lows_m1, closes_m1, daily_bias, pip_size, is_metal)
        votes['padrao'] = {'vote': d_vote, 'conf': d_conf, 'msg': f'FVG score={d_conf}'}
        
        # Contagem de votos
        buy_votes = sum(1 for v in votes.values() if v['vote'] == 'BUY')
        sell_votes = sum(1 for v in votes.values() if v['vote'] == 'SELL')
        total_conf = sum(v['conf'] for v in votes.values()) / len(votes)
        
        # Decisão: maioria + confiança mínima
        if buy_votes > sell_votes and total_conf >= 30:
            return 'BUY', total_conf, d_signal if d_signal else None
        elif sell_votes > buy_votes and total_conf >= 30:
            return 'SELL', total_conf, d_signal if d_signal else None
        else:
            return 'NEUTRAL', total_conf, None
    
    def get_vote_summary(self):
        """Retorna resumo dos votos para logging."""
        return {}  # implementado no analyze


# ═══ TESTE RÁPIDO ═══
if __name__ == '__main__':
    print("Sistema Multi-Agente inicializado.")
    print("Agentes: Perfil, Sessão, Estrutura, Padrão, Confluência")
    print("Pronto para integrar ao forex_bot_multi.py")
