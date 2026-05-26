#!/usr/bin/python3
"""
Login TradingView via Google usando Playwright + perfil Brave persistente.
Contorna o bloqueio "Esse navegador ou app pode não ser seguro" do Google.
"""

import os, sys, time
from playwright.sync_api import sync_playwright

BRAVE_PROFILE = os.path.expanduser("~/.config/BraveSoftware/Brave-Browser/Default")
TRADINGVIEW_LOGIN = "https://br.tradingview.com/accounts/signin/"

print("[1/5] Lançando Playwright com perfil persistente do Brave...")
sys.stdout.flush()

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=BRAVE_PROFILE,
        headless=False,
        args=[
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
        ],
        viewport={'width': 1280, 'height': 900},
        user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'
    )

    page = browser.new_page()

    print("[2/5] Navegando para TradingView login...")
    sys.stdout.flush()
    page.goto(TRADINGVIEW_LOGIN, wait_until='networkidle', timeout=30000)
    time.sleep(2)

    # Verificar se já está logado
    page_title = page.title()
    print(f"  Título: {page_title}")
    sys.stdout.flush()

    if 'signin' not in page.url.lower() and 'accounts' not in page.url.lower():
        print("[OK] Já está logado no TradingView!")
        # Salvar cookies/session info
        page.screenshot(path=os.path.expanduser("~/.hermes/forex/tv_loggedin.png"))
        print("  Screenshot: ~/.hermes/forex/tv_loggedin.png")
        browser.close()
        sys.exit(0)

    print("[3/5] Procurando botão Google login...")
    sys.stdout.flush()

    # O botão Google está dentro de um iframe
    try:
        # Esperar pelo iframe do Google
        page.wait_for_selector('iframe[title*="Google"]', timeout=10000)
        
        # Localizar o iframe
        google_frame = None
        for frame in page.frames:
            if 'google' in frame.url.lower() or 'accounts.google' in frame.url.lower():
                google_frame = frame
                break
        
        if not google_frame:
            # Tentar clicar no botão dentro do iframe via locator
            google_btn = page.frame_locator('iframe[title*="Google"]').locator('button')
            google_btn.click(timeout=5000)
            print("  Clicou no botão Google via frame_locator")
        else:
            print(f"  Iframe Google encontrado: {google_frame.url[:80]}")
            btn = google_frame.locator('button')
            btn.click(timeout=5000)
            print("  Clicou no botão Google dentro do iframe")
        
        time.sleep(3)
    except Exception as e:
        print(f"  Erro: {e}")
        # Tentar método alternativo: clicar no botão "E-mail"
        try:
            email_btn = page.locator('button:has-text("E-mail")')
            email_btn.click(timeout=3000)
            print("  Fallback: clicou em 'E-mail'")
        except:
            pass

    print(f"[4/5] URL atual: {page.url}")
    print(f"  Título: {page.title()}")
    sys.stdout.flush()

    # Verificar se o Google bloqueou
    if 'Não foi possível' in page.content() or 'não ser seguro' in page.content():
        print("[BLOQUEIO] Google detectou automação mesmo com Playwright.")
        print("  Solução: tente fazer login manual no Brave e depois reexecute.")
        page.screenshot(path=os.path.expanduser("~/.hermes/forex/tv_blocked.png"))
    else:
        page.screenshot(path=os.path.expanduser("~/.hermes/forex/tv_login_step.png"))
        print("[OK] Screenshot salvo. Verifique e complete o login manualmente se necessário.")
        print("  Screenshot: ~/.hermes/forex/tv_login_step.png")

    print("[5/5] Mantendo browser aberto por 60s para login manual...")
    print("  Complete o login na janela do navegador.")
    print("  NÃO FECHE a janela.")
    sys.stdout.flush()
    time.sleep(60)

    # Verificar se logou
    page.goto("https://br.tradingview.com/chart/", wait_until='networkidle', timeout=30000)
    time.sleep(3)
    page.screenshot(path=os.path.expanduser("~/.hermes/forex/tv_final.png"))
    print(f"  URL final: {page.url}")
    print(f"  Título final: {page.title()}")
    print("  Screenshot final: ~/.hermes/forex/tv_final.png")
    
    browser.close()
    print("[DONE]")
