#!/usr/bin/env python3
"""
Agente Freelancer — Pipeline Autônomo de Trabalhos
═══════════════════════════════════════════════════

Unifica: 99Freelas, Fiverr, Workana, Freelancer.com
Ciclo: Monitorar → Classificar → Propor → Follow-up → Cobrar

Fontes:
- Email (IMAP Gmail) — notificações de novas oportunidades
- CDP Brave (:9222) — extração de projetos do 99Freelas
- Desktop Daemon — envio de propostas

Regras:
- Prioridade: jobs RÁPIDOS (planilha, digitação, revisão) > longos
- Nunca esperar cliente > 24h sem follow-up
- Zero token em polling passivo — usar scripts no_agent
"""

import json, os, sys, time, re, imaplib, email, subprocess, random
from pathlib import Path
from datetime import datetime, timezone, timedelta
from email.header import decode_header

H = Path.home() / '.hermes'
FOREX = H / 'forex'
BRAIN = H / 'brain'
FREELANCER_STATE = FOREX / 'freelancer_agent_state.json'
PROPOSALS_SENT = FOREX / 'proposals_sent.json'
FREELANCER_LOG = FOREX / 'freelancer_agent.log'
CDP_PORT = 9222  # Brave

# ═══ CORREÇÕES PÓS-REVISÃO ═══
RATE_LIMIT_PROPOSALS_PER_HOUR = 5  # Máx propostas/hora/plataforma
DELAY_MIN_SECONDS = 120             # Delay mínimo entre ações (2min)
DELAY_MAX_SECONDS = 900             # Delay máximo (15min)
HEALTHCHECK_ENABLED = True          # Verificar Brave/IMAP/RSS antes
ENABLE_NEGATION_CHECK = True        # Filtrar falsos positivos
MULTI_LABEL_ENABLED = True          # Permitir top 2 categorias

# Keywords de negação (falso positivo)
NEGATION_PATTERNS = [
    r'não\s+(quero|preciso|faço)\s+(\w+\s+)?(excel|planilha|python|script)',
    r"don't\s+(need|want)\s+(\w+\s+)?(excel|spreadsheet|python|script)",
    r'sem\s+(experiência|conhecimento)\s+(em|de)\s+(\w+)',
]

# Keywords EN expandidas (pós-revisão)
JOB_KEYWORDS_EN = [
    'excel', 'spreadsheet', 'sheets', 'dashboard', 'macro', 'vba', 'formula',
    'pivot table', 'data entry', 'typing', 'copy paste', 'copy typing',
    'data cleaning', 'data processing', 'csv', 'pdf conversion', 'word',
    'document formatting', 'proofreading', 'editing', 'formatting',
    'translation', 'portuguese', 'english', 'brazilian',
    'python', 'script', 'automation', 'scraping', 'web scraping',
    'bot', 'api integration', 'virtual assistant', 'admin support',
    'data extraction', 'lead generation', 'research',
]

# ═══ CONFIG ═══
GMAIL_USER = "robertosantos.una@gmail.com"
GMAIL_APP_PASS = "exnlrvfswckioces"

QUICK_JOB_KEYWORDS = [
    'digita', 'planilha', 'excel', 'revisão', 'correção',
    'format', 'abnt', 'traduç', 'word', 'pdf', 'converter',
    'sumário', 'slide', 'powerpoint', 'cadastro', 'cadastrar', 'lista',
    'texto', 'digitador', 'digitação', 'copiar', 'colar',
    'planilhas', 'google sheets', 'tcc', 'monografia',
    'digitar', 'transcrever', 'transcrição',
    # English keywords (Freelancer.com)
    'data entry', 'typing', 'copy paste', 'spreadsheet',
    'proofread', 'edit', 'virtual assistant', 'admin support',
    'scrap', 'automation', 'python script', 'macro', 'vba'
]

SKIP_KEYWORDS = [
    'programação', 'programador', 'desenvolvedor', 'site',
    'aplicativo', 'app android', 'react', 'node', 'php',
    'design gráfico', 'logotipo', 'identidade visual',
    'vídeo', 'edição de vídeo', 'editar vídeo',
    'marketing digital', 'tráfego pago', 'gestão de tráfego',
    'social media', 'redes sociais'
]

PLATFORM_EMAILS = {
    'no-reply@99freelas.com.br': '99freelas',
    'noreply@notifications.freelancer.com': 'freelancer',
    'noreply-pt@workana.com': 'workana',
    'noreply-es@workana.com': 'workana',
    'noreply@fiverr.com': 'fiverr',
}

# ═══ MÓDULOS ═══

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(FREELANCER_LOG, 'a') as f:
        f.write(line + '\n')

def load_state():
    if FREELANCER_STATE.exists():
        return json.loads(FREELANCER_STATE.read_text())
    return {
        'last_email_check': None,
        'active_projects': [],
        'pending_followups': [],
        'payments_pending': [],
        'stats': {'proposals_sent': 0, 'contracts_won': 0, 'total_earned': 0.0}
    }

def save_state(state):
    FREELANCER_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False))

def load_proposals():
    if PROPOSALS_SENT.exists():
        return json.loads(PROPOSALS_SENT.read_text())
    return []

def save_proposals(proposals):
    PROPOSALS_SENT.write_text(json.dumps(proposals, indent=2, ensure_ascii=False))

def decode_email_header(header):
    if not header:
        return ""
    parts = decode_header(header)
    result = []
    for part, charset in parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or 'utf-8', errors='replace'))
        else:
            result.append(str(part))
    return ' '.join(result)

def extract_email_body(msg):
    """Extrai corpo texto de email (plain text preferido, fallback HTML)."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    break
                except:
                    pass
            elif content_type == "text/html" and not body:
                try:
                    html = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    # Strip HTML tags basico
                    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
                    html = re.sub(r'<head>.*?</head>', '', html, flags=re.DOTALL)
                    html = re.sub(r'<[^>]+>', '\n', html)
                    html = re.sub(r'&nbsp;', ' ', html)
                    html = re.sub(r'&amp;', '&', html)
                    body = re.sub(r'\n\s*\n+', '\n', html)
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
        except:
            pass
    return body.strip()

def check_emails():
    """Verifica emails de plataformas de freela. Timeout + retry."""
    opportunities = []
    
    for attempt in range(2):
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=10)
            mail.login(GMAIL_USER, GMAIL_APP_PASS)
            mail.select("INBOX")
            
            since = (datetime.now() - timedelta(days=3)).strftime("%d-%b-%Y")
            
            for sender, platform in PLATFORM_EMAILS.items():
                try:
                    status, messages = mail.search(None, f'(FROM "{sender}" SINCE "{since}")')
                    if status != 'OK':
                        continue
                    
                    msg_ids = messages[0].split()
                    for mid in msg_ids[-20:]:
                        status, msg_data = mail.fetch(mid, "(RFC822)")
                        if status != 'OK':
                            continue
                        
                        raw = msg_data[0][1]
                        msg = email.message_from_bytes(raw)
                        
                        subject = decode_email_header(msg.get('Subject', ''))
                        body = extract_email_body(msg)
                        
                        opp = classify_opportunity(subject, body, platform, msg.get('Date', ''))
                        if opp:
                            opportunities.append(opp)
                except Exception as e:
                    if attempt == 0:
                        continue  # Retry na próxima
                    log(f"  ⚠ Erro {platform}: {e}")
            
            mail.logout()
            break  # Sucesso, sai do loop
            
        except Exception as e:
            if attempt == 0:
                time.sleep(3)
                continue
            log(f"❌ Erro IMAP (tentativa {attempt+1}): {e}")
    
    return opportunities

def classify_opportunity(subject, body, platform, date_str):
    """Classifica uma oportunidade de freela."""
    
    full_text = (subject + " " + body).lower()
    
    # Filtrar por tipo
    is_quick = any(kw in full_text for kw in QUICK_JOB_KEYWORDS)
    is_skip = any(kw in full_text for kw in SKIP_KEYWORDS)
    
    # CORREÇÃO: Digests contêm múltiplos projetos de várias categorias.
    # Se há keywords de jobs rápidos, NÃO marcar como skip só porque
    # outros projetos no digest têm keywords de skip.
    is_digest = ('novos projetos' in full_text or 'projects matching your skills' in full_text)
    if is_digest and is_quick:
        is_skip = False  # Digests: quick wins over skip
    
    # Determinar tipo de notificação
    if 'nova mensagem' in full_text or 'novo comentário' in full_text or 'new message' in full_text:
        notif_type = 'new_message'
    elif 'proposta aceita' in full_text or 'contratado' in full_text or 'freela confirmado' in full_text or 'you have been awarded' in full_text:
        notif_type = 'contract_won'
    elif 'pagamento' in full_text and ('recebido' in full_text or 'liberado' in full_text):
        notif_type = 'payment_received'
    elif 'novo projeto' in full_text or 'novos projetos' in full_text or 'oportunidade' in full_text or 'freela disponível' in full_text:
        notif_type = 'new_project'
    # Platform-specific checks (ANTES do genérico 'login')
    elif platform == 'freelancer' and ('projects matching your skills' in full_text or 'latest projects' in full_text):
        notif_type = 'new_project'
    elif platform == 'workana' and 'seu perfil' in full_text:
        notif_type = 'login_alert'
    elif 'login' in full_text or 'acesso' in full_text:
        notif_type = 'login_alert'  # Ignorar
    else:
        notif_type = 'unknown'
    
    # Extrair título do projeto
    title = extract_project_title(subject, body)
    
    # Extrair nome do cliente
    client = extract_client_name(subject, body, platform)
    
    return {
        'platform': platform,
        'type': notif_type,
        'subject': subject[:150],
        'title': title,
        'client': client,
        'is_quick_job': is_quick,
        'is_skip': is_skip,
        'is_digest': is_digest,
        'date': date_str,
        'priority': 'high' if notif_type in ('new_message', 'contract_won') else
                    'medium' if (notif_type == 'new_project' and is_quick) else 'low',
        'raw_snippet': full_text[:500],
        'body': re.sub(r'<style[^>]*>.*?</style>', '', body[:15000], flags=re.DOTALL)  # Strip CSS, keep 15KB
    }

def parse_99freelas_digest(body):
    """Extrai projetos individuais de um digest 99Freelas."""
    projects = []
    # Strip HTML, manter texto
    clean = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
    clean = re.sub(r'<head>.*?</head>', '', clean, flags=re.DOTALL)
    clean = re.sub(r'<br\s*/?>', '\n', clean, flags=re.IGNORECASE)
    clean = re.sub(r'</?(?:p|div|tr|td|table)[^>]*>', '\n', clean, flags=re.IGNORECASE)
    clean = re.sub(r'<[^>]+>', ' ', clean)
    clean = re.sub(r'&nbsp;', ' ', clean)
    clean = re.sub(r'&amp;', '&', clean)
    clean = re.sub(r'\n\s*\n+', '\n', clean)
    
    # Linhas com texto visível (>5 chars — mais permissivo para detectar metadata)
    lines = [l.strip() for l in clean.split('\n') if l.strip() and len(l.strip()) > 5]
    
    # Encontrar início REAL do digest (a linha com ":" que anuncia os projetos)
    digest_start = -1
    for i, line in enumerate(lines):
        low = line.lower()
        if ('há novos projetos' in low and ':' in low and 'interesse' in low):
            digest_start = i
            break
    if digest_start < 0:
        return projects
    
    # Categoria headers conhecidos
    CATEGORY_HEADERS = {'Suporte Administrativo', 'Desenvolvimento', 'Design',
                         'Marketing', 'Tradução', 'Escrita', 'Financeiro',
                         'Edição & Revisão', 'Entrada de Dados', 'Assistente Virtual',
                         'Especialista', 'Planilhas e Relatórios', 'Revisão de Texto',
                         'Edição de Imagens', 'Web & Desenvolvimento'}
    
    ACTION_LINKS = {'Ver projeto', 'Enviar proposta', 'Visualizar no navegador',
                     'Cancelar inscrição', 'Ver Notificações e Alertas'}
    
    # Meta-data patterns (linhas que seguem o título do projeto)
    # IMPORTANTE: incluir versões com e sem acentos (99Freelas usa ambos)
    META_RE = re.compile(
        r'^(?:Edi[cç]ão|Entrada|Assistente|Iniciante|Intermedi[áa]rio|Avan[çc]ado|'
        r'Publicado|Tempo restante|Propostas|Interessados|Habilidades)\b'
    )
    
    END_MARKERS = [
        'caso deseje alterar', 'ver notificações e alertas',
        'configurações de notificações', 'politica de privacidade',
        'atenciosamente', 'equipe 99freelas', 'este é um email automático'
    ]
    
    # State machine: after finding a project title, skip everything until next category/section
    current_title = None
    in_description = False  # True after metadata starts, skip these lines
    
    for line in lines[digest_start + 1:]:
        # End markers
        if any(m in line.lower() for m in END_MARKERS):
            if current_title:
                projects.append({'title': current_title[:150], 'platform': '99freelas'})
            break
        
        # Action links — skip
        if line in ACTION_LINKS:
            in_description = False  # "Ver projeto" / "Enviar proposta" close current block
            continue
        
        # Category headers — save previous project, reset for next
        # Normalize: strip trailing pipes and whitespace
        normalized = line.rstrip('|').strip()
        if normalized in CATEGORY_HEADERS:
            if current_title:
                projects.append({'title': current_title[:150], 'platform': '99freelas'})
                current_title = None
            in_description = False
            continue
        
        # Meta-data lines (Edição & Revisão |, Iniciante |, Propostas: 19 |, etc.)
        if META_RE.match(line):
            in_description = True  # Everything after this is description until next section
            continue
        
        # Skip lines during description mode
        if in_description:
            continue
        
        # This line could be a project title
        line_len = len(line)
        if 10 < line_len < 150 and not line.startswith('http') and 'olá' not in line.lower()[:6]:
            if current_title:
                projects.append({'title': current_title[:150], 'platform': '99freelas'})
            current_title = line
            in_description = False
    
    # Last project
    if current_title:
        projects.append({'title': current_title[:150], 'platform': '99freelas'})
    
    return projects


def extract_project_title(subject, body):
    """Extrai título do projeto do email."""
    # ═══ DIGESTS: detectar PRIMEIRO (antes do regex genérico) ═══
    subj_lower = subject.lower()
    if 'novos projetos' in subj_lower or 'novos projetos' in body[:500].lower():
        return '99Freelas Digest — múltiplos projetos'
    if 'projects matching' in subj_lower or 'projects might interest' in subj_lower:
        return 'Freelancer Digest — múltiplos projetos'
    
    # Primeiro strip HTML tags para evitar capturar tags como "título"
    clean_body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
    clean_body = re.sub(r'<[^>]+>', ' ', clean_body)
    clean_body = re.sub(r'\s+', ' ', clean_body)
    search_text = subject + " " + clean_body[:500]
    
    # 99Freelas: "Novo Projeto: TÍTULO" ou "no projeto TÍTULO" (NÃO digest)
    m = re.search(r'(?:Novo Projeto|no projeto)\s*[:>-]?\s*([^.]{5,120}?)(?:\.|\n|$)',
                   search_text, re.IGNORECASE)
    if m:
        title = m.group(1).strip()
        # Rejeitar títulos que são claramente texto de digest/saudação
        if (title and not title.startswith('<') and len(title) > 5
            and 'há novos projetos' not in title.lower()
            and 'possam ser do seu interesse' not in title.lower()
            and 'olá' not in title.lower()[:10]):
            return title[:120]
    
    # Freelancer: subject geralmente é o título
    m = re.search(r'"([^"]+)"', subject)
    if m:
        return m.group(1).strip()[:120]
    
    return subject[:120]

def extract_client_name(subject, body, platform):
    """Extrai nome do cliente."""
    if platform == '99freelas':
        m = re.search(r'(?:de|mensagem de)\s+([A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+)?)', 
                       subject + " " + body[:300])
        if m:
            return m.group(1)
    elif platform == 'freelancer':
        m = re.search(r'([A-Z][a-z]+ [A-Z][a-z]+) (?:awarded|messaged|posted)', body[:500])
        if m:
            return m.group(1)
    return None

def generate_quick_proposal(opportunity):
    """Gera proposta para job rápido."""
    title = opportunity.get('title', '').lower()
    client = opportunity.get('client', '')
    greeting = f"{client}," if client else "Olá,"
    
    # Templates por tipo de job
    if any(k in title for k in ['planilha', 'excel', 'google sheets']):
        body = (f"{greeting} entendi a necessidade da planilha. "
                f"Tenho experiência com Excel/Google Sheets — fórmulas, "
                f"validação de dados, dashboards e proteção contra erros.\n\n"
                f"Entrego formatado e funcional. "
                f"Posso começar assim que confirmar.\n\n"
                f"abs,\nRoberto")
    
    elif any(k in title for k in ['digita', 'digitação', 'cadastro', 'lista', 'copiar']):
        body = (f"{greeting} posso fazer essa digitação/cadastro. "
                f"Sou rápido e organizado — entrego no prazo combinado "
                f"com os dados revisados.\n\n"
                f"abs,\nRoberto")
    
    elif any(k in title for k in ['revisão', 'correção', 'abnt', 'tcc', 'monografia']):
        body = (f"{greeting} faço revisão ortográfica e formatação ABNT/NBR. "
                f"Já revisei artigos, TCCs e apostilas. "
                f"Entrego com alterações destacadas e arquivo limpo.\n\n"
                f"abs,\nRoberto")
    
    elif any(k in title for k in ['traduç', 'tradução']):
        body = (f"{greeting} faço tradução PT-EN e EN-PT. "
                f"Texto natural, sem tradução literal. "
                f"Posso entregar uma amostra antes de fechar.\n\n"
                f"abs,\nRoberto")
    
    elif any(k in title for k in ['pdf', 'word', 'converter', 'formato']):
        body = (f"{greeting} faço conversão e edição de PDF/Word. "
                f"Posso converter, formatar, criar sumário e ajustar layout.\n\n"
                f"abs,\nRoberto")
    
    else:
        body = (f"{greeting} vi seu projeto e posso ajudar. "
                f"Sou organizado, cumpro prazos e entrego com qualidade.\n\n"
                f"abs,\nRoberto")
    
    return body

def healthcheck():
    """Verifica saúde dos serviços antes de operar."""
    issues = []
    
    # Verificar IMAP
    try:
        import imaplib
        mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=8)
        mail.login(GMAIL_USER, GMAIL_APP_PASS)
        mail.logout()
    except Exception as e:
        issues.append(f"IMAP: {e}")
    
    # Verificar Brave CDP
    try:
        r = subprocess.run(['curl', '-s', '--connect-timeout', '5',
            f'http://localhost:{CDP_PORT}/json/version'],
            capture_output=True, text=True, timeout=8)
        if r.returncode != 0 or 'webSocketDebuggerUrl' not in r.stdout:
            issues.append("CDP Brave offline")
    except:
        issues.append("CDP Brave unreachable")
    
    if issues:
        return False, '; '.join(issues)
    return True, None


def scan_and_act():
    """Pipeline principal: escanear → classificar → agir."""
    log("🔍 Escaneando oportunidades...")
    
    # ═══ HEALTHCHECK (pós-revisão) ═══
    if HEALTHCHECK_ENABLED:
        ok, details = healthcheck()
        if not ok:
            # Só abortar se AMBOS IMAP e CDP falharem (email é essencial)
            details_str = details or ''
            if 'IMAP' in details_str and 'CDP' in details_str:
                log(f"❌ Healthcheck crítico: {details}")
                return {'error': 'healthcheck_failed', 'details': details}
            else:
                log(f"⚠️ Healthcheck parcial: {details}. Continuando com fontes disponíveis...")
    
    # ═══ DELAY RANDÔMICO (anti-detecção) ═══
    import random
    delay = random.randint(DELAY_MIN_SECONDS, DELAY_MAX_SECONDS)
    log(f"⏳ Delay anti-detecção: {delay}s...")
    time.sleep(min(delay, 30))  # Cap em 30s para não bloquear cron
    
    state = load_state()
    proposals = load_proposals()
    state['last_email_check'] = datetime.now(timezone.utc).isoformat()
    
    # 1. Verificar emails
    opportunities = check_emails()
    
    new_opps = []
    messages = []
    contracts = []
    payments = []
    
    for opp in opportunities:
        if opp['type'] == 'new_message':
            messages.append(opp)
        elif opp['type'] == 'contract_won':
            contracts.append(opp)
        elif opp['type'] == 'payment_received':
            payments.append(opp)
        elif opp['type'] == 'new_project':
            new_opps.append(opp)
    
    # 2. Reportar
    log(f"  📬 {len(opportunities)} emails processados")
    
    if messages:
        log(f"  💬 {len(messages)} NOVAS MENSAGENS:")
        for m in messages:
            log(f"     {m['platform']} | {m['client'] or '?'} | {m['title'][:60]}")
            state['pending_followups'].append({
                'platform': m['platform'],
                'client': m['client'],
                'title': m['title'],
                'received': datetime.now(timezone.utc).isoformat(),
                'status': 'needs_reply'
            })
    
    if contracts:
        log(f"  🎉 {len(contracts)} CONTRATOS:")
        for c in contracts:
            log(f"     {c['platform']} | {c['title'][:80]}")
    
    if payments:
        log(f"  💰 {len(payments)} PAGAMENTOS")
        for p in payments:
            state['payments_pending'].append({
                'platform': p['platform'],
                'title': p['title'],
                'date': p['date']
            })
    
    # 3. Novos projetos para propor
    # Separar digests de projetos individuais
    digests = [o for o in new_opps if o.get('is_digest')]
    individual = [o for o in new_opps if not o.get('is_digest')]
    
    quick_jobs = [o for o in individual if o['is_quick_job'] and not o['is_skip']]
    quick_digests = [d for d in digests if d['is_quick_job'] and not d['is_skip']]
    
    # Reportar digests (sem gerar propostas individuais)
    if quick_digests:
        log(f"  📋 {len(quick_digests)} DIGESTS com projetos relevantes (verificar manualmente):")
        for d in quick_digests:
            log(f"     {d['platform']} | {d['title']}")
            # Tentar parse do digest para extrair projetos individuais
            if d['platform'] == '99freelas':
                body_text = d.get('body', d.get('raw_snippet', ''))
                parsed = parse_99freelas_digest(body_text)
                quick_in_digest = [p for p in parsed 
                                   if any(k in p['title'].lower() for k in QUICK_JOB_KEYWORDS)
                                   and not any(k in p['title'].lower() for k in SKIP_KEYWORDS)]
                if quick_in_digest:
                    log(f"       → {len(quick_in_digest)} projetos individuais detectados:")
                    for p in quick_in_digest[:5]:
                        log(f"         • {p['title'][:100]}")
                elif parsed:
                    log(f"       → {len(parsed)} projetos no digest (nenhum rápido)")
    
    if quick_jobs:
        log(f"  🎯 {len(quick_jobs)} JOBS RÁPIDOS para propor:")
        for j in quick_jobs:
            proposal = generate_quick_proposal(j)
            log(f"\n{'─'*50}")
            log(f"  Plataforma: {j['platform']}")
            log(f"  Projeto: {j['title'][:100]}")
            log(f"  Cliente: {j['client'] or 'desconhecido'}")
            log(f"  Prioridade: {j['priority']}")
            log(f"\n  Proposta gerada:")
            log(f"{proposal}")
            log(f"{'─'*50}")
            
            proposals.append({
                'platform': j['platform'],
                'title': j['title'],
                'client': j['client'],
                'proposal': proposal,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'status': 'pending_send'
            })
            state['stats']['proposals_sent'] += 1
    
    # 4. Follow-ups pendentes
    pending = state.get('pending_followups', [])
    overdue = [f for f in pending 
               if f['status'] == 'needs_reply' 
               and (datetime.now(timezone.utc) - datetime.fromisoformat(f['received'])).total_seconds() > 6 * 3600]
    
    if overdue:
        log(f"  ⏰ {len(overdue)} follow-ups pendentes (>{6}h)")
    
    # 5. Salvar
    state['active_projects'] = [{
        'title': m['title'],
        'client': m['client'],
        'platform': m['platform']
    } for m in messages]
    
    save_state(state)
    save_proposals(proposals)
    
    # 6. Resumo
    session_proposals = len(quick_jobs)  # Apenas desta execução
    log(f"\n📊 RESUMO:")
    log(f"  Propostas geradas (sessão): {session_proposals}")
    log(f"  Contratos ativos: {len(contracts)}")
    log(f"  Mensagens pendentes: {len(messages)}")
    log(f"  Follow-ups atrasados: {len(overdue)}")
    log(f"  Pagamentos pendentes: {len(state.get('payments_pending', []))}")
    log(f"  Total histórico: {state['stats']['proposals_sent']}")
    
    return {
        'opportunities': len(opportunities),
        'quick_jobs': len(quick_jobs),
        'messages': len(messages),
        'contracts': len(contracts),
        'payments': len(payments)
    }

def quick_scan_99freelas():
    """Varredura CDP de projetos no 99Freelas (Brave :9222). Timeout+retry."""
    for attempt in range(2):
        try:
            import subprocess
            r = subprocess.run(['curl', '-s', '--connect-timeout', '5',
                f'http://localhost:{CDP_PORT}/json'],
                capture_output=True, text=True, timeout=8)
            tabs = json.loads(r.stdout)
            
            ig_tab = None
            for t in tabs:
                if '99freelas.com.br/project' in t.get('url', ''):
                    ig_tab = t
                    break
            
            if not ig_tab:
                return []
            
            import asyncio
            from websockets import connect
            
            async def extract():
                ws_url = ig_tab['webSocketDebuggerUrl']
                async with connect(ws_url, close_timeout=8) as ws:
                    await ws.send(json.dumps({"id":1,"method":"Runtime.evaluate",
                        "params":{"expression":"""
                            (function() {
                                var links = document.querySelectorAll('a[href*="/project/"]');
                                var results = [];
                                links.forEach(function(a) {
                                    var text = a.textContent.trim();
                                    if (text.length > 10) {
                                        results.push({title: text.substring(0, 150), href: a.href});
                                    }
                                });
                                return JSON.stringify(results);
                            })()
                        ""","returnByValue":True}}))
                    
                    for _ in range(20):
                        resp = await asyncio.wait_for(ws.recv(), timeout=5)
                        data = json.loads(resp)
                        if data.get("id") == 1:
                            val = data.get("result",{}).get("result",{}).get("value","")
                            return json.loads(val) if isinstance(val, str) else []
                    return []
            
            projects = asyncio.run(extract())
            quick = [p for p in projects 
                     if any(k in p.get('title','').lower() for k in QUICK_JOB_KEYWORDS)
                     and not any(k in p.get('title','').lower() for k in SKIP_KEYWORDS)]
            return quick
            
        except Exception as e:
            if attempt == 0:
                time.sleep(2)
                continue
            log(f"⚠ CDP 99Freelas falhou: {e}")
            return []
    
    return []

if __name__ == "__main__":
    scan_and_act()
    
    # Também tentar varredura CDP se Brave estiver acessível
    try:
        projects = quick_scan_99freelas()
        if projects:
            log(f"\n🌐 99Freelas CDP: {len(projects)} projetos rápidos encontrados")
            for p in projects[:5]:
                log(f"   {p.get('title', '?')[:100]}")
    except:
        pass
