#!/usr/bin/env python3
"""Extrai velas da tab TV EXISTENTE (já logada) no Brave :9222"""
import asyncio, json, sys, urllib.request

CDP = 'http://localhost:9222'
PAIR = sys.argv[1] if len(sys.argv) > 1 else 'EURUSD'

async def extract():
    import websockets
    
    tabs = json.loads(urllib.request.urlopen(f'{CDP}/json/list').read())
    
    # Encontrar tab TV com o par
    sym_map = {'EURUSD':'EURUSD','GBPUSD':'GBPUSD','USDJPY':'USDJPY',
               'GBPJPY':'GBPJPY','EURJPY':'EURJPY','USDCAD':'USDCAD','XAUUSD':'GOLD'}
    target = sym_map.get(PAIR.upper(), PAIR.upper())
    
    tab = None
    for t in tabs:
        url = t.get('url','')
        if 'tradingview.com/chart' in url:
            print(f'Tab TV: {url[:80]}...')
            tab = t
            break
    
    if not tab:
        print('Nenhuma tab TV'); return
    
    ws_url = tab['webSocketDebuggerUrl']
    print(f'Conectando...')
    
    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        await ws.send(json.dumps({'id':1,'method':'Runtime.enable'}))
        await ws.recv()
        
        # Navegar para o símbolo correto com M1
        sym_tv = {'EURUSD':'FX:EURUSD','GBPUSD':'FX:GBPUSD','USDJPY':'FX:USDJPY',
                  'GBPJPY':'FX:GBPJPY','EURJPY':'FX:EURJPY','USDCAD':'FX:USDCAD',
                  'XAUUSD':'TVC:GOLD'}.get(PAIR.upper(), f'FX:{PAIR.upper()}')
        
        await ws.send(json.dumps({'id':1,'method':'Page.enable'}))
        await ws.recv()
        
        sym_tv_escaped = sym_tv.replace(':', '%3A')
        chart_url = f'https://www.tradingview.com/chart/?symbol={sym_tv_escaped}&interval=1'
        await ws.send(json.dumps({'id':2,'method':'Page.navigate','params':{'url':chart_url}}))
        await ws.recv()
        print(f'Navegando para {sym_tv} M1...')
        await asyncio.sleep(8)
        
        # Verificar se carregou e extrair
        for attempt in range(8):
            await asyncio.sleep(2)
            js = '''
            (function(){
                try {
                    var cc = window._exposed_chartWidgetCollection;
                    if (!cc) return JSON.stringify({ready:false, reason:'no collection'});
                    
                    for (var k in cc) {
                        try {
                            var w = cc[k];
                            var chart = w._chart || (w.chart ? w.chart() : null);
                            if (!chart) continue;
                            
                            // Verificar métodos disponíveis
                            var methods = Object.keys(chart).filter(function(m) {
                                return typeof chart[m] === 'function' && (
                                    m.includes('bar') || m.includes('data') || 
                                    m.includes('series') || m.includes('ohlc') ||
                                    m.includes('price') || m.includes('candle')
                                );
                            });
                            
                            // Tentar dataFeed
                            var sym = w._symbol || (w.symbol ? w.symbol() : null);
                            var symName = sym ? (sym.full_name || sym.description || sym) : '?';
                            
                            return JSON.stringify({
                                ready: true,
                                symbol: symName,
                                methods: methods,
                                allMethods: Object.keys(chart).filter(function(m) {
                                    return typeof chart[m] === 'function';
                                }).slice(0, 30)
                            });
                        } catch(e) {}
                    }
                    return JSON.stringify({ready:false, reason:'no widget with chart'});
                } catch(e) { return JSON.stringify({ready:false, err:e.message}); }
            })()
            '''
            await ws.send(json.dumps({'id':100+attempt,'method':'Runtime.evaluate',
                'params':{'expression':js,'returnByValue':True}}))
            resp = json.loads(await ws.recv())
            val = resp.get('result',{}).get('result',{}).get('value','{}')
            try:
                data = json.loads(val)
                if data.get('ready'):
                    print(f'Symbol: {data.get("symbol")}')
                    print(f'Bar/data methods: {data.get("methods")}')
                    print(f'All methods: {data.get("allMethods", [])[:15]}')
                    
                    # Tentar acessar data via symbol
                    js2 = '''
                    (function(){
                        try {
                            var cc = window._exposed_chartWidgetCollection;
                            for (var k in cc) {
                                var w = cc[k];
                                if (!w._datafeed) continue;
                                return JSON.stringify({
                                    hasDatafeed: true,
                                    dfMethods: Object.keys(w._datafeed).slice(0, 20)
                                });
                            }
                            return JSON.stringify({hasDatafeed: false});
                        } catch(e) { return JSON.stringify({err: e.message}); }
                    })()
                    '''
                    await ws.send(json.dumps({'id':999,'method':'Runtime.evaluate',
                        'params':{'expression':js2,'returnByValue':True}}))
                    resp = json.loads(await ws.recv())
                    val2 = resp.get('result',{}).get('result',{}).get('value','{}')
                    print(f'Datafeed: {val2[:400]}')
                    return
                else:
                    print(f'  {attempt+1}: {data.get("reason", data.get("err", "?"))}')
            except Exception as e:
                print(f'  parse error: {e}')

asyncio.run(extract())
