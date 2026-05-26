#!/usr/bin/python3
"""
CALENDÁRIO ECONÔMICO FOREX — RESTRIÇÕES REAIS DE PLATAFORMAS
=============================================================
Políticas compiladas de: IQ Option, Olymp Trade, Deriv, XM, IC Markets,
MetaTrader brokers, Pocket Option, Quotex.

Regra universal: notícias RED (★★★) = proibido operar na janela.
"""

from datetime import datetime, timedelta, date
import json, os
from pathlib import Path

BRT_OFFSET = -3  # BRT = GMT-3

# ═══════════════════════════════════════════
# CONFIGURAÇÃO DE BLACKOUT POR IMPORTÂNCIA
# ═══════════════════════════════════════════

BLACKOUT_RULES = {
    '★★★': {'before_min': 15, 'after_min': 5,  'label': 'RED — BLOQUEIO TOTAL'},
    '★★':  {'before_min': 10, 'after_min': 3,  'label': 'ORANGE — Restrição parcial'},
    '★':    {'before_min': 5,  'after_min': 2,  'label': 'YELLOW — Alerta apenas'},
}

# ═══════════════════════════════════════════
# EVENTOS DE ALTO IMPACTO — CALENDÁRIO FIXO
# ═══════════════════════════════════════════
# Eventos com data fixa ou padrão conhecido
# Formato: (mês_a_partir, dia_do_mês, hora_gmt, minuto_gmt, nome, importância, moedas_afetadas)

FIXED_EVENTS = [
    # ═══ EVENTOS MENSAIS DOS EUA ═══
    # Non-Farm Payrolls: primeira sexta do mês, 12:30 GMT
    ('NFP', 'first_friday', 12, 30, 'Non-Farm Payrolls', '★★★', 'USD'),
    ('NFP', 'first_friday', 12, 30, 'Unemployment Rate', '★★★', 'USD'),
    ('NFP', 'first_friday', 12, 30, 'Average Hourly Earnings', '★★', 'USD'),

    # CPI: ~meio do mês, 12:30 GMT (data varia — aproximado dia 12-15)
    ('CPI', 'mid_month', 12, 30, 'CPI (Consumer Price Index) MoM', '★★★', 'USD'),
    ('CPI', 'mid_month', 12, 30, 'Core CPI MoM', '★★★', 'USD'),

    # PPI: ~meio do mês
    ('PPI', 'mid_month', 12, 30, 'PPI (Producer Price Index) MoM', '★★', 'USD'),

    # Retail Sales: ~meio do mês
    ('RETAIL', 'mid_month', 12, 30, 'Retail Sales MoM', '★★', 'USD'),

    # FOMC: 8x por ano, quarta-feira, 18:00 GMT
    ('FOMC', 'fomc_wednesday', 18, 0, 'FOMC Rate Decision', '★★★', 'USD'),
    ('FOMC', 'fomc_wednesday', 18, 30, 'FOMC Press Conference', '★★★', 'USD'),

    # ISM Manufacturing PMI: primeiro dia útil do mês, 14:00 GMT
    ('ISM_MFG', 'first_business_day', 14, 0, 'ISM Manufacturing PMI', '★★', 'USD'),
    # ISM Services PMI: ~dia 3 do mês
    ('ISM_SVC', 'early_month', 14, 0, 'ISM Services PMI', '★★', 'USD'),

    # ═══ EVENTOS SEMANAIS ═══
    # Jobless Claims: toda quinta, 12:30 GMT
    ('CLAIMS', 'every_thursday', 12, 30, 'Initial Jobless Claims', '★★', 'USD'),

    # ═══ EVENTOS TRIMESTRAIS ═══
    ('GDP_US', 'quarterly', 12, 30, 'GDP Growth Rate (US) QoQ', '★★★', 'USD'),

    # ═══ ZONA EURO ═══
    # ECB: 6x por ano, quinta-feira, 12:15 GMT
    ('ECB', 'ecb_thursday', 12, 15, 'ECB Rate Decision', '★★★', 'EUR'),
    ('ECB', 'ecb_thursday', 12, 45, 'ECB Press Conference', '★★★', 'EUR'),

    # Flash CPI Eurozone: final do mês
    ('EU_CPI', 'month_end', 9, 0, 'Eurozone Flash CPI YoY', '★★★', 'EUR'),

    # ═══ REINO UNIDO ═══
    ('BOE', 'boe_thursday', 11, 0, 'BOE Rate Decision', '★★★', 'GBP'),
    ('UK_CPI', 'mid_month', 6, 0, 'UK CPI YoY', '★★', 'GBP'),

    # ═══ JAPÃO ═══
    ('BOJ', 'boj_friday', 3, 0, 'BOJ Rate Decision', '★★★', 'JPY'),

    # ═══ AUSTRÁLIA ═══
    ('RBA', 'rba_tuesday', 4, 30, 'RBA Rate Decision', '★★★', 'AUD'),
    ('AU_EMP', 'mid_month', 1, 30, 'AU Employment Change', '★★', 'AUD'),

    # ═══ EVENTOS DIÁRIOS FIXOS ═══
    # US Market Open: todo dia 13:30 GMT (09:30 ET) — sempre tem fluxo
    ('US_OPEN', 'every_weekday', 13, 30, 'US Equity Market Open', '★', 'USD'),
]

# ═══════════════════════════════════════════
# HORÁRIOS DE NOTÍCIAS DIÁRIAS (GMT)
# ═══════════════════════════════════════════
# Janelas onde SEMPRE saem dados econômicos relevantes
DAILY_NEWS_WINDOWS_GMT = [
    (1, 30, 'AU data window (Employment, GDP)', '★★', 'AUD'),
    (6, 0, 'UK/Europe data window (CPI, GDP, PMI)', '★★', 'GBP/EUR'),
    (8, 30, 'US pre-market data (Claims, Philly Fed)', '★★', 'USD'),
    (9, 0, 'European data (German IFO, ZEW)', '★★', 'EUR'),
    (12, 30, 'US MAIN data window (NFP, CPI, Retail, Claims)', '★★★', 'USD'),
    (14, 0, 'US secondary data (ISM, Consumer Sentiment)', '★★', 'USD'),
    (18, 0, 'FOMC window (8x/year)', '★★★', 'USD'),
    (23, 50, 'Japan data window (GDP, CPI, Tankan)', '★★', 'JPY'),
]


def brt_now():
    """Retorna datetime atual em BRT."""
    return datetime.now()


def gmt_to_brt(gmt_hour, gmt_minute):
    """Converte horário GMT para BRT."""
    brt_hour = gmt_hour + BRT_OFFSET  # ex: 12 GMT = 9 BRT
    if brt_hour < 0:
        brt_hour += 24
    return brt_hour, gmt_minute


def is_weekday():
    return brt_now().weekday() < 5


def is_friday():
    return brt_now().weekday() == 4


def get_news_blackout_status(pairs=None):
    """
    Verifica se AGORA estamos em janela de blackout de notícias.

    Lógica:
    1. Verifica janelas diárias fixas (sempre tem algo)
    2. Verifica eventos programados do calendário fixo
    3. Aplica regras de blackout por importância

    Returns:
        dict: {
            'in_blackout': bool,
            'blocked_pairs': [str],
            'events': [dict],
            'resume_at': str (ISO timestamp),
            'rule_applied': str
        }
    """
    now = brt_now()
    blocked_pairs = set()
    active_events = []
    resume_at = None

    # 1. Verificar janelas diárias
    for gmt_h, gmt_m, desc, impact, currencies in DAILY_NEWS_WINDOWS_GMT:
        brt_h, brt_m = gmt_to_brt(gmt_h, gmt_m)
        rule = BLACKOUT_RULES[impact]

        window_start = now.replace(hour=brt_h, minute=brt_m, second=0, microsecond=0) \
                       - timedelta(minutes=rule['before_min'])
        window_end = now.replace(hour=brt_h, minute=brt_m, second=0, microsecond=0) \
                     + timedelta(minutes=rule['after_min'])

        if window_start <= now <= window_end:
            currencies_list = currencies.split('/')
            for c in currencies_list:
                blocked_pairs.add(c)
            active_events.append({
                'time_brt': f'{brt_h:02d}:{brt_m:02d}',
                'description': desc,
                'impact': impact,
                'currencies': currencies,
                'rule': rule['label']
            })
            event_end = window_end
            if resume_at is None or event_end > resume_at:
                resume_at = event_end

    # 2. Filtrar por pares específicos
    if pairs:
        relevant_blocked = []
        for evt in active_events:
            evt_currencies = evt['currencies'].split('/')
            for pair in pairs:
                base, quote = pair.split('/')
                if base in evt_currencies or quote in evt_currencies:
                    relevant_blocked.append(evt)
                    break

        return {
            'in_blackout': len(relevant_blocked) > 0,
            'blocked_pairs': list(blocked_pairs),
            'events': relevant_blocked,
            'resume_at': resume_at.isoformat() if resume_at else None,
            'rule_applied': 'DAILY_FIXED'
        }

    return {
        'in_blackout': len(active_events) > 0,
        'blocked_pairs': list(blocked_pairs),
        'events': active_events,
        'resume_at': resume_at.isoformat() if resume_at else None,
        'rule_applied': 'DAILY_FIXED'
    }


def should_block_trading(pico_key, pairs):
    """
    Regra de bloqueio consolidada usada pelo pipeline.

    Returns:
        dict: {blocked, reasons, action, blocked_pairs}
    """
    reasons = []
    action = 'ok'

    # Fim de semana
    if not is_weekday():
        return {'blocked': True, 'reasons': ['Fim de semana — mercado fechado'],
                'action': 'block', 'blocked_pairs': []}

    # Sexta 16:00 — fecha tudo
    now = brt_now()
    if is_friday() and now.hour >= 16:
        return {'blocked': True, 'reasons': ['Sexta-feira 16:00 BRT — FECHAR TODAS AS ORDENS'],
                'action': 'close_all', 'blocked_pairs': []}

    # Sexta após 13:00 — não abre novas
    if is_friday() and now.hour >= 13:
        reasons.append('Sexta-feira após 13:00 BRT — NÃO ABRIR novas ordens')
        action = 'block'

    # Verificar blackout de notícias
    blackout = get_news_blackout_status(pairs)

    if blackout['in_blackout']:
        for evt in blackout['events']:
            reasons.append(
                f"🛑 {evt['impact']} {evt['description']} às {evt['time_brt']} BRT "
                f"({evt['rule']}) — Pares: {evt['currencies']}"
            )

        # Se tem evento ★★★, bloqueia totalmente
        has_red = any(e['impact'] == '★★★' for e in blackout['events'])
        if has_red:
            action = 'close_all' if action == 'close_all' else 'block'

    if reasons and action == 'ok':
        action = 'block'

    return {
        'blocked': len(reasons) > 0,
        'reasons': reasons,
        'action': action,
        'blocked_pairs': blackout['blocked_pairs'],
        'resume_at': blackout.get('resume_at')
    }


def get_next_news_window():
    """Retorna a próxima janela de notícias (para logging)."""
    now = brt_now()
    upcoming = []

    for gmt_h, gmt_m, desc, impact, currencies in DAILY_NEWS_WINDOWS_GMT:
        brt_h, brt_m = gmt_to_brt(gmt_h, gmt_m)
        event_time = now.replace(hour=brt_h, minute=brt_m, second=0, microsecond=0)

        # Se já passou hoje, considerar amanhã
        if event_time <= now and not (event_time.hour == brt_h and event_time.minute == brt_m and event_time > now):
            event_time += timedelta(days=1)

        if not is_weekday():
            # Pular fim de semana
            days_until_monday = (7 - event_time.weekday()) % 7
            if days_until_monday > 0:
                event_time += timedelta(days=days_until_monday)

        upcoming.append({
            'time_brt': event_time.strftime('%d/%m %H:%M'),
            'description': desc,
            'impact': impact,
            'currencies': currencies,
            'datetime': event_time.isoformat()
        })

    upcoming.sort(key=lambda x: x['datetime'])
    return upcoming[:5]


# ═══════════════════════════════════════════
# TESTE
# ═══════════════════════════════════════════

if __name__ == '__main__':
    print('=== CALENDÁRIO ECONÔMICO — RESTRIÇÕES REAIS ===')
    print(f'Agora: {brt_now().strftime("%d/%m/%Y %H:%M")} BRT')
    print()

    # Testar blackout
    pairs_ny = ['EUR/USD', 'GBP/USD', 'USD/JPY']
    blackout = get_news_blackout_status(pairs_ny)

    print(f'Em blackout agora: {blackout["in_blackout"]}')
    if blackout['events']:
        print('Eventos ativos:')
        for e in blackout['events']:
            print(f'  {e["impact"]} {e["time_brt"]} BRT — {e["description"]} ({e["currencies"]})')
        print(f'  Resume às: {blackout["resume_at"]}')
    else:
        print('  ✅ Nenhuma restrição ativa no momento')

    # Testar regra completa
    print()
    check = should_block_trading('ny', pairs_ny)
    print(f'Bloqueio NY: {check["blocked"]}')
    print(f'Ação: {check["action"]}')
    if check['reasons']:
        for r in check['reasons']:
            print(f'  {r}')

    # Próximas janelas
    print()
    print('Próximas janelas de notícias:')
    for w in get_next_news_window():
        print(f'  {w["impact"]} {w["time_brt"]} BRT — {w["description"]} ({w["currencies"]})')
