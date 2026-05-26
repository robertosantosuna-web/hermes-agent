#!/usr/bin/python3
"""
╔══════════════════════════════════════════════════════════════╗
║  MOTOR CENTRAL — Coleta Unificada (Zero Tokens)            ║
║                                                            ║
║  Roda via cron (no_agent=true, deliver=local)              ║
║  Coleta TUDO que o motor local consegue processar:         ║
║    📧 Plataformas de renda (99Freelas, Fiverr, Workana)   ║
║    ⚡ Sinais de trade M5 (Forex)                           ║
║                                                            ║
║  Output: JSON estruturado → consumido pelo Escalation      ║
║  Agent (único ponto de consumo de tokens LLM)             ║
╚══════════════════════════════════════════════════════════════╝

Arquitetura:
  motor_central.py (no_agent, local) → JSON file
       ↓ context_from
  escalation agent (LLM, 15min) → Telegram (só quando relevante)

Flags de escalação (só estes acionam o LLM):
  🔴 CLIENT_MSG    — Mensagem nova de cliente
  🔴 PAYMENT       — Pagamento recebido ou problema
  🟡 NEW_PROJECT   — Novo projeto nas plataformas
  🟡 SIGNAL_STRONG — Sinal de trade |score| >= 3.5
  🟢 SIGNAL        — Sinal de trade |score| >= 2.0
  ⚪ BLACKOUT      — Bloqueio por notícias ativo
"""

import sys, os, json, re, statistics
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

HOME = Path.home()
FOREX_DIR = HOME / '.hermes' / 'forex'
sys.path.insert(0, str(FOREX_DIR))

# ═══════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════

IMAP_HOST = 'imap.gmail.com'
IMAP_PORT = 993
EMAIL = 'robertosantos.una@gmail.com'
APP_PASSWORD = 'exnlrvfswckioces'

INCOME_PLATFORMS = {
    '99freelas': {
        'search_terms': ['99freelas', '99freela'],
        'project_pattern': r'Novo Projeto:\s*(.+)',
        'message_pattern': r'Nova mensagem de\s*(.+?)\s*no projeto\s*(.+)',
        'payment_pattern': r'(?:pagamento|Pagamento|recebido|Recebido)',
        'priority': 'HIGH',
    },
    'fiverr': {
        'search_terms': ['fiverr'],
        'project_pattern': r'New brief:\s*(.+)',
        'message_pattern': r'New message from\s*(.+)',
        'payment_pattern': r'(?:order|Order|payment|Payment)',
        'priority': 'MEDIUM',
    },
    'workana': {
        'search_terms': ['workana'],
        'project_pattern': r'Novo projeto:\s*(.+)',
        'message_pattern': r'Mensagem de\s*(.+)',
        'payment_pattern': r'(?:pagamento|Pagamento)',
        'priority': 'MEDIUM',
    },
    'freelancer': {
        'search_terms': ['freelancer.com', 'freelancer'],
        'project_pattern': r'New project:\s*(.+)',
        'message_pattern': r'New message from\s*(.+)',
        'payment_pattern': r'(?:payment|Payment|milestone)',
        'priority': 'LOW',
    },
}

# ═══════════════════════════════════════════
# KILLZONES — Momentos de Pico (ICT)
# ═══════════════════════════════════════════
# Apenas 30 min por killzone. Fora disso = silencioso.
KILLZONES = {
    '🇬🇧 London Open': {
        'start_h': 4,  'start_m': 0,   # 04:00 BRT
        'end_h':   4,  'end_m':   30,  # 04:30 BRT
        'pairs': ['EUR/USD', 'GBP/USD', 'EUR/GBP'],
        'range_session': 'Asia',       # Range da Ásia (01:00-04:00) para sweep
        'sweep_direction': 'both',     # Pode romper pra cima ou pra baixo
        't2_analysis': (3, 58),       # 03:58 BRT
    },
    '🇺🇸⭐ NY Open': {
        'start_h': 9,  'start_m': 30,  # 09:30 BRT
        'end_h':   10, 'end_m':   0,   # 10:00 BRT
        'pairs': ['EUR/USD', 'GBP/USD', 'USD/JPY'],
        'range_session': 'London',     # Range de Londres (04:00-09:30) para sweep
        'sweep_direction': 'both',
        't2_analysis': (9, 28),       # 09:28 BRT
    },
    '🇬🇧🇺🇸 London Close': {
        'start_h': 12, 'start_m': 0,   # 12:00 BRT
        'end_h':   12, 'end_m':   30,  # 12:30 BRT
        'pairs': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'EUR/JPY'],
        'range_session': 'Daily',      # Range do dia inteiro
        'sweep_direction': 'both',
        't2_analysis': (11, 58),      # 11:58 BRT
    },
}

# Pares para blackout de notícias
ALL_PAIRS = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'EUR/GBP', 'EUR/JPY']

# CRT (Candle Range Theory) — parâmetros
CRT_MIN_RANGE_PIPS = 3      # Range mínimo da vela de sweep (pips)
CRT_STOP_MULT = 0.5         # Stop = 50% do range da vela de sweep
CRT_TARGET_MULT = 1.5       # Target = 150% do range
CRT_MIN_MOMENTUM = 2        # Momentum mínimo (pips) para confirmar sweep
MAX_LEVERAGE = 30           # Alavancagem máxima nos killzones

# ═══════════════════════════════════════════
# SEÇÃO 1: COLETA DE EMAIL (RENDA)
# ═══════════════════════════════════════════

def check_emails() -> dict:
    """Verifica emails de plataformas de renda. Retorna flags e stats."""
    import imaplib, email as em
    
    result = {
        'checked': False,
        'error': None,
        'emails_scanned': 0,
        'new_since': None,
        'flags': [],
    }
    
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(EMAIL, APP_PASSWORD)
        mail.select('INBOX')
        
        # Buscar emails das últimas 24h
        since = (datetime.now() - timedelta(hours=24)).strftime('%d-%b-%Y')
        result['new_since'] = since
        
        all_flags = []
        total_scanned = 0
        
        for platform, config in INCOME_PLATFORMS.items():
            search_query = ' OR '.join(f'FROM "{term}"' for term in config['search_terms'])
            
            try:
                status, ids = mail.search(None, f'({search_query} SINCE "{since}")')
                if not ids[0]:
                    continue
                
                id_list = ids[0].split()
                total_scanned += len(id_list)
                
                # Processar últimos 20 emails
                for num in id_list[-20:]:
                    status, data = mail.fetch(num, '(RFC822)')
                    msg = em.message_from_bytes(data[0][1])
                    
                    # Decode subject
                    subject_raw = msg['subject'] or ''
                    parts = em.header.decode_header(subject_raw)
                    subject = ''.join(
                        part.decode(charset or 'utf-8', errors='ignore') 
                        if isinstance(part, bytes) else part 
                        for part, charset in parts
                    )
                    
                    # Extrair corpo
                    body = ''
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == 'text/plain':
                                body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                break
                    if not body:
                        for part in msg.walk():
                            if part.get_content_type() == 'text/html':
                                html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                # Strip CSS and HTML tags
                                html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
                                html = re.sub(r'<head[^>]*>.*?</head>', '', html, flags=re.DOTALL)
                                body = re.sub(r'<[^>]+>', ' ', html)
                                body = re.sub(r'\s+', ' ', body).strip()
                                break
                    
                    # Detectar tipo de email
                    flag = None
                    
                    # Mensagem de cliente
                    match = re.search(config['message_pattern'], subject, re.IGNORECASE)
                    if match:
                        sender = match.group(1).strip()
                        projeto = match.group(2).strip() if match.lastindex >= 2 else ''
                        flag = {
                            'type': 'CLIENT_MSG',
                            'platform': platform,
                            'from': sender,
                            'project': projeto[:80],
                            'preview': body[:200].strip(),
                            'priority': 'HIGH',
                        }
                    
                    # Novo projeto
                    if not flag:
                        match = re.search(config['project_pattern'], subject, re.IGNORECASE)
                        if match and 'mensagem' not in subject.lower():
                            projeto = match.group(1).strip()
                            
                            # Extrair orçamento do corpo
                            budget = 'Aberto'
                            bm = re.search(r'Orçamento:\s*(.+)', body)
                            if bm:
                                budget = bm.group(1).strip()[:30]
                            
                            # Extrair categoria
                            category = ''
                            cm = re.search(r'^(?:Categoria[s]?|Área):\s*(.+)', body, re.MULTILINE)
                            if not cm:
                                # Pega a primeira linha não-vazia depois do título
                                lines = [l.strip() for l in body.split('\n') if l.strip() and len(l.strip()) > 3]
                                if len(lines) >= 2:
                                    cat_candidates = [l for l in lines[1:4] 
                                                     if not l.startswith(('Olá','Orçamento','*','Preciso','http'))]
                                    if cat_candidates:
                                        category = cat_candidates[0][:50]
                            
                            flag = {
                                'type': 'NEW_PROJECT',
                                'platform': platform,
                                'title': projeto[:80],
                                'budget': budget,
                                'category': category[:50] if category else '',
                                'priority': 'MEDIUM',
                            }
                    
                    # Pagamento
                    if not flag:
                        if re.search(config['payment_pattern'], subject, re.IGNORECASE):
                            flag = {
                                'type': 'PAYMENT',
                                'platform': platform,
                                'subject': subject[:100],
                                'priority': 'HIGH',
                            }
                    
                    if flag:
                        all_flags.append(flag)
                        
            except Exception as e:
                continue
        
        mail.close()
        mail.logout()
        
        result['checked'] = True
        result['emails_scanned'] = total_scanned
        result['flags'] = all_flags
        
    except Exception as e:
        result['error'] = str(e)[:100]
    
    return result


# ═══════════════════════════════════════════
# SEÇÃO 2: COLETA DE TRADE (FOREX M1/M5 — KILLZONES + CRT)
# ═══════════════════════════════════════════

def check_forex() -> dict:
    """Analisa killzones ICT com CRT. Só nos 30 min de pico."""
    from scalping_m5 import fetch_intraday, analyze_m5, PAIRS
    
    result = {
        'checked': False,
        'error': None,
        'killzones_active': [],
        'pairs_analyzed': 0,
        'signals_total': 0,
        'flags': [],
        'crt_signals': [],  # CRT-specific signals
    }
    
    try:
        now = datetime.now()
        wd = now.weekday()
        h, m = now.hour, now.minute
        hora = h + m / 60.0
        
        # Fim de semana / sexta tarde
        if wd == 5:
            result.update({'checked': True, 'error': 'Sábado'}); return result
        if wd == 6 and hora < 17.0:
            result.update({'checked': True, 'error': 'Domingo antes 17h'}); return result
        if wd == 4 and hora >= 13.0:
            result.update({'checked': True, 'error': 'Sexta após 13h'}); return result
        
        # Blackout
        try:
            from forex_calendar import get_news_blackout_status
            blackout = get_news_blackout_status(ALL_PAIRS)
            if blackout['in_blackout']:
                events_desc = [f"{e['impact']} {e['description']}" for e in blackout['events']]
                result['checked'] = True
                result['error'] = f"BLACKOUT: {'; '.join(events_desc)}"
                result['flags'].append({
                    'type': 'BLACKOUT', 'reason': '; '.join(events_desc), 'priority': 'INFO'
                })
                return result
        except ImportError:
            pass
        
        # Identificar killzones ativas
        active_kz = []
        for name, kz in KILLZONES.items():
            kz_start = kz['start_h'] + kz['start_m'] / 60.0
            kz_end = kz['end_h'] + kz['end_m'] / 60.0
            if kz_start <= hora < kz_end:
                active_kz.append((name, kz))
        
        # T-2: análise pré-killzone
        is_t2 = False
        if not active_kz:
            for name, kz in KILLZONES.items():
                t2_h, t2_m = kz['t2_analysis']
                if h == t2_h and m == t2_m:
                    active_kz.append((name, kz))
                    is_t2 = True
                    break
        
        if not active_kz:
            result['checked'] = True
            result['error'] = 'Fora das killzones'
            return result
        
        result['killzones_active'] = [s[0] for s in active_kz]
        
        # Analisar pares com CRT
        all_pairs = set()
        for _, kz in active_kz:
            all_pairs.update(kz['pairs'])
        
        signals = []
        crt_signals = []
        
        for pair in all_pairs:
            symbol = PAIRS.get(pair)
            if not symbol:
                continue
            
            # Buscar M1 para CRT (mais preciso que M5)
            data_m1 = fetch_intraday(symbol, '1m', hours=6)
            data_m5 = fetch_intraday(symbol, '5m', hours=6)
            
            result['pairs_analyzed'] += 1
            
            # Análise M5 tradicional
            analysis_m5 = analyze_m5(pair, data_m5)
            
            # Análise CRT no M1
            crt = analyze_crt(pair, data_m1)
            
            if crt:
                crt_signals.append(crt)
                result['signals_total'] += 1
                
                priority = 'MEDIUM' if crt.get('sweep_confirmed') else 'LOW'
                if crt.get('range_expanding') and crt.get('sweep_confirmed'):
                    priority = 'MEDIUM'
                
                signals.append({
                    'type': 'SIGNAL_STRONG' if crt.get('sweep_confirmed') else 'SIGNAL',
                    'pair': pair,
                    'direction': crt['direction'],
                    'score': crt.get('crt_score', 0),
                    'strength': 'FORTE' if crt.get('sweep_confirmed') else 'MODERADO',
                    'price': crt['entry'],
                    'stop_pips': crt['stop_pips'],
                    'target_pips': crt['target_pips'],
                    'rsi': analysis_m5['indicators']['rsi9'] if analysis_m5 else None,
                    'momentum': crt.get('momentum_pips', 0),
                    'breakout': 'SWEEP_CONFIRMED' if crt.get('sweep_confirmed') else None,
                    'crt_details': {
                        'sweep_detected': crt['sweep_detected'],
                        'sweep_confirmed': crt['sweep_confirmed'],
                        'range_expanding': crt['range_expanding'],
                        'pattern': crt.get('pattern', ''),
                    },
                    'priority': priority,
                })
        
        result['checked'] = True
        result['crt_signals'] = crt_signals
        
        # Top 3 por score
        signals.sort(key=lambda s: abs(s['score']), reverse=True)
        result['flags'] = signals[:3]
        
    except Exception as e:
        result['error'] = str(e)[:100]
    
    return result


def analyze_crt(pair: str, data: dict) -> dict:
    """Análise CRT (Candle Range Theory) para killzones.
    
    Detecta:
    1. Sweep de liquidez (vela com pavio longo que rompe range anterior)
    2. Confirmação CRT (vela seguinte rompe a máxima/mínima do sweep)
    3. Range expansion (NR4/NR7 → explosão)
    4. Inside bar breakout
    """
    if 'error' in data or len(data.get('closes', [])) < 10:
        return None
    
    closes = data['closes']
    highs = data['highs']
    lows = data['lows']
    opens = data['opens']
    
    if not all([closes, highs, lows]):
        return None
    
    # Últimos candles
    c = closes[-1]   # Current
    c1 = closes[-2]  # Previous
    c2 = closes[-3] if len(closes) >= 3 else c1
    h_cur = highs[-1]; l_cur = lows[-1]
    h1 = highs[-2]; l1 = lows[-2]
    h2 = highs[-3] if len(highs) >= 3 else h1; l2 = lows[-3] if len(lows) >= 3 else l1
    
    pips_factor = 100 if 'JPY' in pair else 10000
    
    range_current = h_cur - l_cur
    range_prev = h1 - l1
    range_prev2 = h2 - l2
    
    range_current_pips = range_current * pips_factor
    range_prev_pips = range_prev * pips_factor
    
    # Média de range dos últimos 5 candles
    ranges_5 = []
    for i in range(-5, 0):
        if abs(i) <= len(highs):
            ranges_5.append(highs[i] - lows[i])
    avg_range = sum(ranges_5) / len(ranges_5) if ranges_5 else range_current
    avg_range_pips = avg_range * pips_factor
    
    result = {
        'pair': pair,
        'price': round(c, 5),
        'sweep_detected': False,
        'sweep_confirmed': False,
        'range_expanding': False,
        'pattern': '',
        'direction': 'NEUTRO',
        'entry': round(c, 5),
        'stop_pips': 0,
        'target_pips': 0,
        'momentum_pips': round((c - c1) * pips_factor, 1),
        'crt_score': 0,
    }
    
    score = 0
    
    # 1. DETECTAR SWEEP (pavio longo que rompe range anterior)
    upper_wick = h_cur - max(c, opens[-1]) if opens and len(opens) >= 1 else h_cur - c
    lower_wick = min(c, opens[-1] if opens and len(opens) >= 1 else c) - l_cur
    body = abs(c - (opens[-1] if opens and len(opens) >= 1 else c1))
    
    # Sweep de alta (rompeu topo da vela anterior com pavio superior comprido)
    if h_cur > h1 and upper_wick > body * 1.5 and c < h_cur:
        result['sweep_detected'] = True
        result['sweep_direction'] = 'ALTA'
        result['sweep_level'] = round(h1, 5)
        score += 1.5
    
    # Sweep de baixa (rompeu fundo da vela anterior com pavio inferior comprido)
    if l_cur < l1 and lower_wick > body * 1.5 and c > l_cur:
        result['sweep_detected'] = True
        result['sweep_direction'] = 'BAIXA'
        result['sweep_level'] = round(l1, 5)
        score += 1.5
    
    # 2. CONFIRMAÇÃO CRT (vela atual rompe range do sweep na direção certa)
    if result.get('sweep_direction') == 'ALTA' and c > h_cur * 0.999 and c > c1:
        # Sweep de alta → vela atual fecha acima do sweep = confirmação de compra
        result['sweep_confirmed'] = True
        result['direction'] = 'VENDA'  # Vendeu no sweep, mercado sobe
        score += 2.0
    elif result.get('sweep_direction') == 'BAIXA' and c < l_cur * 1.001 and c < c1:
        result['sweep_confirmed'] = True
        result['direction'] = 'COMPRA'
        score += 2.0
    
    # 3. RANGE EXPANSION (NR4/NR7 → explosão)
    if range_current_pips > avg_range_pips * 1.3:
        result['range_expanding'] = True
        momentum = (c - c1) * pips_factor
        if momentum > 0:
            result['direction'] = 'COMPRA' if result['direction'] == 'NEUTRO' else result['direction']
        elif momentum < 0:
            result['direction'] = 'VENDA' if result['direction'] == 'NEUTRO' else result['direction']
        score += 1.0
        result['pattern'] = 'NR_EXPANSION'
    
    # NR4 detectado (range atual é o menor de 4)
    if len(ranges_5) >= 4:
        last_4 = ranges_5[-4:]
        if range_current <= min(last_4):
            result['pattern'] = (result['pattern'] + '+NR4').strip('+')
            score += 1.0
    
    # 4. INSIDE BAR
    if h_cur <= h1 and l_cur >= l1:
        result['pattern'] = (result['pattern'] + '+INSIDE').strip('+')
        # Aguardar breakout
        if c > h1:  # Rompeu pra cima
            result['direction'] = 'COMPRA'
            score += 1.5
        elif c < l1:  # Rompeu pra baixo
            result['direction'] = 'VENDA'
            score += 1.5
    
    # Se não tem direção clara, usa momentum
    if result['direction'] == 'NEUTRO':
        mom = (c - c1) * pips_factor
        if mom > CRT_MIN_MOMENTUM:
            result['direction'] = 'COMPRA'
        elif mom < -CRT_MIN_MOMENTUM:
            result['direction'] = 'VENDA'
        else:
            return None  # Sem sinal claro
    
    # Cálculo de stop e target (baseado no range da vela de sweep)
    if result['sweep_detected']:
        stop_dist = range_current * CRT_STOP_MULT
        target_dist = range_current * CRT_TARGET_MULT
    else:
        stop_dist = avg_range * CRT_STOP_MULT
        target_dist = avg_range * CRT_TARGET_MULT
    
    if result['direction'] == 'COMPRA':
        result['entry'] = round(c, 5)
        result['stop'] = round(c - stop_dist, 5)
        result['target'] = round(c + target_dist, 5)
    else:
        result['entry'] = round(c, 5)
        result['stop'] = round(c + stop_dist, 5)
        result['target'] = round(c - target_dist, 5)
    
    result['stop_pips'] = round(stop_dist * pips_factor, 1)
    result['target_pips'] = round(target_dist * pips_factor, 1)
    result['crt_score'] = round(score, 2)
    
    # Validações mínimas
    if result['stop_pips'] < CRT_MIN_RANGE_PIPS:
        result['stop_pips'] = CRT_MIN_RANGE_PIPS
    if result['target_pips'] < result['stop_pips'] * 1.5:
        result['target_pips'] = result['stop_pips'] * 2.0
    
    return result


# ═══════════════════════════════════════════
# MAIN — output sempre JSON
# ═══════════════════════════════════════════

def main():
    output = {
        'timestamp': datetime.now().isoformat(),
        'status': 'ok',
        'renda': {},
        'trade': {},
    }
    
    # Coletar renda
    output['renda'] = check_emails()
    
    # Coletar trade
    output['trade'] = check_forex()
    
    # Status geral
    all_flags = output['renda'].get('flags', []) + output['trade'].get('flags', [])
    has_high = any(f.get('priority') == 'HIGH' for f in all_flags)
    has_medium = any(f.get('priority') == 'MEDIUM' for f in all_flags)
    
    output['summary'] = {
        'total_flags': len(all_flags),
        'has_urgent': has_high,
        'has_attention': has_medium or has_high,
        'high_priority': sum(1 for f in all_flags if f.get('priority') == 'HIGH'),
        'medium_priority': sum(1 for f in all_flags if f.get('priority') == 'MEDIUM'),
    }
    
    print(json.dumps(output, ensure_ascii=False, default=str))
    return 0

if __name__ == '__main__':
    sys.exit(main())
