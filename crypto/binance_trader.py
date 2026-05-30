#!/usr/bin/env python3
"""
BINANCE INTEGRATION — Guia e Módulo de Conexão
=============================================

## O que precisa:

### 1. Conta na Binance
- Criar em binance.com (já tem? verificar)
- Fazer KYC (identidade) — obrigatório para trading
- Depositar via Pix (mínimo ~R$50)

### 2. API Keys
- Acessar: binance.com → Perfil → API Management
- Criar "System generated" API key
- Permissões necessárias:
  ✅ Enable Spot & Margin Trading
  ❌ Enable Withdrawals (NUNCA marcar!)
- Restringir acesso IP (opcional, mais seguro)
- Guardar: API Key + Secret Key

### 3. Biblioteca Python
- Opção 1 (recomendada): python-binance
  pip install python-binance
  
- Opção 2 (oficial): binance-connector  
  pip install binance-connector

- Opção 3 (multi-exchange): ccxt
  pip install ccxt

### 4. Testnet (testar sem dinheiro)
- Spot Testnet: https://testnet.binance.vision/
- Criar conta separada, gerar API keys
- URL: https://testnet.binance.vision/api

### 5. Pares disponíveis (USDT)
BTCUSDT, ETHUSDT, DOGEUSDT, BNBUSDT, SOLUSDT, etc
- Tick size e step size variam por par
- Buscar via GET /api/v3/exchangeInfo

### 6. Ordem de mercado (exemplo python-binance)
```python
from binance.client import Client
client = Client(api_key, api_secret)

# Comprar quantidade em USDT
order = client.order_market_buy(
    symbol='BTCUSDT',
    quoteOrderQty=10  # $10 em BTC
)

# Vender
order = client.order_market_sell(
    symbol='BTCUSDT', 
    quantity=0.0001  # quantidade em BTC
)
```

### 7. Ordem OCO (SL + TP simultâneos)
```python
from binance.client import Client
order = client.order_oco_sell(
    symbol='BTCUSDT',
    quantity=0.0001,
    price=50000,       # TP
    stopPrice=48000,   # SL
    stopLimitPrice=47900
)
```

### 8. Taxas
- Spot: 0.1% maker/taker
- Com BNB: 0.075%
- Futures: mais barato (0.02%/0.04%)

### 9. Valor mínimo por ordem
- ~$10 USD equivalente
- Depende do par (verificar minNotional)

### 10. O que nosso bot precisa fazer:
1. Conectar na API com as keys
2. Buscar saldo USDT disponível
3. Calcular tamanho da posição (0.5% risco)
4. Enviar ordem OCO (entrada + SL + TP)
5. Monitorar posições abertas
6. Fechar quando SL/TP atingidos

## Configuração
Criar arquivo ~/.hermes/crypto/binance_config.json:
{
    "api_key": "SUA_API_KEY",
    "api_secret": "SUA_SECRET_KEY",
    "testnet": true,
    "max_risk_pct": 0.5,
    "max_position_usdt": 50
}
"""

# ═══ MÓDULO DE INTEGRAÇÃO ═══
import sys, json, os, time, hmac, hashlib
from pathlib import Path
from urllib.parse import urlencode
import requests

class BinanceTrader:
    """Cliente Binance para execução de trades."""
    
    def __init__(self, testnet=True):
        self.config_path = Path.home() / '.hermes' / 'crypto' / 'binance_config.json'
        self.testnet = testnet
        
        if self.testnet:
            self.base_url = 'https://testnet.binance.vision'
            self.ws_url = 'wss://testnet.binance.vision/ws'
        else:
            self.base_url = 'https://api.binance.com'
            self.ws_url = 'wss://stream.binance.com:9443/ws'
        
        self.api_key = None
        self.api_secret = None
        self._load_config()
    
    def _load_config(self):
        """Carrega API keys do arquivo de configuração."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    cfg = json.load(f)
                self.api_key = cfg.get('api_key', '')
                self.api_secret = cfg.get('api_secret', '')
                self.testnet = cfg.get('testnet', self.testnet)
                self.max_risk_pct = cfg.get('max_risk_pct', 0.5)
                self.max_position = cfg.get('max_position_usdt', 50)
            except Exception as e:
                print(f"⚠️ Erro ao carregar config: {e}")
    
    def _sign_request(self, params):
        """Assina requisição com HMAC SHA256."""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        params['signature'] = signature
        return params
    
    def _request(self, method, endpoint, signed=False, **params):
        """Faz requisição à API Binance."""
        url = f"{self.base_url}{endpoint}"
        headers = {'X-MBX-APIKEY': self.api_key}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params = self._sign_request(params)
        
        if method == 'GET':
            resp = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == 'POST':
            resp = requests.post(url, headers=headers, data=params, timeout=10)
        elif method == 'DELETE':
            resp = requests.delete(url, headers=headers, params=params, timeout=10)
        else:
            raise ValueError(f"Método inválido: {method}")
        
        if resp.status_code != 200:
            raise Exception(f"Binance API error {resp.status_code}: {resp.text}")
        
        return resp.json()
    
    # ═══ CONTA ═══
    
    def get_balance(self, asset='USDT'):
        """Retorna saldo disponível."""
        data = self._request('GET', '/api/v3/account', signed=True)
        for bal in data.get('balances', []):
            if bal['asset'] == asset:
                return float(bal['free'])
        return 0.0
    
    def get_account_info(self):
        """Informações completas da conta."""
        return self._request('GET', '/api/v3/account', signed=True)
    
    # ═══ MERCADO ═══
    
    def get_price(self, symbol):
        """Preço atual do par."""
        data = self._request('GET', '/api/v3/ticker/price', symbol=symbol)
        return float(data['price'])
    
    def get_exchange_info(self, symbol=None):
        """Informações do par (tick size, step size, etc)."""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/api/v3/exchangeInfo', **params)
    
    def get_symbol_info(self, symbol):
        """Extrai filtros relevantes do par."""
        info = self.get_exchange_info(symbol)
        for sym in info.get('symbols', []):
            if sym['symbol'] == symbol:
                filters = {}
                for f in sym['filters']:
                    if f['filterType'] == 'PRICE_FILTER':
                        filters['tick_size'] = float(f['tickSize'])
                        filters['min_price'] = float(f['minPrice'])
                    elif f['filterType'] == 'LOT_SIZE':
                        filters['step_size'] = float(f['stepSize'])
                        filters['min_qty'] = float(f['minQty'])
                    elif f['filterType'] == 'MIN_NOTIONAL':
                        filters['min_notional'] = float(f['minNotional'])
                return filters
        return {}
    
    # ═══ ORDENS ═══
    
    def market_buy(self, symbol, quote_order_qty=None, quantity=None):
        """Ordem de compra a mercado."""
        params = {'symbol': symbol, 'side': 'BUY', 'type': 'MARKET'}
        if quote_order_qty:
            params['quoteOrderQty'] = quote_order_qty  # quantidade em USDT
        elif quantity:
            params['quantity'] = quantity
        else:
            raise ValueError("Precisa de quote_order_qty ou quantity")
        return self._request('POST', '/api/v3/order', signed=True, **params)
    
    def market_sell(self, symbol, quantity):
        """Ordem de venda a mercado."""
        return self._request('POST', '/api/v3/order', signed=True,
                           symbol=symbol, side='SELL', type='MARKET',
                           quantity=quantity)
    
    def oco_order(self, symbol, side, quantity, price, stop_price, stop_limit_price=None):
        """
        Ordem OCO (One-Cancels-Other): SL + TP simultâneos.
        
        Exemplo de venda (take profit + stop loss):
        side='SELL', price=TP, stopPrice=SL
        """
        params = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': str(price),
            'stopPrice': str(stop_price),
            'stopLimitPrice': str(stop_limit_price or stop_price),
            'stopLimitTimeInForce': 'GTC'
        }
        return self._request('POST', '/api/v3/order/oco', signed=True, **params)
    
    # ═══ POSIÇÕES ═══
    
    def get_open_orders(self, symbol=None):
        """Ordens abertas."""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/api/v3/openOrders', signed=True, **params)
    
    def cancel_order(self, symbol, order_id):
        """Cancela uma ordem."""
        return self._request('DELETE', '/api/v3/order', signed=True,
                           symbol=symbol, orderId=order_id)
    
    # ═══ NOSSO BOT ═══
    
    def round_to_tick(self, price, tick_size):
        """Arredonda preço para o tick size correto."""
        return round(price / tick_size) * tick_size
    
    def round_to_step(self, quantity, step_size, use_floor=False):
        """Arredonda quantidade para step size correto. use_floor=True para venda (evitar saldo insuficiente)."""
        step = float(step_size)
        step_str = f'{step:.10f}'.rstrip('0')
        decimals = len(step_str.split('.')[1]) if '.' in step_str else 0
        if use_floor:
            import math
            return math.floor(quantity / step) * step
        return round(quantity, decimals)
    
    def execute_signal(self, pair, direction, entry, sl_price, tp_price, usdt_amount=None):
        """
        Executa um sinal do bot.
        
        Args:
            pair: ex 'BTCUSD' → convertido para 'BTCUSDT'
            direction: 'BUY' ou 'SELL'
            entry: preço de entrada
            sl_price: preço do stop loss
            tp_price: preço do take profit
            usdt_amount: quantidade em USDT (default: max_position)
        """
        if not self.api_key or not self.api_secret:
            raise Exception("API keys não configuradas. Edite binance_config.json")
        
        # Converter par: BTCUSD → BTCUSDT
        symbol = pair.replace('USD', 'USDT')
        
        if usdt_amount is None:
            usdt_amount = self.max_position
        
        # Verificar saldo (Spot + Margin)
        balance = self.get_balance('USDT')
        margin_bal = self._get_margin_balance('USDT')
        total_bal = balance + margin_bal
        if total_bal < usdt_amount:
            raise Exception(f"Saldo total insuficiente: ${total_bal:.2f} (precisa {usdt_amount})")
        
        # Info do par
        sym_info = self.get_symbol_info(symbol)
        tick_size = sym_info.get('tick_size', 0.01)
        step_size = sym_info.get('step_size', 0.00001)
        min_notional = sym_info.get('min_notional', 10)
        
        if usdt_amount < min_notional:
            raise Exception(f"Valor mínimo: {min_notional} USDT")
        
        # Arredondar preços
        entry = self.round_to_tick(entry, tick_size)
        sl_price = self.round_to_tick(sl_price, tick_size)
        tp_price = self.round_to_tick(tp_price, tick_size)
        
        # Quantidade em cripto
        quantity = self.round_to_step(usdt_amount / entry, step_size)
        
        print(f"  ⚡ Executando {direction} {symbol}")
        print(f"     Entrada: {entry} | SL: {sl_price} | TP: {tp_price}")
        print(f"     Qtd: {quantity} (${usdt_amount})")
        
        if self.testnet:
            print("  🧪 TESTNET — ordem NÃO será executada com dinheiro real")
        
        try:
            if direction == 'BUY':
                balance = self.get_balance('USDT')
                balance_label = 'Spot'
                if balance < usdt_amount:
                    # Tentar margin
                    balance = self._get_margin_balance('USDT')
                    balance_label = 'Margin'
                if balance < usdt_amount:
                    raise Exception(f"Saldo insuficiente: {balance:.2f} USDT ({balance_label})")
                
                if balance_label == 'Margin':
                    # Comprar via Margin com parcial
                    buy = self._request('POST', '/sapi/v1/margin/order', signed=True,
                                      symbol=symbol, side='BUY', type='MARKET',
                                      quoteOrderQty=str(usdt_amount))
                    print(f"  ✅ Compra Margin: {buy}")
                    
                    # Quantidade real executada
                    qty = float(quantity)
                    
                    # Preço real de execução
                    entry_price = float(buy.get('fills', [{}])[0].get('price', 0)) if buy.get('fills') else 0
                    if entry_price == 0:
                        entry_price = float(buy.get('cummulativeQuoteQty', 0)) / qty if buy.get('cummulativeQuoteQty') else float(sl_price)
                    
                    # Recalcular SL/TP com preço REAL
                    sl_pct = abs(float(sl_price) - float(tp_price)) / float(sl_price) * 100 / 4  # RR=3 → div por 4
                    sl_r = self.round_to_tick(entry_price * (1 - sl_pct/100), tick_size)
                    tp_r = self.round_to_tick(entry_price * (1 + sl_pct*3/100), tick_size)  # RR=3
                    
                    # TP1 @ 1:1 (distância do SL)
                    sl_dist = abs(entry_price - sl_r)
                    tp1_r = self.round_to_tick(entry_price + sl_dist, tick_size)
                    
                    # Pegar saldo real após compra
                    base = symbol.replace('USDT', '')
                    acct = self._request('GET', '/sapi/v1/margin/account', signed=True)
                    eth_free = 0.0
                    for a in acct.get('userAssets', []):
                        if a['asset'] == base:
                            eth_free = float(a['free'])
                    half_qty = self.round_to_step(eth_free * 0.49, step_size, use_floor=True)
                    half_qty_str = f'{half_qty:.6f}'.rstrip('0').rstrip('.')
                    rem_qty = self.round_to_step(eth_free * 0.48, step_size, use_floor=True)
                    rem_qty_str = f'{rem_qty:.6f}'.rstrip('0').rstrip('.')
                    
                    if half_qty < 0.0001:
                        # Lote muito pequeno, OCO full
                        oco = self._request('POST', '/sapi/v1/margin/order/oco', signed=True,
                                          symbol=symbol, side='SELL', quantity=str(qty),
                                          price=str(tp_r), stopPrice=str(sl_r),
                                          stopLimitPrice=str(sl_r),
                                          stopLimitTimeInForce='GTC',
                                          sideEffectType='AUTO_REPAY')
                        print(f"  ✅ OCO full: SL={sl_r} TP={tp_r}")
                        return {'buy': buy, 'oco': oco}
                    
                    tp1 = self._request('POST', '/sapi/v1/margin/order', signed=True,
                                      symbol=symbol, side='SELL', type='LIMIT',
                                      timeInForce='GTC', quantity=half_qty_str,
                                      price=str(tp1_r))
                    print(f"  ✅ TP1 50% @{tp1_r} (1:1): {tp1}")
                    
                    oco = self._request('POST', '/sapi/v1/margin/order/oco', signed=True,
                                      symbol=symbol, side='SELL', quantity=rem_qty_str,
                                      price=str(tp_r), stopPrice=str(sl_r),
                                      stopLimitPrice=str(sl_r),
                                      stopLimitTimeInForce='GTC',
                                      sideEffectType='AUTO_REPAY')
                    print(f"  ✅ OCO {rem_qty_str}: SL={sl_r} TP={tp_r}")
                    return {'buy': buy, 'tp1': tp1, 'oco': oco, 'partial': True}
                else:
                    # Spot: sem parcial
                    buy = self.market_buy(symbol, quantity=quantity)
                    print(f"  ✅ Compra Spot: {buy}")
                    oco = self.oco_order(symbol, 'SELL', quantity, price=tp_price, stop_price=sl_price)
                    print(f"  ✅ OCO: SL={sl_price} TP={tp_price}")
                    return {'buy': buy, 'oco': oco}
            else:
                # SELL = Short via Cross Margin
                balance = self._get_margin_balance('USDT')
                if balance < usdt_amount:
                    raise Exception(f"Saldo Margin insuficiente: {balance:.2f} USDT")
                return self._margin_sell(symbol, str(quantity), sl_price, tp_price, tick_size)
        
        except Exception as e:
            print(f"  ❌ Erro na execução: {e}")
            raise
    
    def _get_margin_balance(self, asset='USDT'):
        """Saldo em Cross Margin."""
        data = self._request('GET', '/sapi/v1/margin/account', signed=True)
        for b in data.get('userAssets', []):
            if b['asset'] == asset:
                return float(b['free'])
        return 0.0

    def _margin_sell(self, symbol, quantity, sl_price, tp_price, tick_size=0.01):
        """Short via Cross Margin: empréstimo + venda + parcial (50% @1:1, 50% @3:1)."""
        base_asset = symbol.replace('USDT', '')
        qty = float(quantity)
        half_qty = self.round_to_step(qty / 2, self.get_symbol_info(symbol).get('step_size', 0.00001))
        half_qty_str = f'{half_qty:.6f}'.rstrip('0').rstrip('.')
        
        try:
            # 1. Emprestar e vender full quantity
            loan = self._request('POST', '/sapi/v1/margin/loan', signed=True,
                               asset=base_asset, amount=str(quantity))
            print(f"  ✅ Empréstimo {base_asset}: {loan}")
            
            sell = self._request('POST', '/sapi/v1/margin/order', signed=True,
                               symbol=symbol, side='SELL', type='MARKET',
                               quantity=str(quantity))
            print(f"  ✅ Short executado: {sell}")
            
            # Preços baseados no preço REAL de execução
            entry = float(sell.get('fills', [{}])[0].get('price', 0)) if sell.get('fills') else 0
            if entry == 0:
                entry = float(sell.get('cummulativeQuoteQty', 0)) / qty if sell.get('cummulativeQuoteQty') else float(sl_price)
            
            sl_pct = abs(float(sl_price) - float(tp_price)) / float(sl_price) * 100 / 4  # extrai % (RR=3 → div por 4)
            sl_r = self.round_to_tick(entry * (1 + sl_pct/100), tick_size)  # SELL: SL acima
            tp_r = self.round_to_tick(entry * (1 - sl_pct*3/100), tick_size)  # SELL: TP abaixo
            
            # TP1: 50% @ 1:1
            sl_dist = abs(sl_r - entry)
            tp1_r = self.round_to_tick(entry - sl_dist, tick_size)
            
            # 2. TP1 limit (50% @ 1:1)
            tp1 = self._request('POST', '/sapi/v1/margin/order', signed=True,
                              symbol=symbol, side='BUY', type='LIMIT',
                              timeInForce='GTC', quantity=half_qty_str,
                              price=str(tp1_r))
            print(f"  ✅ TP1 50% @{tp1_r} (1:1): {tp1}")
            
            # 3. OCO: SL + TP2 (50% restante @ 3:1)
            oco = self._request('POST', '/sapi/v1/margin/order/oco', signed=True,
                              symbol=symbol, side='BUY', quantity=half_qty_str,
                              price=str(tp_r), stopPrice=str(sl_r),
                              stopLimitPrice=str(sl_r),
                              stopLimitTimeInForce='GTC',
                              sideEffectType='AUTO_REPAY')
            print(f"  ✅ OCO 50%: SL={sl_r} TP={tp_r}")
            
            return {'loan': loan, 'sell': sell, 'tp1': tp1, 'oco': oco, 'partial': True}
        except Exception as e:
            print(f"  ❌ Erro margin sell: {e}")
            raise

    def check_connection(self):
        """Testa conexão com a API."""
        try:
            # Ping
            self._request('GET', '/api/v3/ping')
            
            # Status
            info = self._request('GET', '/api/v3/account', signed=True)
            balances = {b['asset']: float(b['free']) 
                       for b in info.get('balances', []) 
                       if float(b['free']) > 0}
            
            print("✅ Conexão Binance OK")
            print(f"  Modo: {'TESTNET' if self.testnet else 'REAL'}")
            print(f"  Saldos: {balances}")
            return True
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            return False


if __name__ == '__main__':
    trader = BinanceTrader(testnet=True)
    trader.check_connection()
