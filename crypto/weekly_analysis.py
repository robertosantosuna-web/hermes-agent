#!/usr/bin/env python3
"""
PRÉ-ANÁLISE SEMANAL — Força relativa das moedas
Seleciona pares com maior divergência para a semana
Baseado em: COT (Commitment of Traders), performance 7 dias, momentum
"""
import sys, subprocess, json, os
from datetime import datetime, timezone

VENV_PYTHON = os.path.expanduser('~/.hermes/hermes-agent/venv/bin/python')

# Moedas principais
CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF']

# Pares para medir força (cada par revela força relativa entre 2 moedas)
STRENGTH_PAIRS = {
    'EURUSD': ('EUR', 'USD'), 'GBPUSD': ('GBP', 'USD'), 'USDJPY': ('USD', 'JPY'),
    'AUDUSD': ('AUD', 'USD'), 'NZDUSD': ('NZD', 'USD'), 'USDCAD': ('USD', 'CAD'),
    'USDCHF': ('USD', 'CHF'), 'EURGBP': ('EUR', 'GBP'), 'EURJPY': ('EUR', 'JPY'),
    'GBPJPY': ('GBP', 'JPY'), 'AUDJPY': ('AUD', 'JPY'),
}

def get_weekly_performance():
    """Calcula performance de cada moeda nos últimos 7 dias."""
    code = f"""
from tvDatafeed import TvDatafeed, Interval
tv = TvDatafeed()
import json

pairs = {json.dumps(list(STRENGTH_PAIRS.keys()))}
results = {{}}

for pair in pairs:
    try:
        data = tv.get_hist(symbol=pair, exchange='FX_IDC', interval=Interval.in_daily, n_bars=7)
        if len(data) >= 5:
            change = (data['close'].values[-1] / data['close'].values[0] - 1) * 100
            results[pair] = round(change, 2)
    except:
        pass

print(json.dumps(results))
"""
    r = subprocess.run([VENV_PYTHON, '-c', code], capture_output=True, text=True, timeout=30)
    if r.returncode != 0: return {}
    try: return json.loads(r.stdout.strip())
    except: return {}

def calculate_strength(weekly_changes):
    """Calcula força relativa de cada moeda baseado nas mudanças dos pares."""
    scores = {c: 0.0 for c in CURRENCIES}
    counts = {c: 0 for c in CURRENCIES}
    
    for pair, (base, quote) in STRENGTH_PAIRS.items():
        if pair not in weekly_changes: continue
        change = weekly_changes[pair]
        
        # Se o par subiu, a moeda base fortaleceu vs quote
        # EURUSD +1% → EUR forte, USD fraco
        scores[base] += change
        scores[quote] -= change
        counts[base] += 1
        counts[quote] += 1
    
    # Média por moeda
    for c in CURRENCIES:
        if counts[c] > 0:
            scores[c] = scores[c] / counts[c]
    
    return scores

def select_pairs(strength):
    """Seleciona os melhores pares para a semana baseado em divergência de força."""
    ranked = sorted(strength.items(), key=lambda x: x[1], reverse=True)
    
    strongest = ranked[:3]  # 3 moedas mais fortes
    weakest = ranked[-3:]   # 3 moedas mais fracas
    
    pairs = []
    
    for strong_name, strong_score in strongest:
        for weak_name, weak_score in weakest:
            if strong_name == weak_name: continue
            
            divergence = strong_score - weak_score
            
            # Encontrar o par correspondente
            for pair, (base, quote) in STRENGTH_PAIRS.items():
                if base == strong_name and quote == weak_name:
                    direction = 'BUY'
                    pairs.append({'pair': pair, 'direction': direction, 
                                 'divergence': round(divergence, 1),
                                 'strong': strong_name, 'weak': weak_name})
                    break
                elif base == weak_name and quote == strong_name:
                    direction = 'SELL'
                    pairs.append({'pair': pair, 'direction': direction,
                                 'divergence': round(divergence, 1),
                                 'strong': strong_name, 'weak': weak_name})
                    break
    
    # Ordenar por divergência (maior = mais potencial)
    pairs.sort(key=lambda x: abs(x['divergence']), reverse=True)
    
    return pairs[:6]  # top 6 pares


def run_weekly_analysis():
    """Executa análise semanal completa."""
    date_str = datetime.now(timezone.utc).strftime('%d/%m/%Y')
    print(f"═══ PRÉ-ANÁLISE SEMANAL — {date_str} ═══")
    print()
    
    # 1. Performance semanal
    print("[1/3] Calculando performance semanal...")
    changes = get_weekly_performance()
    
    if not changes:
        print("  ❌ Sem dados do TradingView")
        return None
    
    print(f"  {len(changes)} pares analisados")
    print()
    
    # 2. Força das moedas
    print("[2/3] Calculando força relativa...")
    strength = calculate_strength(changes)
    
    print(f"  {'Moeda':<8s} {'Força':>8s} {'Barra'}")
    print(f"  {'─'*30}")
    for name, score in sorted(strength.items(), key=lambda x: x[1], reverse=True):
        bar = '█' * max(1, int(abs(score) * 10))
        print(f"  {name:<8s} {score:+8.2f}%  {bar}")
    
    print()
    
    # 3. Selecionar pares
    print("[3/3] Selecionando pares com maior divergência...")
    selected = select_pairs(strength)
    
    print(f"\n  {'Par':<10s} {'Dir':<6s} {'Diverg':>8s} {'Forte':<8s} {'Fraca':<8s}")
    print(f"  {'─'*46}")
    for s in selected:
        print(f"  {s['pair']:<10s} {s['direction']:<6s} {s['divergence']:+7.1f}%  {s['strong']:<8s} {s['weak']:<8s}")
    
    print()
    
    # 4. Recomendação de alocação
    print("═══ RECOMENDAÇÃO ═══")
    print(f"  Pares prioritários: {[s['pair'] for s in selected[:4]]}")
    direcoes = ', '.join(f"{s['pair']} {s['direction']}" for s in selected[:4])
    print(f"  Direções: {direcoes}")
    
    # Salvar
    output = {
        'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'strength': strength,
        'selected_pairs': selected,
        'weekly_changes': changes
    }
    
    import pathlib
    outfile = pathlib.Path.home() / '.hermes' / 'forex' / 'weekly_analysis.json'
    outfile.parent.mkdir(parents=True, exist_ok=True)
    with open(outfile, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n  Salvo: {outfile}")
    
    return output


if __name__ == '__main__':
    run_weekly_analysis()
