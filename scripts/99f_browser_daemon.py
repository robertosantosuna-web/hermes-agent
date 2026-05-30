#!/usr/bin/env python3
"""
99FREELAS BROWSER DAEMON — Mantém sessão viva 24/7.
Auto-relogin via Google OAuth quando expira.
Roda como processo background permanente.
"""
import sys, time, json
from pathlib import Path
from datetime import datetime, timezone

PROFILE_DIR = Path('/tmp/brave_hermes_99f')
BRAVE_BIN = '/opt/brave.com/brave/brave'
STATE_FILE = Path('/tmp/99f_daemon_state.json')
KEEPALIVE_INTERVAL = 600  # 10 minutos
GOOGLE_EMAIL = 'robertosantos.una@gmail.com'

def save_state(status, url='', error=''):
    STATE_FILE.write_text(json.dumps({
        'status': status,
        'url': url[:120],
        'error': error,
        'last_check': datetime.now(timezone.utc).isoformat(),
        'pid': __import__('os').getpid()
    }))

def check_logged_in(page):
    """Verifica se a sessão está ativa."""
    try:
        page.goto('https://www.99freelas.com.br/dashboard', 
                  wait_until='domcontentloaded', timeout=20000)
        time.sleep(3)
        url = page.url
        
        if 'login' in url.lower():
            return False, url
        if 'dashboard' in url.lower():
            return True, url
        # Pode estar em outra pagina logada
        text = page.inner_text('body')
        if 'Roberto' in text and ('freelancer' in text.lower() or 'projeto' in text.lower()):
            return True, url
        return False, url
    except Exception as e:
        return False, str(e)[:100]

def do_google_login(page):
    """Faz login via Google OAuth no 99Freelas."""
    try:
        # Ir para pagina de login
        page.goto('https://www.99freelas.com.br/login', 
                  wait_until='domcontentloaded', timeout=30000)
        time.sleep(4)
        
        # Verificar se redirecionou pro Google OAuth
        url = page.url
        if 'accounts.google.com' in url:
            print('  Google OAuth detectado, preenchendo email...')
            
            # Email
            email_input = page.locator('input[type="email"]')
            if email_input.count() > 0:
                email_input.first.click()
                time.sleep(0.5)
                page.keyboard.type(GOOGLE_EMAIL, delay=50)
                time.sleep(0.5)
                page.keyboard.press('Enter')
                time.sleep(5)
                
                # Verificar se pediu senha
                text = page.inner_text('body')
                if 'senha' in text.lower() or 'password' in text.lower():
                    print('  Google pediu senha - precisa intervencao manual')
                    save_state('needs_password', page.url)
                    return False
                
                # Verificar se estamos logados
                time.sleep(3)
                if '99freelas' in page.url.lower() or 'dashboard' in page.url.lower():
                    print('  Login OK!')
                    save_state('logged_in', page.url)
                    return True
        
        # Se nao redirecionou, tentar clicar no botao Google
        google_links = page.locator('a[href*="google"], a[href*="oauth"]').all()
        for link in google_links:
            href = link.get_attribute('href') or ''
            if 'accounts.google.com' in href:
                link.click()
                time.sleep(5)
                return do_google_login(page)  # recursivo apos redirect
        
        print(f'  Nao encontrou fluxo Google OAuth. URL: {url[:100]}')
        return False
        
    except Exception as e:
        print(f'  Erro login: {e}')
        save_state('error', error=str(e)[:200])
        return False

def _run_submission_pipeline(page):
    """Busca projetos e submete propostas usando a sessao ativa."""
    import subprocess, re
    
    # 1. Rodar IMAP agent
    print('  [1/2] Coletando via IMAP...')
    result = subprocess.run(
        ['python3', str(Path.home() / '.hermes' / 'brain' / 'freelancer_agent.py')],
        capture_output=True, text=True, timeout=60,
        cwd=str(Path.home() / '.hermes')
    )
    
    # 2. Extrair projetos
    projects = []
    for line in result.stdout.split('\n'):
        if '•' in line and len(line) > 20:
            title = line.split('•')[-1].strip()
            projects.append(title)
    
    print(f'  [1/2] {len(projects)} projetos IMAP')
    
    # 3. Buscar na plataforma e submeter
    submitted = 0
    state_file = Path('/tmp/freelancer_submitter_state.json')
    state = {}
    if state_file.exists():
        state = json.loads(state_file.read_text())
    if 'submitted' not in state:
        state['submitted'] = []
    
    try:
        page.goto('https://www.99freelas.com.br/projects', 
                  wait_until='domcontentloaded', timeout=20000)
        time.sleep(3)
        
        # Filtrar <24h
        filtro = page.locator('text=Menos de 24 horas').first
        if filtro.count():
            filtro.click()
            time.sleep(2)
        
        # Extrair links
        links = page.locator('a[href*=\"/project/\"]').all()
        seen = set()
        for link in links:
            try:
                txt = link.inner_text().strip()
                href = link.get_attribute('href') or ''
                if len(txt) < 15 or '/project/' not in href or href in seen:
                    continue
                seen.add(href)
                
                full_url = f"https://www.99freelas.com.br{href}" if href.startswith('/') else href
                if full_url in state['submitted']:
                    continue
                
                # Classificar via keywords
                text_lower = txt.lower()
                if any(kw in text_lower for kw in ['word', 'abnt', 'format', 'excel', 'planilha', 'digit', 'cadastr']):
                    print(f'  📋 {txt[:80]}')
                    result = _try_submit(page, full_url, txt)
                    print(f'     → {result}')
                    state['submitted'].append(full_url)
                    if result == 'submitted':
                        submitted += 1
                    if submitted >= 3:
                        break
            except:
                pass
    
    except Exception as e:
        print(f'  Erro busca: {e}')
    
    state['last_run'] = datetime.now(timezone.utc).isoformat()
    state_file.write_text(json.dumps(state, indent=2))
    print(f'  [2/2] {submitted} propostas enviadas')


def _try_submit(page, project_url, title):
    """Tenta submeter proposta para um projeto."""
    import re
    try:
        page.goto(project_url, wait_until='domcontentloaded', timeout=20000)
        time.sleep(3)
        
        text = page.inner_text('body')
        
        if 'exclusivo' in text.lower() or 'premium' in text.lower():
            return 'exclusive'
        
        m = re.search(r'Propostas:\s*(\d+)', text)
        if m and int(m.group(1)) > 50:
            return 'high_competition'
        
        if 'você já enviou' in text.lower():
            return 'already_submitted'
        
        btn = page.locator('button').filter(has_text='Enviar proposta').first
        if not btn.count():
            btn = page.locator('a').filter(has_text='Enviar proposta').first
        if not btn.count():
            return 'no_button'
        
        btn.click()
        time.sleep(4)
        
        # Valor e prazo
        inputs = page.locator('input').all()
        for inp in inputs:
            try:
                if inp.get_attribute('type') == 'number':
                    inp.click()
                    time.sleep(0.3)
                    page.keyboard.type('100', delay=30)
            except:
                pass
        
        # Proposta
        proposta = f"Ola, entendi o projeto. Tenho experiencia com automacao e entrego com qualidade.\\n\\nPrazo: 5 dias. Valor: R$100.\\n\\nabs,\\nRoberto"
        ta = page.locator('textarea').first
        if ta.count():
            ta.click()
            time.sleep(0.5)
            page.keyboard.type(proposta, delay=10)
        
        enviar = page.locator('button').filter(has_text='Enviar').last
        if enviar.count():
            enviar.click()
            time.sleep(3)
            return 'submitted'
        
        return 'filled_not_sent'
        
    except Exception as e:
        return f'error: {str(e)[:80]}'


def main():
    from playwright.sync_api import sync_playwright
    
    print(f'🚀 99Freelas Browser Daemon iniciado (PID {__import__("os").getpid()})')
    save_state('starting')
    
    browser = None
    page = None
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                executable_path=BRAVE_BIN,
                headless=False,
                args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
            )
            page = browser.new_page()
            
            # Verificar sessao inicial
            logged_in, url = check_logged_in(page)
            status = "logado" if logged_in else "deslogado"
            print(f'Estado inicial: {status} ({url[:80]})')
            
            if not logged_in:
                print('Tentando login...')
                logged_in = do_google_login(page)
            
            if not logged_in:
                save_state('needs_manual_login')
                print('❌ Login falhou - aguardando intervencao manual')
                # Fica rodando, tentando a cada 5 min
            else:
                save_state('running', url)
            
            # Loop keep-alive + submissao
            submission_counter = 0
            while True:
                time.sleep(KEEPALIVE_INTERVAL)
                
                try:
                    logged_in, url = check_logged_in(page)
                    
                    if logged_in:
                        save_state('running', url)
                        ts = datetime.now().strftime("%H:%M")
                        print(f'[{ts}] ✅ Sessao ativa')
                        
                        # A cada 2h (12 ciclos de 10min), rodar submissao
                        submission_counter += 1
                        if submission_counter >= 12:
                            submission_counter = 0
                            print(f'[{ts}] 🔍 Rodando pipeline de submissao...')
                            _run_submission_pipeline(page)
                    else:
                        ts = datetime.now().strftime("%H:%M")
                        print(f'[{ts}] ⚠️ Sessao expirada, relogando...')
                        logged_in = do_google_login(page)
                        
                        if not logged_in:
                            save_state('needs_manual_login')
                            print('  ❌ Relogin falhou')
                except Exception as e:
                    print(f'  Erro keep-alive: {e}')
                    save_state('error', error=str(e)[:200])
    
    except KeyboardInterrupt:
        print('Daemon encerrado')
    except Exception as e:
        print(f'Erro fatal: {e}')
        save_state('crashed', error=str(e)[:500])
    finally:
        if browser:
            browser.close()

if __name__ == '__main__':
    main()
