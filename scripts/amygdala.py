#!/usr/bin/env python3
"""
Amygdala — Threat Detector (no_agent, zero tokens).
Scan the Thalamus event log for urgent threats and recent failures.
Only outputs when there's something requiring attention.

Micro cycle: runs every failure.
Daily cycle: runs at 06:00 BRT to scan overnight events.
"""
import json, os, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

HERMES = Path(os.path.expanduser('~/.hermes'))
EVENT_LOG = HERMES / 'thalamus' / 'event_log.json'
FAILURE_LOG = HERMES / 'failure_log.json'
AMYGDALA_OUT = HERMES / 'cron' / 'output' / 'amygdala'

def load_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except:
        return None

def scan_threats():
    now = datetime.now(timezone.utc)
    threats = []
    
    # 1. Scan event log for L3 urgency in last 24h
    events = load_json(EVENT_LOG)
    if events:
        cutoff = (now - timedelta(hours=24)).isoformat()
        for ev in reversed(events if isinstance(events, list) else []):
            if ev.get('timestamp', '') < cutoff:
                continue
            if ev.get('urgency') == 'L3':
                threats.append({
                    'level': 'L3',
                    'source': 'thalamus',
                    'type': ev.get('type'),
                    'summary': ev.get('summary', ''),
                    'timestamp': ev.get('timestamp'),
                })
    
    # 2. Scan failure log for new failures in last 24h
    failures = load_json(FAILURE_LOG)
    if failures:
        cutoff_date = (now - timedelta(hours=24)).strftime('%Y-%m-%d')
        for f in failures.get('failures', []):
            if f.get('date', '') >= cutoff_date:
                if f.get('status') in ('pending', 'requires_human'):
                    threats.append({
                        'level': 'FAILURE',
                        'source': 'failure_log',
                        'category': f.get('category'),
                        'platform': f.get('platform'),
                        'error': f.get('error'),
                        'status': f.get('status'),
                    })
    
    # 3. Check for repeated stalls in brain executive log
    stall_log = HERMES / 'executive' / 'stalls.log'
    if stall_log.exists():
        stall_lines = stall_log.read_text().strip().split('\n')
        recent_stalls = []
        cutoff = now - timedelta(hours=6)
        for line in stall_lines[-50:]:  # last 50
            try:
                entry = json.loads(line)
                ts = datetime.fromisoformat(entry.get('timestamp', ''))
                if ts > cutoff:
                    recent_stalls.extend(entry.get('stalls', []))
            except:
                pass
        if len(recent_stalls) >= 3:
            threats.append({
                'level': 'WARNING',
                'source': 'executive_stalls',
                'message': f'{len(recent_stalls)} stalls in last 6h',
                'modules': list(set(s.get('module', '') for s in recent_stalls)),
            })
    
    return threats

def main():
    threats = scan_threats()
    
    if not threats:
        # Silent — nothing to report
        return
    
    # Output only when threats exist
    AMYGDALA_OUT.mkdir(parents=True, exist_ok=True)
    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'component': 'amygdala',
        'threats_detected': len(threats),
        'threats': threats,
        'action': 'WAKE_CORTEX' if any(t.get('level') == 'L3' for t in threats) else 'LOG_ONLY',
    }
    
    out_file = AMYGDALA_OUT / f"threats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_file.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    
    # ── Neural KB Integration ──
    try:
        from kb_bridge import write as kb_write, query as kb_query
        kb_write('amygdala', {
            'active_threats': threats,
            'threat_level': 'elevated' if len(threats) >= 3 else 'normal',
            'last_scan': datetime.now(timezone.utc).isoformat(),
            'action_required': output['action'],
        })
        # If threats detected, check cerebellum health
        if threats:
            from kb_bridge import synapse
            from kb_bridge import read as kb_read
            cereb = kb_read('cerebellum')
            if cereb and cereb.get('validation_failures'):
                synapse('amygdala', 'cerebellum',
                    f'{len(threats)} threats + {len(cereb["validation_failures"])} validation failures',
                    confidence=0.85, evidence={'threats': len(threats)})
    except ImportError:
        pass
    
    # Print summary for cron delivery
    print(f"🧠 Amygdala: {len(threats)} threat(s) detectados")
    for t in threats:
        print(f"  [{t['level']}] {t.get('summary', t.get('error', t.get('message', '')))}")
    
    # ═══ ANÁLISE PROFUNDA VIA MODELO LOCAL ═══
    if threats:
        try:
            import sys; sys.path.insert(0, str(HERMES / 'scripts'))
            from brain_orchestrator import route_task
            
            threat_text = '\n'.join(
                f"[{t.get('level','?')}] {t.get('summary', t.get('error', t.get('message', '')))}"
                for t in threats[:5]
            )
            
            result = route_task('amygdala',
                f"Avalie estas ameaças e recomende ação:\n{threat_text}",
                context=f"ENTIDADE autônoma. MT5 forex ativo. {len(threats)} ameaças detectadas.",
                timeout=90)
            
            if result['success'] and result['result']:
                # Adicionar análise ao output
                analysis = result['result'][:300]
                output['ai_analysis'] = analysis
                out_file.write_text(json.dumps(output, ensure_ascii=False, indent=2))
                print(f"  🤖 Análise: {analysis[:150]}...")
        except Exception as e:
            pass  # Fallback silencioso — análise determinística já foi feita

if __name__ == '__main__':
    main()
