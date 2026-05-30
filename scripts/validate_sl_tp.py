#!/usr/bin/env python3
"""
VALIDAÇÃO de correções SL/TP — testa ANTES de implementar.
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
MAX_SL_PIPS_PROPOSED = 30  # Máximo de SL proposto (forex)
MAX_SL_TICKS_XAU = 300     # Máximo de SL proposto (ouro)

def validate_trade(direction, pair, entry, sl_pips, strategy, rr=None):
    """Valida um trade e mostra correções propostas."""
    pip = PIP_SIZES.get(pair, 0.0001)
    is_metal = pair == 'XAUUSD'
    rr = rr or RR_MAP.get(strategy, 3.0)
    
    # ═══ CÁLCULO ATUAL ═══
    sl_old, tp_old = calculate_sl_tp(direction, entry, sl_pips, rr, pip, is_metal)
    sl_dist_old = abs(entry - sl_old)
    tp_dist_old = abs(tp_old - entry)
    
    # ═══ CORREÇÃO #1: SL mínimo garantido ═══
    min_sl = 15.0 if not is_metal else 200  # 15 pips forex, 200 ticks ouro
    sl_pips_fixed = max(sl_pips, min_sl)
    
    # ═══ CORREÇÃO #2: SL máximo ═══
    max_sl = MAX_SL_PIPS_PROPOSED if not is_metal else MAX_SL_TICKS_XAU
    sl_pips_capped = min(sl_pips_fixed, max_sl)
    
    # ═══ CORREÇÃO #3: TP = SL * RR (garantido) ═══
    sl_new, tp_new = calculate_sl_tp(direction, entry, sl_pips_capped, rr, pip, is_metal)
    sl_dist_new = abs(entry - sl_new)
    tp_dist_new = abs(tp_new - entry)
    rr_new = tp_dist_new / sl_dist_new if sl_dist_new > 0 else 0
    
    # ═══ CORREÇÃO #4: Volume baseado no SL real ═══
    vol, risk_pct = calculate_volume(BALANCE, sl_pips_capped, pair, None)
    risk_dollar = BALANCE * risk_pct / 100
    
    unit = 'ticks' if is_metal else 'pips'
    
    print(f'{"="*60}')
    print(f'{pair} {direction} | {strategy} | RR={rr}:1')
    print(f'  SL original: {sl_pips:.1f}{unit} → corrigido: {sl_pips_capped:.1f}{unit}')
    if sl_pips != sl_pips_capped:
        print(f'    {"⚠️ SL ajustado!" if sl_pips < min_sl else "🔧 SL CAPADO"}')
    
    print(f'  ANTES: SL={sl_old:.5f} TP={tp_old:.5f} | dist SL={sl_dist_old/pip:.1f}{unit} TP={tp_dist_old/pip:.1f}{unit}')
    print(f'  DEPOIS: SL={sl_new:.5f} TP={tp_new:.5f} | dist SL={sl_dist_new/pip:.1f}{unit} TP={tp_dist_new/pip:.1f}{unit}')
    print(f'  RR: {rr_new:.2f}:1 | Vol: {vol:.2f} lot | Risco: {risk_pct:.1f}% = ${risk_dollar:.2f}')
    
    # Verificar sanidade
    issues = []
    if sl_dist_old == 0:
        issues.append('❌ SL=ENTRY — sem stop loss!')
    if sl_pips > max_sl:
        issues.append(f'⚠️ SL muito longo ({sl_pips:.0f}{unit})')
    if abs(rr_new - rr) > 0.05:
        issues.append(f'⚠️ RR incorreto ({rr_new:.1f} vs {rr})')
    
    if issues:
        for i in issues:
            print(f'  {i}')
    else:
        print(f'  ✅ OK')
    print()


# ═══ TESTAR TODAS AS POSIÇÕES ATUAIS ═══
print('VALIDAÇÃO DE CORREÇÕES SL/TP')
print(f'Balance: ${BALANCE:.2f} | MAX_SL forex={MAX_SL_PIPS_PROPOSED}p | MAX_SL XAU={MAX_SL_TICKS_XAU}t')
print()

# Posições reais do MT5
validate_trade('BUY',  'USDJPY', 159.395, 0.0,    'FVG+CRT')      # ❌ SL=0
validate_trade('SELL', 'EURUSD', 1.16242, 40.3,   'SMC Fractal')   # SL longo
validate_trade('SELL', 'EURJPY', 185.463, 31.8,   'SMC Fractal')   # OK
validate_trade('BUY',  'USDCAD', 1.38356, 40.6,   'SMC Fractal')   # SL longo
validate_trade('SELL', 'XAUUSD', 4455.64, 22.0,   'FVG+CRT', 3.0) # XAU
validate_trade('SELL', 'XAUUSD', 4452.94, 24.0,   'FVG+CRT', 3.0) # XAU

print('='*60)
print('RESUMO:')
print('  Correção #1: SL mínimo = 15p forex / 200t XAU (resolve USDJPY SL=0)')
print('  Correção #2: SL máximo = 30p forex / 300t XAU (resolve EURUSD 40p)')
print('  Correção #3: TP = SL × RR garantido (resolve RR errado)')
print('  Correção #4: Volume recalculado após cap do SL')
