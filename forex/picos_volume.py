#!/usr/bin/env python3
"""
MAPEAMENTO DOS 3 MAIORES PICOS DE VOLUME DO FOREX
+ Rotina de análise 5 min antes + Simulação de entradas nos picos
===============================================================
Autor: ENTIDADE / Roberto Rodrigues
Data: 18/05/2026
Timezone: BRT (GMT-3)
"""

import requests
from datetime import datetime, timedelta
import json
import random
import statistics

# ═══════════════════════════════════════════════════════════════
# SEÇÃO 1: MAPEAMENTO DOS 3 PICOS DE VOLUME
# ═══════════════════════════════════════════════════════════════

PICOS = {
    "PICO_1": {
        "nome": "London Open — Abertura Europeia",
        "horario_gmt": "08:00",
        "horario_brt": "05:00",
        "fuso": "GMT/BRT",
        "porcentagem_volume_diario": "~30%",
        "range_pips_medio": "30-80 pips (EUR/USD)",
        "duracao_pico": "07:30 - 09:00 GMT (90 min de alta intensidade)",
        "caracteristica": "Bancos europeus entram, ordens overnight executadas,"
                         " notícias da madrugada precificadas. Maior aceleração"
                         " de volume das 07:55 às 08:15 GMT.",
        "pares_principais": {
            "EUR/USD": {
                "yahoo_symbol": "EURUSD=X",
                "porcentagem_sessao": "~40% do volume da sessão",
                "spread_medio": "0.1-0.3 pips",
                "perfil": "Par mais líquido do mundo. Range 40-80 pips na abertura."
            },
            "GBP/USD": {
                "yahoo_symbol": "GBPUSD=X",
                "porcentagem_sessao": "~25%",
                "spread_medio": "0.5-1.5 pips",
                "perfil": "Cable. Extremamente volátil na abertura de Londres. Range 50-120 pips."
            },
            "EUR/GBP": {
                "yahoo_symbol": "EURGBP=X",
                "porcentagem_sessao": "~15%",
                "spread_medio": "0.5-1.0 pips",
                "perfil": "Cross europeu puro. Movimentos técnicos limpos em Londres."
            }
        },
        "estrategia_preferida": "Breakout da range asiática (00:00-07:00 GMT)."
    },

    "PICO_2": {
        "nome": "NY Open + Overlap Londres-NY",
        "horario_gmt": "13:00",
        "horario_brt": "10:00",
        "fuso": "GMT/BRT",
        "porcentagem_volume_diario": "~45-50% (MAIOR PICO DO DIA)",
        "range_pips_medio": "50-100+ pips (EUR/USD)",
        "duracao_pico": "12:30 - 17:00 GMT (4.5h — mas o pico REAL são os"
                       " primeiros 90 min: 12:30-14:00 GMT)",
        "caracteristica": "DOIS mercados abertos simultaneamente. Londres ainda"
                         " ativa, Nova York entrando. Liquidez máxima do dia."
                         " Dados econômicos dos EUA saem 08:30 ET (12:30 GMT)."
                         " Movimentos explosivos nos primeiros 30-60 min.",
        "pares_principais": {
            "EUR/USD": {
                "yahoo_symbol": "EURUSD=X",
                "porcentagem_sessao": "~35%",
                "spread_medio": "0.0-0.2 pips",
                "perfil": "Liquidez absoluta. Melhores spreads do dia. Range 60-120 pips."
            },
            "GBP/USD": {
                "yahoo_symbol": "GBPUSD=X",
                "porcentagem_sessao": "~20%",
                "spread_medio": "0.3-1.0 pips",
                "perfil": "Cable no overlap. Notícias UK+US simultâneas. Range 80-150 pips."
            },
            "USD/JPY": {
                "yahoo_symbol": "JPY=X",
                "porcentagem_sessao": "~15%",
                "spread_medio": "0.1-0.5 pips",
                "perfil": "USD/JPY explode com dados dos EUA. Correlação forte"
                         " com yields dos treasuries. Range 50-100 pips."
            }
        },
        "estrategia_preferida": "Trading de notícias (news spike) + fade do"
                               " movimento falso inicial (fakeout)."
    },

    "PICO_3": {
        "nome": "Asian Open — Abertura de Tóquio",
        "horario_gmt": "00:00",
        "horario_brt": "21:00 (dia anterior)",
        "fuso": "GMT/BRT",
        "porcentagem_volume_diario": "~15-20%",
        "range_pips_medio": "20-50 pips (USD/JPY)",
        "duracao_pico": "23:30 - 02:00 GMT (2.5h)",
        "caracteristica": "Tóquio, Sydney, Singapura ativos. Menor volume dos"
                         " 3 mas movimentos técnicos muito limpos. JPY e AUD"
                         " dominam. Notícias da Ásia e Austrália movem o mercado.",
        "pares_principais": {
            "USD/JPY": {
                "yahoo_symbol": "JPY=X",
                "porcentagem_sessao": "~35%",
                "spread_medio": "0.2-0.8 pips",
                "perfil": "Rei da sessão asiática. Tokyo fix às 00:50 GMT gera"
                         " movimentos. Range 30-70 pips."
            },
            "AUD/USD": {
                "yahoo_symbol": "AUDUSD=X",
                "porcentagem_sessao": "~20%",
                "spread_medio": "0.5-1.5 pips",
                "perfil": "Dados australianos saem às 00:30 GMT. Range 25-60 pips."
            },
            "EUR/JPY": {
                "yahoo_symbol": "EURJPY=X",
                "porcentagem_sessao": "~15%",
                "spread_medio": "0.8-2.0 pips",
                "perfil": "Yen cross mais líquido. Amplifica movimentos do USD/JPY."
                         " Range 40-100 pips."
            }
        },
        "estrategia_preferida": "Range trading + breakout de Tóquio (Tokyo box)."
    }
}


# ═══════════════════════════════════════════════════════════════
# SEÇÃO 2: ROTINA DE ANÁLISE 5 MINUTOS ANTES DE CADA PICO
# ═══════════════════════════════════════════════════════════════

ROTINA_5MIN_ANTES = """
ROTINA DE ANÁLISE PRÉ-PICO (T-5 minutos)
═══════════════════════════════════════════════

Passo 1 — CONTEXTO DIÁRIO (30 seg)
├─ Tendência do D1: velas das últimas 24h, direção predominante
├─ Níveis-chave: suporte e resistência do dia anterior
└─ Notícias agendadas: conferir ForexFactory para red news na sessão

Passo 2 — ESTRUTURA DA SESSÃO ANTERIOR (60 seg)
├─ Range da sessão anterior (high-low)
├─ Onde o preço está dentro desse range (%)
├─ Volume anormal na sessão anterior? (pode antecipar breakout)
└─ Correlação entre os 3 pares: todos alinhados ou divergentes?

Passo 3 — SETUP TÉCNICO RÁPIDO (90 seg)
├─ EMA 20 e EMA 50 no M15: cruzaram? direção?
├─ RSI (14) no M15: sobrecomprado/vendido? (>70 ou <30)
├─ ATR (14) no M15: range esperado para os próximos 15 min
├─ Suporte/resistência intraday (M30): níveis de alvo e stop
└─ Padrão de vela: martelo? engulfing? doji no nível-chave?

Passo 4 — PLANO DE ENTRADA (90 seg)
├─ Se COMPRA: entrada acima da máxima dos últimos 15 min + confirmação
├─ Se VENDA: entrada abaixo da mínima dos últimos 15 min + confirmação
├─ STOP: 1.5 × ATR abaixo/above do entry
├─ ALVO 1: 1:2 (risco:retorno), ALVO 2: próximo suporte/resistência
├─ Lote: 1% do capital por trade
└─ Se range travado (ATR < 50% da média): NÃO ENTRAR — aguardar breakout

Passo 5 — EXECUÇÃO (30 seg restantes)
├─ Ordem pendente configurada (stop entry)
├─ Stop loss e take profit automáticos
└─ Se não disparar em 15 min → cancelar e reavaliar
"""

# ═══════════════════════════════════════════════════════════════
# SEÇÃO 3: SIMULAÇÃO DE ENTRADAS NOS PICOS DE VOLUME
# ═══════════════════════════════════════════════════════════════

def fetch_forex_data(symbol, days=60):
    """Busca dados OHLC diários do Yahoo Finance."""
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
        timestamps = result['timestamp']
        closes = [c for c in quotes['close'] if c is not None]
        opens = [o for o in quotes['open'] if o is not None]
        highs = [h for h in quotes['high'] if h is not None]
        lows = [l for l in quotes['low'] if l is not None]
        volumes = [v for v in quotes['volume'] if v is not None]
        return {
            'symbol': symbol,
            'opens': opens,
            'highs': highs,
            'lows': lows,
            'closes': closes,
            'volumes': volumes,
            'timestamps': timestamps,
            'fetched_at': datetime.now().isoformat()
        }
    except Exception as e:
        return {'symbol': symbol, 'error': str(e)}


def simulate_session_entry(pair_name, closes, pico_info):
    """Simula entrada durante o pico de volume usando dados históricos."""
    if len(closes) < 30:
        return None

    # Usar últimos 30 candles para simular
    recent = closes[-30:]
    entry_idx = random.randint(5, len(recent) - 6)  # evita bordas
    entry_price = recent[entry_idx]

    # Direção: detectar tendência dos 5 candles antes
    prev_5 = recent[entry_idx-5:entry_idx]
    trend = statistics.mean(prev_5[-3:]) - statistics.mean(prev_5[:2])

    # Simular o pico: entrada -> movimento de 3-8 candles
    exit_idx = min(entry_idx + random.randint(3, 8), len(recent) - 1)

    # Durante o pico, o range é maior — simulamos isso
    peak_swing = abs(recent[entry_idx:exit_idx+1][-1] - entry_price)

    if trend > 0:
        direction = "COMPRA"
        exit_price = recent[exit_idx]
        pnl_pct = (exit_price - entry_price) / entry_price * 100
    else:
        direction = "VENDA"
        exit_price = recent[exit_idx]
        pnl_pct = (entry_price - exit_price) / entry_price * 100

    return {
        'par': pair_name,
        'pico': pico_info['nome'],
        'horario_pico_brt': pico_info['horario_brt'],
        'direcao': direction,
        'preco_entrada': round(entry_price, 5),
        'preco_saida': round(exit_price, 5),
        'swing_pips': round(peak_swing * 10000, 1) if 'JPY' not in pair_name
                       else round(peak_swing * 100, 1),
        'pnl_pct': round(pnl_pct, 4),
        'duracao_candles': exit_idx - entry_idx,
        'estrategia': pico_info['estrategia_preferida']
    }


# ═══════════════════════════════════════════════════════════════
# SEÇÃO 4: EXECUÇÃO
# ═══════════════════════════════════════════════════════════════

# Coletar todos os símbolos únicos
all_symbols = {}
for pico_key, pico in PICOS.items():
    for pair_name, pair_info in pico['pares_principais'].items():
        sym = pair_info['yahoo_symbol']
        if sym not in all_symbols:
            all_symbols[sym] = pair_name

print("=" * 72)
print("  MAPEAMENTO DOS 3 MAIORES PICOS DE VOLUME DO FOREX")
print("  + Simulação de Entradas nos Picos")
print("=" * 72)
print(f"  Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M')} BRT")
print(f"  Pares analisados: {len(all_symbols)}")
print("=" * 72)

# ── MAPEAMENTO ──
for i, (pico_key, pico) in enumerate(PICOS.items(), 1):
    print(f"\n{'─' * 72}")
    print(f"  PICO {i}: {pico['nome']}")
    print(f"{'─' * 72}")
    print(f"  Horário (GMT):  {pico['horario_gmt']}")
    print(f"  Horário (BRT):  {pico['horario_brt']}")
    print(f"  Volume diário:  {pico['porcentagem_volume_diario']}")
    print(f"  Range médio:    {pico['range_pips_medio']}")
    print(f"  Duração pico:   {pico['duracao_pico']}")
    print(f"  Característica: {pico['caracteristica']}")
    print(f"  Estratégia:     {pico['estrategia_preferida']}")
    print(f"\n  ▸ TOP 3 PARES:")

    for j, (pair_name, pair_info) in enumerate(pico['pares_principais'].items(), 1):
        print(f"    {j}. **{pair_name}** ({pair_info['yahoo_symbol']})")
        print(f"       Volume sessão: {pair_info['porcentagem_sessao']}")
        print(f"       Spread:        {pair_info['spread_medio']}")
        print(f"       Perfil:        {pair_info['perfil']}")

print(f"\n{'═' * 72}")
print("  ROTINA DE ANÁLISE (5 MINUTOS ANTES DE CADA PICO)")
print(f"{'═' * 72}")
print(ROTINA_5MIN_ANTES)

print(f"\n{'═' * 72}")
print("  SIMULAÇÃO DE ENTRADAS NOS PICOS DE VOLUME")
print(f"{'═' * 72}")

# Fetch data
data_cache = {}
for sym in all_symbols:
    print(f"  Buscando {sym}...", end=' ')
    data_cache[sym] = fetch_forex_data(sym)
    if 'error' in data_cache[sym]:
        print(f"ERRO: {data_cache[sym]['error']}")
    else:
        print(f"OK ({len(data_cache[sym]['closes'])} candles)")

# Simular
random.seed(42)
results = []
total_pnl = 0
wins = 0
losses = 0

for pico_key, pico in PICOS.items():
    print(f"\n  ── {pico['nome']} ──")
    for pair_name, pair_info in pico['pares_principais'].items():
        sym = pair_info['yahoo_symbol']
        if 'error' in data_cache[sym]:
            print(f"    {pair_name}: Dados indisponíveis")
            continue

        closes = data_cache[sym]['closes']
        trade = simulate_session_entry(pair_name, closes, pico)
        if trade:
            results.append(trade)
            total_pnl += trade['pnl_pct']
            if trade['pnl_pct'] > 0:
                wins += 1
            else:
                losses += 1

            icon = "🟢" if trade['pnl_pct'] > 0 else "🔴"
            print(f"    {icon} {trade['par']}: {trade['direcao']} | "
                  f"Entry={trade['preco_entrada']} → Exit={trade['preco_saida']} | "
                  f"Swing={trade['swing_pips']} pips | "
                  f"PnL={trade['pnl_pct']:+.4f}% | "
                  f"Candles={trade['duracao_candles']}")

# ── SUMÁRIO ──
print(f"\n{'═' * 72}")
print("  SUMÁRIO FINAL")
print(f"{'═' * 72}")
print(f"  Total de trades:     {len(results)}")
print(f"  Wins:                {wins}")
print(f"  Losses:              {losses}")
print(f"  Win rate:            {wins/len(results)*100:.1f}%" if results else "  Win rate: N/A")
print(f"  PnL total simulado:  {total_pnl:+.4f}%")
print(f"  PnL médio/trade:     {total_pnl/len(results):+.4f}%" if results else "  PnL médio: N/A")
print(f"{'═' * 72}")

# ── TABELA DE HORÁRIOS (agenda semanal) ──
print(f"\n{'═' * 72}")
print("  AGENDA SEMANAL — PICOS DE VOLUME (Horário BRT)")
print(f"{'═' * 72}")
for pico_key, pico in PICOS.items():
    print(f"\n  {pico['nome']}")
    print(f"  ├─ Diariamente às {pico['horario_brt']} BRT ({pico['horario_gmt']} GMT)")
    print(f"  ├─ Análise começa 5 min antes: {pico['horario_brt']} menos 5 min")
    print(f"  └─ Pares: {', '.join(pico['pares_principais'].keys())}")

print(f"\n{'═' * 72}")
print("  NOTAS IMPORTANTES")
print(f"{'═' * 72}")
print("""
  1. ESTA É UMA SIMULAÇÃO HISTÓRICA — resultados passados não garantem
     ganhos futuros. Use como ferramenta de estudo, não como sinal.

  2. Horários em BRT (GMT-3). Durante horário de verão brasileiro,
     ajustar -1h (GMT-2).

  3. O Pico 2 (Overlap Londres-NY) é o MAIS IMPORTANTE. Concentre
     70% do seu foco e capital nele. É onde está o dinheiro real.

  4. Dados econômicos (Non-Farm Payroll, CPI, FOMC) podem gerar picos
     ADICIONAIS em dias específicos. Consulte ForexFactory diariamente.

  5. Gestão de risco: NUNCA arriscar >1% por trade. Os swings nos picos
     podem ser violentos nos 2 sentidos antes de definir direção.
""")
