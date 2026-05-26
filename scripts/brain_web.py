#!/usr/bin/env python3
"""
Brain Web Search — Busca na internet independente para o cérebro.
Zero tokens. Zero APIs pagas.

Fontes (em ordem):
  1. Wikipedia API — conhecimento enciclopédico
  2. DuckDuckGo Instant Answer — definições e tópicos
  3. CDP Browser — para páginas que exigem JavaScript

Uso:
  brain_web.py search "termo"     → busca combinada
  brain_web.py wiki   "termo"     → só Wikipedia
  brain_web.py fetch  URL         → texto de uma página
"""

import json, sys, urllib.request, urllib.parse, re
from pathlib import Path
from datetime import datetime

CACHE_DIR = Path.home() / '.hermes' / 'brain_web_cache'
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

def _cache(key, content=None):
    f = CACHE_DIR / f"{key.replace('/', '_')[:120]}.json"
    if content is not None:
        f.write_text(json.dumps({'ts': datetime.now().timestamp(), 'content': content}))
        return content
    if f.exists():
        try:
            data = json.loads(f.read_text())
            if datetime.now().timestamp() - data.get('ts', 0) < CACHE_TTL:
                return data.get('content')
        except: pass
    return None

UA = 'BrainBot/1.0 (Cérebro da ENTIDADE; +https://t.me/HermesEntidadeBot)'

# ═══════════════ WIKIPEDIA ═══════════════

def _wiki_search(query, limit=5):
    """Busca na Wikipedia."""
    cached = _cache(f"wiki_{query}")
    if cached: return cached
    
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json&srlimit={limit}"
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        
        results = []
        for r in data.get('query', {}).get('search', [])[:limit]:
            snippet = re.sub(r'<[^>]+>', '', r.get('snippet', ''))
            title = r['title']
            results.append({
                'title': title,
                'url': f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}",
                'snippet': snippet[:300],
                'source': 'wikipedia'
            })
        _cache(f"wiki_{query}", results)
        return results
    except Exception as e:
        return [{'error': str(e), 'source': 'wikipedia'}]

def _wiki_extract(title, max_chars=2000):
    """Extrai texto de um artigo da Wikipedia."""
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&titles={urllib.parse.quote(title)}&format=json"
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        pages = data.get('query', {}).get('pages', {})
        for pid, page in pages.items():
            return page.get('extract', '')[:max_chars]
    except: pass
    return ''

# ═══════════════ DUCKDUCKGO ═══════════════

def _ddg_search(query):
    """DuckDuckGo Instant Answer API."""
    cached = _cache(f"ddg_{query}")
    if cached: return cached
    
    try:
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1"
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        
        results = []
        
        # Abstract (definição principal)
        if data.get('Abstract'):
            results.append({
                'title': data.get('Heading', '') or query,
                'url': data.get('AbstractURL', ''),
                'snippet': data['Abstract'][:400],
                'source': 'duckduckgo'
            })
        
        # Related Topics
        for t in data.get('RelatedTopics', [])[:5]:
            text = t.get('Text', '')
            url = t.get('FirstURL', '')
            if text and url:
                results.append({
                    'title': text[:150],
                    'url': url,
                    'snippet': '',
                    'source': 'duckduckgo'
                })
        
        _cache(f"ddg_{query}", results)
        return results
    except Exception as e:
        return [{'error': str(e), 'source': 'duckduckgo'}]

# ═══════════════ CDP BROWSER FALLBACK ═══════════════

def _cdp_fetch(url, max_chars=3000):
    """Busca página via CDP (para sites com JavaScript)."""
    try:
        import websocket, time
        port = 9222
        try:
            urllib.request.urlopen(f'http://localhost:{port}/json/version', timeout=2)
        except:
            port = 9223
        
        req = urllib.request.Request(
            f'http://localhost:{port}/json/new?{urllib.parse.quote(url, safe="")}',
            method='PUT')
        tab = json.loads(urllib.request.urlopen(req, timeout=10).read())
        time.sleep(4)
        
        ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=15)
        ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
            "params": {"expression": "document.body.innerText", "returnByValue": True}}))
        resp = json.loads(ws.recv())
        text = resp.get('result',{}).get('result',{}).get('value','')
        ws.close()
        
        return text[:max_chars] if text else ''
    except: pass
    return ''

# ═══════════════ SEARCH COMBINADA ═══════════════

def search(query, max_results=8):
    """Busca combinada: Wikipedia + DuckDuckGo."""
    all_results = []
    
    wiki_results = _wiki_search(query, max_results//2)
    for r in wiki_results:
        if 'error' not in r:
            # Tentar extrair texto do artigo
            extract = _wiki_extract(r['title'], 500)
            if extract:
                r['snippet'] = extract[:300]
            all_results.append(r)
    
    ddg_results = _ddg_search(query)
    for r in ddg_results:
        if 'error' not in r:
            all_results.append(r)
    
    # Dedup por URL
    seen = set()
    unique = []
    for r in all_results:
        if r.get('url') not in seen:
            seen.add(r.get('url'))
            unique.append(r)
    
    return unique[:max_results]


def fetch(url, max_chars=3000):
    """Busca texto de uma URL (tenta CDP primeiro, depois HTTP)."""
    # CDP primeiro (lida com JavaScript)
    text = _cdp_fetch(url, max_chars)
    if text and len(text) > 100:
        return text
    
    # Fallback HTTP
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
        # Strip HTML
        text = re.sub(r'<script[^>]*>.*?</script>', '', raw, flags=re.DOTALL|re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL|re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()[:max_chars]
    except Exception as e:
        return f"Erro: {e}"


# ═══════════════ CLI ═══════════════
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: brain_web.py <search|wiki|fetch> <termo|url>")
        sys.exit(1)
    
    action = sys.argv[1]
    arg = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else ''
    
    if action == 'search':
        results = search(arg)
    elif action == 'wiki':
        results = _wiki_search(arg)
    elif action == 'fetch':
        results = fetch(arg)
    else:
        print(f"Ação desconhecida: {action}")
        sys.exit(1)
    
    print(json.dumps(results, indent=2, ensure_ascii=False))
