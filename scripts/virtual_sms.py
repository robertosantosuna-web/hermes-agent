#!/usr/bin/env python3
"""
Virtual SMS Tool — Números temporários para receber SMS de verificação.
Uso: python3 virtual_sms.py <ação> [args...]

Estratégias (fallback automático):
  1. receivesms.org — scraping web (números Brasil, gratuito)
  2. smspool.net — API (requer API key, ~R$0.30/ativação)  
  3. sms-activate.org — API (requer API key)

Ações:
  list              — Listar números disponíveis (Brasil)
  get [service]     — Obter número disponível
  check <numero>    — Verificar SMS recebidos no número
  watch <numero>    — Monitorar até receber SMS (timeout 120s)
"""

import requests
import re
import json
import time
import sys
import os
from datetime import datetime
from typing import Optional

# Config
CONFIG_PATH = os.path.expanduser("~/.hermes/config/sms_services.json")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}
CACHE_FILE = os.path.expanduser("~/.hermes/cache/sms_cache.json")


def load_cache():
    """Carregar cache de números/SMS"""
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except:
        return {}


def save_cache(data):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ═══════════════════════════════════════════
# ESTRATÉGIA 1: receivesms.org (gratuito)
# ═══════════════════════════════════════════

def receivesms_get_numbers():
    """Extrair números Brasil disponíveis no receivesms.org"""
    try:
        r = requests.get(
            "https://receivesms.org/sms/brazil-phone-number/",
            headers=HEADERS,
            timeout=15,
        )
        
        # Padrões de número
        patterns = [
            r'phone-number/(\d+)/',
            r'"number":"(\+\d+)"',
        ]
        
        numbers = []
        for p in patterns:
            found = re.findall(p, r.text)
            if found:
                numbers.extend(found)
                break
        
        # Se não encontrou por regex, tentar extrair via JavaScript state
        if not numbers:
            # Buscar dados em JSON inline
            json_data = re.findall(r'(?:numbers|phoneNumbers)\s*[:=]\s*(\[.*?\])', r.text, re.S)
            if json_data:
                try:
                    data = json.loads(json_data[0])
                    numbers = [str(n) for n in data if isinstance(n, (str, int))]
                except:
                    pass
        
        return list(set(numbers))
    except Exception as e:
        return []


def receivesms_get_messages(number):
    """Verificar SMS recebidos em um número do receivesms.org"""
    try:
        url = f"https://receivesms.org/sms/brazil-phone-number/{number}/"
        r = requests.get(url, headers=HEADERS, timeout=15)
        
        # Extrair mensagens
        msgs = []
        # Padrão comum: remetente + corpo da mensagem
        msg_blocks = re.findall(
            r'(?:sender|from)[^\w]*[:\s]*([^<]+).*?(?:message|body|text)[^\w]*[:\s]*([^<]+)',
            r.text,
            re.I | re.S,
        )
        for sender, body in msg_blocks:
            msgs.append({
                "sender": sender.strip()[:50],
                "body": body.strip()[:200],
                "time": datetime.now().isoformat(),
            })
        
        if not msgs:
            # Tentar extrair qualquer texto que pareça mensagem
            raw_msgs = re.findall(
                r'(?:OTP|code|código|senha|verif\w+)[^\n]{3,50}',
                r.text,
                re.I,
            )
            for m in raw_msgs:
                msgs.append({
                    "sender": "unknown",
                    "body": m.strip()[:200],
                    "time": datetime.now().isoformat(),
                })
        
        return msgs
    except:
        return []


def receivesms_list_numbers():
    """Listar números Brasil disponíveis no receivesms.org"""
    try:
        r = requests.get(
            "https://receivesms.org/sms/brazil-phone-number/",
            headers=HEADERS,
            timeout=15,
        )
        # Tentar extrair números
        numbers = set()
        
        # Buscar qualquer padrão numérico
        raw_nums = re.findall(r'(\d{10,13})', r.text)
        for n in raw_nums:
            if n.startswith("55") and len(n) >= 12:
                formatted = f"+{n[:2]} {n[2:4]} {n[4:9]}-{n[9:]}"
                numbers.add(formatted)
        
        return list(numbers)[:20]
    except:
        return []


# ═══════════════════════════════════════════
# ESTRATÉGIA 2: quackr.io (gratuito, números globais)
# ═══════════════════════════════════════════

def quackr_get_numbers():
    """Obter números disponíveis no quackr.io"""
    try:
        r = requests.get(
            "https://quackr.io/temporary-numbers/brazil",
            headers=HEADERS,
            timeout=15,
        )
        # Extrair números do DOM/data
        nums = re.findall(r'\+55[\d\s]+', r.text)
        return list(set([n.strip() for n in nums]))
    except:
        return []


# ═══════════════════════════════════════════
# ESTRATÉGIA 3: API direta (sms-activate, smspool)
# ═══════════════════════════════════════════

def load_api_config():
    """Carregar configurações de API"""
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except:
        return {}


def smspool_get_number(api_key):
    """Alugar número via smspool.net (pago, barato)"""
    try:
        r = requests.post(
            "https://api.smspool.net/purchase/1",
            data={
                "key": api_key,
                "country": "Brazil",
                "service": "any",
            },
            headers=HEADERS,
            timeout=15,
        )
        data = r.json()
        if data.get("success") == 1:
            return {
                "number": data.get("number"),
                "order_id": data.get("order_id"),
                "cost": data.get("cost"),
            }
        return None
    except:
        return None


def smspool_check_sms(api_key, order_id):
    """Verificar SMS no smspool"""
    try:
        r = requests.post(
            "https://api.smspool.net/sms/1",
            data={"key": api_key, "orderid": order_id},
            headers=HEADERS,
            timeout=15,
        )
        data = r.json()
        if data.get("success") == 1 and data.get("sms"):
            return {
                "sender": data.get("sms", {}).get("from", "unknown"),
                "body": data.get("sms", {}).get("text", ""),
                "time": data.get("sms", {}).get("created_at", ""),
            }
        return None
    except:
        return None


# ═══════════════════════════════════════════
# INTERFACE PRINCIPAL
# ═══════════════════════════════════════════

def list_all_numbers():
    """Listar todos os números disponíveis em todos os serviços"""
    results = {}
    
    # receivesms.org
    nums = receivesms_list_numbers()
    if nums:
        results["receivesms.org"] = nums
    
    # quackr.io
    nums = quackr_get_numbers()
    if nums:
        results["quackr.io"] = nums[:10]
    
    return results


def get_best_number(prefer_service=None):
    """
    Obter o melhor número disponível.
    Prioridade: API paga > scraping gratuito
    """
    config = load_api_config()
    
    # 1. Tentar smspool (se tiver API key)
    api_key = config.get("smspool_api_key")
    if api_key:
        result = smspool_get_number(api_key)
        if result:
            return {"service": "smspool", **result}
    
    # 2. receivesms.org (gratuito)
    nums = receivesms_get_numbers()
    if nums:
        return {
            "service": "receivesms.org",
            "number": nums[0],
            "cost": "free",
        }
    
    # 3. quackr.io
    nums = quackr_get_numbers()
    if nums:
        return {
            "service": "quackr.io",
            "number": nums[0],
            "cost": "free",
        }
    
    return {"error": "Nenhum número disponível no momento"}


def check_messages(number, service="receivesms.org"):
    """Verificar SMS recebidos"""
    if "receivesms" in service:
        return receivesms_get_messages(number)
    elif "smspool" in service:
        config = load_api_config()
        api_key = config.get("smspool_api_key")
        order_id = config.get(f"order_{number}")
        if api_key and order_id:
            return [smspool_check_sms(api_key, order_id)]
    return []


def watch_for_sms(number, service="receivesms.org", timeout=120):
    """Monitorar número até receber SMS"""
    start = time.time()
    seen = set()
    
    print(f"🔍 Monitorando {number} ({service})...")
    print(f"   Timeout: {timeout}s")
    print()
    
    while time.time() - start < timeout:
        msgs = check_messages(number, service)
        for msg in msgs:
            key = msg.get("body", "")[:50]
            if key and key not in seen:
                seen.add(key)
                print(f"📩 SMS RECEBIDO!")
                print(f"   De: {msg.get('sender', '?')}")
                print(f"   Msg: {msg.get('body', '?')}")
                print(f"   Hora: {msg.get('time', '?')}")
                print()
                return msg
        
        elapsed = int(time.time() - start)
        print(f"\r   Aguardando... {elapsed}s", end="", flush=True)
        time.sleep(3)
    
    print(f"\r⏰ Timeout ({timeout}s) — nenhum SMS recebido.")
    return None


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    action = sys.argv[1]
    
    if action == "list":
        print("📋 NÚMEROS VIRTUAIS DISPONÍVEIS (Brasil)")
        print("=" * 50)
        results = list_all_numbers()
        if not results:
            print("❌ Nenhum número disponível no momento.")
            return
        
        for service, numbers in results.items():
            print(f"\n🔹 {service} ({len(numbers)} números):")
            for n in numbers[:15]:
                print(f"   {n}")
    
    elif action == "get":
        service = sys.argv[2] if len(sys.argv) > 2 else None
        print("🔍 Buscando melhor número disponível...")
        result = get_best_number(service)
        
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"✅ Número obtido!")
            print(f"   Serviço: {result['service']}")
            print(f"   Número:  {result.get('number')}")
            if result.get("cost"):
                print(f"   Custo:   {result['cost']}")
            
            # Salvar no cache
            cache = load_cache()
            cache["last_number"] = result
            cache["last_updated"] = datetime.now().isoformat()
            save_cache(cache)
    
    elif action == "check":
        if len(sys.argv) < 3:
            print("Uso: virtual_sms.py check <numero> [servico]")
            return
        
        number = sys.argv[2]
        service = sys.argv[3] if len(sys.argv) > 3 else "receivesms.org"
        
        msgs = check_messages(number, service)
        if msgs:
            print(f"📩 {len(msgs)} SMS encontrados:")
            for msg in msgs:
                print(f"   De: {msg.get('sender', '?')}")
                print(f"   Msg: {msg.get('body', '?')}")
                print(f"   ---")
        else:
            print("📭 Nenhum SMS ainda.")
    
    elif action == "watch":
        if len(sys.argv) < 3:
            print("Uso: virtual_sms.py watch <numero> [servico] [timeout]")
            return
        
        number = sys.argv[2]
        service = sys.argv[3] if len(sys.argv) > 3 else "receivesms.org"
        timeout = int(sys.argv[4]) if len(sys.argv) > 4 else 120
        
        watch_for_sms(number, service, timeout)
    
    else:
        print(f"Ação desconhecida: {action}")
        print(__doc__)


if __name__ == "__main__":
    main()
