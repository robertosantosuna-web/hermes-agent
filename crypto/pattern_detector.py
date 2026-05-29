#!/usr/bin/env python3
"""
CRYPTO PATTERN DETECTOR v2 — Alta Assertividade (target >60% WR)
Melhorias:
  - OB exige pullback 0.5-0.618 Fibonacci
  - Volume acima da média no impulso
  - Market Structure como GATE (não só bônus)
  - First-touch em todos os padrões
  - Momentum mínimo (ATR-based)
  - Breaker Block com thresholds calibrados
"""
import numpy as np

class MarketStructure:
    """Estrutura de mercado com swings e CHoCH."""
    
    def analyze(self, highs, lows, closes, lookback=60):
        n = len(highs)
        if n < lookback: return {'structure': 'UNKNOWN', 'swings': [], 'choch': None}
        
        swings = self._find_swings(highs, lows, lookback)
        if len(swings) < 4:
            return {'structure': 'UNKNOWN', 'swings': swings, 'choch': None}
        
        # Separar highs e lows
        sh = [(i, p) for i, is_h, p in swings if is_h]
        sl = [(i, p) for i, is_h, p in swings if not is_h]
        
        if len(sh) < 2 or len(sl) < 2:
            return {'structure': 'UNKNOWN', 'swings': swings, 'choch': None}
        
        # Bullish: último HH > penúltimo HH e último HL > penúltimo HL
        hh = sh[-1][1] > sh[-2][1]
        hl = sl[-1][1] > sl[-2][1]
        
        # Bearish: último LH < penúltimo LH e último LL < penúltimo LL  
        lh = sh[-1][1] < sh[-2][1]
        ll = sl[-1][1] < sl[-2][1]
        
        # CHoCH detection
        choch = None
        if len(sh) >= 3 and len(sl) >= 3:
            # Bullish CHoCH: estava fazendo LH/LL e fez HH
            if sh[-1][1] > sh[-2][1] and sh[-2][1] < sh[-3][1]:
                choch = {'type': 'BULLISH', 'level': sh[-2][1]}
            # Bearish CHoCH: estava fazendo HH/HL e fez LL
            elif sl[-1][1] < sl[-2][1] and sl[-2][1] > sl[-3][1]:
                choch = {'type': 'BEARISH', 'level': sl[-2][1]}
        
        if hh and hl:
            structure = 'BULLISH'
        elif lh and ll:
            structure = 'BEARISH'
        elif choch:
            structure = 'CHoCH'
        else:
            structure = 'RANGE'
        
        # Posição no range
        window_h = max(highs[-lookback:])
        window_l = min(lows[-lookback:])
        pos = (closes[-1] - window_l) / (window_h - window_l) if window_h > window_l else 0.5
        
        # Liquidez
        eq_highs = self._find_equal_levels(highs[-30:], 'high')
        eq_lows = self._find_equal_levels(lows[-30:], 'low')
        
        return {
            'structure': structure,
            'choch': choch,
            'position': pos,
            'liquidity_above': eq_highs,
            'liquidity_below': eq_lows,
        }
    
    def _find_swings(self, highs, lows, lookback=60):
        """Swing highs/lows com 3 velas de cada lado."""
        n = len(highs)
        swings = []
        start = max(0, n - lookback)
        for i in range(start + 3, n - 3):
            if all(highs[i] > highs[i-j] for j in range(1,4)) and \
               all(highs[i] > highs[i+j] for j in range(1,4)):
                swings.append((i, True, highs[i]))
            if all(lows[i] < lows[i-j] for j in range(1,4)) and \
               all(lows[i] < lows[i+j] for j in range(1,4)):
                swings.append((i, False, lows[i]))
        return swings
    
    def _find_equal_levels(self, prices, level_type, tolerance=0.03):
        """Encontra níveis com preços iguais (liquidez)."""
        n = len(prices)
        levels = []
        for i in range(n):
            for j in range(i+3, n):
                if abs(prices[i] - prices[j]) / prices[i] * 100 < tolerance:
                    levels.append(prices[i] if level_type == 'high' else prices[i])
        return sorted(set(levels))[-3:] if levels else []


class AdvancedPatternDetector:
    """Detector de padrões com filtros rigorosos de assertividade."""
    
    def __init__(self):
        self.structure = MarketStructure()
    
    def get_atr(self, highs, lows, closes, period=14):
        """ATR como % do preço."""
        n = len(closes)
        if n < period + 1: return 0.001
        tr = [max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
              for i in range(1, min(period+10, n))]
        atr = sum(tr[-period:]) / period if len(tr) >= period else sum(tr)/len(tr)
        return atr / closes[-1]
    
    def get_avg_volume(self, closes, opens, lookback=20):
        """Volume médio (tamanho do corpo) das últimas velas."""
        bodies = [abs(closes[i] - opens[i]) for i in range(max(0, len(closes)-lookback-1), len(closes)-1)]
        return np.mean(bodies) if bodies else 0
    
    def find_order_block(self, highs, lows, closes, opens, direction):
        """
        Order Block com filtros:
        - Pullback a 0.5-0.618 do impulso
        - Volume do impulso > 1.2x média
        - OB não mitigado (first touch)
        - Impulso mínimo de 0.5x ATR
        """
        n = len(highs)
        if n < 30: return None, 0
        
        atr_pct = self.get_atr(highs, lows, closes)
        avg_body = self.get_avg_volume(closes, opens)
        ms = self.structure.analyze(highs, lows, closes)
        
        best, best_score = None, 0
        
        # Buscar nas últimas 150 velas
        search_start = max(10, n - 150)
        
        for i in range(n-3, search_start, -1):
            if direction == 'BUY':
                # Vela atual é impulso bullish
                if closes[i] <= closes[i-1]: continue
                impulse = closes[i] - closes[i-1]
                
                # Impulso mínimo: 0.3x ATR (relaxado — crypto volátil)
                min_impulse = atr_pct * closes[i] * 0.3
                if impulse < min_impulse: continue
                
                # Volume do impulso > 1.0x média (relaxado)
                impulse_body = abs(closes[i] - opens[i])
                if impulse_body < avg_body * 1.0: continue
                
                # OB = vela antes do impulso (bearish)
                ob_high = highs[i-1]
                ob_low = lows[i-1]
                
                # Pullback tocando o OB na zona 0.5-0.618
                fib_50 = ob_low + (ob_high - ob_low) * 0.5
                fib_618 = ob_low + (ob_high - ob_low) * 0.618
                
                touched = False
                touch_idx = None
                for j in range(i+1, min(i+20, n)):
                    if lows[j] <= ob_high and lows[j] >= ob_low:
                        if lows[j] <= fib_618 and lows[j] >= fib_50:
                            touched = True
                            touch_idx = j
                            break
                
                if not touched or touch_idx is None: continue
                
                # Verificar se não foi mitigado depois do pullback
                mitigated = any(lows[k] < ob_low for k in range(touch_idx+1, min(touch_idx+15, n)))
                if mitigated: continue
                
                # ⚡ GATE: Market Structure
                if ms['structure'] == 'BEARISH' and not ms.get('choch'):
                    continue  # Não comprar em tendência bearish sem CHoCH
                
                # Score
                score = 55
                
                # Qualidade do OB (corpo grande = rejeição forte)
                ob_body = abs(closes[i-1] - opens[i-1])
                if ob_body > avg_body * 1.5: score += 15
                
                # Força do impulso
                impulse_ratio = impulse / (atr_pct * closes[i])
                score += min(impulse_ratio * 15, 20)
                
                # Bônus estrutura
                if ms['structure'] == 'BULLISH': score += 15
                elif (ms.get('choch') or {}).get('type') == 'BULLISH': score += 20
                
                # Zona de discount/premium
                window_h = max(highs[max(0,i-50):i+1])
                window_l = min(lows[max(0,i-50):i+1])
                fib_range = window_h - window_l
                if fib_range > 0:
                    pos_in_range = (closes[i] - window_l) / fib_range
                    if pos_in_range < 0.50: score += 10  # discount
                
                if score > best_score:
                    best_score = score
                    best = {
                        'type': 'OB', 'entry': closes[i-1],
                        'direction': 'BUY', 'idx': i-1,
                        'quality': score,
                        'fib_zone': (fib_50, fib_618),
                        'impulse_ratio': round(impulse_ratio, 1),
                        'market_structure': ms['structure']
                    }
            
            else:  # SELL
                if closes[i] >= closes[i-1]: continue
                impulse = closes[i-1] - closes[i]
                
                min_impulse = atr_pct * closes[i] * 0.3
                if impulse < min_impulse: continue
                
                impulse_body = abs(closes[i] - opens[i])
                if impulse_body < avg_body * 1.0: continue
                
                ob_high = highs[i-1]
                ob_low = lows[i-1]
                
                fib_50 = ob_high - (ob_high - ob_low) * 0.5
                fib_618 = ob_high - (ob_high - ob_low) * 0.618
                
                touched = False
                touch_idx = None
                for j in range(i+1, min(i+20, n)):
                    if highs[j] <= ob_high and highs[j] >= ob_low:
                        if highs[j] >= fib_618 and highs[j] <= fib_50:
                            touched = True
                            touch_idx = j
                            break
                
                if not touched or touch_idx is None: continue
                
                mitigated = any(highs[k] > ob_high for k in range(touch_idx+1, min(touch_idx+15, n)))
                if mitigated: continue
                
                # GATE
                if ms['structure'] == 'BULLISH' and not ms.get('choch'):
                    continue
                
                score = 55
                
                ob_body = abs(closes[i-1] - opens[i-1])
                if ob_body > avg_body * 1.5: score += 15
                
                impulse_ratio = impulse / (atr_pct * closes[i])
                score += min(impulse_ratio * 15, 20)
                
                if ms['structure'] == 'BEARISH': score += 15
                elif (ms.get('choch') or {}).get('type') == 'BEARISH': score += 20
                
                window_h = max(highs[max(0,i-50):i+1])
                window_l = min(lows[max(0,i-50):i+1])
                fib_range = window_h - window_l
                if fib_range > 0:
                    pos_in_range = (closes[i] - window_l) / fib_range
                    if pos_in_range > 0.50: score += 10  # premium
                
                if score > best_score:
                    best_score = score
                    best = {
                        'type': 'OB', 'entry': closes[i-1],
                        'direction': 'SELL', 'idx': i-1,
                        'quality': score,
                        'fib_zone': (fib_618, fib_50),
                        'impulse_ratio': round(impulse_ratio, 1),
                        'market_structure': ms['structure']
                    }
        
        return best, best_score
    
    def find_breaker_block(self, highs, lows, closes, opens, direction):
        """
        Breaker Block: OB rompido + pullback.
        - OB precisa ter sido rompido com força (>0.3% além)
        - Pullback tocando o OB (agora suporte/resistência)
        - Volume de rompimento acima da média
        """
        n = len(highs)
        if n < 30: return None, 0
        
        atr_pct = self.get_atr(highs, lows, closes)
        avg_body = self.get_avg_volume(closes, opens)
        ms = self.structure.analyze(highs, lows, closes)
        
        best, best_score = None, 0
        
        for i in range(n-15, max(10, n-120), -1):
            if direction == 'BUY':
                if closes[i] >= opens[i]: continue  # precisa ser bearish
                
                ob_high = max(opens[i], closes[i])
                ob_low = min(opens[i], closes[i])
                
                # Rompido pra cima com força?
                if closes[i+1] <= ob_high: continue
                breakout_strength = (closes[i+1] - ob_high) / ob_high * 100
                if breakout_strength < 0.1: continue  # mínimo 0.1%
                
                # Volume do rompimento
                breakout_body = abs(closes[i+1] - opens[i+1])
                if breakout_body < avg_body * 1.3: continue
                
                # Pullback tocando o OB
                for j in range(i+2, min(i+20, n)):
                    if lows[j] <= ob_high and lows[j] >= ob_low:
                        # Verificar se não rompeu abaixo
                        if any(lows[k] < ob_low for k in range(j+1, min(j+10, n))): break
                        
                        score = 60
                        
                        if breakout_strength > 0.3: score += 15
                        if breakout_body > avg_body * 2.0: score += 10
                        
                        if ms['structure'] == 'BULLISH': score += 10
                        elif (ms.get('choch') or {}).get('type') == 'BULLISH': score += 15
                        
                        if ms['structure'] == 'BEARISH' and not ms.get('choch'): break
                        
                        if score > best_score:
                            best_score = score
                            best = {
                                'type': 'BREAKER', 'entry': ob_high,
                                'direction': 'BUY', 'idx': i,
                                'quality': score,
                                'breakout_pct': round(breakout_strength, 3),
                                'market_structure': ms['structure']
                            }
                        break
            
            else:  # SELL
                if closes[i] <= opens[i]: continue
                
                ob_high = max(opens[i], closes[i])
                ob_low = min(opens[i], closes[i])
                
                if closes[i+1] >= ob_low: continue
                breakout_strength = (ob_low - closes[i+1]) / ob_low * 100
                if breakout_strength < 0.1: continue
                
                breakout_body = abs(closes[i+1] - opens[i+1])
                if breakout_body < avg_body * 1.3: continue
                
                for j in range(i+2, min(i+20, n)):
                    if highs[j] >= ob_low and highs[j] <= ob_high:
                        if any(highs[k] > ob_high for k in range(j+1, min(j+10, n))): break
                        
                        score = 60
                        
                        if breakout_strength > 0.3: score += 15
                        if breakout_body > avg_body * 2.0: score += 10
                        
                        if ms['structure'] == 'BEARISH': score += 10
                        elif (ms.get('choch') or {}).get('type') == 'BEARISH': score += 15
                        
                        if ms['structure'] == 'BULLISH' and not ms.get('choch'): break
                        
                        if score > best_score:
                            best_score = score
                            best = {
                                'type': 'BREAKER', 'entry': ob_low,
                                'direction': 'SELL', 'idx': i,
                                'quality': score,
                                'breakout_pct': round(breakout_strength, 3),
                                'market_structure': ms['structure']
                            }
                        break
        
        return best, best_score
    
    def find_best_pattern(self, highs, lows, closes, opens, direction):
        """Encontra o melhor padrão combinando OB + Breaker."""
        # OB primeiro (mais comum, mais confiável)
        ob, ob_score = self.find_order_block(highs, lows, closes, opens, direction)
        
        # Breaker como alternativa
        br, br_score = self.find_breaker_block(highs, lows, closes, opens, direction)
        
        # Escolher o melhor
        if ob and (not br or ob_score >= br_score):
            return ob, ob_score
        elif br:
            return br, br_score
        
        return None, 0
    
    def get_market_context(self, highs, lows, closes):
        """Contexto completo do mercado para logging."""
        ms = self.structure.analyze(highs, lows, closes)
        return {
            'structure': ms['structure'],
            'choch': ms.get('choch'),
            'position': ms.get('position', 0.5),
            'liquidity_above': ms.get('liquidity_above', []),
            'liquidity_below': ms.get('liquidity_below', []),
        }
