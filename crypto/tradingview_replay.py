#!/usr/bin/env python3
"""
TRADINGVIEW REPLAY — Simula mercado histórico vela por vela
Extrai dados do TradingView e mostra como o agente reagiria em tempo real
"""
import sys, json, os, time
from pathlib import Path
from datetime import datetime, timedelta, timezone
import numpy as np

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
from tradingview_feed import TradingViewFeed
from crypto_multi_agent import CryptoConfluencia
from pattern_detector import AdvancedPatternDetector

# ═══ CONFIG ═══
RR = 3.0
MIN_CONFIDENCE = 55
REPLAY_SPEED = 0.05  # segundos por vela (0 = instantâneo)
CANDLES_TO_SHOW = 20  # quantas velas mostrar no "gráfico"

class TradingViewReplay:
    """Simula mercado histórico extraindo dados do TradingView."""
    
    def __init__(self, pair='BTCUSD', timeframe='1m', days_back=3):
        self.pair = pair
        self.timeframe = timeframe
        self.feed = TradingViewFeed()
        self.agent = CryptoConfluencia()
        self.detector = AdvancedPatternDetector()
        
        # Carregar dados
        n_bars = min(days_back * 24 * 60, 4000)
        h, l, c, o, v = self.feed.get_candles(pair, timeframe, n_bars)
        
        if c is None or len(c) < 100:
            raise Exception(f"Dados insuficientes: {len(c) if c is not None else 0} candles")
        
        self.highs = h
        self.lows = l
        self.closes = c
        self.opens = o
        self.volumes = v
        self.total_candles = len(c)
        self.current_idx = 100  # começar com 100 velas de histórico
        
        # Resultados
        self.signals = []
        self.trades = []
        self.balance = 1000  # simulado
        self.position = None
    
    def _mini_chart(self, closes, width=40, height=8):
        """Gera um mini gráfico ASCII."""
        if len(closes) < 2: return ''
        c = closes[-CANDLES_TO_SHOW:]
        mn, mx = min(c), max(c)
        if mx == mn: mx = mn + 1
        norm = [(x - mn) / (mx - mn) * (height - 1) for x in c]
        
        # Determinar cor (verde se subiu, vermelho se caiu)
        trend = '↑' if c[-1] > c[0] else '↓'
        
        result = [f'  {trend} ${c[-1]:,.2f} (${mn:,.0f} - ${mx:,.0f})']
        for row in range(height-1, -1, -1):
            line = '  '
            for val in norm:
                if round(val) == row: line += '█'
                else: line += ' '
            result.append(line)
        return '\n'.join(result)
    
    def _detect_signals(self, idx):
        """Roda o agente no ponto atual e retorna sinais."""
        h = self.highs[:idx]
        l = self.lows[:idx]
        c = self.closes[:idx]
        o = self.opens[:idx]
        v = self.volumes[:idx] if self.volumes is not None else None
        
        if len(c) < 200: return None
        
        # BTC change
        btc_chg = (c[-1] / c[-60] - 1) * 100 if len(c) >= 60 and c[-60] > 0 else 0
        
        # Análise para BUY e SELL
        results = []
        for bias in ['BUY', 'SELL']:
            daily_levels = {'resistance': max(h[-100:]), 'support': min(l[-100:])}
            
            decision, conf, signal, v_info = self.agent.analyze(
                self.pair, h, l, c, o, bias, 1.0,
                btc_chg, MIN_CONFIDENCE, v, daily_levels
            )
            
            if decision != 'NEUTRAL' and signal:
                results.append({
                    'direction': decision,
                    'entry': signal.get('entry', c[-1]),
                    'quality': signal.get('quality', 0),
                    'confidence': conf,
                    'pattern': signal.get('type', '?'),
                    'structure': signal.get('market_structure', '?'),
                    'idx': idx
                })
        
        return results
    
    def step(self):
        """Avança uma vela e retorna o estado atual."""
        if self.current_idx >= self.total_candles - 10:
            return None
        
        idx = self.current_idx
        self.current_idx += 1
        
        # Preço atual
        price = self.closes[idx]
        volume = self.volumes[idx] if self.volumes is not None else 0
        
        # Detectar sinais
        signals = self._detect_signals(idx)
        
        # Verificar trades abertos
        trade_closed = None
        if self.position:
            pos = self.position
            if pos['direction'] == 'BUY':
                if self.lows[idx] <= pos['sl']:
                    loss = pos['amount'] * (pos['sl'] - pos['entry']) / pos['entry']
                    self.balance += loss
                    trade_closed = {'result': 'LOSS', 'pnl': loss, 'exit': pos['sl']}
                    self.trades.append({**pos, **trade_closed, 'close_idx': idx})
                    self.position = None
                elif self.highs[idx] >= pos['tp']:
                    profit = pos['amount'] * (pos['tp'] - pos['entry']) / pos['entry']
                    self.balance += profit
                    trade_closed = {'result': 'WIN', 'pnl': profit, 'exit': pos['tp']}
                    self.trades.append({**pos, **trade_closed, 'close_idx': idx})
                    self.position = None
            else:
                if self.highs[idx] >= pos['sl']:
                    loss = pos['amount'] * (pos['entry'] - pos['sl']) / pos['entry']
                    self.balance += loss
                    trade_closed = {'result': 'LOSS', 'pnl': loss, 'exit': pos['sl']}
                    self.trades.append({**pos, **trade_closed, 'close_idx': idx})
                    self.position = None
                elif self.lows[idx] <= pos['tp']:
                    profit = pos['amount'] * (pos['entry'] - pos['tp']) / pos['entry']
                    self.balance += profit
                    trade_closed = {'result': 'WIN', 'pnl': profit, 'exit': pos['tp']}
                    self.trades.append({**pos, **trade_closed, 'close_idx': idx})
                    self.position = None
        
        return {
            'idx': idx,
            'price': price,
            'volume': volume,
            'signals': signals or [],
            'trade_closed': trade_closed,
            'position': self.position,
            'balance': self.balance
        }
    
    def run(self, steps=None, verbose=True):
        """Executa replay completo."""
        if steps is None:
            steps = self.total_candles - self.current_idx - 10
        
        wins = 0
        losses = 0
        
        for _ in range(steps):
            state = self.step()
            if state is None: break
            
            if verbose and REPLAY_SPEED > 0:
                # Mostrar gráfico a cada 10 velas
                if state['idx'] % 10 == 0:
                    chart = self._mini_chart(self.closes[:state['idx']])
                    print(f"\033[H\033[J")  # limpar tela
                    print(f"═══ REPLAY {self.pair} {self.timeframe} ═══")
                    print(f"Vela: {state['idx']}/{self.total_candles} | Preço: ${state['price']:,.2f}")
                    print(f"Balance: ${self.balance:.2f} | Posição: {'ABERTA' if self.position else 'LIVRE'}")
                    print(chart)
                    print(f"  {'─' * 40}")
                
                time.sleep(REPLAY_SPEED)
            
            # Executar sinais
            if state['signals'] and not self.position:
                sig = state['signals'][0]
                # Abrir trade simulado
                entry = sig['entry']
                sl_pct = 0.2
                amount = self.balance * 0.5  # 50% do capital
                
                if sig['direction'] == 'BUY':
                    sl = entry * (1 - sl_pct/100)
                    tp = entry * (1 + sl_pct*RR/100)
                else:
                    sl = entry * (1 + sl_pct/100)
                    tp = entry * (1 - sl_pct*RR/100)
                
                self.position = {
                    'direction': sig['direction'],
                    'entry': entry, 'sl': sl, 'tp': tp,
                    'amount': amount, 'quality': sig['quality'],
                    'open_idx': state['idx']
                }
                
                if verbose:
                    print(f"\n  🔔 SINAL: {sig['direction']} @{entry:.2f} Q={sig['quality']:.0f} {sig['pattern']}")
                    print(f"     SL={sl:.2f} TP={tp:.2f} | Estrutura: {sig['structure']}")
                    time.sleep(1)
            
            if state['trade_closed']:
                tc = state['trade_closed']
                emoji = '✅' if tc['result'] == 'WIN' else '❌'
                if tc['result'] == 'WIN': wins += 1
                else: losses += 1
                if verbose:
                    print(f"\n  {emoji} {tc['result']}: {'+' if tc['pnl']>0 else ''}${tc['pnl']:.2f} | Balance: ${state['balance']:.2f}")
                    time.sleep(0.5)
        
        # Resultado final
        total_trades = wins + losses
        wr = wins / total_trades * 100 if total_trades > 0 else 0
        total_pnl = self.balance - 1000
        
        print(f"\n═══ REPLAY FINALIZADO ═══")
        print(f"Trades: {total_trades} | Wins: {wins} | Losses: {losses} | WR: {wr:.1f}%")
        print(f"PnL: ${total_pnl:+.2f} | Balance final: ${self.balance:.2f}")
        
        return {'trades': total_trades, 'wins': wins, 'losses': losses, 'wr': wr, 'pnl': total_pnl}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='TradingView Replay')
    parser.add_argument('--pair', default='BTCUSD', help='Par (BTCUSD, ETHUSD, etc)')
    parser.add_argument('--tf', default='1m', help='Timeframe (1m, 5m, 15m)')
    parser.add_argument('--days', type=int, default=2, help='Dias para trás (máx 3)')
    parser.add_argument('--speed', type=float, default=0.01, help='Segundos por vela (0=instantâneo)')
    parser.add_argument('--steps', type=int, default=500, help='Número de velas (0=todas)')
    args = parser.parse_args()
    
    REPLAY_SPEED = args.speed
    
    print(f"Carregando {args.pair} {args.tf} ({args.days} dias)...")
    replay = TradingViewReplay(pair=args.pair, timeframe=args.tf, days_back=args.days)
    print(f"Dados: {replay.total_candles} velas")
    print()
    
    result = replay.run(steps=args.steps if args.steps > 0 else None, verbose=True)
