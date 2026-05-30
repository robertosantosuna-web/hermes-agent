#!/usr/bin/env python3
"""
CDP FUTURES EXECUTOR — Contorna bloqueio Brasil na API Binance.
Controla a interface Futures via Edge CDP (porta 9224).
"""
import json, requests, websocket, time, math
from pathlib import Path

CDP_LIST = 'http://localhost:9224/json/list'
FUTURES_URL = 'https://www.binance.com/en/futures/{pair}'

class CDPFuturesExecutor:
    """Executa ordens futures via navegador Edge."""
    
    def __init__(self):
        self.ws = None
        self._pair = None
        self._msg_id = 0
    
    def _connect(self, pair='BNBUSDT'):
        """Conecta na aba Binance Futures do Edge."""
        if self.ws and self._pair == pair:
            try:
                self.ws.ping()
                return
            except:
                self.ws = None
        
        tabs = requests.get(CDP_LIST).json()
        for t in tabs:
            if 'binance.com' in t.get('url', ''):
                url = f'https://www.binance.com/en/futures/{pair}'
                self.ws = websocket.create_connection(
                    t['webSocketDebuggerUrl'], timeout=10
                )
                # Navegar para o par e esperar carregar
                self.ws.send(json.dumps({
                    'id': self._next_id(), 'method': 'Page.navigate',
                    'params': {'url': url}
                }))
                json.loads(self.ws.recv())
                time.sleep(6)  # Esperar página carregar totalmente
                
                # Confirmar que carregou verificando Avbl
                for attempt in range(10):
                    bal = self.get_balance()
                    if bal > 0:
                        break
                    time.sleep(1)
                
                self._pair = pair
                return
        
        raise Exception('Binance Futures tab not found in Edge')
    
    def _next_id(self):
        self._msg_id += 1
        return self._msg_id
    
    def _eval(self, expr):
        """Executa JS e retorna resultado."""
        self.ws.send(json.dumps({
            'id': self._next_id(),
            'method': 'Runtime.evaluate',
            'params': {'expression': expr, 'returnByValue': True}
        }))
        resp = json.loads(self.ws.recv())
        return resp.get('result', {}).get('result', {}).get('value')
    
    # ═══ LEITURA ═══
    
    def get_balance(self):
        """Saldo disponível em USDT."""
        result = self._eval(
            'document.body.innerText.match(/Avbl\\s+([\\d.]+)\\s*USDT/)'
        )
        if result and len(result) > 1:
            return float(result[1])
        return 0.0
    
    def get_leverage(self):
        """Alavancagem atual."""
        result = self._eval(
            'document.body.innerText.match(/(\\d+)x/)'
        )
        return int(result[1]) if result and len(result) > 1 else 5
    
    def get_position(self):
        """Informação da posição aberta (PnL, size, entry price)."""
        return self._eval('''
            (() => {
                const text = document.body.innerText;
                // Procurar seção de posição
                const m = text.match(/Unrealized PnL[\\s\\S]*?(?=Open Orders|Assets)/);
                if (!m) return null;
                const section = m[0];
                const pnl = section.match(/([+-]?[\\d.]+)\\s*USDT/);
                const size = section.match(/([\\d.]+)\\s*(BNB|BTC|ETH|DOGE)/i);
                return {
                    pnl: pnl ? pnl[1] : '?',
                    size: size ? size[0] : '?',
                    raw: section.substring(0, 200)
                };
            })()
        ''')
    
    # ═══ EXECUÇÃO ═══
    
    def set_leverage(self, leverage=5):
        """Configura alavancagem. Clica no seletor e ajusta."""
        # Clicar no seletor de leverage
        current = self._eval('''
            (() => {
                const all = document.querySelectorAll('*');
                for (const el of all) {
                    const t = (el.innerText || '').trim();
                    if (/^\\d+x$/.test(t) && el.offsetWidth > 0 && el.offsetWidth < 60) {
                        el.click();
                        return t;
                    }
                }
                return null;
            })()
        ''')
        time.sleep(2)
        
        # Preencher novo valor
        self._eval(f'''
            (() => {{
                const inputs = document.querySelectorAll('input[type="number"]');
                for (const i of inputs) {{
                    if (i.offsetWidth > 0 && i.value) {{
                        const ns = Object.getOwnPropertyDescriptor(
                            HTMLInputElement.prototype, 'value').set;
                        ns.call(i, '{leverage}');
                        i.dispatchEvent(new Event('input', {{bubbles: true}}));
                        i.dispatchEvent(new Event('change', {{bubbles: true}}));
                        
                        // Clicar Confirm
                        setTimeout(() => {{
                            const btns = document.querySelectorAll('button');
                            for (const b of btns) {{
                                if (b.innerText.trim() === 'Confirm' && b.offsetWidth > 0) {{
                                    b.click();
                                }}
                            }}
                        }}, 500);
                        
                        return 'SET ' + i.value;
                    }}
                }}
                return 'NOT FOUND';
            }})()
        ''')
        time.sleep(3)
        return self.get_leverage()
    
    def market_order(self, pair, direction, usdt_amount):
        """
        Executa ordem a mercado.
        direction: 'BUY' ou 'SELL'
        usdt_amount: tamanho em USDT
        """
        if self._pair != pair:
            self._connect(pair)
        
        # Garantir modo Market
        self._eval('''
            (() => {
                const all = document.querySelectorAll('div, span, button');
                for (const el of all) {
                    if ((el.innerText || '').trim() === 'Market' && 
                        el.offsetWidth > 10 && el.offsetWidth < 100) {
                        el.click();
                        return;
                    }
                }
            })()
        ''')
        time.sleep(1)
        
        # Preencher quantidade
        self._eval(f'''
            (() => {{
                const inputs = document.querySelectorAll('input');
                for (const i of inputs) {{
                    if (i.placeholder === 'Enter Size' && i.offsetWidth > 0) {{
                        const ns = Object.getOwnPropertyDescriptor(
                            HTMLInputElement.prototype, 'value').set;
                        ns.call(i, '{usdt_amount}');
                        i.dispatchEvent(new Event('input', {{bubbles: true}}));
                        i.dispatchEvent(new Event('change', {{bubbles: true}}));
                        return 'SET ' + i.value;
                    }}
                }}
                return 'NOT FOUND';
            }})()
        ''')
        time.sleep(0.5)
        
        # Clicar Buy/Long ou Sell/Short
        btn_text = 'Buy/Long' if direction == 'BUY' else 'Sell/Short'
        result = self._eval(f'''
            (() => {{
                const btns = document.querySelectorAll('button');
                for (const b of btns) {{
                    if ((b.innerText || '').trim() === '{btn_text}' && b.offsetWidth > 0) {{
                        b.click();
                        return 'CLICKED';
                    }}
                }}
                return 'NOT FOUND';
            }})()
        ''')
        time.sleep(3)
        
        # Verificar se abriu posição
        pos = self.get_position()
        balance = self.get_balance()
        
        return {
            'success': result == 'CLICKED',
            'direction': direction,
            'amount': usdt_amount,
            'balance_after': balance,
            'position': pos
        }
    
    def close_position(self):
        """Fecha posição atual (abre ordem inversa do mesmo tamanho)."""
        pos = self.get_position()
        if not pos:
            return {'success': False, 'error': 'No position'}
        
        # Determinar direção inversa e tamanho
        section = pos.get('raw', '')
        is_long = 'Long' in section
        
        # Extrair quantidade
        import re
        size_m = re.search(r'([\d.]+)\s*(BNB|BTC|ETH|DOGE)', section)
        if not size_m:
            return {'success': False, 'error': 'Could not parse size'}
        
        qty = size_m.group(1)
        
        # Clicar Market, preencher qty, clicar na direção inversa
        self._eval('''
            (() => {
                const all = document.querySelectorAll('div, span, button');
                for (const el of all) {
                    if ((el.innerText || '').trim() === 'Market' && 
                        el.offsetWidth > 10 && el.offsetWidth < 100) {
                        el.click();
                    }
                }
            })()
        ''')
        time.sleep(1)
        
        self._eval(f'''
            (() => {{
                const inputs = document.querySelectorAll('input');
                for (const i of inputs) {{
                    if (i.placeholder === 'Enter Size' && i.offsetWidth > 0) {{
                        const ns = Object.getOwnPropertyDescriptor(
                            HTMLInputElement.prototype, 'value').set;
                        ns.call(i, '{qty}');
                        i.dispatchEvent(new Event('input', {{bubbles: true}}));
                        return;
                    }}
                }}
            }})()
        ''')
        time.sleep(0.5)
        
        close_btn = 'Sell/Short' if is_long else 'Buy/Long'
        self._eval(f'''
            (() => {{
                const btns = document.querySelectorAll('button');
                for (const b of btns) {{
                    if ((b.innerText || '').trim() === '{close_btn}' && b.offsetWidth > 0) {{
                        b.click();
                        return;
                    }}
                }}
            }})()
        ''')
        time.sleep(3)
        
        return {
            'success': True,
            'closed': True,
            'balance_after': self.get_balance()
        }
    
    def close(self):
        if self.ws:
            self.ws.close()
            self.ws = None


if __name__ == '__main__':
    # Teste rápido
    ex = CDPFuturesExecutor()
    ex._connect('BNBUSDT')
    print(f'Balance: ${ex.get_balance():.2f}')
    print(f'Leverage: {ex.get_leverage()}x')
    pos = ex.get_position()
    print(f'Position: {pos}')
    ex.close()
