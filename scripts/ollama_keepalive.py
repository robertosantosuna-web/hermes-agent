#!/usr/bin/env python3
"""
OLLAMA KEEP-ALIVE — Mantém os modelos carregados para evitar cold starts.
Roda a cada 5 minutos. Faz uma inferência curta para manter o modelo em memória.
"""
import subprocess, sys
from pathlib import Path
from datetime import datetime

# Modelos a manter aquecidos (ordem de prioridade)
MODELS = ['qwen2.5:3b', 'phi3:mini']

def keep_alive(model: str) -> bool:
    try:
        r = subprocess.run(
            ['ollama', 'run', model],
            input='ping',
            capture_output=True, text=True, timeout=30
        )
        return r.returncode == 0
    except:
        return False

if __name__ == '__main__':
    ok = 0
    for m in MODELS:
        if keep_alive(m):
            ok += 1
    # Silent if all ok
    if ok < len(MODELS):
        print(f"⚠️ {datetime.now().strftime('%H:%M')} Ollama: {ok}/{len(MODELS)} modelos respondendo")
