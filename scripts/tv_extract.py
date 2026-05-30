#!/usr/bin/env python3
"""
Extrai velas M1 do TradingView via CDP WebSocket.
Uso: python3 tv_extract.py EURUSD 60  (60 velas)
"""
import asyncio, json, sys, os, urllib.request
from datetime import datetime
from pathlib import Path

CDP = 'http://localhost:9222'
SYMBOLS_TV = {
    'EURUSD': 'FX%3AEURUSD', 'GBPUSD': 'FX%3AGBPUSD', 'USDJPY': 'FX%3AUSDJPY',
    'GBPJPY': 'FX%3AGBPJPY', 'EURJPY': 'FX%3AEURJPY', 'USDCAD': 'FX%3AUSDCAD',
    'XAUUSD': 'TVC%3AGOLD',
}

PAIR = sys.argv[1] if len(sys.argv) > 1 else 'EURUSD'
COUNT = int(sys.argv[2]) if len(sys.argv) > 2 else 100
SYM = SYMBOLS_TV.get(PAIR.upper(), f'FX%3A{PAIR.upper()}')

async def extract():
    import websockets
    
    # Abrir nova tab
    url = f'https://www.tradingview.com/chart/?symbol={SYM}&interval=1'
    req = urllib.request.Request(f'{CDP}/json/new?{url}', method='PUT')
    tab = json.loads(urllib.request.urlopen(req, timeout=5).read())
    ws_url = tab['webSocketDebuggerUrl']
    print(f'TradingView {PAIR} M1 — tab aberta')
    
    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        # Habilitar Runtime
        await ws.send(json.dumps({'id':1, 'method':'Runtime.enable'}))
        await ws.recv()
        
        # Esperar chart carregar (até 30s)
        print('Aguardando chart carregar...')
        for attempt in range(30):
            await asyncio.sleep(1)
            await ws.send(json.dumps({
                'id': 100+attempt, 
                'method': 'Runtime.evaluate',
                'params': {'expression': '''
                    (function(){
                        try {
                            var w = document.querySelector('.chart-container');
                            if (!w) return JSON.stringify({ready:false, reason:'no container'});
                            var series = document.querySelector('.sources-placeholder canvas');
                            if (!series) return JSON.stringify({ready:false, reason:'no canvas'});
                            return JSON.stringify({ready:true});
                        } catch(e) {
                            return JSON.stringify({ready:false, reason:e.message});
                        }
                    })()
                ''', 'returnByValue': True}
            }))
            resp = json.loads(await ws.recv())
            result = resp.get('result', {}).get('result', {}).get('value', '{}')
            if '"ready":true' in result:
                print('Chart carregado!')
                break
            if attempt % 5 == 0:
                print(f'  aguardando... ({attempt+1}s)')
        else:
            print('Timeout aguardando chart')
            return
        
        # Extrair dados via getBars
        print(f'Extraindo {COUNT} velas M1...')
        
        js = f'''
        (function(){{
            try {{
                var bars = [];
                var widget = window.tvWidget || window.widget;
                if (!widget) {{
                    // Tentar acessar via global
                    var iframes = document.querySelectorAll('iframe');
                    for (var f of iframes) {{
                        try {{
                            var w = f.contentWindow;
                            if (w.tvWidget) {{ widget = w.tvWidget; break; }}
                        }} catch(e) {{}}
                    }}
                }}
                
                if (!widget || !widget.chart) {{
                    return JSON.stringify({{error: 'widget not found', ok: false}});
                }}
                
                var chart = widget.chart();
                if (!chart) {{
                    return JSON.stringify({{error: 'chart() returned null', ok: false}});
                }}
                
                // Tentar acessar dados de velas
                var study = chart.getAllStudies ? chart.getAllStudies() : [];
                var symbol = chart.symbol ? chart.symbol() : null;
                var interval = chart.resolution ? chart.resolution() : '1';
                
                return JSON.stringify({{
                    ok: true,
                    symbol: symbol ? symbol.full_name : '?',
                    interval: interval,
                    studies: study.length,
                    hasGetBars: typeof chart.getBars === 'function',
                    methods: Object.keys(chart).filter(k => typeof chart[k] === 'function').slice(0,20)
                }});
            }} catch(e) {{
                return JSON.stringify({{error: e.message, ok: false}});
            }}
        }})()
        '''
        
        await ws.send(json.dumps({
            'id': 200, 'method': 'Runtime.evaluate',
            'params': {'expression': js, 'returnByValue': True}
        }))
        resp = json.loads(await ws.recv())
        result = resp.get('result', {}).get('result', {}).get('value', '{}')
        info = json.loads(result)
        print(json.dumps(info, indent=2))
        
        if info.get('ok'):
            print(f'\nSymbol: {info.get("symbol")} Interval: {info.get("interval")}')
            print(f'Methods available: {info.get("methods")}')
            print(f'Has getBars: {info.get("hasGetBars")}')

asyncio.run(extract())
