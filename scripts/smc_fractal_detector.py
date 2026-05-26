#!/usr/bin/env python3
"""
SMC Fractal Detector — Metodologia Dinei
=========================================
Detecta estruturas SMC (Smart Money Concepts) usando a metodologia fractal do Dinei:
  - Pivôs 5+1 (swing highs/lows validados)
  - MSS (Market Structure Shift) — não exige rompimento de topo
  - FVGs (Fair Value Gaps) com gap mínimo configurável
  - Order Blocks (OB) — extremos do trecho anterior ao rompimento
  - Liquidez (buyside/sellside) — clusters de swings

Fonte: Chat export Dinei + Lucas (04-11/05/2026)
Indicador base: ICT Concepts [LuxAlgo] (Pine Script v5)

Uso:
  python3 smc_fractal_detector.py                     # EURUSD M15, 5 dias
  python3 smc_fractal_detector.py --pair GBPUSD --tf 1h  # GBPUSD H1
  python3 smc_fractal_detector.py --json               # Saída JSON para bot
"""

import yfinance as yf
import pandas as pd
import numpy as np
import json, argparse, sys
from datetime import datetime
from pathlib import Path

HERMES = Path.home() / ".hermes"
SIGNALS_FILE = HERMES / "forex" / "smc_signals.json"

class SMCFractalDetector:
    def __init__(self, df, pip_val=0.0001, pivot_lookback=5, min_fvg_pips=5):
        self.df = df
        self.pip = pip_val
        self.lookback = pivot_lookback
        self.min_fvg = min_fvg_pips
        self.highs = []
        self.lows = []
        self.mss_signals = []
        self.fvgs = []
        self.obs = []
        self.liquidity = {'buyside': [], 'sellside': []}
        
    def find_swings(self):
        """Pivôs validados: 5 velas atrás + 1 à frente (Dinei/LuxAlgo)"""
        df = self.df
        lb = self.lookback
        for i in range(lb, len(df)-1):
            # Pivot high
            window = df['High'].iloc[i-lb:i+1]
            if df['High'].iloc[i] == window.max() and df['High'].iloc[i] > df['High'].iloc[i+1]:
                self.highs.append({'idx': i, 'price': df['High'].iloc[i], 'time': str(df.index[i])[:16]})
            # Pivot low
            window = df['Low'].iloc[i-lb:i+1]
            if df['Low'].iloc[i] == window.min() and df['Low'].iloc[i] < df['Low'].iloc[i+1]:
                self.lows.append({'idx': i, 'price': df['Low'].iloc[i], 'time': str(df.index[i])[:16]})
        return self.highs, self.lows
    
    def detect_mss(self):
        """MSS: fechamento acima/abaixo do swing anterior (não exige rompimento de topo)"""
        if len(self.highs) < 2 or len(self.lows) < 2:
            return self.mss_signals
        
        # MSS Bullish: close > previous swing high
        for i in range(len(self.highs)-1, 0, -1):
            h = self.highs[i]
            prev_h = self.highs[i-1]
            if h['idx'] < len(self.df):
                close = self.df['Close'].iloc[h['idx']]
                if close > prev_h['price']:
                    self.mss_signals.append({
                        'type': 'MSS_BULL', 'idx': h['idx'], 'time': h['time'],
                        'price': round(close, 5), 'broken_level': round(prev_h['price'], 5)
                    })
                    break
        
        # MSS Bearish: close < previous swing low
        for i in range(len(self.lows)-1, 0, -1):
            l = self.lows[i]
            prev_l = self.lows[i-1]
            if l['idx'] < len(self.df):
                close = self.df['Close'].iloc[l['idx']]
                if close < prev_l['price']:
                    self.mss_signals.append({
                        'type': 'MSS_BEAR', 'idx': l['idx'], 'time': l['time'],
                        'price': round(close, 5), 'broken_level': round(prev_l['price'], 5)
                    })
                    break
        return self.mss_signals
    
    def detect_fvgs(self):
        """FVGs: gap entre candle atual e 2 velas atrás (ICT padrão)"""
        df = self.df
        pip = self.pip
        for i in range(2, len(df)):
            # Bullish FVG
            if df['Low'].iloc[i] > df['High'].iloc[i-2]:
                gap = (df['Low'].iloc[i] - df['High'].iloc[i-2]) / pip
                if gap >= self.min_fvg:
                    self.fvgs.append({
                        'type': 'BULL_FVG', 'idx': i, 'time': str(df.index[i])[:16],
                        'top': round(df['Low'].iloc[i], 5), 'bottom': round(df['High'].iloc[i-2], 5),
                        'gap_pips': round(gap, 1)
                    })
            # Bearish FVG
            elif df['High'].iloc[i] < df['Low'].iloc[i-2]:
                gap = (df['Low'].iloc[i-2] - df['High'].iloc[i]) / pip
                if gap >= self.min_fvg:
                    self.fvgs.append({
                        'type': 'BEAR_FVG', 'idx': i, 'time': str(df.index[i])[:16],
                        'top': round(df['Low'].iloc[i-2], 5), 'bottom': round(df['High'].iloc[i], 5),
                        'gap_pips': round(gap, 1)
                    })
        return self.fvgs
    
    def detect_order_blocks(self):
        """OB: extremo do trecho anterior ao rompimento (Dinei/LuxAlgo)"""
        for i in range(1, len(self.highs)):
            h = self.highs[i]
            start = self.highs[i-1]['idx']
            end = h['idx']
            if end - start > 1:
                seg = self.df.iloc[start:end]
                self.obs.append({
                    'type': 'OB_BEARISH', 'time': h['time'],
                    'high': round(seg['High'].max(), 5), 'low': round(seg['Low'].min(), 5),
                    'range_pips': round((seg['High'].max() - seg['Low'].min()) / self.pip, 1)
                })
        return self.obs
    
    def detect_liquidity(self, atr_pips=3):
        """Liquidez: clusters de swings próximos (Dinei)"""
        pip_val = self.pip * atr_pips
        for h in self.highs[-15:]:
            nearby = sum(1 for h2 in self.highs if abs(h['price'] - h2['price']) < pip_val)
            if nearby >= 2:
                self.liquidity['buyside'].append({
                    'time': h['time'], 'price': round(h['price'], 5), 'cluster_size': nearby
                })
        for l in self.lows[-15:]:
            nearby = sum(1 for l2 in self.lows if abs(l['price'] - l2['price']) < pip_val)
            if nearby >= 2:
                self.liquidity['sellside'].append({
                    'time': l['time'], 'price': round(l['price'], 5), 'cluster_size': nearby
                })
        return self.liquidity
    
    def get_fractal_bias(self):
        """Fractal: HTF = range de 2 tempos abaixo"""
        if not self.mss_signals:
            return 'NEUTRAL'
        last = self.mss_signals[-1]
        return 'BULLISH' if 'BULL' in last['type'] else 'BEARISH'
    
    def get_signal(self):
        """Gera sinal consolidado para o bot"""
        bias = self.get_fractal_bias()
        recent_fvgs = [f for f in self.fvgs if f['idx'] >= len(self.df) - 50]
        recent_liq_buy = [l for l in self.liquidity['buyside'] if l['time'] >= str(self.df.index[-50])[:16]]
        recent_liq_sell = [l for l in self.liquidity['sellside'] if l['time'] >= str(self.df.index[-50])[:16]]
        
        # Near a liquidity zone?
        price = self.df['Close'].iloc[-1]
        near_buyside = any(abs(price - l['price']) < self.pip * 10 for l in recent_liq_buy)
        near_sellside = any(abs(price - l['price']) < self.pip * 10 for l in recent_liq_sell)
        
        signal = {
            'pair': 'EURUSD',
            'timestamp': str(self.df.index[-1])[:19],
            'price': round(price, 5),
            'fractal_bias': bias,
            'swings': {'highs': len(self.highs), 'lows': len(self.lows)},
            'mss': self.mss_signals[-1] if self.mss_signals else None,
            'fvgs_recent': len(recent_fvgs),
            'fvgs_total': len(self.fvgs),
            'liquidity': {
                'near_buyside': near_buyside,
                'near_sellside': near_sellside,
                'buyside_zones': len(recent_liq_buy),
                'sellside_zones': len(recent_liq_sell)
            },
            'action': 'BUY' if bias == 'BULLISH' and near_sellside else 
                      'SELL' if bias == 'BEARISH' and near_buyside else 'WAIT',
            'confidence': 'HIGH' if (bias != 'NEUTRAL' and recent_fvgs and (near_buyside or near_sellside)) 
                          else 'MEDIUM' if bias != 'NEUTRAL' else 'LOW'
        }
        return signal


def main():
    parser = argparse.ArgumentParser(description='SMC Fractal Detector — Metodologia Dinei')
    parser.add_argument('--pair', default='EURUSD', help='Par forex (default: EURUSD)')
    parser.add_argument('--tf', default='15m', help='Timeframe (default: 15m)')
    parser.add_argument('--days', type=int, default=5, help='Dias de histórico (default: 5)')
    parser.add_argument('--pips', type=float, default=5, help='FVG mínimo em pips (default: 5)')
    parser.add_argument('--json', action='store_true', help='Saída JSON')
    args = parser.parse_args()
    
    symbol = f"{args.pair}=X"
    df = yf.Ticker(symbol).history(period=f"{args.days}d", interval=args.tf)
    
    if len(df) < 50:
        print(f"❌ Dados insuficientes: {len(df)} candles")
        sys.exit(1)
    
    pip_val = 0.01 if 'JPY' in args.pair.upper() else 0.0001
    
    detector = SMCFractalDetector(df, pip_val=1/pip_val, min_fvg_pips=args.pips)
    detector.find_swings()
    detector.detect_mss()
    detector.detect_fvgs()
    detector.detect_order_blocks()
    detector.detect_liquidity()
    signal = detector.get_signal()
    
    if args.json:
        signal['swings_detail'] = {
            'highs': [{'t': h['time'], 'p': h['price']} for h in detector.highs[-5:]],
            'lows': [{'t': l['time'], 'p': l['price']} for l in detector.lows[-5:]]
        }
        signal['fvgs_detail'] = detector.fvgs[-5:]
        print(json.dumps(signal, indent=2))
    else:
        print(f"╔══════════════════════════════════════════╗")
        print(f"║  SMC FRACTAL — {args.pair} {args.tf} ({args.days}d)     ║")
        print(f"╚══════════════════════════════════════════╝")
        print(f"  Preço: {signal['price']}")
        print(f"  Viés Fractal: {signal['fractal_bias']}")
        print(f"  Swings: {signal['swings']['highs']}H/{signal['swings']['lows']}L")
        print(f"  FVGs: {signal['fvgs_total']} total, {signal['fvgs_recent']} recentes")
        print(f"  Liquidez buyside: {signal['liquidity']['buyside_zones']} zonas")
        print(f"  Liquidez sellside: {signal['liquidity']['sellside_zones']} zonas")
        print(f"  Ação: {signal['action']} ({signal['confidence']} confiança)")
    
    # Save signal
    SIGNALS_FILE.write_text(json.dumps(signal, indent=2))


if __name__ == '__main__':
    main()
