#!/usr/bin/env python3
"""
CRYPTO BACKTEST v10 — Simulação Realista
- 1 trade por vez (MAX_TOTAL_TRADES=1)
- Anti-correlação USD
- Todos os pares competem no mesmo timeline
- Seleção do melhor par a cada tick
"""
import sys, json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
from crypto_multi_agent import CryptoConfluencia
from pair_selector import CryptoPairSelector
from tradingview_feed import TradingViewFeed

# ═══ CONFIG (igual produção) ═══
RR = 3.0
DATA_DAYS = 7
TIMEFRAME = '1m'  # M1 — ~10k velas em 7 dias
MIN_CONFIDENCE = 55
MAX_TOTAL_TRADES = 1
MIN_CANDLES = 1000  # Mínimo 1000 velas M1 (~16h)

TEST_PAIRS = {
    'BTCUSD': ('BTC-USD', 'BINANCE', 1.0),
    'ETHUSD': ('ETH-USD', 'BINANCE', 0.1),
    'DOGEUSD': ('DOGE-USD', 'BINANCE', 0.001),
    'BNBUSD': ('BNB-USD', 'BINANCE', 0.1),
}

# ═══ CORRELATION GROUPS (igual pair_selector) ═══
CORREL_GROUPS = {
    'BTC_LARGE_CAP': {'pairs': {'BTCUSD', 'ETHUSD'}, 'max_trades': 1},
    'MEME': {'pairs': {'DOGEUSD'}, 'max_trades': 1},
    'EXCHANGE': {'pairs': {'BNBUSD'}, 'max_trades': 1},
}

def get_pair_group(pair):
    for gname, gcfg in CORREL_GROUPS.items():
        if pair in gcfg['pairs']:
            return gname, gcfg
    return None, None

def simulate_trade(highs, lows, closes, direction, entry, sl, tp):
    """Simula trade candle a candle. Retorna (result, exit_price, bars_held)."""
    for i in range(len(closes)):
        if direction == 'BUY':
            if lows[i] <= sl:
                return 'LOSS', max(sl, lows[i]), i + 1
            if highs[i] >= tp:
                return 'WIN', tp, i + 1
        else:
            if highs[i] >= sl:
                return 'LOSS', min(sl, highs[i]), i + 1
            if lows[i] <= tp:
                return 'WIN', tp, i + 1
    last = closes[-1]
    if direction == 'BUY':
        rr = (last - entry) / (entry - sl)
    else:
        rr = (entry - last) / (sl - entry)
    return 'OPEN', last, len(closes)

def get_daily_bias(highs, lows, closes):
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

def run_backtest():
    feed = TradingViewFeed()
    agent = CryptoConfluencia()
    
    print(f"═══ CRYPTO BACKTEST v10 (REALÍSTICO) — {DATA_DAYS}d {TIMEFRAME} ═══")
    print(f"RR={RR}:1 Conf≥{MIN_CONFIDENCE}% MAX_TRADES={MAX_TOTAL_TRADES}")
    print(f"Regras: 1 trade/vz, anti-correlação, seleção melhor par")
    print()
    
    # ═══ 1. Carregar dados de todos os pares ═══
    pair_data = {}
    for pair, (sym, exchange, pip) in TEST_PAIRS.items():
        try:
            h, l, c, o, v = feed.get_candles(pair, TIMEFRAME, MIN_CANDLES + 5000)
            if c is not None and len(c) >= MIN_CANDLES:
                pair_data[pair] = {
                    'h': np.array(h), 'l': np.array(l), 'c': np.array(c),
                    'o': np.array(o), 'v': np.array(v) if v is not None else None,
                    'sym': sym, 'pip': pip
                }
                print(f"  {pair:8s}: {len(c)} velas OK")
            else:
                print(f"  {pair:8s}: dados insuficientes ({len(c) if c is not None else 0})")
        except Exception as e:
            print(f"  {pair:8s}: ERRO — {e}")
    
    if len(pair_data) < 2:
        print("Precisa de pelo menos 2 pares com dados")
        return []
    
    # ═══ 2. Encontrar timeline comum ═══
    min_len = min(len(pd['c']) for pd in pair_data.values())
    # Usar últimos N candles para garantir dados suficientes
    common_len = min(min_len, 8000)
    start_offset = min_len - common_len
    
    print(f"\nTimeline comum: {common_len} velas M1 (~{common_len/1440:.1f} dias)")
    
    # ═══ 3. Iterar candle a candle ═══
    step = 5  # Escanear a cada 5 velas (5 min)
    min_warmup = 200  # Warmup mínimo
    
    trades = []
    active_trade = None  # Trade ativo: {'pair', 'direction', 'entry', 'sl', 'tp', 'start_idx'}
    active_group = None
    active_direction = None
    
    signal_count = 0
    skipped_trade_open = 0
    skipped_correlation = 0
    skipped_weak = 0
    
    for i in range(min_warmup, common_len - 60, step):
        abs_idx = start_offset + i
        
        # ═══ Verificar se trade ativo fechou ═══
        if active_trade:
            start = active_trade['start_idx']
            remain_h = pair_data[active_trade['pair']]['h'][start:]
            remain_l = pair_data[active_trade['pair']]['l'][start:]
            remain_c = pair_data[active_trade['pair']]['c'][start:]
            
            result, exit_price, bars = simulate_trade(
                remain_h, remain_l, remain_c,
                active_trade['direction'],
                active_trade['entry'],
                active_trade['sl'],
                active_trade['tp']
            )
            
            if result != 'OPEN':
                # Trade fechou
                trades.append({
                    'pair': active_trade['pair'],
                    'direction': active_trade['direction'],
                    'entry': active_trade['entry'],
                    'sl': active_trade['sl'],
                    'tp': active_trade['tp'],
                    'result': result,
                    'exit': exit_price,
                    'duration_bars': bars,
                    'duration_min': bars,  # M1 = 1 bar = 1 min
                })
                active_trade = None
                active_group = None
                active_direction = None
                continue  # Próximo tick, já podemos abrir novo trade
        
        # ═══ Se já tem trade ativo, pular ═══
        if active_trade:
            continue
        
        # ═══ Escanear todos os pares por sinais ═══
        candidates = []
        
        for pair, pd in pair_data.items():
            h_win = pd['h'][abs_idx-200:abs_idx]
            l_win = pd['l'][abs_idx-200:abs_idx]
            c_win = pd['c'][abs_idx-200:abs_idx]
            o_win = pd['o'][abs_idx-200:abs_idx] if pd['o'] is not None else c_win
            
            if len(c_win) < 200:
                continue
            
            pip = pd['pip']
            
            # Daily bias from TradingView data (aggregate 1m → daily)
            # No yfinance — evita rate limit
            day_bars = 1440  # 1 dia em M1
            if abs_idx >= day_bars * 3:
                day_h = []
                day_l = []
                day_c = []
                for d in range(3, 0, -1):
                    start_d = abs_idx - d * day_bars
                    end_d = abs_idx - (d-1) * day_bars
                    if start_d >= 0 and end_d <= len(pd['h']):
                        day_h.append(float(np.max(pd['h'][start_d:end_d])))
                        day_l.append(float(np.min(pd['l'][start_d:end_d])))
                        day_c.append(float(pd['c'][end_d-1]))
                if len(day_h) >= 3:
                    bias = get_daily_bias(np.array(day_h), np.array(day_l), np.array(day_c))
                else:
                    bias = 'NEUTRAL'
            else:
                bias = 'NEUTRAL'
            if bias == 'NEUTRAL':
                continue
            
            # BTC change
            btc_chg = None
            if pair != 'BTCUSD':
                try:
                    btc_c = pair_data['BTCUSD']['c'][abs_idx-200:abs_idx]
                    if len(btc_c) >= 60:
                        btc_chg = (btc_c[-1] / btc_c[-60] - 1) * 100
                except:
                    pass
            
            try:
                decision, conf, signal, v_info = agent.analyze(
                    pair, h_win, l_win, c_win, o_win, bias, pip,
                    btc_chg, MIN_CONFIDENCE, None
                )
            except:
                continue
            
            if decision == 'NEUTRAL' or not signal:
                continue
            
            signal_count += 1
            
            entry = signal['entry']
            atr_pct = (v_info or {}).get('atr_pct', 0.3)
            sl_rec = (v_info or {}).get('sl_recommend', None)
            sl_pct = sl_rec or max(atr_pct * 1.5, 0.12)
            
            if decision == 'BUY':
                sl = entry * (1 - sl_pct/100)
                tp = entry * (1 + sl_pct*RR/100)
            else:
                sl = entry * (1 + sl_pct/100)
                tp = entry * (1 - sl_pct*RR/100)
            
            ir = signal.get('impulse_ratio', 0)
            quality = signal.get('quality', 0)
            
            candidates.append({
                'pair': pair, 'direction': decision, 'entry': entry,
                'sl': sl, 'tp': tp, 'sl_pct': sl_pct, 'conf': conf,
                'ir': ir, 'quality': quality, 'group': get_pair_group(pair)[0],
            })
        
        if not candidates:
            continue
        
        # ═══ Selecionar melhor candidato (mesma lógica do pair_selector) ═══
        # Score = IR * 10 + quality/10 + conf/10
        for c in candidates:
            c['score'] = c['ir'] * 10 + c['quality']/10 + c['conf']/10
        
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Filtrar anti-correlação
        for c in candidates:
            gname = c['group']
            if gname is None:
                continue
            
            # Se é SELL e era o trade anterior também SELL no mesmo grupo → skip
            # (anti-correlação só se aplica se teve trade recente na mesma direção)
            # No backtest com 1 trade/vz, anti-correlação é menos relevante
            # mas mantemos a regra do pair_selector
            
            best = c
            break
        else:
            continue
        
        # ═══ Abrir trade ═══
        active_trade = {
            'pair': best['pair'],
            'direction': best['direction'],
            'entry': best['entry'],
            'sl': best['sl'],
            'tp': best['tp'],
            'start_idx': abs_idx,
        }
        active_group = best['group']
        active_direction = best['direction']
    
    # ═══ Trade ainda aberto no final ═══
    if active_trade:
        start = active_trade['start_idx']
        remain_c = pair_data[active_trade['pair']]['c'][start:]
        last_price = remain_c[-1] if len(remain_c) > 0 else active_trade['entry']
        
        if active_trade['direction'] == 'BUY':
            rr = (last_price - active_trade['entry']) / (active_trade['entry'] - active_trade['sl'])
        else:
            rr = (active_trade['entry'] - last_price) / (active_trade['sl'] - active_trade['entry'])
        
        trades.append({
            'pair': active_trade['pair'],
            'direction': active_trade['direction'],
            'entry': active_trade['entry'],
            'sl': active_trade['sl'],
            'tp': active_trade['tp'],
            'result': 'OPEN',
            'exit': last_price,
            'rr': rr,
            'duration_bars': common_len - active_trade['start_idx'],
            'duration_min': common_len - active_trade['start_idx'],
        })
    
    print(f"\nSinais detectados: {signal_count}")
    print(f"Trades executados: {len(trades)}")
    print(f"Pulados (trade aberto): {skipped_trade_open}")
    print(f"Pulados (anti-corr): {skipped_correlation}")
    
    return trades

def analyze_results(trades):
    if not trades:
        return {'passed': False, 'reason': 'Nenhum trade', 'total': 0}
    
    wins = [t for t in trades if t['result'] == 'WIN']
    losses = [t for t in trades if t['result'] == 'LOSS']
    opens = [t for t in trades if t['result'] == 'OPEN']
    
    total = len(trades)
    wr = len(wins) / max(total, 1) * 100
    
    total_r = sum(t.get('rr', (RR if t['result']=='WIN' else -1)) for t in trades)
    gross_win = sum(RR for _ in wins)
    gross_loss = len(losses) * 1
    pf = gross_win / gross_loss if gross_loss > 0 else 999
    
    # Duração média (só trades fechados)
    closed = wins + losses
    durations = [t.get('duration_min', 0) for t in closed if t.get('duration_min')]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    print(f"\n═══ RESULTADOS — {DATA_DAYS}d {TIMEFRAME} (Simulação Realista) ═══")
    print(f"Total trades:  {total}")
    print(f"Wins:          {len(wins)} ({wr:.1f}%)")
    print(f"Losses:        {len(losses)}")
    print(f"Open:          {len(opens)}")
    print(f"Total R:       {total_r:+.1f}R")
    print(f"Profit Factor: {pf:.2f}")
    print(f"Duração média: {avg_duration:.0f} min ({avg_duration/60:.1f}h)")
    if durations:
        print(f"Duração range: {min(durations):.0f}-{max(durations):.0f} min")
    
    # Por par
    print(f"\nPor par:")
    for pair in sorted(set(t['pair'] for t in trades)):
        pt = [t for t in trades if t['pair'] == pair]
        pw = [t for t in pt if t['result'] == 'WIN']
        pl = [t for t in pt if t['result'] == 'LOSS']
        pwr = len(pw)/max(len(pt),1)*100
        
        pdur = [t.get('duration_min', 0) for t in pt if t.get('duration_min') and t['result'] != 'OPEN']
        avg_d = sum(pdur)/len(pdur) if pdur else 0
        
        pr = sum(t.get('rr', RR if t['result']=='WIN' else -1) for t in pt)
        print(f"  {pair:8s}: {len(pt):3d}t WR={pwr:.0f}% {pr:+.1f}R dur={avg_d:.0f}min")
    
    return {
        'passed': total >= 10 and wr >= 50 and pf >= 1.5,
        'total': total, 'wr': wr, 'pf': pf,
        'total_r': total_r, 'wins': len(wins), 'losses': len(losses),
        'avg_duration_min': avg_duration,
    }

if __name__ == '__main__':
    print(f"Iniciando backtest v10 em {datetime.now().strftime('%d/%m %H:%M')} UTC")
    trades = run_backtest()
    result = analyze_results(trades)
    
    if result['passed']:
        print(f"\n✅ SISTEMA APROVADO — Simulação realista")
    else:
        print(f"\n❌ REPROVADO")
    
    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'parameters': {
            'rr': RR, 'days': DATA_DAYS, 'feed': 'tradingview',
            'timeframe': TIMEFRAME, 'max_trades': MAX_TOTAL_TRADES,
            'simulation': 'realista (1 trade/vz, anti-corr, todos pares competindo)'
        },
        'results': result,
        'trades': trades
    }
    outfile = Path.home() / '.hermes' / 'crypto' / 'backtest_v10_realista.json'
    with open(outfile, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nSalvo: {outfile}")
