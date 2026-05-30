#!/usr/bin/env python3
"""
CRYPTO BACKTEST LONGO — M5 para 60 dias
Parâmetros dos agentes ajustados proporcionalmente para M5
"""
import sys, json
from pathlib import Path
from datetime import datetime, timedelta, timezone
import numpy as np
from tradingview_feed import TradingViewFeed

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))

# ═══ Versão adaptada dos agentes para M5 ═══
# Como não podemos modificar o módulo, vamos reimplementar a lógica
# com timeframes ajustados: M15→H1, M5→M15, M1→M5

class TendenciaAgentM5:
    """Multi-TF adaptado para M5: usa H1/M15/M5 em vez de M15/M5/M1."""
    
    def analyze_tf(self, closes, period, label):
        if len(closes) < period * 2: return 'NEUTRAL', 0, []
        half = period // 2
        ema_fast = sum(closes[-half:]) / half
        ema_slow = sum(closes[-period:]) / period
        if closes[-1] > ema_fast > ema_slow:
            return 'BUY', 35, [f'{label}↑']
        elif closes[-1] < ema_fast < ema_slow:
            return 'SELL', 35, [f'{label}↓']
        return 'NEUTRAL', 0, []
    
    def analyze(self, highs, lows, closes):
        if len(closes) < 48: return 'NEUTRAL', 0, ''  # precisa de ~4h de dados
        
        # H1 = 12 velas M5
        h1_dir, h1_score, h1_sig = self.analyze_tf(closes, 12, 'H1')
        if h1_dir == 'NEUTRAL': return 'NEUTRAL', 0, 'H1 neutro'
        
        # M15 = 3 velas M5... muito pouco. Usar 6 (30 min)
        m15_dir, m15_score, m15_sig = self.analyze_tf(closes[-96:] if len(closes)>=96 else closes, 6, 'M15')
        if m15_dir != h1_dir:
            return 'NEUTRAL', 0, f'M15 diverge'
        
        total_score = h1_score + m15_score
        signals = h1_sig + m15_sig
        
        # M5 timing
        m5_dir, m5_score, m5_sig = self.analyze_tf(closes[-48:] if len(closes)>=48 else closes, 3, 'M5')
        if m5_dir == h1_dir:
            total_score += 15
            signals.append('⏱M5')
        
        # S/R
        window = closes[-48:]
        hh, ll = max(window), min(window)
        pos = (closes[-1] - ll) / (hh - ll) if hh > ll else 0.5
        if h1_dir == 'BUY' and pos < 0.50:
            total_score += 15; signals.append('Discount')
        elif h1_dir == 'SELL' and pos > 0.50:
            total_score += 15; signals.append('Premium')
        
        if total_score >= 55:
            return h1_dir, total_score, '|'.join(signals)
        return 'NEUTRAL', total_score, f'Score={total_score}'


class VolatilidadeAgentM5:
    """ATR adaptado para M5."""
    
    def analyze(self, highs, lows, closes):
        n = len(closes)
        if n < 14: return {'regime': 'DESCONHECIDO', 'atr_pct': 0, 'sl_recommend': 0.3}
        tr = [max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
              for i in range(1, min(20, n))]
        atr = sum(tr[-14:]) / 14 if len(tr) >= 14 else sum(tr) / len(tr)
        atr_pct = atr / closes[-1] * 100
        
        if atr_pct > 0.8: regime, sl_rec = 'ALTA_VOL', 0.8
        elif atr_pct > 0.25: regime, sl_rec = 'MEDIA_VOL', 0.4
        elif atr_pct > 0.10: regime, sl_rec = 'NORMAL', 0.25
        else: regime, sl_rec = 'BAIXA_VOL', 0.15
        
        return {'regime': regime, 'atr_pct': round(atr_pct, 3), 'sl_recommend': min(sl_rec, 2.0)}


# ═══ CONFIG ═══
RR = 3.0
MIN_CONFIDENCE = 55
DATA_DAYS = 60  # 60 dias de M5 (máximo yfinance)
MIN_TRADES = 20
MIN_WR = 45
MIN_PF = 2.0

TEST_PAIRS = {
    'BTCUSD': ('BTC-USD', 1.0),
    'ETHUSD': ('ETH-USD', 0.1),
    'DOGEUSD': ('DOGE-USD', 0.001),
    'BNBUSD': ('BNB-USD', 0.1),
}

def get_daily_bias_backtest(highs, lows, closes):
    if len(highs) < 3: return 'NEUTRAL'
    ph, pl = highs[-3], lows[-3]
    ch, cl, cc = highs[-2], lows[-2], closes[-2]
    if ch > ph and cc > ph: return 'BUY'
    if cl < pl and cc < pl: return 'SELL'
    if ch > ph and cc < ph: return 'SELL'
    if cl < pl and cc > pl: return 'BUY'
    if cc > closes[-3]: return 'BUY'
    if cc < closes[-3]: return 'SELL'
    return 'NEUTRAL'

def simulate_trade(highs, lows, closes, direction, entry, sl, tp):
    for i in range(len(closes)):
        if direction == 'BUY':
            if lows[i] <= sl: return {'result': 'LOSS', 'rr': -1, 'exit': max(sl, lows[i])}
            if highs[i] >= tp: return {'result': 'WIN', 'rr': RR, 'exit': tp}
        else:
            if highs[i] >= sl: return {'result': 'LOSS', 'rr': -1, 'exit': min(sl, highs[i])}
            if lows[i] <= tp: return {'result': 'WIN', 'rr': RR, 'exit': tp}
    last = closes[-1]
    if direction == 'BUY': rr = (last - entry) / (entry - sl)
    else: rr = (entry - last) / (sl - entry)
    return {'result': 'OPEN', 'rr': rr, 'exit': last}

def run_backtest():
    from pattern_detector import AdvancedPatternDetector
    
    print(f"═══ CRYPTO BACKTEST LONGO (M5) — {DATA_DAYS} dias ═══")
    print(f"Parâmetros: RR={RR}:1, Conf mín={MIN_CONFIDENCE}%, Pares={len(TEST_PAIRS)}")
    print()
    
    detector = AdvancedPatternDetector()
    trend = TendenciaAgentM5()
    vol = VolatilidadeAgentM5()
    trades = []
    
    for pair, (sym, pip) in TEST_PAIRS.items():
        print(f"Testando {pair}...")
        
        try:
            df_m5 = yf.Ticker(sym).history(period=f'{DATA_DAYS}d', interval='5m')
            if len(df_m5) < 200:
                print(f"  {pair}: dados M5 insuficientes ({len(df_m5)})")
                continue
            
            h = df_m5['High'].values
            l = df_m5['Low'].values
            c = df_m5['Close'].values
            o = df_m5['Open'].values
            
            # Daily bias
            df_d = yf.Ticker(sym).history(period=f'{DATA_DAYS+5}d', interval='1d')
            cm = {c.lower(): c for c in df_d.columns}
            db_h = df_d[cm.get('high','High')].values
            db_l = df_d[cm.get('low','Low')].values
            db_c = df_d[cm.get('close','Close')].values
            
            pair_trades = 0
            last_entry_idx = -100
            
            # Escanear a cada 6 velas M5 (30 min)
            step = 6
            for i in range(100, len(c) - 10, step):
                h_win, l_win = h[:i], l[:i]
                c_win, o_win = c[:i], o[:i]
                
                if len(c_win) < 48: continue
                
                # Daily bias
                day_idx = min(len(db_h)-2, max(0, int(i * 5 / (24*60) + 2)))
                if day_idx < 2: continue
                bias = get_daily_bias_backtest(db_h[:day_idx+1], db_l[:day_idx+1], db_c[:day_idx+1])
                if bias == 'NEUTRAL': continue
                
                # Volatilidade
                v_info = vol.analyze(h_win, l_win, c_win)
                
                # Tendência
                t_dir, t_conf, t_msg = trend.analyze(h_win, l_win, c_win)
                if t_dir == 'NEUTRAL': continue
                
                # Padrão
                pat, score = detector.find_best_pattern(h_win, l_win, c_win, o_win, t_dir)
                if not pat or score < 50: continue
                
                # Market Structure gate
                ms = pat.get('market_structure', '')
                if ms == 'BEARISH' and t_dir == 'BUY' and not pat.get('choch'):
                    continue
                if ms == 'BULLISH' and t_dir == 'SELL' and not pat.get('choch'):
                    continue
                
                # Evitar repetir
                sig_idx = pat.get('idx', i)
                if abs(sig_idx - last_entry_idx) < 10: continue
                last_entry_idx = sig_idx
                
                entry = pat['entry']
                sl_pct = v_info.get('sl_recommend', 0.25)
                
                if t_dir == 'BUY':
                    sl = entry * (1 - sl_pct/100)
                    tp = entry * (1 + sl_pct*RR/100)
                else:
                    sl = entry * (1 + sl_pct/100)
                    tp = entry * (1 - sl_pct*RR/100)
                
                result = simulate_trade(h[i:], l[i:], c[i:], t_dir, entry, sl, tp)
                
                if result:
                    # Estimar confiança
                    conf = min(90, score + (15 if ms in ('BULLISH','BEARISH') and t_dir == ('BUY' if ms=='BULLISH' else 'SELL') else 0))
                    
                    trades.append({
                        'pair': pair, 'direction': t_dir, 'entry': entry,
                        'sl': sl, 'tp': tp, 'sl_pct': sl_pct,
                        'result': result['result'], 'rr': result['rr'],
                        'exit': result['exit'], 'conf': conf,
                        'pattern': pat.get('type', '?'),
                        'quality': score,
                        'market_structure': ms,
                        'regime': v_info.get('regime', '?'),
                    })
                    pair_trades += 1
            
            print(f"  {pair}: {pair_trades} trades")
        
        except Exception as e:
            print(f"  {pair}: ERRO — {e}")
            import traceback
            traceback.print_exc()
    
    print()
    return trades


def analyze_results(trades):
    if not trades:
        return {'passed': False, 'reason': 'Nenhum trade'}
    
    wins = [t for t in trades if t['result'] == 'WIN']
    losses = [t for t in trades if t['result'] == 'LOSS']
    opens = [t for t in trades if t['result'] == 'OPEN']
    
    total = len(trades)
    wr = len(wins) / max(total, 1) * 100
    total_r = sum(t['rr'] for t in trades)
    gross_win = sum(t['rr'] for t in wins) if wins else 0
    gross_loss = abs(sum(t['rr'] for t in losses)) if losses else 1
    pf = gross_win / gross_loss if gross_loss > 0 else 999
    
    print(f"═══ RESULTADOS — {DATA_DAYS} dias M5 ═══")
    print(f"Total trades:  {total}")
    print(f"Wins:          {len(wins)} ({wr:.1f}%)")
    print(f"Losses:        {len(losses)}")
    print(f"Open:          {len(opens)}")
    print(f"Total R:       {total_r:+.1f}R")
    print(f"Profit Factor: {pf:.2f}")
    
    # Por par
    print(f"\nPor par:")
    for pair in sorted(set(t['pair'] for t in trades)):
        pt = [t for t in trades if t['pair'] == pair]
        pw = [t for t in pt if t['result'] == 'WIN']
        pwr = len(pw) / max(len(pt), 1) * 100
        pr = sum(t['rr'] for t in pt)
        print(f"  {pair:8s}: {len(pt):4d} trades, WR={pwr:.0f}%, {pr:+.1f}R")
    
    # Por estrutura
    structures = {}
    for t in trades:
        s = t.get('market_structure', '?')
        if s not in structures: structures[s] = {'t': 0, 'w': 0, 'r': 0}
        structures[s]['t'] += 1
        structures[s]['r'] += t['rr']
        if t['result'] == 'WIN': structures[s]['w'] += 1
    
    print(f"\nPor Market Structure:")
    for s, st in sorted(structures.items()):
        if st['t'] < 3: continue
        swr = st['w']/st['t']*100
        print(f"  {s:10s}: {st['t']:4d} trades, WR={swr:.0f}%, {st['r']:+.1f}R")
    
    # Validação
    print(f"\n═══ VALIDAÇÃO ═══")
    checks = [
        (f"≥{MIN_TRADES} trades", total >= MIN_TRADES, f"{total} trades"),
        (f"WR ≥{MIN_WR}%", wr >= MIN_WR, f"{wr:.1f}%"),
        (f"PF ≥{MIN_PF}", pf >= MIN_PF, f"{pf:.2f}"),
    ]
    all_pass = True
    for check, result, value in checks:
        status = "✅" if result else "❌"
        if not result: all_pass = False
        print(f"  {status} {check}: {value}")
    
    return {'passed': all_pass, 'total': total, 'wr': wr, 'pf': pf,
            'total_r': total_r, 'wins': len(wins), 'losses': len(losses)}


if __name__ == '__main__':
    print(f"Iniciando backtest longo em {datetime.now().strftime('%d/%m %H:%M')} UTC")
    trades = run_backtest()
    result = analyze_results(trades)
    
    if result['passed']:
        print(f"\n✅ SISTEMA APROVADO — Performance consistente em {DATA_DAYS} dias")
    else:
        print(f"\n❌ SISTEMA REPROVADO — Ajustes necessários")
    
    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'parameters': {'rr': RR, 'days': DATA_DAYS, 'timeframe': 'M5'},
        'results': result,
        'trades': trades
    }
    outfile = Path.home() / '.hermes' / 'crypto' / 'backtest_30d.json'
    with open(outfile, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nResultados salvos: {outfile}")
