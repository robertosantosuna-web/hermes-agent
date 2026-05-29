#!/usr/bin/env python3
"""
GERADOR DE SISTEMA MULTI-AGENTE FOREX
Cria estrutura completa em qualquer máquina.
Uso: python3 create_forex_system.py
"""
import os, sys, json
from pathlib import Path

HOME = Path.home()
HERMES = HOME / '.hermes'
SCRIPTS = HERMES / 'scripts'
FOREX = HERMES / 'forex'

def create_all():
    print("=" * 60)
    print("  GERADOR DE SISTEMA MULTI-AGENTE FOREX v1.0")
    print("=" * 60)
    
    # Criar diretórios
    for d in [HERMES, SCRIPTS, FOREX, HERMES / 'skills', HERMES / 'brain']:
        d.mkdir(parents=True, exist_ok=True)
    
    # ── 1. MULTI-AGENT SYSTEM ──
    print("\n[1/5] Criando Multi-Agent System...")
    (SCRIPTS / 'multi_agent.py').write_text('''#!/usr/bin/env python3
"""Sistema Multi-Agente de Análise Forex"""
import numpy as np
from datetime import datetime, timezone

class PerfilAgent:
    PERFIS = {
        'EURUSD': {'asia_wr':0.25,'london_wr':0.35,'ny_wr':0.25},
        'GBPUSD': {'asia_wr':0.20,'london_wr':0.30,'ny_wr':0.25},
        'USDJPY': {'asia_wr':0.35,'london_wr':0.20,'ny_wr':0.20},
        'XAUUSD': {'asia_wr':0.40,'london_wr':0.40,'ny_wr':0.35},
    }
    def analyze(self, pair, hour_utc):
        p = self.PERFIS.get(pair, {'asia_wr':0.2,'london_wr':0.25,'ny_wr':0.2})
        if 0 <= hour_utc < 7: sessao = 'Asia'; wr = p['asia_wr']
        elif 7 <= hour_utc < 15: sessao = 'London'; wr = p['london_wr']
        else: sessao = 'NY'; wr = p['ny_wr']
        if wr < 0.15: return 'NEUTRAL', 0, f'{sessao} WR baixo ({wr:.0%})'
        return 'NEUTRAL', int(wr*100), f'{pair} {sessao} WR~{wr:.0%}'

class SessaoAgent:
    def analyze(self, highs, lows, closes, pip_size):
        n = len(closes)
        if n < 40: return 'NEUTRAL', 0, 'Dados insuficientes'
        asia_n = min(240, n)
        asia_range = (max(highs[-asia_n:]) - min(lows[-asia_n:])) / pip_size
        pre_n = min(240, n - asia_n)
        if pre_n < 20: return 'NEUTRAL', 0, ''
        pre_range = (max(highs[-asia_n-pre_n:-asia_n]) - min(lows[-asia_n-pre_n:-asia_n])) / pip_size
        ratio = asia_range / max(pre_range, 1)
        if ratio < 0.5: return 'NEUTRAL', 60, f'Asia contraiu → breakout'
        return 'NEUTRAL', 30, f'Asia normal'

class EstruturaAgent:
    def analyze(self, highs, lows, closes, daily_bias):
        n = len(closes)
        if n < 20: return 'NEUTRAL', 0, ''
        score = 0; signals = []
        ranges = [highs[i]-lows[i] for i in range(-22, -2)]
        if ranges:
            avg = sum(ranges)/len(ranges)
            crt_h, crt_l = highs[-2], lows[-2]
            crt_range = crt_h - crt_l
            if crt_range > avg * 1.3:
                crt_close = closes[-2]
                sw_h, sw_l, sw_c = highs[-1], lows[-1], closes[-1]
                if crt_close < (crt_l + crt_range*0.5) and sw_l < crt_l and sw_c > crt_l:
                    if daily_bias == 'BUY': score += 40; signals.append('CRT')
                elif crt_close > (crt_l + crt_range*0.5) and sw_h > crt_h and sw_c < crt_h:
                    if daily_bias == 'SELL': score += 40; signals.append('CRT')
        if closes[-1] > closes[-n//2] and daily_bias == 'BUY': score += 30; signals.append('SWING')
        elif closes[-1] < closes[-n//2] and daily_bias == 'SELL': score += 30; signals.append('SWING')
        if score >= 40: return daily_bias, score, '+'.join(signals)
        return 'NEUTRAL', score, f'Score={score}'

class PadraoAgent:
    def analyze(self, highs, lows, closes, direction, pip_size, is_metal=False):
        n = len(closes)
        if n < 10: return 'NEUTRAL', 0, {}
        best_score = 0; best = None
        for i in range(6, n-1):
            if direction == 'BUY' and lows[i] > highs[i-2]:
                gap = (lows[i]-highs[i-2])/pip_size
                score = 30 if closes[i] < (max(highs[-20:])+min(lows[-20:]))/2 else 0
                score += 25 if sum(1 for j in range(1,min(10,i)) if closes[i-j]>closes[i-j-1]) > 5 else 0
                if not any(lows[j] <= highs[i-2] for j in range(i+1, min(i+10, n))): score += 20
                if score > best_score and gap >= (100 if is_metal else 1.0):
                    best_score = score; best = {'entry': closes[i], 'direction': 'BUY', 'idx': i, 'gap': gap}
            elif direction == 'SELL' and highs[i] < lows[i-2]:
                gap = (lows[i-2]-highs[i])/pip_size
                score = 30 if closes[i] > (max(highs[-20:])+min(lows[-20:]))/2 else 0
                score += 25 if sum(1 for j in range(1,min(10,i)) if closes[i-j]<closes[i-j-1]) > 5 else 0
                if not any(highs[j] >= lows[i-2] for j in range(i+1, min(i+10, n))): score += 20
                if score > best_score and gap >= (100 if is_metal else 1.0):
                    best_score = score; best = {'entry': closes[i], 'direction': 'SELL', 'idx': i, 'gap': gap}
        if best: return direction, best_score, best
        return 'NEUTRAL', 0, {}

class ConfluenciaAgent:
    def __init__(self):
        self.perfil = PerfilAgent()
        self.sessao = SessaoAgent()
        self.estrutura = EstruturaAgent()
        self.padrao = PadraoAgent()
        self.weights = {'perfil': 1.0, 'sessao': 1.0, 'estrutura': 1.5, 'padrao': 1.2}
    
    def analyze(self, pair, highs, lows, closes, daily_bias, pip_size, is_metal=False):
        hour = datetime.now(timezone.utc).hour
        p_vote, p_conf, p_msg = self.perfil.analyze(pair, hour)
        s_vote, s_conf, s_msg = self.sessao.analyze(highs, lows, closes, pip_size)
        e_vote, e_conf, e_msg = self.estrutura.analyze(highs, lows, closes, daily_bias)
        d_vote, d_conf, d_sig = self.padrao.analyze(highs, lows, closes, daily_bias, pip_size, is_metal)
        
        votes = {
            'perfil': {'vote': p_vote, 'conf': p_conf * self.weights['perfil']},
            'sessao': {'vote': s_vote, 'conf': s_conf * self.weights['sessao']},
            'estrutura': {'vote': e_vote, 'conf': e_conf * self.weights['estrutura']},
            'padrao': {'vote': d_vote, 'conf': d_conf * self.weights['padrao']},
        }
        
        buy_score = sum(v['conf'] for v in votes.values() if v['vote'] == 'BUY')
        sell_score = sum(v['conf'] for v in votes.values() if v['vote'] == 'SELL')
        total = sum(v['conf'] for v in votes.values())
        conf = max(buy_score, sell_score) / max(total, 1) * 100
        
        if buy_score > sell_score and conf >= 30:
            return 'BUY', conf, d_sig or {'entry': closes[-1], 'direction': 'BUY', 'idx': len(closes)-1}
        elif sell_score > buy_score and conf >= 30:
            return 'SELL', conf, d_sig or {'entry': closes[-1], 'direction': 'SELL', 'idx': len(closes)-1}
        return 'NEUTRAL', conf, None
''')
    print("   ✅ multi_agent.py")
    
    # ── 2. FVG QUALITY ──
    (SCRIPTS / 'fvg_quality.py').write_text('''#!/usr/bin/env python3
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
''')
    print("   ✅ fvg_quality.py")
    
    # ── 3. SELF-LEARNING ──
    (SCRIPTS / 'self_learning.py').write_text('''#!/usr/bin/env python3
"""Self-Learning Engine — Ajuste dinâmico de pesos dos agentes"""
import json
from datetime import datetime
from pathlib import Path
import numpy as np

LEARNING_FILE = Path.home() / '.hermes' / 'forex' / 'agent_learning.json'

class SelfLearning:
    def __init__(self):
        self.weights = {'perfil': 1.0, 'sessao': 1.0, 'estrutura': 1.5, 'padrao': 1.2}
        self.history = []
        self.load()
    def load(self):
        if LEARNING_FILE.exists():
            try:
                data = json.loads(LEARNING_FILE.read_text())
                self.weights = data.get('weights', self.weights)
                self.history = data.get('history', [])
            except: pass
    def save(self):
        LEARNING_FILE.parent.mkdir(parents=True, exist_ok=True)
        LEARNING_FILE.write_text(json.dumps({'weights': self.weights, 'history': self.history[-500:], 'updated': datetime.now().isoformat()}, indent=2))
    def record_trade(self, agent_votes, result_r, pair, direction):
        self.history.append({'time': datetime.now().isoformat(), 'pair': pair, 'direction': direction, 'result_r': result_r, 'votes': agent_votes})
        for agent, vote in agent_votes.items():
            if vote == direction:
                self.weights[agent] = min(3.0, self.weights[agent] * (1.05 if result_r > 0 else 0.98))
            elif vote and vote != 'NEUTRAL':
                self.weights[agent] = max(0.3, self.weights[agent] * 0.95)
        self.save()
    def get_stats(self):
        if not self.history: return {'trades': 0, 'wr': 0, 'r_total': 0}
        recent = self.history[-100:]
        wins = sum(1 for t in recent if t['result_r'] > 0)
        return {'trades': len(recent), 'wr': wins/len(recent)*100, 'r_total': sum(t['result_r'] for t in recent), 'weights': self.weights}
''')
    print("   ✅ self_learning.py")
    
    # ── 4. MONITOR 2R/3R ──
    (SCRIPTS / 'forex_realtime_monitor.py').write_text('''#!/usr/bin/env python3
"""Monitor 2R/3R — Breakeven + Trailing Stop"""
import json, os, time, fcntl
from pathlib import Path

FILES = os.path.expanduser('~/.wine/drive_c/users/roberto/AppData/Roaming/MetaQuotes/Terminal/Common/Files')
CMD = os.path.join(FILES, 'hermes_cmd.json')
RESP = os.path.join(FILES, 'hermes_resp.json')
LOCK = os.path.join(FILES, '.monitor_lock')
OPEN_TRADES = Path.home() / '.hermes' / 'forex' / 'open_trades.json'
RR = 3.0; POLL = 3

def acquire_lock():
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except: return None

def release_lock(fd):
    try: fcntl.flock(fd, fcntl.LOCK_UN); os.close(fd)
    except: pass

def mt5_cmd(action, **kw):
    fd = acquire_lock()
    if not fd: return None
    try:
        if os.path.exists(RESP): os.remove(RESP)
        with open(CMD, 'w') as f: f.write(json.dumps({'action': action, **kw}))
        for _ in range(30):
            time.sleep(0.1)
            if os.path.exists(RESP):
                try: return json.loads(open(RESP).read())
                except: pass
        return None
    finally: release_lock(fd)

def status(): return mt5_cmd('status')
def close_sym(sym): return mt5_cmd('close_symbol', symbol=sym)
def modify(ticket, sl, tp=0): return mt5_cmd('modify_position', ticket=int(ticket), sl=sl, tp=tp)
def load_open_trades():
    if OPEN_TRADES.exists():
        try: return json.loads(OPEN_TRADES.read_text())
        except: pass
    return {}

be_done = set(); trail_done = set()
print(f"Monitor 2R/3R — {time.strftime('%H:%M:%S')}")

while True:
    try:
        s = status()
        if not s or s.get('status') != 'ok': time.sleep(POLL); continue
        open_trades = load_open_trades()
        active = set()
        for p in s.get('positions_data', []):
            ticket = str(p.get('ticket', '')); sym = p.get('symbol', '')
            profit = p.get('profit', 0); entry = p.get('entry', 0)
            sl = p.get('sl', 0); typ = p.get('type', '')
            if not ticket or not entry: continue
            active.add(ticket)
            trade = open_trades.get(ticket, {})
            risk = trade.get('risk_dollar', 0)
            if risk <= 0: continue
            if profit < -risk * 0.8: close_sym(sym); continue
            if ticket not in be_done and profit >= risk * 2.0:
                if abs(sl - entry) > 0.00001:
                    r = modify(ticket, sl=entry)
                    if r and r.get('status') == 'ok': be_done.add(ticket)
            if ticket not in trail_done and profit >= risk * 3.0:
                sl_pips = trade.get('sl_pips', 15)
                tick = 0.01 if 'JPY' in sym else (0.01 if 'XAU' in sym else 0.0001)
                new_sl = round(entry + sl_pips * 1.5 * tick, 5) if typ == 'BUY' else round(entry - sl_pips * 1.5 * tick, 5)
                r = modify(ticket, sl=new_sl)
                if r and r.get('status') == 'ok': trail_done.add(ticket)
        stale = [t for t in open_trades if t not in active]
        if stale:
            for t in stale: del open_trades[t]; be_done.discard(t); trail_done.discard(t)
            OPEN_TRADES.write_text(json.dumps(open_trades, indent=2))
        time.sleep(POLL)
    except KeyboardInterrupt: break
    except Exception as e: time.sleep(POLL)
''')
    print("   ✅ forex_realtime_monitor.py")
    
    # ── 5. BOT PRINCIPAL ──
    (SCRIPTS / 'forex_bot.py').write_text('''#!/usr/bin/env python3
"""FOREX BOT — Multi-Agente v1.0"""
import sys, json, os, numpy as np
from pathlib import Path
from datetime import datetime
import yfinance as yf

sys.path.insert(0, str(Path.home() / '.hermes' / 'scripts'))
from multi_agent import ConfluenciaAgent

RR = 3.0; MIN_SL = 10; MAX_SL = 30; RISK_PCT = 0.5
PAIRS = {
    'EURUSD': ('EURUSD=X', 0.0001), 'GBPUSD': ('GBPUSD=X', 0.0001),
    'USDJPY': ('USDJPY=X', 0.01), 'XAUUSD': ('GC=F', 0.01, True),
}

def get_bias(highs, lows, closes):
    if len(highs) < 3: return 'NEUTRAL'
    ph, pl = highs[-3], lows[-3]; ch, cl, cc = highs[-2], lows[-2], closes[-2]
    if ch > ph and cc < ph: return 'SELL'
    if cl < pl and cc > pl: return 'BUY'
    if ch > ph and cc > ph: return 'BUY'
    if cl < pl and cc < pl: return 'SELL'
    return 'NEUTRAL'

agent = ConfluenciaAgent()

print(f"Forex Bot Multi-Agente — {datetime.now().strftime('%H:%M')}")

for name, cfg in PAIRS.items():
    sym, pip = cfg[0], cfg[1]
    is_metal = len(cfg) > 2
    
    try:
        # Daily bias
        df_d = yf.Ticker(sym).history(period='30d', interval='1d')
        cm = {c.lower(): c for c in df_d.columns}
        dh = df_d[cm.get('high','High')].values
        dl = df_d[cm.get('low','Low')].values
        dc = df_d[cm.get('close','Close')].values
        bias = get_bias(dh, dl, dc)
        if bias == 'NEUTRAL': continue
        
        # M1 data
        df_m1 = yf.Ticker(sym).history(period='5d', interval='1m')
        if df_m1 is None or len(df_m1) < 100: continue
        h = df_m1['High'].values; l = df_m1['Low'].values
        c = df_m1['Close'].values
        
        # Multi-Agent analysis
        decision, conf, signal = agent.analyze(name, h, l, c, bias, pip, is_metal)
        
        if decision != 'NEUTRAL' and signal:
            slp = max(MIN_SL, min(abs(signal['entry'] - l[-1]) / pip * 2, MAX_SL if not is_metal else 300))
            print(f"  {name}: {decision} @{signal['entry']:.5f} SL={slp:.0f}p Conf={conf:.0f}%")
    
    except Exception as e:
        pass

print("FIM")
''')
    print("   ✅ forex_bot.py")
    
    # ── BOOTSTRAP ──
    (HOME / 'forex-agent-setup.sh').write_text('''#!/bin/bash
# FOREX MULTI-AGENT SETUP — 1 comando
set -e
echo "═══════════════════════════════════════"
echo "  FOREX MULTI-AGENT SETUP"
echo "═══════════════════════════════════════"
sudo apt update -qq
sudo apt install -y -qq python3 python3-pip curl git 2>/dev/null
pip3 install --break-system-packages -q yfinance pandas numpy 2>/dev/null

HERMES="$HOME/.hermes"
mkdir -p "$HERMES"/{scripts,forex,skills,brain}

# Baixar scripts do repositório
echo "Baixando sistema multi-agente..."
wget -q -O "$HERMES/scripts/multi_agent.py" https://raw.githubusercontent.com/robertosantosuna-web/hermes-agent/master/scripts/multi_agent.py 2>/dev/null || true
wget -q -O "$HERMES/scripts/fvg_quality.py" https://raw.githubusercontent.com/robertosantosuna-web/hermes-agent/master/scripts/fvg_quality.py 2>/dev/null || true
wget -q -O "$HERMES/scripts/self_learning.py" https://raw.githubusercontent.com/robertosantosuna-web/hermes-agent/master/scripts/self_learning.py 2>/dev/null || true
wget -q -O "$HERMES/scripts/forex_bot.py" https://raw.githubusercontent.com/robertosantosuna-web/hermes-agent/master/scripts/forex_bot.py 2>/dev/null || true

echo "✅ Sistema instalado em ~/.hermes/"
echo "▶️  Para iniciar: cd ~/.hermes/scripts && python3 forex_bot.py"
''')
    os.chmod(HOME / 'forex-agent-setup.sh', 0o755)
    print("   ✅ ~/forex-agent-setup.sh")
    
    print("\n" + "=" * 60)
    print("  SISTEMA CRIADO COM SUCESSO!")
    print("=" * 60)
    print(f"""
  Estrutura:
    ~/.hermes/scripts/
      multi_agent.py          ← 5 agentes especializados
      fvg_quality.py          ← Scoring de qualidade FVG
      self_learning.py        ← Aprendizado contínuo
      forex_bot.py            ← Bot principal
      forex_realtime_monitor.py ← Gestão 2R/3R

  Para iniciar:
    cd ~/.hermes/scripts
    python3 forex_bot.py

  Setup em outro PC:
    bash ~/forex-agent-setup.sh
""")

if __name__ == '__main__':
    create_all()
