#!/usr/bin/env python3
"""FVG Quality Scoring — Premium/Discount + Trend + Touch"""
import numpy as np

def find_swing_levels(highs, lows, lookback=20):
    n = len(highs)
    if n < lookback: return None, None
    return max(highs[-lookback:]), min(lows[-lookback:])

def score_fvg(highs, lows, closes, fvg_idx, direction, pip_size, swing_high=None, swing_low=None, is_metal=False):
    n = len(closes)
    if fvg_idx >= n-1 or fvg_idx < 6: return 0, {}
    min_gap = 2.0 if not is_metal else 50
    gap = (lows[fvg_idx] - highs[fvg_idx-2])/pip_size if direction=='BUY' else (lows[fvg_idx-2] - highs[fvg_idx])/pip_size
    if gap < min_gap: return 0, {'reason': f'gap {gap:.1f}'}
    score = 0; details = {'gap': round(gap,1)}
    if swing_high and swing_low:
        eq = (swing_high + swing_low)/2
        if direction=='BUY' and closes[fvg_idx] < eq: score += 30; details['zone']='discount'
        elif direction=='SELL' and closes[fvg_idx] > eq: score += 30; details['zone']='premium'
        else: details['zone']='wrong'
    else: score += 15
    if len(closes) >= 10:
        rc = closes[max(0,fvg_idx-9):fvg_idx+1]
        up = sum(1 for i in range(1,len(rc)) if rc[i]>rc[i-1])
        if (direction=='BUY' and up > (len(rc)-1-up)) or (direction=='SELL' and up < (len(rc)-1-up)):
            score += 25; details['trend']='aligned'
    mitigated = False
    if direction=='BUY':
        for j in range(fvg_idx+1, min(fvg_idx+10, n)):
            if lows[j] <= highs[fvg_idx-2]: mitigated = True; break
    else:
        for j in range(fvg_idx+1, min(fvg_idx+10, n)):
            if highs[j] >= lows[fvg_idx-2]: mitigated = True; break
    if not mitigated: score += 20; details['touch']='first'
    details['score'] = score
    return score, details

def is_fvg_valid(highs, lows, closes, fvg_idx, direction, pip_size, is_metal=False, min_score=35):
    sh, sl = find_swing_levels(highs, lows, 20)
    score, details = score_fvg(highs, lows, closes, fvg_idx, direction, pip_size, sh, sl, is_metal)
    return score >= min_score, details
