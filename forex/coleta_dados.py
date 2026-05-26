#!/usr/bin/env python3
"""Coleta CNPJ, endereço, modalidades de clínicas radiológicas"""
import csv, json, re, os, time
import requests
import urllib3
urllib3.disable_warnings()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
}
CACHE_FILE = '/home/roberto/.hermes/forex/cache_cnpj.json'

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

def buscar_cnpj_brasilapi(cnpj):
    """Verify CNPJ via Brasil API"""
    cnpj_clean = re.sub(r'[^\d]', '', cnpj)
    try:
        r = requests.get(f'https://brasilapi.com.br/api/cnpj/v1/{cnpj_clean}', 
                        headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def extrair_do_site(url, nome):
    """Extrai CNPJ, endereço, e outras infos do site"""
    info = {'cnpj': '', 'endereco': '', 'telefone': '', 'modalidades': '', 'linkedin': ''}
    
    if not url or not url.startswith('http'):
        return info
    
    paginas = [url]
    # Add common subpages
    for sub in ['/politica-de-privacidade/', '/politica-de-privacidade', '/privacidade/',
                '/lgpd/', '/lgpd', '/termos-de-uso/', '/contato/', '/fale-conosco/',
                '/institucional/', '/quem-somos/', '/sobre/']:
        if url.endswith('/'):
            paginas.append(url.rstrip('/') + sub)
        else:
            paginas.append(url + sub)
    
    for pagina in paginas[:3]:  # Max 3 pages per site
        try:
            r = requests.get(pagina, headers=HEADERS, timeout=12, verify=False)
            text = r.text
            
            # CNPJ
            if not info['cnpj']:
                cnpjs = re.findall(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', text)
                if cnpjs:
                    info['cnpj'] = cnpjs[0]
            
            # Endereço - multiple patterns
            if not info['endereco']:
                patterns = [
                    # Full address with CEP
                    r'(?:Rua|Avenida|Av\.?|Alameda|Praça|Rodovia|Estrada)\s+[\wÀ-ú\s]+[,.]?\s*(?:n[º°.]?\s*)?\d+[\w-]*(?:[,\s]+(?:sl|sala|andar|conj|conjunto|bloco|torre)\s*\d+[-\w]*)?[,\s]+(?:[\wÀ-ú\s]+)[,\s]+(?:[A-Z]{2})[,\s]*\d{5}-\d{3}',
                    # Simpler pattern
                    r'(?:Rua|Avenida|Av\.?|Alameda)\s+[\wÀ-ú\s]+[,.]?\s*(?:n?[º°.]?\s*)?\d+[\w-]*',
                ]
                for pat in patterns:
                    ends = re.findall(pat, text)
                    if ends:
                        info['endereco'] = ends[0].strip()
                        break
            
            # LinkedIn
            if not info['linkedin']:
                li = re.findall(r'(https?://(?:www\.)?linkedin\.com/[^\s"\'<>]+)', text)
                if li:
                    info['linkedin'] = li[0]
            
            # Modalidades - look for exam types mentioned
            if not info['modalidades']:
                modalidades_encontradas = []
                for mod in ['Ressonância Magnética', 'Tomografia Computadorizada', 
                           'Mamografia', 'Ultrassonografia', 'Raio[Xx]',
                           'Densitometria', 'PET[- ]CT', 'Medicina Nuclear',
                           'Ecocardiograma', 'Doppler', 'Angiografia',
                           'Radiologia Intervencionista', 'Biópsia']:
                    if re.search(mod, text, re.IGNORECASE):
                        modalidades_encontradas.append(mod.replace('[Xx]', ' X').replace('[- ]', '-'))
                if modalidades_encontradas:
                    info['modalidades'] = '; '.join(modalidades_encontradas[:8])
            
            # If we got CNPJ and address, we can stop
            if info['cnpj'] and info['endereco']:
                break
                
        except Exception as e:
            continue
    
    return info

# Known CNPJs from research
KNOWN_CNPJS = {
    "FLEURY": "60.840.055/0001-31",
    "DASA": "61.486.650/0001-83",
    "HERMES PARDINI": "19.378.769/0001-76",
    "HCOR": "60.453.024/0003-90",
    "CDB": "17.447.154/0002-00",
}

def get_cnpj_by_name(nome_upper):
    for key, cnpj in KNOWN_CNPJS.items():
        if key in nome_upper:
            return cnpj
    return None

def process_clinics(csv_path, start=0, count=20):
    """Process a batch of clinics"""
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    cache = load_cache()
    
    for i in range(start, min(start + count, len(rows))):
        row = rows[i]
        nome = row['Nome']
        site = row['Site']
        cidade = row['Cidade']
        
        print(f"\n[{i+1}/{len(rows)}] {nome}")
        
        # Check cache
        cache_key = nome.strip()
        if cache_key in cache:
            cached = cache[cache_key]
            for field in ['CNPJ','Endereco','Modalidades','LinkedIn Clinica','LinkedIn Decisor']:
                if cached.get(field):
                    row[field] = cached[field]
            print(f"  [CACHE] CNPJ={row['CNPJ']}, End={row['Endereco'][:50] if row['Endereco'] else 'N/A'}")
            continue
        
        # Try known CNPJ first
        cnpj_known = get_cnpj_by_name(nome.upper())
        if cnpj_known:
            row['CNPJ'] = cnpj_known
            print(f"  CNPJ (known): {cnpj_known}")
            
            # Verify via Brasil API for address
            br_data = buscar_cnpj_brasilapi(cnpj_known)
            if br_data:
                logr = br_data.get('logradouro', '') or ''
                num = br_data.get('numero', '') or ''
                bairro = br_data.get('bairro', '') or ''
                muni = br_data.get('municipio', '') or ''
                uf = br_data.get('uf', '') or ''
                cep = br_data.get('cep', '') or ''
                if logr:
                    row['Endereco'] = f"{logr}, {num} - {bairro}, {muni}/{uf}, CEP {cep}"
                    print(f"  End (BrasilAPI): {row['Endereco'][:80]}")
        
        # Extract from website
        if site:
            print(f"  Acessando: {site}")
            info = extrair_do_site(site, nome)
            
            if not row['CNPJ'] and info.get('cnpj'):
                row['CNPJ'] = info['cnpj']
                print(f"  CNPJ (site): {info['cnpj']}")
            
            if not row['Endereco'] and info.get('endereco'):
                row['Endereco'] = info['endereco']
                print(f"  End (site): {info['endereco'][:80]}")
            
            if not row['Modalidades'] and info.get('modalidades'):
                row['Modalidades'] = info['modalidades']
                print(f"  Mod: {info['modalidades'][:80]}")
            
            if not row['LinkedIn Clinica'] and info.get('linkedin'):
                row['LinkedIn Clinica'] = info['linkedin']
                print(f"  LinkedIn: {info['linkedin']}")
        
        # Save to cache
        cache[cache_key] = {
            'CNPJ': row['CNPJ'],
            'Endereco': row['Endereco'],
            'Modalidades': row['Modalidades'],
            'LinkedIn Clinica': row['LinkedIn Clinica'],
        }
        
        time.sleep(0.5)  # Rate limiting
    
    save_cache(cache)
    
    # Write updated CSV
    fieldnames = list(rows[0].keys())
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n✅ CSV salvo: {csv_path}")
    
    # Summary
    filled_cnpj = sum(1 for r in rows if r['CNPJ'])
    filled_end = sum(1 for r in rows if r['Endereco'])
    filled_mod = sum(1 for r in rows if r['Modalidades'])
    print(f"Progresso: CNPJ={filled_cnpj}/{len(rows)}, End={filled_end}/{len(rows)}, Mod={filled_mod}/{len(rows)}")

if __name__ == '__main__':
    csv_path = '/home/roberto/.hermes/forex/clinicas_radiologicas_martin_v2.csv'
    process_clinics(csv_path, start=0, count=20)
