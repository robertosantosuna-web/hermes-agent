"""
Freelancer Onboarding Automation via CDP — Complete flow.
Completes all 9 onboarding pages automatically.
Requires: Edge running with --remote-debugging-port=9222
Usage: /usr/bin/python3 freelancer_onboarding.py
"""
import json, time, urllib.request, websocket, sys

BASE = 'http://localhost:9222'

def cdp_controller(ws_url):
    ws = websocket.create_connection(ws_url, timeout=15, origin=BASE)
    mid = [0]
    
    def cdp(method, params=None):
        mid[0] += 1
        ws.send(json.dumps({'id': mid[0], 'method': method, 'params': params or {}}))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == mid[0]:
                if 'error' in resp:
                    raise Exception(f"CDP Error: {resp['error']}")
                return resp.get('result', {})
    
    def ev(expr):
        return cdp('Runtime.evaluate', {'expression': expr, 'returnByValue': True}).get('result', {}).get('value')
    
    def click(x, y):
        cdp('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': x, 'y': y})
        time.sleep(0.05)
        cdp('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})
        time.sleep(0.05)
        cdp('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})
    
    def type_text(text):
        for char in text:
            cdp('Input.dispatchKeyEvent', {'type': 'keyDown', 'text': char, 'unmodifiedText': char, 'key': char})
            cdp('Input.dispatchKeyEvent', {'type': 'keyUp', 'text': char, 'unmodifiedText': char, 'key': char})
    
    def triple_click_and_type(pos, text):
        cdp('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': pos['x'], 'y': pos['y']})
        time.sleep(0.05)
        cdp('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': pos['x'], 'y': pos['y'], 'button': 'left', 'clickCount': 3})
        time.sleep(0.05)
        cdp('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': pos['x'], 'y': pos['y'], 'button': 'left', 'clickCount': 3})
        time.sleep(0.2)
        type_text(text)
    
    return cdp, ev, click, type_text, triple_click_and_type, ws


def click_bottom_button(ev, click, text):
    btns = ev(f'''
        (() => {{
            const all = document.querySelectorAll('button, a, [role="button"]');
            const c = [];
            for (const b of all) {{
                if (b.textContent.trim() === '{text}' && b.offsetParent) {{
                    const r = b.getBoundingClientRect();
                    c.push({{x: r.left + r.width/2, y: r.top + r.height/2, bottom: r.bottom}});
                }}
            }}
            c.sort((a,b) => b.bottom - a.bottom);
            return c;
        }})()
    ''')
    if btns:
        click(btns[0]['x'], btns[0]['y'])


def new_tab(url):
    req = urllib.request.Request(f'{BASE}/json/new?{url}', method='PUT')
    resp = json.loads(urllib.request.urlopen(req, timeout=8).read())
    return resp['webSocketDebuggerUrl']


def complete_skills():
    ws_url = new_tab('https://www.freelancer.com/new-freelancer/skills')
    cdp, ev, click, type_text, triple_and_type, ws = cdp_controller(ws_url)
    time.sleep(4)
    cdp('Runtime.enable')
    time.sleep(1)

    pos = ev('''
        (() => {
            const items = document.querySelectorAll("fl-list-item");
            for (const item of items) {
                if (item.textContent.includes("Websites, IT")) {
                    const h = item.querySelector(".BitsListItemHeader");
                    h.scrollIntoView({block: "center", behavior: "instant"});
                    const r = h.getBoundingClientRect();
                    return {x: r.left + r.width/2, y: r.top + r.height/2};
                }
            }
            return null;
        })()
    ''')
    if pos: click(pos['x'], pos['y'])
    time.sleep(2)

    for skill in ['Python', 'Automation', 'Web Scraping', 'API Development', 'Data Collection', 'Linux']:
        pos = ev(f'''
            (() => {{
                const items = document.querySelectorAll("fl-list-item");
                for (const item of items) {{
                    const t = item.textContent.trim();
                    if (t.startsWith("{skill}") && t.includes("jobs")) {{
                        const h = item.querySelector(".BitsListItemHeader");
                        h.scrollIntoView({{block: "center", behavior: "instant"}});
                        const r = h.getBoundingClientRect();
                        return {{x: r.left + r.width/2, y: r.top + r.height/2}};
                    }}
                }}
                return null;
            }})()
        ''')
        if pos: click(pos['x'], pos['y'])
        time.sleep(0.4)

    time.sleep(0.5)
    click_bottom_button(ev, click, 'Next')
    time.sleep(3)
    print(f"  -> {ev('window.location.href')}")
    ws.close()


def skip_page(keyword):
    pages = json.loads(urllib.request.urlopen(f'{BASE}/json', timeout=5).read())
    target = next((p for p in pages if keyword in p['url']), None)
    if not target:
        print(f"  Not on {keyword}")
        return

    cdp, ev, click, type_text, triple_and_type, ws = cdp_controller(target['webSocketDebuggerUrl'])
    cdp('Runtime.enable')
    time.sleep(0.5)

    pos = ev('''
        (() => {
            const all = document.querySelectorAll('button, a, [role="button"]');
            for (const b of all) {
                const t = b.textContent.trim();
                if ((t === 'Skip' || t === 'Next') && b.offsetParent) {
                    b.scrollIntoView({block: "center"});
                    const r = b.getBoundingClientRect();
                    return {x: r.left + r.width/2, y: r.top + r.height/2};
                }
            }
            return null;
        })()
    ''')

    if pos: click(pos['x'], pos['y'])
    time.sleep(3)
    print(f"  -> {ev('window.location.href')}")
    ws.close()


def fill_name():
    pages = json.loads(urllib.request.urlopen(f'{BASE}/json', timeout=5).read())
    target = next((p for p in pages if 'photo-and-name' in p['url']), None)
    if not target: return print("  Not on name page")

    cdp, ev, click, type_text, triple_and_type, ws = cdp_controller(target['webSocketDebuggerUrl'])
    cdp('Runtime.enable')
    time.sleep(0.5)

    ev('''
        (() => {
            const inputs = document.querySelectorAll("input");
            for (const inp of inputs) {
                const ph = (inp.placeholder || "").toLowerCase();
                const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
                if (ph.includes("first")) { setter.call(inp, "Roberto"); inp.dispatchEvent(new Event("input", {bubbles: true})); inp.dispatchEvent(new Event("change", {bubbles: true})); }
                if (ph.includes("last")) { setter.call(inp, "Rodrigues"); inp.dispatchEvent(new Event("input", {bubbles: true})); inp.dispatchEvent(new Event("change", {bubbles: true})); }
            }
            return "done";
        })()
    ''')
    time.sleep(0.5)
    click_bottom_button(ev, click, 'Next')
    time.sleep(3)
    print(f"  -> {ev('window.location.href')}")
    ws.close()


def complete_headline_and_summary():
    pages = json.loads(urllib.request.urlopen(f'{BASE}/json', timeout=5).read())
    target = next((p for p in pages if 'headline-and-summary' in p['url']), None)
    if not target: return print("  Not on headline page")

    cdp, ev, click, type_text, triple_and_type, ws = cdp_controller(target['webSocketDebuggerUrl'])
    cdp('Runtime.enable')
    time.sleep(0.5)

    pos = ev('''
        (() => {
            const inp = document.querySelector('fl-input .NativeElement');
            if (!inp) return null;
            inp.scrollIntoView({block: "center"});
            const r = inp.getBoundingClientRect();
            return {x: r.left + r.width/2, y: r.top + r.height/2};
        })()
    ''')
    if pos: triple_and_type(pos, 'Python Developer & Automation Specialist'); time.sleep(0.3)

    pos = ev('''
        (() => {
            const ta = document.querySelector('textarea.TextArea');
            if (!ta) return null;
            ta.scrollIntoView({block: "center"});
            const r = ta.getBoundingClientRect();
            return {x: r.left + r.width/2, y: r.top + r.height/2};
        })()
    ''')
    if pos: triple_and_type(pos, 'I build automation solutions, web scrapers, and API integrations with Python. Fast delivery, clean code, Linux systems.'); time.sleep(0.3)

    click_bottom_button(ev, click, 'Next')
    time.sleep(3)
    print(f"  -> {ev('window.location.href')}")
    ws.close()


def complete_languages_birthdate():
    pages = json.loads(urllib.request.urlopen(f'{BASE}/json', timeout=5).read())
    target = next((p for p in pages if 'languages-and-birthdate' in p['url']), None)
    if not target: return print("  Not on languages page")

    cdp, ev, click, type_text, triple_and_type, ws = cdp_controller(target['webSocketDebuggerUrl'])
    cdp('Runtime.enable')
    time.sleep(0.5)

    pos = ev('''
        (() => {
            const inp = document.querySelector('input:not([type="hidden"])');
            if (!inp) return null;
            inp.scrollIntoView({block: "center"});
            const r = inp.getBoundingClientRect();
            return {x: r.left + r.width/2, y: r.top + r.height/2};
        })()
    ''')
    if pos:
        click(pos['x'], pos['y']); time.sleep(0.3)
        type_text('Portugu'); time.sleep(0.5)
        cdp('Input.dispatchKeyEvent', {'type': 'keyDown', 'key': 'Enter'})
        cdp('Input.dispatchKeyEvent', {'type': 'keyUp', 'key': 'Enter'})
        time.sleep(0.5)
        type_text('Ingl'); time.sleep(0.5)
        cdp('Input.dispatchKeyEvent', {'type': 'keyDown', 'key': 'Enter'})
        cdp('Input.dispatchKeyEvent', {'type': 'keyUp', 'key': 'Enter'})
        time.sleep(0.5)

    pos = ev('''
        (() => {
            const inp = document.getElementById('inputBirthdate');
            if (!inp) return null;
            inp.scrollIntoView({block: "center"});
            const r = inp.getBoundingClientRect();
            return {x: r.left + r.width/2, y: r.top + r.height/2};
        })()
    ''')
    if pos: click(pos['x'], pos['y']); time.sleep(0.3); type_text('01/15/1990'); time.sleep(0.3)

    click_bottom_button(ev, click, 'Next')
    time.sleep(3)
    print(f"  -> {ev('window.location.href')}")
    ws.close()


def click_finish():
    pages = json.loads(urllib.request.urlopen(f'{BASE}/json', timeout=5).read())
    target = next((p for p in pages if 'references' in p['url']), None)
    if not target: return print("  Not on references page")

    cdp, ev, click, type_text, triple_and_type, ws = cdp_controller(target['webSocketDebuggerUrl'])
    cdp('Runtime.enable')
    time.sleep(0.5)

    pos = ev('''
        (() => {
            const btns = document.querySelectorAll('button');
            for (const b of btns) {
                if (b.textContent.trim() === 'Finish' && b.offsetParent) {
                    b.scrollIntoView({block: "center"});
                    const r = b.getBoundingClientRect();
                    return {x: r.left + r.width/2, y: r.top + r.height/2};
                }
            }
            return null;
        })()
    ''')

    if pos: click(pos['x'], pos['y']); time.sleep(3)
    print(f"  -> {ev('window.location.href')}")
    ws.close()


if __name__ == '__main__':
    print("=== Freelancer Onboarding ===\n")
    try:
        pages = json.loads(urllib.request.urlopen(f'{BASE}/json', timeout=5).read())
        print(f"CDP: {len(pages)} tabs\n")
    except:
        print("ERROR: Edge CDP not available"); sys.exit(1)

    complete_skills()
    skip_page('linked-accounts')
    fill_name()
    complete_headline_and_summary()
    complete_languages_birthdate()
    skip_page('payment-verification')
    skip_page('membership-offer')
    skip_page('experiences')
    click_finish()
    print("\nDone.")
