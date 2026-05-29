#!/usr/bin/env python3
"""
Sub-Agente: Freelancer.com
═══════════════════════════════════
Prioridade #1 segundo 3 especialistas.

Funções:
- Verificar telefone (bloqueio crítico)
- Monitor RSS feed de novos projetos
- Filtrar por keywords: Excel, Python, Data Entry, PDF, scraping
- Alertar via Tálamo quando job compatível aparece
- Gerar template de proposta em inglês
"""

import json, os, sys, time, re, subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET
from urllib.request import urlopen, Request
from urllib.error import URLError

H = Path.home() / '.hermes'
FOREX = H / 'forex'
FREELANCER_STATE = FOREX / 'freelancer_state.json'
FREELANCER_JOBS = FOREX / 'freelancer_jobs.json'
FREELANCER_LOG = FOREX / 'freelancer_agent.log'

# ═══ CONFIG ═══
RSS_FEEDS = [
    "https://www.freelancer.com/rss.xml",
]

JOB_KEYWORDS = [
    'excel', 'spreadsheet', 'data entry', 'typing', 'copy paste',
    'pdf', 'word', 'virtual assistant', 'admin', 'python script',
    'data scraping', 'web scraping', 'csv', 'google sheets',
    'formatting', 'proofreading', 'translation', 'portuguese',
    'data cleaning', 'automation', 'macro', 'vba'
]

SKIP_KEYWORDS = [
    'web development', 'app development', 'website design',
    'logo design', 'graphic design', 'video editing', 'animation',
    'marketing', 'seo', 'social media manager', 'blockchain',
    'machine learning', 'ai model', 'deep learning'
]

MIN_BUDGET_USD = 10   # Ignorar jobs abaixo disso
MAX_PROPOSALS = 15    # Ignorar jobs com muitas propostas (muita concorrência)

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    with open(FREELANCER_LOG, 'a') as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def load_state():
    if FREELANCER_STATE.exists():
        return json.loads(FREELANCER_STATE.read_text())
    return {
        'seen_job_ids': [],
        'last_scan': None,
        'total_scanned': 0,
        'matches_found': 0,
        'phone_verified': False,
        'verified_badge': False
    }

def save_state(state):
    FREELANCER_STATE.write_text(json.dumps(state, indent=2))

def load_jobs():
    if FREELANCER_JOBS.exists():
        return json.loads(FREELANCER_JOBS.read_text())
    return []

def save_jobs(jobs):
    FREELANCER_JOBS.write_text(json.dumps(jobs, indent=2, ensure_ascii=False))

def fetch_rss(url):
    """Busca feed RSS do Freelancer com timeout+retry."""
    for attempt in range(2):
        try:
            req = Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            })
            with urlopen(req, timeout=15) as resp:
                return resp.read()
        except Exception as e:
            if attempt == 0:
                time.sleep(3)
            else:
                log(f"⚠ RSS {url[-5:]}: {e}")
    return None

def parse_freelancer_rss(xml_data):
    """Parse do feed RSS do Freelancer.com."""
    jobs = []
    try:
        root = ET.fromstring(xml_data)
        for item in root.findall('.//item'):
            title = item.findtext('title', '')
            link = item.findtext('link', '')
            desc = item.findtext('description', '')
            pubdate = item.findtext('pubDate', '')
            
            # Extrair budget do título (ex: "$30 - $250")
            budget_match = re.search(r'\$[\d,]+', title)
            budget = budget_match.group(0) if budget_match else None
            
            # Extrair número de propostas
            proposals_match = re.search(r'(\d+)\s*(?:bids?|proposals?)', desc, re.IGNORECASE)
            proposals = int(proposals_match.group(1)) if proposals_match else 999
            
            # Extrair skills
            skills = re.findall(r'(?:Excel|Python|Data Entry|Web Scraping|PDF|Word|Virtual Assistant|Typing|Copy Paste|CSV|Data Processing|Automation|Translation|Proofreading|Formatting)', desc, re.IGNORECASE)
            
            job_id = re.search(r'/projects/(?:[^/]+-)?(\d+)', link)
            job_id = job_id.group(1) if job_id else link
            
            jobs.append({
                'id': job_id,
                'title': title,
                'link': link,
                'description': desc[:500],
                'budget': budget,
                'proposals': proposals,
                'skills': list(set(s.lower() for s in skills)),
                'pubdate': pubdate,
                'scanned_at': datetime.now(timezone.utc).isoformat()
            })
    except ET.ParseError as e:
        log(f"⚠ Erro parse RSS: {e}")
    
    return jobs

def filter_jobs(jobs, state):
    """Filtra jobs por relevância e orçamento."""
    matches = []
    
    for job in jobs:
        job_id = str(job.get('id', ''))
        title = (job.get('title', '') + ' ' + job.get('description', '')).lower()
        
        # Pular já vistos
        if job_id in state.get('seen_job_ids', []):
            continue
        
        # Pular muitos concorrentes
        if job.get('proposals', 0) > MAX_PROPOSALS:
            continue
        
        # Verificar keywords positivas
        has_keyword = any(k in title for k in JOB_KEYWORDS)
        has_skip = any(k in title for k in SKIP_KEYWORDS)
        
        if has_keyword and not has_skip:
            # Score de match
            score = sum(1 for k in JOB_KEYWORDS if k in title)
            score += 2 if 'excel' in title and any(k in title for k in ['advanced', 'macro', 'vba', 'formula']) else 0
            score += 2 if 'python' in title else 0
            
            job['score'] = score
            matches.append(job)
    
    # Ordenar por score
    matches.sort(key=lambda j: j.get('score', 0), reverse=True)
    return matches

def generate_proposal(job):
    """Gera proposta em inglês para Freelancer.com."""
    title = job.get('title', '').lower()
    
    if any(k in title for k in ['excel', 'spreadsheet', 'google sheets']):
        return (
            f"I can deliver this Excel work quickly and professionally. "
            f"I have advanced Excel skills including formulas, macros, "
            f"data validation, and dashboard creation.\n\n"
            f"I can start right away and deliver within the deadline.\n\n"
            f"Best regards,\nRoberto"
        )
    
    elif any(k in title for k in ['data entry', 'typing', 'copy paste']):
        return (
            f"I can handle this data entry task accurately and quickly. "
            f"I'm detail-oriented and can deliver clean, organized results.\n\n"
            f"Available to start immediately.\n\n"
            f"Best regards,\nRoberto"
        )
    
    elif any(k in title for k in ['python', 'scraping', 'automation', 'script']):
        return (
            f"I can build this Python script for you. "
            f"I've done similar automation and data extraction projects "
            f"and can deliver a working, documented solution.\n\n"
            f"I can provide a prototype within 24 hours.\n\n"
            f"Best regards,\nRoberto"
        )
    
    elif any(k in title for k in ['pdf', 'word', 'conversion']):
        return (
            f"I can convert and format this document accurately. "
            f"I work with PDF, Word, and Excel conversions regularly "
            f"and can deliver clean formatted output.\n\n"
            f"Best regards,\nRoberto"
        )
    
    elif any(k in title for k in ['virtual assistant', 'admin']):
        return (
            f"I'm available to assist with this task. "
            f"I'm organized, reliable, and can handle administrative "
            f"work efficiently.\n\n"
            f"Best regards,\nRoberto"
        )
    
    else:
        return (
            f"I'm interested in this project and can deliver quality results. "
            f"With my skills in data processing and automation, "
            f"I can complete this efficiently.\n\n"
            f"Best regards,\nRoberto"
        )

def scan():
    """Pipeline principal do sub-agente Freelancer.com."""
    log("🔍 Escaneando Freelancer.com...")
    
    state = load_state()
    all_jobs = []
    new_matches = []
    
    for feed_url in RSS_FEEDS:
        xml_data = fetch_rss(feed_url)
        if xml_data:
            jobs = parse_freelancer_rss(xml_data)
            all_jobs.extend(jobs)
    
    log(f"  📡 {len(all_jobs)} jobs via RSS")
    
    # Filtrar
    matches = filter_jobs(all_jobs, state)
    
    if matches:
        log(f"  🎯 {len(matches)} JOBS COMPATÍVEIS:")
        for j in matches[:10]:
            budget = j.get('budget', '?') or '?'
            proposals = j.get('proposals', '?')
            score = j.get('score', 0)
            log(f"     [{score}] {j['title'][:80]} | {budget} | {proposals} bids")
    
    # Atualizar estado
    for job in all_jobs:
        jid = str(job.get('id', ''))
        if jid not in state.get('seen_job_ids', []):
            state['seen_job_ids'].append(jid)
    
    state['last_scan'] = datetime.now(timezone.utc).isoformat()
    state['total_scanned'] += len(all_jobs)
    state['matches_found'] += len(matches)
    
    # Manter últimos 500 job IDs
    if len(state.get('seen_job_ids', [])) > 500:
        state['seen_job_ids'] = state['seen_job_ids'][-500:]
    
    save_state(state)
    
    # Salvar matches
    if matches:
        existing = load_jobs()
        existing = [j for j in existing if j.get('id') not in [m['id'] for m in matches]]
        existing.extend(matches)
        existing = existing[-100:]  # Manter últimos 100
        save_jobs(existing)
        
        # Alertar Tálamo se tiver jobs high-score
        high_score = [j for j in matches if j.get('score', 0) >= 4]
        if high_score:
            try:
                import thalamus
                for j in high_score[:3]:
                    thalamus.broadcast_to_workspace(
                        f"💼 Freelancer.com: {j['title'][:80]} | {j.get('budget','?')} | "
                        f"Score:{j.get('score',0)} | {j.get('proposals',0)} bids",
                        priority=7, source="freelancer_agent"
                    )
            except:
                pass
    
    # Resumo
    log(f"\n📊 RESUMO Freelancer.com:")
    log(f"  Total escaneados: {state['total_scanned']}")
    log(f"  Matches hoje: {state['matches_found']}")
    log(f"  Telefone verificado: {state['phone_verified']}")
    log(f"  Selo Verified: {state['verified_badge']}")
    
    if not state['phone_verified']:
        log(f"  ⛔ AÇÃO PENDENTE: Verificar telefone!")
    
    return matches

def check_profile_status():
    """Verifica status do perfil via CDP Brave."""
    try:
        r = subprocess.run(['curl', '-s', 'http://localhost:9222/json'],
            capture_output=True, text=True, timeout=5)
        tabs = json.loads(r.stdout)
        
        for t in tabs:
            if 'freelancer.com' in t.get('url', '').lower():
                # Perfil já aberto — verificar status
                import asyncio
                from websockets import connect
                
                async def check():
                    async with connect(t['webSocketDebuggerUrl'], close_timeout=10) as ws:
                        await ws.send(json.dumps({"id":1,"method":"Runtime.evaluate",
                            "params":{"expression":"""
                                (function() {
                                    return JSON.stringify({
                                        url: window.location.href,
                                        has_verify_banner: !!document.querySelector('[class*="verify"], [class*="verification"]'),
                                        body_snippet: document.body ? document.body.innerText.substring(0, 1000) : ''
                                    });
                                })()
                            ""","returnByValue":True}}))
                        for _ in range(20):
                            resp = await asyncio.wait_for(ws.recv(), timeout=5)
                            data = json.loads(resp)
                            if data.get("id") == 1:
                                return json.loads(data.get("result",{}).get("result",{}).get("value",""))
                        return None
                
                return asyncio.run(check())
    except:
        pass
    return None

if __name__ == "__main__":
    scan()
