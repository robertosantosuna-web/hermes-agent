#!/usr/bin/env python3
"""
MT5 Order Executor — envia ordens reais no MetaTrader 5 via xdotool.
Usa CHoCH+FVG M15 com RR 3:1, parâmetros validados em backtest 30d.
"""
import subprocess, time, os, json, sys

DISPLAY = ':99'
MT5_WIN_NAME = 'MetaTrader'

# Pares e símbolos MT5
SYMBOLS = {
    'GBP/USD': 'GBPUSD',
    'AUD/USD': 'AUDUSD',
    'NZD/USD': 'NZDUSD',
    'EUR/USD': 'EURUSD',
}

def xdotool(*args):
    """Executa xdotool no display :99"""
    cmd = ['xdotool'] + list(args)
    result = subprocess.run(cmd, env={**os.environ, 'DISPLAY': DISPLAY},
                          capture_output=True, text=True, timeout=5)
    return result.stdout.strip()

def get_mt5_wid():
    """Encontra a janela principal do MT5"""
    out = xdotool('search', '--name', MT5_WIN_NAME)
    if out:
        return out.split('\n')[0]
    return None

def focus_mt5():
    """Foca a janela do MT5"""
    wid = get_mt5_wid()
    if wid:
        xdotool('windowfocus', wid)
        time.sleep(0.3)
        return wid
    return None

def open_new_order(symbol, volume=0.01):
    """Abre janela de nova ordem - F9, preenche símbolo"""
    focus_mt5()
    # F9 = New Order
    xdotool('key', 'F9')
    time.sleep(1.5)
    
    # A janela New Order abriu. Foco no campo de símbolo.
    # Tab até o campo de símbolo (geralmente já está focado)
    # Limpar e digitar símbolo
    xdotool('key', 'ctrl+a')
    time.sleep(0.1)
    xdotool('type', symbol)
    time.sleep(0.3)
    xdotool('key', 'Return')
    time.sleep(0.5)
    
    return True

def set_sl_tp(sl_price, tp_price, volume=0.01):
    """Preenche SL e TP na janela de ordem (já deve estar aberta)"""
    # Tab até campo de volume
    xdotool('key', 'Tab')
    time.sleep(0.1)
    xdotool('key', 'Tab')
    time.sleep(0.1)
    # Digitar volume
    xdotool('key', 'ctrl+a')
    time.sleep(0.05)
    xdotool('type', str(volume))
    time.sleep(0.2)
    
    # Tab até SL
    xdotool('key', 'Tab')
    time.sleep(0.1)
    xdotool('key', 'Tab')
    time.sleep(0.1)
    # Digitar SL
    xdotool('key', 'ctrl+a')
    time.sleep(0.05)
    xdotool('type', f'{sl_price:.5f}')
    time.sleep(0.2)
    
    # Tab até TP
    xdotool('key', 'Tab')
    time.sleep(0.1)
    # Digitar TP
    xdotool('key', 'ctrl+a')
    time.sleep(0.05)
    xdotool('type', f'{tp_price:.5f}')
    time.sleep(0.2)
    
    return True

def click_buy():
    """Clica no botão Buy (Alt+B ou Tab até o botão)"""
    # Alt+B geralmente é o atalho para Buy
    xdotool('key', 'alt+b')
    time.sleep(1)
    return True

def click_sell():
    """Clica no botão Sell (Alt+S geralmente)"""
    xdotool('key', 'alt+s')
    time.sleep(1)
    return True

def place_order(symbol, direction, volume, sl_price, tp_price):
    """Ordem completa: abre janela, preenche, envia"""
    wid = focus_mt5()
    if not wid:
        return {'error': 'MT5 window not found'}
    
    open_new_order(symbol, volume)
    set_sl_tp(sl_price, tp_price, volume)
    
    if direction.upper() in ('BUY', 'LONG'):
        click_buy()
    else:
        click_sell()
    
    # Fechar janela de ordem se ainda estiver aberta
    time.sleep(0.5)
    xdotool('key', 'Escape')
    
    return {'status': 'sent', 'symbol': symbol, 'direction': direction, 
            'volume': volume, 'sl': sl_price, 'tp': tp_price}

def get_open_positions():
    """Abre terminal (Ctrl+T) e tenta ler posições"""
    focus_mt5()
    xdotool('key', 'ctrl+t')
    time.sleep(1)
    # TODO: ler tabela de posições via OCR ou screen scraping
    return []

def close_position(ticket):
    """Fecha posição pelo ticket"""
    focus_mt5()
    xdotool('key', 'ctrl+t')
    time.sleep(1)
    # TODO: navegar até a posição e clicar no X
    # Por enquanto, placeholder
    return {'status': 'not_implemented', 'ticket': ticket}

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    
    if cmd == 'test':
        # Teste: abrir ordem de 0.01 em EURUSD
        result = place_order('EURUSD', 'BUY', 0.01, 1.1600, 1.1660)
        print(json.dumps(result))
    elif cmd == 'status':
        wid = get_mt5_wid()
        print(json.dumps({'mt5_window': wid is not None, 'wid': wid}))
    else:
        print(json.dumps({'error': f'unknown command: {cmd}'}))
