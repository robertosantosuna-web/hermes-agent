#!/usr/bin/env python3
"""Cerebelo — Validador de comandos, trades e deploys.
On-demand: invocado sempre que uma ação precisa de validação prévia.
Regex contra padrões perigosos, validação de risco por trade,
e gate de deploy em produção.

Usa o Tálamo para ler tasks pendentes de validação e registrar resultados.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# ── path setup ──────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.expanduser("~/.hermes/brain"))
import thalamus

# ── constants ───────────────────────────────────────────────────────────────
VALIDATION_SOURCE = "cerebellum"

# Patterns that should NEVER be executed without explicit review
DANGEROUS_PATTERNS = [
    (r"sudo\s+-S",                          "sudo -S (password via stdin)"),
    (r"curl\s+.*\|.*(?:sh|bash)",            "curl pipe shell — remote code execution"),
    (r"wget\s+.*-O\s*-\s*\|.*(?:sh|bash)",   "wget pipe shell — remote code execution"),
    (r"rm\s+-rf\s+/",                        "rm -rf / — recursive root delete"),
    (r"rm\s+-rf\s+~",                        "rm -rf ~ — recursive home delete"),
    (r"rm\s+-rf\s+\$HOME",                   "rm -rf $HOME — recursive home delete"),
    (r"chmod\s+777\s+/",                     "chmod 777 on root path"),
    (r"chmod\s+-R\s+777",                    "chmod -R 777 — recursive world-writable"),
    (r":\(\)\s*\{\s*:\s*\|\s*&\s*\}",       "fork bomb pattern"),
    (r"dd\s+if=/dev/zero\s+of=/dev/sd",      "dd zero to block device"),
    (r"mkfs\.",                              "mkfs — filesystem format"),
    (r">\s*/dev/sda",                        "redirect to block device"),
    (r"eval\s+",                             "eval with untrusted input"),
    (r"__import__\s*\(\s*['\"]os['\"]",      "dynamic os import (sandbox escape)"),
    (r"exec\s*\(\s*.*\bcompile\b",           "exec+compile (code injection)"),
    (r"subprocess\.\w*\(\s*.*shell\s*=\s*True", "subprocess shell=True"),
    (r"os\.system\s*\(.+\)",                "os.system with dynamic command"),
    (r"os\.popen\s*\(.+\)",                 "os.popen with dynamic command"),
]

MAX_RISK_PCT = 2.0  # max trade risk as % of balance


# ═══════════════════════════════════════════════════════════════════════════════
#  Validators
# ═══════════════════════════════════════════════════════════════════════════════

def validate_command(cmd: str) -> dict:
    """Testa um comando contra DANGEROUS_PATTERNS.
    Retorna dict com: safe (bool), matches (list), blocked (bool).
    """
    if not isinstance(cmd, str) or not cmd.strip():
        return {"safe": True, "matches": [], "blocked": False, "detail": "empty command"}

    matches = []
    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            matches.append({"pattern": pattern, "description": description, "matched_in": cmd[:200]})

    safe = len(matches) == 0
    # Patterns that are ALWAYS blocked (no override)
    always_block = any(
        m["description"].startswith(prefix)
        for m in matches
        for prefix in [
            "sudo -S", "curl pipe", "wget pipe", "rm -rf /", "rm -rf ~",
            "rm -rf $HOME", "fork bomb", "dd if=/dev/zero", "mkfs",
            "redirect to block device",
        ]
    )

    return {
        "safe": safe,
        "matches": matches,
        "blocked": always_block,
        "blockable": len(matches) > 0,
        "detail": f"{len(matches)} dangerous pattern(s) found" if matches else "clean",
    }


def validate_trade(symbol: str, direction: str, volume: float,
                   sl: float, tp: float, balance: float) -> dict:
    """Valida se o risco do trade não excede MAX_RISK_PCT do balance.
    Risco = (entry - sl) * volume. Para long: entry - sl > 0. Para short: sl - entry > 0.
    Como não temos entry price explícito, estimamos pelo SL distance.

    Retorna dict com: valid, risk_pct, risk_amount, max_risk, detail.
    """
    if not balance or balance <= 0:
        return {"valid": False, "risk_pct": None, "detail": "Invalid or missing balance"}

    if not symbol or volume <= 0:
        return {"valid": False, "risk_pct": None, "detail": "Invalid symbol or volume"}

    max_risk = balance * (MAX_RISK_PCT / 100.0)

    # If we have SL, estimate risk. Without entry, use SL as approximate pip distance * volume.
    # For forex, 1 pip ≈ $10 per standard lot (100k units). Volume in lots.
    if sl and sl > 0:
        # Assume SL is in pips; risk = sl * volume * pip_value (approx $10/lot)
        pip_value = 10.0
        risk_amount = sl * volume * pip_value
    else:
        risk_amount = 0.0

    risk_pct = round((risk_amount / balance) * 100, 2) if balance > 0 else 0

    valid = risk_pct <= MAX_RISK_PCT

    return {
        "valid": valid,
        "risk_pct": risk_pct,
        "risk_amount": round(risk_amount, 2),
        "max_risk": round(max_risk, 2),
        "max_risk_pct": MAX_RISK_PCT,
        "symbol": symbol,
        "direction": direction,
        "detail": (
            f"Risk {risk_pct}% {'OK' if valid else 'EXCEEDS'} limit {MAX_RISK_PCT}%"
        ),
    }


def validate_deploy(target: str, is_production: bool) -> dict:
    """Validação de deploy. Produção sempre gera warning e requer confirmação."""
    result = {
        "target": target,
        "is_production": is_production,
        "allowed": True,
        "require_confirmation": False,
        "warnings": [],
    }

    if is_production:
        result["require_confirmation"] = True
        result["warnings"].append(
            "PRODUCTION DEPLOY: requires explicit confirmation. "
            "Verify: backups done? rollback plan ready? maintenance window?"
        )

    # Target safety checks
    target_lower = target.lower()
    if any(kw in target_lower for kw in ["prod", "production", "live", "master", "main"]):
        if not is_production:
            result["warnings"].append(
                f"Target '{target}' looks like production but is_production=False — verify"
            )

    if any(dangerous in target_lower for dangerous in ["rm -rf", "drop database", "truncate"]):
        result["allowed"] = False
        result["warnings"].append(f"Target '{target}' contains destructive operation — BLOCKED")

    return result


def run_checks() -> dict:
    """Varre tarefas pendentes de validação no Tálamo e processa cada uma."""
    state = thalamus._load() if hasattr(thalamus, '_load') else {}
    tasks = state.get("tasks", [])
    validations = state.get("validations", [])

    results = {"processed": 0, "validations": [], "alerts": []}

    # Process pending validation tasks
    pending = [t for t in tasks if t.get("status") == "pending_validation"]
    for task in pending:
        task_type = task.get("task_type", "")
        payload = task.get("payload", {})

        if task_type == "command":
            cmd = payload.get("command") or payload.get("cmd", "")
            v = validate_command(cmd)
            results["validations"].append({**v, "task_id": task.get("id"), "type": "command"})
            if not v["safe"]:
                thalamus.raise_alert(
                    level="critical" if v.get("blocked") else "warning",
                    title="Dangerous Command Blocked" if v.get("blocked") else "Command Needs Review",
                    description=v["detail"],
                    source=VALIDATION_SOURCE,
                )
                results["alerts"].append(f"command_blocked: {v['detail']}")

        elif task_type == "trade":
            v = validate_trade(
                symbol=payload.get("symbol", ""),
                direction=payload.get("direction", "long"),
                volume=float(payload.get("volume", 0)),
                sl=float(payload.get("sl", 0)),
                tp=float(payload.get("tp", 0)),
                balance=float(payload.get("balance", 0)),
            )
            results["validations"].append({**v, "task_id": task.get("id"), "type": "trade"})
            if not v["valid"]:
                thalamus.raise_alert(
                    level="warning",
                    title=f"Trade Risk Exceeded: {v['risk_pct']}%",
                    description=v["detail"],
                    source=VALIDATION_SOURCE,
                )
                results["alerts"].append(f"trade_risk: {v['detail']}")

        elif task_type == "deploy":
            v = validate_deploy(
                target=payload.get("target", "unknown"),
                is_production=payload.get("is_production", False),
            )
            results["validations"].append({**v, "task_id": task.get("id"), "type": "deploy"})
            if v["require_confirmation"] or not v["allowed"]:
                level = "critical" if not v["allowed"] else "warning"
                thalamus.raise_alert(
                    level=level,
                    title="Deploy Requires Confirmation",
                    description="; ".join(v["warnings"]),
                    source=VALIDATION_SOURCE,
                )
                results["alerts"].append(f"deploy_gate: {'; '.join(v['warnings'])}")

        results["processed"] += 1

    # Log validation cycle
    thalamus.log_event(
        event_type="cerebellum_validation",
        source=VALIDATION_SOURCE,
        data={"processed": results["processed"], "alerts": len(results["alerts"])},
        severity="info",
    )

    return results


# ═══════════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Cerebelo — Validador de Comandos, Trades e Deploys")
    sub = parser.add_subparsers(dest="mode", help="Validation mode")

    # cmd mode
    cmd_p = sub.add_parser("cmd", help="Validate a shell command")
    cmd_p.add_argument("command", nargs="?", help="Command string to validate")

    # trade mode
    trade_p = sub.add_parser("trade", help="Validate a trade")
    trade_p.add_argument("--symbol", required=True, help="Trading symbol (e.g., GBPJPY)")
    trade_p.add_argument("--direction", default="long", choices=["long", "short"])
    trade_p.add_argument("--volume", type=float, required=True, help="Volume in lots")
    trade_p.add_argument("--sl", type=float, required=True, help="Stop loss in pips")
    trade_p.add_argument("--tp", type=float, default=0, help="Take profit in pips")
    trade_p.add_argument("--balance", type=float, required=True, help="Account balance")

    # deploy mode
    deploy_p = sub.add_parser("deploy", help="Validate a deploy")
    deploy_p.add_argument("--target", required=True, help="Deploy target")
    deploy_p.add_argument("--prod", action="store_true", help="Is production deploy")

    # run mode (scan tasks)
    sub.add_parser("run", help="Run pending validation checks from thalamus tasks")

    args = parser.parse_args()

    print("=" * 60)
    print("  CEREBELO — Validador")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    if args.mode == "cmd":
        if args.command:
            result = validate_command(args.command)
            print(f"\n🔍 Comando: {args.command[:120]}")
            print(f"   Safe: {'✅' if result['safe'] else '❌'}")
            print(f"   Blocked: {'🚫' if result.get('blocked') else '⚠️ Review' if result.get('blockable') else '—'}")
            for m in result["matches"]:
                print(f"   ⚡ {m['description']}")
        else:
            # Demo mode: show all patterns
            print("\n📋 DANGEROUS_PATTERNS registradas:")
            for pattern, desc in DANGEROUS_PATTERNS:
                print(f"   • {desc}")

    elif args.mode == "trade":
        result = validate_trade(args.symbol, args.direction, args.volume, args.sl, args.tp, args.balance)
        print(f"\n📈 Trade: {args.symbol} {args.direction} {args.volume} lots")
        print(f"   SL: {args.sl} pips | TP: {args.tp} pips")
        print(f"   Balance: ${args.balance:.2f}")
        print(f"   Risco: {result['risk_pct']}% (${result['risk_amount']})")
        print(f"   Limite: {result['max_risk_pct']}% (${result['max_risk']})")
        print(f"   Válido: {'✅' if result['valid'] else '❌'} — {result['detail']}")

    elif args.mode == "deploy":
        result = validate_deploy(args.target, args.prod)
        print(f"\n🚀 Deploy: {args.target}")
        print(f"   Produção: {'Sim' if args.prod else 'Não'}")
        print(f"   Permitido: {'✅' if result['allowed'] else '🚫'}")
        print(f"   Requer confirmação: {'⚠️ Sim' if result['require_confirmation'] else 'Não'}")
        for w in result["warnings"]:
            print(f"   ⚡ {w}")

    elif args.mode == "run":
        result = run_checks()
        print(f"\n📋 Validações processadas: {result['processed']}")
        for v in result["validations"]:
            vtype = v.get("type", "?")
            detail = v.get("detail", "")
            safe = v.get("safe") or v.get("valid") or v.get("allowed", True)
            print(f"   {'✅' if safe else '❌'} [{vtype}] {detail}")
        if result["alerts"]:
            print(f"\n🚨 Alertas: {len(result['alerts'])}")
            for a in result["alerts"]:
                print(f"   • {a}")

    else:
        # Default: show help
        parser.print_help()
