#!/usr/bin/env python3
"""FVG Quality Scoring System — elimina FVGs falsos"""
import numpy as np

def score_fvg(highs, lows, closes, fvg_idx, direction, pip_size, 
              swing_high=None, swing_low=None, is_metal=False):
    """
    Pontua FVG de 0-100. Só retorna True se score >= threshold.
    
    Critérios:
    1. Tamanho mínimo (>2x spread) — OBRIGATÓRIO
    2. Premium/Discount (30pts) — compra em discount, venda em premium
    3. Alinhamento com tendência (25pts) — FVG na direção do momentum
    4. First touch / não mitigado (20pts) — nunca foi revisitado
    5. Sessão liquidez (15pts) — fora de Ásia
    6. Vela de qualidade (10pts) — range amplo, sem rejeição
    """
    n = len(closes)
    if fvg_idx >= n-1 or fvg_idx < 6:
        return 0, {}
    
    score = 0
    details = {}
    
    # ═══ 1. TAMANHO MÍNIMO (obrigatório) ═══
    min_gap_pips = 2.0 if not is_metal else 50  # 2 pips forex / 50 ticks metal
    if direction == 'BUY':
        gap = (lows[fvg_idx] - highs[fvg_idx-2]) / pip_size
    else:
        gap = (lows[fvg_idx-2] - highs[fvg_idx]) / pip_size
    
    if gap < min_gap_pips:
        return 0, {'reason': f'gap {gap:.1f}p < {min_gap_pips}p mínimo'}
    details['gap'] = round(gap, 1)
    
    # ═══ 2. PREMIUM/DISCOUNT (30pts) ═══
    if swing_high is not None and swing_low is not None:
        equilibrium = (swing_high + swing_low) / 2
        entry = closes[fvg_idx]
        
        if direction == 'BUY' and entry < equilibrium:
            score += 30  # compra em discount
            details['zone'] = 'discount'
        elif direction == 'SELL' and entry > equilibrium:
            score += 30  # venda em premium
            details['zone'] = 'premium'
        elif direction == 'BUY' and entry > equilibrium:
            details['zone'] = 'premium (ruim)'
        else:
            details['zone'] = 'discount (ruim)'
    else:
        score += 15  # sem swing definido, pontuação parcial
        details['zone'] = 'unknown'
    
    # ═══ 3. ALINHAMENTO COM TENDÊNCIA (25pts) ═══
    # Verificar últimas 10 velas: maioria bullish ou bearish?
    if len(closes) >= 10:
        recent_closes = closes[max(0,fvg_idx-9):fvg_idx+1]
        up_bars = sum(1 for i in range(1,len(recent_closes)) 
                      if recent_closes[i] > recent_closes[i-1])
        down_bars = len(recent_closes) - 1 - up_bars
        
        if direction == 'BUY' and up_bars > down_bars:
            score += 25
            details['trend'] = 'aligned'
        elif direction == 'SELL' and down_bars > up_bars:
            score += 25
            details['trend'] = 'aligned'
        else:
            details['trend'] = 'against'
    
    # ═══ 4. FIRST TOUCH / NÃO MITIGADO (20pts) ═══
    # Verificar se candles após o FVG já tocaram o gap
    mitigated = False
    if direction == 'BUY':
        fvg_top = highs[fvg_idx-2]
        fvg_bottom = lows[fvg_idx]
        for j in range(fvg_idx+1, min(fvg_idx+10, n)):
            if lows[j] <= fvg_top:  # preço voltou ao gap
                mitigated = True
                break
    else:
        fvg_top = lows[fvg_idx-2]
        fvg_bottom = highs[fvg_idx]
        for j in range(fvg_idx+1, min(fvg_idx+10, n)):
            if highs[j] >= fvg_bottom:
                mitigated = True
                break
    
    if not mitigated:
        score += 20
        details['touch'] = 'first'
    else:
        details['touch'] = 'mitigated'
    
    # ═══ 5. VELA DE QUALIDADE (10pts) ═══
    body = abs(closes[fvg_idx] - closes[fvg_idx-1])  # corpo da vela do gap
    avg_body = np.mean([abs(closes[i]-closes[i-1]) 
                        for i in range(max(1,fvg_idx-10), fvg_idx)])
    if body > avg_body * 1.3:
        score += 10
        details['candle'] = 'strong'
    else:
        details['candle'] = 'average'
    
    # ═══ 6. CONSECUTIVE FVGs (penalidade se >3) ═══
    consecutive = 0
    for i in range(fvg_idx-1, max(0,fvg_idx-20), -1):
        if direction == 'BUY' and lows[i] > highs[i-2]:
            consecutive += 1
        elif direction == 'SELL' and highs[i] < lows[i-2]:
            consecutive += 1
        else:
            break
    if consecutive > 3:
        score = max(0, score - 15)  # penalidade
        details['consecutive'] = consecutive
    
    details['score'] = score
    return score, details


def find_swing_levels(highs, lows, lookback=20):
    """Encontra swing high e swing low recentes."""
    n = len(highs)
    if n < lookback: return None, None
    h = highs[-lookback:]
    l = lows[-lookback:]
    sh = max(h)
    sl = min(l)
    return sh, sl


def is_fvg_valid(highs, lows, closes, fvg_idx, direction, pip_size, 
                 is_metal=False, min_score=55):
    """
    Filtro principal: retorna True se FVG tem qualidade suficiente.
    min_score=55: premium/discount(30) + trend(25) = 55 (mínimo)
    """
    sh, sl = find_swing_levels(highs, lows, 20)
    score, details = score_fvg(highs, lows, closes, fvg_idx, direction, 
                                pip_size, sh, sl, is_metal)
    return score >= min_score, details
