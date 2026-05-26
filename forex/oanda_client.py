#!/usr/bin/python3
"""
OANDA CLIENT — Pronto para operar
=================================
Assim que o token for configurado, use:

    python3 oanda_client.py status       # Ver saldo e posições
    python3 oanda_client.py quote EUR_USD # Cotação em tempo real
    python3 oanda_client.py trade EUR_USD buy 1000  # Abrir trade
    python3 oanda_client.py close_all    # Fechar todas as posições

Configuração: defina OANDA_TOKEN no arquivo ~/.hermes/forex/oanda_config.json
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

CONFIG_PATH = Path.home() / '.hermes' / 'forex' / 'oanda_config.json'

# Mapeamento de pares → instrumentos OANDA
PAIR_TO_INSTRUMENT = {
    'EUR/USD': 'EUR_USD',
    'GBP/USD': 'GBP_USD',
    'USD/JPY': 'USD_JPY',
    'AUD/USD': 'AUD_USD',
    'EUR/GBP': 'EUR_GBP',
    'EUR/JPY': 'EUR_JPY',
    'USD/CAD': 'USD_CAD',
}

INSTRUMENT_TO_PAIR = {v: k for k, v in PAIR_TO_INSTRUMENT.items()}


def load_config():
    """Carrega configuração da OANDA."""
    if not CONFIG_PATH.exists():
        # Criar template
        template = {
            "practice": True,
            "token": "SEU_TOKEN_AQUI",
            "account_id": "SEU_ACCOUNT_ID_AQUI",
            "environment": "practice"
        }
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            json.dump(template, f, indent=2)
        print(f"⚠️  Arquivo de configuração criado: {CONFIG_PATH}")
        print(f"   Edite e coloque seu token e account_id da OANDA.")
        return None
    
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    
    token = config.get('token', '')
    if token == 'SEU_TOKEN_AQUI' or not token:
        print(f"⚠️  Token não configurado. Edite: {CONFIG_PATH}")
        return None
    
    return config


def get_api():
    """Inicializa a API da OANDA."""
    config = load_config()
    if not config:
        return None, None

    try:
        from oandapyV20 import API
    except ImportError:
        print("❌ oandapyV20 não instalado. Execute:")
        print("   pip install --break-system-packages oandapyV20")
        return None, None

    env = "practice" if config.get('practice', True) else "live"
    api = API(access_token=config['token'], environment=env)
    account_id = config.get('account_id', '')
    return api, account_id


def get_accounts(api):
    """Lista todas as contas."""
    try:
        r = api.request(api.accounts())
        if r.status_code == 200:
            accounts = r.json().get('accounts', [])
            return accounts
        else:
            print(f"Erro: {r.status_code} - {r.text[:200]}")
            return []
    except Exception as e:
        print(f"Erro ao listar contas: {e}")
        return []


def get_account_summary(api, account_id):
    """Resumo da conta."""
    try:
        from oandapyV20.endpoints.accounts import AccountSummary
        r = api.request(AccountSummary(account_id))
        if r.status_code == 200:
            data = r.json()
            acc = data.get('account', {})
            return {
                'id': acc.get('id'),
                'balance': float(acc.get('balance', 0)),
                'unrealizedPL': float(acc.get('unrealizedPL', 0)),
                'realizedPL': float(acc.get('realizedPL', 0)),
                'marginUsed': float(acc.get('marginUsed', 0)),
                'marginAvailable': float(acc.get('marginAvailable', 0)),
                'openTrades': acc.get('openTradeCount', 0),
                'openPositions': acc.get('openPositionCount', 0),
            }
        else:
            print(f"Erro: {r.status_code}")
            return None
    except Exception as e:
        print(f"Erro: {e}")
        return None


def get_pricing(api, account_id, instruments):
    """Cotação em tempo real."""
    try:
        from oandapyV20.endpoints.pricing import PricingInfo
        params = {"instruments": ",".join(instruments)}
        r = api.request(PricingInfo(account_id, params=params))
        if r.status_code == 200:
            prices = r.json().get('prices', [])
            result = {}
            for p in prices:
                inst = p.get('instrument', '')
                pair = INSTRUMENT_TO_PAIR.get(inst, inst)
                bids = p.get('bids', [{}])
                asks = p.get('asks', [{}])
                result[pair] = {
                    'bid': float(bids[0].get('price', 0)) if bids else 0,
                    'ask': float(asks[0].get('price', 0)) if asks else 0,
                    'spread': round(float(asks[0].get('price', 0)) - float(bids[0].get('price', 0)), 5) if bids and asks else 0,
                    'time': p.get('time', '')
                }
            return result
    except Exception as e:
        print(f"Erro pricing: {e}")
        return None


def place_market_order(api, account_id, instrument, units, stop_loss=None, take_profit=None):
    """Ordem a mercado."""
    try:
        from oandapyV20.endpoints.orders import OrderCreate
        order_data = {
            "order": {
                "type": "MARKET",
                "instrument": instrument,
                "units": str(units),
                "timeInForce": "FOK",
            }
        }
        if stop_loss:
            order_data["order"]["stopLossOnFill"] = {"price": str(stop_loss)}
        if take_profit:
            order_data["order"]["takeProfitOnFill"] = {"price": str(take_profit)}

        r = api.request(OrderCreate(account_id, data=order_data))
        if r.status_code == 201:
            data = r.json()
            ord_id = data.get('orderCreateTransaction', {}).get('id')
            print(f"✅ Ordem executada: {ord_id}")
            return data
        else:
            print(f"❌ Erro ordem: {r.status_code} - {r.text[:300]}")
            return None
    except Exception as e:
        print(f"Erro: {e}")
        return None


def close_all_positions(api, account_id):
    """Fecha todas as posições abertas."""
    try:
        from oandapyV20.endpoints.positions import PositionClose
        from oandapyV20.endpoints.positions import OpenPositions

        r = api.request(OpenPositions(account_id))
        if r.status_code != 200:
            print(f"Erro ao listar posições: {r.status_code}")
            return

        positions = r.json().get('positions', [])
        for pos in positions:
            inst = pos.get('instrument', '')
            long_units = int(pos.get('long', {}).get('units', 0))
            short_units = int(pos.get('short', {}).get('units', 0))

            if long_units > 0:
                data = {"longUnits": "ALL"}
                r_close = api.request(PositionClose(account_id, inst, data=data))
                pair = INSTRUMENT_TO_PAIR.get(inst, inst)
                print(f"✅ Fechado LONG {pair}: {r_close.status_code}")

            if short_units > 0:
                data = {"shortUnits": "ALL"}
                r_close = api.request(PositionClose(account_id, inst, data=data))
                pair = INSTRUMENT_TO_PAIR.get(inst, inst)
                print(f"✅ Fechado SHORT {pair}: {r_close.status_code}")

        print("✅ Todas as posições fechadas.")
    except Exception as e:
        print(f"Erro: {e}")


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python3 oanda_client.py status")
        print("  python3 oanda_client.py quote [EUR_USD]")
        print("  python3 oanda_client.py trade EUR_USD buy 1000")
        print("  python3 oanda_client.py close_all")
        print(f"\n  Config: {CONFIG_PATH}")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == 'status':
        api, account_id = get_api()
        if not api or not account_id:
            sys.exit(1)
        summary = get_account_summary(api, account_id)
        if summary:
            print(f"\n{'═'*40}")
            print(f"  📊 OANDA {'PRACTICE' if load_config().get('practice') else 'LIVE'}")
            print(f"{'═'*40}")
            print(f"  Conta: {summary['id']}")
            print(f"  Saldo: ${summary['balance']:,.2f}")
            print(f"  PnL não realizado: ${summary['unrealizedPL']:+,.2f}")
            print(f"  Margem usada: ${summary['marginUsed']:,.2f}")
            print(f"  Margem livre: ${summary['marginAvailable']:,.2f}")
            print(f"  Trades abertos: {summary['openTrades']}")
            print(f"  Posições abertas: {summary['openPositions']}")

    elif cmd == 'quote':
        api, account_id = get_api()
        if not api or not account_id:
            sys.exit(1)
        inst = sys.argv[2] if len(sys.argv) > 2 else 'EUR_USD'
        if inst in PAIR_TO_INSTRUMENT:
            inst = PAIR_TO_INSTRUMENT[inst]
        prices = get_pricing(api, account_id, [inst])
        if prices:
            for pair, p in prices.items():
                print(f"  {pair}: Bid={p['bid']} Ask={p['ask']} Spread={p['spread']}")

    elif cmd == 'trade':
        if len(sys.argv) < 5:
            print("Uso: trade EUR_USD buy|sell 1000 [stop] [target]")
            sys.exit(1)
        api, account_id = get_api()
        if not api or not account_id:
            sys.exit(1)
        inst = sys.argv[2]
        direction = sys.argv[3]
        units = int(sys.argv[4])
        if direction == 'sell':
            units = -units

        if inst in PAIR_TO_INSTRUMENT:
            inst = PAIR_TO_INSTRUMENT[inst]

        place_market_order(api, account_id, inst, units)

    elif cmd == 'close_all':
        api, account_id = get_api()
        if not api or not account_id:
            sys.exit(1)
        close_all_positions(api, account_id)

    else:
        print(f"Comando desconhecido: {cmd}")
