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
# CAMADA 1: TRADINGVIEW CDP (fonte primária M1 — sem erro de escala)
# ═══════════════════════════════════════════

def _tv_cdp_fetch(symbol, interval='1m'):
    """Extrai OHLC diretamente do TradingView via CDP (Brave :9222)."""
    try:
        sym_map = {
            'EURUSD=X': 'FX:EURUSD', 'GBPUSD=X': 'FX:GBPUSD',
            'USDJPY=X': 'FX:USDJPY', 'GBPJPY=X': 'FX:GBPJPY',
            'EURJPY=X': 'FX:EURJPY', 'USDCAD=X': 'FX:USDCAD',
            'GC=F': 'TVC:GOLD',
        }
        tv_sym = sym_map.get(symbol, 'FX:' + symbol.replace('=X', ''))
        tf = interval.replace('m', '')
        
        clean_name = symbol.replace('=X', '').replace('/', '_')
        out = f'/tmp/tv_{clean_name}.json'
        
        result = subprocess.run(
            [sys.executable, '/home/roberto/tv_ohlc_extractor.py',
             '--symbol', tv_sym, '--interval', tf, '--output', out],
            capture_output=True, text=True, timeout=25
        )
        
        if Path(out).exists():
            data = json.loads(Path(out).read_text())
            candles_raw = data.get('bars', data.get('candles', []))
            
            candles = []
            for c in candles_raw:
                try:
                    candles.append({
                        'Open': c['open'], 'High': c['high'],
                        'Low': c['low'], 'Close': c['close'],
                        'Datetime': datetime.fromtimestamp(c['time'])
                    })
                except:
                    pass
            
            if candles:
                df = pd.DataFrame(candles)
                df.set_index('Datetime', inplace=True)
                df = df[['Open', 'High', 'Low', 'Close']]
                return df
    except Exception:
        pass
    return None


# ═══════════════════════════════════════════
# CAMADA 2: YFINANCE (fallback)
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
    Data sources (in order):
    1. TradingView CDP (primary for M1 — sem erro de escala)
    2. yfinance (fallback + timeframes maiores)
    3. Local cache (last resort)
    """
    clean = symbol.replace('=X', '')
    
    # 1. Para M1: TradingView CDP (fonte precisa, sem erro de escala)
    if interval == '1m':
        df = _tv_cdp_fetch(symbol, interval)
        if df is not None and len(df) >= 10:
            _cache_write(symbol, df)
            return df
    
    # 2. Try yfinance
    df = _yfinance_fetch(symbol, period, interval)
    if df is not None and len(df) >= 10:
        _cache_write(symbol, df)
        return df
    
    # 3. Try local cache
    df = _cache_read(symbol)
    if df is not None and len(df) >= 10:
        return df
    
    # 4. Last resort: CDP quote
    quote = _cdp_quote(clean)
    cached = _cache_read(symbol)
    
    if cached is not None and len(cached) > 0:
        if quote and 'bid' in quote:
            now = datetime.now()
            price = quote['bid']
            new_row = pd.DataFrame([{
                'Open': price, 'High': price,
                'Low': price, 'Close': price
            }], index=[now])
            return pd.concat([cached, new_row])
        return cached
    
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
