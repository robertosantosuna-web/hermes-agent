#!/usr/bin/env python3
"""
CRYPTO TRADE MONITOR — Verifica SL/TP dos trades abertos
Atualiza open_trades.json, registra resultados em trade_log.json
"""
import sys, json
from pathlib import Path
from datetime import datetime, timezone
import yfinance as yf
from telegram_notify import notify_close

TRADES_FILE = Path.home() / '.hermes' / 'crypto' / 'open_trades.json'
LOG_FILE = Path.home() / '.hermes' / 'crypto' / 'trade_log.json'

def load_json(path):
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except:
            pass
    return [] if 'trade_log' in str(path) else []

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def check_trade(trade):
    """Verifica se SL ou TP foi atingido."""
    sym = trade['sym']
    direction = trade['direction']
    sl = trade['sl']
    tp = trade['tp']
    
    try:
        # Últimos 30 candles M1 para verificar
        df = yf.Ticker(sym).history(period='1d', interval='1m')
        if len(df) < 10:
            return None
        
        current_price = float(df['Close'].values[-1])
        recent_low = float(df['Low'].values[-30:].min()) if len(df) >= 30 else float(df['Low'].min())
        recent_high = float(df['High'].values[-30:].max()) if len(df) >= 30 else float(df['High'].max())
        
        if direction == 'BUY':
            if recent_low <= sl:
                return {'result': 'LOSS', 'exit': sl, 'rr': -1}
            if recent_high >= tp:
                return {'result': 'WIN', 'exit': tp, 'rr': trade.get('sl_pct', 0) * 3 / trade.get('sl_pct', 0.1)}
        else:
            if recent_high >= sl:
                return {'result': 'LOSS', 'exit': sl, 'rr': -1}
            if recent_low <= tp:
                return {'result': 'WIN', 'exit': tp, 'rr': trade.get('sl_pct', 0) * 3 / trade.get('sl_pct', 0.1)}
        
        # Ainda aberto — retorna preço atual
        return {'result': 'OPEN', 'exit': current_price, 'current': current_price}
    
    except Exception as e:
        return None

def main():
    open_trades = load_json(TRADES_FILE)
    
    if not open_trades:
        print(f"Crypto Monitor: 0 trades abertos — {datetime.now(timezone.utc).strftime('%H:%M')} UTC")
        return
    
    trade_log = load_json(LOG_FILE)
    still_open = []
    closed = []
    
    for trade in open_trades:
        result = check_trade(trade)
        
        if result is None:
            still_open.append(trade)  # erro, mantém aberto
            continue
        
        if result['result'] == 'OPEN':
            # Atualizar preço atual
            trade['current_price'] = result['current']
            trade['pnl_pct'] = round(
                (result['current'] - trade['entry']) / trade['entry'] * 100
                if trade['direction'] == 'BUY' else
                (trade['entry'] - result['current']) / trade['entry'] * 100, 3
            )
            still_open.append(trade)
        else:
            # Trade fechado
            trade['result'] = result['result']
            trade['exit_price'] = result['exit']
            trade['rr_result'] = result['rr']
            trade['closed_at'] = datetime.now(timezone.utc).isoformat()
            closed.append(trade)
    
    # Salvar
    save_json(TRADES_FILE, still_open)
    
    if closed:
        trade_log.extend(closed)
        save_json(LOG_FILE, trade_log)
    
    # Report
    print(f"Crypto Monitor — {datetime.now(timezone.utc).strftime('%d/%m %H:%M')} UTC")
    
    if closed:
        print(f"  🔒 Fechados: {len(closed)}")
        for t in closed:
            emoji = '✅' if t['result'] == 'WIN' else '❌'
            pnl = t['entry'] * t.get('sl_pct', 0.003) * t['rr_result']
            print(f"     {emoji} {t['pair']} {t['direction']} {t['result']} "
                  f"({t['rr_result']:+.0f}R) @{t['exit_price']:.4f}")
            # Notificar Telegram
            notify_close(t['pair'], t['result'], abs(pnl), 0)  # balance via Binance
    
    if still_open:
        print(f"  📊 Abertos: {len(still_open)}")
        for t in still_open:
            pnl = t.get('pnl_pct', 0)
            print(f"     {t['pair']} {t['direction']} @{t['entry']:.4f} "
                  f"SL={t['sl_pct']:.2f}% TP={t['sl_pct']*3:.2f}% PnL={pnl:+.2f}%")
    
    if not closed and not still_open:
        print("  Nenhum trade ativo")


if __name__ == '__main__':
    main()
