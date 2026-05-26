#!/usr/bin/python3
"""
FOREX PIPELINE v2.0 — TradingView + Regras Completas
=====================================================
- Dados em tempo real via TradingView Scanner API
- Day trade: abre e fecha no mesmo dia
- Bloqueio -5 min antes de notícias (ForexFactory)
- Sexta-feira: não abre após 13:00, fecha tudo às 16:00 BRT
- Alavancagem 50x com gestão de risco 1:3
- Análise T-5 min + Execução no pico

Uso:
  python3 forex_pipeline_v2.py analise  --pico london|ny|asia
  python3 forex_pipeline_v2.py executar --pico london|ny|asia
  python3 forex_pipeline_v2.py status
"""

import sys
import os
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar diretório dos módulos
sys.path.insert(0, str(Path(__file__).parent.parent / 'forex'))
from tv_data import get_live_quotes, PAIR_TO_TICKER
from forex_calendar import should_block_trading, is_weekday, is_friday, get_news_blackout_status, get_next_news_window
from scalping_m5 import fetch_intraday, analyze_m5, PAIRS as SCALP_PAIRS

# ═══════════════════════════════════════════
# CONFIGURAÇÃO
# ═══════════════════════════════════════════

CAPITAL_INICIAL = 1000.0
ALAVANCAGEM = 50
RISCO_POR_TRADE_PCT = 1.0  # 1% do capital
RELACAO_RISCO_RETORNO = 3.0  # 1:3
ATR_MULTIPLIER_STOP = 1.5

ESTADO_DIR = Path.home() / '.hermes' / 'forex' / 'estado'
HISTORICO_DIR = Path.home() / '.hermes' / 'forex' / 'historico'
ORDENS_ABERTAS_PATH = Path.home() / '.hermes' / 'forex' / 'ordens_abertas.json'

for d in [ESTADO_DIR, HISTORICO_DIR]:
    d.mkdir(parents=True, exist_ok=True)

PICOS = {
    'london': {
        'nome': '🇬🇧 London Open',
        'horario_brt': '05:00',
        'pares': ['EUR/USD', 'GBP/USD', 'EUR/GBP'],
        'estrategia': 'Breakout da range asiática',
        'volume': '~30%'
    },
    'ny': {
        'nome': '🇺🇸⭐ NY Overlap',
        'horario_brt': '10:00',
        'pares': ['EUR/USD', 'GBP/USD', 'USD/JPY'],
        'estrategia': 'News spike + fade do fakeout',
        'volume': '~50%'
    },
    'asia': {
        'nome': '🇯🇵 Asian Open',
        'horario_brt': '21:00',
        'pares': ['USD/JPY', 'AUD/USD', 'EUR/JPY'],
        'estrategia': 'Tokyo box breakout',
        'volume': '~17%'
    }
}


# ═══════════════════════════════════════════
# ANÁLISE DE SINAL (usa dados TradingView)
# ═══════════════════════════════════════════

def analyze_signal(quote):
    """
    Analisa uma cotação do TradingView e determina o bias.

    Critérios:
    - Recommend.All: -1 (venda forte) a +1 (compra forte)
    - RSI: <30 sobrevendido (compra), >70 sobrecomprado (venda)
    - MACD: acima do signal (compra), abaixo (venda)
    - Preço vs SMA20/SMA50
    """
    signals = []
    score = 0.0  # positivo = compra, negativo = venda

    # 1. Recommend.All (peso 2)
    rec = quote.get('recommend', 0)
    if rec is not None:
        score += rec * 2
        if rec > 0.3:
            signals.append(f'Rec=COMPRA({rec:.2f})')
        elif rec < -0.3:
            signals.append(f'Rec=VENDA({rec:.2f})')
        else:
            signals.append(f'Rec=NEUTRO({rec:.2f})')

    # 2. RSI (peso 1.5)
    rsi = quote.get('rsi', 50)
    if rsi is not None:
        if rsi < 30:
            score += 1.5
            signals.append(f'RSI={rsi:.0f} SOBREVENDIDO')
        elif rsi > 70:
            score -= 1.5
            signals.append(f'RSI={rsi:.0f} SOBRECOMPRADO')
        elif rsi > 55:
            score += 0.5
            signals.append(f'RSI={rsi:.0f} bullish')
        elif rsi < 45:
            score -= 0.5
            signals.append(f'RSI={rsi:.0f} bearish')
        else:
            signals.append(f'RSI={rsi:.0f} neutro')

    # 3. MACD vs Signal (peso 1)
    macd = quote.get('macd', 0)
    macd_signal = quote.get('macd_signal', 0)
    if macd is not None and macd_signal is not None:
        if macd > macd_signal:
            score += 1.0
            macd_diff = macd - macd_signal
            signals.append(f'MACD>Signal (+{macd_diff:.5f})')
        else:
            score -= 1.0
            macd_diff = macd_signal - macd
            signals.append(f'MACD<Signal (-{macd_diff:.5f})')

    # 4. Price vs SMA20/50 (peso 1)
    close = quote.get('close', 0)
    sma20 = quote.get('sma20', 0)
    sma50 = quote.get('sma50', 0)
    if close and sma20 and sma50:
        if close > sma20 > sma50:
            score += 1.0
            signals.append('Preço>SMA20>SMA50 (tendência alta)')
        elif close < sma20 < sma50:
            score -= 1.0
            signals.append('Preço<SMA20<SMA50 (tendência baixa)')
        elif close > sma20:
            score += 0.5
            signals.append('Preço>SMA20')
        elif close < sma20:
            score -= 0.5
            signals.append('Preço<SMA20')

    # Determinar direção
    if score > 1.5:
        direction = 'COMPRA'
        strength = 'FORTE' if score > 3 else 'MODERADO'
    elif score < -1.5:
        direction = 'VENDA'
        strength = 'FORTE' if score < -3 else 'MODERADO'
    else:
        # Default: seguir Recommend ou RSI
        if rec is not None and rec > 0.1:
            direction = 'COMPRA'
            strength = 'FRACO'
        elif rec is not None and rec < -0.1:
            direction = 'VENDA'
            strength = 'FRACO'
        elif rsi and rsi > 50:
            direction = 'COMPRA'
            strength = 'FRACO'
        else:
            direction = 'VENDA'
            strength = 'FRACO'

    return {
        'direction': direction,
        'strength': strength,
        'score': round(score, 2),
        'signals': signals,
        'rsi': rsi,
        'atr': quote.get('atr'),
        'close': close,
        'bb_upper': quote.get('bb_upper'),
        'bb_lower': quote.get('bb_lower')
    }


# ═══════════════════════════════════════════
# MODO: ANÁLISE PRÉ-PICO (T-5 min)
# ═══════════════════════════════════════════

def modo_analise(pico_key):
    pico = PICOS[pico_key]
    agora = datetime.now()

    print(f'╔════════════════════════════════════════════════════╗')
    print(f"║  🔍 ANÁLISE PRÉ-PICO — {pico['nome']}")
    print(f"║  {agora.strftime('%d/%m/%Y %H:%M')} BRT | Pico às {pico['horario_brt']}")
    print(f'╚════════════════════════════════════════════════════╝')
    print()

    # Verificar bloqueios
    check = should_block_trading(pico_key, pico['pares'])
    if check['blocked']:
        print(f"  🛑 BLOQUEADO: {', '.join(check['reasons'])}")
        estado = {
            'pico': pico_key,
            'horario_analise': agora.isoformat(),
            'bloqueado': True,
            'motivo_bloqueio': check['reasons'],
            'acao': check['action']
        }
        with open(ESTADO_DIR / f'{pico_key}.json', 'w') as f:
            json.dump(estado, f, indent=2, default=str)
        return estado

    # Fechar ordens abertas se for sexta 16h
    if check['action'] == 'close_all':
        print("  🔒 Sexta-feira 16:00 — FECHANDO TODAS AS ORDENS ABERTAS")
        fechar_todas_ordens()
        return

    # Buscar dados ao vivo do TradingView
    print('  📡 Buscando dados ao vivo (TradingView API)...')
    quotes = get_live_quotes(pico['pares'])

    if 'error' in quotes:
        print(f"  ❌ Erro TradingView: {quotes['error']}")
        return

    analises = {}
    sinais_compra = 0
    sinais_venda = 0

    for pair in pico['pares']:
        if pair not in quotes:
            print(f'  ⚠️ {pair}: sem dados')
            continue

        q = quotes[pair]
        signal = analyze_signal(q)

        analises[pair] = {
            'preco': q.get('close'),
            'change_pct': q.get('change'),
            'rsi': signal['rsi'],
            'atr': q.get('atr'),
            'sma20': q.get('sma20'),
            'sma50': q.get('sma50'),
            'macd': q.get('macd'),
            'macd_signal': q.get('macd_signal'),
            'bb_upper': q.get('bb_upper'),
            'bb_lower': q.get('bb_lower'),
            'recommend': q.get('recommend'),
            'direction': signal['direction'],
            'strength': signal['strength'],
            'score': signal['score'],
            'signals_detail': signal['signals']
        }

        if signal['direction'] == 'COMPRA':
            sinais_compra += 1
        else:
            sinais_venda += 1

        icon = '🟢' if signal['direction'] == 'COMPRA' else '🔴'
        print(f"  {icon} {pair}: {q.get('close')} ({q.get('change', 0):+.3f}%)")
        print(f"     Direção: {signal['direction']} ({signal['strength']}) | Score: {signal['score']}")
        print(f"     RSI={signal['rsi']:.0f} | ATR={signal['atr']} | Rec={q.get('recommend', 0):.2f}")
        print(f"     {', '.join(signal['signals'][:3])}")

    # Bias consolidado
    if sinais_compra > sinais_venda:
        bias_geral = f'🟢 COMPRA ({sinais_compra}/{len(analises)} pares)'
    elif sinais_venda > sinais_compra:
        bias_geral = f'🔴 VENDA ({sinais_venda}/{len(analises)} pares)'
    else:
        bias_geral = '⚖️ DIVIDIDO — aguardar'

    print(f'\n  📊 Bias geral: {bias_geral}')

    # Salvar estado
    estado = {
        'pico': pico_key,
        'pico_nome': pico['nome'],
        'horario_analise': agora.isoformat(),
        'horario_pico_brt': pico['horario_brt'],
        'bloqueado': False,
        'bias_geral': bias_geral,
        'pares_analisados': list(analises.keys()),
        'analises': analises,
        'estrategia': pico['estrategia'],
        'fonte': 'TradingView'
    }

    with open(ESTADO_DIR / f'{pico_key}.json', 'w') as f:
        json.dump(estado, f, indent=2, default=str)

    print(f'  ✅ Estado salvo: {ESTADO_DIR/pico_key}.json')
    print(f'  ⏰ Execução às {pico["horario_brt"]} BRT')
    return estado


# ═══════════════════════════════════════════
# MODO: EXECUTAR ORDENS (NO PICO)
# ═══════════════════════════════════════════

def modo_executar(pico_key):
    pico = PICOS[pico_key]
    agora = datetime.now()
    estado_path = ESTADO_DIR / f'{pico_key}.json'

    print(f'╔════════════════════════════════════════════════════╗')
    print(f"║  🚀 EXECUÇÃO — {pico['nome']}")
    print(f"║  {agora.strftime('%d/%m/%Y %H:%M')} BRT")
    print(f'╚════════════════════════════════════════════════════╝')
    print()

    # Verificar bloqueios NOVAMENTE (condições podem ter mudado)
    check = should_block_trading(pico_key, pico['pares'])
    if check['blocked']:
        print(f"  🛑 EXECUÇÃO BLOQUEADA: {', '.join(check['reasons'])}")
        if check['action'] == 'close_all':
            fechar_todas_ordens()
        return

    # Carregar análise
    if not estado_path.exists():
        print('  ❌ Nenhuma análise encontrada! Execute analise primeiro.')
        return

    with open(estado_path) as f:
        estado = json.load(f)

    if estado.get('bloqueado'):
        print(f"  🛑 Análise já estava bloqueada: {estado.get('motivo_bloqueio')}")
        return

    analise_time = datetime.fromisoformat(estado['horario_analise'])
    delta = (agora - analise_time).total_seconds() / 60
    print(f"  📋 Análise: {analise_time.strftime('%H:%M')} ({delta:.0f} min atrás)")
    print(f"  🎯 Bias anterior: {estado['bias_geral']}")
    print()

    # CONFIRMAÇÃO: re-fetch TradingView
    print('  ── CONFIRMAÇÃO COM DADOS FRESCOS (TradingView) ──')
    quotes_fresh = get_live_quotes(pico['pares'])

    if 'error' in quotes_fresh:
        print(f"  ❌ Erro: {quotes_fresh['error']}")
        return

    ordens = []
    ordens_abertas = carregar_ordens_abertas()
    random.seed(int(agora.timestamp()))

    for pair in pico['pares']:
        if pair not in estado.get('analises', {}) or pair not in quotes_fresh:
            continue

        analise_antiga = estado['analises'][pair]
        q = quotes_fresh[pair]
        signal = analyze_signal(q)

        preco_antes = analise_antiga.get('preco', 0)
        preco_agora = q.get('close', 0)
        variacao = (preco_agora - preco_antes) / preco_antes * 100 if preco_antes else 0

        # Verificar se direção ainda é válida
        dir_antes = analise_antiga.get('direction', '')
        dir_agora = signal['direction']
        confirmado = dir_antes == dir_agora or signal['strength'] in ('FORTE', 'MODERADO')

        print(f"  ▸ {pair}: {preco_antes} → {preco_agora} ({variacao:+.3f}%)")
        print(f"    Dir antes={dir_antes}, agora={dir_agora} ({signal['strength']})")
        print(f"    Confirmado: {'✅' if confirmado else '⚠️ (divergência)'}")

        if not confirmado and signal['strength'] == 'FRACO':
            print(f"    ⏭️ Pulando — sinal fraco com divergência")
            continue

        # Calcular entry, stop, take
        direction = signal['direction']
        entry = preco_agora
        atr_val = q.get('atr', entry * 0.005)

        if direction == 'COMPRA':
            stop = entry - ATR_MULTIPLIER_STOP * atr_val
            target = entry + ATR_MULTIPLIER_STOP * RELACAO_RISCO_RETORNO * atr_val
        else:
            stop = entry + ATR_MULTIPLIER_STOP * atr_val
            target = entry - ATR_MULTIPLIER_STOP * RELACAO_RISCO_RETORNO * atr_val

        # Simular resultado (intraday — fecha no mesmo dia)
        # Baseado no movimento real do candle (aproximação)
        high = q.get('high', entry)
        low = q.get('low', entry)

        if direction == 'COMPRA':
            if high >= target:
                exit_price = target
                pnl_pct = RISCO_POR_TRADE_PCT * RELACAO_RISCO_RETORNO
            elif low <= stop:
                exit_price = stop
                pnl_pct = -RISCO_POR_TRADE_PCT
            else:
                exit_price = q.get('close', entry)
                var = (exit_price - entry) / entry * ALAVANCAGEM
                pnl_pct = var * 100
        else:
            if low <= target:
                exit_price = target
                pnl_pct = RISCO_POR_TRADE_PCT * RELACAO_RISCO_RETORNO
            elif high >= stop:
                exit_price = stop
                pnl_pct = -RISCO_POR_TRADE_PCT
            else:
                exit_price = q.get('close', entry)
                var = (entry - exit_price) / entry * ALAVANCAGEM
                pnl_pct = var * 100

        swing_pips = abs(entry - exit_price)
        if 'JPY' in pair:
            swing_pips *= 100
        else:
            swing_pips *= 10000

        ordem = {
            'par': pair,
            'direcao': direction,
            'preco_entrada': round(entry, 5),
            'stop': round(stop, 5),
            'target': round(target, 5),
            'preco_saida': round(exit_price, 5),
            'swing_pips': round(swing_pips, 1),
            'pnl_pct': round(pnl_pct, 4),
            'timestamp': agora.isoformat(),
            'pico': pico_key,
            'day_trade': True,
            'fechamento_previsto': f'{agora.strftime("%d/%m/%Y")} 23:59 BRT'
        }
        ordens.append(ordem)

        # Registrar como ordem aberta (para fechar no fim do dia)
        ordens_abertas.append(ordem)

        icon = '🟢' if pnl_pct > 0 else '🔴'
        print(f"    {icon} {direction} @ {entry}")
        print(f"    {icon} Stop={stop} | Target={target} | Saída={exit_price}")
        print(f"    {icon} PnL={pnl_pct:+.4f}% | Swing={swing_pips:.1f} pips")

    # Salvar ordens abertas
    salvar_ordens_abertas(ordens_abertas)

    # Salvar histórico
    resultado = {
        'pico': pico_key,
        'pico_nome': pico['nome'],
        'horario': agora.isoformat(),
        'ordens': ordens,
        'total_ordens': len(ordens),
        'fonte': 'TradingView'
    }

    if ordens:
        wins = sum(1 for o in ordens if o['pnl_pct'] > 0)
        pnl_total = sum(o['pnl_pct'] for o in ordens)
        resultado['wins'] = wins
        resultado['losses'] = len(ordens) - wins
        resultado['pnl_total'] = round(pnl_total, 4)

        hist_path = HISTORICO_DIR / f'{pico_key}_{agora.strftime("%Y%m%d_%H%M")}.json'
        with open(hist_path, 'w') as f:
            json.dump(resultado, f, indent=2, default=str)

        print(f"\n  {'═' * 50}")
        print(f'  📊 RESUMO DA SESSÃO')
        print(f'  Total: {len(ordens)} trades | Wins: {wins} | PnL: {pnl_total:+.4f}%')
        print(f"  Ordens abertas no dia: {len(ordens_abertas)}")
        print(f"  ⚠️ LEMBRETE: Todas as ordens devem ser fechadas hoje!")

    # Se for sexta-feira, verificar fechamento
    if is_friday():
        agora_hora = agora.hour
        if agora_hora >= 16:
            print('\n  🔒 Sexta-feira 16:00+ — FECHANDO TODAS AS ORDENS!')
            fechar_todas_ordens()


# ═══════════════════════════════════════════
# GESTÃO DE ORDENS ABERTAS
# ═══════════════════════════════════════════

def carregar_ordens_abertas():
    if ORDENS_ABERTAS_PATH.exists():
        with open(ORDENS_ABERTAS_PATH) as f:
            return json.load(f)
    return []

def salvar_ordens_abertas(ordens):
    with open(ORDENS_ABERTAS_PATH, 'w') as f:
        json.dump(ordens, f, indent=2, default=str)

def fechar_todas_ordens():
    """Fecha todas as ordens abertas (sexta 16h ou emergência)."""
    ordens = carregar_ordens_abertas()
    if not ordens:
        print('  Nenhuma ordem aberta para fechar.')
        return

    agora = datetime.now()
    print(f'  Fechando {len(ordens)} ordens abertas...')

    # Buscar preços atuais para calcular PnL de fechamento
    todos_pares = list(set(o['par'] for o in ordens))
    quotes = get_live_quotes(todos_pares)

    fechadas = []
    pnl_total = 0
    for ordem in ordens:
        pair = ordem['par']
        current_price = quotes.get(pair, {}).get('close', ordem['preco_entrada'])

        if ordem['direcao'] == 'COMPRA':
            pnl = (current_price - ordem['preco_entrada']) / ordem['preco_entrada'] * 100
        else:
            pnl = (ordem['preco_entrada'] - current_price) / ordem['preco_entrada'] * 100

        ordem['preco_fechamento'] = current_price
        ordem['pnl_fechamento'] = round(pnl, 4)
        ordem['fechado_em'] = agora.isoformat()
        fechadas.append(ordem)
        pnl_total += pnl

        icon = '🟢' if pnl > 0 else '🔴'
        print(f"  {icon} {pair} {ordem['direcao']}: "
              f"{ordem['preco_entrada']} → {current_price} | PnL={pnl:+.4f}%")

    # Salvar fechamento no histórico
    hist_path = HISTORICO_DIR / f'fechamento_{agora.strftime("%Y%m%d_%H%M")}.json'
    with open(hist_path, 'w') as f:
        json.dump({'tipo': 'fechamento_geral', 'ordens': fechadas,
                    'pnl_total': round(pnl_total, 4)}, f, indent=2, default=str)

    # Limpar ordens abertas
    ORDENS_ABERTAS_PATH.unlink(missing_ok=True)

    print(f'\n  ✅ {len(fechadas)} ordens fechadas | PnL total: {pnl_total:+.4f}%')
    print(f'  📁 Histórico: {hist_path}')


# ═══════════════════════════════════════════
# MODO: STATUS
# ═══════════════════════════════════════════

def modo_status():
    agora = datetime.now()
    print(f'╔════════════════════════════════════════════════════╗')
    print(f"║  📊 STATUS FOREX — {agora.strftime('%d/%m/%Y %H:%M')} BRT")
    print(f'╚════════════════════════════════════════════════════╝')
    print()

    # Ordens abertas
    ordens = carregar_ordens_abertas()
    print(f'  📋 Ordens abertas hoje: {len(ordens)}')
    for o in ordens[-5:]:
        pnl = o.get('pnl_pct', 0)
        icon = '🟢' if pnl > 0 else '🔴'
        print(f"     {icon} {o['par']} {o['direcao']} @ {o['preco_entrada']} | PnL={pnl:+.4f}%")

    # Regras
    print(f'\n  📅 Regras ativas:')
    print(f'     Dia útil: {"✅" if is_weekday() else "❌ (fim de semana)"}')
    print(f'     Sexta-feira: {"⚠️ SIM" if is_friday() else "Não"}')

    # Blackout de notícias
    blackout = get_news_blackout_status()
    print(f'\n  🛑 Blackout notícias:')
    if blackout['in_blackout']:
        print(f'     ⛔ EM BLACKOUT — Não operar!')
        for e in blackout['events']:
            print(f'     {e["impact"]} {e["time_brt"]} BRT — {e["description"]} ({e["currencies"]})')
        if blackout.get('resume_at'):
            print(f'     ⏰ Liberado às: {blackout["resume_at"][:16]}')
    else:
        print(f'     ✅ Sem restrições ativas')
        print(f'\n  ⏰ Próximas janelas:')
        for w in get_next_news_window()[:4]:
            print(f'     {w["impact"]} {w["time_brt"]} BRT — {w["description"]} ({w["currencies"]}')

    # Últimas execuções
    print(f'\n  📈 Últimas execuções:')
    historicos = sorted(HISTORICO_DIR.glob('*.json'), key=os.path.getmtime, reverse=True)[:5]
    for h in historicos:
        with open(h) as f:
            hist = json.load(f)
        pnl = hist.get('pnl_total', 0)
        icon = '🟢' if pnl > 0 else '🔴' if pnl < 0 else '⚪'
        tipo = hist.get('tipo', hist.get('pico_nome', '?'))[:40]
        print(f'     {icon} {tipo} | Trades={hist.get("total_ordens", 0)} | PnL={pnl:+.4f}%')


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Forex Pipeline v2 — TradingView + Regras + Scalping')
    parser.add_argument('modo', choices=['analise', 'executar', 'status', 'fechar', 'scalping'],
                        help='Modo de operação (scalping = análise M5)')
    parser.add_argument('--pico', choices=['london', 'ny', 'asia'],
                        help='Pico de volume')
    parser.add_argument('--tf', choices=['5', '15'], default='5',
                        help='Timeframe para scalping (M5 ou M15)')
    args = parser.parse_args()

    if args.modo == 'status':
        modo_status()
    elif args.modo == 'fechar':
        fechar_todas_ordens()
    elif args.modo == 'analise' and args.pico:
        modo_analise(args.pico)
    elif args.modo == 'executar' and args.pico:
        modo_executar(args.pico)
    elif args.modo == 'scalping':
        from scalping_m5 import fetch_intraday, analyze_m5, PAIRS as SCALP_PAIRS
        tf = f'{args.tf}m'
        print(f"╔{'═'*58}╗")
        print(f"║  ⚡ SCALPING M{args.tf} — Análise Curto Prazo")
        print(f"║  {datetime.now().strftime('%d/%m/%Y %H:%M')} BRT | 50x | RR 1:3")
        print(f"╚{'═'*58}╝\n")
        
        # Verificar blackout
        check = should_block_trading('scalping', list(SCALP_PAIRS.keys()))
        if check['blocked']:
            print(f"  🛑 BLOQUEADO: {', '.join(check['reasons'])}")
            sys.exit(0)
        
        all_signals = []
        for pair, symbol in SCALP_PAIRS.items():
            data = fetch_intraday(symbol, tf, hours=6)
            result = analyze_m5(pair, data)
            if result is None:
                print(f"  ❌ {pair}: dados insuficientes")
                continue
            all_signals.append(result)
            
            dir_icon = {'COMPRA': '🟢', 'VENDA': '🔴', 'NEUTRO': '⚪'}
            icon = dir_icon.get(result['direction'], '⚪')
            print(f"  {icon} {pair}: {result['price']} | {result['direction']} ({result['strength']}) | Score={result['score']}")
            print(f"     EMA9={result['indicators']['ema9']} RSI={result['indicators']['rsi9']} | Mom={result['indicators']['momentum_pips']}p")
            if result['trade']['stop']:
                print(f"     🎯 Stop={result['trade']['stop_pips']}p | Target={result['trade']['target_pips']}p | "
                      f"R:R=1:{RELACAO_RISCO_RETORNO:.0f}")
            print()
        
        buys = sum(1 for s in all_signals if s['direction'] == 'COMPRA')
        sells = sum(1 for s in all_signals if s['direction'] == 'VENDA')
        print(f"  📊 🟢{buys} | 🔴{sells} | ⚪{len(all_signals)-buys-sells}")
    else:
        print('Uso: forex_pipeline_v2.py analise|executar|status|fechar|scalping [--pico london|ny|asia] [--tf 5|15]')
        sys.exit(1)
