#!/usr/bin/env python3
"""
ANÁLISE DE FATORES DE INFLUÊNCIA — CRYPTO
Identifica o que realmente afeta a assertividade dos trades
Fatores: BTC Dominance, Fear & Greed, S&P 500, Volume, Correlação BTC
"""
import json, requests, sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import numpy as np
import yfinance as yf

def get_fear_greed():
    """Fear & Greed Index (0-100). <25 = medo extremo, >75 = ganância."""
    try:
        r = requests.get('https://api.alternative.me/fng/?limit=30', timeout=10)
        data = r.json()['data']
        return [{'date': d['timestamp'], 'value': int(d['value']), 
                 'classification': d['value_classification']} for d in data]
    except:
        return []

def get_btc_dominance():
    """BTC Dominance via CoinGecko (grátis)."""
    try:
        r = requests.get('https://api.coingecko.com/api/v3/global', timeout=10)
        data = r.json()['data']
        return {
            'btc_dominance': data['market_cap_percentage']['btc'],
            'eth_dominance': data['market_cap_percentage']['eth'],
            'total_mcap': data['total_market_cap']['usd'],
            'total_volume': data['total_volume']['usd'],
        }
    except:
        return {}

def get_sp500_correlation():
    """Correlação S&P 500 vs BTC nos últimos 30 dias."""
    try:
        sp = yf.Ticker('^GSPC').history(period='30d', interval='1d')
        btc = yf.Ticker('BTC-USD').history(period='30d', interval='1d')
        if len(sp) < 10 or len(btc) < 10: return None
        
        sp_ret = sp['Close'].pct_change().dropna()
        btc_ret = btc['Close'].pct_change().dropna()
        
        # Alinhar índices
        common = sp_ret.index.intersection(btc_ret.index)
        if len(common) < 10: return None
        
        corr = np.corrcoef(sp_ret[common], btc_ret[common])[0][1]
        
        return {
            'correlation': round(corr, 3),
            'sp500_change_30d': round((sp['Close'].values[-1] / sp['Close'].values[0] - 1) * 100, 1),
            'btc_change_30d': round((btc['Close'].values[-1] / btc['Close'].values[0] - 1) * 100, 1),
        }
    except:
        return None

def analyze_factors():
    """Análise completa dos fatores de influência."""
    print(f"═══ FATORES DE INFLUÊNCIA — CRYPTO ═══")
    print(f"Data: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} UTC")
    print()
    
    # 1. Fear & Greed
    print("[1/3] Fear & Greed Index...")
    fng = get_fear_greed()
    if fng:
        current = fng[0]
        avg_7d = np.mean([d['value'] for d in fng[:7]])
        avg_30d = np.mean([d['value'] for d in fng])
        print(f"  Atual: {current['value']} — {current['classification']}")
        print(f"  Média 7d: {avg_7d:.0f} | 30d: {avg_30d:.0f}")
        
        # Interpretação
        if current['value'] < 25:
            print(f"  📉 Medo extremo → potencial fundo, favorece BUY")
        elif current['value'] > 75:
            print(f"  📈 Ganância extrema → potencial topo, favorece SELL")
        elif current['value'] > 60:
            print(f"  📊 Ganância → cautela em compras")
        elif current['value'] < 40:
            print(f"  📊 Medo → oportunidade de compra")
    print()
    
    # 2. BTC Dominance
    print("[2/3] BTC Dominance (CoinGecko)...")
    dom = get_btc_dominance()
    if dom:
        btc_d = dom['btc_dominance']
        print(f"  BTC Dominance: {btc_d:.1f}%")
        print(f"  ETH Dominance: {dom['eth_dominance']:.1f}%")
        print(f"  Market Cap: ${dom['total_mcap']/1e12:.2f}T")
        
        # Interpretação
        if btc_d > 60:
            print(f"  🔼 BTC Dominance alto → alts pressionados, focar BTC")
        elif btc_d < 45:
            print(f"  🔽 BTC Dominance baixo → altseason potencial, alts podem voar")
        else:
            print(f"  ➡️ Neutro — balanceado")
    print()
    
    # 3. S&P 500 Correlation
    print("[3/3] S&P 500 vs BTC...")
    sp = get_sp500_correlation()
    if sp:
        print(f"  Correlação 30d: {sp['correlation']:.2f}")
        print(f"  S&P 500 30d: {sp['sp500_change_30d']:+.1f}%")
        print(f"  BTC 30d: {sp['btc_change_30d']:+.1f}%")
        
        if abs(sp['correlation']) > 0.5:
            print(f"  ⚠️ Alta correlação com S&P → eventos macro afetam crypto")
        else:
            print(f"  ✅ Baixa correlação → crypto descorrelacionado (bom)")
    print()
    
    # ═══ IMPACTO NOS TRADES ═══
    print("═══ IMPACTO ESTIMADO NOS TRADES ═══")
    
    impacts = []
    
    if fng:
        current = fng[0]['value']
        if current < 30:
            impacts.append(('Fear & Greed', 'BUY +15', 'Medo extremo favorece compras'))
        elif current > 70:
            impacts.append(('Fear & Greed', 'SELL +15', 'Ganância favorece vendas'))
    
    if dom:
        btc_d = dom['btc_dominance']
        if btc_d > 58:
            impacts.append(('BTC Dominance', 'Focar BTC/ETH', f'Dominância {btc_d:.0f}% — alts fracos'))
        elif btc_d < 45:
            impacts.append(('BTC Dominance', 'Alts +10', f'Dominância {btc_d:.0f}% — altseason'))
    
    if sp and abs(sp['correlation']) > 0.6:
        if sp['sp500_change_30d'] < -3:
            impacts.append(('S&P 500', 'SELL +10', 'Mercado tradicional em queda'))
        elif sp['sp500_change_30d'] > 3:
            impacts.append(('S&P 500', 'BUY +10', 'Mercado tradicional em alta'))
    
    # Correlação entre os próprios pares (já medimos: 85% sincronia)
    impacts.append(('Correlação interna', 'MAX 1 trade', '85% dos dias mesma direção'))
    
    print(f"  {'Fator':<20s} {'Viés':<15s} {'Razão'}")
    print(f"  {'─'*60}")
    for factor, bias, reason in impacts:
        print(f"  {factor:<20s} {bias:<15s} {reason}")
    
    # Salvar
    output = {
        'date': datetime.now(timezone.utc).isoformat(),
        'fear_greed': fng[0] if fng else None,
        'btc_dominance': dom,
        'sp500': sp,
        'impacts': [{'factor': f, 'bias': b, 'reason': r} for f, b, r in impacts]
    }
    
    path = Path.home() / '.hermes' / 'crypto' / 'macro_factors.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n  Salvo: {path}")
    return output


if __name__ == '__main__':
    analyze_factors()
