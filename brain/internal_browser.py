#!/usr/bin/env python3
"""
Navegador Interno da ENTIDADE — Chromium headless dedicado.
Porta CDP: 9226
Perfil persistente: ~/.hermes/browser-profile/
Não conflita com Brave (:9222), Edge WA (:9224), Edge (:9225)
"""

import subprocess, sys, time, json, os
from pathlib import Path

PROFILE_DIR = Path.home() / '.hermes' / 'browser-profile'
CDP_PORT = 9226
CHROMIUM_BIN = Path.home() / '.cache/ms-playwright/chromium-1217/chrome-linux64/chrome'

def start():
    """Inicia o navegador interno em background."""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Mata instância anterior se existir
    subprocess.run(['pkill', '-f', f'chromium.*{CDP_PORT}'], capture_output=True)
    time.sleep(1)
    
    cmd = [
        str(CHROMIUM_BIN),
        f'--remote-debugging-port={CDP_PORT}',
        f'--user-data-dir={PROFILE_DIR}',
        '--headless=new',
        '--no-first-run',
        '--no-default-browser-check',
        '--disable-gpu',
        '--disable-extensions',
        '--disable-background-networking',
        '--disable-sync',
        '--disable-translate',
        '--disable-features=TranslateUI',
        '--window-size=1920,1080',
        '--no-sandbox',
        'about:blank'
    ]
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    
    # Aguardar CDP ficar disponível
    for i in range(15):
        time.sleep(0.5)
        try:
            r = subprocess.run(
                ['curl', '-s', f'http://localhost:{CDP_PORT}/json/version'],
                capture_output=True, text=True, timeout=3
            )
            if r.returncode == 0 and 'webSocketDebuggerUrl' in r.stdout:
                print(f"✅ Navegador interno online — porta {CDP_PORT} (PID {proc.pid})")
                return proc.pid
        except:
            pass
    
    print(f"❌ Falha ao iniciar navegador interno na porta {CDP_PORT}")
    return None

def stop():
    """Para o navegador interno."""
    subprocess.run(['pkill', '-f', f'chromium.*{CDP_PORT}'], capture_output=True)
    print("🛑 Navegador interno parado")

def status():
    """Verifica se está rodando."""
    try:
        r = subprocess.run(
            ['curl', '-s', f'http://localhost:{CDP_PORT}/json/version'],
            capture_output=True, text=True, timeout=3
        )
        if r.returncode == 0:
            data = json.loads(r.stdout)
            print(f"✅ ONLINE — porta {CDP_PORT}")
            print(f"   Browser: {data.get('Browser', '?')}")
            print(f"   User-Agent: {data.get('User-Agent', '?')[:80]}...")
            
            # Listar abas
            tabs = json.loads(subprocess.run(
                ['curl', '-s', f'http://localhost:{CDP_PORT}/json'],
                capture_output=True, text=True, timeout=3
            ).stdout)
            print(f"   Abas abertas: {len(tabs)}")
            for t in tabs:
                print(f"     - {t.get('title', '?')[:60]} | {t.get('url', '?')[:80]}")
            return True
    except:
        pass
    print("❌ OFFLINE")
    return False

def restart():
    """Reinicia o navegador."""
    stop()
    time.sleep(2)
    return start()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: internal_browser.py [start|stop|status|restart]")
        sys.exit(1)
    
    action = sys.argv[1]
    if action == 'start':
        start()
    elif action == 'stop':
        stop()
    elif action == 'status':
        status()
    elif action == 'restart':
        restart()
    else:
        print(f"Ação desconhecida: {action}")
        sys.exit(1)
