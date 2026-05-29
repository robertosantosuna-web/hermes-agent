#!/usr/bin/env python3
"""
Memória de Aprendizado do Agente Freelancer
═══════════════════════════════════════════════

SONA-lite adaptado para freelancing:
- Aprende quais categorias convertem mais
- Aprende quais templates vendem melhor
- Aprende melhores horários para propor
- Mantém replay buffer das últimas 100 interações
- Atualiza pesos a cada ciclo

Arquivo: ~/.hermes/forex/memory_weights.json
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter

H = Path.home() / '.hermes'
FOREX = H / 'forex'
MEMORY_FILE = FOREX / 'memory_weights.json'

# ═══ CATEGORIAS (TÓPICOS) ═══
CATEGORIES = {
    'excel': {
        'keywords': ['excel', 'planilha', 'spreadsheet', 'google sheets', 'dashboard',
                     'macro', 'vba', 'fórmula', 'formula', 'tabela dinâmica', 'pivot'],
        'templates': ['excel_v1', 'excel_v2'],
        'price_range_brl': (80, 400),
        'price_range_usd': (25, 80),
    },
    'data_entry': {
        'keywords': ['digita', 'data entry', 'typing', 'copiar', 'colar', 'cadastro',
                     'lista', 'planilha simples', 'digitação', 'digitador'],
        'templates': ['data_entry_v1'],
        'price_range_brl': (50, 150),
        'price_range_usd': (15, 35),
    },
    'revisao': {
        'keywords': ['revisão', 'correção', 'abnt', 'tcc', 'monografia', 'ortográfica',
                     'format', 'normas', 'nbr', 'acadêmico', 'artigo científico'],
        'templates': ['revisao_v1', 'revisao_v2'],
        'price_range_brl': (80, 300),
        'price_range_usd': (20, 60),
    },
    'traducao': {
        'keywords': ['traduç', 'translation', 'translate', 'inglês', 'português',
                     'english', 'portuguese', 'pt-en', 'en-pt'],
        'templates': ['traducao_v1'],
        'price_range_brl': (50, 150),
        'price_range_usd': (15, 40),
    },
    'python': {
        'keywords': ['python', 'script', 'automação', 'automation', 'scraping',
                     'web scraping', 'bot', 'api', 'data extraction', 'extrair dados',
                     'limpeza de dados', 'data cleaning', 'csv', 'pandas'],
        'templates': ['python_v1', 'python_v2'],
        'price_range_brl': (150, 600),
        'price_range_usd': (50, 200),
    },
    'pdf_word': {
        'keywords': ['pdf', 'word', 'converter', 'conversão', 'sumário', 'formatação',
                     'documento', 'docx', 'editor', 'editar pdf'],
        'templates': ['pdf_v1'],
        'price_range_brl': (50, 150),
        'price_range_usd': (15, 35),
    },
    'virtual_assistant': {
        'keywords': ['virtual assistant', 'assistente virtual', 'admin', 'administrativo',
                     'secretária', 'atendimento', 'suporte', 'organização'],
        'templates': ['va_v1'],
        'price_range_brl': (60, 200),
        'price_range_usd': (15, 50),
    },
}

def load_memory():
    """Carrega pesos da memória."""
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text())
    return init_memory()

def init_memory():
    """Inicializa estrutura de memória vazia."""
    mem = {
        'version': '1.0',
        'created': datetime.now(timezone.utc).isoformat(),
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'categories': {},
        'templates': {},
        'clients': {},
        'keyword_performance': {},
        'time_windows': {str(h): {'proposals': 0, 'wins': 0} for h in range(24)},
        'replay_buffer': [],
        'stats': {
            'total_proposals': 0,
            'total_contracts': 0,
            'total_earned_brl': 0.0,
            'total_earned_usd': 0.0,
            'total_hours': 0.0,
        }
    }
    
    for cat_name, cat_data in CATEGORIES.items():
        mem['categories'][cat_name] = {
            'proposals_sent': 0,
            'contracts_won': 0,
            'conversion_rate': 0.0,
            'avg_ticket_brl': 0.0,
            'avg_ticket_usd': 0.0,
            'avg_delivery_hours': 0.0,
            'total_earned_brl': 0.0,
            'total_earned_usd': 0.0,
            'best_template': None,
            'best_hour': None,
            'roi_per_hour_brl': 0.0,
            'active': True,
        }
        for tid in cat_data['templates']:
            mem['templates'][tid] = {
                'category': cat_name,
                'uses': 0,
                'wins': 0,
                'conversion_rate': 0.0,
                'last_used': None,
                'last_won': None,
            }
    
    save_memory(mem)
    return mem

def save_memory(mem):
    mem['last_updated'] = datetime.now(timezone.utc).isoformat()
    MEMORY_FILE.write_text(json.dumps(mem, indent=2, ensure_ascii=False))

def classify_job(title, description=''):
    """Classifica um job em uma categoria."""
    text = (title + ' ' + description).lower()
    scores = {}
    
    for cat_name, cat_data in CATEGORIES.items():
        score = sum(1 for kw in cat_data['keywords'] if kw in text)
        if score > 0:
            scores[cat_name] = score
    
    if not scores:
        return None, 0
    
    best_cat = max(scores, key=scores.get)
    return best_cat, scores[best_cat]

def get_best_template(category):
    """Retorna o template com maior taxa de conversão para a categoria."""
    mem = load_memory()
    cat_data = CATEGORIES.get(category, {})
    template_ids = cat_data.get('templates', [])
    
    best_id = None
    best_rate = -1
    
    for tid in template_ids:
        t = mem.get('templates', {}).get(tid, {})
        rate = t.get('conversion_rate', 0)
        uses = t.get('uses', 0)
        # Template novo (sem dados) também é candidato
        if uses == 0:
            if best_id is None:
                best_id = tid
        elif rate > best_rate:
            best_rate = rate
            best_id = tid
    
    return best_id or (template_ids[0] if template_ids else None)

def get_best_time_window():
    """Retorna melhor horário para enviar proposta."""
    mem = load_memory()
    best_hour = None
    best_rate = -1
    
    for hour_str, data in mem.get('time_windows', {}).items():
        proposals = data.get('proposals', 0)
        wins = data.get('wins', 0)
        if proposals >= 3:
            rate = wins / proposals
            if rate > best_rate:
                best_rate = rate
                best_hour = int(hour_str)
    
    return best_hour, best_rate

def record_proposal_sent(category, template_id, platform, hour=None):
    """Registra envio de proposta."""
    mem = load_memory()
    
    if hour is None:
        hour = datetime.now(timezone.utc).hour - 3  # BRT
        if hour < 0:
            hour += 24
    
    # Categoria
    if category in mem.get('categories', {}):
        mem['categories'][category]['proposals_sent'] += 1
    
    # Template
    if template_id in mem.get('templates', {}):
        mem['templates'][template_id]['uses'] += 1
        mem['templates'][template_id]['last_used'] = datetime.now(timezone.utc).isoformat()
    
    # Time window
    hour_str = str(hour)
    if hour_str in mem.get('time_windows', {}):
        mem['time_windows'][hour_str]['proposals'] += 1
    
    # Stats
    mem['stats']['total_proposals'] += 1
    
    # Replay buffer
    mem.setdefault('replay_buffer', []).append({
        'type': 'proposal_sent',
        'category': category,
        'template': template_id,
        'platform': platform,
        'hour': hour,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })
    
    # Manter últimos 200
    if len(mem.get('replay_buffer', [])) > 200:
        mem['replay_buffer'] = mem['replay_buffer'][-200:]
    
    save_memory(mem)

def record_contract_won(category, template_id, platform, ticket_brl=0, ticket_usd=0, 
                        delivery_hours=0, client_name=None, hour=None):
    """Registra contrato ganho."""
    mem = load_memory()
    
    if hour is None:
        hour = datetime.now(timezone.utc).hour - 3
        if hour < 0:
            hour += 24
    
    # Categoria
    cat = mem.get('categories', {}).get(category, {})
    if cat:
        cat['contracts_won'] += 1
        proposals = cat.get('proposals_sent', 0)
        cat['conversion_rate'] = round(cat['contracts_won'] / max(proposals, 1), 3)
        
        if ticket_brl > 0:
            cat['total_earned_brl'] += ticket_brl
            cat['avg_ticket_brl'] = round(cat['total_earned_brl'] / cat['contracts_won'], 2)
        if ticket_usd > 0:
            cat['total_earned_usd'] += ticket_usd
            cat['avg_ticket_usd'] = round(cat['total_earned_usd'] / cat['contracts_won'], 2)
        if delivery_hours > 0:
            cat['avg_delivery_hours'] = round(
                (cat.get('avg_delivery_hours', 0) * (cat['contracts_won'] - 1) + delivery_hours)
                / cat['contracts_won'], 1
            )
        
        if ticket_brl > 0 and delivery_hours > 0:
            cat['roi_per_hour_brl'] = round(cat['total_earned_brl'] / 
                                            (cat['contracts_won'] * max(cat.get('avg_delivery_hours', 1), 0.5)), 2)
    
    # Template
    if template_id in mem.get('templates', {}):
        mem['templates'][template_id]['wins'] += 1
        uses = mem['templates'][template_id].get('uses', 1)
        mem['templates'][template_id]['conversion_rate'] = round(
            mem['templates'][template_id]['wins'] / max(uses, 1), 3
        )
        mem['templates'][template_id]['last_won'] = datetime.now(timezone.utc).isoformat()
    
    # Time window
    hour_str = str(hour)
    if hour_str in mem.get('time_windows', {}):
        mem['time_windows'][hour_str]['wins'] += 1
    
    # Cliente
    if client_name:
        client = mem.setdefault('clients', {}).setdefault(client_name, {
            'jobs': 0, 'total_paid_brl': 0, 'total_paid_usd': 0, 'platform': platform
        })
        client['jobs'] += 1
        client['total_paid_brl'] += ticket_brl
        client['total_paid_usd'] += ticket_usd
    
    # Stats globais
    mem['stats']['total_contracts'] += 1
    mem['stats']['total_earned_brl'] += ticket_brl
    mem['stats']['total_earned_usd'] += ticket_usd
    mem['stats']['total_hours'] += delivery_hours
    
    # Replay buffer
    mem.setdefault('replay_buffer', []).append({
        'type': 'contract_won',
        'category': category,
        'template': template_id,
        'platform': platform,
        'ticket_brl': ticket_brl,
        'ticket_usd': ticket_usd,
        'hour': hour,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })
    
    # Atualizar melhor template e hora
    best_t = get_best_template(category)
    if best_t:
        mem['categories'][category]['best_template'] = best_t
    
    best_h, _ = get_best_time_window()
    if best_h is not None:
        mem['categories'][category]['best_hour'] = best_h
    
    save_memory(mem)

def record_proposal_lost(category, template_id, reason='no_response'):
    """Registra proposta perdida/sem resposta."""
    mem = load_memory()
    mem.setdefault('replay_buffer', []).append({
        'type': 'proposal_lost',
        'category': category,
        'template': template_id,
        'reason': reason,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })
    if len(mem.get('replay_buffer', [])) > 200:
        mem['replay_buffer'] = mem['replay_buffer'][-200:]
    
    save_memory(mem)

def get_category_stats(category):
    """Retorna estatísticas de uma categoria."""
    mem = load_memory()
    return mem.get('categories', {}).get(category, {})

def get_global_stats():
    """Retorna estatísticas globais."""
    mem = load_memory()
    return mem.get('stats', {})

def get_top_categories(min_proposals=3):
    """Retorna categorias ordenadas por conversão."""
    mem = load_memory()
    ranked = []
    
    for name, data in mem.get('categories', {}).items():
        if data.get('proposals_sent', 0) >= min_proposals:
            ranked.append((name, data.get('conversion_rate', 0), data))
    
    ranked.sort(key=lambda x: -x[1])
    return ranked

def get_insights():
    """Gera insights baseados na memória."""
    mem = load_memory()
    insights = []
    
    # Melhor categoria
    top = get_top_categories(min_proposals=1)
    if top:
        insights.append(f"🔥 Melhor categoria: {top[0][0]} ({top[0][1]*100:.0f}% conversão)")
    
    # Melhor horário
    best_h, best_rate = get_best_time_window()
    if best_h is not None and best_rate > 0:
        insights.append(f"⏰ Melhor horário: {best_h}h ({best_rate*100:.0f}% conversão)")
    
    # Categorias com baixa conversão (candidatas a depreciação)
    for name, rate, data in top:
        if rate < 0.10 and data.get('proposals_sent', 0) >= 5:
            insights.append(f"⚠️ Baixa conversão: {name} ({rate*100:.0f}%) — considere mudar template ou preço")
    
    # Categorias sem dados (oportunidade)
    for name in CATEGORIES:
        cat = mem.get('categories', {}).get(name, {})
        if cat.get('proposals_sent', 0) == 0:
            insights.append(f"🆕 Sem dados: {name} — oportunidade inexplorada")
    
    # ROI por hora
    stats = mem.get('stats', {})
    if stats.get('total_hours', 0) > 0 and stats.get('total_earned_brl', 0) > 0:
        roi = stats['total_earned_brl'] / stats['total_hours']
        insights.append(f"💰 ROI médio: R${roi:.2f}/hora")
    
    return insights

def replay_learn():
    """Aprendizado por replay: reavalia estratégias baseado no buffer."""
    mem = load_memory()
    buffer = mem.get('replay_buffer', [])
    
    if len(buffer) < 10:
        return  # Precisa de dados suficientes
    
    # Analisar últimos 50 eventos
    recent = buffer[-50:]
    
    # Contar wins por template
    template_wins = Counter()
    template_uses = Counter()
    for event in recent:
        tid = event.get('template', '')
        if event.get('type') == 'proposal_sent':
            template_uses[tid] += 1
        elif event.get('type') == 'contract_won':
            template_wins[tid] += 1
    
    # Templates com baixa performance → flag
    for tid, uses in template_uses.items():
        if uses >= 5:
            wins = template_wins.get(tid, 0)
            rate = wins / uses
            if rate < 0.10:
                # Depreciar template
                if tid in mem.get('templates', {}):
                    mem['templates'][tid]['deprecated'] = True
    
    save_memory(mem)

# ═══ TESTE ═══
if __name__ == "__main__":
    mem = load_memory()
    print(f"Memória v{mem['version']}")
    print(f"Criada: {mem['created']}")
    print(f"Categorias: {len(mem['categories'])}")
    print(f"Templates: {len(mem['templates'])}")
    print(f"Buffer: {len(mem.get('replay_buffer', []))} eventos")
    
    # Teste de classificação
    test_jobs = [
        "Preciso de planilha Excel com dashboard e macros",
        "Digitação de 500 nomes para planilha",
        "Revisão de TCC nas normas ABNT 2026",
        "Tradução de artigo PT-EN 5 páginas",
        "Script Python para extrair dados de site e salvar CSV",
        "Converter PDF para Word com formatação",
        "Assistente virtual para organizar emails",
    ]
    
    for job in test_jobs:
        cat, score = classify_job(job)
        print(f"  [{score}] {cat}: {job[:60]}")
    
    insights = get_insights()
    print(f"\nInsights ({len(insights)}):")
    for i in insights:
        print(f"  {i}")
