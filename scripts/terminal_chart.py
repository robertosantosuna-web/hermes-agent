#!/usr/bin/env python3
"""
Terminal Chart — Gráfico de velas ASCII direto no terminal.
Zero dependência de browser, GUI, ou HTML.
Usa dados do TradingView (tvDatafeed).

Uso:
  python3 terminal_chart.py GBPJPY 15m    # Últimas 40 velas
  python3 terminal_chart.py EURUSD 1h     # H1
  python3 terminal_chart.py GBPUSD 15m 60 # 60 velas
"""

import sys, os
from pathlib import Path
from datetime import datetime

HERMES = Path.home() / ".hermes"
sys.path.insert(0, str(HERMES / "scripts"))

PIP_SIZES = {
    'GBPJPY': 0.01, 'USDJPY': 0.01, 'EURJPY': 0.01,
    'EURUSD': 0.0001, 'GBPUSD': 0.0001, 'USDCAD': 0.0001,
    'XAUUSD': 0.01,
}

# ═══ Blocos Unicode para candles ═══
BULL_FULL = '█'
BEAR_FULL = '█'
BULL_BODY = '┃'
BEAR_BODY = '┃'
WICK = '│'
SHADOW = '╎'

# ═══ CORES ANSI ═══
GREEN = '\033[32m'
RED = '\033[31m'
YELLOW = '\033[33m'
CYAN = '\033[36m'
BLUE = '\033[34m'
GRAY = '\033[90m'
BOLD = '\033[1m'
RESET = '\033[0m'


def fetch_tv(symbol, interval='15m', n_bars=60):
    """Puxa dados do TradingView."""
    from tvDatafeed import TvDatafeed, Interval as TVI
    imap = {'1m': TVI.in_1_minute, '5m': TVI.in_5_minute,
            '15m': TVI.in_15_minute, '30m': TVI.in_30_minute,
            '1h': TVI.in_1_hour, '4h': TVI.in_4_hour, '1d': TVI.in_daily}
    exchange = 'OANDA' if symbol == 'XAUUSD' else 'FX'
    tv = TvDatafeed()
    return tv.get_hist(symbol=symbol, exchange=exchange, 
                       interval=imap.get(interval, TVI.in_15_minute), n_bars=n_bars)


def detect_fvgs_terminal(o, h, l, c, pip, min_gap=2.0):
    """FVG detection para terminal (retorna índices)."""
    fvgs = []
    for i in range(2, len(c)):
        gap_up = (l[i] - h[i-2]) / pip
        gap_down = (l[i-2] - h[i]) / pip
        if gap_up >= min_gap:
            fvgs.append({'idx': i, 'type': 'BULL', 'gap': gap_up, 
                         'top': h[i-2], 'bot': l[i]})
        elif gap_down >= min_gap:
            fvgs.append({'idx': i, 'type': 'BEAR', 'gap': gap_down,
                         'top': h[i], 'bot': l[i-2]})
    return fvgs


def render_terminal(symbol, interval, df, fvgs, pip_size, width=40):
    """Renderiza gráfico de velas ASCII colorido no terminal."""
    o = df['open'].values[-width:]
    h = df['high'].values[-width:]
    l = df['low'].values[-width:]
    c = df['close'].values[-width:]
    
    # Filtrar FVGs visíveis
    offset = len(df) - width
    visible_fvgs = [f for f in fvgs if f['idx'] >= offset]
    
    # Escala do gráfico
    all_prices = list(h) + list(l)
    price_min = min(all_prices)
    price_max = max(all_prices)
    price_range = price_max - price_min or 0.00001
    chart_height = 16
    
    # Cabeçalho
    last_price = c[-1]
    change = (c[-1] - c[-2]) / pip_size if len(c) >= 2 else 0
    change_color = GREEN if change >= 0 else RED
    fmt = 3 if 'JPY' in symbol else 5
    
    print(f"\n{BOLD}{symbol} {interval}{RESET}  {change_color}{last_price:.{fmt}f}{RESET}  "
          f"{change_color}{'+' if change>=0 else ''}{change:.1f}p{RESET}  "
          f"Vol: {len(df)} velas  {GRAY}{datetime.now().strftime('%H:%M')}{RESET}")
    print(f"{GRAY}H: {price_max:.{fmt}f}  L: {price_min:.{fmt}f}  Range: {price_range/pip_size:.0f}p  "
          f"FVGs: {len(fvgs)}{RESET}")
    print()
    
    # Grade de preço (eixo Y)
    for row in range(chart_height, -1, -1):
        price_level = price_min + (row / chart_height) * price_range
        
        # Label do preço
        if row % 4 == 0:
            label = f"{price_level:.{fmt}f}".rjust(8)
        elif row % 2 == 0:
            label = f"{GRAY}····{RESET}".rjust(12)
        else:
            label = " " * 8
        
        line = label + " "
        
        # Renderizar cada vela
        for i in range(len(o)):
            body_top = max(o[i], c[i])
            body_bot = min(o[i], c[i])
            is_bull = c[i] >= o[i]
            
            # Posições normalizadas
            wick_top = int((h[i] - price_min) / price_range * chart_height)
            body_t = int((body_top - price_min) / price_range * chart_height)
            body_b = int((body_bot - price_min) / price_range * chart_height)
            wick_bot = int((l[i] - price_min) / price_range * chart_height)
            
            color = GREEN if is_bull else RED
            
            # Verificar FVG nessa vela
            fvg_here = [f for f in visible_fvgs if f['idx'] == offset + i]
            fvg_marker = ''
            if fvg_here:
                fvg_marker = f"{YELLOW}▼{RESET}" if fvg_here[0]['type'] == 'BULL' else f"{BLUE}▲{RESET}"
            
            if row == wick_top:
                line += f"{color}{WICK}{RESET}"
            elif row == wick_bot:
                line += f"{color}{WICK}{RESET}"
            elif body_b <= row <= body_t:
                if body_t == body_b:
                    line += f"{color}─{RESET}"
                else:
                    line += f"{color}{BULL_FULL}{RESET}"
            elif row == wick_bot - 1 and fvg_marker:
                line += fvg_marker
            else:
                line += " "
        
        print(line)
    
    # Linha do tempo
    print(" " * 9 + f"{GRAY}└{'─' * width}{RESET}")
    
    # Últimos timestamps
    ts_labels = []
    for i in [0, width//4, width//2, 3*width//4, width-1]:
        if i < len(df):
            ts = df.index[offset + i]
            ts_str = ts.strftime('%d/%H') if hasattr(ts, 'strftime') else str(ts)[5:10]
            ts_labels.append((i, ts_str))
    
    ts_line = " " * 9
    last_pos = 0
    for pos, label in ts_labels:
        ts_line += " " * (pos - last_pos) + label
        last_pos = pos + len(label)
    print(ts_line)
    
    # ═══ FVGs recentes ═══
    recent = [f for f in visible_fvgs[-8:]]
    if recent:
        print(f"\n{BOLD}FVGs recentes:{RESET}")
        for f in recent:
            idx = f['idx']
            ts = df.index[idx]
            ts_str = ts.strftime('%d/%m %H:%M') if hasattr(ts, 'strftime') else str(ts)
            emoji = '🟢' if f['type'] == 'BULL' else '🔴'
            print(f"  {emoji} {ts_str}  gap={f['gap']:.1f}p  top={f['top']:.5f} bot={f['bot']:.5f}")
    
    # ═══ SENTIMENTO ═══
    bull_count = sum(1 for f in visible_fvgs if f['type'] == 'BULL')
    bear_count = sum(1 for f in visible_fvgs if f['type'] == 'BEAR')
    ratio = bull_count / max(bear_count, 1)
    
    if ratio > 2.0:
        sentiment = f"{GREEN}⬆ FORTEMENTE BULLISH{RESET}"
    elif ratio > 1.3:
        sentiment = f"{GREEN}⬆ bullish{RESET}"
    elif ratio < 0.5:
        sentiment = f"{RED}⬇ FORTEMENTE BEARISH{RESET}"
    elif ratio < 0.75:
        sentiment = f"{RED}⬇ bearish{RESET}"
    else:
        sentiment = f"{YELLOW}↔ NEUTRO{RESET}"
    
    print(f"\n{BOLD}Sentimento:{RESET} {sentiment}  "
          f"({bull_count}🟢 vs {bear_count}🔴 = {ratio:.1f}x)")
    print(f"{'='*60}")


def main():
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'GBPJPY'
    interval = sys.argv[2] if len(sys.argv) > 2 else '15m'
    n_bars = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    
    symbol = symbol.upper()
    pip = PIP_SIZES.get(symbol, 0.0001)
    
    df = fetch_tv(symbol, interval, n_bars)
    if df is None or len(df) < 10:
        print(f"⚠️ Sem dados para {symbol}")
        sys.exit(1)
    
    o = df['open'].values
    h = df['high'].values
    l = df['low'].values
    c = df['close'].values
    
    fvgs = detect_fvgs_terminal(o, h, l, c, pip)
    
    render_terminal(symbol, interval, df, fvgs, pip, width=min(60, n_bars))


if __name__ == '__main__':
    main()
