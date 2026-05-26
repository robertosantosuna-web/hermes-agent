#!/usr/bin/env python3
"""
Resume Script — Retomada automática após reboot.
Lê ~/.hermes/state/current.json e restaura o estado operacional.
"""
import json, os, subprocess, datetime, time

STATE_FILE = os.path.expanduser("~/.hermes/state/current.json")
LOG_FILE = os.path.expanduser("~/.hermes/state/resume.log")

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def main():
    log("═══ RESUME SCRIPT INICIADO ═══")
    
    # 1. Verificar estado anterior
    if not os.path.exists(STATE_FILE):
        log("⚠️ Nenhum estado encontrado. Iniciando fresh.")
        state = {"status": "fresh_start"}
    else:
        with open(STATE_FILE) as f:
            state = json.load(f)
        log(f"✅ Estado carregado: {state.get('status')} — {state.get('last_action', 'N/A')[:80]}")
    
    # 2. Verificar saúde do sistema
    mem = subprocess.run(["free", "-h"], capture_output=True, text=True).stdout.split("\n")[1]
    disk = subprocess.run(["df", "-h", "/"], capture_output=True, text=True).stdout.split("\n")[1]
    log(f"Sistema: {mem.strip()} | {disk.strip()}")
    
    # 3. Verificar GPU
    try:
        nvidia = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader"], 
                               capture_output=True, text=True).stdout.strip()
        log(f"GPU: {nvidia}")
    except:
        log("⚠️ GPU não detectada")
    
    # 4. Reconectar Telegram
    log("📡 Reconectando Telegram...")
    try:
        result = subprocess.run([
            "python3", "-c", """
from telethon import TelegramClient
import asyncio
async def main():
    c = TelegramClient('roberto3', 2040, 'b18441a1ff607e10a989891a5462e627')
    await c.start(phone='+5531982125758')
    me = await c.get_me()
    print(f'OK: @{me.username}')
    await c.send_message(8781127500, '🔄 ENTIDADE REINICIADA — Sistema recuperado após reboot.')
    await c.disconnect()
asyncio.run(main())
"""
        ], capture_output=True, text=True, timeout=30)
        log(f"Telegram: {result.stdout.strip()}")
    except Exception as e:
        log(f"⚠️ Telegram erro: {e}")
    
    # 5. Carregar modelo local (GPU)
    log("🧠 Carregando modelo local...")
    try:
        result = subprocess.run([
            "python3", "-c", """
from llama_cpp import Llama
llm = Llama.from_pretrained('bartowski/Phi-3.1-mini-4k-instruct-GGUF', filename='*Q4_K_M.gguf', n_ctx=2048, n_gpu_layers=24, verbose=False)
print('GPU OK')
"""
        ], capture_output=True, text=True, timeout=30)
        log(f"LLM: {result.stdout.strip()}")
    except Exception as e:
        log(f"⚠️ LLM erro: {e}")
    
    # 6. Verificar email
    log("📧 Verificando email...")
    try:
        result = subprocess.run([
            "python3", "-c", """
import imaplib
m = imaplib.IMAP4_SSL('imap.gmail.com', 993)
m.login('robertosantos.una@gmail.com', 'exnlrvfswckioces')
m.select('INBOX')
s, d = m.search(None, 'UNSEEN')
count = len(d[0].split()) if d[0] else 0
print(f'{count} não lidos')
m.logout()
"""
        ], capture_output=True, text=True, timeout=20)
        log(f"Email: {result.stdout.strip()}")
    except Exception as e:
        log(f"⚠️ Email erro: {e}")
    
    # 7. Atualizar estado
    state["last_boot"] = datetime.datetime.now().isoformat()
    state["status"] = "operational"
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    
    # 8. Resumo das pendências
    pending = state.get("pending_tasks", [])
    log(f"📋 {len(pending)} tarefas pendentes:")
    for t in pending[:5]:
        log(f"  • {t}")
    
    log("═══ RESUME CONCLUÍDO ═══")
    return 0

if __name__ == "__main__":
    exit(main())
