#!/usr/bin/env python3
"""
HYPERLIQUID DATA FEED — Candles M1 em tempo real via WebSocket
Substitui yfinance para dados crypto com latência zero
"""
import json, time, threading
import numpy as np
from collections import defaultdict
import websocket

class HyperliquidFeed:
    """Mantém candles M1 em memória via WebSocket Hyperliquid (público, sem API key)."""
    
    # Pares disponíveis (Hyperliquid usa nomes diferentes)
    SYMBOLS = {
        'BTCUSD': 'BTC',
        'ETHUSD': 'ETH', 
        'DOGEUSD': 'DOGE',
        'BNBUSD': 'BNB',
        'SOLUSD': 'SOL',
    }
    
    def __init__(self, symbols=None):
        self.symbols = symbols or ['BTC', 'ETH', 'DOGE', 'SOL']
        self.candles = defaultdict(list)  # symbol → [(open, high, low, close, volume), ...]
        self.current = defaultdict(dict)  # symbol → {open, high, low, close, volume}
        self.last_price = {}
        self.ws = None
        self.running = False
        self.lock = threading.Lock()
    
    def start(self):
        """Inicia WebSocket em thread separada."""
        self.running = True
        self.thread = threading.Thread(target=self._run_ws, daemon=True)
        self.thread.start()
        print(f"Hyperliquid Feed: conectando... ({len(self.symbols)} pares)")
    
    def _run_ws(self):
        """Loop principal do WebSocket."""
        while self.running:
            try:
                self.ws = websocket.WebSocket()
                self.ws.connect('wss://api.hyperliquid.xyz/ws')
                
                # Inscrever em todos os pares
                for coin in self.symbols:
                    sub = {'method': 'subscribe', 'subscription': {'type': 'trades', 'coin': coin}}
                    self.ws.send(json.dumps(sub))
                
                # Receber trades
                while self.running:
                    msg = json.loads(self.ws.recv())
                    self._process_message(msg)
                    
            except Exception as e:
                print(f"Hyperliquid WS erro: {e}, reconectando em 5s...")
                time.sleep(5)
    
    def _process_message(self, msg):
        """Processa mensagem de trade e atualiza candles M1."""
        if msg.get('channel') != 'trades':
            return
        
        data = msg.get('data', [])
        if not data:
            return
        
        with self.lock:
            for trade in data:
                coin = trade.get('coin', '')
                px = float(trade['px'])
                sz = float(trade['sz'])
                trade_time = trade.get('time', 0)
                
                if coin not in self.symbols:
                    continue
                
                self.last_price[coin] = px
                
                # Determinar minuto do candle
                minute = trade_time // 60000
                
                cur = self.current.get(coin, {})
                
                # Novo candle?
                if cur.get('minute') != minute:
                    # Fechar candle anterior
                    if cur:
                        self.candles[coin].append((
                            cur['open'], cur['high'], cur['low'], 
                            cur['close'], cur['volume']
                        ))
                        # Manter últimos 5000 candles (~3.5 dias)
                        if len(self.candles[coin]) > 5000:
                            self.candles[coin] = self.candles[coin][-5000:]
                    
                    # Novo candle
                    cur = {
                        'minute': minute,
                        'open': px, 'high': px, 'low': px, 
                        'close': px, 'volume': sz
                    }
                else:
                    # Atualizar candle atual
                    cur['high'] = max(cur['high'], px)
                    cur['low'] = min(cur['low'], px)
                    cur['close'] = px
                    cur['volume'] += sz
                
                self.current[coin] = cur
    
    def get_candles(self, symbol, count=200):
        """Retorna candles M1 no formato compatível com o bot.
        symbol: 'BTC', 'ETH', etc.
        Retorna: (highs, lows, closes, opens, volumes) arrays numpy
        """
        hl_symbol = self.SYMBOLS.get(symbol, symbol)
        coin = hl_symbol if hl_symbol in self.symbols else symbol
        
        with self.lock:
            candles = self.candles.get(coin, [])
            
            if not candles:
                return None, None, None, None, None
            
            n = min(count, len(candles))
            recent = candles[-n:]
            
            opens = np.array([c[0] for c in recent])
            highs = np.array([c[1] for c in recent])
            lows = np.array([c[2] for c in recent])
            closes = np.array([c[3] for c in recent])
            volumes = np.array([c[4] for c in recent])
            
            # Adicionar candle atual (não fechado)
            cur = self.current.get(coin, {})
            if cur:
                opens = np.append(opens, cur['open'])
                highs = np.append(highs, cur['high'])
                lows = np.append(lows, cur['low'])
                closes = np.append(closes, cur['close'])
                volumes = np.append(volumes, cur['volume'])
        
        return highs, lows, closes, opens, volumes
    
    def get_price(self, symbol):
        """Preço atual."""
        coin = self.SYMBOLS.get(symbol, symbol)
        return self.last_price.get(coin)
    
    def has_data(self, symbol, min_candles=100):
        """Verifica se tem dados suficientes."""
        coin = self.SYMBOLS.get(symbol, symbol)
        return len(self.candles.get(coin, [])) >= min_candles
    
    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()


if __name__ == '__main__':
    feed = HyperliquidFeed()
    feed.start()
    
    print("Aguardando dados (15s)...")
    time.sleep(15)
    
    for sym in ['BTCUSD', 'ETHUSD', 'DOGEUSD', 'SOLUSD']:
        h, l, c, o, v = feed.get_candles(sym, 5)
        price = feed.get_price(sym)
        n = len(c) if c is not None else 0
        print(f"  {sym}: {n} candles, price=${price}")
    
    feed.stop()
    print("OK")
