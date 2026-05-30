#!/usr/bin/env python3
"""CRYPTO LIVE DASHBOARD — Ordens, P&L, Saldo em tempo real"""
import sys, json, time, os
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path.home() / '.hermes' / 'crypto'))
from binance_trader import BinanceTrader
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.console import Group
from rich import box

TRADES_FILE = Path.home() / '.hermes' / 'crypto' / 'open_trades.json'
TRADE_LOG = Path.home() / '.hermes' / 'crypto' / 'trade_log.json'

def load_json(path, default=None):
    if default is None: default = []
    try:
        if path.exists():
            with open(path) as f: return json.load(f)
    except: pass
    return default

def fmt_pnl(pnl, pnl_pct):
    color = "green" if pnl >= 0 else "red"
    sign = "+" if pnl >= 0 else ""
    return f"[{color}]{sign}${pnl:.2f} ({sign}{pnl_pct:.2f}%)[/{color}]"

def build_dashboard(trader):
    layout = Layout()
    layout.split_column(
        Layout(name="top", size=3),
        Layout(name="body"),
        Layout(name="bottom", size=3),
    )
    layout["body"].split_row(
        Layout(name="left", ratio=2),
        Layout(name="right", ratio=1),
    )
    layout["left"].split_column(
        Layout(name="position"),
        Layout(name="orders"),
    )

    now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    # ═══ HEADER ═══
    header = Table.grid(padding=(0, 2))
    header.add_column(justify="left")
    header.add_column(justify="center")
    header.add_column(justify="right")
    
    # Saldo
    spot_bal = trader.get_balance('USDT')
    margin_bal = trader._get_margin_balance('USDT')
    total = spot_bal + margin_bal
    
    # Preço BTC
    btc_price = trader.get_price('BTCUSDT')
    eth_price = trader.get_price('ETHUSDT')
    
    header.add_row(
        f"💰 Spot: ${spot_bal:.2f}  Margin: ${margin_bal:.2f}  Total: ${total:.2f}",
        f"₿ ${btc_price:,.0f}  Ξ ${eth_price:,.2f}",
        f"🕐 {now}"
    )
    layout["top"].update(Panel(header, title="🔴 CRYPTO LIVE", border_style="red"))

    # ═══ POSIÇÃO ═══
    pos_table = Table(title="📊 POSIÇÃO ABERTA", box=box.ROUNDED, border_style="cyan")
    pos_table.add_column("Par", style="bold")
    pos_table.add_column("Dir")
    pos_table.add_column("Entry")
    pos_table.add_column("Atual")
    pos_table.add_column("P&L")
    pos_table.add_column("SL")
    pos_table.add_column("TP")
    pos_table.add_column("Conf")
    
    trades = load_json(TRADES_FILE)
    for t in trades:
        pair = t['pair']
        symbol = pair.replace('USD', 'USDT')
        direction = t['direction']
        entry = t['entry']
        sl = t.get('sl', 0)
        tp = t.get('tp', 0)
        conf = t.get('conf', 0)
        
        try:
            current = trader.get_price(symbol)
        except:
            current = entry
        
        if direction == 'BUY':
            pnl = current - entry
            pnl_pct = (current / entry - 1) * 100
        else:
            pnl = entry - current
            pnl_pct = (1 - current / entry) * 100
        
        sl_dist = abs(current - sl) / current * 100
        tp_dist = abs(tp - current) / current * 100
        
        pos_table.add_row(
            pair, direction,
            f"${entry:,.2f}", f"${current:,.2f}",
            fmt_pnl(pnl, pnl_pct),
            f"${sl:,.2f} ({sl_dist:.2f}%)",
            f"${tp:,.2f} ({tp_dist:.2f}%)",
            f"{conf:.0f}%"
        )
    
    if not trades:
        pos_table.add_row("—", "—", "—", "—", "—", "—", "—", "—")
    
    layout["position"].update(pos_table)

    # ═══ ORDENS OCO ═══
    orders_table = Table(title="📋 ORDENS ABERTAS (OCO)", box=box.ROUNDED, border_style="yellow")
    orders_table.add_column("Par")
    orders_table.add_column("Tipo")
    orders_table.add_column("Lado")
    orders_table.add_column("Preço")
    orders_table.add_column("Qtd")
    orders_table.add_column("Status")
    
    try:
        # Margin orders
        margin_orders = []
        margin_orders = trader._request('GET', '/sapi/v1/margin/openOrders', signed=True)
        for o in margin_orders:
            otype = o.get('type', '?')
            side = o.get('side', '?')
            price = o.get('price', o.get('stopPrice', 'market'))
            qty = o.get('origQty', '?')
            status = o.get('status', '?')
            orders_table.add_row(
                o.get('symbol', '?'), otype, side,
                str(price), str(qty), status
            )
    except:
        pass
    
    try:
        spot_orders = []
        spot_orders = trader._request('GET', '/api/v3/openOrders', signed=True)
        for o in spot_orders:
            orders_table.add_row(
                o.get('symbol', '?'), o.get('type', '?'), o.get('side', '?'),
                str(o.get('price', 'market')), str(o.get('origQty', '?')),
                o.get('status', '?')
            )
    except:
        pass
    
    if not margin_orders and not spot_orders:
        orders_table.add_row("—", "—", "—", "—", "—", "sem ordens")
    
    layout["orders"].update(orders_table)

    # ═══ ÚLTIMAS 4 ORDENS FINALIZADAS ═══
    history_table = Table(title="📋 ÚLTIMAS 4 FINALIZADAS", box=box.ROUNDED, border_style="green")
    history_table.add_column("Par")
    history_table.add_column("Dir")
    history_table.add_column("P&L")
    history_table.add_column("Result")
    
    log = load_json(TRADE_LOG)
    # Filtrar só trades com resultado (fechados)
    closed = [t for t in log if t.get('result') or t.get('status') in ('WIN', 'LOSS', 'closed')]
    for t in closed[-4:]:
        pair = t.get('pair', '?')
        direction = t.get('direction', '?')
        pnl = t.get('pnl', t.get('pnl_usdt', 0))
        result = t.get('result', t.get('status', '?'))
        pnl_color = "green" if float(pnl or 0) >= 0 else "red"
        res_emoji = "✅" if result == 'WIN' else "❌" if result == 'LOSS' else ""
        history_table.add_row(
            pair, direction,
            f"[{pnl_color}]{float(pnl or 0):+.2f}[/{pnl_color}]",
            f"{res_emoji} {result}"
        )
    
    if not closed:
        history_table.add_row("—", "—", "—", "—")
    
    layout["right"].update(history_table)

    # ═══ FOOTER ═══
    # Margin level
    try:
        acct = trader._request('GET', '/sapi/v1/margin/account', signed=True)
        margin_level = float(acct.get('marginLevel', 999))
        ml_color = "green" if margin_level > 3 else "yellow" if margin_level > 1.5 else "red"
    except:
        margin_level = 999
        ml_color = "green"
    
    # Daily P&L
    cfg_path = Path.home() / '.hermes' / 'crypto' / 'binance_config.json'
    daily = {}
    if cfg_path.exists():
        try:
            with open(cfg_path) as f:
                daily = json.load(f).get('daily_pnl', {})
        except: pass
    
    daily_trades = daily.get('trades', 0)
    daily_pnl = daily.get('pnl_usdt', 0)
    dpnl_color = "green" if daily_pnl >= 0 else "red"
    
    footer_text = (
        f"📊 Margin Level: [{ml_color}]{margin_level:.1f}x[/{ml_color}]  |  "
        f"Hoje: {daily_trades} trades  |  "
        f"PnL Dia: [{dpnl_color}]${daily_pnl:.2f}[/{dpnl_color}]  |  "
        f"Ctrl+C para sair"
    )
    layout["bottom"].update(Panel(footer_text, border_style="dim"))

    return layout

def main():
    trader = BinanceTrader(testnet=False)
    
    with Live(build_dashboard(trader), refresh_per_second=2, screen=True) as live:
        while True:
            time.sleep(2)
            try:
                live.update(build_dashboard(trader))
            except Exception as e:
                # Silently retry on transient errors
                pass

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Dashboard fechado.")
