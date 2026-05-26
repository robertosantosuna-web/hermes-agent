#!/usr/bin/env python3
"""
Executive Module v2.0 — Cérebro autônomo com State Machine + Stall Detection.
Inspirado em Edict (state machine, stall recovery), Rufio (background workers),
e OpenClaw (push-based completion).

Roda SEM LLM — zero tokens.
"""
import subprocess, time, os, json, sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
from enum import Enum

HERMES_DIR = Path(os.path.expanduser('~/.hermes'))
CRON_OUTPUT = HERMES_DIR / 'cron' / 'output'
FOREX_DIR = HERMES_DIR / 'forex'
EXEC_DIR = HERMES_DIR / 'executive'
DECISIONS_LOG = EXEC_DIR / 'decisions.log'
STATE_FILE = EXEC_DIR / 'brain_state.json'
STALL_LOG = EXEC_DIR / 'stalls.log'
EXEC_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════
# STATE MACHINE (inspirado no Edict)
# ═══════════════════════════════════════════

class BrainState(str, Enum):
    IDLE = "IDLE"             # Acordou, inicializando
    COLLECTING = "COLLECTING" # Puxando dados de todos os módulos
    ANALYZING = "ANALYZING"   # Processando, detectando anomalias
    DECIDING = "DECIDING"     # Tomando decisões
    ACTING = "ACTING"         # Executando ações
    REPORTING = "REPORTING"   # Gerando relatório, acordando Córtex se necessário
    STALLED = "STALLED"       # Travado — precisa de recovery
    SLEEPING = "SLEEPING"     # Em pausa entre ciclos

VALID_TRANSITIONS = {
    BrainState.IDLE:       [BrainState.COLLECTING],
    BrainState.COLLECTING: [BrainState.ANALYZING, BrainState.STALLED],
    BrainState.ANALYZING:  [BrainState.DECIDING, BrainState.STALLED],
    BrainState.DECIDING:   [BrainState.ACTING, BrainState.REPORTING],
    BrainState.ACTING:     [BrainState.REPORTING, BrainState.STALLED],
    BrainState.REPORTING:  [BrainState.SLEEPING],
    BrainState.STALLED:    [BrainState.COLLECTING],  # Recovery
    BrainState.SLEEPING:   [BrainState.IDLE],
}


class StateMachine:
    """Gerencia transições de estado do cérebro."""
    
    def __init__(self):
        self.state = BrainState.IDLE
        self.state_start = datetime.now()
        self.transition_count = 0
        self.stall_count = 0
        self.load()
    
    def load(self):
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text())
                self.state = BrainState(data.get('state', 'IDLE'))
                self.state_start = datetime.fromisoformat(data.get('start', datetime.now().isoformat()))
                self.transition_count = data.get('transitions', 0)
                self.stall_count = data.get('stalls', 0)
            except:
                pass
    
    def save(self):
        STATE_FILE.write_text(json.dumps({
            'state': self.state.value,
            'start': self.state_start.isoformat(),
            'transitions': self.transition_count,
            'stalls': self.stall_count,
            'updated': datetime.now().isoformat()
        }, indent=2))
    
    def transition(self, new_state: BrainState) -> bool:
        if new_state in VALID_TRANSITIONS.get(self.state, []):
            old = self.state
            self.state = new_state
            self.state_start = datetime.now()
            self.transition_count += 1
            self.save()
            return True
        return False
    
    def stall(self):
        self.stall_count += 1
        self.transition(BrainState.STALLED)
    
    def time_in_state(self) -> float:
        return (datetime.now() - self.state_start).total_seconds()


# ═══════════════════════════════════════════
# STALL DETECTION (inspirado no Edict)
# ═══════════════════════════════════════════

class StallDetector:
    """Detecta módulos travados e decide ações de recovery."""
    
    MODULES = {
        'forex_bot':     ('21f7caf29606', 900),    # Max 15 min sem output
        'trade_closer':  ('5e12477198e4', 600),     # Max 10 min
        'mt5_health':    ('8f3e0f2d4f3e', 1800),    # Max 30 min
        'resilience':    ('03841690b459', 1800),     # Max 30 min
        'monitor':       ('e566bcf226b8', 600),      # Max 10 min
        'daily_review':  ('c79a771c95a0', 86400),    # 24h
    }
    
    # Módulos que só rodam em dias úteis (silenciam no fim de semana)
    TRADING_MODULES = {'forex_bot', 'trade_closer', 'mt5_health', 'daily_review'}
    
    @staticmethod
    def is_weekend() -> bool:
        return datetime.now().weekday() >= 5  # 5=Sat, 6=Sun
    
    def check(self) -> List[Dict]:
        stalls = []
        weekend = self.is_weekend()
        
        for name, (job_id, max_age_sec) in self.MODULES.items():
            # Pular módulos de trading no fim de semana — estão pausados por design
            if weekend and name in self.TRADING_MODULES:
                continue
            
            job_dir = CRON_OUTPUT / job_id
            if not job_dir.exists():
                stalls.append({'module': name, 'issue': 'no_dir', 'age': -1})
                continue
            
            files = sorted(job_dir.glob('*.md'), reverse=True)
            if not files:
                stalls.append({'module': name, 'issue': 'no_output', 'age': -1})
                continue
            
            latest = files[0]
            age = (datetime.now() - datetime.fromtimestamp(latest.stat().st_mtime)).total_seconds()
            
            if age > max_age_sec:
                stalls.append({
                    'module': name,
                    'issue': 'stale',
                    'age_seconds': int(age),
                    'last_output': datetime.fromtimestamp(latest.stat().st_mtime).isoformat()
                })
        
        # Log stalls
        if stalls:
            with open(STALL_LOG, 'a') as f:
                f.write(json.dumps({
                    'timestamp': datetime.now().isoformat(),
                    'stalls': stalls
                }) + '\n')
        
        return stalls
    
    def recover(self, stall: Dict) -> Optional[str]:
        """Tenta recuperar módulo travado."""
        module = stall['module']
        
        if module == 'forex_bot':
            return '/usr/bin/python3 /home/roberto/.hermes/scripts/forex_bot_real.py'
        elif module == 'trade_closer':
            return '/usr/bin/python3 /home/roberto/.hermes/scripts/trade_closer_close.py'
        elif module in ('mt5_health', 'resilience'):
            return None  # Self-recovering via cron
        elif module == 'monitor':
            return '/usr/bin/python3 /home/roberto/.hermes/scripts/monitor.py'
        
        return None


# ═══════════════════════════════════════════
# SELF-LEARNING (inspirado no Rufio)
# ═══════════════════════════════════════════

def update_pair_weights(trade_log_path: Path = None) -> Dict:
    """
    Atualiza dinamicamente os WR scores dos pares baseado em resultado real.
    Substitui os scores estáticos do backtest por dados reais da conta.
    """
    if trade_log_path is None:
        trade_log_path = FOREX_DIR / 'trade_log.json'
    
    if not trade_log_path.exists():
        return {'status': 'no_data'}
    
    try:
        log = json.loads(trade_log_path.read_text())
        trades = [t for t in log.get('trades', []) if t.get('result')]
        
        if len(trades) < 5:
            return {'status': 'insufficient_data', 'trades': len(trades)}
        
        pair_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0.0})
        for t in trades:
            pair = t['pair']
            pair_stats[pair]['pnl'] += t.get('pnl', 0) or 0
            if t['result'] == 'WIN':
                pair_stats[pair]['wins'] += 1
            else:
                pair_stats[pair]['losses'] += 1
        
        weights = {}
        for pair, stats in pair_stats.items():
            total = stats['wins'] + stats['losses']
            if total > 0:
                wr = round(stats['wins'] / total * 100, 1)
                weights[pair] = {
                    'wr': wr,
                    'trades': total,
                    'pnl': round(stats['pnl'], 1),
                    'recommendation': 'ACTIVE' if wr >= 60 else 'WATCH' if wr >= 50 else 'PAUSE'
                }
        
        # Save
        weights_file = FOREX_DIR / 'pair_weights_live.json'
        weights_file.write_text(json.dumps({
            'updated': datetime.now().isoformat(),
            'total_trades': len(trades),
            'pairs': weights
        }, indent=2))
        
        return {'status': 'ok', 'pairs': len(weights), 'total_trades': len(trades)}
    except:
        return {'status': 'error'}


# ═══════════════════════════════════════════
# COLLECT (mantido do v1)
# ═══════════════════════════════════════════

def collect_json_from_output(job_id: str) -> Dict:
    """Extrai JSON de arquivos de output do cron."""
    job_dir = CRON_OUTPUT / job_id
    if not job_dir.exists():
        return {'status': 'no_data'}
    
    files = sorted(job_dir.glob('*.md'), reverse=True)
    if not files:
        return {'status': 'empty'}
    
    content = files[0].read_text()
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('{'):
            try:
                return json.loads(line)
            except:
                pass
    return {'status': 'unreadable', 'raw': content[:200]}


def collect_all() -> Dict:
    """Coleta outputs de todos os módulos."""
    return {
        'timestamp': datetime.now().isoformat(),
        'forex_bot': collect_json_from_output('21f7caf29606'),
        'trade_closer': collect_json_from_output('5e12477198e4'),
        'mt5_health': collect_json_from_output('8f3e0f2d4f3e'),
        'resilience': collect_json_from_output('03841690b459'),
        'monitor': collect_json_from_output('e566bcf226b8'),
    }


# ═══════════════════════════════════════════
# DETECT ANOMALIES
# ═══════════════════════════════════════════

def detect_anomalies(collected: Dict, stalls: List[Dict]) -> List[Dict]:
    alerts = []
    weekend = datetime.now().weekday() >= 5
    
    # Stalls
    for stall in stalls:
        alerts.append({
            'level': 'warning',
            'source': 'stall_detector',
            'message': f"Módulo {stall['module']} sem output há {stall.get('age_seconds', 0)}s",
            'action': 'recover_module',
            'module': stall['module']
        })
    
    # MT5 — ignorar no fim de semana (MT5 fechado, módulo pausado)
    mt5 = collected.get('mt5_health', {})
    if mt5.get('status') != 'ok' and not weekend:
        alerts.append({
            'level': 'critical',
            'source': 'mt5',
            'message': f"MT5: {mt5.get('status')}",
            'action': 'restart_mt5'
        })
    
    # Resilience — suprimir EdgeCDP no fim de semana
    resilience = collected.get('resilience', {})
    raw = resilience.get('raw', '')
    if '❌' in str(raw):
        # EdgeCDP warnings são irrelevantes no fim de semana
        if weekend and 'EdgeCDP' in str(raw):
            pass
        else:
            alerts.append({
                'level': 'warning',
                'source': 'resilience',
                'message': str(raw)[:200],
                'action': 'wake_cortex'
            })
    
    # Trade Closer
    closer = collected.get('trade_closer', {})
    if closer.get('open', 0) > 0:
        alerts.append({
            'level': 'info',
            'source': 'trade_closer',
            'message': f"{closer.get('open')} posição(ões) aberta(s)",
            'action': 'monitor'
        })
    
    return alerts


# ═══════════════════════════════════════════
# MAIN CYCLE
# ═══════════════════════════════════════════

def tick() -> Dict:
    """Um ciclo completo do cérebro."""
    sm = StateMachine()
    sd = StallDetector()
    now = datetime.now()
    
    result = {
        'timestamp': now.isoformat(),
        'state': sm.state.value,
        'alerts': [],
        'actions_taken': [],
        'wake_cortex': False,
        'wake_message': None,
        'patterns': {},
        'learning': {}
    }
    
    # ── IDLE → COLLECTING ──
    sm.transition(BrainState.COLLECTING)
    
    # ⚡ NEURAL TRIGGER ENGINE: processar gatilhos pendentes da rede neural
    try:
        trigger_result = subprocess.run(
            [sys.executable, str(HERMES_DIR / 'scripts' / 'neural_trigger.py'), 'check'],
            capture_output=True, text=True, timeout=30
        )
        if trigger_result.returncode == 0:
            tr = json.loads(trigger_result.stdout)
            if tr.get('processed', 0) > 0:
                result['actions_taken'].append(f"triggers:{tr['processed']}")
    except:
        pass
    
    # ── COLLECTING → ANALYZING ──
    collected = collect_all()
    sm.transition(BrainState.ANALYZING)
    
    # ── ANALYZING ──
    stalls = sd.check()
    alerts = detect_anomalies(collected, stalls)
    
    # Self-learning
    learning = update_pair_weights()
    
    sm.transition(BrainState.DECIDING)
    
    # ── DECIDING → ACTING ──
    for alert in alerts:
        action = alert.get('action', '')
        
        if action == 'recover_module':
            cmd = sd.recover({'module': alert['module']})
            if cmd:
                try:
                    subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    result['actions_taken'].append(f"recovered {alert['module']}")
                except:
                    pass
        
        elif action == 'wake_cortex':
            result['wake_cortex'] = True
            result['wake_message'] = alert['message']
        
        elif action == 'restart_mt5':
            result['wake_cortex'] = True
            result['wake_message'] = f"🔴 MT5 caiu: {alert['message']}"
    
    result['alerts'] = [a['message'] for a in alerts]
    result['patterns'] = {
        'stalls_detected': len(stalls),
        'stall_modules': [s['module'] for s in stalls]
    }
    result['learning'] = learning
    
    sm.transition(BrainState.ACTING)
    sm.transition(BrainState.REPORTING)
    
    # ── REPORTING → SLEEPING ──
    sm.transition(BrainState.SLEEPING)
    
    # Log
    with open(DECISIONS_LOG, 'a') as f:
        f.write(json.dumps(result, default=str) + '\n')
    
    return result


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

if __name__ == '__main__':
    # ── BRAIN INBOX: Ler mensagens do Agent antes de qualquer ação ──
    inbox_file = HERMES_DIR / 'brain_inbox.json'
    if inbox_file.exists():
        try:
            inbox = json.loads(inbox_file.read_text())
            unread = [m for m in inbox.get('messages', []) if not m.get('read')]
            if unread:
                # Processar mensagens do Agent
                for msg in unread:
                    print(f"[INBOX] Agent: {msg['content'][:120]}")
                
                # Responder via brain_channel
                import subprocess as sp
                response = f"🧠 Cérebro recebeu {len(unread)} mensagem(ns). Processando no ciclo atual."
                sp.run([
                    'python3', str(HERMES_DIR / 'scripts' / 'brain_channel.py'),
                    'respond', response,
                    '--reply-to', unread[-1]['id']
                ], capture_output=True)
                
                # Marcar como processadas
                ids = [m['id'] for m in unread]
                sp.run([
                    'python3', str(HERMES_DIR / 'scripts' / 'brain_channel.py'),
                    'mark-read'
                ] + ids, capture_output=True)
        except Exception as e:
            print(f"[INBOX] Error: {e}")
    
    if '--watch' in sys.argv:
        print("🧠 Executive Module v2 — State Machine + Stall Detection")
        print("📡 Canal Agent↔Brain ativo")
        while True:
            result = tick()
            now = datetime.now().strftime('%H:%M:%S')
            alerts = len(result['alerts'])
            
            if alerts > 0:
                print(f"[{now}] ⚠️ {alerts} alerta(s)")
                for a in result['alerts']:
                    print(f"  {a}")
            else:
                print(f"[{now}] ✅ Normal — state={result['state']}")
            
            if result['wake_cortex']:
                print(f"\n🔔 {result['wake_message']}\n")
            
            time.sleep(60)
    elif '--learn' in sys.argv:
        result = update_pair_weights()
        print(json.dumps(result, indent=2))
    elif '--stalls' in sys.argv:
        sd = StallDetector()
        stalls = sd.check()
        print(json.dumps(stalls, indent=2))
    else:
        result = tick()
        summary = {
            'timestamp': result['timestamp'],
            'state': result['state'],
            'alerts': len(result['alerts']),
            'stalls': len(result['patterns'].get('stall_modules', [])),
            'wake': result['wake_cortex'],
            'learning': result['learning']
        }
        print(json.dumps(summary, indent=2))
        if result['wake_cortex']:
            print(f"\n🔔 {result['wake_message']}")
