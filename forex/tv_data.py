#!/usr/bin/python3
"""
Módulo de dados do TradingView via Scanner API
===============================================
Acesso gratuito, sem login, dados em tempo real com indicadores técnicos.
"""

import requests
import time
from datetime import datetime

# Sessão persistente com headers de browser real
_session = None

def _get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Origin': 'https://br.tradingview.com',
            'Referer': 'https://br.tradingview.com/',
        })
    return _session

# Mapeamento de pares → tickers TradingView
PAIR_TO_TICKER = {
    'EUR/USD': 'FX:EURUSD',
    'GBP/USD': 'FX:GBPUSD',
    'EUR/GBP': 'FX:EURGBP',
    'USD/JPY': 'FX:USDJPY',
    'AUD/USD': 'FX:AUDUSD',
    'EUR/JPY': 'FX:EURJPY',
}

TICKER_TO_PAIR = {v: k for k, v in PAIR_TO_TICKER.items()}

# Colunas que queremos extrair
COLUMNS = [
    'close', 'high', 'low', 'open', 'volume', 'change',
    'Recommend.All',
    'RSI', 'RSI[1]',
    'MACD.macd', 'MACD.signal',
    'SMA20', 'SMA50',
    'BB.upper', 'BB.lower',
    'ATR', 'Volatility.D'
]


def get_live_quotes(pairs=None):
    """
    Obtém cotações em tempo real com indicadores técnicos.

    Args:
        pairs: lista de nomes como ['EUR/USD', 'GBP/USD'] ou None para todos

    Returns:
        dict: {pair_name: {close, high, low, open, volume, change, rsi, macd, sma20, ...}}
    """
    if pairs is None:
        pairs = list(PAIR_TO_TICKER.keys())

    tickers = [PAIR_TO_TICKER[p] for p in pairs if p in PAIR_TO_TICKER]

    session = _get_session()
    payload = {
        'symbols': {'tickers': tickers},
        'columns': COLUMNS
    }

    try:
        r = session.post('https://scanner.tradingview.com/forex/scan',
                         json=payload, timeout=15)
        r.raise_for_status()
        result = r.json()
    except Exception as e:
        return {'error': str(e)}

    quotes = {}
    col_names = ['close', 'high', 'low', 'open', 'volume', 'change',
                 'recommend', 'rsi', 'rsi_prev',
                 'macd', 'macd_signal',
                 'sma20', 'sma50',
                 'bb_upper', 'bb_lower',
                 'atr', 'volatility']

    for item in result.get('data', []):
        ticker = item['s']
        pair = TICKER_TO_PAIR.get(ticker, ticker)
        d = item['d']
        quote = {'ticker': ticker, 'timestamp': datetime.now().isoformat()}
        for i, name in enumerate(col_names):
            if i < len(d):
                quote[name] = d[i]
        quotes[pair] = quote

    return quotes


def get_historical(ticker, count=50, timeframe='15'):
    """
    Obtém candles históricos via scanner (limitado ao que o scanner retorna).

    Nota: O scanner retorna dados do timeframe atual, não séries históricas.
    Para séries históricas longas, use Yahoo Finance como fallback.
    """
    session = _get_session()

    # O scanner retorna o estado ATUAL do candle para o timeframe
    # Para histórico real, usaríamos o chart API que requer websocket
    # Por enquanto, retornamos o snapshot atual
    payload = {
        'symbols': {'tickers': [ticker]},
        'columns': COLUMNS,
        'filter': [{'left': 'timeframe', 'operation': 'equal', 'right': timeframe}]
    }

    try:
        r = session.post('https://scanner.tradingview.com/forex/scan',
                         json=payload, timeout=15)
        r.raise_for_status()
        result = r.json()
        if result.get('data'):
            d = result['data'][0]['d']
            col_names = ['close', 'high', 'low', 'open', 'volume', 'change',
                         'recommend', 'rsi', 'rsi_prev', 'macd', 'macd_signal',
                         'sma20', 'sma50', 'bb_upper', 'bb_lower', 'atr', 'volatility']
            return {col_names[i]: d[i] for i in range(min(len(col_names), len(d)))}
    except:
        pass
    return None


if __name__ == '__main__':
    # Teste rápido
    print("=== TESTE TRADINGVIEW API ===")
    quotes = get_live_quotes(['EUR/USD', 'GBP/USD', 'USD/JPY'])
    for pair, q in quotes.items():
        print(f"\n{pair}:")
        print(f"  Preço: {q.get('close')} | Δ {q.get('change', 0):.3f}%")
        print(f"  Range: {q.get('low')} - {q.get('high')}")
        print(f"  RSI: {q.get('rsi', 'N/A')} | Recommend: {q.get('recommend', 'N/A')}")
        print(f"  SMA20: {q.get('sma20', 'N/A')} | SMA50: {q.get('sma50', 'N/A')}")
        print(f"  MACD: {q.get('macd', 'N/A')} | ATR: {q.get('atr', 'N/A')}")
        print(f"  BB: {q.get('bb_lower', 'N/A')} - {q.get('bb_upper', 'N/A')}")
