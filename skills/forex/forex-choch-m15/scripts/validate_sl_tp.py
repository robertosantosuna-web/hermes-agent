#!/usr/bin/env python3
"""
VALIDAÇÃO de correções SL/TP — testa ANTES de implementar.
Testa funções isoladas SEM chamar execute_trade() (que envia ordens reais).
"""
import sys
sys.path.insert(0, '/home/roberto/.hermes/scripts')

from forex_bot_multi import calculate_sl_tp, calculate_volume

PIP_SIZES = {
    'EURUSD': 0.0001, 'GBPUSD': 0.0001, 'USDCAD': 0.0001,
    'USDJPY': 0.01, 'GBPJPY': 0.01, 'EURJPY': 0.01,
    'XAUUSD': 0.01,
}

RR_MAP = {'FVG+CRT': 3.0, 'SMC Fractal': 2.0, 'S/R+FVG': 3.0}
BALANCE = 363.41
MAX_SL_PIPS = 30
MAX_SL_TICKS_XAU = 300
MIN_SL_PIPS = 15
MIN_SL_TICKS_XAU = 200


def validate_trade(direction, pair, entry, sl_pips, strategy, rr=None):
    pip = PIP_SIZES.get(pair, 0.0001)
    is_metal = pair == 'XAUUSD'
    rr = rr or RR_MAP.get(strategy, 3.0)
    max_sl = MAX_SL_TICKS_XAU if is_metal else MAX_SL_PIPS
    min_sl = MIN_SL_TICKS_XAU if is_metal else MIN_SL_PIPS
    
    # SL validation
    if sl_pips <= 0:
        print(f'{pair} {direction}: ❌ REJEITADO — SL=0 sem stop loss')
        return None
    
    sl_pips_fixed = max(min_sl, min(sl_pips, max_sl))
    
    sl, tp = calculate_sl_tp(direction, entry, sl_pips_fixed, rr, pip, is_metal)
    sl_dist = abs(entry - sl) / pip
    tp_dist = abs(tp - entry) / pip
    rr_real = tp_dist / sl_dist if sl_dist > 0 else 0
    
    unit = 'ticks' if is_metal else 'pips'
    print(f'{pair} {direction} | {strategy}: SL {sl_pips:.0f}→{sl_pips_fixed:.0f}{unit} | TP {tp_dist:.0f}{unit} | RR {rr_real:.1f}:1')
    
    if sl_pips != sl_pips_fixed:
        print(f'  {"⚠️ SL=0→mínimo" if sl_pips <= 0 else "🔧 SL capado"}')
    
    return {'sl': sl, 'tp': tp, 'sl_pips': sl_pips_fixed}


if __name__ == '__main__':
    print('VALIDAÇÃO SL/TP (teste seco — sem ordens reais)')
    print(f'Balance: ${BALANCE} | SL forex: {MIN_SL_PIPS}-{MAX_SL_PIPS}p | SL XAU: {MIN_SL_TICKS_XAU}-{MAX_SL_TICKS_XAU}t\n')
    
    validate_trade('BUY',  'USDJPY', 159.395, 0.0,    'FVG+CRT')
    validate_trade('SELL', 'EURUSD', 1.16242, 40.3,   'SMC Fractal')
    validate_trade('SELL', 'EURJPY', 185.463, 31.8,   'SMC Fractal')
    validate_trade('BUY',  'USDCAD', 1.38356, 40.6,   'SMC Fractal')
    validate_trade('SELL', 'XAUUSD', 4455.64, 22.0,   'FVG+CRT', 3.0)
    validate_trade('SELL', 'XAUUSD', 4452.94, 24.0,   'FVG+CRT', 3.0)
