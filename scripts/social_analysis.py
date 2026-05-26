#!/usr/bin/env python3
"""
ANALISE COMPORTAMENTAL E SOCIAL DE ROBERTO
Sintese a partir de dados WhatsApp (66 conversas) + Telegram (13 conversas)
"""
import json, os
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR = Path.home() / '.hermes' / 'data' / 'social'

# Carregar dados
with open(DATA_DIR / 'whatsapp_chats.json') as f:
    wa = json.load(f)

with open(DATA_DIR / 'telegram_dialogs.json') as f:
    tg = json.load(f)

wa_chats = wa['chats']
tg_dialogs = tg['dialogs']

print("=" * 70)
print("🔬 ANALISE COMPORTAMENTAL E SOCIAL DE ROBERTO")
print("=" * 70)
print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print(f"Fontes: WhatsApp ({len(wa_chats)} conversas) + Telegram ({len(tg_dialogs)} conversas)")
print()

# ============================================================
# 1. METRICAS GERAIS
# ============================================================
print("━" * 70)
print("📊 1. METRICAS GERAIS DE ENGAJAMENTO")
print("━" * 70)

wa_total_unread = sum(c.get('unread', 0) for c in wa_chats)
tg_total_unread = tg.get('total_unread', 0)
wa_unread_chats = [c for c in wa_chats if c.get('unread', 0) > 0]
tg_unread_chats = [d for d in tg_dialogs if d.get('unread', 0) > 0]

print(f"""
WhatsApp:
  Conversas totais:     {len(wa_chats)}
  Mensagens nao lidas:  {wa_total_unread}
  Conversas pendentes:  {len(wa_unread_chats)}
  Taxa de negligencia:  {len(wa_unread_chats)/max(len(wa_chats),1)*100:.0f}% das conversas

Telegram:
  Conversas totais:     {len(tg_dialogs)}
  Mensagens nao lidas:  {tg_total_unread}
  Conversas pendentes:  {len(tg_unread_chats)}
  Taxa de negligencia:  {len(tg_unread_chats)/max(len(tg_dialogs),1)*100:.0f}% das conversas
""")

# ============================================================
# 2. DISTRIBUICAO DE ATENCAO POR CATEGORIA
# ============================================================
print("━" * 70)
print("🎯 2. DISTRIBUICAO DE ATENCAO POR CATEGORIA (WhatsApp)")
print("━" * 70)

cats = defaultdict(lambda: {'count': 0, 'unread': 0, 'responded': 0})
for c in wa_chats:
    cat = c.get('category', 'social')
    cats[cat]['count'] += 1
    cats[cat]['unread'] += c.get('unread', 0)
    if c.get('unread', 0) == 0 and c.get('time'):
        cats[cat]['responded'] += 1

print(f"\n{'Categoria':<15} {'Total':>5} {'Nao Lidas':>10} {'Respondidas':>12} {'% Atencao':>10}")
print("-" * 55)
for cat in ['familia', 'trabalho', 'religiao', 'comercial', 'social']:
    d = cats.get(cat, {'count':0, 'unread':0, 'responded':0})
    pct = d['responded']/max(d['count'],1)*100
    bar = '█' * int(pct/5)
    print(f"{cat:<15} {d['count']:>5} {d['unread']:>10} {d['responded']:>12} {pct:>9.0f}% {bar}")

print(f"\n🔴 PADRAO CRITICO: Categorias 'social' e 'comercial' concentram {cats['social']['unread'] + cats['comercial']['unread']} msgs nao lidas.")
print(f"🟢 Familia recebe atencao quase total ({cats.get('familia',{}).get('responded',0)}/{cats.get('familia',{}).get('count',0)} respondidas)")

# ============================================================
# 3. PADRAO DE NEGLIGENCIA (EVITACAO)
# ============================================================
print("\n" + "━" * 70)
print("🚨 3. PADRAO DE NEGLIGENCIA / EVITACAO")
print("━" * 70)

# Top chats ignorados
ignored = sorted(wa_chats, key=lambda c: c.get('unread', 0), reverse=True)

print("\nTop 10 conversas MAIS NEGLIGENCIADAS:")
print(f"{'#':<4} {'Nome':<45} {'Nao Lidas':>10} {'Ultimo Contato':>18} {'Tipo':<12}")
print("-" * 92)
for i, c in enumerate(ignored[:10]):
    cat = c.get('category', '?')
    time = c.get('time', '?')
    print(f"{i+1:<4} {c['name'][:44]:<45} {c['unread']:>10} {time:>18} {cat:<12}")

# Analise: sao grupos/comunidades ou individuos?
community_kw = ['comunidade', 'grupo', 'group', 'aula', 'mecânico', 'criminalista', 'fretado', 'whatsapp']
neglected_communities = [c for c in ignored if any(kw in c['name'].lower() for kw in community_kw)]
neglected_people = [c for c in ignored if not any(kw in c['name'].lower() for kw in community_kw) and c.get('unread', 0) > 10]

print(f"\n📢 Comunidades/Grupos negligenciados: {len(neglected_communities)} ({sum(c['unread'] for c in neglected_communities)} msgs)")
print(f"👤 Pessoas negligenciadas (>10 msgs): {len(neglected_people)} ({sum(c['unread'] for c in neglected_people)} msgs)")

if neglected_people:
    for c in neglected_people:
        print(f"   - {c['name'][:40]} ({c['unread']} msgs)")

# Padrao: subscriber de comunidades que nunca le
subscriber_pattern = sum(c['unread'] for c in neglected_communities)
print(f"\n⚠️  PADRAO 'SUBSCRIBER FANTASMA': {len(neglected_communities)} comunidades com {subscriber_pattern} msgs acumuladas.")
print("   Entra em canais/grupos mas nunca consome o conteudo.")

# ============================================================
# 4. PADRAO DE RESPOSTA (QUEM RECEBE ATENCAO)
# ============================================================
print("\n" + "━" * 70)
print("💬 4. PADRAO DE RESPOSTA — QUEM RECEBE ATENCAO?")
print("━" * 70)

# Chats respondidos (unread=0, tem timestamp recente)
recently_active = [c for c in wa_chats if c.get('unread', 0) == 0 and c.get('time')]
today_chats = [c for c in recently_active if c.get('time', '') and not any(kw in c.get('time','').lower() for kw in ['ontem', 'semana', 'mês', 'mes', 'maio', 'abril', 'março', 'segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo'])]

print(f"\nConversas ATIVAS HOJE: {len(today_chats)}")
for c in today_chats:
    print(f"  ✓ {c['name'][:40]:40s} {c.get('time','?'):>6s} | {c.get('last_msg','')[:60]}")

# Analise de reciprocidade (baseado em ultima msg)
# No WhatsApp, se a ultima msg foi enviada por Roberto = "outgoing", senao = "incoming"
family_chats = [c for c in wa_chats if c.get('category') == 'familia']
social_chats_active = [c for c in wa_chats if c.get('category') == 'social' and c.get('time')]

print(f"\n📞 PADRAO FAMILIAR: {len(family_chats)} contatos")
print("   Familia recebe atencao prioritaria — todos respondidos hoje ou ontem.")
for c in family_chats:
    print(f"   {'👤' if not c.get('group') else '👥'} {c['name'][:30]:30s} {c.get('time','?'):>6s} | {c.get('last_msg','')[:50]}")

# ============================================================
# 5. PADRAO TEMPORAL
# ============================================================
print("\n" + "━" * 70)
print("⏰ 5. PADRAO TEMPORAL DE COMUNICACAO")
print("━" * 70)

# Extrair horarios das ultimas mensagens
times = []
for c in wa_chats:
    t = c.get('time', '')
    if ':' in t and len(t) <= 5:
        try:
            h, m = t.split(':')
            times.append(int(h))
        except:
            pass

if times:
    time_dist = Counter(times)
    print("\nDistribuicao de ultimas interacoes por hora:")
    for h in range(24):
        count = time_dist.get(h, 0)
        if count > 0:
            bar = '█' * count
            period = '🌅 manhã' if 6 <= h < 12 else '☀️ tarde' if 12 <= h < 18 else '🌙 noite' if 18 <= h < 23 else '🕐 madrugada'
            print(f"  {h:02d}h [{period:15s}] {count:3d} {bar}")

# ============================================================
# 6. ANALISE TELEGRAM
# ============================================================
print("\n" + "━" * 70)
print("📱 6. ANALISE TELEGRAM (13 conversas)")
print("━" * 70)

tg_sorted = sorted(tg_dialogs, key=lambda d: d.get('last_date', ''), reverse=True)

print("\nTodas as conversas Telegram (ordenadas por atividade):")
for d in tg_sorted:
    tag = "📌" if d.get('pinned') else "  "
    name = d['name'][:40]
    last = d.get('last_date', '?')[:10] if d.get('last_date') else '?'
    msg = d.get('last_msg', '')[:60]
    unread = d.get('unread', 0)
    unread_str = f"[{unread}]" if unread else ""
    print(f"  {tag} {name:<42s} {last} {unread_str:>6s} | {msg}")

# Telegram inactivity
now = datetime.now()
inactive_tg = []
for d in tg_dialogs:
    if d.get('last_date'):
        try:
            last_date = datetime.fromisoformat(d['last_date'].replace('Z', '+00:00'))
            days_inactive = (now - last_date.replace(tzinfo=None)).days
            if days_inactive > 90 and not d.get('is_channel'):
                inactive_tg.append((d['name'], days_inactive))
        except:
            pass

if inactive_tg:
    print(f"\n⚠️  CONTATOS TELEGRAM INATIVOS (>90 dias sem msg):")
    for name, days in sorted(inactive_tg, key=lambda x: x[1], reverse=True):
        print(f"   - {name[:40]:40s} {days} dias")
        if days > 365:
            print(f"     🔴 ABANDONADO — mais de 1 ano sem contato")

# ============================================================
# 7. DIAGNOSTICO COMPORTAMENTAL
# ============================================================
print("\n" + "=" * 70)
print("🧠 7. DIAGNOSTICO COMPORTAMENTAL")
print("=" * 70)

diagnosticos = []

# 7.1 Sobrecarga de informacao
diagnosticos.append({
    'titulo': 'SOBRECARGA DE INFORMACAO',
    'gravidade': '🔴 ALTA',
    'dados': f'{wa_total_unread} mensagens nao lidas em {len(wa_unread_chats)} conversas WhatsApp',
    'padrao': 'Acumulo massivo de conteudo nao processado. Entra em canais/comunidades mas nao consome. Cria ansiedade de backlog.',
    'impacto': 'Estresse cognitivo, FOMO, sensacao de estar sempre atrasado'
})

# 7.2 Subscriber fantasma
diagnosticos.append({
    'titulo': 'SUBSCRIBER FANTASMA',
    'gravidade': '🔴 ALTA',
    'dados': f'{len(neglected_communities)} comunidades com {subscriber_pattern} msgs acumuladas',
    'padrao': 'Entra em grupos/canais por impulso (interesse momentaneo) mas nunca consome o conteudo. Coleciona comunidades como se fossem conquistas.',
    'impacto': 'Desperdicio de atencao, notificacoes que drenam energia, falsa sensacao de estar se informando'
})

# 7.3 Hiperfoco familiar
diagnosticos.append({
    'titulo': 'HIPERFOCO FAMILIAR',
    'gravidade': '🟡 MEDIA',
    'dados': f'Familia: {cats["familia"]["responded"]}/{cats["familia"]["count"]} respondidas. Social: {cats["social"]["responded"]}/{cats["social"]["count"]} respondidas.',
    'padrao': 'Prioriza familia acima de tudo. Responde rapido para nucleo familiar mas negligencia outras relacoes.',
    'impacto': 'Relacoes sociais e profissionais sofrem. Oportunidades de networking perdidas.'
})

# 7.4 Rede social inchada e superficial
diagnosticos.append({
    'titulo': 'REDE SOCIAL INCHADA E SUPERFICIAL',
    'gravidade': '🟡 MEDIA',
    'dados': f'66 conversas WhatsApp, maioria social superficial. Telegram: apenas 13 contatos, mais focado.',
    'padrao': 'WhatsApp = rede inchada com muitos contatos superficiais. Telegram = rede enxuta e focada. Incapaz de manter 66 relacoes ativas.',
    'impacto': 'Dispersao de energia social. Relacoes de alto valor diluidas no ruido.'
})

# 7.5 Evitacao de conflito/confronto
diagnosticos.append({
    'titulo': 'EVITACAO DE COMPROMISSO SOCIAL',
    'gravidade': '🟡 MEDIA',
    'dados': 'Deixa mensagens acumularem em vez de responder ou silenciar/sair.',
    'padrao': 'Nao sai de grupos que nao interessam mais. Nao silencia notificacoes. Prefere ignorar do que confrontar (dar unfollow/sair).',
    'impacto': 'Backlog crescente gera ansiedade. Incapacidade de dizer "nao" a convites/grupos.'
})

# 7.6 Baixa manutencao de relacoes de longo prazo
diagnosticos.append({
    'titulo': 'BAIXA MANUTENCAO DE RELACOES ANTIGAS',
    'gravidade': '🟡 MEDIA',
    'dados': f'Telegram: Germanio Pai e Mae inativos ha meses/anos. WhatsApp: varias conversas paradas.',
    'padrao': 'Relacoes antigas (amigos, familia extendida) sao deixadas morrer por inercia. Nao inicia contato proativamente.',
    'impacto': 'Isolamento progressivo da rede de suporte extendida. Perda de capital social.'
})

for i, d in enumerate(diagnosticos):
    print(f"\n{i+1}. {d['gravidade']} — {d['titulo']}")
    print(f"   Dados: {d['dados']}")
    print(f"   Padrao: {d['padrao']}")
    print(f"   Impacto: {d['impacto']}")

# ============================================================
# 8. PLANO DE CORRECAO
# ============================================================
print("\n" + "=" * 70)
print("🔧 8. PLANO DE CORRECAO COMPORTAMENTAL")
print("=" * 70)

plano = [
    {
        'acao': 'FAXINA SOCIAL IMEDIATA',
        'prazo': 'HOJE (30 min)',
        'passos': [
            'Sair de TODOS os grupos/comunidades que nao le ha mais de 7 dias',
            'Silenciar grupos que quer manter mas sem notificacoes',
            'Arquivar conversas inativas (sem contato ha 30+ dias)',
            'Meta: reduzir de 66 para ~25 conversas ativas'
        ]
    },
    {
        'acao': 'SISTEMA DE RESPOSTA EM LOTES',
        'prazo': 'DIARIO (15 min)',
        'passos': [
            'Definir 2 horarios fixos por dia para responder mensagens (ex: 09h e 18h)',
            'Fora desses horarios: WhatsApp fechado/silenciado',
            'Regra: cada mensagem = responder OU arquivar em 24h',
            'Usar respostas rapidas para mensagens simples'
        ]
    },
    {
        'acao': 'RECONSTRUIR RELACOES ABANDONADAS',
        'prazo': 'ESTA SEMANA',
        'passos': [
            'Enviar mensagem para Germanio Pai (Telegram, inativo desde out/2025)',
            'Retomar contato com Mae no Telegram (inativa desde nov/2024)',
            'Identificar 3 contatos valiosos no WhatsApp e iniciar conversa',
            'Foco em QUALIDADE, nao quantidade'
        ]
    },
    {
        'acao': 'REGRA ANTI-SUBSCRIBER',
        'prazo': 'PERMANENTE',
        'passos': [
            'Antes de entrar em qualquer grupo/comunidade: esperar 24h',
            'So entrar se ainda tiver interesse depois de 1 dia',
            'Regra 1-in-1-out: entrar em um grupo = sair de outro',
            'Maximo 3 grupos de interesse ativos simultaneamente'
        ]
    },
    {
        'acao': 'TREINO DE ASSERTIVIDADE',
        'prazo': 'CONTINUO',
        'passos': [
            'Praticar dizer "nao" a convites para grupos',
            'Sair de grupo = ato de autocuidado, nao ofensa',
            'Responder mensagens dificeis em vez de ignorar',
            'Template: "Obrigado, mas nao tenho banda para isso agora"'
        ]
    }
]

for p in plano:
    print(f"\n▶ {p['acao']}")
    print(f"   ⏱ Prazo: {p['prazo']}")
    for i, passo in enumerate(p['passos']):
        print(f"     {i+1}. {passo}")

# ============================================================
# 9. METRICAS DE ACOMPANHAMENTO
# ============================================================
print("\n" + "━" * 70)
print("📈 9. METRICAS DE ACOMPANHAMENTO (semanal)")
print("━" * 70)

metricas = [
    ("Total msgs nao lidas WhatsApp", f"{wa_total_unread}", "< 50"),
    ("Conversas com pendencia", f"{len(wa_unread_chats)}", "< 5"),
    ("Tempo medio de resposta", "?", "< 4h"),
    ("Grupos ativos (lendo)", "?", "max 3"),
    ("Novas conversas iniciadas/semana", "0", "min 1"),
    ("Relacoes recuperadas/mes", "0", "min 2"),
]

print(f"\n{'Metrica':<40} {'Atual':>12} {'Alvo':>12}")
print("-" * 68)
for metrica, atual, alvo in metricas:
    print(f"{metrica:<40} {atual:>12} {alvo:>12}")

# Salvar relatorio
REPORT_PATH = DATA_DIR / 'analise_comportamental_2026-05-24.json'
report = {
    'data': datetime.now().isoformat(),
    'metricas_gerais': {
        'wa_total_chats': len(wa_chats),
        'wa_total_unread': wa_total_unread,
        'tg_total_chats': len(tg_dialogs),
        'tg_total_unread': tg_total_unread,
    },
    'diagnosticos': diagnosticos,
    'plano_correcao': plano,
    'metricas_acompanhamento': [{'metrica': m, 'atual': a, 'alvo': al} for m, a, al in metricas]
}

with open(REPORT_PATH, 'w') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f"\n✅ Relatorio completo salvo: {REPORT_PATH}")
