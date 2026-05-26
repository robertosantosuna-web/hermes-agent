#!/usr/bin/env python3
"""
SIMULAÇÃO ALAVANCADA 50X — FOREX PICOS DE VOLUME
================================================
- Alavancagem: 50x
- Relação Risco:Retorno = 1:3 (arrisca 1%, busca 3%)
- Risk management: lote ajustado para stop = 1% do capital
- Capital inicial: R$ 1.000 (referência)
"""

import requests
import json
import statistics
import random
from datetime import datetime, timedelta
from pathlib import Path

# ═══════════════════════════════════════════
# CONFIGURAÇÃO
# ═══════════════════════════════════════════

CAPITAL_INICIAL = 1000.0       # R$
ALAVANCAGEM = 50               # 50x
RISCO_POR_TRADE_PCT = 1.0      # 1% do capital
RELACAO_RISCO_RETORNO = 3.0    # 1:3 (busca 3x o risco)
ATR_MULTIPLIER_STOP = 1.5      # Stop = 1.5 × ATR

PICOS = {
    "london": {
        "nome": "🇬🇧 London Open",
        "horario_brt": "05:00",
        "pares": {"EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "EUR/GBP": "EURGBP=X"}
    },
    "ny": {
        "nome": "🇺🇸⭐ NY Overlap",
        "horario_brt": "10:00",
        "pares": {"EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X"}
    },
    "asia": {
        "nome": "🇯🇵 Asian Open",
        "horario_brt": "21:00",
        "pares": {"USD/JPY": "JPY=X", "AUD/USD": "AUDUSD=X", "EUR/JPY": "EURJPY=X"}
    }
}


def fetch_forex(symbol, days=90):
    """Busca dados diários do Yahoo Finance."""
    end = int(datetime.now().timestamp())
    start = int((datetime.now() - timedelta(days=days)).timestamp())
    url = (
        f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'
        f'?period1={start}&period2={end}&interval=1d'
    )
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        result = data['chart']['result'][0]
        quotes = result['indicators']['quote'][0]
        closes = [c for c in quotes['close'] if c is not None]
        highs = [h for h in quotes['high'] if h is not None]
        lows = [l for l in quotes['low'] if l is not None]
        opens = [o for o in quotes['open'] if o is not None]
        return {'opens': opens, 'highs': highs, 'lows': lows, 'closes': closes}
    except Exception as e:
        return {'error': str(e)}


def calc_atr(highs, lows, closes, period=14):
    """Average True Range."""
    if len(closes) < period + 1:
        return None
    trs = []
    for i in range(-period, 0):
        h = highs[i]
        l = lows[i]
        c_prev = closes[i - 1] if i > -period else closes[i - 1]
        tr = max(h - l, abs(h - c_prev), abs(l - c_prev))
        trs.append(tr)
    return sum(trs) / period


def detect_trend(closes, lookback=5):
    """Detecta tendência recente."""
    recent = closes[-lookback:]
    return "ALTA" if recent[-1] > recent[0] else "BAIXA"


def simulate_leveraged_trade(pair_name, data):
    """
    Simula UM trade alavancado com gestão de risco 1:3.

    Retorna dict com resultado detalhado.
    """
    if 'error' in data or len(data['closes']) < 20:
        return None

    closes = data['closes']
    highs = data['highs']
    lows = data['lows']

    # Entry: último candle fechado
    entry = closes[-1]
    atr_val = calc_atr(highs, lows, closes, 14)
    if not atr_val or atr_val <= 0:
        return None

    trend = detect_trend(closes, 5)
    direction = "COMPRA" if trend == "ALTA" else "VENDA"

    # Stop e Take (relação 1:3)
    stop_distance = ATR_MULTIPLIER_STOP * atr_val
    take_distance = stop_distance * RELACAO_RISCO_RETORNO  # 3x o stop

    if direction == "COMPRA":
        stop_price = entry - stop_distance
        take_price = entry + take_distance
    else:
        stop_price = entry + stop_distance
        take_price = entry - take_distance

    # Distância percentual do stop
    stop_pct = stop_distance / entry  # distância % até o stop

    # Com alavancagem 50x, o stop causaria: stop_pct × 50 de perda no capital
    # Para limitar a 1%: lote = 0.01 / (stop_pct × 50)
    lote_pct_do_capital = RISCO_POR_TRADE_PCT / 100 / (stop_pct * ALAVANCAGEM)

    # Verificar resultado contra candle seguinte (simulando forward test)
    # Usamos o penúltimo candle como entry, último como resultado
    if len(closes) < 3:
        return None

    # Simular com candle anterior
    entry_sim = closes[-2]
    atr_sim = calc_atr(highs[:-1], lows[:-1], closes[:-1], 14)
    if not atr_sim or atr_sim <= 0:
        return None

    trend_sim = "ALTA" if closes[-2] > closes[-3] else "BAIXA"
    dir_sim = "COMPRA" if trend_sim == "ALTA" else "VENDA"

    stop_dist_sim = ATR_MULTIPLIER_STOP * atr_sim
    take_dist_sim = stop_dist_sim * RELACAO_RISCO_RETORNO

    if dir_sim == "COMPRA":
        stop_sim = entry_sim - stop_dist_sim
        take_sim = entry_sim + take_dist_sim
    else:
        stop_sim = entry_sim + stop_dist_sim
        take_sim = entry_sim - take_dist_sim

    # Calcular lote simulado
    stop_pct_sim = stop_dist_sim / entry_sim
    lote_sim = RISCO_POR_TRADE_PCT / 100 / (stop_pct_sim * ALAVANCAGEM)

    # O que aconteceu no candle seguinte?
    high_next = highs[-1]
    low_next = lows[-1]
    close_next = closes[-1]

    # Verificar se bateu take ou stop primeiro (pelo range do candle)
    hit_take = False
    hit_stop = False

    if dir_sim == "COMPRA":
        if high_next >= take_sim and low_next > stop_sim:
            hit_take = True
        elif low_next <= stop_sim and high_next < take_sim:
            hit_stop = True
        elif high_next >= take_sim and low_next <= stop_sim:
            # Bateu os dois — assume que bateu o take primeiro (tendência a favor)
            hit_take = True
    else:  # VENDA
        if low_next <= take_sim and high_next < stop_sim:
            hit_take = True
        elif high_next >= stop_sim and low_next > take_sim:
            hit_stop = True
        elif low_next <= take_sim and high_next >= stop_sim:
            hit_take = True  # tendência a favor

    # Resultado
    if hit_take:
        resultado_pct = RISCO_POR_TRADE_PCT * RELACAO_RISCO_RETORNO  # +3%
        resultado_rs = CAPITAL_INICIAL * resultado_pct / 100
        status = "WIN 🟢"
    elif hit_stop:
        resultado_pct = -RISCO_POR_TRADE_PCT  # -1%
        resultado_rs = CAPITAL_INICIAL * resultado_pct / 100
        status = "LOSS 🔴"
    else:
        # Não bateu nenhum — fecha no close
        if dir_sim == "COMPRA":
            var_pct = (close_next - entry_sim) / entry_sim
        else:
            var_pct = (entry_sim - close_next) / entry_sim
        resultado_pct = var_pct * ALAVANCAGEM * lote_sim * 100  # em % do capital
        resultado_rs = CAPITAL_INICIAL * resultado_pct / 100
        status = "PARCIAL ⚡"

    # Calcular o swing em pips
    if 'JPY' in pair_name:
        swing_stop = stop_dist_sim * 100
        swing_take = take_dist_sim * 100
    else:
        swing_stop = stop_dist_sim * 10000
        swing_take = take_dist_sim * 10000

    return {
        'par': pair_name,
        'direcao': dir_sim,
        'entry': round(entry_sim, 5),
        'stop': round(stop_sim, 5),
        'take': round(take_sim, 5),
        'stop_pips': round(swing_stop, 1),
        'take_pips': round(swing_take, 1),
        'atr': round(atr_sim, 5),
        'lote_pct_capital': round(lote_sim * 100, 2),  # % do capital alocado
        'alavancagem_efetiva': round(lote_sim * ALAVANCAGEM, 1),
        'close_final': round(close_next, 5),
        'resultado_pct_capital': round(resultado_pct, 4),
        'resultado_rs': round(resultado_rs, 2),
        'status': status
    }


# ═══════════════════════════════════════════
# EXECUÇÃO PRINCIPAL
# ═══════════════════════════════════════════

print("╔══════════════════════════════════════════════════════════════╗")
print("║  📊 SIMULAÇÃO ALAVANCADA 50X — FOREX PICOS DE VOLUME       ║")
print("║  Risco:Retorno = 1:3 | Stop = 1.5×ATR | Risco/trade = 1%  ║")
print(f"║  Capital: R$ {CAPITAL_INICIAL:,.2f} | Alavancagem: {ALAVANCAGEM}x")
print("╚══════════════════════════════════════════════════════════════╝")
print()

random.seed(42)

# Buscar todos os dados primeiro
all_pairs = {}
for pico_key, pico in PICOS.items():
    for pair_name, symbol in pico['pares'].items():
        if symbol not in all_pairs:
            print(f"  🔄 Buscando {pair_name} ({symbol})...", end=' ')
            all_pairs[symbol] = fetch_forex(symbol, 90)
            if 'error' in all_pairs[symbol]:
                print(f"❌ {all_pairs[symbol]['error']}")
            else:
                print(f"✅ {len(all_pairs[symbol]['closes'])} candles")

print()

# Simular por pico
capital = CAPITAL_INICIAL
todos_trades = []
resultados_por_pico = {}

for pico_key, pico in PICOS.items():
    print(f"  {'─' * 62}")
    print(f"  {pico['nome']} ({pico['horario_brt']} BRT)")
    print(f"  {'─' * 62}")

    pico_trades = []
    for pair_name, symbol in pico['pares'].items():
        data = all_pairs[symbol]
        trade = simulate_leveraged_trade(pair_name, data)

        if trade is None:
            print(f"    ⚠️ {pair_name}: dados insuficientes")
            continue

        pico_trades.append(trade)
        todos_trades.append(trade)

        # Aplicar resultado ao capital
        capital += trade['resultado_rs']

        icon = trade['status'].split()[0]
        print(f"    {icon} {trade['par']}: {trade['direcao']} @ {trade['entry']}")
        print(f"       Stop: {trade['stop']} ({trade['stop_pips']} pips) | "
              f"Take: {trade['take']} ({trade['take_pips']} pips)")
        print(f"       ATR: {trade['atr']} | Lote: {trade['lote_pct_capital']}% capital | "
              f"Alav. efetiva: {trade['alavancagem_efetiva']}x")
        print(f"       Resultado: R$ {trade['resultado_rs']:+.2f} "
              f"({trade['resultado_pct_capital']:+.2f}% do capital) | {trade['status']}")
        print()

    resultados_por_pico[pico_key] = {
        'nome': pico['nome'],
        'trades': len(pico_trades),
        'pnl_rs': sum(t['resultado_rs'] for t in pico_trades),
        'pnl_pct': sum(t['resultado_pct_capital'] for t in pico_trades)
    }

# ═══════════════════════════════════════════
# SUMÁRIO CONSOLIDADO
# ═══════════════════════════════════════════

wins = [t for t in todos_trades if 'WIN' in t['status']]
losses = [t for t in todos_trades if 'LOSS' in t['status']]
parciais = [t for t in todos_trades if 'PARCIAL' in t['status']]

print(f"  {'═' * 62}")
print(f"  📊 SUMÁRIO FINAL — ALAVANCADO 50x (1:3)")
print(f"  {'═' * 62}")
print()

# Por pico
for pico_key, res in resultados_por_pico.items():
    icon = "🟢" if res['pnl_rs'] > 0 else "🔴"
    print(f"  {icon} {res['nome']}: {res['trades']} trades | "
          f"R$ {res['pnl_rs']:+.2f} ({res['pnl_pct']:+.2f}%)")

print()
print(f"  Capital inicial:   R$ {CAPITAL_INICIAL:,.2f}")
print(f"  Capital final:     R$ {capital:,.2f}")
print(f"  Lucro líquido:     R$ {capital - CAPITAL_INICIAL:+,.2f}")
print(f"  Rentabilidade:     {(capital/CAPITAL_INICIAL - 1)*100:+.2f}%")
print()
print(f"  Total trades:      {len(todos_trades)}")
print(f"  Wins:              {len(wins)} 🟢")
print(f"  Losses:            {len(losses)} 🔴")
print(f"  Parciais:          {len(parciais)} ⚡")
if todos_trades:
    print(f"  Win rate:          {len(wins)/len(todos_trades)*100:.1f}%")
    print(f"  PnL médio/trade:   R$ {(capital-CAPITAL_INICIAL)/len(todos_trades):+.2f}")
print()

# Ranking
print(f"  🏆 RANKING POR LUCRO:")
ranking = sorted(todos_trades, key=lambda t: t['resultado_rs'], reverse=True)
for i, t in enumerate(ranking, 1):
    icon = t['status'].split()[0]
    print(f"  {i}. {icon} {t['par']}: {t['direcao']} | "
          f"R$ {t['resultado_rs']:+.2f} ({t['resultado_pct_capital']:+.2f}%) | "
          f"Stop={t['stop_pips']}pips Take={t['take_pips']}pips")

# Detalhe: exposição × resultado
print()
print(f"  📈 ANÁLISE DE RISCO:")
for t in todos_trades:
    risco_rs = CAPITAL_INICIAL * RISCO_POR_TRADE_PCT / 100
    retorno_rs = t['resultado_rs']
    rr_real = abs(retorno_rs / risco_rs) if risco_rs > 0 else 0
    print(f"  {t['par']}: Arriscou R$ {risco_rs:.2f} → Retornou R$ {retorno_rs:+.2f} "
          f"(R:R real = 1:{rr_real:.1f})")

print()
print(f"  {'═' * 62}")
print(f"  ⚠️ AVISO: Simulação com dados históricos. Resultados passados")
print(f"  não garantem rentabilidade futura. Alavancagem 50x pode causar")
print(f"  perda total do capital se o stop não for respeitado.")
print(f"  {'═' * 62}")
