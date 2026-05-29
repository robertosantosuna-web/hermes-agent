#!/usr/bin/env python3
"""
GatewayGuard — Proteção Anti-queda do Hermes Gateway.
Monitora: serviço systemd, memória RAM, disco.
Auto-heal: tenta reiniciar o gateway se cair.
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import thalamus

import subprocess
import time
from datetime import datetime, timezone

GATEWAY_SERVICE = "hermes-gateway"
MEMORY_THRESHOLD = 80   # percentual
DISK_THRESHOLD = 90     # percentual
CHECK_INTERVAL = 60     # segundos entre ciclos


def check_gateway():
    """Verifica se o hermes-gateway está ativo via systemctl."""
    try:
        result = subprocess.run(
            ["systemctl", "--user", "is-active", GATEWAY_SERVICE],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() == "active"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_memory():
    """Verifica uso de RAM via free -m. Retorna (percent, alert)."""
    try:
        result = subprocess.run(
            ["free", "-m"], capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split("\n")
        # Linha 1: Mem: total used free shared buff/cache available
        if len(lines) >= 2:
            parts = lines[1].split()
            total = float(parts[1])
            used = float(parts[2])
            if total > 0:
                percent = (used / total) * 100
                alert = percent > MEMORY_THRESHOLD
                return round(percent, 1), alert
    except (subprocess.TimeoutExpired, FileNotFoundError, IndexError, ValueError):
        pass
    return 0.0, False


def check_disk():
    """Verifica uso de disco no /. Retorna (percent, alert)."""
    try:
        result = subprocess.run(
            ["df", "-h", "/"], capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            parts = lines[1].split()
            # Ex: /dev/sda1  100G  50G  45G  53% /
            use_str = parts[4].replace("%", "")
            percent = float(use_str)
            alert = percent > DISK_THRESHOLD
            return percent, alert
    except (subprocess.TimeoutExpired, FileNotFoundError, IndexError, ValueError):
        pass
    return 0.0, False


def restart_gateway():
    """Reinicia o hermes-gateway via systemctl --user."""
    try:
        result = subprocess.run(
            ["systemctl", "--user", "restart", GATEWAY_SERVICE],
            capture_output=True, text=True, timeout=30
        )
        success = result.returncode == 0
        if not success:
            thalamus.log_event("gateway_restart_failed", "GatewayGuard", {
                "stderr": result.stderr.strip(),
            }, severity="error")
        return success
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        thalamus.log_event("gateway_restart_exception", "GatewayGuard", {
            "error": str(e),
        }, severity="error")
        return False


def run(once=False):
    """Orquestra os checks. Se problema detectado, tenta auto-heal e levanta alerta."""
    issues = []

    # 1. Gateway
    gateway_ok = check_gateway()
    if not gateway_ok:
        issues.append("gateway_down")
        thalamus.log_event("gateway_check", "GatewayGuard", {
            "gateway": "down",
        }, severity="error")
        thalamus.raise_alert(
            level="critical",
            title="Hermes Gateway DOWN",
            description="O serviço hermes-gateway não está ativo. Tentando reiniciar...",
            source="GatewayGuard",
        )
        # Auto-heal
        if restart_gateway():
            thalamus.log_event("gateway_restarted", "GatewayGuard", {
                "gateway": "restarted successfully",
            })
            thalamus.raise_alert(
                level="info",
                title="Hermes Gateway Restarted",
                description="Auto-heal: gateway reiniciado com sucesso.",
                source="GatewayGuard",
            )
        else:
            thalamus.raise_alert(
                level="critical",
                title="Hermes Gateway FAILED to restart",
                description="Auto-heal falhou. Intervenção manual necessária.",
                source="GatewayGuard",
            )
    else:
        thalamus.log_event("gateway_check", "GatewayGuard", {
            "gateway": "ok",
        })

    # 2. Memória
    mem_percent, mem_alert = check_memory()
    if mem_alert:
        issues.append("memory_high")
        thalamus.raise_alert(
            level="warning",
            title=f"High Memory Usage: {mem_percent}%",
            description=f"Uso de RAM está em {mem_percent}% (threshold: {MEMORY_THRESHOLD}%).",
            source="GatewayGuard",
        )
    thalamus.log_event("memory_check", "GatewayGuard", {
        "memory_percent": mem_percent,
        "alert": mem_alert,
    })

    # 3. Disco
    disk_percent, disk_alert = check_disk()
    if disk_alert:
        issues.append("disk_high")
        thalamus.raise_alert(
            level="warning",
            title=f"High Disk Usage: {disk_percent}%",
            description=f"Uso de disco em / está em {disk_percent}% (threshold: {DISK_THRESHOLD}%).",
            source="GatewayGuard",
        )
    thalamus.log_event("disk_check", "GatewayGuard", {
        "disk_percent": disk_percent,
        "alert": disk_alert,
    })

    # Atualiza health score
    thalamus.update_state("health_score", 100 - (len(issues) * 15))

    return {
        "gateway_ok": gateway_ok,
        "memory_percent": mem_percent,
        "disk_percent": disk_percent,
        "issues": issues,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ----------------------------------------------------------------------
# __main__
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print(f"GatewayGuard — Checking system health at {datetime.now(timezone.utc).isoformat()}")

    result = run(once=True)

    print(f"  Gateway: {'OK' if result['gateway_ok'] else 'DOWN'}")
    print(f"  Memory:  {result['memory_percent']}%")
    print(f"  Disk:    {result['disk_percent']}%")
    print(f"  Issues:  {result['issues'] if result['issues'] else 'None'}")
