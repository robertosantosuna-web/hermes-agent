#!/usr/bin/env python3
"""Cria repo no GitHub via Brave CDP WebSocket"""
import asyncio, json, urllib.request, time

CDP = 'http://localhost:9222'

async def create_repo():
    import websockets
    
    # Encontrar tab do github.com/new
    tabs = json.loads(urllib.request.urlopen(f'{CDP}/json/list').read())
    tab = None
    for t in tabs:
        if 'github.com/new' in t.get('url', ''):
            tab = t
            break
    
    if not tab:
        print("Tab github.com/new não encontrada. Abrindo...")
        req = urllib.request.Request(f'{CDP}/json/new?https://github.com/new', method='PUT')
        tab = json.loads(urllib.request.urlopen(req, timeout=5).read())
        await asyncio.sleep(4)
    
    ws_url = tab['webSocketDebuggerUrl']
    print(f'Conectando: {tab["url"][:60]}...')
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        # Enable Runtime
        await ws.send(json.dumps({'id':1, 'method':'Runtime.enable'}))
        resp = json.loads(await ws.recv())
        
        # Verificar se está logado
        await ws.send(json.dumps({'id':2, 'method':'Runtime.evaluate',
            'params':{'expression': '''
                (function(){
                    var el = document.querySelector('input[name="repository[name]"]');
                    if (el) return JSON.stringify({ready:true, placeholder: el.placeholder, value: el.value});
                    var login = document.querySelector('.logged-in');
                    if (login) return JSON.stringify({ready:false, reason:'campo nao encontrado, mas logado'});
                    return JSON.stringify({ready:false, reason:'nao logado', title: document.title});
                })()
            ''', 'returnByValue': True}}))
        resp = json.loads(await ws.recv())
        result = resp.get('result',{}).get('result',{}).get('value','{}')
        data = json.loads(result)
        print(f'Status: {data}')
        
        if data.get('ready'):
            # Preencher nome do repo
            repo_name = 'hermes-agent'
            print(f'Preenchendo nome: {repo_name}')
            
            # Clicar no campo primeiro
            await ws.send(json.dumps({'id':3, 'method':'Runtime.evaluate',
                'params':{'expression': f'''
                    (function(){{
                        var el = document.querySelector('input[name="repository[name]"]');
                        if (!el) return 'not found';
                        el.focus();
                        el.select();
                        // Usar React value setter
                        var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                        nativeInputValueSetter.call(el, '{repo_name}');
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return 'filled: ' + el.value;
                    }})()
                ''', 'returnByValue': True}}))
            resp = json.loads(await ws.recv())
            result = resp.get('result',{}).get('result',{}).get('value','?')
            print(f'Preenchimento: {result}')
            
            await asyncio.sleep(1)
            
            # Clicar Create repository
            await ws.send(json.dumps({'id':4, 'method':'Runtime.evaluate',
                'params':{'expression': '''
                    (function(){
                        var btns = document.querySelectorAll('button');
                        for (var i = 0; i < btns.length; i++) {
                            if (btns[i].textContent.includes('Create repository')) {
                                btns[i].click();
                                return 'clicked';
                            }
                        }
                        return 'button not found. Buttons: ' + Array.from(btns).map(b => b.textContent.trim()).join(', ');
                    })()
                ''', 'returnByValue': True}}))
            resp = json.loads(await ws.recv())
            result = resp.get('result',{}).get('result',{}).get('value','?')
            print(f'Clique: {result}')
            
            await asyncio.sleep(3)
            
            # Verificar resultado
            await ws.send(json.dumps({'id':5, 'method':'Runtime.evaluate',
                'params':{'expression': 'window.location.href', 'returnByValue': True}}))
            resp = json.loads(await ws.recv())
            url = resp.get('result',{}).get('result',{}).get('value','?')
            print(f'URL final: {url}')
            
            if 'hermes-agent' in str(url):
                print('\n✅ REPO CRIADO!')
                return True
        else:
            print('GitHub não está logado ou campo não encontrado.')
    
    return False

asyncio.run(create_repo())
