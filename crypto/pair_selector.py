#!/usr/bin/env python3
"""
CRYPTO PAIR SELECTOR v2 — Anti-correlação USD + Filtro de Volume
Regra: todos os pares são USD-based → correlação natural.
Máximo 1 trade por grupo de correlação, máximo 2 trades simultâneos total.
"""
import numpy as np
import yfinance as yf
import json
from pathlib import Path
from datetime import datetime, timezone

class CryptoPairSelector:
    """Seleciona os melhores pares com anti-correlação e volume mínimo."""
    
    # Pares organizados por grupo de correlação REAL
    # BTC domina → ETH segue (0.85+ corr). Memes são independentes. Exchange tokens também.
    CORREL_GROUPS = {
        'BTC_LARGE_CAP': {  # Alta correlação com BTC
            'pairs': {
                'BTCUSD':  {'sym': 'BTC-USD',  'pip': 1.0,   'tier': 'S'},
                'ETHUSD':  {'sym': 'ETH-USD',  'pip': 0.1,   'tier': 'S'},
            },
            'max_trades': 1,  # Só 1 trade neste grupo por vez
            'description': 'Large caps — seguem BTC'
        },
        'MEME': {  # Memes — vol independente
            'pairs': {
                'DOGEUSD': {'sym': 'DOGE-USD', 'pip': 0.001, 'tier': 'A'},
            },
            'max_trades': 1,
            'description': 'Memes — volatilidade própria'
        },
        'EXCHANGE': {  # Exchange tokens — fundamento próprio
            'pairs': {
                'BNBUSD':  {'sym': 'BNB-USD',  'pip': 0.1,   'tier': 'A'},
            },
            'max_trades': 1,
            'description': 'Exchange tokens — independente'
        },
    }
    
    MAX_TOTAL_TRADES = 1  # Dados: 85% sincronia → 2 trades = risco dobrado
    
    def __init__(self, max_pairs=3):
        self.max_pairs = max_pairs
        self.selected = []
        self.open_trades = self._load_open_trades()
    
    def _load_open_trades(self):
        """Carrega trades abertos para verificar anti-correlação."""
        path = Path.home() / '.hermes' / 'crypto' / 'open_trades.json'
        if path.exists():
            try:
                with open(path) as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _get_active_groups(self):
        """Retorna grupos que já têm trades abertos."""
        active = {}
        for trade in self.open_trades:
            pair = trade.get('pair', '')
            for gname, gcfg in self.CORREL_GROUPS.items():
                if pair in gcfg['pairs']:
                    active[gname] = active.get(gname, 0) + 1
        return active
    
    def _get_active_direction(self):
        """Retorna direção predominante dos trades abertos."""
        directions = [t.get('direction') for t in self.open_trades if t.get('direction')]
        if not directions:
            return None
        # Se todos mesma direção, retorna ela
        if all(d == directions[0] for d in directions):
            return directions[0]
        return 'MIXED'
    
    def analyze_volatility(self, sym, period='5d'):
        """Calcula volatilidade recente como % do preço."""
        try:
            df = yf.Ticker(sym).history(period=period, interval='1h')
            if len(df) < 20: return 0
            returns = df['Close'].pct_change().dropna()
            return returns.std() * 100
        except:
            return 0
    
    def analyze_volume(self, sym):
        """Verifica volume médio diário (em USD)."""
        try:
            df = yf.Ticker(sym).history(period='5d', interval='1h')
            if len(df) < 10: return 0
            return df['Volume'].mean()
        except:
            return 0
    
    def analyze_momentum(self, sym, period='5d'):
        """Momentum de curto prazo."""
        try:
            df = yf.Ticker(sym).history(period=period, interval='1h')
            if len(df) < 10: return 0
            if len(df) >= 50:
                return (df['Close'].values[-1] / df['Close'].values[-50] - 1) * 100
            return (df['Close'].values[-1] / df['Close'].values[0] - 1) * 100
        except:
            return 0
    
    def _get_wr_bonus(self, pair, direction):
        """Calcula bônus baseado na WR histórica do par+direção.
        Backtest v10: DOGE SELL=96%, ETH SELL=92%, DOGE BUY=40%, BNB BUY=50%."""
        # Dados do último backtest realista (v10 com gates)
        wr_data = {
            ('DOGEUSD', 'SELL'): 96,
            ('ETHUSD', 'SELL'): 92,
            ('BTCUSD', 'SELL'): 67,
            ('ETHUSD', 'BUY'): 70,
            ('BNBUSD', 'SELL'): 65,
            ('BNBUSD', 'BUY'): 50,
            ('DOGEUSD', 'BUY'): 40,
        }
        wr = wr_data.get((pair, direction), 50)
        
        if wr >= 90: return 25   # Elite
        elif wr >= 80: return 20  # Excelente
        elif wr >= 70: return 15  # Muito bom
        elif wr >= 60: return 5   # OK
        elif wr >= 50: return 0   # Neutro
        else: return -15          # Penalidade (abaixo de 50%)
    
    def select_best_pairs(self):
        """Seleciona os melhores pares respeitando anti-correlação USD."""
        active_groups = self._get_active_groups()
        active_direction = self._get_active_direction()
        used_groups = dict(active_groups)  # começa com grupos já ocupados
        total_open = len(self.open_trades)
        remaining_slots = max(0, self.MAX_TOTAL_TRADES - total_open)
        
        if remaining_slots == 0:
            self.selected = []
            return []
        
        # Coletar scores por grupo
        group_scores = {}
        
        for gname, gcfg in self.CORREL_GROUPS.items():
            # Grupo já saturado?
            if used_groups.get(gname, 0) >= gcfg['max_trades']:
                continue
            
            best_pair = None
            best_score = 0
            
            for pname, pcfg in gcfg['pairs'].items():
                sym = pcfg['sym']
                
                # Volume mínimo (evitar pares ilíquidos)
                vol_usd = self.analyze_volume(sym)
                if pcfg['tier'] in ('A', 'S') and vol_usd < 100_000:
                    continue  # Tier S/A precisa de volume mínimo
                elif pcfg['tier'] == 'B' and vol_usd < 500_000:
                    continue  # Tier B precisa de volume maior para compensar
                
                # Volatilidade
                vol = self.analyze_volatility(sym)
                if vol < 0.08:  # parado demais
                    continue
                
                # Momentum
                mom = self.analyze_momentum(sym)
                
                # Score base
                vol_score = min(vol * 10, 40)
                mom_score = min(abs(mom) * 2, 30)
                tier_bonus = {'S': 30, 'A': 20, 'B': 10}.get(pcfg['tier'], 0)
                
                # Bônus por performance histórica (WR do par+direção)
                direction = 'BUY' if mom > 1 else ('SELL' if mom < -1 else 'NEUTRAL')
                wr_bonus = self._get_wr_bonus(pname, direction)
                
                total = vol_score + mom_score + tier_bonus + wr_bonus
                
                # Anti-correlação USD: se já tem trade SELL, evitar mais SELL
                if active_direction and direction == active_direction and total_open > 0:
                    total *= 0.5  # penalidade: mesma direção que trade existente
                
                if total > best_score:
                    best_score = total
                    best_pair = {
                        'pair': pname, 'sym': sym, 'pip': pcfg['pip'],
                        'vol': round(vol, 2), 'mom': round(mom, 1),
                        'score': round(total, 1), 'direction': direction,
                        'group': gname, 'tier': pcfg['tier']
                    }
            
            if best_pair:
                group_scores[gname] = best_pair
        
        # Selecionar top grupos (limitado por remaining_slots)
        ranked = sorted(group_scores.values(), key=lambda x: x['score'], reverse=True)
        
        self.selected = ranked[:remaining_slots]
        return self.selected
    
    def get_active_pairs(self):
        """Retorna pares ativos para scan (não inclui os já tradados)."""
        if not self.selected:
            self.select_best_pairs()
        
        return {s['pair']: (s['sym'], s['pip']) for s in self.selected}
    
    def get_pair_direction(self, pair):
        for s in self.selected:
            if s['pair'] == pair:
                return s['direction']
        return 'NEUTRAL'
    
    def can_open_trade(self, pair, direction):
        """Verifica se pode abrir trade respeitando anti-correlação."""
        self.open_trades = self._load_open_trades()
        active_groups = self._get_active_groups()
        active_direction = self._get_active_direction()
        
        # Já no limite global?
        if len(self.open_trades) >= self.MAX_TOTAL_TRADES:
            return False, 'MAX_TRADES atingido (2)'
        
        # Grupo já saturado?
        for gname, gcfg in self.CORREL_GROUPS.items():
            if pair in gcfg['pairs']:
                if active_groups.get(gname, 0) >= gcfg['max_trades']:
                    return False, f'Grupo {gname} saturado'
                
                # Anti-correlação USD: não abrir mesma direção se já tem trade
                if active_direction == direction and len(self.open_trades) > 0:
                    return False, f'Anti-correlação USD: já tem {active_direction}'
        
        return True, 'OK'
    
    def print_summary(self):
        if not self.selected:
            self.select_best_pairs()
        
        if not self.selected:
            print("  Nenhum par disponível (limites de correlação atingidos ou baixo volume)")
            return
        
        print(f"\n  {'Pair':8s} {'Vol':>6s} {'Mom':>7s} {'Score':>6s} {'Dir':>6s} {'Grupo':>16s}")
        print('  ' + '-' * 56)
        for s in self.selected:
            print(f"  {s['pair']:8s} {s['vol']:5.1f}% {s['mom']:+6.1f}% {s['score']:6.1f} {s['direction']:>6s} {s['group']:>16s}")
        
        active = self._get_active_groups()
        if active:
            print(f"\n  ⚡ Trades abertos: {len(self.open_trades)}/{self.MAX_TOTAL_TRADES}")
            for t in self.open_trades:
                print(f"     {t.get('pair','?'):8s} {t.get('direction','?'):4s} @{t.get('entry',0):.4f}")


if __name__ == '__main__':
    selector = CryptoPairSelector(max_pairs=3)
    selector.select_best_pairs()
    selector.print_summary()
    active = selector.get_active_pairs()
    if active:
        print(f"\nPares para scan: {list(active.keys())}")
    else:
        print("\nNenhum par disponível para scan.")
