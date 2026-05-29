#!/usr/bin/env python3
"""
Instagram Monitor — Modo Passivo (v2)
═══════════════════════════════════════

Instagram bloqueia qualquer automação (CDP, Selenium, Playwright).
Estratégia: monitoramento passivo de uso sem interagir com a página.

Métricas:
- Detecção de uso (aba aberta no Brave)
- Tempo de sessão
- Frequência diária
- Score social derivado

NÃO tenta login, NÃO extrai conteúdo, NÃO navega.
"""

import json, os, sys, time, subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

H = Path.home() / '.hermes'
SOCIAL_DIR = H / 'social'
INSTAGRAM_DATA = SOCIAL_DIR / 'instagram_usage.json'
CDP_PORT = 9222

def ensure_dirs():
    SOCIAL_DIR.mkdir(parents=True, exist_ok=True)

def detect_instagram_tab():
    """Detecta se Instagram está aberto no Brave sem interagir com a página."""
    try:
        r = subprocess.run(['curl', '-s', f'http://localhost:{CDP_PORT}/json'],
            capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            return None
        
        tabs = json.loads(r.stdout)
        for t in tabs:
            url = t.get('url', '')
            if 'instagram.com' in url:
                # Só retorna se NÃO for página de recaptcha
                if 'recaptcha' not in url and 'auth_platform' not in url:
                    return {
                        'tab_id': t.get('id'),
                        'url': url,
                        'title': t.get('title', ''),
                        'detected_at': datetime.now(timezone.utc).isoformat()
                    }
        return None
    except:
        return None

def load_usage():
    if INSTAGRAM_DATA.exists():
        try:
            return json.loads(INSTAGRAM_DATA.read_text())
        except:
            pass
    return {
        'sessions': [],
        'daily_summary': {},
        'last_detection': None
    }

def save_usage(data):
    ensure_dirs()
    INSTAGRAM_DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False))

def record_session():
    """Registra detecção de uso do Instagram."""
    data = load_usage()
    now = datetime.now(timezone.utc)
    today = now.strftime('%Y-%m-%d')
    
    detected = detect_instagram_tab()
    
    # Atualizar resumo diário
    if today not in data['daily_summary']:
        data['daily_summary'][today] = {
            'detections': 0,
            'first_seen': None,
            'last_seen': None
        }
    
    summary = data['daily_summary'][today]
    
    if detected:
        summary['detections'] += 1
        summary['last_seen'] = now.isoformat()
        if not summary['first_seen']:
            summary['first_seen'] = now.isoformat()
        
        # Registrar sessão se for nova (gap > 5 min desde última detecção)
        last = data.get('last_detection')
        if not last or (now - datetime.fromisoformat(last)).total_seconds() > 300:
            data.setdefault('sessions', []).append({
                'start': now.isoformat(),
                'day': today,
                'hour': now.hour
            })
        
        data['last_detection'] = now.isoformat()
    
    # Limpar sessões antigas (>7 dias)
    cutoff = (now - timedelta(days=7)).isoformat()
    data['sessions'] = [s for s in data.get('sessions', []) if s.get('start', '') > cutoff]
    
    # Limpar daily_summary antigo (>7 dias)
    data['daily_summary'] = {k: v for k, v in data.get('daily_summary', {}).items() if k >= (now - timedelta(days=7)).strftime('%Y-%m-%d')}
    
    save_usage(data)
    return detected is not None

def analyze_usage():
    """Analisa padrão de uso do Instagram."""
    data = load_usage()
    now = datetime.now(timezone.utc)
    today = now.strftime('%Y-%m-%d')
    
    sessions = data.get('sessions', [])
    today_sessions = [s for s in sessions if s.get('day') == today]
    
    # Últimos 7 dias
    days_with_use = len(set(s.get('day') for s in sessions))
    
    # Horários de pico
    hours = [s.get('hour', 0) for s in sessions]
    late_night = sum(1 for h in hours if h >= 22 or h <= 5)
    
    analysis = {
        'timestamp': now.isoformat(),
        'sessions_today': len(today_sessions),
        'sessions_7days': len(sessions),
        'days_active_7days': days_with_use,
        'late_night_sessions': late_night,
        'currently_open': detect_instagram_tab() is not None,
        'social_score': 10,
        'usage_pattern': 'saudável',
        'insights': [],
        'recommendations': []
    }
    
    # Score e padrão
    avg_daily = len(sessions) / max(days_with_use, 1)
    
    if avg_daily <= 2 and late_night == 0:
        analysis['usage_pattern'] = 'saudável'
        analysis['social_score'] = 9
    elif avg_daily <= 4:
        analysis['usage_pattern'] = 'moderado'
        analysis['social_score'] = 7
    elif avg_daily <= 8:
        analysis['usage_pattern'] = 'elevado'
        analysis['social_score'] = 5
        analysis['insights'].append('Uso frequente — considere limitar sessões')
    else:
        analysis['usage_pattern'] = 'excessivo'
        analysis['social_score'] = 3
        analysis['insights'].append('Uso excessivo detectado')
        analysis['recommendations'].append('Timer de 15min para Instagram')
    
    if late_night > 0:
        analysis['social_score'] -= 1
        analysis['insights'].append(f'{late_night} sessões tarde da noite — afeta qualidade do sono')
        analysis['recommendations'].append('Evitar Instagram após 22h')
    
    if analysis['currently_open']:
        analysis['insights'].append('Instagram aberto agora')
    
    return analysis

def run():
    """Execução principal (modo passivo)."""
    print(f"📱 Instagram Monitor {datetime.now().strftime('%H:%M')}")
    
    is_open = record_session()
    analysis = analyze_usage()
    
    status = "🟢 aberto" if is_open else "⚫ fechado"
    print(f"  Status: {status}")
    print(f"  Sessões hoje: {analysis['sessions_today']}")
    print(f"  Score social: {analysis['social_score']}/10")
    print(f"  Padrão: {analysis['usage_pattern']}")
    
    if analysis['insights']:
        for i in analysis['insights']:
            print(f"  💡 {i}")
    
    # Salvar estado para Córtex Insular
    state = {
        'last_run': datetime.now(timezone.utc).isoformat(),
        'currently_open': is_open,
        'sessions_today': analysis['sessions_today'],
        'social_score': analysis['social_score'],
        'usage_pattern': analysis['usage_pattern']
    }
    (SOCIAL_DIR / 'instagram_state.json').write_text(json.dumps(state, indent=2))
    
    # Alerta se score baixo
    if analysis['social_score'] < 5:
        try:
            import thalamus
            thalamus.broadcast_to_workspace(
                f"📱 Instagram: uso {analysis['usage_pattern']} "
                f"(score {analysis['social_score']}/10). "
                f"{len(analysis.get('recommendations',[]))} recomendações.",
                priority=4, source="cortex_insular"
            )
        except:
            pass
    
    return analysis

if __name__ == "__main__":
    run()
