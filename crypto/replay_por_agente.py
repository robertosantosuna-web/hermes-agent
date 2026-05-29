#!/usr/bin/env python3
"""
REPLAY ANALÍTICO POR AGENTE — Mostra assertividade individual de cada agente
Simula como cada agente agiria isoladamente vs decisão do conselho
"""
import sys, time, json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
from tradingview_feed import TradingViewFeed
from crypto_multi_agent import CryptoConfluencia, PadraoAgent, TendenciaAgent, VolatilidadeAgent, SessaoAgent, FluxoAgent

RR = 3.0
MIN_CONFIDENCE = 55
SIM_DAYS = 2
SIM_SPEED = 0  # 0 = instantâneo

class AgentAnalytics:
    """Analisa performance individual de cada agente."""
    
    def __init__(self, pair='BTCUSD', days=SIM_DAYS):
        self.pair = pair
        self.feed = TradingViewFeed()
        self.agent = CryptoConfluencia()
        
        # Carregar dados
        h, l, c, o, v = self.feed.get_candles(pair, '1m', min(days * 1440, 4000))
        if c is None or len(c) < 200:
            raise Exception(f"Dados insuficientes: {len(c) if c is not None else 0}")
        
        self.h, self.l, self.c, self.o, self.v = h, l, c, o, v
        
        # Resultados por agente
        self.agent_stats = {
            'volatilidade': {'signals': 0, 'wins': 0, 'losses': 0, 'total_r': 0, 'votes': []},
            'tendencia':    {'signals': 0, 'wins': 0, 'losses': 0, 'total_r': 0, 'votes': []},
            'padrao':       {'signals': 0, 'wins': 0, 'losses': 0, 'total_r': 0, 'votes': []},
            'sessao':       {'signals': 0, 'wins': 0, 'losses': 0, 'total_r': 0, 'votes': []},
            'fluxo':        {'signals': 0, 'wins': 0, 'losses': 0, 'total_r': 0, 'votes': []},
        }
        self.council_trades = []
        self.position = None
        self.balance = 1000
    
    def _get_votes(self, idx):
        """Obtém votos individuais de cada agente no ponto atual."""
        h = self.h[:idx]
        l = self.l[:idx]
        c = self.c[:idx]
        o = self.o[:idx]
        v = self.v[:idx] if self.v is not None else None
        
        if len(c) < 200: return None
        
        atr_pct = np.mean([max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1]))
                          for i in range(1, min(20, len(c)))]) / c[-1]
        
        pip = 1.0
        btc_chg = (c[-1] / c[-60] - 1) * 100 if len(c) >= 60 and c[-60] > 0 else 0
        daily_levels = {'resistance': max(h[-100:]), 'support': min(l[-100:])}
        
        votes = {}
        
        # 1. Volatilidade
        _, _, v_info = self.agent.volatilidade.analyze(h, l, c, pip)
        votes['volatilidade'] = {
            'regime': v_info.get('regime', '?'),
            'atr_pct': v_info.get('atr_pct', 0),
            'sl_rec': v_info.get('sl_recommend', 0.2)
        }
        
        # 2. Tendência
        t_dir, t_conf, t_msg = self.agent.tendencia.analyze(h, l, c)
        votes['tendencia'] = {'direction': t_dir, 'confidence': t_conf, 'msg': t_msg}
        
        if t_dir == 'NEUTRAL':
            return votes  # sem tendência, sem padrão
        
        # 3. Padrão
        p_dir, p_conf, p_sig = self.agent.padrao.analyze(h, l, c, o, t_dir, pip, v, daily_levels)
        votes['padrao'] = {
            'direction': p_dir, 'confidence': p_conf,
            'pattern': p_sig.get('type') if p_sig else None,
            'quality': p_sig.get('quality', 0) if p_sig else 0,
            'entry': p_sig.get('entry') if p_sig else None
        }
        
        # 4. Sessão
        s_dir, s_conf, s_msg = self.agent.sessao.analyze()
        hour_bonus = self.agent.sessao.get_hour_bonus()
        votes['sessao'] = {'direction': s_dir, 'confidence': s_conf, 'hour_bonus': hour_bonus}
        
        # 5. Fluxo
        f_dir, f_conf, f_msg = self.agent.fluxo.analyze(self.pair, btc_chg)
        votes['fluxo'] = {'direction': f_dir, 'confidence': f_conf, 'btc_chg': btc_chg}
        
        return votes
    
    def _simulate_single_agent(self, direction, entry, sl_pct, idx):
        """Simula trade para um agente individual."""
        if direction == 'NEUTRAL' or entry is None:
            return None
        
        if direction == 'BUY':
            sl_price = entry * (1 - sl_pct/100)
            tp_price = entry * (1 + sl_pct*RR/100)
        else:
            sl_price = entry * (1 + sl_pct/100)
            tp_price = entry * (1 - sl_pct*RR/100)
        
        # Simular nas velas seguintes
        for j in range(idx, min(idx + 500, len(self.c))):
            if direction == 'BUY':
                if self.l[j] <= sl_price: return {'result': 'LOSS', 'rr': -1}
                if self.h[j] >= tp_price: return {'result': 'WIN', 'rr': RR}
            else:
                if self.h[j] >= sl_price: return {'result': 'LOSS', 'rr': -1}
                if self.l[j] <= tp_price: return {'result': 'WIN', 'rr': RR}
        
        return None  # não bateu SL nem TP
    
    def run(self):
        """Executa replay completo com análise por agente."""
        print(f"═══ REPLAY ANALÍTICO: {self.pair} ═══")
        print(f"Velas: {len(self.c)} | Período: ~{len(self.c)/1440:.1f} dias")
        print()
        
        step = 30  # analisar a cada 30 velas (30 min)
        signals_checked = 0
        council_signals = 0
        
        for idx in range(200, len(self.c) - 300, step):
            votes = self._get_votes(idx)
            if votes is None: continue
            
            signals_checked += 1
            
            # Verificar se cada agente individualmente geraria sinal
            t_dir = votes['tendencia']['direction']
            if t_dir == 'NEUTRAL': continue
            
            p_entry = votes['padrao'].get('entry')
            p_quality = votes['padrao'].get('quality', 0)
            
            if p_entry is None or p_quality < 50: continue
            
            council_signals += 1
            atr_pct = votes['volatilidade']['atr_pct']
            sl_rec = votes['volatilidade']['sl_rec']
            sl_pct = max(sl_rec, atr_pct * 1.5, 0.15)
            
            # ═══ SIMULAR CADA AGENTE SEPARADAMENTE ═══
            
            # 1. Tendência sozinho (ignora padrão, só EMA)
            t_result = self._simulate_single_agent(t_dir, self.c[idx], sl_pct, idx)
            if t_result:
                self.agent_stats['tendencia']['signals'] += 1
                self.agent_stats['tendencia']['total_r'] += t_result['rr']
                if t_result['result'] == 'WIN':
                    self.agent_stats['tendencia']['wins'] += 1
                else:
                    self.agent_stats['tendencia']['losses'] += 1
                self.agent_stats['tendencia']['votes'].append(t_result['result'])
            
            # 2. Padrão sozinho (entra em qualquer OB, ignora tendência)
            # Testar BUY e SELL separadamente
            for test_dir in ['BUY', 'SELL']:
                pat, score = self.agent.padrao.detector.find_best_pattern(
                    self.h[:idx], self.l[:idx], self.c[:idx], self.o[:idx], 
                    test_dir, self.v[:idx] if self.v is not None else None,
                    {'resistance': max(self.h[:idx][-100:]), 'support': min(self.l[:idx][-100:])}
                )
                if pat and score >= 50:
                    p_result = self._simulate_single_agent(test_dir, pat['entry'], sl_pct, idx)
                    if p_result:
                        self.agent_stats['padrao']['signals'] += 1
                        self.agent_stats['padrao']['total_r'] += p_result['rr']
                        if p_result['result'] == 'WIN':
                            self.agent_stats['padrao']['wins'] += 1
                        else:
                            self.agent_stats['padrao']['losses'] += 1
                        self.agent_stats['padrao']['votes'].append(p_result['result'])
                    break  # só conta 1 padrão por iteração
            
            # 3. Sessão sozinho (entra na direção da sessão, ignora resto)
            s_dir = votes['sessao']['direction'] if votes['sessao']['confidence'] >= 50 else 'NEUTRAL'
            if s_dir != 'NEUTRAL':
                s_result = self._simulate_single_agent(s_dir, self.c[idx], sl_pct, idx)
                if s_result:
                    self.agent_stats['sessao']['signals'] += 1
                    self.agent_stats['sessao']['total_r'] += s_result['rr']
                    if s_result['result'] == 'WIN':
                        self.agent_stats['sessao']['wins'] += 1
                    else:
                        self.agent_stats['sessao']['losses'] += 1
                    self.agent_stats['sessao']['votes'].append(s_result['result'])
            
            # 4. Fluxo sozinho
            f_dir = votes['fluxo']['direction'] if votes['fluxo']['confidence'] >= 40 else 'NEUTRAL'
            if f_dir != 'NEUTRAL':
                f_result = self._simulate_single_agent(f_dir, self.c[idx], sl_pct, idx)
                if f_result:
                    self.agent_stats['fluxo']['signals'] += 1
                    self.agent_stats['fluxo']['total_r'] += f_result['rr']
                    if f_result['result'] == 'WIN':
                        self.agent_stats['fluxo']['wins'] += 1
                    else:
                        self.agent_stats['fluxo']['losses'] += 1
                    self.agent_stats['fluxo']['votes'].append(f_result['result'])
            
            # 5. Conselho (tendência + padrão juntos) = decisão real
            if t_dir == votes['padrao'].get('direction', 'NEUTRAL'):
                c_result = self._simulate_single_agent(t_dir, p_entry, sl_pct, idx)
                if c_result:
                    self.council_trades.append({
                        'direction': t_dir,
                        'entry': p_entry,
                        'result': c_result['result'],
                        'rr': c_result['rr'],
                        'quality': p_quality
                    })
    
    def report(self):
        """Relatório final de assertividade por agente."""
        print(f"\n═══ ASSERTIVIDADE POR AGENTE ═══")
        print(f"{'Agente':<16s} {'Sinais':>7s} {'Wins':>6s} {'Losses':>7s} {'WR':>7s} {'R':>8s} {'Contrib':>9s}")
        print("-" * 70)
        
        best_wr = 0
        best_agent = ''
        
        for name in ['tendencia', 'padrao', 'sessao', 'fluxo']:
            s = self.agent_stats[name]
            total = s['signals']
            if total == 0: continue
            wr = s['wins'] / total * 100
            rr = s['total_r']
            
            # Contribuição: quantos % dos sinais do conselho este agente acertaria
            council_total = len(self.council_trades)
            if council_total > 0:
                contrib = s['wins'] / council_total * 100
            else:
                contrib = 0
            
            bar = '█' * int(wr / 5)
            print(f"{name:<16s} {total:7d} {s['wins']:6d} {s['losses']:7d} {wr:6.1f}% {rr:+8.1f}R {contrib:8.1f}% {bar}")
            
            if wr > best_wr:
                best_wr = wr
                best_agent = name
        
        # Conselho
        if self.council_trades:
            cw = sum(1 for t in self.council_trades if t['result'] == 'WIN')
            cl = sum(1 for t in self.council_trades if t['result'] == 'LOSS')
            ct = len(self.council_trades)
            cwr = cw / ct * 100
            cr = sum(t['rr'] for t in self.council_trades)
            bar = '█' * int(cwr / 5)
            print(f"{'CONSELHO':<16s} {ct:7d} {cw:6d} {cl:7d} {cwr:6.1f}% {cr:+8.1f}R {'─':>9s} {bar}")
        
        print()
        print(f"═══ ANÁLISE ═══")
        print(f"  Melhor agente isolado: {best_agent} ({best_wr:.1f}% WR)")
        print(f"  Conselho (tendência+padrão): {cwr:.1f}% WR")
        
        # A contribuição de cada agente para o resultado do conselho
        print(f"\n  Matriz de contribuição:")
        print(f"  {'Agente':<16s} {'Peso':>6s} {'Impacto':>10s}")
        print(f"  {'─'*34}")
        for name, weight in self.agent.weights.items():
            s = self.agent_stats.get(name)
            if not s or s['signals'] == 0: continue
            wr = s['wins'] / s['signals'] * 100
            impacto = (wr - cwr) if cwr > 0 else 0
            status = '⬆️' if impacto > 0 else '⬇️' if impacto < 0 else '➡️'
            print(f"  {name:<16s} {weight:5.1f}x {impacto:+7.1f}pp {status}")
        
        print(f"\n  ⚡ Conclusão: O conselho supera agentes isolados quando:")
        print(f"     Tendência + Padrão concordam (gate atual)")
        print(f"     Sessão e Fluxo adicionam peso mas não decidem sozinhos")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--pair', default='BTCUSD')
    parser.add_argument('--days', type=int, default=2)
    args = parser.parse_args()
    
    SIM_DAYS = args.days
    analytics = AgentAnalytics(pair=args.pair, days=args.days)
    analytics.run()
    analytics.report()
