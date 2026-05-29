#!/usr/bin/env python3
"""
Córtex Insular + Pré-Frontal Social — Agente de Evolução Pessoal Contínua
═══════════════════════════════════════════════════════════════════════════

Função: Análise mental, emocional e social de Roberto.
Ajuda na evolução contínua como pessoa, pai, profissional e indivíduo.

Este agente:
- Monitora estado mental (humor, energia, foco, ansiedade)
- Analisa interações sociais (WhatsApp, Telegram, emails)
- Detecta padrões comportamentais (gatilhos, hábitos, ciclos)
- Sugere melhorias baseadas em dados reais
- Conecta com MindCoach para dados de saúde

Ciclo: a cada 2 horas + on-demand quando detecta mudanças
"""

import json, os, sys, time, re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

H = Path.home() / '.hermes'
BRAIN = H / 'brain'

# ═══ FONTES DE DADOS ═══
MINCOACH_DATA = H / 'mindcoach' / 'data' / 'latest.json'
MINCOACH_MANUAL = H / 'mindcoach' / 'manual_inputs.json'
TELEGRAM_EXPORT = H / 'scripts' / 'social_extract_telegram.py'
WHATSAPP_EXPORT = H / 'scripts' / 'social_extract_whatsapp.py'
SOCIAL_DATA = H / 'social_data.json'  # Cache de análises sociais
MENTAL_STATE_FILE = H / 'brain' / 'mental_state.json'
INSTAGRAM_CHECK = True  # Habilitar monitoramento Instagram via navegador interno

# ═══ PERFIL DE ROBERTO ═══
ROBERTO_PROFILE = {
    "name": "Roberto Rodrigues dos Santos",
    "age": 32,
    "archetype": "O Construtor Sobrevivente",
    "context": {
        "family": "Divorciado, 2 filhas (Heloisa, Isadora), mora com pai e irmã",
        "work": "Técnico de Manutenção de Aeronaves - GOL (promoção aprovada, início Jul/2026)",
        "income": "R$ 3.671,17 (após promoção)",
        "goals": ["Autonomia financeira via forex/freelas", "Evolução pessoal contínua", "Ser melhor pai"],
        "challenges": ["Espaço pessoal limitado", "Equilíbrio trabalho/família/forex", "Disciplina emocional"]
    }
}

# ═══ ANÁLISE MENTAL ═══

def analyze_mental_state():
    """Analisa estado mental a partir de dados disponíveis."""
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": {},
        "trends": {},
        "insights": [],
        "recommendations": []
    }
    
    # 1. Dados do MindCoach (saúde, sono, humor)
    if MINCOACH_DATA.exists():
        try:
            mc = json.loads(MINCOACH_DATA.read_text())
            state["mindcoach"] = {
                "last_update": mc.get("timestamp", "?"),
                "mood": mc.get("mood"),
                "energy": mc.get("energy"),
                "sleep_hours": mc.get("sleep_hours"),
                "stress": mc.get("stress"),
                "anxiety": mc.get("anxiety")
            }
        except:
            pass
    
    # 2. Dados manuais (inputs do Roberto)
    if MINCOACH_MANUAL.exists():
        try:
            manual = json.loads(MINCOACH_MANUAL.read_text())
            if isinstance(manual, list):
                recent = [m for m in manual if _is_recent(m.get("timestamp", ""), hours=48)]
                state["manual_inputs"] = len(recent)
        except:
            pass
    
    # 3. Análise de padrão de atividade (horários)
    hour = datetime.now().hour
    if hour < 6:
        state["recommendations"].append("🌙 Madrugada — considere dormir. Recuperação é essencial para decisões de trading.")
    elif hour < 8:
        state["recommendations"].append("🌅 Bom momento para planejar o dia. Mente fresca = melhores decisões.")
    elif 20 <= hour < 23:
        state["recommendations"].append("🌆 Final do dia — bom momento para reflexão, não para trading agressivo.")
    
    # 4. Dias desde última análise
    state["day_of_week"] = datetime.now().strftime("%A")
    state["week_number"] = datetime.now().isocalendar()[1]
    
    return state


def analyze_social_patterns():
    """Analisa interações sociais e detecta padrões."""
    patterns = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "contacts": defaultdict(int),
        "sentiment": {"positive": 0, "neutral": 0, "negative": 0},
        "response_times": [],
        "insights": [],
        "relationships_to_nurture": [],
        "boundaries_to_set": []
    }
    
    # 1. Analisar WhatsApp (se dados disponíveis)
    wa_data = _load_social_data("whatsapp")
    if wa_data:
        for msg in wa_data:
            sender = msg.get("sender", "")
            if sender and sender != "Roberto":
                patterns["contacts"][sender] += 1
            sentiment = _analyze_sentiment(msg.get("text", ""))
            patterns["sentiment"][sentiment] += 1
    
    # 2. Analisar Telegram
    tg_data = _load_social_data("telegram")
    if tg_data:
        for msg in tg_data:
            sender = msg.get("sender", "")
            if sender and sender != "Roberto":
                patterns["contacts"][sender] += 1
            sentiment = _analyze_sentiment(msg.get("text", ""))
            patterns["sentiment"][sentiment] += 1
    
    # 3. Analisar Instagram (via navegador interno :9226)
    if INSTAGRAM_CHECK:
        try:
            from instagram_monitor import load_instagram_data, analyze_social_health
            ig_health = analyze_social_health()
            patterns["instagram"] = {
                "sessions_today": ig_health.get("today_sessions", 0),
                "avg_session_min": ig_health.get("avg_session_minutes", 0),
                "social_score": ig_health.get("social_score", 0),
                "usage_pattern": ig_health.get("usage_pattern", "unknown"),
                "notifications": ig_health.get("total_notifications", 0)
            }
            if ig_health.get("insights"):
                patterns["insights"].extend(ig_health["insights"])
            if ig_health.get("recommendations"):
                for rec in ig_health["recommendations"]:
                    if rec not in patterns["insights"]:
                        patterns["insights"].append(f"📱 {rec}")
        except ImportError:
            pass
        except Exception as e:
            patterns["instagram"] = {"error": str(e)[:100]}
    
    # 3. Insights sociais
    total_msgs = sum(patterns["sentiment"].values())
    if total_msgs > 0:
        pos_ratio = patterns["sentiment"]["positive"] / total_msgs
        neg_ratio = patterns["sentiment"]["negative"] / total_msgs
        
        if pos_ratio > 0.6:
            patterns["insights"].append("Rede social majoritariamente positiva — bom momento para conexões.")
        if neg_ratio > 0.3:
            patterns["insights"].append("⚠️ Alta proporção de interações negativas. Avalie limites com esses contatos.")
    
    # 4. Contatos para nutrir (top 5)
    top_contacts = sorted(patterns["contacts"].items(), key=lambda x: -x[1])[:5]
    patterns["relationships_to_nurture"] = [c for c, _ in top_contacts]
    
    # 5. Filhas — prioridade automática
    patterns["insights"].append("👨‍👧‍👧 Filhas Heloisa e Isadora — mantenha contato regular. Sua presença é o melhor investimento.")
    
    return patterns


def analyze_evolution_progress():
    """Acompanha progresso de evolução pessoal."""
    progress = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pillars": {},
        "streaks": {},
        "weekly_review": {}
    }
    
    # Pilares de evolução
    pillars = {
        "financeiro": {"goal": "Autonomia financeira", "metric": "forex_pnl", "target": "Renda extra > R$500/mês"},
        "profissional": {"goal": "Transição GOL", "metric": "promoção", "target": "Início Jul/2026", "status": "aprovado"},
        "paternal": {"goal": "Ser melhor pai", "metric": "tempo_qualidade", "target": "Contato diário com filhas"},
        "mental": {"goal": "Estabilidade emocional", "metric": "mindcoach_score", "target": "Score > 7/10"},
        "social": {"goal": "Rede de apoio saudável", "metric": "interações_positivas", "target": "> 60% positivas"},
        "fisico": {"goal": "Saúde e energia", "metric": "sono_exercicio", "target": "Sono > 7h, exercício 3x/semana"}
    }
    
    progress["pillars"] = pillars
    
    # Streaks (sequências)
    progress["streaks"]["forex_consistency"] = "Sistema autônomo ativo desde 28/05"
    progress["streaks"]["learning"] = "Novo agente de evolução criado"
    
    return progress


def generate_daily_affirmation():
    """Gera afirmação diária personalizada baseada no contexto."""
    day = datetime.now().strftime("%A")
    context = ROBERTO_PROFILE["context"]
    
    affirmations = {
        "Monday": "Nova semana, novas oportunidades. Você é O Construtor — cada trade, cada freela, constrói seu futuro.",
        "Tuesday": "Consistência vence intensidade. Pequenos passos diários levam a grandes conquistas.",
        "Wednesday": "Metade da semana. Você já superou desafios maiores que este. Continue construindo.",
        "Thursday": "O mercado recompensa disciplina. Sua preparação técnica é seu diferencial.",
        "Friday": "Foco no fechamento. Celebre as vitórias da semana, aprenda com os desafios.",
        "Saturday": "Dia de recarregar. Suas filhas precisam do pai presente, não do trader estressado.",
        "Sunday": "Planeje a semana com calma. O Construtor que planeja bem, executa melhor."
    }
    
    return affirmations.get(day, "Cada dia é uma nova oportunidade de evolução.")


def detect_growth_opportunities():
    """Detecta oportunidades de crescimento baseado em padrões."""
    opportunities = []
    
    # Verificar consistência do trading
    try:
        trade_log = H / 'forex' / 'trade_log.json'
        if trade_log.exists():
            trades = json.loads(trade_log.read_text()).get('trades', [])
            if len(trades) < 5:
                opportunities.append("📈 Trading: Poucos trades recentes. Considere aumentar oportunidades com critério.")
    except:
        pass
    
    # Verificar MindCoach
    if MINCOACH_DATA.exists():
        try:
            mc = json.loads(MINCOACH_DATA.read_text())
            if mc.get("sleep_hours", 0) < 6:
                opportunities.append("😴 Sono: Abaixo de 6h. Priorize dormir mais — afeta diretamente decisões de trading.")
            if mc.get("stress", 0) > 7:
                opportunities.append("🧘 Stress: Nível alto detectado. Considere pausa de 5min para respirar.")
        except:
            pass
    
    # Sempre incluir
    opportunities.append("📚 Aprendizado: Separar 25min/dia para estudo (forex, aviação, ou desenvolvimento pessoal).")
    
    return opportunities


# ═══ HELPERS ═══

def _is_recent(ts, hours=48):
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return (datetime.now(timezone.utc) - dt).total_seconds() < hours * 3600
    except:
        return False

def _load_social_data(source):
    path = H / f'social_{source}_cache.json'
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            pass
    return []

def _analyze_sentiment(text):
    if not text:
        return "neutral"
    positive = ["obrigado", "valeu", "ótimo", "perfeito", "❤", "😊", "boa", "parabéns", "obrigada"]
    negative = ["não", "nunca", "problema", "triste", "raiva", "😡", "😢", "horrível"]
    text_lower = text.lower()
    pos = sum(1 for w in positive if w in text_lower)
    neg = sum(1 for w in negative if w in text_lower)
    if pos > neg: return "positive"
    if neg > pos: return "negative"
    return "neutral"


# ═══ MAIN ═══

def run():
    print(f"🧠 CÓRTEX INSULAR — Análise de Evolução Pessoal")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # 1. Análise mental
    mental = analyze_mental_state()
    print("😌 ESTADO MENTAL:")
    mc = mental.get("mindcoach", {})
    if mc:
        print(f"   Humor: {mc.get('mood', '?')} | Energia: {mc.get('energy', '?')} | "
              f"Sono: {mc.get('sleep_hours', '?')}h | Stress: {mc.get('stress', '?')}")
    
    for rec in mental.get("recommendations", []):
        print(f"   {rec}")
    
    # 2. Padrões sociais
    social = analyze_social_patterns()
    total = sum(social["sentiment"].values())
    if total > 0:
        print(f"\n👥 SOCIAL ({total} interações):")
        print(f"   Positivas: {social['sentiment']['positive']} | "
              f"Neutras: {social['sentiment']['neutral']} | "
              f"Negativas: {social['sentiment']['negative']}")
    
    for insight in social.get("insights", []):
        print(f"   {insight}")
    
    # 3. Progresso
    progress = analyze_evolution_progress()
    print(f"\n📈 PROGRESSO (6 pilares):")
    for pillar, info in progress["pillars"].items():
        status = info.get("status", "📊")
        print(f"   {pillar}: {info['goal']} — {status}")
    
    # 4. Afirmação do dia
    affirmation = generate_daily_affirmation()
    print(f"\n💫 AFIRMAÇÃO: {affirmation}")
    
    # 5. Oportunidades
    opps = detect_growth_opportunities()
    print(f"\n🌱 OPORTUNIDADES DE CRESCIMENTO:")
    for opp in opps:
        print(f"   {opp}")
    
    # 6. Publicar no Tálamo
    try:
        import thalamus
        
        # Salvar estado mental
        thalamus.update_state("mental_state", mental)
        thalamus.update_state("social_patterns", social)
        thalamus.update_state("evolution_progress", progress)
        
        # Log de insights importantes
        for rec in mental.get("recommendations", []):
            thalamus.log_event("mental_insight", "cortex_insular", {"recommendation": rec})
        
        for insight in social.get("insights", []):
            thalamus.log_event("social_insight", "cortex_insular", {"insight": insight})
        
        # Se algo crítico
        stress_val = mc.get("stress") or 0
        sleep_val = mc.get("sleep_hours") or 0
        
        if stress_val > 8:
            thalamus.raise_alert("warning", "high_stress", 
                               f"Nível de stress elevado: {stress_val}/10", "cortex_insular")
        
        if sleep_val < 4 and sleep_val > 0:
            thalamus.raise_alert("warning", "low_sleep",
                               f"Sono muito baixo: {mc['sleep_hours']}h", "cortex_insular")
        
        print(f"\n✅ Publicado no Tálamo")
    except Exception as e:
        print(f"\n⚠️ Tálamo indisponível: {e}")
    
    # 7. Salvar estado local
    state = {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "mental": mental,
        "social": social,
        "progress": progress,
        "opportunities": opps
    }
    MENTAL_STATE_FILE.write_text(json.dumps(state, indent=2, default=str))
    
    return state


if __name__ == "__main__":
    run()
