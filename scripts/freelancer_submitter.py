#!/usr/bin/env python3
"""
FREELANCER SUBMITTER v1 — Agente autônomo de submissão de propostas
Mantém browser vivo, submete propostas para projetos 100% automatizáveis.
"""
import sys, json, time, re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
HERMES = Path.home() / '.hermes'
STATE_FILE = Path('/tmp/freelancer_submitter_state.json')
PROFILE_DIR = Path('/tmp/brave_hermes_99f')
BRAVE_BIN = '/opt/brave.com/brave/brave'

# Projetos 100% automatizaveis (ferramentas disponiveis)
AUTOMATABLE_KEYWORDS = [
    ('word', 'python-docx'),
    ('abnt', 'python-docx'),
    ('formatação', 'python-docx'),
    ('formatar', 'python-docx'),
    ('excel', 'openpyxl'),
    ('planilha', 'openpyxl'),
    ('google sheets', 'gspread'),
    ('digitação', 'script'),
    ('digitar', 'script'),
    ('cadastrar', 'script'),
    ('cadastro', 'script'),
    ('copiar e colar', 'script'),
    ('transcrição', 'script'),
    ('converter pdf', 'pymupdf'),
    ('pdf editável', 'pymupdf'),
]

# Templates de proposta por tipo
TEMPLATES = {
    'python-docx': "Entendi o escopo. Tenho experiencia com automacao de documentos Word (python-docx) - consigo entregar com formatacao consistente, padrao ABNT e revisoes incluidas.\\n\\nPrazo: {prazo} dias. Valor: R${valor}.\\n\\nabs,\\nRoberto",
    'openpyxl': "Entendi a ideia. Tenho experiencia com automacao de planilhas Excel (openpyxl) - entrego com formulas, validacao e formatacao profissional.\\n\\nPrazo: {prazo} dias. Valor: R${valor}.\\n\\nabs,\\nRoberto",
    'script': "Entendi o trabalho. Consigo automatizar esse processo com script Python, garantindo velocidade e zero erros.\\n\\nPrazo: {prazo} dias. Valor: R${valor}.\\n\\nabs,\\nRoberto",
    'pymupdf': "Entendi. Tenho experiencia com conversao e extracao de PDFs (pymupdf) - entrego arquivo editavel mantendo formatacao original.\\n\\nPrazo: {prazo} dias. Valor: R${valor}.\\n\\nabs,\\nRoberto",
    'gspread': "Entendi. Trabalho com Google Sheets e automacao via API (gspread) - entrego planilha organizada e funcional.\\n\\nPrazo: {prazo} dias. Valor: R${valor}.\\n\\nabs,\\nRoberto",
}

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {'submitted': [], 'errors': [], 'last_run': None}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))

def classify_project(title, description=''):
    """Classifica projeto como automatizavel e qual ferramenta usar."""
    text = (title + ' ' + description).lower()
    for kw, tool in AUTOMATABLE_KEYWORDS:
        if kw in text:
            return True, tool
    return False, None

def submit_proposal(page, project_url, tool, title):
    """Submete proposta para um projeto. Retorna True se enviado."""
    try:
        page.goto(project_url, wait_until='domcontentloaded', timeout=30000)
        time.sleep(4)
        
        text = page.inner_text('body')
        
        # Verificar se ja existe proposta enviada
        if 'proposta enviada' in text.lower() or 'você já enviou' in text.lower():
            return 'already_submitted'
        
        # Verificar exclusivo
        if 'projeto exclusivo' in text.lower() or 'freelancer premium' in text.lower():
            return 'exclusive'
        
        # Verificar concorrencia
        m = re.search(r'Propostas:\s*(\d+)', text)
        n_props = int(m.group(1)) if m else 0
        if n_props > 50:
            return 'high_competition'
        
        # Clicar Enviar Proposta (ignorar whitespace)
        btn = page.locator('button').filter(has_text='Enviar proposta').first
        if not btn.count():
            btn = page.locator('a').filter(has_text='Enviar proposta').first
        if not btn.count():
            return 'no_button'
        
        btn.click()
        time.sleep(4)
        
        # Preencher valor (baseado no tipo)
        precos = {'python-docx': '150', 'openpyxl': '120', 'script': '100', 'pymupdf': '80', 'gspread': '120'}
        valor = precos.get(tool, '100')
        prazo = '5'
        
        # Preencher campos
        inputs = page.locator('input').all()
        for inp in inputs:
            try:
                if inp.get_attribute('type') == 'number':
                    inp.click()
                    time.sleep(0.3)
                    page.keyboard.type(valor, delay=30)
            except:
                pass
        
        # Proposta
        template = TEMPLATES.get(tool, TEMPLATES['script'])
        proposta = template.format(valor=valor, prazo=prazo)
        
        ta = page.locator('textarea').first
        if ta.is_visible():
            ta.click()
            time.sleep(0.5)
            page.keyboard.type(proposta, delay=10)
        
        # Clicar Enviar
        enviar = page.locator('button:has-text("Enviar")').last
        if enviar.is_visible(timeout=3000):
            enviar.click()
            time.sleep(4)
            
            # Verificar sucesso
            text = page.inner_text('body')
            if 'proposta enviada' in text.lower() or 'sucesso' in text.lower():
                return 'submitted'
        
        return 'form_filled_not_sent'
        
    except Exception as e:
        return f'error: {str(e)[:100]}'


def _active_search(page):
    """Busca ativa de projetos por categorias e filtros."""
    projects = []
    categorias = [
        'https://www.99freelas.com.br/projects?category=suporte-administrativo',
        'https://www.99freelas.com.br/projects?category=escrita',
    ]
    
    for url in categorias:
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=20000)
            time.sleep(3)
            
            # Clicar "Menos de 24 horas" se visivel
            filtro = page.locator('text=Menos de 24 horas').first
            if filtro.count():
                filtro.click()
                time.sleep(2)
            
            # Extrair projetos da pagina
            links = page.locator('a[href*="/project/"]').all()
            seen = set()
            for link in links:
                try:
                    txt = link.inner_text().strip()
                    href = link.get_attribute('href') or ''
                    if len(txt) > 15 and '/project/' in href and href not in seen:
                        seen.add(href)
                        full_url = f"https://www.99freelas.com.br{href}" if href.startswith('/') else href
                        projects.append({'title': txt, 'url': full_url})
                except:
                    pass
        except Exception as e:
            print(f'  Erro busca categoria: {e}')
    
    return projects

def scan_and_submit():
    """Pipeline principal: escaneia projetos e submete propostas."""
    from playwright.sync_api import sync_playwright
    
    state = load_state()
    state['last_run'] = datetime.now().isoformat()
    
    # 1. Rodar IMAP agent para coletar projetos
    print('[1/3] Coletando projetos via IMAP...')
    import subprocess
    result = subprocess.run(['python3', str(HERMES / 'brain' / 'freelancer_agent.py')],
                          capture_output=True, text=True, timeout=60,
                          cwd=str(HERMES))
    
    # 2. Extrair projetos do output
    projects = []
    for line in result.stdout.split('\n'):
        if '•' in line and len(line) > 20:
            title = line.split('•')[-1].strip()
            projects.append({'title': title, 'source': 'imap_digest'})
    
    print(f'[1/3] {len(projects)} projetos encontrados')
    
    # 3. Classificar
    viable = []
    for p in projects:
        ok, tool = classify_project(p['title'])
        if ok:
            p['tool'] = tool
            viable.append(p)
    
    print(f'[2/3] {len(viable)} automatizaveis')
    
    if not viable:
        save_state(state)
        return
    
    # 4. Submeter via Playwright
    print('[3/3] Submetendo propostas...')
    
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            executable_path=BRAVE_BIN,
            headless=False,
            args=['--no-sandbox']
        )
        page = browser.new_page()
        page.goto('https://www.99freelas.com.br/dashboard', wait_until='domcontentloaded', timeout=30000)
        time.sleep(3)
        
        # Verificar login
        if 'login' in page.url.lower():
            print('[3/3] ❌ Sessao expirada - precisa re-login')
            state['errors'].append({'time': datetime.now().isoformat(), 'error': 'session_expired'})
            save_state(state)
            browser.close()
            return
        
        # Busca ativa + IMAP digests combinados
        page_projects = _active_search(page)
        print(f'  Busca ativa: {len(page_projects)} projetos')
        
        # Cruzar com viaveis do IMAP (digests)
        for v in viable:
            if v.get('url') and v['url'] not in [p['url'] for p in page_projects]:
                page_projects.append(v)
        
        # Cruzar com viaveis do IMAP
        submitted = 0
        for pp in page_projects[:20]:  # max 20
            # Pular ja submetidos
            if pp['url'] in state['submitted']:
                continue
            
            ok, tool = classify_project(pp['title'])
            if not ok:
                continue
            
            print(f"  Enviando: {pp['title'][:80]}...")
            result = submit_proposal(page, pp['url'], tool, pp['title'])
            print(f"  Resultado: {result}")
            
            if result == 'submitted':
                state['submitted'].append(pp['url'])
                submitted += 1
            elif result in ('exclusive', 'high_competition', 'already_submitted'):
                state['submitted'].append(pp['url'])  # nao tentar de novo
            
            if submitted >= 3:  # max 3 propostas por execucao
                break
        
        browser.close()
    
    print(f'[3/3] {submitted} propostas enviadas')
    save_state(state)

if __name__ == '__main__':
    scan_and_submit()
