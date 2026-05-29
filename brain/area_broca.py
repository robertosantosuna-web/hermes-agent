#!/usr/bin/env python3
"""Área de Broca — Comunicação e Mensagens.
Execução: scan a cada 30 minutos. Coleta mensagens de email (himalaya/monitor),
Telegram (brain_telegram/inbox), e 99Freelas. Prepara rascunhos de respostas
e propostas, publicando tasks pendentes de revisão no Tálamo.

Usa o Tálamo como canal único de publicação.
"""

import json
import os
import re
import sys
import subprocess
from datetime import datetime, timezone

# ── path setup ──────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.expanduser("~/.hermes/brain"))
import thalamus

# ── constants ───────────────────────────────────────────────────────────────
BROCA_SOURCE = "area_broca"
FAILURE_LOG_PATH = os.path.expanduser("~/.hermes/failure_log.json")
INBOX_PATH = os.path.expanduser("~/.hermes/brain_telegram/inbox")

# 99Freelas proposal template (Portuguese)
PROPOSAL_TEMPLATE_99FREELAS = """\
Olá {client_name},

Me chamo Roberto, sou desenvolvedor full-stack e analista de dados com {years}+ anos de experiência.

{personalized_opening}

{qualification_summary}

Fico à disposição para conversarmos melhor sobre o projeto e alinharmos os detalhes.

Atenciosamente,
Roberto
"""

# Email patterns to detect freelancer platforms
FREELAS_PATTERNS = [
    r"99freelas", r"99freela", r"workana", r"freelancer\.com",
    r"fiverr", r"getninjas", r"upwork",
]

# Telegram patterns
TELEGRAM_PATTERNS = [
    r"telegram", r"tg://", r"t\.me/",
]


# ═══════════════════════════════════════════════════════════════════════════════
#  Email
# ═══════════════════════════════════════════════════════════════════════════════

def check_email() -> dict:
    """Verifica emails via himalaya CLI (ou monitor.py como fallback).
    Retorna lista de mensagens não lidas/recentes.
    """
    result = {"source": "email", "messages": [], "error": None}

    # Try himalaya first
    try:
        proc = subprocess.run(
            ["himalaya", "list", "-s", "NEW", "-w", "200", "--output", "json"],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            emails = json.loads(proc.stdout)
            for em in emails if isinstance(emails, list) else [emails]:
                result["messages"].append({
                    "channel": "email",
                    "from": em.get("from", "?"),
                    "subject": em.get("subject", ""),
                    "date": em.get("date", ""),
                    "snippet": (em.get("snippet") or em.get("body", ""))[:200],
                    "id": em.get("id", ""),
                })
            return result
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass

    # Fallback: monitor.py or any email watcher
    monitor_paths = [
        os.path.expanduser("~/.hermes/monitor.py"),
        os.path.expanduser("~/.hermes/forex/monitor.py"),
        os.path.expanduser("~/.hermes/email_monitor.py"),
    ]
    for mp in monitor_paths:
        if os.path.exists(mp):
            try:
                proc = subprocess.run(
                    [sys.executable, mp, "--check"],
                    capture_output=True, text=True, timeout=30,
                )
                if proc.stdout.strip():
                    result["messages"].append({
                        "channel": "email",
                        "from": "monitor.py",
                        "subject": "Email check result",
                        "date": datetime.now(timezone.utc).isoformat(),
                        "snippet": proc.stdout.strip()[:200],
                    })
                    return result
            except (subprocess.TimeoutExpired, OSError):
                pass

    result["error"] = "No email backend available (himalaya not found, no monitor.py)"
    return result


# ═══════════════════════════════════════════════════════════════════════════════
#  Telegram
# ═══════════════════════════════════════════════════════════════════════════════

def check_telegram() -> dict:
    """Verifica mensagens do Telegram via inbox file ou brain_telegram module."""
    result = {"source": "telegram", "messages": [], "error": None}

    # 1. Check inbox directory
    if os.path.isdir(INBOX_PATH):
        try:
            for fname in sorted(os.listdir(INBOX_PATH)):
                fpath = os.path.join(INBOX_PATH, fname)
                if os.path.isfile(fpath):
                    mtime = os.path.getmtime(fpath)
                    age_hours = (datetime.now().timestamp() - mtime) / 3600
                    if age_hours <= 24:  # only recent files
                        try:
                            with open(fpath) as f:
                                content = f.read(500)
                        except OSError:
                            content = f"[binary: {fname}]"
                        result["messages"].append({
                            "channel": "telegram",
                            "from": fname,
                            "subject": f"Telegram inbox: {fname}",
                            "date": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(),
                            "snippet": content[:200],
                            "file": fpath,
                        })
        except OSError:
            pass

    # 2. Try brain_telegram module
    brain_tg_path = os.path.expanduser("~/.hermes/brain_telegram")
    if os.path.isdir(brain_tg_path):
        # Check for recent messages in any json state file
        for fname in ("state.json", "messages.json", "inbox.json"):
            fpath = os.path.join(brain_tg_path, fname)
            if os.path.exists(fpath):
                try:
                    with open(fpath) as f:
                        data = json.load(f)
                    msgs = data if isinstance(data, list) else data.get("messages", [])
                    for m in msgs[-5:]:  # last 5
                        result["messages"].append({
                            "channel": "telegram",
                            "from": m.get("from", m.get("sender", "?")),
                            "subject": m.get("text", "")[:80],
                            "date": m.get("date", m.get("timestamp", "")),
                            "snippet": str(m.get("text", ""))[:200],
                        })
                except (json.JSONDecodeError, OSError):
                    pass

    if not result["messages"]:
        result["error"] = "No recent Telegram messages"

    return result


# ═══════════════════════════════════════════════════════════════════════════════
#  99Freelas
# ═══════════════════════════════════════════════════════════════════════════════

def check_freelas() -> dict:
    """Escaneia emails relacionados a plataformas de freela (99Freelas, Workana, etc)."""
    result = {"source": "freelas", "opportunities": [], "error": None}

    # Check emails for freelancer platform patterns
    email_check = check_email()
    for msg in email_check.get("messages", []):
        subject = (msg.get("subject", "") + " " + msg.get("snippet", "")).lower()

        for pattern in FREELAS_PATTERNS:
            if re.search(pattern, subject):
                result["opportunities"].append({
                    "platform": pattern.replace(r"\d+", "").replace("\\", ""),
                    "from": msg.get("from", "?"),
                    "subject": msg.get("subject", ""),
                    "date": msg.get("date", ""),
                    "snippet": msg.get("snippet", ""),
                    "email_id": msg.get("id", ""),
                })
                break

    if not result["opportunities"]:
        result["error"] = "No freelancer platform messages found"

    return result


# ═══════════════════════════════════════════════════════════════════════════════
#  Templates
# ═══════════════════════════════════════════════════════════════════════════════

def format_proposal_template(client_name: str = "",
                              years: str = "5+",
                              personalized_opening: str = "",
                              qualification_summary: str = "") -> str:
    """Formata template de proposta para 99Freelas.
    Segue regra do failure_log: NUNCA mencionar valor/prazo no texto.
    """
    if not personalized_opening:
        personalized_opening = (
            "Vi seu projeto e acredito que meu perfil se encaixa bem "
            "com o que você precisa."
        )

    if not qualification_summary:
        qualification_summary = (
            "Tenho experiência com Python, automação, análise de dados, "
            "web scraping e desenvolvimento full-stack (Flask, FastAPI, React). "
            "Já desenvolvi sistemas de trading algorítmico, dashboards interativos "
            "e integrações com APIs de terceiros."
        )

    template = PROPOSAL_TEMPLATE_99FREELAS.format(
        client_name=client_name or "[NOME_CLIENTE]",
        years=years,
        personalized_opening=personalized_opening,
        qualification_summary=qualification_summary,
    )

    return template.strip()


# ═══════════════════════════════════════════════════════════════════════════════
#  Orchestrator
# ═══════════════════════════════════════════════════════════════════════════════

def run() -> dict:
    """Coleta mensagens de todos os canais, prepara rascunhos e publica tasks no Tálamo."""
    all_messages = []
    tasks_created = 0

    # 1. Email
    email_result = check_email()
    for msg in email_result.get("messages", []):
        all_messages.append({**msg, "source": "email"})
    if email_result.get("error"):
        all_messages.append({
            "channel": "email", "source": "email",
            "from": "SYSTEM", "subject": "Email check error",
            "snippet": email_result["error"],
            "date": datetime.now(timezone.utc).isoformat(),
        })

    # 2. Telegram
    tg_result = check_telegram()
    for msg in tg_result.get("messages", []):
        all_messages.append({**msg, "source": "telegram"})
    if tg_result.get("error") and not tg_result.get("messages"):
        pass  # silently skip "no messages" — it's normal

    # 3. Freelas
    freelas_result = check_freelas()
    for opp in freelas_result.get("opportunities", []):
        all_messages.append({
            "channel": "freelas",
            "source": "freelas",
            "from": opp.get("platform", "?"),
            "subject": opp.get("subject", ""),
            "snippet": f"[{opp.get('platform')}] {opp.get('subject', '')} — {opp.get('snippet', '')[:100]}",
            "date": opp.get("date", ""),
        })

    # 4. Generate proposal drafts for freelancer opportunities
    for opp in freelas_result.get("opportunities", []):
        draft = format_proposal_template(
            client_name="[Cliente — extrair do email]",
            personalized_opening=(
                f"Vi seu projeto '{opp.get('subject', '')}' na plataforma "
                f"e acredito que posso contribuir."
            ),
        )
        # Post as task pending review
        task_id = f"broca-proposal-{hash(opp.get('subject', '')) % 100000}"
        thalamus.send_message(
            source=BROCA_SOURCE,
            target="master",
            msg_type="proposal_draft",
            content={
                "platform": opp.get("platform", ""),
                "subject": opp.get("subject", ""),
                "draft": draft,
                "email_id": opp.get("email_id", ""),
            },
            priority=7,
        )
        tasks_created += 1

    # 5. Post collected messages as review tasks
    for msg in all_messages:
        if msg.get("channel") in ("email", "telegram") and msg.get("from") != "SYSTEM":
            task_id = f"broca-review-{hash(msg.get('subject', '')) % 100000}"
            thalamus.send_message(
                source=BROCA_SOURCE,
                target="master",
                msg_type="message_review",
                content={
                    "channel": msg.get("channel"),
                    "from": msg.get("from"),
                    "subject": msg.get("subject"),
                    "snippet": msg.get("snippet", "")[:200],
                },
                priority=5,
            )
            tasks_created += 1

    # 6. Update state
    thalamus.update_state("broca_messages_collected", len(all_messages))
    thalamus.log_event(
        event_type="area_broca_scan",
        source=BROCA_SOURCE,
        data={
            "total_messages": len(all_messages),
            "email_msgs": len(email_result.get("messages", [])),
            "telegram_msgs": len(tg_result.get("messages", [])),
            "freelas_opps": len(freelas_result.get("opportunities", [])),
            "tasks_created": tasks_created,
        },
        severity="info",
    )

    # Broadcast summary if anything interesting
    if freelas_result.get("opportunities"):
        thalamus.broadcast_to_workspace(
            content=f"📨 {len(freelas_result['opportunities'])} nova(s) oportunidade(s) de freela detectada(s)",
            priority=7,
            source=BROCA_SOURCE,
        )

    total_freelas = len(freelas_result.get("opportunities", []))
    if total_freelas > 0:
        thalamus.broadcast_to_workspace(
            content=f"📋 {total_freelas} rascunho(s) de proposta gerado(s) — aguardando revisão",
            priority=5,
            source=BROCA_SOURCE,
        )

    return {
        "total_messages": len(all_messages),
        "email": len(email_result.get("messages", [])),
        "telegram": len(tg_result.get("messages", [])),
        "freelas_opportunities": total_freelas,
        "tasks_created": tasks_created,
        "freelas_detail": freelas_result.get("opportunities", []),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Área de Broca — Comunicação e Mensagens")
    sub = parser.add_subparsers(dest="mode")

    sub.add_parser("run", help="Full scan: email + telegram + freelas + drafts")
    sub.add_parser("email", help="Check email only")
    sub.add_parser("telegram", help="Check Telegram only")
    sub.add_parser("freelas", help="Check freelancer platforms only")

    template_p = sub.add_parser("template", help="Generate a proposal template")
    template_p.add_argument("--client", default="", help="Client name")
    template_p.add_argument("--years", default="5+", help="Years of experience")
    template_p.add_argument("--opening", default="", help="Personalized opening line")
    template_p.add_argument("--qualification", default="", help="Qualification summary")

    args = parser.parse_args()

    print("=" * 60)
    print("  ÁREA DE BROCA — Comunicação")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    if args.mode == "email":
        result = check_email()
        print(f"\n📧 Email:")
        print(f"   Mensagens: {len(result.get('messages', []))}")
        for m in result.get("messages", []):
            print(f"   • [{m.get('from','?')}] {m.get('subject','')[:60]}")
        if result.get("error"):
            print(f"   ⚠️  {result['error']}")

    elif args.mode == "telegram":
        result = check_telegram()
        print(f"\n📱 Telegram:")
        print(f"   Mensagens: {len(result.get('messages', []))}")
        for m in result.get("messages", []):
            print(f"   • [{m.get('from','?')}] {m.get('subject','')[:60]}")
        if result.get("error"):
            print(f"   ⚠️  {result['error']}")

    elif args.mode == "freelas":
        result = check_freelas()
        print(f"\n💼 Freelas:")
        print(f"   Oportunidades: {len(result.get('opportunities', []))}")
        for opp in result.get("opportunities", []):
            print(f"   • [{opp.get('platform','?')}] {opp.get('subject','')[:70]}")
        if result.get("error"):
            print(f"   ⚠️  {result['error']}")

    elif args.mode == "template":
        draft = format_proposal_template(
            client_name=args.client,
            years=args.years,
            personalized_opening=args.opening,
            qualification_summary=args.qualification,
        )
        print(f"\n📝 Template de Proposta 99Freelas:")
        print("-" * 60)
        print(draft)
        print("-" * 60)
        print("\n⚠️  Lembrete (failure_log): NUNCA mencionar valor ou prazo no texto!")

    else:
        # run mode (default)
        result = run()
        print(f"\n📊 Resumo da varredura:")
        print(f"   📧 Emails: {result['email']}")
        print(f"   📱 Telegram: {result['telegram']}")
        print(f"   💼 Oportunidades freela: {result['freelas_opportunities']}")
        print(f"   📋 Tasks criadas no Tálamo: {result['tasks_created']}")
        print(f"   📨 Total mensagens: {result['total_messages']}")

        if result["freelas_opportunities"]:
            print(f"\n💼 Detalhe oportunidades:")
            for opp in result["freelas_detail"]:
                print(f"   • [{opp.get('platform','?')}] {opp.get('subject','')[:70]}")
