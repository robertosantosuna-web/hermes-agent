# 99Freelas — Pesquisa de Dados para Cliente (22/05/2026)

## Contexto

Cliente Martin L. pediu planilha com dados de clínicas radiológicas (CNPJ, endereço, modalidades, decisores, LinkedIn). Base com 18 clínicas, apenas nome/cidade/estado/site preenchidos. O resto precisava de pesquisa web.

## Métodos que FUNCIONARAM

### DuckDuckGo Lite (CNPJ e dados básicos)
```python
import urllib.request, urllib.parse, re
query = urllib.parse.quote(f"{nome} {cidade} CNPJ endereço")
url = f"https://lite.duckduckgo.com/lite/?q={query}"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=10)
html = resp.read().decode('utf-8', errors='replace')
cnpjs = re.findall(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', html)
```
Pitfall: Rate limit após ~5-8 chamadas. Espaçar 2s.

### Scraping direto dos sites
```python
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=15, context=ssl_ctx)
html = resp.read().decode('utf-8', errors='replace')
cnpj = re.findall(r'CNPJ[:\s]*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', html)
addr = re.findall(r'(?:Rua|Av\.|Alameda)\s+[A-Z][^,<]*\d+', html)
emails = re.findall(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', html)
```
Pitfall: Alguns sites bloqueiam 403. Ignorar SSL com `ssl._create_unverified_context()`.

### Modalidades
```python
mods = ['Raio X','Tomografia','Ressonância','Mamografia','Ultrassonografia',
        'Densitometria','PET-CT','Medicina Nuclear']
found = [m for m in mods if m.lower() in html.lower()]
```

## Métodos que NÃO FUNCIONARAM

- Google Search via browser tools: CAPTCHA
- Google Search via curl: bloqueio imediato
- BrasilAPI/ReceitaWS: precisa do CNPJ primeiro
- LinkedIn scraping: requer login

## Template de Mensagem

NUNCA mencionar valor/prazo no corpo. Abrir com nome do cliente. Fechar com "abs, Roberto".
