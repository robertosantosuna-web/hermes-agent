#!/usr/bin/env python3
"""
FOREX BOT — OANDA DEMO (execução real)
Conecta na OANDA Practice API e executa trades reais na conta demo.
Estratégia: CHoCH+FVG @ M15, RR 3:1

Configuração:
  ~/.hermes/forex/oanda_config.json
  {
    "account_id": "XXX-XXX-XXXXXXXX-XXX",
    "api_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "environment": "practice"
  }
"""
import json
import urllib.request
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from oandapyV20 import API
from oandapyV20.endpoints.orders import OrderCreate
from oandapyV20.endpoints.positions import PositionList, OpenPositions
from oandapyV20.endpoints.accounts import AccountSummary
import oandapyV20.endpoints.trades as trades

# ═══════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════
FOREX_DIR = Path.home() / '.hermes' / 'forex'
CONFIG_FILE = FOREX_DIR / 'oanda_config.json'
STATE_FILE = FOREX_DIR / 'oanda_state.json'

PAIRS = {
    'GBP/USD': 'GBP_USD',
    'AUD/USD': 'AUD_USD',
    'EUR/USD': 'EUR_USD',
    'NZD/USD': 'NZD_USD',
}

OANDA_PAIRS = {v: k for k, v in PAIRS.items()}

RR = 3.0
FVG_MIN_PIPS = 1.0
GOLDEN_HOURS = {7, 10, 14, 16}

def pip_val(pair):
    return 0.01 if 'JPY' in pair else 0.0001

def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return None

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {'open_trades': [], 'closed_trades': [], 'daily_pnl': 0}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))

def log(msg, level='INFO'):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] [{level}] {msg}")

# ═══════════════════════════════════════
# YAHOO FINANCE (MESMA LÓGICA DO PAPER)
# ═══════════════════════════════════════
YAHOO_PAIRS = {
    'GBP/USD': 'GBPUSD=X',
    'AUD/USD': 'AUDUSD=X',
    'EUR/USD': 'EURUSD=X',
    'NZD/USD': 'NZDUSD=X',
}

def fetch_m15(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=15m"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())['chart']['result'][0]
        candles = []
        for i, ts in enumerate(data['timestamp']):
            q = data['indicators']['quote'][0]
            o, h, l, c = q['open'][i], q['high'][i], q['low'][i], q['close'][i]
            if None not in (o, h, l, c):
                dt = datetime.utcfromtimestamp(ts) - timedelta(hours=3)
                candles.append({'time': dt, 'o': o, 'h': h, 'l': l, 'c': c})
        return candles
    except Exception as e:
        return []

def atr(candles, period=14):
    if len(candles) < 2: return 0
    trs = []
    for i in range(1, len(candles)):
        h, l, pc = candles[i]['h'], candles[i]['l'], candles[i-1]['c']
        trs.append(max(h-l, abs(h-pc), abs(l-pc)))
    n = min(period, len(trs))
    return sum(trs[-n:])/n if n > 0 else 0

def detect_swings(candles):
    highs, lows = [], []
    for i in range(3, len(candles)-3):
        h, l = candles[i]['h'], candles[i]['l']
        left_h = max(c['h'] for c in candles[i-3:i])
        right_h = max(c['h'] for c in candles[i+1:i+4])
        left_l = min(c['l'] for c in candles[i-3:i])
        right_l = min(c['l'] for c in candles[i+1:i+4])
        if h > left_h and h > right_h:
            highs.append({'idx': i, 'price': h})
        if l < left_l and l < right_l:
            lows.append({'idx': i, 'price': l})
    return highs, lows

def find_fvgs(candles):
    fvgs = []
    for i in range(1, len(candles)-1):
        prev, curr = candles[i-1], candles[i]
        if curr['l'] > prev['h']:
            fvgs.append({'type': 'BULLISH', 'top': curr['l'], 'bottom': prev['h']})
        elif curr['h'] < prev['l']:
            fvgs.append({'type': 'BEARISH', 'top': prev['l'], 'bottom': curr['h']})
    return fvgs

def detect_signal(pair_name):
    symbol = YAHOO_PAIRS[pair_name]
    pv = pip_val(pair_name)
    candles = fetch_m15(symbol)
    if not candles or len(candles) < 20:
        return None
    
    atr_val = atr(candles, 14)
    atr_pips = atr_val / pv
    if atr_pips < 1.0:
        return None
    
    swings_h, swings_l = detect_swings(candles)
    if len(swings_h) < 2 or len(swings_l) < 2:
        return None
    
    last = candles[-1]
    direction = None
    if last['c'] > swings_h[-2]['price']:
        direction = 'LONG'
    elif last['c'] < swings_l[-2]['price']:
        direction = 'SHORT'
    if not direction:
        return None
    
    fvgs = find_fvgs(candles[-8:])
    valid_fvg = None
    if direction == 'SHORT':
        for f in reversed(fvgs):
            if f['type'] == 'BEARISH': valid_fvg = f; break
    else:
        for f in reversed(fvgs):
            if f['type'] == 'BULLISH': valid_fvg = f; break
    if not valid_fvg:
        return None
    
    entry = valid_fvg['bottom'] if direction=='SHORT' else valid_fvg['top']
    fvg_sl = valid_fvg['top'] if direction=='SHORT' else valid_fvg['bottom']
    fvg_width = abs(entry - fvg_sl) / pv
    if fvg_width < FVG_MIN_PIPS:
        return None
    
    sl_pips = fvg_width
    tp_pips = sl_pips * RR
    
    sl_price = round(entry + sl_pips * pv, 5) if direction=='SHORT' else round(entry - sl_pips * pv, 5)
    tp_price = round(entry - tp_pips * pv, 5) if direction=='SHORT' else round(entry + tp_pips * pv, 5)
    entry = round(entry, 5)
    
    return {
        'pair': pair_name,
        'oanda_pair': PAIRS[pair_name],
        'direction': direction,
        'entry': entry,
        'sl': sl_price,
        'tp': tp_price,
        'sl_pips': sl_pips,
        'tp_pips': tp_pips,
        'atr_pips': round(atr_pips, 1),
        'fvg_pips': round(fvg_width, 1),
    }

# ═══════════════════════════════════════
# OANDA ORDER EXECUTION
# ═══════════════════════════════════════
def place_oanda_order(api, account_id, signal):
    """Place MARKET order with TP/SL on OANDA demo."""
    units = 100  # 100 units = micro lot (seguro pra demo)
    if signal['direction'] == 'SHORT':
        units = -100
    
    order_data = {
        "order": {
            "type": "MARKET",
            "instrument": signal['oanda_pair'],
            "units": str(units),
            "takeProfitOnFill": {
                "price": str(signal['tp']),
                "timeInForce": "GTC"
            },
            "stopLossOnFill": {
                "price": str(signal['sl']),
                "timeInForce": "GTC"
            }
        }
    }
    
    try:
        r = OrderCreate(accountID=account_id, data=order_data)
        response = api.request(r)
        log(f"✅ ORDEM REAL: {signal['pair']} {signal['direction']} "
            f"E={signal['entry']} SL={signal['sl']} TP={signal['tp']} "
            f"ID={response.get('orderCreateTransaction',{}).get('id','?')}", 'TRADE')
        return response
    except Exception as e:
        log(f"❌ ERRO ordem {signal['pair']}: {e}", 'ERROR')
        return None

def check_open_positions(api, account_id):
    """Verifica posições abertas na OANDA."""
    try:
        r = OpenPositions(accountID=account_id)
        response = api.request(r)
        positions = response.get('positions', [])
        return positions
    except Exception as e:
        log(f"Erro ao verificar posições: {e}", 'ERROR')
        return []

# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════
def main():
    now = datetime.now()
    hour = now.hour
    dow = now.weekday()
    
    config = load_config()
    if not config:
        log("❌ Config não encontrada. Crie ~/.hermes/forex/oanda_config.json", 'ERROR')
        log("   Formato: {\"account_id\": \"...\", \"api_token\": \"...\", \"environment\": \"practice\"}")
        return
    
    # Verificar horário
    if dow in (0, 4, 5, 6):
        log(f"Fora de dia útil (dow={dow}) — [SILENT]")
        return
    if hour < 4 or hour > 17:
        log(f"Fora de horário ({hour}h) — [SILENT]")
        return
    if hour not in GOLDEN_HOURS:
        log(f"Fora de golden hour ({hour}h) — só verificando posições")
    
    # Conectar OANDA
    api = API(access_token=config['api_token'],
              environment=config.get('environment', 'practice'))
    account_id = config['account_id']
    
    log(f"🤖 BOT OANDA DEMO — {now.strftime('%d/%m %H:%M')} BRT")
    
    # Verificar posições abertas
    positions = check_open_positions(api, account_id)
    if positions:
        log(f"📊 {len(positions)} posição(ões) aberta(s):")
        for pos in positions:
            inst = pos.get('instrument', '?')
            long_units = float(pos.get('long', {}).get('units', 0))
            short_units = float(pos.get('short', {}).get('units', 0))
            pl = pos.get('unrealizedPL', '0')
            pair = OANDA_PAIRS.get(inst, inst)
            direction = 'LONG' if long_units > 0 else 'SHORT'
            log(f"  {pair} {direction} P/L: {pl}")
    
    # Detectar novos sinais
    if hour in GOLDEN_HOURS:
        long_signals = []
        short_signals = []
        
        for pair_name in PAIRS:
            signal = detect_signal(pair_name)
            if signal:
                if signal['direction'] == 'LONG':
                    long_signals.append(signal)
                else:
                    short_signals.append(signal)
                log(f"SINAL {signal['pair']} {signal['direction']} "
                    f"E={signal['entry']} SL={signal['sl_pips']}p TP={signal['tp_pips']}p")
        
        # Máximo 1 ordem por direção (dedup)
        if long_signals:
            best = max(long_signals, key=lambda s: s['fvg_pips'])
            place_oanda_order(api, account_id, best)
        if short_signals:
            best = max(short_signals, key=lambda s: s['fvg_pips'])
            place_oanda_order(api, account_id, best)
        
        if not long_signals and not short_signals:
            log("Nenhum sinal detectado")

if __name__ == '__main__':
    main()
