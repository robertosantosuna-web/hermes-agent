#!/usr/bin/env python3
"""
CRYPTO PATTERN DETECTOR v3 — Fatores extras de assertividade
Novos: Volume real, Wick rejection, Candle fechado, S/R diário
"""
import numpy as np

class MarketStructure:
    def analyze(self, highs, lows, closes, lookback=60):
        n = len(highs)
        if n < lookback: return {'structure': 'UNKNOWN', 'choch': None, 'position': 0.5}
        swings = self._find_swings(highs, lows, lookback)
        if len(swings) < 4:
            return {'structure': 'UNKNOWN', 'choch': None, 'position': 0.5}
        sh = [(i, p) for i, is_h, p in swings if is_h]
        sl = [(i, p) for i, is_h, p in swings if not is_h]
        if len(sh) < 2 or len(sl) < 2:
            return {'structure': 'UNKNOWN', 'choch': None, 'position': 0.5}
        hh = sh[-1][1] > sh[-2][1]
        hl = sl[-1][1] > sl[-2][1]
        lh = sh[-1][1] < sh[-2][1]
        ll = sl[-1][1] < sl[-2][1]
        choch = None
        if len(sh) >= 3 and len(sl) >= 3:
            if sh[-1][1] > sh[-2][1] and sh[-2][1] < sh[-3][1]:
                choch = {'type': 'BULLISH', 'level': sh[-2][1]}
            elif sl[-1][1] < sl[-2][1] and sl[-2][1] > sl[-3][1]:
                choch = {'type': 'BEARISH', 'level': sl[-2][1]}
        if hh and hl: structure = 'BULLISH'
        elif lh and ll: structure = 'BEARISH'
        elif choch: structure = 'CHoCH'
        else: structure = 'RANGE'
        window_h = max(highs[-lookback:])
        window_l = min(lows[-lookback:])
        pos = (closes[-1] - window_l) / (window_h - window_l) if window_h > window_l else 0.5
        return {'structure': structure, 'choch': choch, 'position': pos}
    
    def _find_swings(self, highs, lows, lookback=60):
        n = len(highs); swings = []
        start = max(0, n - lookback)
        for i in range(start+3, n-3):
            if all(highs[i] > highs[i-j] for j in range(1,4)) and all(highs[i] > highs[i+j] for j in range(1,4)):
                swings.append((i, True, highs[i]))
            if all(lows[i] < lows[i-j] for j in range(1,4)) and all(lows[i] < lows[i+j] for j in range(1,4)):
                swings.append((i, False, lows[i]))
        return swings


class AdvancedPatternDetector:
    """Detector de OB com todos os fatores de assertividade."""
    
    def __init__(self):
        self.structure = MarketStructure()
    
    def get_atr(self, highs, lows, closes, period=14):
        n = len(closes)
        if n < period+1: return 0.001
        tr = [max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
              for i in range(1, min(period+10, n))]
        return (sum(tr[-period:])/period) / closes[-1] if len(tr) >= period else (sum(tr)/len(tr)) / closes[-1]
    
    def get_avg_body(self, closes, opens, lookback=20):
        bodies = [abs(closes[i]-opens[i]) for i in range(max(0, len(closes)-lookback-1), len(closes)-1)]
        return np.mean(bodies) if bodies else 0
    
    def get_avg_volume(self, volumes, lookback=20):
        """Volume real médio (coluna Volume do yfinance)."""
        if volumes is None or len(volumes) < lookback:
            return 0
        vol_slice = volumes[max(0, len(volumes)-lookback-1):len(volumes)-1]
        return np.mean(vol_slice) if len(vol_slice) > 0 else 0
    
    def find_daily_levels(self, daily_highs, daily_lows, daily_closes):
        """Encontra S/R de longo prazo (diário)."""
        if daily_highs is None or len(daily_highs) < 5:
            return {'resistance': None, 'support': None}
        
        # Resistência: topo dos últimos 5-10 dias
        resistance = max(daily_highs[-10:]) if len(daily_highs) >= 10 else max(daily_highs)
        # Suporte: fundo dos últimos 5-10 dias
        support = min(daily_lows[-10:]) if len(daily_lows) >= 10 else min(daily_lows)
        
        return {'resistance': resistance, 'support': support}
    
    def find_order_block(self, highs, lows, closes, opens, direction, volumes=None, daily_levels=None):
        """
        Order Block com TODOS os fatores:
        + Volume real do impulso > 1.0x média
        + Wick rejection (pavio oposto > 60% do corpo)
        + Candle fechado (não opera vela atual)
        + Pullback Fibonacci 0.5-0.618
        + S/R diário (não comprar perto de resistência, não vender perto de suporte)
        + Market Structure gate
        """
        n = len(highs)
        if n < 30: return None, 0
        
        atr_pct = self.get_atr(highs, lows, closes)
        avg_body = self.get_avg_body(closes, opens)
        avg_vol = self.get_avg_volume(volumes)
        ms = self.structure.analyze(highs, lows, closes)
        
        # Níveis diários
        daily_res = daily_levels.get('resistance') if daily_levels else None
        daily_sup = daily_levels.get('support') if daily_levels else None
        
        best, best_score = None, 0
        search_start = max(10, n - 150)
        
        for i in range(n-3, search_start, -1):
            current_price = closes[-1]
            
            if direction == 'BUY':
                if closes[i] <= closes[i-1]: continue
                impulse = closes[i] - closes[i-1]
                
                # 1. Impulso mínimo 0.3x ATR
                min_impulse = atr_pct * closes[i] * 0.3
                if impulse < min_impulse: continue
                
                # 2. Volume real do impulso > 1.0x média
                if volumes is not None and avg_vol > 0:
                    if volumes[i] < avg_vol * 1.0: continue
                
                # 3. Wick rejection: OB (vela bearish) com pavio inferior longo = rejeição de venda
                ob_body = abs(closes[i-1] - opens[i-1])
                ob_low = lows[i-1]
                ob_high = highs[i-1]
                lower_wick = min(opens[i-1], closes[i-1]) - ob_low
                wick_ratio = lower_wick / ob_body if ob_body > 0 else 0
                if ob_body > 0:
                    wick_ratio = lower_wick / ob_body
                
                # 4. OB = vela antes do impulso (bearish)
                # Pullback Fibonacci 0.5-0.618
                fib_50 = ob_low + (ob_high - ob_low) * 0.5
                fib_618 = ob_low + (ob_high - ob_low) * 0.618
                
                touched = False; touch_idx = None
                for j in range(i+1, min(i+20, n)):
                    if lows[j] <= ob_high and lows[j] >= ob_low:
                        if lows[j] <= fib_618 and lows[j] >= fib_50:
                            touched = True; touch_idx = j; break
                
                if not touched or touch_idx is None: continue
                
                # 5. First-touch: não mitigado depois do pullback
                if any(lows[k] < ob_low for k in range(touch_idx+1, min(touch_idx+15, n))): continue
                
                # 6. Candle fechado: o pullback já fechou? (touch_idx < n-2)
                if touch_idx >= n - 2: continue
                
                # 7. Market Structure gate
                if ms['structure'] == 'BEARISH' and not ms.get('choch'): continue
                
                # 8. S/R diário: não comprar se preço está perto da resistência diária
                if daily_res and current_price > daily_res * 0.995: continue
                
                # ═══ SCORING ═══
                score = 55
                
                # OB corpo grande = rejeição forte
                if ob_body > avg_body * 1.5: score += 15
                
                # Wick rejection
                if ob_body > 0:
                    wick_ratio = lower_wick / ob_body
                    score += min(wick_ratio * 15, 15)
                
                # Força do impulso
                impulse_ratio = impulse / (atr_pct * closes[i])
                score += min(impulse_ratio * 15, 20)
                
                # Volume real
                if volumes is not None and avg_vol > 0:
                    vol_ratio = volumes[i] / avg_vol
                    score += min(vol_ratio * 10, 15)
                
                # Estrutura alinhada
                if ms['structure'] == 'BULLISH': score += 15
                elif (ms.get('choch') or {}).get('type') == 'BULLISH': score += 20
                
                # Discount zone
                window_h = max(highs[max(0,i-50):i+1])
                window_l = min(lows[max(0,i-50):i+1])
                if window_h > window_l:
                    pos = (closes[i] - window_l) / (window_h - window_l)
                    if pos < 0.50: score += 10
                
                # S/R diário: bônus se está próximo do suporte
                if daily_sup and current_price < daily_sup * 1.01:
                    score += 10
                
                if score > best_score:
                    best_score = score
                    best = {
                        'type': 'OB', 'entry': closes[i-1],
                        'direction': 'BUY', 'idx': i-1,
                        'quality': score,
                        'impulse_ratio': round(impulse_ratio, 1),
                        'wick_ratio': round(wick_ratio if ob_body > 0 else 0, 1),
                        'vol_ratio': round(volumes[i]/avg_vol if volumes is not None and avg_vol > 0 else 0, 1),
                        'market_structure': ms['structure']
                    }
            
            else:  # SELL
                if closes[i] >= closes[i-1]: continue
                impulse = closes[i-1] - closes[i]
                
                if impulse < atr_pct * closes[i] * 0.3: continue
                
                if volumes is not None and avg_vol > 0:
                    if volumes[i] < avg_vol * 1.0: continue
                
                ob_body = abs(closes[i-1] - opens[i-1])
                ob_high = highs[i-1]
                ob_low = lows[i-1]
                upper_wick = ob_high - max(opens[i-1], closes[i-1])
                wick_ratio = upper_wick / ob_body if ob_body > 0 else 0
                
                fib_50 = ob_high - (ob_high - ob_low) * 0.5
                fib_618 = ob_high - (ob_high - ob_low) * 0.618
                
                touched = False; touch_idx = None
                for j in range(i+1, min(i+20, n)):
                    if highs[j] <= ob_high and highs[j] >= ob_low:
                        if highs[j] >= fib_618 and highs[j] <= fib_50:
                            touched = True; touch_idx = j; break
                
                if not touched or touch_idx is None: continue
                if any(highs[k] > ob_high for k in range(touch_idx+1, min(touch_idx+15, n))): continue
                if touch_idx >= n - 2: continue
                
                if ms['structure'] == 'BULLISH' and not ms.get('choch'): continue
                
                # Não vender perto do suporte diário
                if daily_sup and current_price < daily_sup * 1.005: continue
                
                score = 55
                
                if ob_body > avg_body * 1.5: score += 15
                
                if ob_body > 0:
                    wick_ratio = upper_wick / ob_body
                    score += min(wick_ratio * 15, 15)
                
                impulse_ratio = impulse / (atr_pct * closes[i])
                score += min(impulse_ratio * 15, 20)
                
                if volumes is not None and avg_vol > 0:
                    vol_ratio = volumes[i] / avg_vol
                    score += min(vol_ratio * 10, 15)
                
                if ms['structure'] == 'BEARISH': score += 15
                elif (ms.get('choch') or {}).get('type') == 'BEARISH': score += 20
                
                window_h = max(highs[max(0,i-50):i+1])
                window_l = min(lows[max(0,i-50):i+1])
                if window_h > window_l:
                    pos = (closes[i] - window_l) / (window_h - window_l)
                    if pos > 0.50: score += 10
                
                if daily_res and current_price > daily_res * 0.99:
                    score += 10
                
                if score > best_score:
                    best_score = score
                    best = {
                        'type': 'OB', 'entry': closes[i-1],
                        'direction': 'SELL', 'idx': i-1,
                        'quality': score,
                        'impulse_ratio': round(impulse_ratio, 1),
                        'wick_ratio': round(wick_ratio if ob_body > 0 else 0, 1),
                        'vol_ratio': round(volumes[i]/avg_vol if volumes is not None and avg_vol > 0 else 0, 1),
                        'market_structure': ms['structure']
                    }
        
        return best, best_score
    
    def find_best_pattern(self, highs, lows, closes, opens, direction, volumes=None, daily_levels=None):
        """Encontra melhor padrão na direção especificada."""
        return self.find_order_block(highs, lows, closes, opens, direction, volumes, daily_levels)
    
    def get_market_context(self, highs, lows, closes):
        ms = self.structure.analyze(highs, lows, closes)
        return {
            'structure': ms['structure'],
            'choch': ms.get('choch'),
            'position': ms.get('position', 0.5),
        }
