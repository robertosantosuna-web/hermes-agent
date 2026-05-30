#!/usr/bin/env python3
"""Repassa alerta do autopilot como contexto para o agente."""
import json, sys
from pathlib import Path

ALERT_FILE = Path.home() / '.hermes' / 'crypto' / 'autopilot_alert.json'

if not ALERT_FILE.exists():
    print("NO_ALERT")
    sys.exit(0)

try:
    with open(ALERT_FILE) as f:
        alert = json.load(f)
    print(f"ALERTA ATIVO: {alert.get('error')}")
    print(f"Horário: {alert.get('time')}")
    print(f"Output: {alert.get('output', '')[:500]}")
    # NÃO deletar — o agente deleta após resolver
except Exception as e:
    print(f"ERRO_LENDO_ALERTA: {e}")
