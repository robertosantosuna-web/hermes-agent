#!/usr/bin/env python3
"""
Brain Gateway — Canal Direto Usuário ↔ Cérebro
================================================
Entrada independente: usuário fala direto com o cérebro sem passar pelo Agent.
O Agent assimila depois via neural_sync.json no ciclo de sincronismo.

Arquitetura:
  User → /brain msg → brain_gateway_inbox.json
                         ↓ (cron a cada 2 min)
                    Brain Gateway processa
                         ↓
              ┌─ brain_outbox.json (resposta pro usuário)
              └─ neural_sync.json  (Agent assimila depois)

Comandos:
  brain_gateway.py process         → processa inbox pendente
  brain_gateway.py sync [N]       → exporta últimas N interações pra neural_sync
  brain_gateway.py stats          → status do gateway
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERMES = Path.home() / ".hermes"
SCRIPTS = HERMES / "scripts"
GATEWAY_INBOX = HERMES / "brain_gateway_inbox.json"
NEURAL_SYNC = HERMES / "neural_sync.json"
NN_ENGINE = SCRIPTS / "nn_engine.py"


def _now():
    return datetime.now(timezone.utc).isoformat()


def _load(path):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            pass
    return {"messages": []}


def _save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ═══════════════════════════════════════════════
# Brain Knowledge Base (local, zero tokens)
# ═══════════════════════════════════════════════

def _load_knowledge():
    """Load brain's current knowledge for answering questions."""
    knowledge = {"topics": {}, "status": {}}
    
    # Load brain context
    ctx_file = HERMES / "brain_context.json"
    if ctx_file.exists():
        ctx = json.loads(ctx_file.read_text())
        knowledge["status"]["modules"] = ctx.get("modules_status", {})
        knowledge["status"]["forex"] = ctx.get("forex_status", {})
        knowledge["topics"]["chart_patterns"] = ctx.get("chart_patterns", {})
    
    # Load weekly bias
    bias_file = HERMES / "forex" / "weekly_bias.json"
    if bias_file.exists():
        knowledge["topics"]["weekly_bias"] = json.loads(bias_file.read_text())
    
    # Load FVG trend
    fvg_file = HERMES / "forex" / "fvg_trend.json"
    if fvg_file.exists():
        knowledge["topics"]["fvg_trend"] = json.loads(fvg_file.read_text())
    
    # Load NN status
    nn_result = subprocess.run(
        ["python3", str(NN_ENGINE), "status"],
        capture_output=True, text=True, timeout=10
    )
    knowledge["status"]["neural"] = nn_result.stdout[:1000] if nn_result.returncode == 0 else "offline"
    
    # Load brain knowledge base (pillars, skills, memory, capabilities)
    kb_file = HERMES / "brain_knowledge_base.json"
    if kb_file.exists():
        kb = json.loads(kb_file.read_text())
        knowledge["pillars"] = kb.get("pillars", {})
        knowledge["skills_summary"] = kb.get("skills_summary", {})
        knowledge["capabilities"] = kb.get("capabilities", {})
        knowledge["memory"] = kb.get("memory", {})
        knowledge["current_context"] = kb.get("current_context", {})
        knowledge["identity"] = kb.get("identity", {})
        knowledge["self_development"] = kb.get("self_development", {})
        knowledge["learned_qa"] = kb.get("learned_qa", [])
    
    return knowledge


def _brain_process(message):
    """
    Processa mensagem do usuário usando conhecimento local do cérebro.
    ZERO tokens de LLM — apenas consulta a knowledge base.
    """
    import re, sys, subprocess
    knowledge = _load_knowledge()
    msg_lower = message.lower()
    response_parts = []
    topics_touched = []
    
    # ── Status dos módulos ──
    if any(k in msg_lower for k in ["status", "modulo", "módulo", "como está", "saúde"]):
        mods = knowledge["status"].get("modules", {})
        # Check module activity via cron jobs
        active = sum(1 for v in mods.values() if isinstance(v, dict))
        total = len(mods)
        response_parts.append(f"🧠 Módulos: {total} registrados")
        for name, st in mods.items():
            # Try to check if the cron job is enabled
            icon = "🟢" if isinstance(st, dict) else "⚪"
            response_parts.append(f"  {icon} {name}")
        topics_touched.append("modules_status")
    
    # ── Forex / Viés semanal ──
    if any(k in msg_lower for k in ["forex", "viés", "vies", "semanal", "semana", "bias", "trading"]):
        bias = knowledge["topics"].get("weekly_bias", {})
        if bias:
            response_parts.append(f"\n💱 Viés Semanal ({bias.get('week_start', '?')} a {bias.get('week_end', '?')}):")
            response_parts.append(f"  {bias.get('summary', '?')}")
            for pair, direction in bias.get("pairs", {}).items():
                response_parts.append(f"  • {pair}: {direction}")
            for evt in bias.get("risk_events", [])[:3]:
                response_parts.append(f"  📅 {evt['date']}: {evt['event']}")
        else:
            response_parts.append("💱 Viés semanal: não disponível")
        topics_touched.append("weekly_bias")
    
    # ── FVG / Padrões ──
    if any(k in msg_lower for k in ["fvg", "gap", "padrão", "padrao", "chart", "grafico", "volatil"]):
        fvg = knowledge["topics"].get("fvg_trend", {})
        if fvg:
            response_parts.append("\n📊 FVG Trend:")
            for pair, data in fvg.get("pairs", {}).items():
                response_parts.append(
                    f"  • {pair}: {data['fvg_count']} FVGs, gap médio {data['gap_avg_pips']}p "
                    f"({'📈' if data.get('trend') == 'rising' else '📉'})"
                )
        topics_touched.append("fvg_trend")
    
    # ── Neural Network ──
    if any(k in msg_lower for k in ["neural", "rede", "sinapse", "neuronio", "neurônio"]):
        nn = knowledge["status"].get("neural", "offline")
        response_parts.append(f"\n🔗 Redes Neurais:\n{nn[:500]}")
        topics_touched.append("neural_status")
    
    # ── IDENTIDADE / HIERARQUIA (só sobre o próprio cérebro) ──
    if any(k in msg_lower for k in ["quem é você", "quem e voce", "quem és", "sua identidade", "sua hierarquia", "seu chefe", "teu chefe"]):
        identity = knowledge.get("identity", {})
        if identity:
            response_parts.append(f"\n🪪 {identity.get('name', 'Cérebro da ENTIDADE')}")
            response_parts.append(f"   Entidade: {identity.get('entity', '')[:100]}")
            hier = identity.get('hierarchy', {})
            response_parts.append("\n📊 HIERARQUIA:")
            for level, desc in hier.items():
                response_parts.append(f"  {desc[:120]}")
            response_parts.append(f"\n📋 Função: {identity.get('role', '')[:150]}")
            principles = identity.get('principles', [])
            if principles:
                response_parts.append(f"\n📜 Princípios ({len(principles)}):")
                for p in principles[:4]:
                    response_parts.append(f"  • {p[:100]}")
        topics_touched.append("identity")
    
    # ── AUTO-DESENVOLVIMENTO ──
    if any(k in msg_lower for k in ["auto desenvolvimento", "auto-desenvolvimento", "self development", "aprendizado", "aprender", "evoluir", "evolução", "evolucao", "melhorar"]):
        sd = knowledge.get("self_development", {})
        if sd:
            response_parts.append(f"\n🧠 AUTO-DESENVOLVIMENTO: {sd.get('status', '?')}")
            cycles = sd.get('cycles', {})
            response_parts.append("\n⏱️ Ciclos de aprendizado:")
            for name, desc in cycles.items():
                response_parts.append(f"  • {desc[:120]}")
            caps = sd.get('learning_capabilities', [])
            response_parts.append(f"\n📚 Capacidades ({len(caps)}):")
            for c in caps[:5]:
                response_parts.append(f"  • {c[:110]}")
            limits = sd.get('limitations', [])
            response_parts.append(f"\n⚠️ Limitações ({len(limits)}):")
            for l in limits[:3]:
                response_parts.append(f"  • {l[:100]}")
        topics_touched.append("self_development")
    
    # ── EMAIL ──
    if any(k in msg_lower for k in ["email", "e-mail", "gmail", "outlook", "correio", "mensagem"]):
        response_parts.append("\n📧 EMAIL:")
        response_parts.append("  Não tenho acesso direto a emails — isso é função do Agente (Córtex).")
        response_parts.append("  O Agente gerencia:")
        response_parts.append("  • Gmail pessoal (robertosantos.una@gmail.com) via IMAP")
        response_parts.append("  • Outlook GOL e Outlook pessoal via CDP")
        response_parts.append("  • Monitoramento: monitor.py a cada 5 min")
        response_parts.append("  Peça ao Agente para verificar seus emails.")
        topics_touched.append("email")
    
    # ── COTAÇÃO FOREX EM TEMPO REAL (MT5) ──
    if any(k in msg_lower for k in ["cotação", "cotacao", "preço", "preco", "câmbio", "cambio", "dólar", "dolar", "iene", "libra"]):
        pairs_map = {
            'audusd': 'AUDUSD', 'aud': 'AUDUSD',
            'eurusd': 'EURUSD', 'euro dólar': 'EURUSD', 'euro dolar': 'EURUSD', 'euro': 'EURUSD',
            'gbpusd': 'GBPUSD', 'libra dólar': 'GBPUSD', 'libra dolar': 'GBPUSD', 'libra': 'GBPUSD',
            'usdjpy': 'USDJPY', 'dólar iene': 'USDJPY', 'dolar iene': 'USDJPY', 'iene': 'USDJPY',
            'dólar': 'USDJPY', 'dolar': 'USDJPY', 'dólar hoje': 'USDJPY',
        }
        pair = 'USDJPY'  # default
        for k, v in pairs_map.items():
            if k in msg_lower:
                pair = v
                break
        
        try:
            import MetaTrader5 as mt5
            mt5_initialized = mt5.initialize()
            if mt5_initialized:
                symbol_info = mt5.symbol_info(pair)
                tick = mt5.symbol_info_tick(pair)
                if tick and symbol_info:
                    bid = tick.bid
                    ask = tick.ask
                    spread = round((ask - bid) / symbol_info.point, 1) if symbol_info.point else 0
                    response_parts.append(f"\n💱 {pair} (MT5 IC Markets):")
                    response_parts.append(f"  Bid: {bid:.5f}")
                    response_parts.append(f"  Ask: {ask:.5f}")
                    response_parts.append(f"  Spread: {spread} pontos")
                    response_parts.append(f"  📡 Fonte: MT5 IC Markets (tempo real)")
                else:
                    response_parts.append(f"  ⚠️ {pair}: sem dados de tick (mercado pode estar fechado)")
                mt5.shutdown()
            else:
                response_parts.append(f"  ❌ MT5 não disponível (erro ao inicializar)")
        except ImportError:
            response_parts.append(f"  ❌ MetaTrader5 não instalado")
        except Exception as e:
            response_parts.append(f"  ❌ Erro ao buscar cotação MT5: {str(e)[:100]}")
        topics_touched.append("forex_quote")
    
    # ── WEB SEARCH ── (busca na internet)
    if any(k in msg_lower for k in ["/search", "buscar", "pesquisar", "procure", "procura", "internet"]):
        # Extrair termo de busca (após o comando)
        search_term = message
        for cmd in ["/search", "buscar", "pesquisar", "procure", "procura"]:
            if cmd in msg_lower:
                idx = msg_lower.find(cmd) + len(cmd)
                search_term = message[idx:].strip()
                break
        
        if search_term and len(search_term) > 2:
            response_parts.append(f"🔍 Buscando: \"{search_term}\"...")
            try:
                import subprocess, sys
                r = subprocess.run(
                    [sys.executable, str(SCRIPTS / "brain_web.py"), "search", search_term],
                    capture_output=True, text=True, timeout=20
                )
                if r.returncode == 0:
                    web_results = json.loads(r.stdout)
                    response_parts.append(f"\n🌐 Resultados da internet ({len(web_results)}):")
                    for wr in web_results[:5]:
                        if 'error' in wr: continue
                        response_parts.append(f"\n📰 {wr.get('title', '?')[:120]}")
                        if wr.get('snippet'):
                            response_parts.append(f"   {wr['snippet'][:200]}")
                        response_parts.append(f"   🔗 {wr.get('url', '?')[:100]}")
                else:
                    response_parts.append("❌ Erro na busca")
            except Exception as e:
                response_parts.append(f"❌ Erro: {str(e)[:100]}")
        else:
            response_parts.append("❓ Use: /search <termo> — ex: /search Kevin Warsh Fed")
        topics_touched.append("web_search")
    
    # ── Q&A APRENDIDAS ── (experiência acumulada)
    learned = knowledge.get("learned_qa", [])
    if learned:
        # Buscar pergunta similar nas aprendidas
        for qa in reversed(learned):
            q_words = set(qa.get("question", "").lower().split())
            m_words = set(msg_lower.split())
            overlap = len(q_words & m_words)
            if overlap >= 3 and overlap / max(len(q_words), 1) > 0.3:
                response_parts.append(f"\n📚 Já respondi algo parecido antes:\n{qa.get('response', '')[:400]}")
                topics_touched.append("learned_qa")
                break
    
    # ── Chart Patterns ──
    if any(k in msg_lower for k in ["chart pattern", "padrão gráfico"]):
        cp = knowledge["topics"].get("chart_patterns", {})
        response_parts.append(f"\n📈 Chart Patterns: {cp.get('patterns_detected', '?')} detectados em 7 pares")
        topics_touched.append("chart_patterns")
    
    # ── PILARES ── (conhecimento completo do agente)
    if any(k in msg_lower for k in ["pilar", "pilares", "pillar", "pillars"]):
        pillars = knowledge.get("pillars", {})
        response_parts.append(f"\n🏛️ PILARES DA ENTIDADE ({len(pillars)} pilares):")
        for key, p in pillars.items():
            response_parts.append(f"\n  📌 {p['name']}")
            response_parts.append(f"     Meta: {p['goal'][:120]}")
            comps = p.get('components', {})
            for cname, cdesc in list(comps.items())[:3]:
                desc = cdesc[:80] if isinstance(cdesc, str) else cdesc.get('goal', str(cdesc))[:80]
                response_parts.append(f"     • {cname}: {desc}")
        topics_touched.append("pillars")
    
    # ── Skills ──
    if any(k in msg_lower for k in ["skill", "skills", "habilidade", "capacidade"]):
        skills = knowledge.get("skills_summary", {})
        response_parts.append(f"\n🛠️ SKILLS ({skills.get('total', '?')} total):")
        for cat, names in skills.get("categories", {}).items():
            response_parts.append(f"  • {cat}: {', '.join(names[:3])}...")
        topics_touched.append("skills")
    
    # ── Capacidades ──
    if any(k in msg_lower for k in ["capacidade", "capability", "o que faz", "funcionalidade"]):
        caps = knowledge.get("capabilities", {})
        response_parts.append(f"\n⚡ CAPACIDADES ({len(caps)} áreas):")
        for name, desc in caps.items():
            response_parts.append(f"  • {name}: {desc[:100]}")
        topics_touched.append("capabilities")
    
    # ── Memória ──
    if any(k in msg_lower for k in ["memória", "memoria", "memory", "lembrar", "lembra"]):
        mem = knowledge.get("memory", {})
        response_parts.append("\n🧠 MEMÓRIA:")
        response_parts.append(f"  Usuário: {mem.get('user', '?')[:80]}")
        response_parts.append(f"  Conta: {mem.get('forex_account', '?')}")
        response_parts.append(f"  Ferramentas: {mem.get('tools', '?')[:120]}")
        aps = mem.get('anti_patterns_learned', [])
        if aps:
            response_parts.append(f"  Anti-padrões: {len(aps)} aprendidos")
        topics_touched.append("memory")
    
    # ── Contexto atual ──
    if any(k in msg_lower for k in ["contexto", "atual", "agora", "hoje", "semana"]):
        ctx = knowledge.get("current_context", {})
        response_parts.append("\n📍 CONTEXTO ATUAL:")
        for k, v in ctx.items():
            response_parts.append(f"  • {k}: {str(v)[:120]}")
        topics_touched.append("context")
    
    # ── Saúde / Mental ──
    if any(k in msg_lower for k in ["saúde", "saude", "mental", "health", "bem-estar", "habito"]):
        hp = knowledge.get("pillars", {}).get("health", {})
        mb = knowledge.get("pillars", {}).get("mental_behavioral", {})
        response_parts.append("\n💚 SAÚDE & MENTAL:")
        if hp:
            for cname, cdesc in hp.get("components", {}).items():
                desc = cdesc[:80] if isinstance(cdesc, str) else str(cdesc)[:80]
                response_parts.append(f"  • {cname}: {desc}")
        if mb:
            response_parts.append(f"  • General Orders: 7 regras inegociáveis")
            response_parts.append(f"  • Frameworks: Extreme Ownership, 40% Rule, OODA Loop...")
        topics_touched.append("health")
    
    # ── Financeiro ──
    if any(k in msg_lower for k in ["dinheiro", "renda", "ganho", "lucro", "receita", "freela"]):
        fp = knowledge.get("pillars", {}).get("financial", {})
        response_parts.append("\n💰 FINANCEIRO:")
        for cname, cdesc in fp.get("components", {}).items():
            desc = cdesc[:100] if isinstance(cdesc, str) else str(cdesc)[:100]
            response_parts.append(f"  • {cname}: {desc}")
        topics_touched.append("financial")
    
    # ── Fallback: raciocínio via LLM local (Ollama) ──
    # Se NENHUM handler de keyword respondeu OU se a pergunta é conversacional,
    # usar Ollama para raciocinar. Handlers diretos (identidade, status, forex quote, 
    # busca web, email, cotação) NÃO são substituídos por raciocínio.
    DIRECT_HANDLERS = {'identity', 'modules_status', 'forex_quote', 'web_search', 'email'}
    is_direct = bool(topics_touched and set(topics_touched) & DIRECT_HANDLERS)
    
    conversational = not is_direct and any(k in msg_lower for k in [
        "?", "como", "por que", "porque", "qual", "quando", "onde", "devo", 
        "deveria", "pode", "posso", "melhor", "pior", "certo", "errado",
        "vale a pena", "compensa", "sugestão", "dica", "opinião", "conselho"
    ])
    
    if not response_parts or conversational:
        # Se teve keyword match, usar como contexto enriquecido
        keyword_context = "\n".join(response_parts) if response_parts else ""
        
        # 🌐 Busca web automática para perguntas que precisam de info atual
        web_context = ""
        needs_web = any(k in msg_lower for k in [
            "quem é", "o que é", "quem foi", "notícia", "noticia", "hoje", 
            "hoje em dia", "atualmente", "preço", "preco", "cotação", "cotacao",
            "última", "ultima", "recente", "aconteceu"
        ])
        if needs_web:
            try:
                # Limpar pergunta para busca: remover palavras interrogativas
                clean_query = re.sub(r'\b(quem é|quem e|o que é|o que e|qual|quando|onde|como|por que|porque)\b', '', message, flags=re.IGNORECASE).strip()
                if not clean_query:
                    clean_query = message[:200]
                
                r = subprocess.run(
                    [sys.executable, str(SCRIPTS / "brain_web.py"), "search", clean_query[:200]],
                    capture_output=True, text=True, timeout=20
                )
                if r.returncode == 0:
                    web_data = json.loads(r.stdout)
                    web_parts = []
                    for wr in web_data[:3]:
                        if 'error' in wr: continue
                        web_parts.append(f"- {wr.get('title', '')}: {wr.get('snippet', '')[:200]}")
                    if web_parts:
                        web_context = "Informação atual da internet:\n" + "\n".join(web_parts)
            except: pass
        
        reason_response = _brain_reason(message, knowledge, keyword_context, web_context)
        
        if conversational:
            # Substituir resposta de keyword pela de raciocínio
            response_parts = [reason_response]
        else:
            response_parts.append(reason_response)
        
        topics_touched.append("reasoning")
    
    return "\n".join(response_parts), topics_touched


# ═══════════════════════════════════════════════
# Raciocínio via Ollama (fallback quando keyword não cobre)
# ═══════════════════════════════════════════════

def _brain_reason(question, knowledge, keyword_context="", web_context=""):
    """Usa Ollama local para raciocinar. Inclui busca web como contexto adicional."""
    import urllib.request
    
    # Construir contexto compacto do conhecimento atual
    ctx_parts = []
    
    identity = knowledge.get("identity", {})
    if identity:
        ctx_parts.append(f"Identidade: {identity.get('name', 'Cérebro da ENTIDADE')}. "
                        f"Hierarquia: Roberto → Agente (Córtex) → Cérebro. "
                        f"Função: {identity.get('role', '')[:200]}")
    
    ctx = knowledge.get("current_context", {})
    if ctx:
        ctx_parts.append(f"Contexto atual: {ctx.get('forex_week', '')[:150]}")
    
    pillars = knowledge.get("pillars", {})
    if pillars:
        p_list = ", ".join(p.get('name', '') for p in pillars.values())
        ctx_parts.append(f"Pilares: {p_list}")
    
    # Adicionar contexto de keyword match (dados relevantes)
    if keyword_context:
        ctx_parts.append(f"\nDados relevantes encontrados:\n{keyword_context[:500]}")
    
    # 🌐 Resultados da internet
    if web_context:
        ctx_parts.append(f"\n{web_context[:800]}")
    
    # Perfil do Roberto (para respostas personalizadas)
    profile = knowledge.get("current_context", {}).get("roberto_profile", "")
    if profile:
        ctx_parts.append(f"\nPerfil de Roberto: {profile}")
    
    insights = knowledge.get("roberto_insights", {})
    if insights:
        insight_text = "; ".join(f"{k}: {v[:100]}" for k, v in list(insights.items())[:4])
        ctx_parts.append(f"Insights: {insight_text}")
    
    # Montar prompt
    system_ctx = "\n".join(ctx_parts)
    prompt = (
        f"Você é o Cérebro da ENTIDADE, camada operacional digital de Roberto. "
        f"Subordinado ao Agente (Córtex) e a Roberto.\n\n"
        f"{system_ctx}\n\n"
        f"Roberto perguntou: \"{question}\"\n\n"
        f"REGRAS PARA RESPONDER:\n"
        f"1. Use APENAS os dados fornecidos acima. NÃO invente informações.\n"
        f"2. Se houver 'Informação atual da internet', use-a como fonte primária.\n"
        f"3. Se não tiver dados suficientes, seja honesto e sugira perguntar ao Agente.\n"
        f"4. Responda em português, de forma CONCISA e DIRETA (máximo 4 frases).\n"
        f"5. NUNCA invente datas, nomes ou números que não estejam no contexto."
    )
    
    try:
        data = json.dumps({
            "model": "qwen2.5:3b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 200,
                "stop": ["\n\n\n", "---"]
            }
        }).encode()
        
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=45) as resp:
            result = json.loads(resp.read())
            response = result.get("response", "").strip()
            
            if response:
                return f"💭 {response}\n\n_(resposta via raciocínio local, sem tokens do Agente)_"
    except Exception as e:
        pass
    
    # Fallback final se Ollama falhar
    return (
        "❓ Não entendi completamente. Tente:\n"
        "• status — saúde dos módulos\n"
        "• forex — análise semanal\n"
        "• pilares — estrutura completa\n"
        "• auto desenvolvimento — meus ciclos\n"
        "Ou pergunte ao Agente (Córtex) que tem mais capacidade de raciocínio."
    )


# ═══════════════════════════════════════════════
# Aprendizado Contínuo — Expande KB com cada interação
# ═══════════════════════════════════════════════

def _brain_learn(question, response, topics):
    """Aprende com cada interação: salva Q&A no knowledge base."""
    kb_file = HERMES / "brain_knowledge_base.json"
    if not kb_file.exists():
        return
    
    try:
        kb = json.loads(kb_file.read_text())
        qa_store = kb.setdefault("learned_qa", [])
        
        # Evitar duplicatas
        q_lower = question.lower()[:100]
        for existing in qa_store[-50:]:
            if existing.get("question", "").lower()[:80] == q_lower[:80]:
                return  # Já existe
        
        qa_store.append({
            "question": question[:200],
            "response": response[:300],
            "topics": topics,
            "learned_at": _now()
        })
        
        # Limitar a 100 Q&A
        kb["learned_qa"] = qa_store[-100:]
        kb_file.write_text(json.dumps(kb, indent=2, ensure_ascii=False))
    except:
        pass

# ═══════════════════════════════════════════════
# Processamento do Inbox
# ═══════════════════════════════════════════════

def process_inbox():
    """Processa mensagens pendentes no inbox do gateway."""
    inbox = _load(GATEWAY_INBOX)
    unread = [m for m in inbox.get("messages", []) if not m.get("read")]
    
    if not unread:
        return {"status": "empty", "processed": 0}
    
    results = []
    
    for msg in unread:
        try:
            response, topics = _brain_process(msg["content"])
            
            # Enviar resposta via brain_channel
            subprocess.run([
                "python3", str(SCRIPTS / "brain_channel.py"), "respond",
                response, msg["id"]
            ], capture_output=True, timeout=10)
            
            # Sync para neural_sync.json (Agent assimila depois)
            sync_entry = {
                "timestamp": _now(),
                "user_message": msg["content"][:300],
                "brain_response": response[:300],
                "topics": topics,
                "message_id": msg["id"],
            }
            _append_to_neural_sync(sync_entry)
            
            # Marcar como lida
            msg["read"] = True
            msg["processed_at"] = _now()
            msg["topics"] = topics
            
            results.append({"id": msg["id"], "topics": topics, "response_len": len(response)})
            
        except Exception as e:
            msg["read"] = True
            msg["error"] = str(e)[:100]
            results.append({"id": msg["id"], "error": str(e)[:100]})
    
    _save(GATEWAY_INBOX, inbox)
    
    return {"status": "ok", "processed": len(results), "results": results}


# ═══════════════════════════════════════════════
# Neural Sync — Agent Assimilation
# ═══════════════════════════════════════════════

def _append_to_neural_sync(entry):
    """Append interaction to neural sync file for Agent assimilation."""
    sync = _load(NEURAL_SYNC)
    if "interactions" not in sync:
        sync["interactions"] = []
    sync["interactions"].append(entry)
    # Keep last 200
    sync["interactions"] = sync["interactions"][-200:]
    sync["last_updated"] = _now()
    _save(NEURAL_SYNC, sync)
    
    # Also feed directly to NN-Shared
    try:
        subprocess.run([
            "python3", str(NN_ENGINE), "learn", "shared",
            f"User asked brain: {entry['user_message'][:200]}. "
            f"Brain responded about: {','.join(entry['topics'])}"
        ], capture_output=True, timeout=10)
    except:
        pass


def sync_to_agent(n=10):
    """Export recent interactions for Agent to read."""
    sync = _load(NEURAL_SYNC)
    interactions = sync.get("interactions", [])[-n:]
    return {
        "status": "ok",
        "interactions": interactions,
        "total": len(sync.get("interactions", [])),
        "last_sync": sync.get("last_updated"),
    }


def stats():
    """Gateway statistics."""
    inbox = _load(GATEWAY_INBOX)
    sync = _load(NEURAL_SYNC)
    
    total_inbox = len(inbox.get("messages", []))
    unread = sum(1 for m in inbox.get("messages", []) if not m.get("read"))
    total_sync = len(sync.get("interactions", []))
    
    return {
        "inbox_total": total_inbox,
        "inbox_unread": unread,
        "neural_sync_entries": total_sync,
        "last_sync": sync.get("last_updated", "never"),
    }


# ═══════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        s = stats()
        print("🧠 Brain Gateway")
        print(f"   Inbox: {s['inbox_total']} total, {s['inbox_unread']} pendentes")
        print(f"   Neural Sync: {s['neural_sync_entries']} interações")
        print(f"   Last sync: {s['last_sync']}")
        print()
        print("   Comandos: process | sync [N] | stats")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "process":
        result = process_inbox()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif cmd == "sync":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        result = sync_to_agent(n)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif cmd == "stats":
        print(json.dumps(stats(), indent=2))
    
    else:
        print(f"Unknown: {cmd}")
