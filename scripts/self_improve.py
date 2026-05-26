#!/usr/bin/env python3
"""
ROTINA DE AUTO-APRIMORAMENTO — ENTIDADE
Executa 1x/dia, ~25 minutos.
Mapeia eficiência, corrige bugs, otimiza código local.
"""
import os, sys, json, subprocess
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

BASE = os.path.expanduser("~/.hermes")
LOG_FILE = os.path.expanduser("~/.hermes/logs/agent.log")
ERROR_LOG = os.path.expanduser("~/.hermes/logs/errors.log")
IMPROVEMENT_LOG = os.path.expanduser("~/.hermes/monitor/improvements.jsonl")

def analyze_errors():
    """Analisa padrões de erro nos logs"""
    errors = []
    if Path(ERROR_LOG).exists():
        with open(ERROR_LOG) as f:
            for line in f:
                if 'ERROR' in line or 'WARNING' in line or 'Traceback' in line:
                    errors.append(line.strip()[-200:])
    
    # Classificar erros
    patterns = Counter()
    for e in errors:
        if 'timeout' in e.lower():
            patterns['timeout'] += 1
        elif 'connection' in e.lower():
            patterns['connection'] += 1
        elif 'permission' in e.lower():
            patterns['permission'] += 1
        elif 'not found' in e.lower():
            patterns['not_found'] += 1
        elif 'cloudflare' in e.lower():
            patterns['cloudflare'] += 1
        elif 'token' in e.lower():
            patterns['token_limit'] += 1
        else:
            patterns['other'] += 1
    
    return dict(patterns), len(errors)

def analyze_cron_health():
    """Verifica saúde dos cron jobs"""
    try:
        result = subprocess.run(['hermes', 'cron', 'list'], capture_output=True, text=True, timeout=10)
        output = result.stdout
        
        jobs_total = output.count('job_id')
        jobs_ok = output.count('ok')
        jobs_error = output.count('error')
        
        return {
            'total': jobs_total,
            'ok': jobs_ok,
            'error': jobs_error,
        }
    except:
        return {'total': 0, 'ok': 0, 'error': 0}

def analyze_token_efficiency():
    """Analisa eficiência de uso de tokens"""
    tokens_file = Path(BASE) / "monitor" / "token_usage.json"
    
    # Estimar pelos logs de sessão
    sessions = list(Path(BASE) / "logs" / "sessions")
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_sessions = [s for s in sessions if today in s.name]
    
    return {
        'sessions_today': len(today_sessions),
        'estimated_tokens': len(today_sessions) * 50000,  # estimativa bruta
    }

def check_monitor_effectiveness():
    """Verifica se o motor local está funcionando"""
    wake_file = Path(BASE) / "monitor" / "wake.txt"
    alert_file = Path(BASE) / "monitor" / "alerts.json"
    
    wakes = 0
    if wake_file.exists():
        content = wake_file.read_text()
        wakes = content.count('WAKE:')
    
    alerts = []
    if alert_file.exists():
        try:
            alerts = json.loads(alert_file.read_text())
        except:
            pass
    
    return {
        'wakes_today': wakes,
        'alerts_pending': len(alerts),
    }

def check_script_health():
    """Verifica se scripts locais estão funcionando"""
    scripts = {
        'monitor.py': Path(BASE) / "scripts" / "monitor.py",
        'forex_check.py': Path(BASE) / "scripts" / "forex_check.py",
        'forex_daily_study.py': Path(BASE) / "scripts" / "forex_daily_study.py",
        'motor_central.py': Path(BASE) / "scripts" / "motor_central.py",
        'scalping_watchdog.py': Path(BASE) / "scripts" / "scalping_watchdog.py",
    }
    
    status = {}
    for name, path in scripts.items():
        if path.exists():
            try:
                result = subprocess.run(['python3', '-c', f'import ast; ast.parse(open("{path}").read())'],
                                      capture_output=True, timeout=5)
                status[name] = 'OK' if result.returncode == 0 else 'SYNTAX_ERROR'
            except:
                status[name] = 'CHECK_ERROR'
        else:
            status[name] = 'MISSING'
    
    return status

def suggest_improvements():
    """Sugere melhorias baseado na análise"""
    suggestions = []
    
    errors, total = analyze_errors()
    cron = analyze_cron_health()
    monitor = check_monitor_effectiveness()
    scripts = check_script_health()
    
    # Timeout issues
    if errors.get('timeout', 0) > 5:
        suggestions.append("ALTA TAXA DE TIMEOUT: Reduzir complexidade de chamadas CDP. Usar scripts no_agent para coleta.")
    
    # Cloudflare blocks
    if errors.get('cloudflare', 0) > 3:
        suggestions.append("CLOUDFLARE FREQUENTE: Migrar 100% para monitoramento por email (IMAP). Parar de tentar CDP em 99Freelas.")
    
    # Token limits
    if errors.get('token_limit', 0) > 2:
        suggestions.append("ESTORO DE TOKENS: Contexto muito longo. Fazer compaction mais agressivo. Respostas mais curtas.")
    
    # Cron health
    if cron['error'] > 0:
        suggestions.append(f"CRON JOBS COM ERRO: {cron['error']} jobs falhando. Revisar e corrigir scripts.")
    
    # Script issues
    broken = [name for name, status in scripts.items() if status != 'OK']
    if broken:
        suggestions.append(f"SCRIPTS QUEBRADOS: {', '.join(broken)}. Corrigir sintaxe ou recriar.")
    
    # Monitor effectiveness
    if monitor['wakes_today'] == 0 and monitor['alerts_pending'] > 0:
        suggestions.append("MOTOR NÃO ACORDOU AGENTE: Alertas pendentes mas wake não disparou. Verificar monitor.py.")
    
    return suggestions

def main():
    print("=" * 60)
    print("ROTINA DE AUTO-APRIMORAMENTO — ENTIDADE")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # 1. Análise de erros
    print("\n🔍 ERROS NOS LOGS:")
    errors, total = analyze_errors()
    print(f"  Total: {total} erros/warnings")
    for etype, count in sorted(errors.items(), key=lambda x: -x[1]):
        print(f"    {etype}: {count}")
    
    # 2. Saúde dos cron jobs
    print("\n⏰ CRON JOBS:")
    cron = analyze_cron_health()
    print(f"  Total: {cron['total']} | OK: {cron['ok']} | Erro: {cron['error']}")
    
    # 3. Scripts locais
    print("\n📜 SCRIPTS:")
    scripts = check_script_health()
    for name, status in scripts.items():
        icon = '✅' if status == 'OK' else '❌'
        print(f"  {icon} {name}: {status}")
    
    # 4. Motor local
    print("\n🔔 MOTOR LOCAL:")
    monitor = check_monitor_effectiveness()
    print(f"  Wakes hoje: {monitor['wakes_today']}")
    print(f"  Alertas pendentes: {monitor['alerts_pending']}")
    
    # 5. Eficiência
    print("\n📊 EFICIÊNCIA:")
    eff = analyze_token_efficiency()
    print(f"  Sessões hoje: {eff['sessions_today']}")
    print(f"  Tokens estimados: {eff['estimated_tokens']:,}")
    
    # 6. Sugestões
    print("\n💡 SUGESTÕES DE MELHORIA:")
    suggestions = suggest_improvements()
    if suggestions:
        for s in suggestions:
            print(f"  ⚡ {s}")
    else:
        print("  ✅ Nada crítico detectado")
    
    # Salvar log
    log_entry = {
        'date': datetime.now().isoformat(),
        'errors': dict(errors),
        'cron': cron,
        'scripts': scripts,
        'monitor': monitor,
        'suggestions': suggestions,
    }
    
    Path(IMPROVEMENT_LOG).parent.mkdir(parents=True, exist_ok=True)
    with open(IMPROVEMENT_LOG, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    print(f"\n✅ Auto-análise concluída. Log: {IMPROVEMENT_LOG}")

if __name__ == "__main__":
    main()
