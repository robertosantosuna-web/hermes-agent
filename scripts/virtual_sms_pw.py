#!/usr/bin/env python3
"""
Virtual SMS Tool usando Playwright + CDP existente (porta 9226).
Extrai números temporários reais de serviços web.
"""

import asyncio
import sys
import json
import os
import time
from datetime import datetime

CACHE_FILE = os.path.expanduser("~/.hermes/cache/sms_cache.json")
CDP_PORT = 9226  # Chrome headless já rodando

SERVICES = {
    "receivesms": {
        "name": "receivesms.org",
        # URL que lista números Brasil
        "url": "https://receivesms.org/sms/brazil-phone-number/",
        # JS para extrair números
        "extract_js": """
            Array.from(document.querySelectorAll('a[href*="phone-number"], a[href*="/sms/"]'))
                .map(a => a.textContent.trim())
                .filter(t => /[0-9]/.test(t) && t.length > 5)
                .slice(0, 30)
        """,
        # URL para ver mensagens de um número específico
        "msg_url": lambda n: f"https://receivesms.org/sms/brazil-phone-number/{n}/",
    },
    "smsreceiving": {
        "name": "smsreceiving.com",
        "url": "https://smsreceiving.com/country/br/",
        "extract_js": """
            Array.from(document.querySelectorAll('.number-box, .number, a[href*="number"]'))
                .map(el => el.textContent.trim())
                .filter(t => /\\d{8,}/.test(t.replace(/\\s/g,'')))
                .slice(0, 30)
        """,
        "msg_url": lambda n: f"https://smsreceiving.com/number/br/{n}/",
    },
}


async def run():
    from playwright.async_api import async_playwright
    
    if len(sys.argv) < 2:
        print("📱 Virtual SMS Tool")
        print("  list              — Listar números disponíveis")
        print("  get [servico]     — Pegar números")
        print("  check <numero>    — Ver mensagens")
        print("  watch <numero>    — Monitorar até receber SMS")
        return
    
    action = sys.argv[1]
    
    async with async_playwright() as p:
        # Conectar ao Chrome já rodando na porta 9226
        browser = await p.chromium.connect_over_cdp(f"http://localhost:{CDP_PORT}")
        
        if action == "list" or action == "get":
            service_key = sys.argv[2] if len(sys.argv) > 2 else "receivesms"
            await list_numbers(browser, service_key)
        
        elif action == "check":
            number = sys.argv[2] if len(sys.argv) > 2 else None
            if not number:
                print("❌ Especifique o número")
                return
            service_key = sys.argv[3] if len(sys.argv) > 3 else "receivesms"
            await check_messages(browser, number, service_key)
        
        elif action == "watch":
            number = sys.argv[2] if len(sys.argv) > 2 else None
            if not number:
                print("❌ Especifique o número")
                return
            service_key = sys.argv[3] if len(sys.argv) > 3 else "receivesms"
            timeout = int(sys.argv[4]) if len(sys.argv) > 4 else 120
            await watch_number(browser, number, service_key, timeout)


async def list_numbers(browser, service_key="receivesms"):
    """Listar números disponíveis"""
    for key in [service_key] + [k for k in SERVICES if k != service_key]:
        svc = SERVICES.get(key)
        if not svc:
            continue
        
        print(f"🔍 {svc['name']}...")
        
        try:
            page = await browser.new_page()
            await page.goto(svc["url"], timeout=15000, wait_until="domcontentloaded")
            await page.wait_for_timeout(4000)
            
            numbers = await page.evaluate(svc["extract_js"])
            await page.close()
            
            if numbers:
                clean = []
                for n in numbers:
                    n = n.strip()
                    clean.append(n)
                
                print(f"✅ {len(clean)} números em {svc['name']}:")
                for i, n in enumerate(clean[:15]):
                    print(f"   [{i}] {n}")
                
                # Salvar cache
                cache = load_cache()
                cache["last_numbers"] = clean
                cache["last_service"] = key
                cache["last_updated"] = datetime.now().isoformat()
                save_cache(cache)
                return
            else:
                print(f"   📭 Nenhum número encontrado")
        
        except Exception as e:
            print(f"   ❌ {str(e)[:100]}")
    
    print("❌ Nenhum número encontrado em nenhum serviço.")


async def check_messages(browser, number, service_key="receivesms"):
    """Verificar mensagens em um número"""
    svc = SERVICES.get(service_key)
    if not svc:
        print(f"❌ Serviço desconhecido: {service_key}")
        return
    
    url = svc["msg_url"](number)
    print(f"📩 Verificando {number}...")
    
    try:
        page = await browser.new_page()
        await page.goto(url, timeout=15000, wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)
        
        # JS para extrair mensagens
        msgs = await page.evaluate("""
            () => {
                const results = [];
                const items = document.querySelectorAll('.message, .sms, .msg, tr, .row, [class*="mess"], [class*="sms"]');
                for (const item of items) {
                    const text = item.textContent.trim();
                    if (text.length > 10 && text.length < 500 && /[a-zA-Z0-9]/.test(text)) {
                        results.push(text);
                    }
                }
                if (results.length === 0) {
                    const lines = document.body.innerText.split('\\n').filter(l => l.trim().length > 8);
                    for (const l of lines.slice(0, 25)) {
                        if (l.length < 300) results.push(l);
                    }
                }
                return results.slice(0, 20);
            }
        """)
        
        await page.close()
        
        if msgs:
            print(f"📩 {len(msgs)} mensagens encontradas:")
            for i, msg in enumerate(msgs):
                print(f"   [{i}] {msg[:250]}")
        else:
            print("📭 Nenhuma mensagem ainda.")
    
    except Exception as e:
        print(f"❌ {str(e)[:100]}")


async def watch_number(browser, number, service_key="receivesms", timeout=120):
    """Monitorar número até receber SMS"""
    svc = SERVICES.get(service_key)
    if not svc:
        return
    
    url = svc["msg_url"](number)
    start = time.time()
    seen = set()
    
    print(f"🔍 Monitorando {number}...")
    print(f"   Timeout: {timeout}s\n")
    
    while time.time() - start < timeout:
        try:
            page = await browser.new_page()
            await page.goto(url, timeout=10000, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            
            texts = await page.evaluate("""
                () => {
                    const results = [];
                    const items = document.querySelectorAll('.message, .sms, .msg, tr, .row, [class*="mess"]');
                    for (const item of items) {
                        const t = item.textContent.trim();
                        if (t.length > 8 && t.length < 500) results.push(t);
                    }
                    return results;
                }
            """)
            
            await page.close()
            
            for t in texts:
                key = t[:50]
                if key not in seen:
                    seen.add(key)
                    # Filtrar apenas códigos/mensagens relevantes
                    if any(word in t.lower() for word in ['code', 'código', 'verify', 'senha', 'otp', 'token', 'confirm', 'activation', 'whatsapp', 'telegram', 'google']):
                        print(f"📩 SMS RECEBIDO!")
                        print(f"   {t[:300]}")
                        return t
            
            elapsed = int(time.time() - start)
            print(f"\r   Aguardando... {elapsed}s", end="", flush=True)
        
        except Exception as e:
            print(f"\r   Erro: {str(e)[:80]}")
        
        await asyncio.sleep(5)
    
    print(f"\r⏰ Timeout ({timeout}s) — nenhum SMS recebido.")
    return None


def load_cache():
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except:
        return {}


def save_cache(data):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    asyncio.run(run())
