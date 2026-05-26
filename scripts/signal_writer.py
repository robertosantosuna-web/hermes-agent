#!/usr/bin/env python3
"""
Hermes Signal Writer — envia sinais para o EA no MT5.
Formato: ação|par|direção|entry|sl|tp|volume|ticket_id
"""
import os, time, json

# Pasta COMMON do MT5 (acessível via FILE_COMMON no MQL5)
SIGNAL_DIR = os.path.expanduser('~/.wine_mt5/drive_c/Program Files/MetaTrader 5/Files')
SIGNAL_FILE = os.path.join(SIGNAL_DIR, 'hermes_signals.json')

os.makedirs(SIGNAL_DIR, exist_ok=True)

SYMBOLS = {
    'GBP/USD': 'GBPUSD',
    'AUD/USD': 'AUDUSD',
    'NZD/USD': 'NZDUSD',
    'EUR/USD': 'EURUSD',
}

def send_open(pair, direction, entry, sl, tp, volume=0.01, ticket_id=1):
    """Envia sinal de ABERTURA para o EA"""
    symbol = SYMBOLS.get(pair, pair)
    line = f"OPEN|{symbol}|{direction.upper()}|{entry:.5f}|{sl:.5f}|{tp:.5f}|{volume}|{ticket_id}"
    _write(line)
    return {'action': 'OPEN', 'symbol': symbol, 'direction': direction.upper(),
            'entry': entry, 'sl': sl, 'tp': tp}

def send_close(ticket):
    """Fecha posição específica pelo ticket"""
    line = f"CLOSE|{ticket}"
    _write(line)
    return {'action': 'CLOSE', 'ticket': ticket}

def send_close_all():
    """Fecha TODAS as posições do Hermes"""
    _write("CLOSE_ALL")
    return {'action': 'CLOSE_ALL'}

def _write(line):
    """Escreve sinal no arquivo (sobrescreve - EA processa e deleta)"""
    with open(SIGNAL_FILE, 'w') as f:
        f.write(line + '\n')
    # Garantir permissões
    os.chmod(SIGNAL_FILE, 0o666)

def get_status():
    """Verifica se arquivo de sinal anterior foi processado"""
    if os.path.exists(SIGNAL_FILE):
        mtime = os.path.getmtime(SIGNAL_FILE)
        age = time.time() - mtime
        if age > 30:  # Mais de 30s = EA não processou
            return {'status': 'stale', 'age_seconds': age}
        return {'status': 'pending', 'age_seconds': age}
    return {'status': 'clear'}

def execute_signal(pair, direction, entry_price, fvg_pips, atr_pips):
    """
    Calcula SL/TP baseado no FVG width (estratégia validada) e envia.
    RR = 3:1
    SL = FVG width (topo/base do gap)
    TP = SL * 3
    """
    pip_value = 0.0001  # Para pares USD (não-JPY)
    if 'JPY' in pair:
        pip_value = 0.01
    
    sl_pips = fvg_pips
    tp_pips = sl_pips * 3
    
    if direction.upper() in ('BUY', 'LONG'):
        sl = entry_price - (sl_pips * pip_value)
        tp = entry_price + (tp_pips * pip_value)
    else:
        sl = entry_price + (sl_pips * pip_value)
        tp = entry_price - (tp_pips * pip_value)
    
    return send_open(pair, direction, entry_price, sl, tp, volume=0.01)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'status':
            print(json.dumps(get_status(), indent=2))
        elif cmd == 'close_all':
            print(json.dumps(send_close_all(), indent=2))
        else:
            print(json.dumps({'error': f'unknown command: {cmd}'}))
    else:
        print(json.dumps(get_status(), indent=2))
