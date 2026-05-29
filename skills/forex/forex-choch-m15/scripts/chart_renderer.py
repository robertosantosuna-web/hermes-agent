#!/usr/bin/env python3
"""
Chart Renderer — Gera gráficos HTML interativos com indicadores.
Substitui dependência de browser/CDP/TradingView.
Usa lightweight-charts (CDN) para renderização profissional.

Uso:
  python3 chart_renderer.py GBPJPY 15m    # Gráfico M15 do GBPJPY
  python3 chart_renderer.py EURUSD 1h     # Gráfico H1 do EURUSD
  python3 chart_renderer.py --all          # Todos os 6 pares no M15

Output: ~/.hermes/forex/charts/<PAR>_<TF>_<TS>.html
Dependências: yfinance, lightweight-charts (carregado via CDN no HTML)
"""
import json, sys, os
from pathlib import Path
from datetime import datetime, timezone, timedelta

HERMES = Path.home() / ".hermes"
CHARTS_DIR = HERMES / "forex" / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

SYMBOLS = {
    'GBPJPY': 'GBPJPY=X', 'USDJPY': 'USDJPY=X', 'EURUSD': 'EURUSD=X',
    'GBPUSD': 'GBPUSD=X', 'EURJPY': 'EURJPY=X', 'USDCAD': 'USDCAD=X',
    'XAUUSD': 'GC=F',
}

PIP_SIZES = {
    'GBPJPY': 0.01, 'USDJPY': 0.01, 'EURJPY': 0.01,
    'EURUSD': 0.0001, 'GBPUSD': 0.0001, 'USDCAD': 0.0001,
    'XAUUSD': 0.01,
}


def detect_fvgs(closes, highs, lows, pip_size, min_gap=2.0):
    """Detecta Fair Value Gaps."""
    fvgs = []
    for i in range(2, len(closes)):
        gap_up = lows[i] - highs[i-2]
        gap_down = lows[i-2] - highs[i]
        gap_pips_up = gap_up / pip_size
        gap_pips_down = gap_down / pip_size
        
        if gap_pips_up >= min_gap:
            fvgs.append({'index': i, 'type': 'bullish', 'top': float(highs[i-2]), 'bottom': float(lows[i]), 'gap': float(gap_pips_up)})
        elif gap_pips_down >= min_gap:
            fvgs.append({'index': i, 'type': 'bearish', 'top': float(highs[i]), 'bottom': float(lows[i-2]), 'gap': float(gap_pips_down)})
    return fvgs


def detect_swings(highs, lows, pip_size, min_swing=5):
    """Detecta swing highs/lows."""
    swings = []
    n = len(highs)
    for i in range(3, n - 3):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            swings.append({'index': i, 'type': 'high', 'price': float(highs[i])})
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            swings.append({'index': i, 'type': 'low', 'price': float(lows[i])})
    return swings


def fetch_data(symbol, interval='15m', days=5):
    """Puxa dados OHLCV via Yahoo Finance."""
    import yfinance as yf
    ticker = SYMBOLS.get(symbol, symbol)
    period_map = {1: '1d', 2: '2d', 5: '5d', 10: '10d', 30: '1mo'}
    period = period_map.get(days, '5d')
    interval_map = {'1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m', '1h': '60m', '4h': '60m'}
    yf_interval = interval_map.get(interval, '15m')
    df = yf.download(ticker, period=period, interval=yf_interval, progress=False, auto_adjust=True)
    return df if not df.empty else None


def render_html(symbol, df, interval, fvgs, swings, pip_size, output_path):
    """Gera HTML com gráfico de candles + indicadores lightweight-charts."""
    import numpy as np
    
    candles = []
    for i, (idx, row) in enumerate(df.iterrows()):
        ts = int(idx.timestamp()) if hasattr(idx, 'timestamp') else int(datetime.fromisoformat(str(idx)).timestamp())
        try:
            o = float(row['Open'].iloc[0]) if hasattr(row['Open'], 'iloc') else float(row['Open'])
            h = float(row['High'].iloc[0]) if hasattr(row['High'], 'iloc') else float(row['High'])
            l = float(row['Low'].iloc[0]) if hasattr(row['Low'], 'iloc') else float(row['Low'])
            c = float(row['Close'].iloc[0]) if hasattr(row['Close'], 'iloc') else float(row['Close'])
        except:
            continue
        candles.append({'time': ts, 'open': o, 'high': h, 'low': l, 'close': c})
    
    fvg_markers = []
    for f in fvgs[-20:]:
        idx = f['index']
        if idx < len(candles):
            ts = candles[idx]['time']
            fvg_markers.append({
                'time': ts, 'position': 'aboveBar' if f['type'] == 'bullish' else 'belowBar',
                'color': 'green' if f['type'] == 'bullish' else 'red',
                'shape': 'circle', 'text': f"FVG {f['gap']:.1f}p",
            })
    
    swing_markers = []
    for s in swings[-15:]:
        idx = s['index']
        if idx < len(candles):
            ts = candles[idx]['time']
            swing_markers.append({
                'time': ts, 'position': 'aboveBar' if s['type'] == 'low' else 'belowBar',
                'color': '#FF9800' if s['type'] == 'high' else '#2196F3',
                'shape': 'arrowDown' if s['type'] == 'high' else 'arrowUp',
                'text': f"{'HH' if s['type']=='high' else 'LL'} {s['price']:.5f}",
            })
    
    html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{symbol} {interval} — Hermes</title>
<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<style>body{{margin:0;padding:10px;background:#1a1a2e;color:#eee;font-family:monospace}}#chart{{width:100%;height:600px}}.info{{padding:10px;font-size:12px;color:#888}}span{{color:#4fc3f7}}</style></head>
<body><div class="info">{symbol} · {interval} · {len(candles)} candles · {len(fvgs)} FVGs · {len(swings)} swings <span>{datetime.now():%d/%m %H:%M}</span></div>
<div id="chart"></div><script>
const c=LightweightCharts.createChart(document.getElementById('chart'),{{layout:{{background:{{color:'#1a1a2e'}},textColor:'#999'}},grid:{{vertLines:{{color:'#2a2a3e'}},horzLines:{{color:'#2a2a3e'}}}},crosshair:{{mode:1}},timeScale:{{timeVisible:!0}}}});
c.addCandlestickSeries({{upColor:'#00c853',downColor:'#ff1744',borderUpColor:'#00c853',borderDownColor:'#ff1744',wickUpColor:'#00c853',wickDownColor:'#ff1744'}}).setData({json.dumps(candles, default=str)});
const fvgD={json.dumps(fvg_markers)};if(fvgD.length){{c.addLineSeries({{color:'transparent',lineWidth:0,lastValueVisible:!1}}).setMarkers(fvgD)}}
const swD={json.dumps(swing_markers)};if(swD.length){{c.addLineSeries({{color:'transparent',lineWidth:0,lastValueVisible:!1}}).setMarkers(swD)}}
c.timeScale().fitContent();</script></body></html>'''
    
    output_path.write_text(html)
    return output_path


def main():
    import argparse, numpy as np
    parser = argparse.ArgumentParser()
    parser.add_argument('symbol', nargs='?', default='GBPJPY')
    parser.add_argument('interval', nargs='?', default='15m')
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--days', type=int, default=2)
    args = parser.parse_args()
    
    symbols = list(SYMBOLS.keys())[:6] if args.all else [args.symbol.upper()]
    
    for sym in symbols:
        print(f"📊 {sym} {args.interval}...")
        df = fetch_data(sym, args.interval, args.days)
        if df is None or len(df) < 20:
            print(f"   ⚠️ Dados insuficientes")
            continue
        
        pip = PIP_SIZES.get(sym, 0.0001)
        closes = np.array(df['Close']).flatten().astype(float)
        highs = np.array(df['High']).flatten().astype(float)
        lows = np.array(df['Low']).flatten().astype(float)
        
        fvgs = detect_fvgs(closes, highs, lows, pip)
        swings = detect_swings(highs, lows, pip)
        
        ts = datetime.now().strftime('%Y%m%d_%H%M')
        out = CHARTS_DIR / f'{sym}_{args.interval}_{ts}.html'
        render_html(sym, df, args.interval, fvgs, swings, pip, out)
        print(f"   ✅ {len(fvgs)} FVGs, {len(swings)} swings → {out}")
    
    if args.all:
        print(f"\n📁 {len(symbols)} gráficos em {CHARTS_DIR}/")


if __name__ == '__main__':
    main()
