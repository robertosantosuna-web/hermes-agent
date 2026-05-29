#!/usr/bin/env python3
"""
OllamaKeepAlive — Monitora e mantém o Ollama rodando.
Faz health check via API /api/tags e reinicia se necessário.
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import thalamus

import json
import subprocess
import time
from datetime import datetime, timezone

OLLAMA_URL = "http://localhost:11434/api/tags"
OLLAMA_SERVICE = "ollama"
CHECK_TIMEOUT = 10


def check_ollama():
    """Verifica se o Ollama está respondendo via curl na API /api/tags.
    Retorna (ok: bool, data: dict|None)."""
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", str(CHECK_TIMEOUT), OLLAMA_URL],
            capture_output=True, text=True, timeout=CHECK_TIMEOUT + 5,
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            return True, data
        return False, None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return False, None


def restart_ollama():
    """Reinicia o serviço Ollama via systemctl --user."""
    try:
        result = subprocess.run(
            ["systemctl", "--user", "restart", OLLAMA_SERVICE],
            capture_output=True, text=True, timeout=30,
        )
        success = result.returncode == 0
        if not success:
            thalamus.log_event("ollama_restart_failed", "OllamaKeepAlive", {
                "stderr": result.stderr.strip(),
            }, severity="error")
        return success
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        thalamus.log_event("ollama_restart_exception", "OllamaKeepAlive", {
            "error": str(e),
        }, severity="error")
        return False


def run():
    """Executa o health check e tenta auto-heal se necessário."""
    ok, data = check_ollama()

    if ok:
        model_count = len(data.get("models", [])) if data else 0
        thalamus.log_event("ollama_check", "OllamaKeepAlive", {
            "status": "ok",
            "models": model_count,
        })
        return {
            "status": "ok",
            "models": model_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    else:
        thalamus.log_event("ollama_check", "OllamaKeepAlive", {
            "status": "down",
        }, severity="warning")
        thalamus.raise_alert(
            level="warning",
            title="Ollama is DOWN",
            description="Ollama não está respondendo na API. Tentando reiniciar...",
            source="OllamaKeepAlive",
        )

        # Auto-heal
        if restart_ollama():
            thalamus.log_event("ollama_restarted", "OllamaKeepAlive", {
                "status": "restarted successfully",
            })
            thalamus.raise_alert(
                level="info",
                title="Ollama Restarted",
                description="Auto-heal: Ollama reiniciado com sucesso.",
                source="OllamaKeepAlive",
            )
            # Espera um pouco e verifica de novo
            time.sleep(3)
            ok2, data2 = check_ollama()
            if ok2:
                model_count = len(data2.get("models", [])) if data2 else 0
                return {
                    "status": "recovered",
                    "models": model_count,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

        thalamus.raise_alert(
            level="critical",
            title="Ollama FAILED to restart",
            description="Auto-heal falhou. Ollama continua offline.",
            source="OllamaKeepAlive",
        )
        return {
            "status": "down",
            "models": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ----------------------------------------------------------------------
# __main__
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print(f"OllamaKeepAlive — Checking at {datetime.now(timezone.utc).isoformat()}")

    result = run()

    print(f"  Status: {result['status']}")
    print(f"  Models: {result['models']}")
