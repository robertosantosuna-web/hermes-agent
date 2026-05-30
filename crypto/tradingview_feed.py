#!/usr/bin/env python3
"""
TRADINGVIEW FEED — Dados direto do TradingView via tvDatafeed
Multi-timeframe nativo: M1, M5, M15, M30, H1, H4, D1
Sem limite de 7 dias, sem delay, sem API key
"""
import numpy as np
from datetime import datetime, timezone

# Usar python do venv que tem tvDatafeed
import sys, subprocess, json, os

class TradingViewFeed:
    """Feed de dados do TradingView (Binance) via tvDatafeed."""
    
    # Mapeamento: nosso par → (symbol, exchange)
    SYMBOLS = {
        # Crypto (Binance)
        'BTCUSD': ('BTCUSDT', 'BINANCE'),
        'ETHUSD': ('ETHUSDT', 'BINANCE'),
        'DOGEUSD': ('DOGEUSDT', 'BINANCE'),
        'BNBUSD': ('BNBUSDT', 'BINANCE'),
        'SOLUSD': ('SOLUSDT', 'BINANCE'),
        # Forex (OANDA)
        'EURUSD': ('EURUSD', 'OANDA'),
        'GBPUSD': ('GBPUSD', 'OANDA'),
        'USDJPY': ('USDJPY', 'OANDA'),
        'EURJPY': ('EURJPY', 'OANDA'),
        'GBPJPY': ('GBPJPY', 'OANDA'),
        'AUDUSD': ('AUDUSD', 'OANDA'),
        'USDCAD': ('USDCAD', 'OANDA'),
        'NZDUSD': ('NZDUSD', 'OANDA'),
        'EURGBP': ('EURGBP', 'OANDA'),
    }
    
    # Timeframes disponíveis
    TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
    
    def __init__(self):
        self._cache = {}
        self._last_fetch = {}
    
    def _run_tv(self, code):
        """Executa código via venv python (que tem tvDatafeed)."""
        venv_python = os.path.expanduser('~/.hermes/hermes-agent/venv/bin/python')
        result = subprocess.run(
            [venv_python, '-c', code],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            raise Exception(result.stderr.strip())
        return result.stdout.strip()
    
    def get_candles(self, pair, timeframe='1m', count=200):
        """
        Retorna candles do TradingView.
        Retorna: (highs, lows, closes, opens, volumes) arrays numpy
        """
        sym, exchange = self.SYMBOLS.get(pair, (pair.replace('USD', 'USDT'), 'BINANCE'))
        
        # Mapear timeframe
        tf_map = {'1m': 'in_1_minute', '5m': 'in_5_minute', '15m': 'in_15_minute',
                  '30m': 'in_30_minute', '1h': 'in_1_hour', '4h': 'in_4_hour', '1d': 'in_1_day'}
        tf = tf_map.get(timeframe, 'in_1_minute')
        
        cache_key = f"{sym}_{exchange}_{tf}_{count}"
        
        # Cache de 30 segundos (evitar rate limiting)
        now = datetime.now(timezone.utc)
        if cache_key in self._last_fetch:
            if (now - self._last_fetch[cache_key]).total_seconds() < 30:
                if cache_key in self._cache:
                    return self._cache[cache_key]
        
        code = f"""
from tvDatafeed import TvDatafeed, Interval
tv = TvDatafeed()
data = tv.get_hist(symbol='{sym}', exchange='{exchange}', interval=Interval.{tf}, n_bars={count})
import json
if len(data) == 0:
    print('EMPTY')
else:
    result = {{
        'high': data['high'].values.tolist(),
        'low': data['low'].values.tolist(),
        'close': data['close'].values.tolist(),
        'open': data['open'].values.tolist(),
        'volume': data['volume'].values.tolist() if 'volume' in data.columns else [],
        'index': [str(i) for i in data.index[:5]]
    }}
    print(json.dumps(result))
"""
        
        try:
            output = self._run_tv(code)
            if output == 'EMPTY':
                return None, None, None, None, None
            
            data = json.loads(output)
            
            highs = np.array(data['high'])
            lows = np.array(data['low'])
            closes = np.array(data['close'])
            opens = np.array(data['open'])
            volumes = np.array(data['volume']) if data['volume'] else None
            
            result = (highs, lows, closes, opens, volumes)
            self._cache[cache_key] = result
            self._last_fetch[cache_key] = now
            
            return result
        
        except Exception as e:
            print(f"[TV] Erro {pair} {timeframe}: {e}")
            return None, None, None, None, None
    
    def get_multi_tf(self, pair, timeframes=None):
        """Retorna dados de múltiplos timeframes de uma vez."""
        if timeframes is None:
            timeframes = ['1m', '5m', '15m', '1h']
        
        result = {}
        for tf in timeframes:
            data = self.get_candles(pair, tf, 200)
            if data[2] is not None:
                result[tf] = data
        return result
    
    def get_price(self, pair):
        """Preço atual (último close M1)."""
        _, _, c, _, _ = self.get_candles(pair, '1m', 2)
        return float(c[-1]) if c is not None and len(c) > 0 else None


if __name__ == '__main__':
    feed = TradingViewFeed()
    
    print("═══ TRADINGVIEW FEED ═══")
    for pair in ['BTCUSD', 'ETHUSD', 'DOGEUSD', 'BNBUSD']:
        h, l, c, o, v = feed.get_candles(pair, '1m', 5)
        price = feed.get_price(pair)
        n = len(c) if c is not None else 0
        print(f"  {pair:8s}: {n} candles M1, \${price:,.2f}" if price else f"  {pair:8s}: {n} candles")
    
    print("\n═══ MULTI-TF BTC ═══")
    mtf = feed.get_multi_tf('BTCUSD', ['1m','5m','15m','30m','1h','4h'])
    for tf, (h,l,c,o,v) in mtf.items():
        print(f"  {tf:4s}: {len(c)} candles, last=${c[-1]:,.2f}")
