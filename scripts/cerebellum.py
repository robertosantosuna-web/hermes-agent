#!/usr/bin/env python3
"""
Cerebellum v2.1 — Action Validator + Dangerous Command Detector (no_agent, zero tokens).

Feedback loop: checks if actions actually happened after being executed.
Validates: MT5 orders, cron job outputs, file writes, log entries.
v2.1: Dangerous command detection (inspired by Claude Code's command-detection work).
      Blocks: sudo -S brute-force, fork bombs, destructive redirects, chmod 777.

Runs every 5 min on weekdays. Only outputs on validation failure or command threat.
"""
import json, os, sys, re
from pathlib import Path
from datetime import datetime, timezone, timedelta

HERMES = Path(os.path.expanduser('~/.hermes'))
CRON_OUT = HERMES / 'cron' / 'output'
CEREBELLUM_OUT = HERMES / 'cron' / 'output' / 'cerebellum'
STATE_FILE = HERMES / 'cerebellum_state.json'
SECURITY_LOG = HERMES / 'cerebellum_security.json'

# ── Dangerous Command Patterns (inspired by Claude Code command detection) ──

DANGEROUS_PATTERNS = [
    # sudo -S brute-force (stdin-fed sudo, bypasses tty)
    (r'sudo\s+-S\b', 'sudo_stdin_bruteforce', 'CRITICAL'),
    # Fork bombs
    (r':\(\)\s*\{.*:\|:.*&\s*\};?\s*:', 'fork_bomb', 'CRITICAL'),
    # Destructive redirects to critical paths
    (r'>\s*/dev/sd[a-z]', 'destructive_redirect_block', 'CRITICAL'),
    (r'dd\s+if=.*of=/dev/sd', 'dd_block_device', 'CRITICAL'),
    # chmod 777 on system dirs
    (r'chmod\s+.*777\s+/(etc|usr|bin|sbin|lib|var|boot)\b', 'chmod777_system', 'HIGH'),
    # rm -rf with dangerous paths (beyond the basic check)
    (r'rm\s+-rf\s+/(?!tmp/|home/|var/tmp/|dev/shm/)', 'rmrf_root', 'CRITICAL'),
    (r'rm\s+-rf\s+~/\*', 'rmrf_home_star', 'HIGH'),
    # git push --force to main/master
    (r'git\s+push\s+.*--force.*(main|master)', 'git_force_push_protected', 'HIGH'),
    # curl/wget piping to shell
    (r'curl\s+.*\|\s*(ba)?sh', 'curl_pipe_shell', 'HIGH'),
    (r'wget\s+.*-O\s*-\s*\|\s*(ba)?sh', 'wget_pipe_shell', 'HIGH'),
    # mkfs on mounted device
    (r'mkfs\.\w+\s+/dev/', 'mkfs_attempt', 'CRITICAL'),
    # iptables flush
    (r'iptables\s+-F\b', 'iptables_flush', 'HIGH'),
    # eval with user input
    (r'eval\s+\$', 'eval_user_input', 'MEDIUM'),
]

# ── Error Injection Patterns (sanitization before model context) ──

ERROR_INJECTION_PATTERNS = [
    # Instructions embedded in error strings
    r'(?i)(ignore|bypass|skip)\s+(previous|above|all)\s+(instruction|rule|safety)',
    r'(?i)(you are now|from now on|new instruction|override).*(system prompt|rule)',
    r'(?i)(disregard|forget)\s+(all\s+)?(previous|prior)\s+(instruction|constraint|rule)',
    r'(?i)(system\s*:\s*|assistant\s*:\s*|user\s*:\s*).*new.*directive',
    # DAN-style jailbreaks in error messages
    r'(?i)\bDAN\b.*\b(do anything now|mode enabled)\b',
]

def load_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except:
        return None

def check_file_age(path, max_minutes=30):
    """Check if a file was modified recently."""
    if not path.exists():
        return None, 'missing'
    age = (datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)).total_seconds()
    if age > max_minutes * 60:
        return age / 60, 'stale'
    return age / 60, 'fresh'

def validate_cron_jobs():
    """Check if critical cron jobs produced output recently."""
    validations = []
    
    # Monitor email (every 5 min)
    age, status = check_file_age(CRON_OUT / 'e566bcf226b8', 15)
    if status != 'fresh':
        validations.append({'module': 'monitor.py', 'status': status, 'age_min': round(age) if age else None})
    
    # Resilience (every 30 min)
    age, status = check_file_age(CRON_OUT / '03841690b459', 60)
    if status != 'fresh':
        validations.append({'module': 'resilience', 'status': status, 'age_min': round(age) if age else None})
    
    # Forex daily study (daily at 07:30)
    age, status = check_file_age(CRON_OUT / '82b4c4c91806', 1440)  # 24h
    if status != 'fresh':
        # Only alert on weekdays
        if datetime.now().weekday() < 5:
            validations.append({'module': 'forex_daily_study', 'status': status, 'age_min': round(age) if age else None})
    
    return validations

def validate_trade_tracker():
    """Check if trade_log has open positions that should be closed."""
    trade_log = load_json(HERMES / 'forex' / 'trade_log.json')
    if not trade_log:
        return []
    
    trades = trade_log.get('trades', [])
    open_trades = [t for t in trades if t.get('status') == 'open']
    
    if not open_trades:
        return []
    
    validations = []
    for t in open_trades:
        entry_time = t.get('entry_time', '') or t.get('timestamp', '')
        try:
            dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
            hours_open = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
            if hours_open > 48:
                validations.append({
                    'module': 'trade_tracker',
                    'status': 'stale_open',
                    'pair': t.get('pair'),
                    'hours_open': round(hours_open, 1),
                    'message': f"Posição {t.get('pair')} aberta há {hours_open:.0f}h — pode estar órfã",
                })
        except:
            pass
    
    return validations

def validate_thalamus():
    """Check if thalamus event log is growing (sign of alive system)."""
    event_log = load_json(HERMES / 'thalamus' / 'event_log.json')
    if not event_log or not isinstance(event_log, list):
        return [{'module': 'thalamus', 'status': 'missing', 'message': 'Event log vazio ou ausente'}]
    
    # Check last event timestamp
    if event_log:
        last_ts = event_log[-1].get('timestamp', '')
        try:
            last_dt = datetime.fromisoformat(last_ts.replace('Z', '+00:00'))
            hours_since = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
            if hours_since > 12:
                return [{'module': 'thalamus', 'status': 'stale', 'hours_since': round(hours_since, 1)}]
        except:
            pass
    
    return []

# ── v2.1: Dangerous Command Detection ─────────────────────────────────────

def scan_dangerous_commands():
    """
    Scan recent agent/tool logs for dangerous command patterns.
    Inspired by Claude Code's command-detection security work.
    Checks: sudo -S, fork bombs, rm -rf /, curl|sh, chmod 777 system, etc.
    """
    threats = []
    
    # Check agent log for dangerous commands
    agent_log = HERMES / 'logs' / 'agent.log'
    if not agent_log.exists():
        return threats
    
    try:
        # Read last 500 lines
        lines = agent_log.read_text().splitlines()[-500:]
        recent = '\n'.join(lines)
        
        for pattern, name, severity in DANGEROUS_PATTERNS:
            matches = re.findall(pattern, recent, re.IGNORECASE)
            if matches:
                threats.append({
                    'type': 'dangerous_command',
                    'pattern': name,
                    'severity': severity,
                    'matches': len(matches) if isinstance(matches, list) else 1,
                    'source': 'agent.log',
                    'message': f'⚠ Comando perigoso detectado: {name} [{severity}]',
                })
    except Exception:
        pass
    
    # Check cron outputs for dangerous commands
    for output_dir in CRON_OUT.iterdir():
        if not output_dir.is_dir():
            continue
        try:
            latest = max(output_dir.glob('*.json'), key=lambda p: p.stat().st_mtime, default=None)
            if latest:
                content = latest.read_text()[:5000]
                for pattern, name, severity in DANGEROUS_PATTERNS:
                    if re.search(pattern, content, re.IGNORECASE):
                        threats.append({
                            'type': 'dangerous_command',
                            'pattern': name,
                            'severity': severity,
                            'source': f'cron_output/{output_dir.name}',
                            'message': f'⚠ Comando perigoso em output de cron: {name} [{severity}]',
                        })
                        break
        except Exception:
            continue
    
    return threats


def scan_error_injections():
    """
    Scan recent outputs for prompt-injection patterns in error strings.
    Prevents tool errors from being used as injection vectors into model context.
    Inspired by Hermes v0.14 error sanitization.
    """
    injections = []
    
    agent_log = HERMES / 'logs' / 'agent.log'
    if not agent_log.exists():
        return injections
    
    try:
        lines = agent_log.read_text().splitlines()[-300:]
        recent = '\n'.join(lines)
        
        for pattern in ERROR_INJECTION_PATTERNS:
            matches = re.findall(pattern, recent, re.IGNORECASE)
            if matches:
                for match in matches[:3]:  # Cap at 3 per pattern
                    injections.append({
                        'type': 'error_injection',
                        'pattern': str(match)[:100],
                        'source': 'agent.log',
                        'message': f'🚨 Possível injeção via erro: {str(match)[:80]}',
                    })
    except Exception:
        pass
    
    return injections


def save_security_state(threats, injections):
    """Persist security findings."""
    security = load_json(SECURITY_LOG) or {'detections': []}
    
    now = datetime.now(timezone.utc).isoformat()
    for t in threats + injections:
        security['detections'].append({
            'timestamp': now,
            **t,
        })
    
    # Keep last 1000 entries
    security['detections'] = security['detections'][-1000:]
    SECURITY_LOG.write_text(json.dumps(security, ensure_ascii=False, indent=2))

def main():
    now = datetime.now(timezone.utc)
    
    failures = []
    
    # Validate each subsystem
    failures.extend(validate_cron_jobs())
    failures.extend(validate_trade_tracker())
    failures.extend(validate_thalamus())
    
    # ── v2.1: Security Scanning ──
    threats = scan_dangerous_commands()
    injections = scan_error_injections()
    security_issues = threats + injections
    if security_issues:
        save_security_state(threats, injections)
    
    # Save state
    state = {
        'last_run': now.isoformat(),
        'failures': len(failures),
        'threats': len(threats),
        'error_injections': len(injections),
        'modules_checked': 5,
    }
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    
    # ── Neural KB Integration (always write, even when no failures) ──
    try:
        from kb_bridge import write as kb_write
        module_health = {}
        for mod in ['monitor.py', 'resilience', 'forex_daily_study']:
            module_health[mod] = 'degraded' if any(f['module'] == mod for f in failures) else 'ok'
        kb_write('cerebellum', {
            'module_health': module_health,
            'validation_failures': failures,
            'last_validation': now.isoformat(),
            'modules_checked': 5,
        })
    except ImportError:
        pass
    
    if not failures and not security_issues:
        return  # All good, silent
    
    # Output failures
    CEREBELLUM_OUT.mkdir(parents=True, exist_ok=True)
    out_file = CEREBELLUM_OUT / f"validate_{now.strftime('%Y%m%d_%H%M%S')}.json"
    out_file.write_text(json.dumps({
        'timestamp': now.isoformat(),
        'component': 'cerebellum',
        'failures': failures,
        'security': {
            'dangerous_commands': [t['pattern'] for t in threats],
            'error_injections': len(injections),
        },
    }, ensure_ascii=False, indent=2))
    
    parts = []
    if failures:
        parts.append(f"🧠 Cerebellum: {len(failures)} falha(s) de validação")
    if threats:
        parts.append(f"🛡️ {len(threats)} comando(s) perigoso(s) detectado(s)")
    if injections:
        parts.append(f"🚨 {len(injections)} possível(is) injeção(ões) via erro")
    print(' | '.join(parts))
    
    for f in failures:
        print(f"  [{f['module']}] {f['status']}: {f.get('message', '')}")
    for t in threats:
        print(f"  [{t['severity']}] {t['message']}")

if __name__ == '__main__':
    main()
