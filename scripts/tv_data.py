#!/usr/bin/env python3
"""
tv_data.py v2 — Fonte de dados forex híbrida (long-term stable).
- OHLC histórico: yfinance (gratuito, sem API key)
- Cotação live: TradingView CDP via brain_browser.py
- Cache local para fallback offline

Uso: from tv_data import fetch_ohlcv
      df = fetch_ohlcv('EURUSD=X', period='5d', interval='15m')

Backup: Se yfinance falhar, usa cache TV + quotes CDP.
"""
import json, sys, subprocess, time, os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

HERMES = Path.home() / ".hermes"
SCRIPTS = HERMES / "scripts"
CACHE_DIR = HERMES / "forex" / "ohlcv_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════
# CAMADA 1: YFINANCE (OHLC histórico)
# ═══════════════════════════════════════════

def _yfinance_fetch(symbol_clean, period='5d', interval='15m'):
    """Fetch OHLC from Yahoo Finance. Returns DataFrame or None."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol_clean)
        df = ticker.history(period=period, interval=interval)
        if df is not None and len(df) >= 10:
            # Standardize columns
            df = df.rename(columns={
                'Open': 'Open', 'High': 'High', 
                'Low': 'Low', 'Close': 'Close'
            })
            # Keep only OHLC
            cols = ['Open', 'High', 'Low', 'Close']
            df = df[[c for c in cols if c in df.columns]]
            return df
    except Exception as e:
        pass
    return None


# ═══════════════════════════════════════════
# CAMADA 2: CDP LIVE QUOTE (preço atual)
# ═══════════════════════════════════════════

def _cdp_quote(symbol_clean):
    """Get current bid/ask from TradingView CDP."""
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / 'forex_quote.py'), symbol_clean],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'bid' in data:
                return data
    except:
        pass
    return None


# ═══════════════════════════════════════════
# CAMADA 3: CACHE LOCAL (fallback)
# ═══════════════════════════════════════════

def _cache_path(symbol):
    """Cache file path for a symbol."""
    clean = symbol.replace('=X', '').replace('/', '_')
    return CACHE_DIR / f"{clean}_15m.json"


def _cache_read(symbol):
    """Read cached OHLC data."""
    path = _cache_path(symbol)
    if path.exists():
        try:
            data = json.loads(path.read_text())
            if data.get('candles') and len(data['candles']) >= 5:
                df = pd.DataFrame(data['candles'])
                df['Datetime'] = pd.to_datetime(df['t'])
                df.set_index('Datetime', inplace=True)
                return df
        except:
            pass
    return None


def _cache_write(symbol, df):
    """Write OHLC data to cache."""
    if df is None or len(df) == 0:
        return
    try:
        candles = []
        for idx, row in df.iterrows():
            candles.append({
                't': idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                'o': float(row['Open']),
                'h': float(row['High']),
                'l': float(row['Low']),
                'c': float(row['Close']),
            })
        path = _cache_path(symbol)
        path.write_text(json.dumps({
            'symbol': symbol,
            'updated': datetime.now().isoformat(),
            'count': len(candles),
            'candles': candles[-500:]  # Keep last 500
        }))
    except:
        pass


# ═══════════════════════════════════════════
# API PÚBLICA
# ═══════════════════════════════════════════

def fetch_ohlcv(symbol, period='5d', interval='15m'):
    """
    Drop-in replacement for yf.Ticker(symbol).history(period, interval).
    Returns pandas DataFrame with columns: Open, High, Low, Close.
    
    Data sources (in order):
    1. yfinance (primary — full OHLC history)
    2. Local cache (fallback — last known data)
    3. CDP quote (last resort — single price point)
    """
    clean = symbol.replace('=X', '')
    
    # 1. Try yfinance
    df = _yfinance_fetch(symbol, period, interval)
    if df is not None and len(df) >= 10:
        _cache_write(symbol, df)
        return df
    
    # 2. Try local cache
    df = _cache_read(symbol)
    if df is not None and len(df) >= 10:
        return df
    
    # 3. Last resort: CDP quote + cached data
    quote = _cdp_quote(clean)
    cached = _cache_read(symbol)
    
    if cached is not None and len(cached) > 0:
        # Add current quote to cached data
        if quote and 'bid' in quote:
            now = datetime.now()
            price = quote['bid']
            new_row = pd.DataFrame([{
                'Open': price, 'High': price,
                'Low': price, 'Close': price
            }], index=[now])
            return pd.concat([cached, new_row])
        return cached
    
    # Nothing available
    if quote and 'bid' in quote:
        now = datetime.now()
        price = quote['bid']
        return pd.DataFrame([{
            'Open': price, 'High': price,
            'Low': price, 'Close': price
        }], index=[now])
    
    return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close'])


# ═══════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════
if __name__ == '__main__':
    for sym in ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X']:
        df = fetch_ohlcv(sym)
        print(f"{sym}: {len(df)} candles, last Close={df.iloc[-1]['Close']:.5f}")
