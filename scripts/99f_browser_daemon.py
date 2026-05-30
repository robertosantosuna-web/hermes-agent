#!/usr/bin/env python3
"""
99FREELAS BROWSER DAEMON v2 — Motor Completo.
- Keep-alive 10min + auto-relogin Google OAuth
- Scan inteligente: classificação por nicho, detecção de exclusivos, preços dinâmicos
- Submissão ordenada por menor competição
- State management limpo (só salva submissões reais)
"""
import sys, time, json, re, subprocess
from pathlib import Path
from datetime import datetime, timezone

PROFILE_DIR = Path('/tmp/brave_hermes_99f')
BRAVE_BIN = '/opt/brave.com/brave/brave'
STATE_FILE = Path('/tmp/99f_daemon_state.json')
SUBMIT_STATE = Path('/tmp/freelancer_submitter_state.json')
KEEPALIVE_INTERVAL = 600  # 10 minutos
GOOGLE_EMAIL = 'robertosantos.una@gmail.com'
HERMES_DIR = Path.home() / '.hermes'

# ============================================================
# MOTOR DE CLASSIFICAÇÃO
# ============================================================
SKILL_KEYWORDS = {
    'ABNT/Word': ['abnt', 'tcc', 'monografia', 'formatação', 'formatar', 'normas', 'word',
                   'trabalho acadêmico', 'revisão', 'revisao', 'correção', 'correcao',
                   'dissertação', 'artigo cientifico', 'artigo científico', 'acadêmico', 'academico',
                   'dissertacao', 'tese', 'mestrado', 'doutorado'],
    'Excel': ['excel', 'planilha', 'dashboard', 'tabela', 'vba', 'macro', 'google sheets',
              'planilhas', 'gráfico', 'grafico', 'relatório', 'relatorio', 'planilha excel',
              'custo', 'controle financeiro', 'orcamento'],
    'Digitacao': ['digitar', 'digitação', 'digitacao', 'transcrever', 'transcrição',
                   'transcricao', 'texto para', 'audio para texto', 'copiar e colar'],
    'Cadastro': ['cadastr', 'cadastro', 'planilhar', 'catalogar', 'catalogaç',
                 'preencher planilha', 'preenchimento', 'alimentar', 'prospec',
                 'pesquisa online', 'organização de dados', 'organizacao de dados'],
    'PDF': ['pdf em word', 'converter pdf', 'pdf para word', 'editar pdf',
             'extrair pdf', 'conversão pdf', 'conversao pdf', 'pdf escaneado',
             'pdf interativo', 'pdf preenchivel'],
    'Automacao': ['python', 'script', 'automação', 'automacao', 'bot', 'scraping',
                  'raspagem', 'web scraping', 'selenium', 'playwright', 'proxy', 'prox',
                  'api', 'integração', 'integracao'],
    'PPT': ['powerpoint', 'apresentação', 'apresentacao', 'slides', 'ppt'],
}

PRICING = {
    'ABNT/Word': (100, 180),
    'Excel': (120, 200),
    'Digitacao': (60, 100),
    'Cadastro': (80, 130),
    'PDF': (60, 100),
    'Automacao': (150, 300),
    'PPT': (80, 150),
}


def save_state(status, url='', error=''):
    STATE_FILE.write_text(json.dumps({
        'status': status,
        'url': url[:120],
        'error': error,
        'last_check': datetime.now(timezone.utc).isoformat(),
        'pid': __import__('os').getpid()
    }))


def check_logged_in(page):
    try:
        page.goto('https://www.99freelas.com.br/dashboard',
                  wait_until='domcontentloaded', timeout=20000)
        time.sleep(3)
        url = page.url
        if 'login' in url.lower():
            return False, url
        if 'dashboard' in url.lower():
            return True, url
        text = page.inner_text('body')
        if 'Roberto' in text and ('freelancer' in text.lower() or 'projeto' in text.lower()):
            return True, url
        return False, url
    except Exception as e:
        return False, str(e)[:100]


def do_google_login(page):
    try:
        page.goto('https://www.99freelas.com.br/login',
                  wait_until='domcontentloaded', timeout=30000)
        time.sleep(4)
        url = page.url
        if 'accounts.google.com' in url:
            print('  Google OAuth detectado, preenchendo email...')
            email_input = page.locator('input[type="email"]')
            if email_input.count() > 0:
                email_input.first.click()
                time.sleep(0.5)
                page.keyboard.type(GOOGLE_EMAIL, delay=50)
                time.sleep(0.5)
                page.keyboard.press('Enter')
                time.sleep(5)
                text = page.inner_text('body')
                if 'senha' in text.lower() or 'password' in text.lower():
                    print('  Google pediu senha - precisa intervencao manual')
                    save_state('needs_password', page.url)
                    return False
                time.sleep(3)
                if '99freelas' in page.url.lower() or 'dashboard' in page.url.lower():
                    print('  Login OK!')
                    save_state('logged_in', page.url)
                    return True
        google_links = page.locator('a[href*="google"], a[href*="oauth"]').all()
        for link in google_links:
            href = link.get_attribute('href') or ''
            if 'accounts.google.com' in href:
                link.click()
                time.sleep(5)
                return do_google_login(page)
        print(f'  Fluxo Google OAuth nao encontrado. URL: {url[:100]}')
        return False
    except Exception as e:
        print(f'  Erro login: {e}')
        save_state('error', error=str(e)[:200])
        return False


# ============================================================
# MOTOR DE SCAN + CLASSIFICAÇÃO
# ============================================================

def classify_project(text):
    """Classifica por nicho com pontuação."""
    tl = text.lower()
    scores = {}
    for skill, keywords in SKILL_KEYWORDS.items():
        s = sum(1 for kw in keywords if kw in tl)
        if s > 0:
            scores[skill] = s
    return sorted(scores, key=lambda k: scores[k], reverse=True)


def is_exclusive(text):
    """Detecção robusta de projeto exclusivo."""
    tl = text.lower()
    if 'projeto exclusivo' in tl:
        return True
    if 'estará disponível para todos os profissionais' in tl:
        return True
    if 'seja um freelancer premium' in tl and 'envie proposta usando pontos' in tl:
        return True
    if re.search(r'estar[aá]\s+dispon[ií]vel\s+para\s+todos', tl):
        return True
    return False


def already_sent(text):
    return 'você já enviou' in text.lower() or 'proposta enviada' in text.lower()


def get_competitive_price(tipos, proposals, text, valor_minimo=0):
    """Preço de mercado competitivo: base por nicho → complexidade → desconto por competição (10-20%).

    Estratégia:
      1. Preço base pela tabela PRICING (faixa por nicho)
      2. Ajuste por complexidade (páginas, palavras, tradução, múltiplas skills)
      3. Desconto por competição:
         - 1-5 propostas:  -10% (pouca disputa, desconto leve)
         - 6-15 propostas: -15% (média)
         - 16-30 propostas: -20% (alta)
         - 31-50 propostas: -20% (muito alta)
      4. Garante acima do valor_minimo do cliente
      5. Arredonda múltiplo de 10

    A plataforma cobra 25% sobre a oferta (Oferta Final = Oferta × 1.25).
    Ex: ofertar R$80 → cliente vê R$100. Precificar pensando no valor final.
    """
    if not tipos:
        return max(80, valor_minimo + 10)

    primary = tipos[0]
    lo, hi = PRICING.get(primary, (80, 150))

    # --- FASE 1: Complexidade ---
    pages_m = re.search(r'(\d+)\s*(?:p[aá]ginas?|paginas?|pgs?)', text, re.IGNORECASE)
    words_m = re.search(r'(\d+)\s*(?:palavras|words)', text, re.IGNORECASE)

    if pages_m:
        pages = int(pages_m.group(1))
        if pages > 30:
            lo, hi = lo * 2, hi * 2
        elif pages > 15:
            lo = int(lo * 1.5)
            hi = int(hi * 1.5)

    if words_m:
        wc = int(words_m.group(1))
        if wc > 10000:
            lo, hi = lo * 2, hi * 2
        elif wc > 4000:
            lo = int(lo * 1.5)
            hi = int(hi * 1.5)

    # Tradução = premium
    if any(kw in text.lower() for kw in ['tradução', 'traducao', 'inglês', 'ingles',
                                            'english', 'translate', 'translation']):
        lo = int(lo * 1.5)
        hi = int(hi * 2)

    # Múltiplas skills
    if len(tipos) >= 3:
        lo = int(lo * 1.2)
        hi = int(hi * 1.3)

    # Preço base (média da faixa)
    market_price = (lo + hi) // 2

    # --- FASE 2: Desconto por competição ---
    if proposals <= 5:
        discount = 0.90      # -10%
    elif proposals <= 15:
        discount = 0.85      # -15%
    elif proposals <= 30:
        discount = 0.80      # -20%
    else:  # 31-50
        discount = 0.80      # -20%

    competitive = int(market_price * discount)

    # --- FASE 3: Piso (valor_minimo + margem) ---
    floor = max(valor_minimo + 20, 60)  # Pelo menos R$20 acima do mínimo
    competitive = max(competitive, floor)

    # --- FASE 4: Arredondar ---
    competitive = ((competitive + 5) // 10) * 10

    # Log para debug
    print(f'      💰 Base=R${market_price} | Desc={int((1-discount)*100)}% | '
          f'Min=R${valor_minimo} | Final=R${competitive}')

    return competitive


def extract_valor_minimo(text):
    """Extrai o valor mínimo definido pelo cliente no projeto."""
    m = re.search(r'Valor\s*(?:M[íi]nimo|Min[ií]mo)[:\s]*R?\$?\s*([\d.,]+)', text, re.IGNORECASE)
    if m:
        try:
            return int(float(m.group(1).replace('.', '').replace(',', '.')))
        except:
            pass
    return 0


def find_submit_button(page):
    """Encontra botão de enviar proposta com múltiplos padrões."""
    for pattern in ['Enviar proposta', 'Fazer proposta', 'Quero fazer proposta',
                     'ENVIAR PROPOSTA', 'FAZER PROPOSTA']:
        btn = page.locator('button, a').filter(has_text=pattern).first
        if btn.count():
            return btn
    # Busca genérica
    all_el = page.locator('button, a, [role="button"]').all()
    for el in all_el:
        try:
            txt = el.inner_text().strip().lower()
            if 'proposta' in txt and ('enviar' in txt or 'fazer' in txt or 'quero' in txt):
                return el
        except:
            pass
    return None


# ============================================================
# PIPELINE DE SUBMISSÃO
# ============================================================

def _run_submission_pipeline(page):
    """Scan inteligente + submissão ordenada por menor competição."""
    print('  [Scan] Buscando projetos...')

    # Carregar state
    state = {}
    if SUBMIT_STATE.exists():
        state = json.loads(SUBMIT_STATE.read_text())
    state.setdefault('submitted', [])

    # Navegar para projetos <24h
    page.goto('https://www.99freelas.com.br/projects',
              wait_until='domcontentloaded', timeout=25000)
    time.sleep(4)

    for filtro in ['Menos de 24 horas', 'Últimas 24h']:
        el = page.locator(f'text={filtro}').first
        if el.count():
            el.click()
            time.sleep(3)
            break

    # Scroll
    for i in range(12):
        page.keyboard.press('PageDown')
        time.sleep(0.6)

    # Extrair links deduplicados
    links_data = page.evaluate('''() => {
        const links = document.querySelectorAll('a[href*="/project/"]');
        const seen = new Set();
        const results = [];
        links.forEach(a => {
            const href = a.href || '';
            const m = href.match(/\\/project\\/([^/?]+)/);
            if (!m) return;
            const pid = m[1];
            if (seen.has(pid)) return;
            seen.add(pid);
            const title = a.innerText.trim();
            if (title.length > 10 && !title.includes('Publique um projeto')) {
                results.push({url: href, title: title.substring(0, 150)});
            }
        });
        return results;
    }''')

    print(f'  [Scan] {len(links_data)} projetos encontrados')

    # Analisar cada projeto
    candidates = []
    for proj in links_data[:25]:
        try:
            url = proj['url']
            page.goto(url, wait_until='domcontentloaded', timeout=20000)
            time.sleep(3)
            text = page.inner_text('body')

            if already_sent(text):
                continue
            if is_exclusive(text):
                continue
            if url in state['submitted']:
                continue

            prop_m = re.search(r'Propostas?[:\s]*(\d+)', text)
            proposals = int(prop_m.group(1)) if prop_m else 99

            if proposals > 50:
                continue

            tipos = classify_project(text)
            if not tipos:
                continue

            valor_minimo = extract_valor_minimo(text)
            has_button = find_submit_button(page) is not None
            price = get_competitive_price(tipos, proposals, text, valor_minimo)

            candidates.append({
                'url': url, 'title': proj['title'],
                'proposals': proposals, 'tipos': tipos,
                'has_button': has_button, 'price': price
            })

            stitle = proj['title'][:70].replace('\n', ' ').strip()
            print(f'    {stitle} → {tipos[:2]} prop={proposals} R${price} btn={has_button}')

        except Exception as e:
            print(f'    Erro scan: {e}')

    # Ordenar: menor competição primeiro
    candidates.sort(key=lambda c: (c['proposals'], -len(c['tipos'])))

    # Submeter (max 5 por ciclo, só com botão)
    submitted = 0
    max_submit = 5

    for c in candidates:
        if submitted >= max_submit:
            break
        if not c['has_button']:
            continue

        result = _try_submit(page, c['url'], c['title'], c['price'])
        stitle = c['title'][:60].replace('\n', ' ').strip()
        print(f'    R${c["price"]} | {stitle} → {result}')

        # SÓ salvar no state se realmente submeteu
        if result == 'submitted':
            state['submitted'].append(c['url'])
            submitted += 1
            SUBMIT_STATE.write_text(json.dumps(state, indent=2))
        elif result not in ('no_button', 'exclusive', 'high_competition', 'already_submitted'):
            # Erros recuperáveis: marcar pra não repetir neste ciclo
            state['submitted'].append(c['url'])
            SUBMIT_STATE.write_text(json.dumps(state, indent=2))

    state['last_run'] = datetime.now(timezone.utc).isoformat()
    SUBMIT_STATE.write_text(json.dumps(state, indent=2))
    print(f'  [Scan] {submitted} propostas enviadas | {len(candidates)} candidatos analisados')


def _try_submit(page, project_url, title, price):
    """Submete proposta com preço inteligente."""
    try:
        page.goto(project_url, wait_until='domcontentloaded', timeout=20000)
        time.sleep(4)

        text = page.inner_text('body')

        # Verificações
        if is_exclusive(text):
            return 'exclusive'
        if already_sent(text):
            return 'already_submitted'

        prop_m = re.search(r'Propostas?[:\s]*(\d+)', text)
        if prop_m and int(prop_m.group(1)) > 50:
            return 'high_competition'

        btn = find_submit_button(page)
        if not btn:
            return 'no_button'

        btn.click()
        time.sleep(4)

        # Preencher valor
        try:
            for inp in page.locator('input').all():
                try:
                    attrs = (inp.get_attribute('name') or '') + (inp.get_attribute('placeholder') or '')
                    if any(kw in attrs.lower() for kw in ['valor', 'preço', 'preco', 'orçamento', 'orcamento']):
                        inp.click()
                        time.sleep(0.2)
                        inp.fill('')
                        page.keyboard.type(str(price), delay=50)
                        break
                except:
                    pass
        except:
            pass

        # Prazo
        try:
            for inp in page.locator('input').all():
                try:
                    attrs = (inp.get_attribute('name') or '') + (inp.get_attribute('placeholder') or '')
                    if any(kw in attrs.lower() for kw in ['prazo', 'dias', 'entrega']):
                        inp.click()
                        time.sleep(0.2)
                        page.keyboard.type('3', delay=50)
                        break
                except:
                    pass
        except:
            pass

        # Mensagem
        msg = (f"Ola, tenho experiencia comprovada nesse tipo de trabalho. "
               f"Entrego com qualidade e dentro do prazo.\n\n"
               f"Valor: R${price}. Prazo: 2-3 dias uteis.\n\n"
               f"Disponivel para iniciar imediatamente.\n\nRoberto")

        for ta in page.locator('textarea').all():
            try:
                if ta.is_visible():
                    ta.click()
                    time.sleep(0.3)
                    page.keyboard.type(msg, delay=3)
                    break
            except:
                continue

        time.sleep(1)

        # Enviar
        for pattern in ['Enviar', 'ENVIAR', 'Confirmar', 'CONFIRMAR']:
            send = page.locator('button').filter(has_text=pattern).last
            if send.count():
                send.click()
                time.sleep(5)
                break

        after = page.inner_text('body')
        if 'proposta enviada' in after.lower() or 'enviada com sucesso' in after.lower():
            return 'submitted'
        if 'obrigado' in after.lower() and 'proposta' in after.lower():
            return 'submitted'

        return 'sent_uncertain'

    except Exception as e:
        return f'error: {str(e)[:80]}'


# ============================================================
# LOOP PRINCIPAL
# ============================================================

def main():
    from playwright.sync_api import sync_playwright

    print(f'🚀 99Freelas Daemon v2 (PID {__import__("os").getpid()})')
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

            logged_in, url = check_logged_in(page)
            print(f'Estado inicial: {"logado" if logged_in else "deslogado"} ({url[:80]})')

            if not logged_in:
                print('Tentando login...')
                logged_in = do_google_login(page)

            if not logged_in:
                save_state('needs_manual_login')
                print('❌ Login falhou - aguardando intervencao manual')
            else:
                save_state('running', url)

            submission_counter = 0
            while True:
                time.sleep(KEEPALIVE_INTERVAL)

                try:
                    logged_in, url = check_logged_in(page)

                    if logged_in:
                        save_state('running', url)
                        ts = datetime.now().strftime('%H:%M')
                        print(f'[{ts}] ✅ Sessao ativa')

                        submission_counter += 1
                        if submission_counter >= 12:  # 2h
                            submission_counter = 0
                            print(f'[{ts}] 🔍 Pipeline de submissao...')
                            _run_submission_pipeline(page)
                    else:
                        ts = datetime.now().strftime('%H:%M')
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
