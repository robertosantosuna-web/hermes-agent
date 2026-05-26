#!/usr/bin/env python3
"""
System & Self Study Collector — Ciclos de estudo de infraestrutura.
Coleta dados sobre 4 domínios para análise e auto-aperfeiçoamento:

  1. SO/Infra — Linux, Wayland, Xvfb, Wine, systemd
  2. Agentes — Ollama, browsers, CDP, Desktop Daemon, ydotool
  3. Arquitetura — Skills, cron jobs, brain components, Neural KB
  4. Córtex — Hermes Agent config, modelos, memória, ferramentas

no_agent — zero tokens. Roda semanalmente (sábado 03:00).
Output: ~/.hermes/study_system/{date}/
"""
import json, os, sys, subprocess, pkg_resources
from pathlib import Path
from datetime import datetime, timezone, timedelta

HERMES = Path(os.path.expanduser('~/.hermes'))
STUDY_DIR = HERMES / 'study_system'

# ═══════════════════════════════════════════════════════════
# DOMÍNIO 1: SO / INFRAESTRUTURA
# ═══════════════════════════════════════════════════════════

def study_os():
    """Coleta informações do sistema operacional e infraestrutura."""
    data = {
        'domain': 'os_infrastructure',
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    
    # Kernel
    try:
        data['kernel'] = subprocess.run(['uname', '-r'], capture_output=True, text=True).stdout.strip()
        data['hostname'] = subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip()
        data['os_release'] = subprocess.run(['cat', '/etc/os-release'], capture_output=True, text=True).stdout.strip()[:500]
    except:
        pass
    
    # Display server
    try:
        data['display_server'] = os.environ.get('XDG_SESSION_TYPE', 'unknown')
        data['display'] = os.environ.get('DISPLAY', 'none')
    except:
        pass
    
    # Xvfb
    try:
        xvfb_check = subprocess.run(['pgrep', '-a', 'Xvfb'], capture_output=True, text=True)
        data['xvfb'] = {
            'running': xvfb_check.returncode == 0,
            'processes': xvfb_check.stdout.strip().split('\n') if xvfb_check.stdout.strip() else [],
        }
    except:
        data['xvfb'] = {'running': False, 'error': 'pgrep failed'}
    
    # Wine
    try:
        wine_ver = subprocess.run(['wine', '--version'], capture_output=True, text=True)
        data['wine'] = {
            'installed': wine_ver.returncode == 0,
            'version': wine_ver.stdout.strip() if wine_ver.returncode == 0 else 'not found',
            'prefix': str(HERMES / '.wine_mt5') if (HERMES / '.wine_mt5').exists() else None,
        }
    except:
        data['wine'] = {'installed': False}
    
    # systemd services relevant to us
    try:
        services = subprocess.run(
            ['systemctl', 'list-units', '--type=service', '--state=running', '--no-legend'],
            capture_output=True, text=True
        )
        our_services = [l for l in services.stdout.split('\n') if any(
            kw in l.lower() for kw in ['hermes', 'desktop-daemon', 'xvfb', 'wine', 'ollama']
        )]
        data['systemd_services'] = our_services[:10]
    except:
        data['systemd_services'] = []
    
    # Disk, RAM, CPU
    try:
        disk = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
        data['disk'] = disk.stdout.strip().split('\n')[-1] if disk.stdout.strip() else 'unknown'
        mem = subprocess.run(['free', '-h'], capture_output=True, text=True)
        data['memory'] = mem.stdout.strip()[:300]
        load = subprocess.run(['uptime'], capture_output=True, text=True)
        data['load'] = load.stdout.strip()
    except:
        pass
    
    # Key installed packages
    try:
        pkgs = subprocess.run(['dpkg', '-l'], capture_output=True, text=True)
        key_pkgs = [l for l in pkgs.stdout.split('\n') if any(
            kw in l.lower() for kw in ['xdotool', 'wine', 'xvfb', 'tesseract', 'chromium', 'playwright', 'ollama']
        )]
        data['key_packages'] = key_pkgs[:15]
    except:
        data['key_packages'] = []
    
    return data

# ═══════════════════════════════════════════════════════════
# DOMÍNIO 2: AGENTES / FERRAMENTAS
# ═══════════════════════════════════════════════════════════

def study_agents():
    """Coleta informações sobre agentes e ferramentas de automação."""
    data = {
        'domain': 'agents_tools',
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    
    # Ollama
    try:
        ollama_list = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        data['ollama'] = {
            'available': ollama_list.returncode == 0,
            'models': ollama_list.stdout.strip(),
        }
    except:
        data['ollama'] = {'available': False}
    
    # Python packages
    try:
        pkgs = {p.key: p.version for p in pkg_resources.working_set}
        key_libs = {k: v for k, v in pkgs.items() if k in [
            'playwright', 'selenium', 'websockets', 'Pillow', 'numpy', 'pandas',
            'yfinance', 'feedparser', 'youtube-transcript-api', 'opencv-python',
            'pytesseract', 'psutil', 'requests', 'fastapi', 'uvicorn',
        ]}
        data['python_libs'] = key_libs
    except:
        data['python_libs'] = {}
    
    # Desktop Daemon
    try:
        dd_check = subprocess.run(['systemctl', 'is-active', 'desktop-daemon'], capture_output=True, text=True)
        dd_port = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
        data['desktop_daemon'] = {
            'service_active': dd_check.stdout.strip() == 'active',
            'port_9876': ':9876' in dd_port.stdout,
        }
    except:
        data['desktop_daemon'] = {'status': 'unknown'}
    
    # Browser automation
    try:
        playwright_check = subprocess.run(
            ['python3', '-c', 'from playwright.sync_api import sync_playwright; print("OK")'],
            capture_output=True, text=True
        )
        data['playwright'] = {'functional': 'OK' in playwright_check.stdout}
    except:
        data['playwright'] = {'functional': False}
    
    # ydotool
    try:
        ydo = subprocess.run(['which', 'ydotool'], capture_output=True, text=True)
        data['ydotool'] = {
            'installed': ydo.returncode == 0,
            'path': ydo.stdout.strip() if ydo.returncode == 0 else None,
        }
    except:
        data['ydotool'] = {'installed': False}
    
    # MT5 status (via Wine Xvfb)
    try:
        mt5_check = subprocess.run(
            ['pgrep', '-f', 'terminal64.exe'],
            capture_output=True, text=True
        )
        data['mt5'] = {
            'running': mt5_check.returncode == 0,
            'pids': mt5_check.stdout.strip().split('\n') if mt5_check.stdout.strip() else [],
        }
    except:
        data['mt5'] = {'running': False}
    
    return data

# ═══════════════════════════════════════════════════════════
# DOMÍNIO 3: ARQUITETURA ENTIDADE
# ═══════════════════════════════════════════════════════════

def study_architecture():
    """Coleta informações sobre a arquitetura da ENTIDADE."""
    data = {
        'domain': 'entidade_architecture',
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    
    # Skills inventory
    skills_dir = HERMES / 'skills'
    if skills_dir.exists():
        skill_cats = {}
        total_skills = 0
        for cat_dir in skills_dir.iterdir():
            if cat_dir.is_dir():
                skills = list(cat_dir.glob('*/SKILL.md'))
                skill_cats[cat_dir.name] = {
                    'count': len(skills),
                    'names': [s.parent.name for s in skills],
                }
                total_skills += len(skills)
        data['skills'] = {
            'total': total_skills,
            'categories': len(skill_cats),
            'by_category': skill_cats,
        }
    
    # Scripts inventory
    scripts_dir = HERMES / 'scripts'
    if scripts_dir.exists():
        py_scripts = list(scripts_dir.glob('*.py'))
        sh_scripts = list(scripts_dir.glob('*.sh'))
        data['scripts'] = {
            'python': len(py_scripts),
            'shell': len(sh_scripts),
            'total': len(py_scripts) + len(sh_scripts),
            'names': [s.name for s in sorted(py_scripts + sh_scripts)],
        }
    
    # Brain components
    brain_files = {
        'thalamus': list((HERMES / 'thalamus').glob('*.py')) if (HERMES / 'thalamus').exists() else [],
        'cortex': list((HERMES / 'cortex').glob('*.py')) if (HERMES / 'cortex').exists() else [],
        'executive': list((HERMES / 'executive').glob('*.py')) if (HERMES / 'executive').exists() else [],
    }
    data['brain_components'] = {
        k: {'files': len(v), 'names': [f.name for f in v]}
        for k, v in brain_files.items()
    }
    
    # Neural KB stats
    kb_path = HERMES / 'neural_knowledge_base.json'
    if kb_path.exists():
        try:
            kb = json.loads(kb_path.read_text())
            data['neural_kb'] = {
                'synapses': kb.get('_meta', {}).get('total_synapses', 0),
                'modules': len(kb.get('modules', {})),
                'market_regime': kb.get('global_state', {}).get('market_regime', 'unknown'),
            }
        except:
            data['neural_kb'] = {'status': 'error'}
    
    # Codebase metrics (using pygount if available)
    try:
        result = subprocess.run(
            ['python3', '-m', 'pygount', '--format=summary', str(HERMES / 'scripts')],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data['code_metrics'] = {'pygount': result.stdout.strip()[:1000]}
    except:
        pass
    
    # Evolution logs
    evo_log = HERMES / 'brain_evolution_log.json'
    self_evo = HERMES / 'self_evolution_log.json'
    data['evolution'] = {
        'brain_events': len(json.loads(evo_log.read_text()).get('evolution_events', [])) if evo_log.exists() else 0,
        'self_cycles': len(json.loads(self_evo.read_text()).get('cycles', [])) if self_evo.exists() else 0,
    }
    
    return data

# ═══════════════════════════════════════════════════════════
# DOMÍNIO 4: CÓRTEX (HERMES AGENT)
# ═══════════════════════════════════════════════════════════

def study_cortex():
    """Coleta informações sobre o Hermes Agent / Córtex."""
    data = {
        'domain': 'cortex_hermes',
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    
    # Config
    config_path = HERMES / 'config.yaml'
    if config_path.exists():
        try:
            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f)
            data['config'] = {
                'model': config.get('model', {}).get('model', 'unknown') if 'model' in config else 'unknown',
                'provider': config.get('model', {}).get('provider', 'unknown') if 'model' in config else 'unknown',
                'max_turns': config.get('limits', {}).get('max_turns', 'unknown'),
                'memory_limit': config.get('memory', {}).get('char_limit', 'unknown'),
            }
        except:
            data['config'] = {'status': 'parse_error'}
    
    # Memory usage
    memory_path = HERMES / 'memory.json'
    if memory_path.exists():
        try:
            mem = json.loads(memory_path.read_text())
            data['memory'] = {
                'entries': len(mem.get('entries', [])),
                'size_chars': len(json.dumps(mem)),
                'usage_pct': round(len(json.dumps(mem)) / 4000 * 100, 1),
            }
        except:
            data['memory'] = {'status': 'error'}
    
    # Available tools (check tool definitions)
    tools_search = list(HERMES.glob('tools/*.py')) if (HERMES / 'tools').exists() else []
    data['tools'] = {
        'tool_files': len(tools_search),
    }
    
    # Skills loaded by cortex
    skills_meta = HERMES / 'skills'
    if skills_meta.exists():
        md_files = list(skills_meta.glob('*/*/SKILL.md'))
        data['skills_available'] = {
            'total': len(md_files),
            'core': len(list(skills_meta.glob('core/*/SKILL.md'))),
            'forex': len(list(skills_meta.glob('forex/*/SKILL.md'))) if (skills_meta / 'forex').exists() else 0,
        }
    
    # Recent sessions (cortex log)
    cortex_log = HERMES / 'cortex_synapses.jsonl'
    if cortex_log.exists():
        lines = cortex_log.read_text().strip().split('\n')
        data['cortex_activity'] = {
            'insights_written': len([l for l in lines if l.strip()]),
            'last_insight': json.loads(lines[-1]) if lines and lines[-1].strip() else None,
        }
    
    return data

# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    now = datetime.now(timezone.utc)
    today = now.strftime('%Y-%m-%d')
    date_dir = STUDY_DIR / today
    date_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📚 System & Self Study — {today}")
    
    domains = {
        'os': ('SO / Infraestrutura', study_os),
        'agents': ('Agentes / Ferramentas', study_agents),
        'architecture': ('Arquitetura ENTIDADE', study_architecture),
        'cortex': ('Córtex / Hermes Agent', study_cortex),
    }
    
    report = {
        'date': today,
        'domains': {},
    }
    
    for key, (label, func) in domains.items():
        print(f"\n▶ {label}")
        try:
            data = func()
            report['domains'][key] = data
            
            # Summary per domain
            if key == 'os':
                print(f"  Kernel: {data.get('kernel', '?')}")
                print(f"  Display: {data.get('display_server', '?')}")
                print(f"  Wine: {data.get('wine', {}).get('installed', False)}")
                print(f"  Xvfb: {data.get('xvfb', {}).get('running', False)}")
            elif key == 'agents':
                print(f"  Ollama: {data.get('ollama', {}).get('available', False)}")
                print(f"  Desktop Daemon: {data.get('desktop_daemon', {}).get('service_active', False)}")
                print(f"  MT5: {data.get('mt5', {}).get('running', False)}")
                print(f"  ydotool: {data.get('ydotool', {}).get('installed', False)}")
            elif key == 'architecture':
                print(f"  Skills: {data.get('skills', {}).get('total', 0)}")
                print(f"  Scripts: {data.get('scripts', {}).get('total', 0)}")
                print(f"  Neural KB: {data.get('neural_kb', {}).get('synapses', 0)} synapses")
                print(f"  Evolution: {data.get('evolution', {})}")
            elif key == 'cortex':
                print(f"  Model: {data.get('config', {}).get('model', '?')}")
                print(f"  Memory: {data.get('memory', {}).get('usage_pct', '?')}%")
                print(f"  Skills: {data.get('skills_available', {}).get('total', 0)}")
                print(f"  Insights: {data.get('cortex_activity', {}).get('insights_written', 0)}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            report['domains'][key] = {'error': str(e)}
    
    # Save report
    report_path = date_dir / 'system_study_report.json'
    report_path.write_text(json.dumps(report, indent=2, default=str))
    
    # Save per-domain files for easy reading
    for key in domains:
        domain_path = date_dir / f'{key}_study.json'
        if key in report['domains']:
            domain_path.write_text(json.dumps(report['domains'][key], indent=2, default=str))
    
    print(f"\n✅ Report salvo: {report_path}")
    print(f"   Domínios: {len(report['domains'])}")

if __name__ == '__main__':
    main()
