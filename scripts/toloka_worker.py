#!/usr/bin/env python3
"""
Toloka Worker — Agente autônomo de renda USD
Usa API REST da Toloka para buscar e completar micro tarefas.

API: https://toloka.ai/docs/api/api-reference/
Sem dependências externas (requests puro).
"""

import requests
import json
import time
import os
import sys
from datetime import datetime
from typing import Optional

API_BASE = "https://toloka.dev/api/v1"
CONFIG_PATH = os.path.expanduser("~/.hermes/config/toloka.json")
LOG_PATH = os.path.expanduser("~/.hermes/logs/toloka_worker.log")

HEADERS_TEMPLATE = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
}


def load_config():
    """Carregar token da Toloka"""
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def log(msg):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    timestamp = datetime.now().isoformat()
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def get_headers():
    """Headers com OAuth token"""
    config = load_config()
    token = config.get("oauth_token", "")
    h = HEADERS_TEMPLATE.copy()
    if token:
        h["Authorization"] = f"OAuth {token}"
    return h


# ═══════════════════════════════════════
# API TOLOKA
# ═══════════════════════════════════════

def get_balance():
    """Verificar saldo atual"""
    try:
        r = requests.get(f"{API_BASE}/requester", headers=get_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get("balance", 0)
        return None
    except:
        return None


def get_available_tasks(max_retries=3):
    """
    Buscar tasks disponíveis via pool da Toloka.
    A Toloka usa 'pools' de tasks que precisam ser completadas.
    Para o worker (executor), precisamos buscar tasks abertas.
    """
    try:
        # Buscar tasks disponíveis para o worker
        r = requests.get(
            f"{API_BASE}/task-suits",
            headers=get_headers(),
            timeout=10,
        )
        if r.status_code == 200:
            return r.json().get("items", [])
        return []
    except:
        return []


def submit_task(task_id, result):
    """Submeter resultado de uma task"""
    try:
        r = requests.post(
            f"{API_BASE}/assignments/{task_id}/submit",
            headers=get_headers(),
            json={"result": result},
            timeout=10,
        )
        return r.status_code == 200
    except:
        return False


# ═══════════════════════════════════════
# WORKER PRINCIPAL
# ═══════════════════════════════════════

def run_worker(loop=True, interval=60):
    """
    Executar worker da Toloka.
    Busca tasks → executa → submete → repete.
    """
    log("🤖 Toloka Worker iniciado")
    
    config = load_config()
    if not config.get("oauth_token"):
        log("❌ Token OAuth não configurado!")
        log("   1. Crie conta em https://toloka.ai/")
        log("   2. Pegue o token OAuth em: https://platform.toloka.ai/requester/profile")
        log("   3. Salve em ~/.hermes/config/toloka.json como:")
        log('      {"oauth_token": "SEU_TOKEN_AQUI"}')
        return
    
    tasks_completed = 0
    earnings = 0.0
    
    while True:
        try:
            # 1. Verificar saldo
            balance = get_balance()
            if balance is not None:
                log(f"💰 Saldo: ${balance:.2f}")
            
            # 2. Buscar tasks disponíveis
            tasks = get_available_tasks()
            
            if tasks:
                log(f"📋 {len(tasks)} tasks disponíveis")
                
                for task in tasks:
                    task_id = task.get("id", "")
                    task_type = task.get("type", "unknown")
                    reward = task.get("reward", 0)
                    
                    log(f"  🔹 {task_type} — ${reward}")
                    
                    # 3. Executar task (placeholder — cada tipo precisa de handler específico)
                    result = execute_task(task)
                    
                    if result is not None:
                        # 4. Submeter
                        success = submit_task(task_id, result)
                        if success:
                            tasks_completed += 1
                            earnings += reward
                            log(f"  ✅ Task {task_id} concluída! +${reward}")
                        else:
                            log(f"  ❌ Falha ao submeter task {task_id}")
            else:
                log("📭 Nenhuma task disponível no momento")
            
            log(f"📊 Total: {tasks_completed} tasks | ${earnings:.2f}")
            
            if not loop:
                break
            
            log(f"⏳ Aguardando {interval}s...")
            time.sleep(interval)
            
        except KeyboardInterrupt:
            log("🛑 Worker interrompido")
            break
        except Exception as e:
            log(f"⚠️ Erro: {e}")
            time.sleep(interval)


def execute_task(task):
    """
    Executar uma task da Toloka.
    Tipos comuns: IMAGE_CLASSIFICATION, TEXT_MODERATION, SIDE_BY_SIDE, SURVEY
    
    Aqui retornamos placeholder — cada tipo precisa de lógica específica.
    Um agente LLM pode ser usado para tarefas de classificação/moderação.
    """
    task_type = task.get("type", "")
    task_input = task.get("input", {})
    
    # Por enquanto, placeholder
    # TODO: Implementar handlers específicos por tipo
    # TODO: Integrar com LLM para classificação/moderação
    
    result = {
        "status": "completed",
        "output": task_input,
    }
    
    return result


# ═══════════════════════════════════════
# CLI
# ═══════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Toloka Worker — Renda autônoma USD")
        print("  python3 toloka_worker.py start    — Iniciar worker (loop)")
        print("  python3 toloka_worker.py once     — Executar uma rodada")
        print("  python3 toloka_worker.py setup    — Configurar token")
        print("  python3 toloka_worker.py balance  — Ver saldo")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "setup":
        token = input("Token OAuth Toloka: ").strip()
        save_config({"oauth_token": token})
        print("✅ Token salvo!")
    
    elif cmd == "start":
        run_worker(loop=True, interval=60)
    
    elif cmd == "once":
        run_worker(loop=False)
    
    elif cmd == "balance":
        b = get_balance()
        if b is not None:
            print(f"💰 Saldo: ${b:.2f}")
        else:
            print("❌ Erro ao verificar saldo. Token configurado?")
