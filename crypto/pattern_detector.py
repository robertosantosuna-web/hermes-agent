#!/usr/bin/env python3
"""
CRYPTO PATTERN DETECTOR — Padrões ICT e Estrutura de Mercado
Patterns: CHoCH, Order Block, Breaker Block, Liquidity Sweep, Market Structure
"""
import numpy as np

class MarketStructure:
    """Analisa estrutura de mercado: HH/HL (bullish), LH/LL (bearish)."""
    
    def analyze(self, highs, lows, closes, lookback=50):
        """Retorna estrutura atual e pontos de quebra."""
        n = len(highs)
        if n < lookback: return {'structure': 'UNKNOWN', 'swings': [], 'choch': None}
        
        # Encontrar swing highs e lows (pivôs)
        swings = self._find_swings(highs, lows, lookback)
        
        if len(swings) < 4:
            return {'structure': 'UNKNOWN', 'swings': swings, 'choch': None}
        
        # Determinar estrutura
        swing_highs = [(i, h) for i, h, _ in swings]
        swing_lows = [(i, l) for _, i, l in swings]
        
        # Bullish: HH + HL
        hh_count = sum(1 for j in range(1, len(swing_highs)) 
                      if swing_highs[j][1] > swing_highs[j-1][1])
        hl_count = sum(1 for j in range(1, len(swing_lows))
                      if swing_lows[j][1] > swing_lows[j-1][1])
        
        # Bearish: LH + LL
        lh_count = sum(1 for j in range(1, len(swing_highs))
                      if swing_highs[j][1] < swing_highs[j-1][1])
        ll_count = sum(1 for j in range(1, len(swing_lows))
                      if swing_lows[j][1] < swing_lows[j-1][1])
        
        # Detectar CHoCH (mudança de estrutura)
        choch = self._detect_choch(swing_highs, swing_lows, closes)
        
        # Classificar
        if hh_count >= 2 and hl_count >= 2:
            structure = 'BULLISH'
        elif lh_count >= 2 and ll_count >= 2:
            structure = 'BEARISH'
        elif choch:
            structure = 'CHoCH'
        else:
            structure = 'RANGE'
        
        # Níveis de liquidez
        eq_highs = self._find_equal_highs(highs)
        eq_lows = self._find_equal_lows(lows)
        
        return {
            'structure': structure,
            'swings': swings[-4:],
            'choch': choch,
            'liquidity_above': eq_highs,
            'liquidity_below': eq_lows,
            'current_pos': (closes[-1] - min(lows[-lookback:])) / 
                          (max(highs[-lookback:]) - min(lows[-lookback:]))
                          if max(highs[-lookback:]) > min(lows[-lookback:]) else 0.5
        }
    
    def _find_swings(self, highs, lows, lookback=50):
        """Encontra swing highs e lows (pivôs com 5 velas de confirmação)."""
        n = len(highs)
        swings = []
        start = max(0, n - lookback)
        
        for i in range(start + 3, n - 3):
            # Swing high: vela mais alta com 3 menores de cada lado
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i-3] \
               and highs[i] > highs[i+1] and highs[i] > highs[i+2] and highs[i] > highs[i+3]:
                swings.append((i, True, highs[i]))  # (index, is_high, price)
            
            # Swing low
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i-3] \
               and lows[i] < lows[i+1] and lows[i] < lows[i+2] and lows[i] < lows[i+3]:
                swings.append((i, False, lows[i]))
        
        return swings
    
    def _detect_choch(self, swing_highs, swing_lows, closes):
        """Detecta Change of Character: quebra de estrutura."""
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return None
        
        last_sh = swing_highs[-1] if swing_highs else None
        prev_sh = swing_highs[-2] if len(swing_highs) >= 2 else None
        last_sl = swing_lows[-1] if swing_lows else None
        prev_sl = swing_lows[-2] if len(swing_lows) >= 2 else None
        
        current = closes[-1]
        
        # Bearish CHoCH: rompeu último HL (mudança de bullish pra bearish)
        if prev_sl and last_sl and last_sl[1] < prev_sl[1]:
            return {'type': 'BEARISH', 'level': prev_sl[1], 
                    'message': 'Quebrou HL anterior → possível reversão bearish'}
        
        # Bullish CHoCH: rompeu último LH
        if prev_sh and last_sh and last_sh[1] > prev_sh[1]:
            return {'type': 'BULLISH', 'level': prev_sh[1],
                    'message': 'Rompendo LH anterior → possível reversão bullish'}
        
        return None
    
    def _find_equal_highs(self, highs, tolerance_pct=0.05):
        """Encontra topos iguais (liquidez acima)."""
        n = len(highs)
        if n < 20: return []
        
        recent = highs[-20:]
        eq_highs = []
        
        for i in range(len(recent)):
            for j in range(i+1, len(recent)):
                if abs(recent[i] - recent[j]) / recent[i] * 100 < tolerance_pct:
                    eq_highs.append(max(recent[i], recent[j]))
        
        return sorted(set(eq_highs))[-3:] if eq_highs else []
    
    def _find_equal_lows(self, lows, tolerance_pct=0.05):
        """Encontra fundos iguais (liquidez abaixo)."""
        n = len(lows)
        if n < 20: return []
        
        recent = lows[-20:]
        eq_lows = []
        
        for i in range(len(recent)):
            for j in range(i+1, len(recent)):
                if abs(recent[i] - recent[j]) / recent[i] * 100 < tolerance_pct:
                    eq_lows.append(min(recent[i], recent[j]))
        
        return sorted(set(eq_lows))[:3] if eq_lows else []


class OrderBlockDetector:
    """Detecta Order Blocks: última vela oposta antes do impulso."""
    
    def find(self, highs, lows, closes, opens, direction):
        """Encontra OB na direção especificada."""
        n = len(highs)
        if n < 10: return None, 0
        
        best, best_score = None, 0
        
        # Buscar nas últimas 100 velas
        for i in range(n-4, max(4, n-100), -1):
            if direction == 'BUY':
                # Impulso bullish: vela fecha acima da anterior
                if closes[i] <= closes[i-1]: continue
                impulse = closes[i] - closes[i-1]
                
                # OB é a vela bearish antes do impulso (i-1)
                # Buscar pullback tocando a área do OB
                ob_high = highs[i-1]
                ob_low = lows[i-1]
                
                for j in range(i+1, min(i+10, n)):
                    if lows[j] <= ob_high and lows[j] >= ob_low:
                        score = 55
                        
                        # Qualidade do OB
                        ob_body = abs(closes[i-1] - opens[i-1])
                        avg_body = np.mean([abs(closes[k]-opens[k]) 
                                          for k in range(max(0,i-20), i-1)])
                        if ob_body > avg_body * 1.5: score += 15
                        
                        # Impulso forte
                        if impulse > avg_body * 2: score += 10
                        
                        # Não mitigado depois do pullback
                        mitigated = any(lows[k] < ob_low for k in range(j+1, min(j+10, n)))
                        if not mitigated: score += 10
                        
                        if score > best_score:
                            best_score = score
                            best = {
                                'type': 'OB', 'entry': closes[i-1],
                                'direction': 'BUY', 'idx': i-1,
                                'quality': score, 'ob_range': (ob_low, ob_high)
                            }
                        break
            
            else:  # SELL
                if closes[i] >= closes[i-1]: continue
                impulse = closes[i-1] - closes[i]
                
                ob_high = highs[i-1]
                ob_low = lows[i-1]
                
                for j in range(i+1, min(i+10, n)):
                    if highs[j] <= ob_high and highs[j] >= ob_low:
                        score = 55
                        
                        ob_body = abs(closes[i-1] - opens[i-1])
                        avg_body = np.mean([abs(closes[k]-opens[k])
                                          for k in range(max(0,i-20), i-1)])
                        if ob_body > avg_body * 1.5: score += 15
                        
                        if impulse > avg_body * 2: score += 10
                        
                        mitigated = any(highs[k] > ob_high for k in range(j+1, min(j+10, n)))
                        if not mitigated: score += 10
                        
                        if score > best_score:
                            best_score = score
                            best = {
                                'type': 'OB', 'entry': closes[i-1],
                                'direction': 'SELL', 'idx': i-1,
                                'quality': score, 'ob_range': (ob_low, ob_high)
                            }
                        break
        
        return best, best_score


class BreakerBlockDetector:
    """Detecta Breaker Blocks: OB rompido que vira suporte/resistência."""
    
    def find(self, highs, lows, closes, opens, direction):
        """
        Bullish breaker: OB bearish que foi rompido pra cima → vira suporte
        Bearish breaker: OB bullish que foi rompido pra baixo → vira resistência
        """
        n = len(highs)
        if n < 20: return None, 0
        
        best, best_score = None, 0
        
        for i in range(n-10, max(10, n-100), -1):
            if direction == 'BUY':
                # Procurar OB bearish antigo que foi rompido
                if closes[i] >= opens[i]: continue  # não é bearish
                
                ob_high = max(opens[i], closes[i])
                ob_low = min(opens[i], closes[i])
                
                # Foi rompido pra cima?
                if closes[i+1] <= ob_high: continue
                
                # Pullback tocando o OB rompido
                for j in range(i+2, min(i+15, n)):
                    if lows[j] <= ob_high and lows[j] >= ob_low:
                        score = 60
                        
                        # Impulso pós-rompimento
                        if closes[i+1] > ob_high * 1.002: score += 15
                        
                        if score > best_score:
                            best_score = score
                            best = {
                                'type': 'BREAKER', 'entry': ob_high,
                                'direction': 'BUY', 'idx': i,
                                'quality': score
                            }
                        break
            
            else:  # SELL
                if closes[i] <= opens[i]: continue
                
                ob_high = max(opens[i], closes[i])
                ob_low = min(opens[i], closes[i])
                
                if closes[i+1] >= ob_low: continue
                
                for j in range(i+2, min(i+15, n)):
                    if highs[j] >= ob_low and highs[j] <= ob_high:
                        score = 60
                        
                        if closes[i+1] < ob_low * 0.998: score += 15
                        
                        if score > best_score:
                            best_score = score
                            best = {
                                'type': 'BREAKER', 'entry': ob_low,
                                'direction': 'SELL', 'idx': i,
                                'quality': score
                            }
                        break
        
        return best, best_score


class LiquiditySweep:
    """Detecta caça aos stops (liquidity sweep)."""
    
    def detect(self, highs, lows, closes, market_structure):
        """
        Detecta sweep de liquidez:
        - Sweep acima de equal highs + reversão = venda
        - Sweep abaixo de equal lows + reversão = compra
        """
        n = len(highs)
        if n < 20: return None
        
        ms = market_structure
        current = closes[-1]
        
        # Sweep bearish: rompeu equal highs e reverteu
        if ms.get('liquidity_above'):
            liq_level = max(ms['liquidity_above'])
            # Últimas velas romperam o nível
            for i in range(n-5, n-1):
                if highs[i] > liq_level and closes[i] < liq_level:
                    return {
                        'type': 'LIQ_SWEEP', 'direction': 'SELL',
                        'level': liq_level, 'quality': 70,
                        'message': f'Sweep acima de {liq_level:.2f} → venda'
                    }
        
        # Sweep bullish: rompeu equal lows e reverteu
        if ms.get('liquidity_below'):
            liq_level = min(ms['liquidity_below'])
            for i in range(n-5, n-1):
                if lows[i] < liq_level and closes[i] > liq_level:
                    return {
                        'type': 'LIQ_SWEEP', 'direction': 'BUY',
                        'level': liq_level, 'quality': 70,
                        'message': f'Sweep abaixo de {liq_level:.2f} → compra'
                    }
        
        return None


class PatternIntegrator:
    """Integra todos os padrões e escolhe o melhor."""
    
    def __init__(self):
        self.structure = MarketStructure()
        self.ob = OrderBlockDetector()
        self.breaker = BreakerBlockDetector()
        self.sweep = LiquiditySweep()
    
    def find_best_pattern(self, highs, lows, closes, opens, direction):
        """Encontra o melhor padrão disponível na direção."""
        n = len(highs)
        if n < 30: return None, 0
        
        # Análise de estrutura
        ms = self.structure.analyze(highs, lows, closes)
        
        patterns = []
        
        # 1. Order Block
        ob, ob_score = self.ob.find(highs, lows, closes, opens, direction)
        if ob:
            ob['structure'] = ms['structure']
            patterns.append((ob, ob_score, 'OB'))
        
        # 2. Breaker Block
        br, br_score = self.breaker.find(highs, lows, closes, opens, direction)
        if br:
            br['structure'] = ms['structure']
            patterns.append((br, br_score, 'BREAKER'))
        
        # 3. Liquidity Sweep
        sw = self.sweep.detect(highs, lows, closes, ms)
        if sw and sw['direction'] == direction:
            sw['structure'] = ms['structure']
            patterns.append((sw, sw.get('quality', 60), 'LIQ_SWEEP'))
        
        if not patterns:
            return None, 0
        
        # Bônus por alinhamento com estrutura
        for pat, score, ptype in patterns:
            if ms['structure'] == 'BULLISH' and direction == 'BUY':
                score += 20
            elif ms['structure'] == 'BEARISH' and direction == 'SELL':
                score += 20
            elif ms['structure'] == 'CHoCH':
                choch = ms.get('choch', {})
                if choch.get('type') == direction:
                    score += 30  # CHoCH alinhado = bônus máximo
        
        # Melhor padrão
        patterns.sort(key=lambda x: x[1], reverse=True)
        best_pat, best_score, best_type = patterns[0]
        
        return best_pat, best_score
    
    def get_market_context(self, highs, lows, closes):
        """Retorna contexto completo do mercado."""
        ms = self.structure.analyze(highs, lows, closes)
        
        return {
            'structure': ms['structure'],
            'choch': ms.get('choch'),
            'liquidity_above': ms.get('liquidity_above', []),
            'liquidity_below': ms.get('liquidity_below', []),
            'position_in_range': ms.get('current_pos', 0.5),
            'swings': len(ms.get('swings', []))
        }


if __name__ == '__main__':
    # Teste rápido
    import yfinance as yf
    
    df = yf.Ticker('BTC-USD').history(period='5d', interval='1m')
    h = df['High'].values
    l = df['Low'].values
    c = df['Close'].values
    o = df['Open'].values
    
    pi = PatternIntegrator()
    
    print("═══ MARKET STRUCTURE ═══")
    ctx = pi.get_market_context(h, l, c)
    for k, v in ctx.items():
        print(f"  {k}: {v}")
    
    print("\n═══ PATTERNS ═══")
    for direction in ['BUY', 'SELL']:
        pat, score = pi.find_best_pattern(h, l, c, o, direction)
        if pat:
            print(f"  {direction}: {pat['type']} Q={score} entry={pat.get('entry', '?'):.4f}")
        else:
            print(f"  {direction}: Nenhum padrão")
