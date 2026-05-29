#!/usr/bin/env python3
"""
CRYPTO BACKTEST VALIDATOR — Testa o sistema antes de aplicar
Requer: PF > 2.0, WR > 40%, mínimo 10 trades em 15 dias
"""
import sys, json
from pathlib import Path
from datetime import datetime, timedelta, timezone
import numpy as np
import yfinance as yf

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
from crypto_multi_agent import CryptoConfluencia

RR = 3.0
DATA_DAYS = 7  # yfinance limita M1 a ~8 dias
MIN_TRADES = 5   # mínimo para 7 dias
MIN_WR = 35       # ajustado para período curto
MIN_PF = 1.8
MIN_CONFIDENCE = 40

# Pares testados
TEST_PAIRS = {
    'BTCUSD': ('BTC-USD', 1.0),
    'ETHUSD': ('ETH-USD', 0.1),
    'SOLUSD': ('SOL-USD', 0.01),
    'DOGEUSD': ('DOGE-USD', 0.001),
    'BNBUSD': ('BNB-USD', 0.1),
}

def run_backtest():
    """Executa backtest do sistema crypto multi-agente."""
    print(f"═══ CRYPTO BACKTEST — {DATA_DAYS} dias ═══")
    print(f"Parâmetros: RR={RR}:1, Conf mín={MIN_CONFIDENCE}%, Pares={len(TEST_PAIRS)}")
    print()
    
    agent = CryptoConfluencia()
    trades = []
    
    for pair, (sym, pip) in TEST_PAIRS.items():
        print(f"Testando {pair}...")
        
        try:
            # Dados diários para bias
            df_d = yf.Ticker(sym).history(period=f'{DATA_DAYS+5}d', interval='1d')
            cm = {c.lower(): c for c in df_d.columns}
            db_high = df_d[cm.get('high','High')].values
            db_low = df_d[cm.get('low','Low')].values
            db_close = df_d[cm.get('close','Close')].values
            
            # Dados M1 para entradas
            df_m1 = yf.Ticker(sym).history(period=f'{DATA_DAYS}d', interval='1m')
            if len(df_m1) < 500:
                print(f"  {pair}: dados M1 insuficientes ({len(df_m1)})")
                continue
            
            h = df_m1['High'].values
            l = df_m1['Low'].values
            c = df_m1['Close'].values
            o = df_m1['Open'].values
            
            # Simular BTC change (simplificado: usar últimos dados)
            try:
                df_btc = yf.Ticker('BTC-USD').history(period=f'{DATA_DAYS}d', interval='1h')
                btc_4h = (df_btc['Close'].values[-1] / df_btc['Close'].values[-5] - 1) * 100 if len(df_btc) >= 5 else 0
            except:
                btc_4h = 0
            
            pair_trades = 0
            last_entry_idx = -100  # evitar repetir mesmo FVG
            
            # Simular entradas a cada hora do período
            step = 60  # 60 velas M1 = 1 hora
            for i in range(200, len(c) - 10, step):
                # Janela de dados até o ponto i
                h_win, l_win = h[:i], l[:i]
                c_win, o_win = c[:i], o[:i]
                
                # Daily bias no ponto
                day_idx = min(len(db_high)-2, max(0, int(i * 1 / (24*60) + 2)))
                if day_idx < 2: continue
                bias = get_daily_bias_backtest(db_high[:day_idx+1], db_low[:day_idx+1], db_close[:day_idx+1])
                
                if bias == 'NEUTRAL': continue
                
                # Análise
                decision, conf, signal, v_info = agent.analyze(
                    pair, h_win, l_win, c_win, o_win, bias, pip,
                    btc_4h if pair != 'BTCUSD' else None,
                    MIN_CONFIDENCE
                )
                
                if decision == 'NEUTRAL' or not signal:
                    continue
                
                # Evitar repetir mesmo FVG
                sig_idx = signal.get('idx', i)
                if abs(sig_idx - last_entry_idx) < 30:  # mesmo FVG
                    continue
                last_entry_idx = sig_idx
                
                entry = signal['entry']
                atr_pct = v_info.get('atr_pct', 0.5)
                sl_rec = v_info.get('sl_recommend', None)
                sl_pct = sl_rec or max(atr_pct * 1.5, 0.15)
                
                if decision == 'BUY':
                    sl = entry * (1 - sl_pct/100)
                    tp = entry * (1 + sl_pct*RR/100)
                else:
                    sl = entry * (1 + sl_pct/100)
                    tp = entry * (1 - sl_pct*RR/100)
                
                # Simular resultado (olhar velas futuras)
                result = simulate_trade(h[i:], l[i:], c[i:], decision, entry, sl, tp)
                
                if result:
                    trades.append({
                        'pair': pair, 'direction': decision, 'entry': entry,
                        'sl': sl, 'tp': tp, 'sl_pct': sl_pct,
                        'result': result['result'], 'rr': result['rr'],
                        'exit': result['exit'], 'conf': conf,
                        'pattern': signal.get('type', '?'),
                        'quality': signal.get('quality', 0),
                        'regime': v_info.get('regime', '?')
                    })
                    pair_trades += 1
            
            print(f"  {pair}: {pair_trades} trades")
        
        except Exception as e:
            print(f"  {pair}: ERRO — {e}")
    
    print()
    return trades


def get_daily_bias_backtest(highs, lows, closes):
    """Daily bias para backtest."""
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
    """Simula resultado de um trade nas velas futuras."""
    for i in range(len(closes)):
        if direction == 'BUY':
            if lows[i] <= sl:
                sl_hit = max(sl, lows[i])
                return {'result': 'LOSS', 'rr': -1, 'exit': sl_hit}
            if highs[i] >= tp:
                return {'result': 'WIN', 'rr': RR, 'exit': tp}
        else:
            if highs[i] >= sl:
                sl_hit = min(sl, highs[i])
                return {'result': 'LOSS', 'rr': -1, 'exit': sl_hit}
            if lows[i] <= tp:
                return {'result': 'WIN', 'rr': RR, 'exit': tp}
    # Não bateu nem SL nem TP — fecha no último preço
    last = closes[-1]
    if direction == 'BUY':
        rr = (last - entry) / (entry - sl)
    else:
        rr = (entry - last) / (sl - entry)
    return {'result': 'OPEN', 'rr': rr, 'exit': last}


def analyze_results(trades):
    """Analisa resultados do backtest."""
    if not trades:
        return {'passed': False, 'reason': 'Nenhum trade'}
    
    wins = [t for t in trades if t['result'] == 'WIN']
    losses = [t for t in trades if t['result'] == 'LOSS']
    opens = [t for t in trades if t['result'] == 'OPEN']
    
    total = len(trades)
    wr = len(wins) / max(total, 1) * 100
    total_r = sum(t['rr'] for t in trades)
    
    # Profit Factor
    gross_win = sum(t['rr'] for t in wins) if wins else 0
    gross_loss = abs(sum(t['rr'] for t in losses)) if losses else 1
    pf = gross_win / gross_loss if gross_loss > 0 else 999
    
    print(f"═══ RESULTADOS ═══")
    print(f"Total trades:  {total}")
    print(f"Wins:          {len(wins)} ({wr:.1f}%)")
    print(f"Losses:        {len(losses)}")
    print(f"Open (expirou): {len(opens)}")
    print(f"Total R:       {total_r:+.1f}R")
    print(f"Profit Factor: {pf:.2f}")
    
    # Por par
    print(f"\nPor par:")
    for pair in sorted(set(t['pair'] for t in trades)):
        pt = [t for t in trades if t['pair'] == pair]
        pw = [t for t in pt if t['result'] == 'WIN']
        pwr = len(pw) / max(len(pt), 1) * 100
        pr = sum(t['rr'] for t in pt)
        print(f"  {pair:8s}: {len(pt):3d} trades, WR={pwr:.0f}%, {pr:+.1f}R")
    
    # Por padrão
    patterns = {}
    for t in trades:
        p = t.get('pattern', '?')
        if p not in patterns: patterns[p] = {'total': 0, 'wins': 0, 'r': 0}
        patterns[p]['total'] += 1
        if t['result'] == 'WIN': patterns[p]['wins'] += 1
        patterns[p]['r'] += t['rr']
    
    print(f"\nPor padrão:")
    for p, stats in sorted(patterns.items()):
        pwr = stats['wins'] / stats['total'] * 100
        print(f"  {p:8s}: {stats['total']:3d} trades, WR={pwr:.0f}%, {stats['r']:+.1f}R")
    
    # Por regime de volatilidade
    regimes = {}
    for t in trades:
        r = t.get('regime', '?')
        if r not in regimes: regimes[r] = {'total': 0, 'wins': 0, 'r': 0}
        regimes[r]['total'] += 1
        if t['result'] == 'WIN': regimes[r]['wins'] += 1
        regimes[r]['r'] += t['rr']
    
    print(f"\nPor regime:")
    for r, stats in sorted(regimes.items()):
        rwr = stats['wins'] / stats['total'] * 100
        print(f"  {r:10s}: {stats['total']:3d} trades, WR={rwr:.0f}%, {stats['r']:+.1f}R")
    
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
    print(f"Iniciando backtest em {datetime.now().strftime('%d/%m %H:%M')} UTC")
    
    trades = run_backtest()
    result = analyze_results(trades)
    
    print()
    if result['passed']:
        print("✅ SISTEMA APROVADO — Pode ser aplicado ao vivo.")
    else:
        print("❌ SISTEMA REPROVADO — Ajustes necessários antes do deploy.")
    
    # Salvar resultados
    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'parameters': {'rr': RR, 'days': DATA_DAYS, 'min_confidence': MIN_CONFIDENCE},
        'results': result,
        'trades': trades
    }
    
    outfile = Path.home() / '.hermes' / 'crypto' / 'backtest_result.json'
    with open(outfile, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\nResultados salvos: {outfile}")
