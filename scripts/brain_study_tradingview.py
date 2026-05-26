#!/usr/bin/env python3
"""
Brain Study: TradingView Platform v2 — Deep Extraction
Usa OCR (Tesseract), screenshots CDP, DOM extraction, e API endpoints.
Extrai: vídeos educacionais, scripts Pine, ideias, notícias, webinars.

Requer: pytesseract, Pillow, websockets
"""
import asyncio, json, urllib.request, base64, os, sys, time, re
from pathlib import Path
from datetime import datetime, timezone
from io import BytesIO

CDP = 'http://localhost:9222'
HERMES = Path.home() / '.hermes'
STUDY_DIR = HERMES / 'forex' / 'research' / datetime.now().strftime('%Y-%m-%d')
SCREENSHOT_DIR = STUDY_DIR / 'screenshots'
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

discoveries = []

def write_bridge(content):
    import subprocess
    subprocess.run([
        'python3', str(HERMES / 'scripts' / 'knowledge_bridge.py'),
        'write', 'brain', content
    ], capture_output=True, timeout=10)

async def get_tv_ws():
    """Get TradingView tab WebSocket URL."""
    tabs = json.loads(urllib.request.urlopen(f"{CDP}/json/list").read())
    for t in tabs:
        if t.get('type') == 'page' and 'tradingview' in t.get('url', '').lower():
            return t['webSocketDebuggerUrl']
    # Open new
    req = urllib.request.Request(f"{CDP}/json/new?https://br.tradingview.com", method='PUT')
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
    await asyncio.sleep(3)
    return resp['webSocketDebuggerUrl']

async def cdp_screenshot(ws_url, filename):
    """Take screenshot via CDP and save to file."""
    import websockets
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({
            "id": 1, "method": "Page.captureScreenshot",
            "params": {"format": "png"}
        }))
        msg = await ws.recv()
        data = json.loads(msg)
        img_data = data.get('result', {}).get('data', '')
        if img_data:
            filepath = SCREENSHOT_DIR / filename
            filepath.write_bytes(base64.b64decode(img_data))
            return str(filepath)
    return None

async def cdp_navigate(ws_url, url, wait=5):
    """Navigate and wait for load."""
    import websockets
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({
            "id": 1, "method": "Page.navigate",
            "params": {"url": url}
        }))
        await ws.recv()
        await asyncio.sleep(wait)
    return ws_url

async def cdp_evaluate(ws_url, expression):
    """Execute JS and return result."""
    import websockets
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({
            "id": 1, "method": "Runtime.evaluate",
            "params": {"expression": expression, "returnByValue": True}
        }))
        for _ in range(3):
            msg = await ws.recv()
            data = json.loads(msg)
            if 'result' in data:
                return data['result'].get('result', {}).get('value', '')
    return None

def ocr_image(image_path):
    """Run OCR on a screenshot."""
    try:
        from PIL import Image
        import pytesseract
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='por+eng')
        return text
    except Exception as e:
        return f"OCR error: {e}"

def extract_trading_knowledge(text):
    """Extract trading-relevant lines from OCR text."""
    if not text:
        return []
    
    keywords = [
        'suporte', 'resistência', 'tendência', 'rompimento', 'padrão',
        'support', 'resistance', 'trend', 'breakout', 'pattern',
        'fvg', 'order block', 'liquidity', 'wyckoff', 'ict',
        'média móvel', 'moving average', 'rsi', 'macd', 'bollinger',
        'estratégia', 'strategy', 'setup', 'entrada', 'entry',
        'stop loss', 'take profit', 'risk', 'risco',
        'volume', 'delta', 'footprint', 'order flow',
        'candle', 'vela', 'doji', 'engolfo', 'pinbar',
        'notícia', 'news', 'fed', 'juros', 'inflação',
    ]
    
    lines = text.split('\n')
    relevant = []
    for line in lines:
        line = line.strip()
        if len(line) < 20:
            continue
        if any(k in line.lower() for k in keywords):
            relevant.append(line[:200])
    
    return relevant

# ═══════════════════════════════════════════════════
# STUDY PHASES
# ═══════════════════════════════════════════════════

async def study_videos(ws_url):
    """Extract video content from TradingView (webinars, analysis videos)."""
    print("🎬 FASE 1: Vídeos e Webinars...")
    
    urls = [
        ('https://br.tradingview.com/videos/', 'Vídeos em destaque'),
        ('https://br.tradingview.com/ideas/video/', 'Ideias em vídeo'),
        ('https://br.tradingview.com/education/', 'Educacional'),
    ]
    
    for url, label in urls:
        try:
            await cdp_navigate(ws_url, url, wait=4)
            
            # Screenshot + OCR
            screenshot = await cdp_screenshot(ws_url, f"tv_{label.lower().replace(' ','_')}.png")
            if screenshot:
                text = ocr_image(screenshot)
                knowledge = extract_trading_knowledge(text)
                
                if knowledge:
                    summary = f"TRADINGVIEW {label.upper()}: {len(knowledge)} insights via OCR. {' | '.join(knowledge[:5][:400])}"
                    write_bridge(summary)
                    discoveries.append(summary[:200])
                    print(f"  ✅ {label}: {len(knowledge)} insights")
                else:
                    # Try DOM as fallback
                    dom_text = await cdp_evaluate(ws_url, "document.body ? document.body.innerText.substring(0, 3000) : ''")
                    if dom_text and len(dom_text) > 100:
                        knowledge = extract_trading_knowledge(dom_text)
                        if knowledge:
                            summary = f"TRADINGVIEW {label.upper()}: {len(knowledge)} insights via DOM. {' | '.join(knowledge[:5][:400])}"
                            write_bridge(summary)
                            discoveries.append(summary[:200])
                            print(f"  ✅ {label}: {len(knowledge)} insights (DOM)")
                        else:
                            print(f"  ⚠️ {label}: sem conteúdo relevante")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"  ⚠️ {label}: {e}")

async def study_pine_editor(ws_url):
    """Deep study of Pine Script editor and popular strategies."""
    print("\n📜 FASE 2: Pine Script Editor...")
    
    # Pine Script v5 documentation
    await cdp_navigate(ws_url, 'https://br.tradingview.com/pine-script-docs/en/v5/', wait=3)
    
    # Screenshot + OCR
    screenshot = await cdp_screenshot(ws_url, "pine_script_docs.png")
    if screenshot:
        text = ocr_image(screenshot)
        knowledge = extract_trading_knowledge(text)
        
        # Also try to get structured data from the page
        dom_text = await cdp_evaluate(ws_url, """
        (function() {
            var items = document.querySelectorAll('a[href*="strategy"], a[href*="indicator"]');
            var result = [];
            items.forEach(function(a) { result.push(a.innerText.trim()); });
            return result.slice(0, 20).join(' | ');
        })()
        """)
        
        total_insights = len(knowledge)
        if dom_text and len(dom_text) > 10:
            total_insights += 1
        
        summary = f"TRADINGVIEW PINE SCRIPT v5: {total_insights} tópicos. Funções: {dom_text[:300] if dom_text else 'N/A'}"
        write_bridge(summary)
        discoveries.append(summary[:200])
        print(f"  ✅ {len(knowledge)} insights Pine Script")

async def study_ideas_deep(ws_url):
    """Deep study of trading ideas with multiple approaches."""
    print("\n💡 FASE 3: Ideias de Trading (análise profunda)...")
    
    sections = [
        ('https://br.tradingview.com/ideas/forex/', 'Forex'),
        ('https://br.tradingview.com/ideas/technical-analysis/', 'Análise Técnica'),
        ('https://br.tradingview.com/ideas/indicators/', 'Indicadores'),
    ]
    
    for url, label in sections:
        try:
            await cdp_navigate(ws_url, url, wait=4)
            
            # Screenshot + OCR
            screenshot = await cdp_screenshot(ws_url, f"ideas_{label.lower().replace(' ','_')}.png")
            
            # DOM extraction for structured data
            ideas = await cdp_evaluate(ws_url, """
            (function() {
                var cards = document.querySelectorAll('[data-testid="idea-card"], .tv-card, article');
                var result = [];
                cards.forEach(function(c) {
                    var title = c.querySelector('h3, h2, [class*="title"]')?.innerText || '';
                    var desc = c.querySelector('p, [class*="description"]')?.innerText || '';
                    if (title) result.push(title + ': ' + desc.substring(0, 150));
                });
                return result.slice(0, 10).join(' ||| ');
            })()
            """)
            
            if ideas and len(ideas) > 20:
                knowledge = extract_trading_knowledge(ideas)
                summary = f"TRADINGVIEW IDEIAS {label}: {len(knowledge)} relevantes. {ideas[:400]}"
                write_bridge(summary)
                discoveries.append(summary[:200])
                print(f"  ✅ {label}: {len(knowledge)} ideias")
            elif screenshot:
                text = ocr_image(screenshot)
                knowledge = extract_trading_knowledge(text)
                if knowledge:
                    summary = f"TRADINGVIEW IDEIAS {label} (OCR): {len(knowledge)} insights. {' | '.join(knowledge[:5][:400])}"
                    write_bridge(summary)
                    discoveries.append(summary[:200])
                    print(f"  ✅ {label} (OCR): {len(knowledge)} insights")
                else:
                    print(f"  ⚠️ {label}: sem conteúdo")
            
            await asyncio.sleep(2)
        except Exception as e:
            print(f"  ⚠️ {label}: {e}")

async def study_markets(ws_url):
    """Study market overview and key data."""
    print("\n📊 FASE 4: Visão geral de mercados...")
    
    await cdp_navigate(ws_url, 'https://br.tradingview.com/markets/forex/', wait=4)
    
    # Extract forex market data
    forex_data = await cdp_evaluate(ws_url, """
    (function() {
        var rows = document.querySelectorAll('tr');
        var result = [];
        rows.forEach(function(r) {
            var text = r.innerText.trim();
            if (text.length > 10 && text.length < 200) result.push(text);
        });
        return result.slice(0, 30).join(' | ');
    })()
    """)
    
    if forex_data:
        summary = f"TRADINGVIEW FOREX MARKET: {forex_data[:500]}"
        write_bridge(summary)
        discoveries.append(summary[:200])
        print(f"  ✅ Dados de mercado extraídos")
    
    # Economic calendar deep
    await cdp_navigate(ws_url, 'https://br.tradingview.com/economic-calendar/', wait=4)
    
    calendar = await cdp_evaluate(ws_url, """
    (function() {
        var events = document.querySelectorAll('[data-testid="calendar-row"], tr[class*="row"]');
        var result = [];
        events.forEach(function(e) {
            var t = e.innerText.trim();
            if (t.length > 20 && t.length < 300) result.push(t.substring(0, 200));
        });
        return result.slice(0, 20).join(' || ');
    })()
    """)
    
    if calendar and len(calendar) > 50:
        summary = f"TRADINGVIEW CALENDÁRIO ECONÔMICO: {calendar[:500]}"
        write_bridge(summary)
        discoveries.append(summary[:200])
        print(f"  ✅ Calendário econômico extraído")

async def study_news(ws_url):
    """Study market news and sentiment."""
    print("\n📰 FASE 5: Notícias e sentimento...")
    
    await cdp_navigate(ws_url, 'https://br.tradingview.com/news/', wait=4)
    
    # Screenshot for OCR
    screenshot = await cdp_screenshot(ws_url, "market_news.png")
    
    # DOM extraction
    news = await cdp_evaluate(ws_url, """
    (function() {
        var items = document.querySelectorAll('article, [class*="news"], [class*="story"]');
        var result = [];
        items.forEach(function(item) {
            var t = item.innerText.trim();
            if (t.length > 30 && t.length < 400) result.push(t.substring(0, 300));
        });
        return result.slice(0, 15).join(' ||| ');
    })()
    """)
    
    if news and len(news) > 50:
        knowledge = extract_trading_knowledge(news)
        summary = f"TRADINGVIEW NOTÍCIAS: {len(knowledge)} relevantes para trading. {news[:500]}"
        write_bridge(summary)
        discoveries.append(summary[:200])
        print(f"  ✅ {len(knowledge)} notícias relevantes")
    elif screenshot:
        text = ocr_image(screenshot)
        knowledge = extract_trading_knowledge(text)
        if knowledge:
            summary = f"TRADINGVIEW NOTÍCIAS (OCR): {len(knowledge)} insights. {' | '.join(knowledge[:5][:400])}"
            write_bridge(summary)
            discoveries.append(summary[:200])
            print(f"  ✅ (OCR) {len(knowledge)} notícias")

async def main():
    print("🧠 BRAIN STUDY v2: TradingView Deep Extraction")
    print(f"📁 {STUDY_DIR}\n")
    
    try:
        ws_url = await get_tv_ws()
        print("✅ TradingView conectado\n")
    except Exception as e:
        print(f"❌ Falha: {e}")
        return
    
    # Study phases
    await study_videos(ws_url)
    await study_pine_editor(ws_url)
    await study_ideas_deep(ws_url)
    await study_markets(ws_url)
    await study_news(ws_url)
    
    # Save session
    session = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'platform': 'TradingView',
        'version': 'v2-deep',
        'discoveries': len(discoveries),
        'topics': discoveries,
        'screenshots': len(list(SCREENSHOT_DIR.glob('*.png'))),
    }
    
    session_file = STUDY_DIR / 'tradingview_study_v2.json'
    session_file.write_text(json.dumps(session, indent=2, ensure_ascii=False))
    
    # Final summary
    final = f"TRADINGVIEW DEEP STUDY v2: {len(discoveries)} descobertas. Vídeos, Pine Script, ideias, mercados, notícias, calendário. Screenshots+OCR+DOM combinados. {session_file}"
    write_bridge(final)
    
    # NN absorb
    os.system(f"cd {HERMES} && python3 scripts/nn_engine.py absorb 2>/dev/null")
    
    print(f"\n✅ Concluído: {len(discoveries)} descobertas")
    print(f"📁 {session_file}")
    print(f"📸 {session['screenshots']} screenshots")

asyncio.run(main())
