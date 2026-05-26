#!/usr/bin/env python3
"""
Brain Research Cycle — Motor de Auto-Desenvolvimento (no_agent, zero tokens).
Script central que coordena os ciclos de pesquisa e evolução do cérebro.

Ciclos:
  Micro: a cada falha detectada → Amygdala ativada
  Diário: 06:00 BRT → escaneia gaps, verifica componentes
  Semanal: Domingo 10:00 BRT → Hippocampus consolida
  Mensal: 1º dia do mês → propostas estruturais

Este script é a "mente por trás" — analisa o estado de todos os componentes,
detecta gaps, e registra propostas de evolução no log.
"""
import json, os, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

HERMES = Path(os.path.expanduser('~/.hermes'))
RESEARCH_OUT = HERMES / 'cron' / 'output' / 'brain_research'
BRAIN_LOG = HERMES / 'brain_evolution_log.json'
SELF_EVO = HERMES / 'self_evolution_log.json'
SUGGESTIONS = HERMES / 'brain_suggestions.json'

def load_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except:
        return None

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

def check_component_health():
    """Check status of all brain components."""
    components = {}
    
    # Thalamus
    thalamus_log = HERMES / 'thalamus' / 'event_log.json'
    components['thalamus'] = {
        'exists': thalamus_log.exists(),
        'events': len(load_json(thalamus_log) or []),
        'status': 'operational' if thalamus_log.exists() else 'missing',
    }
    
    # Cortices
    for cortex in ['visual', 'audio', 'motor']:
        path = HERMES / 'cortex' / f'{cortex}.py'
        components[f'cortex_{cortex}'] = {
            'exists': path.exists(),
            'status': 'operational' if path.exists() else 'missing',
        }
    
    # Executive
    executive = HERMES / 'executive' / 'brain.py'
    components['executive'] = {
        'exists': executive.exists(),
        'status': 'operational' if executive.exists() else 'missing',
    }
    
    # Brain sub-components (scripts)
    for comp in ['amygdala', 'n_accumbens', 'hippocampus', 'cerebellum']:
        path = HERMES / 'scripts' / f'{comp}.py'
        components[comp] = {
            'exists': path.exists(),
            'status': 'operational' if path.exists() else 'missing',
        }
    
    return components

def detect_gaps(components):
    """Identify missing or broken components."""
    gaps = []
    
    missing = [k for k, v in components.items() if not v['exists']]
    if missing:
        gaps.append({'type': 'missing_components', 'items': missing})
    
    # Check if thalamus has recent events
    thalamus = components.get('thalamus', {})
    if thalamus.get('events', 0) == 0:
        gaps.append({'type': 'inactive_thalamus', 'message': 'Thalamus sem eventos registrados'})
    
    return gaps

def scan_cron_errors():
    """Scan cron output for recent errors."""
    import subprocess
    try:
        result = subprocess.run(
            ['hermes', 'cron', 'list'],
            capture_output=True, text=True, timeout=10
        )
        # Parse errors from output
        errors = []
        for line in result.stdout.split('\n'):
            if 'error' in line.lower() or 'failed' in line.lower():
                errors.append(line.strip()[:200])
        return errors[:5]
    except:
        return []

def propose_evolution(gaps, errors):
    """Generate evolution proposals based on gaps."""
    proposals = []
    
    for gap in gaps:
        if gap['type'] == 'missing_components':
            proposals.append({
                'priority': 'high',
                'component': gap['items'],
                'action': 'create_missing_components',
                'rationale': 'Brain components missing — autonomy incomplete',
            })
        elif gap['type'] == 'inactive_thalamus':
            proposals.append({
                'priority': 'medium',
                'component': 'thalamus',
                'action': 'wire_sensors_to_thalamus',
                'rationale': 'Thalamus exists but no sensors are feeding it events',
            })
    
    if errors:
        proposals.append({
            'priority': 'high',
            'component': 'cron_jobs',
            'action': 'fix_cron_errors',
            'rationale': f'{len(errors)} cron jobs with errors',
        })
    
    return proposals

def log_evolution_event(phase, title, description, components, gaps, proposals):
    """Append to brain evolution log."""
    log = load_json(BRAIN_LOG) or {'evolution_events': []}
    
    event = {
        'event_id': f"ev-{len(log['evolution_events']) + 1:03d}",
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'phase': phase,
        'title': title,
        'description': description,
        'components_summary': {
            'total': len(components),
            'operational': sum(1 for v in components.values() if v['status'] == 'operational'),
            'missing': sum(1 for v in components.values() if v['status'] == 'missing'),
        },
        'gaps': gaps,
        'proposals': proposals,
    }
    
    log['evolution_events'].append(event)
    
    # Keep last 500 events
    if len(log['evolution_events']) > 500:
        log['evolution_events'] = log['evolution_events'][-500:]
    
    save_json(BRAIN_LOG, log)
    return event

def main():
    now = datetime.now(timezone.utc)
    is_weekly = now.weekday() == 6  # Sunday
    is_monthly = now.day == 1
    
    phase = 'monthly' if is_monthly else 'weekly' if is_weekly else 'daily'
    
    # 1. Check components
    components = check_component_health()
    
    # 2. Detect gaps
    gaps = detect_gaps(components)
    
    # 3. Scan errors
    errors = scan_cron_errors()
    
    # 4. Generate proposals
    proposals = propose_evolution(gaps, errors)
    
    # 5. Log event
    title = {
        'daily': 'Ciclo Diário de Auto-Desenvolvimento',
        'weekly': 'Ciclo Semanal de Auto-Desenvolvimento',
        'monthly': 'Ciclo Mensal de Auto-Desenvolvimento — Propostas Estruturais',
    }[phase]
    
    event = log_evolution_event(phase, title, 
        f"Ciclo {phase} de auto-desenvolvimento: {len(components)} componentes, "
        f"{len(gaps)} gaps, {len(proposals)} propostas",
        components, gaps, proposals)
    
    # 6. Update suggestions for Roberto (monthly only)
    if is_monthly and proposals:
        suggestions = load_json(SUGGESTIONS) or {'suggestions': []}
        for p in proposals:
            if p['priority'] == 'high':
                suggestions['suggestions'].append({
                    'id': f"sug-{len(suggestions['suggestions']) + 1:03d}",
                    'timestamp': now.isoformat(),
                    'component': str(p.get('component', 'unknown')),
                    'suggestion': p.get('rationale', ''),
                    'priority': p['priority'],
                    'status': 'pending_roberto',
                    'action_needed': p.get('action', ''),
                })
        save_json(SUGGESTIONS, suggestions)
    
    # Output
    RESEARCH_OUT.mkdir(parents=True, exist_ok=True)
    out_file = RESEARCH_OUT / f"cycle_{phase}_{now.strftime('%Y%m%d_%H%M%S')}.json"
    out_file.write_text(json.dumps(event, ensure_ascii=False, indent=2))
    
    print(f"🧠 Brain Research: Ciclo {phase}")
    print(f"   Componentes: {event['components_summary']['operational']}/{event['components_summary']['total']} operacionais")
    print(f"   Gaps: {len(gaps)}")
    print(f"   Propostas: {len(proposals)}")
    if proposals:
        for p in proposals:
            print(f"   - [{p['priority']}] {p.get('rationale', '')}")

if __name__ == '__main__':
    main()
