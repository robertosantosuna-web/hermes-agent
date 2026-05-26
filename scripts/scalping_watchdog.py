#!/usr/bin/python3
"""
╔══════════════════════════════════════════════════════════════╗
║  SCALPING WATCHDOG — Execução Local Zero Tokens            ║
║  Roda a cada 5 min via cron (no_agent=true).               ║
║  Só emite saída quando há SINAIS ACIONÁVEIS.               ║
║  Silencioso = sem sinais = sem entrega = zero custo.       ║
╚══════════════════════════════════════════════════════════════╝

Arquitetura de economia de tokens:
  ┌──────────┐     ┌──────────────┐     ┌──────────┐
  │ CRON     │────▶│ WATCHDOG.PY  │────▶│ ENTREGA  │
  │ cada 5m  │     │ (todo local) │     │ (se tiver│
  │ $0 tokens│     │ $0 tokens    │     │ sinais)  │
  └──────────┘     └──────────────┘     └──────────┘

Regras aplicadas localmente:
  - Fim de semana → sai silencioso
  - Fora das 3 sessões → sai silencioso  
  - Blackout (notícias) → sai com alerta de bloqueio
  - Sexta após 13:00 BRT → sai silencioso
  - Sem sinais → sai silencioso
  - Com sinais → saída compacta direto pro Telegram
"""

import sys
import os
from datetime import datetime, date, timedelta
from pathlib import Path

# Adicionar módulos forex ao path
FOREX_DIR = Path.home() / '.hermes' / 'forex'
sys.path.insert(0, str(FOREX_DIR))

try:
    from scalping_m5 import fetch_intraday, analyze_m5, PAIRS as ALL_PAIRS
    from forex_calendar import should_block_trading, is_weekday, is_friday, BLACKOUT_RULES
except ImportError as e:
    print(f"❌ Erro import: {e}")
    sys.exit(1)

# ═══════════════════════════════════════════
# CONFIGURAÇÃO DAS SESSÕES (BRT = GMT-3)
# ═══════════════════════════════════════════

SESSIONS = {
    '🇬🇧 London': {
        'start': 5,   # 05:00 BRT
        'end': 12,    # 12:00 BRT  
        'pairs': ['EUR/USD', 'GBP/USD', 'EUR/GBP'],
        'pico': 5,    # 05:00
        'analise_t5': 55,  # 04:55 (minuto)
        'analise_hora': 4,
    },
    '🇺🇸⭐ NY Overlap': {
        'start': 10,  # 10:00 BRT
        'end': 17,    # 17:00 BRT
        'pairs': ['EUR/USD', 'GBP/USD', 'USD/JPY'],
        'pico': 10,
        'analise_t5': 55,
        'analise_hora': 9,
    },
    '🇯🇵 Asia': {
        'start': 21,  # 21:00 BRT
        'end': 29,    # 05:00 BRT (representado como 29 para comparação)
        'pairs': ['USD/JPY', 'AUD/USD', 'EUR/JPY'],
        'pico': 21,
        'analise_t5': 55,
        'analise_hora': 20,
    },
}

MIN_SCORE = 2.0  # Só reporta sinais com score >= este valor (absoluto)
CAPITAL = 1000.0
RISCO_PCT = 1.0
RR = 3.0

# ═══════════════════════════════════════════
# LÓGICA DE TEMPO
# ═══════════════════════════════════════════

def get_active_hour() -> int:
    """Retorna hora atual BRT como float (ex: 21.5 = 21:30)."""
    now = datetime.now()
    return now.hour + now.minute / 60.0

def is_session_active(session: dict, now_hour: float) -> bool:
    """Verifica se a sessão está ativa agora."""
    start, end = session['start'], session['end']
    if end > 24:
        # Sessão que cruza meia-noite (Asia: 21:00-05:00)
        return now_hour >= start or now_hour < (end - 24)
    return start <= now_hour < end

def is_t5_analysis(session: dict) -> bool:
    """Estamos no minuto exato da análise T-5?"""
    now = datetime.now()
    return (now.hour == session['analise_hora'] and 
            now.minute == session['analise_t5'])

def is_valid_trading_time() -> tuple[bool, str]:
    """Verifica se é horário válido para trading."""
    now = datetime.now()
    wd = now.weekday()  # 0=Seg, ..., 4=Sex, 5=Sáb, 6=Dom
    hora = now.hour + now.minute / 60.0
    
    # Sábado: sempre bloqueado
    if wd == 5:
        return False, "Sábado — mercado fechado"
    
    # Domingo antes das 17:00 BRT: bloqueado
    if wd == 6 and hora < 17.0:
        return False, "Domingo — mercado abre 17:00 BRT"
    
    # Sexta após 13:00: sem novas ordens
    if wd == 4 and hora >= 13.0:
        return False, "Sexta após 13:00 — sem novas ordens"
    
    # Blackout por notícias
    try:
        blocked, reason = should_block_trading()
        if blocked:
            return False, f"BLACKOUT: {reason}"
    except Exception:
        pass  # Se calendário falhar, continua
    
    return True, "OK"

def get_active_sessions() -> list:
    """Retorna lista de sessões ativas agora."""
    now_hour = get_active_hour()
    active = []
    for name, session in SESSIONS.items():
        if is_session_active(session, now_hour):
            active.append((name, session))
    return active

# ═══════════════════════════════════════════
# ANÁLISE
# ═══════════════════════════════════════════

def analyze_session(name: str, session: dict, is_pre_pico: bool) -> list:
    """Analisa todos os pares de uma sessão. Retorna lista de sinais."""
    signals = []
    
    for pair in session['pairs']:
        symbol = ALL_PAIRS.get(pair)
        if not symbol:
            continue
        
        data = fetch_intraday(symbol, '5m', hours=6)
        result = analyze_m5(pair, data)
        
        if result is None:
            continue
        
        # Só reporta se tiver direção definida
        if result['direction'] == 'NEUTRO':
            continue
        
        # Só reporta scores significativos
        if abs(result['score']) < MIN_SCORE:
            continue
        
        signals.append(result)
    
    # Ordenar por score (mais forte primeiro)
    signals.sort(key=lambda s: abs(s['score']), reverse=True)
    return signals

def format_signal(s: dict) -> str:
    """Formata um sinal para saída compacta."""
    dir_icon = '🟢' if s['direction'] == 'COMPRA' else '🔴'
    strength = s['strength']
    
    lines = [
        f"{dir_icon} **{s['pair']}** {s['direction']} ({strength}) | Score: {s['score']}",
        f"  Preço: {s['price']} | RSI: {s['indicators']['rsi9']} | Mom: {s['indicators']['momentum_pips']}p",
    ]
    
    if s.get('breakout'):
        lines.append(f"  ⚡ {s['breakout']}")
    
    if s['trade']['stop']:
        lines.append(
            f"  🎯 Stop: {s['trade']['stop_pips']}p | Target: {s['trade']['target_pips']}p | "
            f"RR 1:{RR:.0f}"
        )
        risco_valor = CAPITAL * RISCO_PCT / 100
        ganho_valor = risco_valor * RR
        lines.append(f"  💰 Risco: R${risco_valor:.0f} → Alvo: R${ganho_valor:.0f}")
    
    return '\n'.join(lines)

# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

def main():
    now = datetime.now()
    
    # 1. Validar horário
    valid, reason = is_valid_trading_time()
    if not valid:
        # Só reporta blackout; resto é silencioso
        if 'BLACKOUT' in reason:
            print(f"⛔ {reason}")
        return 0
    
    # 2. Identificar sessões ativas
    active = get_active_sessions()
    if not active:
        return 0  # Fora de todas as sessões → silencioso
    
    # 3. Analisar cada sessão ativa
    all_signals = []
    pre_pico_info = []
    
    for name, session in active:
        is_pre = is_t5_analysis(session)
        signals = analyze_session(name, session, is_pre)
        
        if is_pre:
            pre_pico_info.append(name)
        
        if signals:
            all_signals.append((name, session, signals, is_pre))
    
    # 4. Se não tem sinal nenhum, sai silencioso
    if not all_signals:
        return 0
    
    # 5. Formatar saída
    print(f"┌{'─'*40}┐")
    print(f"│ ⚡ SCALPING M5 — {now.strftime('%d/%m %H:%M')} BRT")
    
    if pre_pico_info:
        print(f"│ ⏰ PRÉ-PICO: {', '.join(pre_pico_info)}")
    
    total_buy = total_sell = 0
    
    for sess_name, session, signals, is_pre in all_signals:
        print(f"├{'─'*40}┤")
        print(f"│ {sess_name}")
        
        for s in signals:
            formatted = format_signal(s)
            for line in formatted.split('\n'):
                print(f"│ {line}")
            print(f"│")
            
            if s['direction'] == 'COMPRA':
                total_buy += 1
            else:
                total_sell += 1
    
    print(f"├{'─'*40}┤")
    print(f"│ 📊 {total_buy}🟢 COMPRA | {total_sell}🔴 VENDA")
    print(f"└{'─'*40}┘")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
