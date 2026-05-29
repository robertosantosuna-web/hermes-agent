#!/usr/bin/env python3
"""
CRYPTO PAIR SELECTOR — Seleção dinâmica dos melhores pares
Baseado em: volatilidade, volume, correlação, momentum
"""
import numpy as np
import yfinance as yf

class CryptoPairSelector:
    """Seleciona os melhores pares crypto para operar no momento."""
    
    # Pares disponíveis com perfil
    ALL_PAIRS = {
        'BTCUSD':  {'sym': 'BTC-USD',  'pip': 1.0,   'tier': 'S', 'correl': 'base'},
        'ETHUSD':  {'sym': 'ETH-USD',  'pip': 0.1,   'tier': 'S', 'correl': 'btc_high'},
        'DOGEUSD': {'sym': 'DOGE-USD', 'pip': 0.001, 'tier': 'A', 'correl': 'meme'},
        'BNBUSD':  {'sym': 'BNB-USD',  'pip': 0.1,   'tier': 'A', 'correl': 'exchange'},
        'XRPUSD':  {'sym': 'XRP-USD',  'pip': 0.001, 'tier': 'B', 'correl': 'btc_med'},
        'ADAUSD':  {'sym': 'ADA-USD',  'pip': 0.001, 'tier': 'B', 'correl': 'btc_high'},
    }
    
    def __init__(self, max_pairs=5):
        self.max_pairs = max_pairs
        self.selected = []
    
    def analyze_volatility(self, sym, period='5d'):
        """Calcula volatilidade recente como % do preço."""
        try:
            df = yf.Ticker(sym).history(period=period, interval='1h')
            if len(df) < 20: return 0
            returns = df['Close'].pct_change().dropna()
            vol = returns.std() * 100  # volatilidade diária em %
            return vol
        except:
            return 0
    
    def analyze_momentum(self, sym, period='5d'):
        """Momentum de curto prazo."""
        try:
            df = yf.Ticker(sym).history(period=period, interval='1h')
            if len(df) < 10: return 0
            return (df['Close'].values[-1] / df['Close'].values[-50] - 1) * 100 if len(df) >= 50 else \
                   (df['Close'].values[-1] / df['Close'].values[0] - 1) * 100
        except:
            return 0
    
    def select_best_pairs(self):
        """Seleciona os melhores pares para operar agora."""
        scores = []
        
        for name, cfg in self.ALL_PAIRS.items():
            sym = cfg['sym']
            
            # Volatilidade (prefere alta, mas não extrema)
            vol = self.analyze_volatility(sym)
            if vol < 0.08:  # menos de 0.08% = muito parado (alinhado com BAIXA_VOL)
                continue
            
            # Momentum (prefere tendência clara)
            mom = self.analyze_momentum(sym)
            
            # Score composto
            vol_score = min(vol * 10, 40)  # max 40pts por volatilidade
            mom_score = min(abs(mom) * 2, 30)  # max 30pts por momentum
            tier_bonus = {'S': 30, 'A': 20, 'B': 10}.get(cfg['tier'], 0)
            
            total = vol_score + mom_score + tier_bonus
            direction = 'BUY' if mom > 1 else ('SELL' if mom < -1 else 'NEUTRAL')
            
            scores.append({
                'pair': name, 'sym': sym, 'pip': cfg['pip'],
                'vol': round(vol, 2), 'mom': round(mom, 1),
                'score': round(total, 1), 'direction': direction,
                'correl': cfg['correl']
            })
        
        # Ordenar por score e selecionar top N
        scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Evitar pares muito correlacionados (max 2 do mesmo grupo)
        selected = []
        correl_count = {}
        
        for s in scores:
            corr = s['correl']
            if correl_count.get(corr, 0) >= 2:
                continue  # Já tem 2 pares deste grupo
            
            selected.append(s)
            correl_count[corr] = correl_count.get(corr, 0) + 1
            
            if len(selected) >= self.max_pairs:
                break
        
        self.selected = selected
        return selected
    
    def get_active_pairs(self):
        """Retorna dicionário de pares ativos para o bot."""
        if not self.selected:
            self.select_best_pairs()
        
        return {s['pair']: (s['sym'], s['pip']) for s in self.selected}
    
    def get_pair_direction(self, pair):
        """Retorna direção preferencial do par (momentum)."""
        for s in self.selected:
            if s['pair'] == pair:
                return s['direction']
        return 'NEUTRAL'
    
    def print_summary(self):
        """Imprime resumo da seleção."""
        if not self.selected:
            self.select_best_pairs()
        
        print(f"\n{'Pair':8s} {'Vol':>6s} {'Mom':>7s} {'Score':>6s} {'Dir':>6s} {'Correl':>8s}")
        print('-' * 48)
        for s in self.selected:
            print(f"{s['pair']:8s} {s['vol']:5.1f}% {s['mom']:+6.1f}% {s['score']:6.1f} {s['direction']:>6s} {s['correl']:>8s}")


if __name__ == '__main__':
    selector = CryptoPairSelector(max_pairs=5)
    selector.select_best_pairs()
    selector.print_summary()
    print(f"\nPares ativos: {list(selector.get_active_pairs().keys())}")
