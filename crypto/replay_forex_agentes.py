#!/usr/bin/env python3
"""
REPLAY ANALÍTICO FOREX — Assertividade por agente no sistema forex
Usa agentes forex (multi_agent.py) + dados TradingView FX_IDC
"""
import sys, json, subprocess, os
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

sys.path.insert(0, str(Path.home() / '.hermes' / 'scripts'))
from multi_agent import PerfilAgent, SessaoAgent, EstruturaAgent, PadraoAgent, ConfluenciaAgent

VENV_PYTHON = os.path.expanduser('~/.hermes/hermes-agent/venv/bin/python')

def get_tv_data(symbol, exchange='FX_IDC', n_bars=3000):
    """Extrai dados M15 do TradingView."""
    code = f"""
from tvDatafeed import TvDatafeed, Interval
tv = TvDatafeed()
data = tv.get_hist(symbol='{symbol}', exchange='{exchange}', interval=Interval.in_15_minute, n_bars={n_bars})
import json
if len(data) == 0: print('EMPTY')
else:
    r = {{'high': data['high'].values.tolist(), 'low': data['low'].values.tolist(),
         'close': data['close'].values.tolist(), 'open': data['open'].values.tolist(),
         'volume': data['volume'].values.tolist() if 'volume' in data.columns else []}}
    print(json.dumps(r))
"""
    r = subprocess.run([VENV_PYTHON, '-c', code], capture_output=True, text=True, timeout=30)
    if r.returncode != 0 or r.stdout.strip() == 'EMPTY': return None
    return json.loads(r.stdout.strip())

# ═══ CONFIG ═══
RR = 3.0
SIM_DAYS = 10  # ~10 dias de M15
FOREX_PAIRS = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
PIP_SIZES = {'EURUSD': 0.0001, 'GBPUSD': 0.0001, 'USDJPY': 0.01, 'AUDUSD': 0.0001}

class ForexAgentAnalytics:
    """Analisa performance individual de cada agente forex."""
    
    def __init__(self, pair='EURUSD'):
        self.pair = pair
        self.pip = PIP_SIZES.get(pair, 0.0001)
        
        # Inicializar agentes forex
        self.perfil = PerfilAgent()
        self.sessao = SessaoAgent()
        self.estrutura = EstruturaAgent()
        self.padrao = PadraoAgent()
        self.confluencia = ConfluenciaAgent()
        
        # Carregar dados
        data = get_tv_data(pair, 'FX_IDC', min(SIM_DAYS * 24 * 4, 4000))
        if data is None:
            raise Exception(f"Sem dados para {pair}")
        
        self.h = np.array(data['high'])
        self.l = np.array(data['low'])
        self.c = np.array(data['close'])
        self.o = np.array(data['open'])
        
        # Stats
        self.agent_stats = {
            'perfil':      {'signals': 0, 'wins': 0, 'losses': 0, 'total_r': 0},
            'sessao':      {'signals': 0, 'wins': 0, 'losses': 0, 'total_r': 0},
            'estrutura':   {'signals': 0, 'wins': 0, 'losses': 0, 'total_r': 0},
            'padrao':      {'signals': 0, 'wins': 0, 'losses': 0, 'total_r': 0},
            'confluencia': {'signals': 0, 'wins': 0, 'losses': 0, 'total_r': 0},
        }
        self.council_trades = []
    
    def _simulate_trade(self, direction, entry, sl_pips, idx):
        """Simula resultado do trade."""
        if direction not in ('BUY', 'SELL'): return None
        
        if direction == 'BUY':
            sl_price = entry - sl_pips
            tp_price = entry + sl_pips * RR
        else:
            sl_price = entry + sl_pips
            tp_price = entry - sl_pips * RR
        
        for j in range(idx, min(idx + 500, len(self.c))):
            if direction == 'BUY':
                if self.l[j] <= sl_price: return {'result': 'LOSS', 'rr': -1}
                if self.h[j] >= tp_price: return {'result': 'WIN', 'rr': RR}
            else:
                if self.h[j] >= sl_price: return {'result': 'LOSS', 'rr': -1}
                if self.l[j] <= tp_price: return {'result': 'WIN', 'rr': RR}
        return None
    
    def run(self):
        """Executa replay completo."""
        print(f"\n═══ {self.pair} ═══")
        print(f"Velas: {len(self.c)} M15 (~{len(self.c)//96:.0f} dias)")
        
        step = 4  # 4 velas M15 = 1 hora
        signals_checked = 0
        
        for idx in range(100, len(self.c) - 200, step):
            h = self.h[:idx]
            l = self.l[:idx]
            c = self.c[:idx]
            o = self.o[:idx]
            
            if len(c) < 50: continue
            
            # Calcular daily_bias real
            if len(c) >= 96:  # ~1 dia em M15
                prev_day_open = c[-96]
                daily_bias = 'BUY' if c[-1] > prev_day_open else 'SELL'
            else:
                daily_bias = 'NEUTRAL'
            
            # ═══ ANÁLISE DE CADA AGENTE ═══
            hour = datetime.now(timezone.utc).hour
            
            # 1. Perfil (contexto, não direção)
            p_dir, p_conf, p_msg = self.perfil.analyze(self.pair, hour)
            
            # 2. Sessão (volatilidade, não direção)
            s_dir, s_conf, s_msg = self.sessao.analyze(h, l, c, self.pip)
            
            # 3. Estrutura (CRT pattern, precisa de daily_bias)
            e_dir, e_conf, e_msg = self.estrutura.analyze(h, l, c, daily_bias)
            
            # 4. Padrão (FVG)
            pat_dir, pat_conf, pat_sig = self.padrao.analyze(h, l, c, e_dir if e_dir != 'NEUTRAL' else daily_bias, self.pip)
            
            # 5. Confluência (conselho)
            c_dir, c_conf, c_msg = self.confluencia.analyze(self.pair, h, l, c, daily_bias, self.pip)
            
            signals_checked += 1
            
            # SL típico de 15 pips
            sl_pips = 15 * self.pip
            
            # ═══ SIMULAR CADA AGENTE ISOLADAMENTE ═══
            
            # Perfil
            if p_dir != 'NEUTRAL':
                r = self._simulate_trade(p_dir, c[-1], sl_pips, idx)
                if r:
                    self.agent_stats['perfil']['signals'] += 1
                    self.agent_stats['perfil']['total_r'] += r['rr']
                    if r['result'] == 'WIN': self.agent_stats['perfil']['wins'] += 1
                    else: self.agent_stats['perfil']['losses'] += 1
            
            # Sessão
            if s_dir != 'NEUTRAL':
                r = self._simulate_trade(s_dir, c[-1], sl_pips, idx)
                if r:
                    self.agent_stats['sessao']['signals'] += 1
                    self.agent_stats['sessao']['total_r'] += r['rr']
                    if r['result'] == 'WIN': self.agent_stats['sessao']['wins'] += 1
                    else: self.agent_stats['sessao']['losses'] += 1
            
            # Estrutura
            if e_dir != 'NEUTRAL':
                r = self._simulate_trade(e_dir, c[-1], sl_pips, idx)
                if r:
                    self.agent_stats['estrutura']['signals'] += 1
                    self.agent_stats['estrutura']['total_r'] += r['rr']
                    if r['result'] == 'WIN': self.agent_stats['estrutura']['wins'] += 1
                    else: self.agent_stats['estrutura']['losses'] += 1
            
            # Padrão (FVG)
            if pat_dir != 'NEUTRAL' and pat_sig:
                entry = pat_sig.get('entry', c[-1])
                r = self._simulate_trade(pat_dir, entry, sl_pips, idx)
                if r:
                    self.agent_stats['padrao']['signals'] += 1
                    self.agent_stats['padrao']['total_r'] += r['rr']
                    if r['result'] == 'WIN': self.agent_stats['padrao']['wins'] += 1
                    else: self.agent_stats['padrao']['losses'] += 1
            
            # Confluência (conselho)
            if c_dir != 'NEUTRAL':
                r = self._simulate_trade(c_dir, c[-1], sl_pips, idx)
                if r:
                    self.council_trades.append({
                        'direction': c_dir, 'entry': c[-1],
                        'result': r['result'], 'rr': r['rr']
                    })
        
        return signals_checked
    
    def report(self):
        """Relatório de assertividade."""
        print(f"\n  {'Agente':<16s} {'Sinais':>7s} {'Wins':>6s} {'Losses':>7s} {'WR':>7s} {'R':>8s}")
        print(f"  {'─'*57}")
        
        best_wr, best_agent = 0, ''
        
        for name in ['perfil', 'sessao', 'estrutura', 'padrao', 'confluencia']:
            s = self.agent_stats[name]
            if s['signals'] == 0: continue
            wr = s['wins'] / s['signals'] * 100
            rr = s['total_r']
            bar = '█' * int(wr / 5)
            print(f"  {name:<16s} {s['signals']:7d} {s['wins']:6d} {s['losses']:7d} {wr:6.1f}% {rr:+8.1f}R {bar}")
            if wr > best_wr:
                best_wr, best_agent = wr, name
        
        if self.council_trades:
            cw = sum(1 for t in self.council_trades if t['result'] == 'WIN')
            cl = sum(1 for t in self.council_trades if t['result'] == 'LOSS')
            ct = len(self.council_trades)
            cwr = cw / ct * 100 if ct > 0 else 0
            cr = sum(t['rr'] for t in self.council_trades)
            print(f"  {'CONSELHO':<16s} {ct:7d} {cw:6d} {cl:7d} {cwr:6.1f}% {cr:+8.1f}R {'█'*int(cwr/5)}")
        
        return best_agent, best_wr, cwr if self.council_trades else 0


# ═══ MAIN ═══
print(f"═══ REPLAY ANALÍTICO FOREX — TradingView M15 ~10 dias ═══")
print()

results = []
for pair in FOREX_PAIRS:
    try:
        a = ForexAgentAnalytics(pair)
        a.run()
        best, bwr, cwr = a.report()
        results.append({'pair': pair, 'best_agent': best, 'best_wr': bwr, 'council_wr': cwr})
    except Exception as e:
        print(f"  {pair}: ERRO — {e}")

print(f"\n═══ CONSOLIDADO FOREX ═══")
print(f"  {'Par':<10s} {'Melhor Agente':<16s} {'WR Agente':>10s} {'WR Conselho':>12s}")
print(f"  {'─'*52}")
for r in results:
    print(f"  {r['pair']:<10s} {r['best_agent']:<16s} {r['best_wr']:>9.1f}% {r['council_wr']:>11.1f}%")
