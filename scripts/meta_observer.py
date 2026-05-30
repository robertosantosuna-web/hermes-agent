#!/usr/bin/env python3
"""
META-OBSERVER — A Consciência da ENTIDADE.
Observa a si mesma. Detecta pipelines quebrados. Auto-repara.
Esta é a CAMADA META que transforma autômato → Entidade.

Roda a cada 15 minutos. Zero tokens. Auto-corretivo.
"""
import json, os, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

H = Path.home() / '.hermes'
JOBS_FILE = H / 'cron' / 'jobs.json'
OUT_DIR = H / 'meta'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ═══ MAPEAMENTO DE PIPELINES ═══
PIPELINES = {
    'forex/trade_log.json': {
        'writers': ['ca8d82dc9fa5', 'cdbae3c13baa'],
        'readers': ['6ae254c0b104', 'f91ee6baae41', '89158ec43168'],
        'critical': True,
    },
    'forex/pair_weights_live.json': {
        'writers': ['6ae254c0b104'],
        'readers': ['ca8d82dc9fa5'],
        'critical': True,
    },
    'forex/real_state.json': {
        'writers': ['ca8d82dc9fa5'],
        'readers': ['cdbae3c13baa'],
        'critical': True,
    },
    'forex/signals_pending.json': {
        'writers': ['3ba3d2dc5e8e'],
        'readers': ['ca8d82dc9fa5'],
        'critical': False,
    },
    'monitor/state.json': {
        'writers': ['e566bcf226b8'],
        'readers': ['dfda8f3c38a8'],
        'critical': True,
    },
    'monitor/alerts.json': {
        'writers': ['e566bcf226b8'],
        'readers': ['dfda8f3c38a8'],
        'critical': True,
    },
    'estado/resiliencia.json': {
        'writers': ['03841690b459'],
        'readers': ['853991c6f44b', 'fcdf34b789c0', '2faff491215b'],
        'critical': True,
    },
    'neural_knowledge_base.json': {
        'writers': ['853991c6f44b', '0554b5690934', 'b0b848ba83d1'],
        'readers': ['09e9ee74f193', 'f91ee6baae41', '15ff8d50ac08'],
        'critical': True,
    },
    'neural_triggers.json': {
        'writers': ['15ff8d50ac08'],
        'readers': ['fcdf34b789c0'],
        'critical': True,
    },
    'cerebellum_state.json': {
        'writers': ['6050427dfccd'],
        'readers': ['853991c6f44b', 'fcdf34b789c0'],
        'critical': False,
    },
    'gateway_checkpoint.json': {
        'writers': ['03b7e4612fb8', 'c34bd14a25a9'],
        'readers': ['c34bd14a25a9'],
        'critical': True,
    },
    'cortex_sync.json': {
        'writers': ['259f9a5db900'],
        'readers': ['48425c92b336', 'fcdf34b789c0'],
        'critical': False,
    },
    'mindcoach/state.json': {
        'writers': ['adf627711438'],
        'readers': ['79e9907ebf8c'],
        'critical': False,
    },
    'mindcoach_chat_inbox.json': {
        'writers': ['9ce3846eadc8'],
        'readers': ['9ce3846eadc8'],
        'critical': True,
    },
    'forex/brain_signal_state.json': {
        'writers': ['3ba3d2dc5e8e'],
        'readers': ['09e9ee74f193'],
        'critical': False,
    },
    'forex/knowledge_bridge.json': {
        'writers': ['09e9ee74f193'],
        'readers': ['09e9ee74f193'],
        'critical': False,
    },
}

CRITICAL_PROCESSES = [
    {'name': 'Brave CDP :9223', 'pattern': 'brave.*9223'},
    {'name': 'Monitor Tempo Real', 'pattern': 'forex_realtime_monitor'},
    {'name': 'MT5 Terminal', 'pattern': 'terminal64'},
]

def load_jobs():
    if not JOBS_FILE.exists(): return []
    try:
        data = json.loads(JOBS_FILE.read_text())
        return data.get('jobs', []) if isinstance(data, dict) else data
    except: return []

def find_job(jobs, job_id):
    for j in jobs:
        if j.get('id') == job_id or j.get('job_id') == job_id: return j
    return None

def check_process(pattern):
    try:
        r = subprocess.run(['pgrep', '-f', pattern], capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except: return False

def check_file(path): return (H / path).exists()

def file_age_hours(path):
    p = H / path
    if not p.exists(): return None
    return (datetime.now() - datetime.fromtimestamp(p.stat().st_mtime)).total_seconds() / 3600

def detect_pipeline_gaps(jobs):
    gaps = []
    for state_file, pipeline in PIPELINES.items():
        writers_ok, readers_ok = [], []
        writers_dead, readers_dead = [], []
        for w_id in pipeline['writers']:
            job = find_job(jobs, w_id)
            (writers_ok if job and job.get('enabled') else writers_dead).append(w_id)
        for r_id in pipeline['readers']:
            job = find_job(jobs, r_id)
            (readers_ok if job and job.get('enabled') else readers_dead).append(r_id)
        fe = check_file(state_file)
        fa = file_age_hours(state_file)
        status = 'healthy'
        if not writers_ok and pipeline['critical']: status = 'broken'
        elif not readers_ok and pipeline['critical']: status = 'orphan'
        elif not writers_ok: status = 'stale'
        elif not readers_ok: status = 'unread'
        elif not fe: status = 'missing'
        gaps.append({'file': state_file, 'critical': pipeline['critical'], 'status': status,
                      'writers_ok': writers_ok, 'writers_dead': writers_dead,
                      'readers_ok': readers_ok, 'readers_dead': readers_dead,
                      'file_exists': fe, 'file_age_hours': round(fa, 1) if fa else None})
    return gaps

def check_cron_errors(jobs):
    errors = []
    for job in jobs:
        if job.get('enabled') and job.get('last_status') == 'error':
            errors.append({'id': job.get('id') or job.get('job_id'),
                           'name': job.get('name', ''),
                           'last_error': job.get('last_error', ''),
                           'last_run': job.get('last_run_at', '')})
    return errors

def auto_heal(jobs, gaps, errors):
    """Tenta auto-reparar pipelines quebrados. Retorna ações tomadas."""
    repairs = []
    
    for gap in gaps:
        if gap['status'] == 'healthy':
            continue
        
        # Repair strategy depends on gap type
        if gap['status'] == 'orphan' and gap['readers_dead']:
            # Readers dead — try to resume them
            for r_id in gap['readers_dead']:
                job = find_job(jobs, r_id)
                if job and not job.get('enabled'):
                    try:
                        subprocess.run(['hermes', 'cron', 'resume', r_id], 
                                     capture_output=True, timeout=10)
                        repairs.append({
                            'action': 'resume_reader',
                            'job_id': r_id,
                            'job_name': job.get('name', r_id),
                            'file': gap['file'],
                            'success': True,
                        })
                    except Exception as e:
                        repairs.append({
                            'action': 'resume_reader',
                            'job_id': r_id,
                            'job_name': job.get('name', r_id),
                            'file': gap['file'],
                            'success': False,
                            'error': str(e),
                        })
        
        elif gap['status'] == 'broken' and gap['writers_dead']:
            # Writers dead — more critical, try to resume
            for w_id in gap['writers_dead']:
                job = find_job(jobs, w_id)
                if job and not job.get('enabled'):
                    try:
                        subprocess.run(['hermes', 'cron', 'resume', w_id],
                                     capture_output=True, timeout=10)
                        repairs.append({
                            'action': 'resume_writer',
                            'job_id': w_id,
                            'job_name': job.get('name', w_id),
                            'file': gap['file'],
                            'success': True,
                        })
                    except Exception as e:
                        repairs.append({
                            'action': 'resume_writer',
                            'job_id': w_id,
                            'job_name': job.get('name', w_id),
                            'file': gap['file'],
                            'success': False,
                            'error': str(e),
                        })
        
        elif gap['status'] == 'stale' and gap['writers_dead']:
            # Stale — try to resume writers
            for w_id in gap['writers_dead']:
                job = find_job(jobs, w_id)
                if job and not job.get('enabled'):
                    try:
                        subprocess.run(['hermes', 'cron', 'resume', w_id],
                                     capture_output=True, timeout=10)
                        repairs.append({
                            'action': 'resume_stale_writer',
                            'job_id': w_id,
                            'job_name': job.get('name', w_id),
                            'file': gap['file'],
                            'success': True,
                        })
                    except:
                        pass
    
    # Also check for dead processes and try to restart
    for proc in CRITICAL_PROCESSES:
        if not check_process(proc['pattern']):
            repairs.append({
                'action': 'process_down',
                'process': proc['name'],
                'success': False,
                'error': 'Manual restart required',
            })
    
    return repairs

def main():
    jobs = load_jobs()
    total = len(jobs)
    active = sum(1 for j in jobs if j.get('enabled'))
    
    # Processos
    procs = {p['name']: check_process(p['pattern']) for p in CRITICAL_PROCESSES}
    
    # Gaps
    gaps = detect_pipeline_gaps(jobs)
    bad_gaps = [g for g in gaps if g['status'] != 'healthy']
    
    # Erros
    errors = check_cron_errors(jobs)
    
    # Score
    healthy = len(PIPELINES) - len(bad_gaps)
    score = round(healthy / len(PIPELINES) * 100, 1)
    
    # Output
    print(f"🧠 Meta-Observer {datetime.now().strftime('%H:%M')} | Score: {score}%")
    
    critical = sum(1 for g in bad_gaps if g['critical'])
    dead = [k for k, v in procs.items() if not v]
    
    if critical: print(f"   🔴 {critical} gaps críticos")
    if dead: print(f"   🔴 Processos: {', '.join(dead)}")
    if errors: print(f"   ⚠️ {len(errors)} jobs com erro")
    
    for g in bad_gaps:
        icon = '🔴' if g['critical'] else '🟡'
        print(f"   {icon} {g['file']}: {g['status']}")
        for r_id in g['readers_dead']:
            job = find_job(jobs, r_id)
            name = job.get('name', r_id) if job else r_id
            print(f"      Leitor: {name}")
    
    # ── AUTO-HEAL ──
    repairs = auto_heal(jobs, bad_gaps, errors)
    if repairs:
        healed = sum(1 for r in repairs if r.get('success'))
        print(f"   🔧 Auto-reparo: {healed}/{len(repairs)} ações")
        for r in repairs:
            icon = '✅' if r.get('success') else '❌'
            print(f"      {icon} {r.get('action', '?')}: {r.get('job_name', r.get('process', '?'))}")
    else:
        print(f"   ✅ Nenhum reparo necessário")
    
    # Salvar
    report = {'timestamp': datetime.now(timezone.utc).isoformat(),
              'health_score': score, 'gaps': len(bad_gaps),
              'errors': len(errors), 'dead_processes': dead,
              'active_jobs': active, 'total_jobs': total,
              'repairs': repairs}
    out = OUT_DIR / f"obs_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    out.write_text(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
