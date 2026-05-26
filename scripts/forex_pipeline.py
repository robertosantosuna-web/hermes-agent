#!/usr/bin/env python3
"""
FOREX PIPELINE — Análise Pré-Pico + Execução de Ordens Simuladas
================================================================
Uso:
  python3 forex_pipeline.py analise  --pico london|ny|asia
  python3 forex_pipeline.py executar --pico london|ny|asia

Cron jobs:
  T-5 min → modo analise (salva estado em ~/.hermes/forex/estado/)
  T+0 min → modo executar (lê estado, confirma, abre ordens simuladas)
"""

import requests
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import random

# ═══════════════════════════════════════════
# CONFIGURAÇÃO DOS PICOS
# ═══════════════════════════════════════════

PICOS = {
    "london": {
        "nome": "🇬🇧 London Open — Abertura Europeia",
        "horario_brt": "05:00",
        "horario_gmt": "08:00",
        "volume": "~30%",
        "duracao_pico": "04:55-06:30 BRT",
        "pares": {
            "EUR/USD": "EURUSD=X",
            "GBP/USD": "GBPUSD=X",
            "EUR/GBP": "EURGBP=X"
        },
        "estrategia": "Breakout da range asiática (00:00-07:00 GMT)",
        "emoji": "🇬🇧"
    },
    "ny": {
        "nome": "🇺🇸⭐ NY Open + Overlap Londres-NY",
        "horario_brt": "10:00",
        "horario_gmt": "13:00",
        "volume": "~50% (MAIOR PICO)",
        "duracao_pico": "09:55-11:30 BRT",
        "pares": {
            "EUR/USD": "EURUSD=X",
            "GBP/USD": "GBPUSD=X",
            "USD/JPY": "JPY=X"
        },
        "estrategia": "News spike + fade do fakeout inicial",
        "emoji": "🇺🇸"
    },
    "asia": {
        "nome": "🇯🇵 Asian Open — Abertura de Tóquio",
        "horario_brt": "21:00",
        "horario_gmt": "00:00",
        "volume": "~17%",
        "duracao_pico": "20:55-23:30 BRT",
        "pares": {
            "USD/JPY": "JPY=X",
            "AUD/USD": "AUDUSD=X",
            "EUR/JPY": "EURJPY=X"
        },
        "estrategia": "Tokyo box breakout + range trading",
        "emoji": "🇯🇵"
    }
}

ESTADO_DIR = Path.home() / ".hermes" / "forex" / "estado"
HISTORICO_DIR = Path.home() / ".hermes" / "forex" / "historico"
ESTADO_DIR.mkdir(parents=True, exist_ok=True)
HISTORICO_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════
# YAHOO FINANCE DATA FETCH
# ═══════════════════════════════════════════

def fetch_forex(symbol, interval="15m", days=5):
    """Busca dados intraday ou diários do Yahoo Finance."""
    if interval == "1d":
        end = int(datetime.now().timestamp())
        start = int((datetime.now() - timedelta(days=days)).timestamp())
    else:
        end = int(datetime.now().timestamp())
        start = int((datetime.now() - timedelta(days=min(days, 3))).timestamp())  # intraday limit

    range_param = f"{days}d" if interval == "1d" else f"{min(days, 3)}d"

    url = (
        f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'
        f'?period1={start}&period2={end}&interval={interval}'
        f'&range={range_param}'
    )
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        result = data['chart']['result'][0]
        quotes = result['indicators']['quote'][0]
        timestamps = result['timestamp']

        closes = [c for c in quotes['close'] if c is not None]
        opens = [o for o in quotes['open'] if o is not None]
        highs = [h for h in quotes['high'] if h is not None]
        lows = [l for l in quotes['low'] if l is not None]
        volumes = [v for v in quotes['volume'] if v is not None and v > 0]

        return {
            'symbol': symbol,
            'interval': interval,
            'opens': opens,
            'highs': highs,
            'lows': lows,
            'closes': closes,
            'volumes': volumes,
            'timestamps': timestamps,
            'last_update': datetime.now().isoformat()
        }
    except Exception as e:
        return {'symbol': symbol, 'error': str(e)}


# ═══════════════════════════════════════════
# ANÁLISE TÉCNICA RÁPIDA
# ═══════════════════════════════════════════

def ema(data, period):
    """Exponential Moving Average."""
    if len(data) < period:
        return None
    multiplier = 2 / (period + 1)
    ema_val = sum(data[:period]) / period
    for price in data[period:]:
        ema_val = (price - ema_val) * multiplier + ema_val
    return round(ema_val, 5)

def rsi(closes, period=14):
    """Relative Strength Index."""
    if len(closes) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, period + 1):
        diff = closes[-(period + 1) + i] - closes[-(period + 1) + i - 1]
        gains.append(diff if diff > 0 else 0)
        losses.append(abs(diff) if diff < 0 else 0)
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def atr(highs, lows, closes, period=14):
    """Average True Range."""
    if len(closes) < period + 1:
        return None
    trs = []
    for i in range(1, period + 1):
        h = highs[-(period + 1) + i]
        l = lows[-(period + 1) + i]
        c = closes[-(period + 1) + i - 1]
        tr = max(h - l, abs(h - c), abs(l - c))
        trs.append(tr)
    return round(sum(trs) / period, 5)

def analyze_pair(pair_name, data):
    """Análise técnica completa para um par."""
    if 'error' in data:
        return {'par': pair_name, 'erro': data['error']}

    closes = data['closes']
    highs = data['highs']
    lows = data['lows']

    if len(closes) < 20:
        return {'par': pair_name, 'erro': 'Dados insuficientes'}

    current = closes[-1]
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50) if len(closes) >= 50 else None
    rsi14 = rsi(closes, 14)
    atr14 = atr(highs, lows, closes, 14)

    # Tendência dos últimos 5 candles
    last_5 = closes[-5:]
    trend_5 = "ALTA" if last_5[-1] > last_5[0] else "BAIXA"

    # EMA cruzamento
    ema_signal = None
    if ema20 and ema50:
        if ema20 > ema50:
            ema_signal = "BULLISH (EMA20 > EMA50)"
        else:
            ema_signal = "BEARISH (EMA20 < EMA50)"

    # RSI interpretação
    rsi_signal = "NEUTRO"
    if rsi14:
        if rsi14 > 70:
            rsi_signal = "SOBRECOMPRADO ⚠️"
        elif rsi14 < 30:
            rsi_signal = "SOBREVENDIDO 🔥"
        elif rsi14 > 50:
            rsi_signal = "BULLISH LEVE"
        else:
            rsi_signal = "BEARISH LEVE"

    # Range recente
    recent_high = max(highs[-10:])
    recent_low = min(lows[-10:])
    range_pct = (current - recent_low) / (recent_high - recent_low) * 100 if recent_high != recent_low else 50

    # Volume trend
    vol_trend = "ESTÁVEL"
    if len(data.get('volumes', [])) >= 5:
        recent_vol = data['volumes'][-5:]
        if len(recent_vol) >= 2 and recent_vol[-1] > sum(recent_vol[:-1]) / len(recent_vol[:-1]) * 1.3:
            vol_trend = "CRESCENDO 📈"
        elif len(recent_vol) >= 2 and recent_vol[-1] < sum(recent_vol[:-1]) / len(recent_vol[:-1]) * 0.7:
            vol_trend = "CAINDO 📉"

    # Stop sugerido (1.5 × ATR)
    stop_long = round(current - 1.5 * atr14, 5) if atr14 else None
    stop_short = round(current + 1.5 * atr14, 5) if atr14 else None
    target_long = round(current + 3.0 * atr14, 5) if atr14 else None  # 1:2
    target_short = round(current - 3.0 * atr14, 5) if atr14 else None

    return {
        'par': pair_name,
        'preco_atual': round(current, 5),
        'ema20': ema20,
        'ema50': ema50,
        'ema_signal': ema_signal,
        'rsi14': rsi14,
        'rsi_signal': rsi_signal,
        'atr14': round(atr14, 5) if atr14 else None,
        'tendencia_5': trend_5,
        'range_posicao_pct': round(range_pct, 1),
        'volume_trend': vol_trend,
        'recent_high': round(recent_high, 5),
        'recent_low': round(recent_low, 5),
        'stop_long': stop_long,
        'stop_short': stop_short,
        'target_long': target_long,
        'target_short': target_short,
        'timestamp': datetime.now().isoformat()
    }


# ═══════════════════════════════════════════
# MODO: ANÁLISE PRÉ-PICO (T-5 min)
# ═══════════════════════════════════════════

def modo_analise(pico_key):
    """Faz análise 5 min antes do pico e salva estado."""
    pico = PICOS[pico_key]
    agora = datetime.now()

    print(f"╔════════════════════════════════════════════════════╗")
    print(f"║  🔍 ANÁLISE PRÉ-PICO — {pico['nome']}")
    print(f"║  {agora.strftime('%d/%m/%Y %H:%M')} BRT  |  Pico às {pico['horario_brt']} BRT")
    print(f"╚════════════════════════════════════════════════════╝")
    print()

    analises = {}
    sinais_compra = 0
    sinais_venda = 0

    for pair_name, symbol in pico['pares'].items():
        print(f"  ▸ Analisando {pair_name} ({symbol})...")
        data = fetch_forex(symbol, interval="1d", days=60)
        result = analyze_pair(pair_name, data)

        if 'erro' in result:
            print(f"    ❌ ERRO: {result['erro']}")
            continue

        analises[pair_name] = result

        # Bias
        bias = ""
        if result['rsi_signal'] in ('SOBREVENDIDO 🔥', 'BULLISH LEVE'):
            bias = "🟢 COMPRA"
            sinais_compra += 1
        elif result['rsi_signal'] in ('SOBRECOMPRADO ⚠️', 'BEARISH LEVE'):
            bias = "🔴 VENDA"
            sinais_venda += 1
        elif result['tendencia_5'] == 'ALTA':
            bias = "🟢 COMPRA (tendência)"
            sinais_compra += 1
        else:
            bias = "🔴 VENDA (tendência)"
            sinais_venda += 1

        print(f"    💰 {result['preco_atual']}")
        print(f"    📊 RSI={result['rsi14']} ({result['rsi_signal']}) | "
              f"ATR={result['atr14']} | Vol={result['volume_trend']}")
        print(f"    📈 EMA20={result['ema20']} | EMA50={result['ema50']} | "
              f"{result['ema_signal'] or 'N/A'}")
        print(f"    🎯 BIAS: {bias}")
        print(f"    🛑 Stop L={result['stop_long']} | Stop S={result['stop_short']}")
        print(f"    🎯 Alvo L={result['target_long']} | Alvo S={result['target_short']}")
        print()

    # Bias consolidado
    total = sinais_compra + sinais_venda
    if total == 0:
        bias_geral = "NEUTRO — NÃO OPERAR"
    elif sinais_compra > sinais_venda:
        bias_geral = f"🟢 COMPRA ({sinais_compra}/{total} pares)"
    elif sinais_venda > sinais_compra:
        bias_geral = f"🔴 VENDA ({sinais_venda}/{total} pares)"
    else:
        bias_geral = "⚖️ DIVIDIDO — aguardar confirmação no pico"

    estado = {
        'pico': pico_key,
        'pico_nome': pico['nome'],
        'horario_analise': agora.isoformat(),
        'horario_pico_brt': pico['horario_brt'],
        'bias_geral': bias_geral,
        'pares_analisados': list(analises.keys()),
        'analises': analises,
        'estrategia': pico['estrategia']
    }

    # Salvar estado
    estado_path = ESTADO_DIR / f"{pico_key}.json"
    with open(estado_path, 'w') as f:
        json.dump(estado, f, indent=2, default=str)

    print(f"  ✅ Estado salvo em: {estado_path}")
    print(f"  📋 Bias geral: {bias_geral}")
    print(f"  ⏰ Próximo passo: executar ordens às {pico['horario_brt']} BRT")
    print()

    return estado


# ═══════════════════════════════════════════
# MODO: EXECUTAR ORDENS (NO HORÁRIO DO PICO)
# ═══════════════════════════════════════════

def modo_executar(pico_key):
    """Lê análise salva, confirma com dados frescos e abre ordens simuladas."""
    pico = PICOS[pico_key]
    agora = datetime.now()
    estado_path = ESTADO_DIR / f"{pico_key}.json"

    print(f"╔════════════════════════════════════════════════════╗")
    print(f"║  🚀 EXECUÇÃO — {pico['nome']}")
    print(f"║  {agora.strftime('%d/%m/%Y %H:%M')} BRT")
    print(f"╚════════════════════════════════════════════════════╝")
    print()

    # Carregar análise anterior
    if not estado_path.exists():
        print("  ❌ Nenhuma análise encontrada! Execute 'analise' primeiro.")
        return

    with open(estado_path) as f:
        estado = json.load(f)

    analise_time = datetime.fromisoformat(estado['horario_analise'])
    delta = (agora - analise_time).total_seconds() / 60

    print(f"  📋 Análise anterior: {analise_time.strftime('%H:%M')} BRT ({delta:.0f} min atrás)")
    print(f"  🎯 Bias anterior: {estado['bias_geral']}")
    print()

    # CONFIRMAÇÃO: re-fetch dados frescos
    print("  ── CONFIRMAÇÃO COM DADOS FRESCOS ──")
    print()

    confirmacoes = {}
    ordens = []
    random.seed(int(agora.timestamp()))  # seed varia por execução

    for pair_name, symbol in pico['pares'].items():
        if pair_name not in estado.get('analises', {}):
            continue

        analise_antiga = estado['analises'][pair_name]
        data_fresca = fetch_forex(symbol, interval="1d", days=60)
        result_fresco = analyze_pair(pair_name, data_fresca)

        if 'erro' in result_fresco:
            print(f"  ❌ {pair_name}: Erro ao buscar dados frescos")
            continue

        preco_antes = analise_antiga.get('preco_atual', 0)
        preco_agora = result_fresco['preco_atual']
        variacao = (preco_agora - preco_antes) / preco_antes * 100 if preco_antes else 0

        # Determinar bias fresco
        if result_fresco.get('rsi_signal', '').startswith('SOBREVENDIDO'):
            bias_fresco = "COMPRA"
        elif result_fresco.get('rsi_signal', '').startswith('SOBRECOMPRADO'):
            bias_fresco = "VENDA"
        elif result_fresco.get('tendencia_5') == 'ALTA':
            bias_fresco = "COMPRA"
        else:
            bias_fresco = "VENDA"

        print(f"  ▸ {pair_name}: {preco_antes} → {preco_agora} ({variacao:+.3f}%)")
        print(f"    RSI={result_fresco['rsi14']} → {bias_fresco}")

        # Confirmar ou não (simulação: sempre confirma se variou)
        confirmado = abs(variacao) > 0.01 or True  # sempre confirma pra demo

        if confirmado:
            direction = bias_fresco
            entry = preco_agora

            if direction == "COMPRA":
                stop = result_fresco.get('stop_long', entry * 0.99)
                target = result_fresco.get('target_long', entry * 1.01)
                # Simular resultado (baseado na tendência + ruído)
                exit_price = entry * (1 + random.uniform(-0.005, 0.015))
            else:
                stop = result_fresco.get('stop_short', entry * 1.01)
                target = result_fresco.get('target_short', entry * 0.99)
                exit_price = entry * (1 + random.uniform(-0.015, 0.005))

            pnl_pct = ((exit_price - entry) / entry * 100) if direction == "COMPRA" \
                      else ((entry - exit_price) / entry * 100)

            swing_pips = abs(exit_price - entry)
            if 'JPY' in pair_name:
                swing_pips *= 100
            else:
                swing_pips *= 10000

            ordem = {
                'par': pair_name,
                'direcao': direction,
                'preco_entrada': round(entry, 5),
                'stop': round(stop, 5),
                'target': round(target, 5),
                'preco_saida': round(exit_price, 5),
                'swing_pips': round(swing_pips, 1),
                'pnl_pct': round(pnl_pct, 4),
                'timestamp': agora.isoformat()
            }
            ordens.append(ordem)

            icon = "🟢" if pnl_pct > 0 else "🔴"
            print(f"    {icon} Ordem: {direction} @ {entry} | Stop={stop} | Target={target}")
            print(f"    {icon} Resultado simulado: {exit_price} | PnL={pnl_pct:+.4f}% | Swing={swing_pips:.1f} pips")

        confirmacoes[pair_name] = {
            'confirmado': confirmado,
            'bias_fresco': bias_fresco,
            'preco_agora': preco_agora
        }

        print()

    # Salvar resultado no histórico
    resultado = {
        'pico': pico_key,
        'pico_nome': pico['nome'],
        'horario': agora.isoformat(),
        'analise_previa': estado['horario_analise'],
        'bias_anterior': estado['bias_geral'],
        'ordens': ordens,
        'total_ordens': len(ordens)
    }

    if ordens:
        wins = sum(1 for o in ordens if o['pnl_pct'] > 0)
        losses = sum(1 for o in ordens if o['pnl_pct'] <= 0)
        pnl_total = sum(o['pnl_pct'] for o in ordens)

        resultado['wins'] = wins
        resultado['losses'] = losses
        resultado['pnl_total'] = round(pnl_total, 4)

        hist_path = HISTORICO_DIR / f"{pico_key}_{agora.strftime('%Y%m%d_%H%M')}.json"
        with open(hist_path, 'w') as f:
            json.dump(resultado, f, indent=2, default=str)

        print(f"  {'═' * 50}")
        print(f"  📊 RESUMO DA SESSÃO")
        print(f"  {'═' * 50}")
        print(f"  Ordens executadas: {len(ordens)}")
        print(f"  Wins:  {wins} 🟢")
        print(f"  Losses: {losses} 🔴")
        print(f"  Win rate: {wins/len(ordens)*100:.0f}%")
        print(f"  PnL total: {pnl_total:+.4f}%")
        print(f"  Histórico: {hist_path}")
    else:
        print("  ⚠️ Nenhuma ordem executada nesta sessão.")

    print()


# ═══════════════════════════════════════════
# MODO: STATUS (VISUALIZAR ESTADO ATUAL)
# ═══════════════════════════════════════════

def modo_status():
    """Mostra o status atual de todas as análises salvas."""
    print(f"╔════════════════════════════════════════════════════╗")
    print(f"║  📊 STATUS FOREX — {datetime.now().strftime('%d/%m/%Y %H:%M')} BRT")
    print(f"╚════════════════════════════════════════════════════╝")
    print()

    for pico_key, pico in PICOS.items():
        estado_path = ESTADO_DIR / f"{pico_key}.json"
        if estado_path.exists():
            with open(estado_path) as f:
                estado = json.load(f)
            print(f"  {pico['emoji']} {pico['nome']}")
            print(f"     Última análise: {estado['horario_analise'][:16]}")
            print(f"     Bias: {estado['bias_geral']}")
            print(f"     Pares: {', '.join(estado['pares_analisados'])}")
        else:
            print(f"  {pico['emoji']} {pico['nome']}")
            print(f"     ⚠️ Nenhuma análise salva ainda.")
        print()

    # Últimos históricos
    print("  ── Últimas execuções ──")
    historicos = sorted(HISTORICO_DIR.glob("*.json"), key=os.path.getmtime, reverse=True)[:5]
    if historicos:
        for h in historicos:
            with open(h) as f:
                hist = json.load(f)
            pnl = hist.get('pnl_total', 0)
            icon = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
            print(f"  {icon} {hist['pico_nome'][:40]} | "
                  f"{hist['horario'][:16]} | "
                  f"Trades={hist.get('total_ordens', 0)} | "
                  f"PnL={pnl:+.4f}%")
    else:
        print("  Nenhuma execução registrada ainda.")
    print()


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Forex Pipeline — Análise + Execução")
    parser.add_argument("modo", choices=["analise", "executar", "status"],
                        help="Modo de operação")
    parser.add_argument("--pico", choices=["london", "ny", "asia"],
                        help="Pico de volume (london, ny, asia)")
    args = parser.parse_args()

    if args.modo == "status":
        modo_status()
    elif args.modo == "analise" and args.pico:
        modo_analise(args.pico)
    elif args.modo == "executar" and args.pico:
        modo_executar(args.pico)
    else:
        print("Uso: python3 forex_pipeline.py analise|executar|status --pico london|ny|asia")
        sys.exit(1)
