#!/usr/bin/env python3
"""
TOOLKIT FREELANCER — Ferramentas de Acesso, Leitura e Estruturação
═══════════════════════════════════════════════════════════════════

Cada plataforma tem 3 ferramentas:
  ACCESS  → login, navegação, gestão de sessão
  READ    → extrair jobs, mensagens, status
  STRUCT  → parse, organizar, cache

+ Ferramentas transversais:
  EMAIL   → IMAP parse multi-formato
  RSS     → feed parser
  CDP     → navegação e extração DOM
  MEMORY  → cache, dedup, histórico
"""

import json, re, time, random
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

H = Path.home() / '.hermes'
FOREX = H / 'forex'

# ═══════════════════════════════════════════════════════════════
# BLOCO 1: FERRAMENTAS UNIVERSAIS
# ═══════════════════════════════════════════════════════════════

class CDPClient:
    """Cliente CDP unificado (Brave :9222, Edge :9225, Interno :9226)."""
    
    def __init__(self, port=9222):
        self.port = port
        self.base = f"http://localhost:{port}"
    
    def _curl(self, endpoint, method='GET', timeout=8):
        import subprocess
        cmd = ['curl', '-s', '--connect-timeout', str(timeout)]
        if method == 'PUT':
            cmd += ['-X', 'PUT']
        cmd.append(f"{self.base}{endpoint}")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+2)
        return r.stdout
    
    def _ws_send(self, ws_url, method, params=None, timeout=10):
        import asyncio
        from websockets import connect as ws_connect
        
        async def _do():
            async with ws_connect(ws_url, close_timeout=timeout) as ws:
                msg = {"id": 1, "method": method, "params": params or {}}
                await ws.send(json.dumps(msg))
                for _ in range(30):
                    resp = await asyncio.wait_for(ws.recv(), timeout=timeout)
                    data = json.loads(resp)
                    if data.get("id") == 1:
                        return data.get("result", {})
                return None
        return asyncio.run(_do())
    
    def list_tabs(self):
        tabs_json = self._curl('/json')
        return json.loads(tabs_json) if tabs_json else []
    
    def find_tab(self, url_pattern):
        for tab in self.list_tabs():
            if url_pattern in tab.get('url', ''):
                return tab
        return None
    
    def new_tab(self, url=None):
        endpoint = '/json/new'
        if url:
            endpoint += f'?url={url}'
        tab_json = self._curl(endpoint, method='PUT')
        return json.loads(tab_json) if tab_json else None
    
    def navigate(self, ws_url, url, wait_load=True):
        import asyncio
        from websockets import connect as ws_connect
        
        async def _nav():
            async with ws_connect(ws_url, close_timeout=15) as ws:
                await ws.send(json.dumps({"id":1,"method":"Page.enable"}))
                await asyncio.sleep(0.3)
                await ws.send(json.dumps({"id":2,"method":"Page.navigate",
                    "params":{"url":url}}))
                
                if wait_load:
                    for _ in range(40):
                        try:
                            resp = await asyncio.wait_for(ws.recv(), timeout=5)
                            if '"method":"Page.loadEventFired"' in resp:
                                return True
                        except:
                            break
                return True
        return asyncio.run(_nav())
    
    def evaluate(self, ws_url, expression, timeout=10):
        import asyncio
        from websockets import connect as ws_connect
        
        async def _eval():
            async with ws_connect(ws_url, close_timeout=timeout) as ws:
                await ws.send(json.dumps({"id":1,"method":"Runtime.evaluate",
                    "params":{"expression":expression,"returnByValue":True}}))
                for _ in range(30):
                    resp = await asyncio.wait_for(ws.recv(), timeout=timeout)
                    data = json.loads(resp)
                    if data.get("id") == 1:
                        return data.get("result",{}).get("result",{}).get("value")
                return None
        return asyncio.run(_eval())
    
    def click(self, ws_url, x, y):
        import asyncio
        from websockets import connect as ws_connect
        
        async def _click():
            async with ws_connect(ws_url, close_timeout=5) as ws:
                await ws.send(json.dumps({"id":1,"method":"Input.dispatchMouseEvent",
                    "params":{"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":1}}))
                await ws.send(json.dumps({"id":2,"method":"Input.dispatchMouseEvent",
                    "params":{"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":1}}))
                return True
        return asyncio.run(_click())
    
    def type_text(self, ws_url, text):
        """Digita caractere por caractere (anti-detecção)."""
        import asyncio
        from websockets import connect as ws_connect
        
        async def _type():
            async with ws_connect(ws_url, close_timeout=15) as ws:
                for char in text:
                    await ws.send(json.dumps({"id":1,"method":"Input.dispatchKeyEvent",
                        "params":{"type":"keyDown","key":char,"text":char}}))
                    await ws.send(json.dumps({"id":2,"method":"Input.dispatchKeyEvent",
                        "params":{"type":"keyUp","key":char,"text":char}}))
                    await asyncio.sleep(random.uniform(0.05, 0.15))
                return True
        return asyncio.run(_type())
    
    def fill_textarea(self, ws_url, text, selector='textarea'):
        """Preenche textarea via value setter com eventos (fallback)."""
        text_escaped = json.dumps(text)
        js = f"""
        (function() {{
            var el = document.querySelector('{selector}');
            if (!el) return 'NO ELEMENT';
            var ns = Object.getOwnPropertyDescriptor(
                window.HTMLTextAreaElement.prototype, 'value'
            )?.set;
            if (ns) ns.call(el, {text_escaped});
            else el.value = {text_escaped};
            el.dispatchEvent(new Event('input', {{bubbles: true}}));
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
            el.focus();
            return 'OK';
        }})()
        """
        return self.evaluate(ws_url, js)


class EmailClient:
    """Cliente IMAP unificado com parse multi-formato."""
    
    def __init__(self, user, password):
        self.user = user
        self.password = password
    
    def fetch_recent(self, senders, since_days=2):
        import imaplib, email as em
        from email.header import decode_header
        
        results = []
        
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=10)
            mail.login(self.user, self.password)
            mail.select("INBOX")
            
            since = (datetime.now() - timedelta(days=since_days)).strftime("%d-%b-%Y")
            
            for sender, platform in senders.items():
                try:
                    status, messages = mail.search(None, 
                        f'(FROM "{sender}" SINCE "{since}")')
                    if status != 'OK':
                        continue
                    
                    for mid in messages[0].split()[-30:]:
                        status, msg_data = mail.fetch(mid, "(RFC822)")
                        if status != 'OK':
                            continue
                        
                        msg = em.message_from_bytes(msg_data[0][1])
                        
                        subject = self._decode_header(msg.get('Subject', ''))
                        body = self._extract_body(msg)
                        
                        results.append({
                            'platform': platform,
                            'subject': subject,
                            'body': body,
                            'date': msg.get('Date', ''),
                            'message_id': mid.decode(),
                        })
                except:
                    continue
            
            mail.logout()
        except:
            pass
        
        return results
    
    def _decode_header(self, header):
        from email.header import decode_header
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
    
    def _extract_body(self, msg):
        import email as em
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        break
                    except:
                        pass
                elif ct == "text/html" and not body:
                    try:
                        html = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        body = self._strip_html(html)
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
            except:
                pass
        return body.strip()
    
    def _strip_html(self, html):
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
        html = re.sub(r'<head>.*?</head>', '', html, flags=re.DOTALL)
        html = re.sub(r'<[^>]+>', '\n', html)
        html = re.sub(r'&nbsp;', ' ', html)
        html = re.sub(r'&amp;', '&', html)
        return re.sub(r'\n\s*\n+', '\n', html)


class RSSClient:
    """Cliente RSS unificado."""
    
    def fetch(self, url):
        import xml.etree.ElementTree as ET
        from urllib.request import urlopen, Request
        
        try:
            req = Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            })
            with urlopen(req, timeout=15) as resp:
                data = resp.read()
            
            root = ET.fromstring(data)
            items = []
            
            for item in root.findall('.//item'):
                items.append({
                    'title': item.findtext('title', ''),
                    'link': item.findtext('link', ''),
                    'description': item.findtext('description', ''),
                    'pubdate': item.findtext('pubDate', ''),
                })
            
            return items
        except:
            return []


class JobCache:
    """Cache e deduplicação de jobs."""
    
    def __init__(self, cache_file):
        self.file = Path(cache_file)
        self.data = self._load()
    
    def _load(self):
        if self.file.exists():
            try:
                return json.loads(self.file.read_text())
            except:
                pass
        return {'seen_ids': [], 'jobs': [], 'stats': {}}
    
    def save(self):
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(self.data, indent=2, ensure_ascii=False))
    
    def is_new(self, job_id):
        return str(job_id) not in self.data['seen_ids']
    
    def mark_seen(self, job_id):
        self.data['seen_ids'].append(str(job_id))
        if len(self.data['seen_ids']) > 1000:
            self.data['seen_ids'] = self.data['seen_ids'][-500:]
    
    def add_job(self, job):
        self.data['jobs'].append(job)
        if len(self.data['jobs']) > 200:
            self.data['jobs'] = self.data['jobs'][-200:]
    
    def get_recent(self, hours=24):
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        return [j for j in self.data['jobs'] if j.get('scanned_at', '') > cutoff]


# ═══════════════════════════════════════════════════════════════
# BLOCO 2: FERRAMENTAS POR PLATAFORMA
# ═══════════════════════════════════════════════════════════════

class Platform99Freelas:
    """Acesso, leitura e estruturação do 99Freelas."""
    
    def __init__(self):
        self.cdp = CDPClient(port=9222)  # Brave
        self.cache = JobCache(FOREX / 'cache_99freelas.json')
        self.base_url = "https://www.99freelas.com.br"
    
    def access(self):
        """Abre ou localiza sessão no 99Freelas."""
        tab = self.cdp.find_tab('99freelas.com.br')
        if not tab:
            tab = self.cdp.new_tab()
            if tab:
                self.cdp.navigate(tab['webSocketDebuggerUrl'], 
                                 f"{self.base_url}/projects")
                time.sleep(3)
        return tab
    
    def read_projects(self):
        """Extrai lista de projetos disponíveis."""
        tab = self.access()
        if not tab:
            return []
        
        js = """
        (function() {
            var projects = [];
            var links = document.querySelectorAll('a[href*="/project/"]');
            links.forEach(function(a) {
                var text = a.innerText.trim();
                if (text.length > 10 && text.length < 200) {
                    projects.push({title: text, href: a.href});
                }
            });
            
            // Tentar extrair budgets e propostas
            var cards = document.querySelectorAll('[class*="job"], [class*="project-item"]');
            cards.forEach(function(c, i) {
                if (projects[i]) {
                    var t = c.innerText;
                    var budgetMatch = t.match(/R\\$\\s*[\\d.,]+/);
                    var propMatch = t.match(/(\\d+)\\s*propostas?/);
                    if (budgetMatch) projects[i].budget = budgetMatch[0];
                    if (propMatch) projects[i].proposals = parseInt(propMatch[1]);
                }
            });
            
            return JSON.stringify(projects);
        })()
        """
        
        result = self.cdp.evaluate(tab['webSocketDebuggerUrl'], js)
        try:
            projects = json.loads(result) if isinstance(result, str) else result
        except:
            projects = []
        
        # Marcar no cache
        for p in projects:
            jid = p.get('href', '')
            if self.cache.is_new(jid):
                self.cache.mark_seen(jid)
                p['scanned_at'] = datetime.now(timezone.utc).isoformat()
                self.cache.add_job(p)
        
        self.cache.save()
        return projects
    
    def read_messages(self):
        """Lê mensagens de projetos ativos."""
        tab = self.cdp.find_tab('99freelas.com.br/messages')
        if not tab:
            return []
        
        js = """
        (function() {
            var conversations = [];
            var items = document.querySelectorAll('[class*="message"], [class*="conversation"], [class*="chat"]');
            items.forEach(function(el) {
                var text = el.innerText.trim();
                if (text.length > 10) conversations.push(text.substring(0, 500));
            });
            return JSON.stringify(conversations);
        })()
        """
        result = self.cdp.evaluate(tab['webSocketDebuggerUrl'], js)
        try:
            return json.loads(result) if isinstance(result, str) else []
        except:
            return []
    
    def struct_project(self, project):
        """Estrutura um projeto em formato padronizado."""
        title = project.get('title', '')
        return {
            'id': project.get('href', '').split('/')[-1] if project.get('href') else '',
            'title': title,
            'url': project.get('href', ''),
            'budget': project.get('budget', ''),
            'proposals': project.get('proposals', 0),
            'category': self._classify(title),
            'platform': '99freelas',
            'currency': 'BRL',
        }
    
    def _classify(self, title):
        title_lower = title.lower()
        if any(k in title_lower for k in ['planilha', 'excel', 'dashboard']):
            return 'excel'
        if any(k in title_lower for k in ['digita', 'data entry', 'cadastro']):
            return 'data_entry'
        if any(k in title_lower for k in ['revisão', 'correção', 'abnt', 'tcc']):
            return 'revisao'
        if any(k in title_lower for k in ['traduç', 'translation']):
            return 'traducao'
        if any(k in title_lower for k in ['python', 'script', 'automação']):
            return 'python'
        if any(k in title_lower for k in ['pdf', 'word', 'converter']):
            return 'pdf_word'
        if any(k in title_lower for k in ['assistente', 'virtual', 'admin']):
            return 'virtual_assistant'
        return 'other'


class PlatformFreelancer:
    """Acesso, leitura e estruturação do Freelancer.com."""
    
    def __init__(self):
        self.cdp = CDPClient(port=9225)  # Edge
        self.rss = RSSClient()
        self.cache = JobCache(FOREX / 'cache_freelancer.json')
        self.base_url = "https://www.freelancer.com"
    
    def access(self):
        """Verifica/acessa Freelancer.com."""
        tab = self.cdp.find_tab('freelancer.com')
        if not tab:
            tab = self.cdp.new_tab()
            if tab:
                self.cdp.navigate(tab['webSocketDebuggerUrl'],
                                 f"{self.base_url}/jobs/")
                time.sleep(3)
        return tab
    
    def read_rss(self):
        """Lê feed RSS (não requer login)."""
        items = self.rss.fetch(f"{self.base_url}/rss.xml")
        jobs = []
        for item in items:
            job = self.struct_rss_item(item)
            if self.cache.is_new(job['id']):
                self.cache.mark_seen(job['id'])
                jobs.append(job)
        self.cache.save()
        return jobs
    
    def struct_rss_item(self, item):
        title = item.get('title', '')
        desc = item.get('description', '')
        
        # Extrair budget
        budget_match = re.search(r'\$[\d,]+', title)
        budget = budget_match.group(0) if budget_match else None
        
        # Extrair propostas
        prop_match = re.search(r'(\d+)\s*(?:bids?|proposals?)', desc, re.IGNORECASE)
        proposals = int(prop_match.group(1)) if prop_match else 999
        
        return {
            'id': item.get('link', ''),
            'title': title,
            'url': item.get('link', ''),
            'description': desc[:500],
            'budget': budget,
            'proposals': proposals,
            'pubdate': item.get('pubdate', ''),
            'platform': 'freelancer',
            'currency': 'USD',
            'scanned_at': datetime.now(timezone.utc).isoformat(),
        }


class PlatformWorkana:
    """Acesso passivo ao Workana (bloqueado para envio)."""
    
    def __init__(self):
        self.status = 'blocked'  # Perfil em análise
    
    def access(self):
        return {'status': self.status, 'reason': 'Perfil em análise — paywall R$59,90'}
    
    def read_email_only(self, emails):
        """Extrai apenas de notificações por email."""
        return [e for e in emails if e.get('platform') == 'workana']


class PlatformFiverr:
    """Monitoramento passivo do Fiverr (ABANDONADO para automação)."""
    
    def __init__(self):
        self.status = 'abandoned'  # 3 contas banidas
    
    def access(self):
        return {'status': self.status, 'reason': '3 contas banidas — NÃO automatizar'}
    
    def read_email_only(self, emails):
        return [e for e in emails if e.get('platform') == 'fiverr']


# ═══════════════════════════════════════════════════════════════
# BLOCO 3: ORQUESTRAÇÃO (UNIFICA TUDO)
# ═══════════════════════════════════════════════════════════════

class FreelancerToolkit:
    """Toolkit unificado — todas as ferramentas em um só lugar."""
    
    def __init__(self):
        self.email = EmailClient(
            user="robertosantos.una@gmail.com",
            password="exnlrvfswckioces"
        )
        self.platforms = {
            '99freelas': Platform99Freelas(),
            'freelancer': PlatformFreelancer(),
            'workana': PlatformWorkana(),
            'fiverr': PlatformFiverr(),
        }
        self.cache = JobCache(FOREX / 'cache_unified.json')
        
        # Mapeamento de remetentes de email
        self.email_senders = {
            'no-reply@99freelas.com.br': '99freelas',
            'notifications@freelancer.com': 'freelancer',
            'noreply@workana.com': 'workana',
            'noreply@fiverr.com': 'fiverr',
        }
    
    def scan_all(self):
        """Varredura completa: email + RSS + CDP."""
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'email': [],
            'rss': [],
            'cdp_99freelas': [],
            'total_new': 0,
        }
        
        # 1. Email
        results['email'] = self.email.fetch_recent(self.email_senders)
        
        # 2. RSS Freelancer
        try:
            results['rss'] = self.platforms['freelancer'].read_rss()
        except:
            results['rss'] = []
        
        # 3. CDP 99Freelas
        try:
            projects = self.platforms['99freelas'].read_projects()
            results['cdp_99freelas'] = [
                self.platforms['99freelas'].struct_project(p) 
                for p in projects
            ]
        except:
            results['cdp_99freelas'] = []
        
        # Contar novos
        results['total_new'] = (
            len(results['email']) + 
            len(results['rss']) + 
            len(results['cdp_99freelas'])
        )
        
        return results
    
    def status_report(self):
        """Relatório de status de todas as plataformas."""
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'platforms': {},
        }
        
        for name, plat in self.platforms.items():
            access = plat.access()
            report['platforms'][name] = {
                'status': access.get('status', 'active'),
                'detail': access.get('reason', 'OK'),
            }
        
        # Estatísticas do cache
        cache_data = self.cache.data
        report['cache'] = {
            'total_seen': len(cache_data.get('seen_ids', [])),
            'jobs_cached': len(cache_data.get('jobs', [])),
            'new_today': len([j for j in cache_data.get('jobs', []) 
                            if j.get('scanned_at', '')[:10] == datetime.now().strftime('%Y-%m-%d')]),
        }
        
        return report


# ═══════════════════════════════════════════════════════════════
# TESTE
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("TOOLKIT FREELANCER — Teste de ferramentas")
    print("=" * 60)
    
    toolkit = FreelancerToolkit()
    
    # Status
    print("\n📊 STATUS DAS PLATAFORMAS:")
    status = toolkit.status_report()
    for name, info in status['platforms'].items():
        emoji = "✅" if info['status'] == 'active' else "⛔" if info['status'] == 'blocked' else "❌"
        print(f"  {emoji} {name}: {info['status']} — {info['detail']}")
    
    # Scan
    print("\n🔍 SCAN COMPLETO:")
    results = toolkit.scan_all()
    print(f"  Email: {len(results['email'])} mensagens")
    print(f"  RSS Freelancer: {len(results['rss'])} jobs")
    print(f"  CDP 99Freelas: {len(results['cdp_99freelas'])} projetos")
    print(f"  TOTAL NOVOS: {results['total_new']}")
    
    print(f"\n  Cache: {status['cache']['total_seen']} vistos, "
          f"{status['cache']['new_today']} novos hoje")
