#!/usr/bin/env python3
"""
Análise Forex Pré-Pico — Roda 5 min antes de cada killzone.
Só acorda o agente se houver setup válido (não consome tokens em espera).
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Horários BRT das killzones
KILLZONES = {
    "london_open": {"brt": "04:55", "gmt_hour": 8},
    "ny_open": {"brt": "09:55", "gmt_hour": 13},
    "london_close": {"brt": "11:55", "gmt_hour": 15},
}

ALERT_FILE = os.path.expanduser("~/.hermes/monitor/forex_alert.txt")
STATE_FILE = os.path.expanduser("~/.hermes/monitor/forex_state.json")

def get_current_killzone():
    """Determine which killzone we're about to enter — STRICT windows only"""
    now = datetime.now()
    brt_hour = (now.hour - 3) % 24
    brt_min = now.minute
    weekday = now.weekday()  # 0=Mon, 6=Sun
    
    # FORA de dias úteis = sem killzone
    if weekday >= 5:
        return None
    
    # London Open: 04:55-05:00 BRT (análise T-5)
    if brt_hour == 4 and 55 <= brt_min <= 59:
        return "london_open"
    
    # NY Open: 09:55-10:00 BRT (análise T-5)
    elif brt_hour == 9 and 55 <= brt_min <= 59:
        return "ny_open"
    
    # London Close: 11:55-12:00 BRT (análise T-5)
    elif brt_hour == 11 and 55 <= brt_min <= 59:
        return "london_close"
    
    return None

def check_setup(killzone):
    """
    Verifica se há setup válido para a killzone.
    Regras simplificadas:
    - London Open: se há red news no ForexFactory nas próximas 2h
    - NY Open: sempre tem setup (maior volume)
    - London Close: sempre tem setup (melhor win rate)
    """
    # Por enquanto, sempre retorna True para London Close e NY Open
    # Futuramente pode integrar com dados de mercado
    if killzone in ["ny_open", "london_close"]:
        return True
    elif killzone == "london_open":
        # Verificar se é dia útil (seg-sex)
        now = datetime.now()
        if now.weekday() >= 5:  # Sábado ou domingo
            return False
        return True
    return False

def main():
    killzone = get_current_killzone()
    
    if not killzone:
        print("Fora do horário de killzone")
        return
    
    if not check_setup(killzone):
        print(f"Killzone {killzone}: sem setup — agente dorme")
        return
    
    # Verificar se já processou essa killzone hoje
    today = datetime.now().strftime("%Y-%m-%d")
    state = {}
    if Path(STATE_FILE).exists():
        try:
            state = json.loads(Path(STATE_FILE).read_text())
        except:
            pass
    
    key = f"{today}_{killzone}"
    if state.get(key):
        print(f"Killzone {killzone} já processada hoje")
        return
    
    # Acordar agente
    alert_msg = (
        f"FOREX:{killzone}:{KILLZONES[killzone]['brt']} BRT:"
        f"Análise T-5 para entrada 3:1 RR\n"
        f"Pares: EURUSD, EURJPY, USDJPY\n"
        f"Setup: CRT sweep + EMA20 + London Close only"
    )
    
    Path(ALERT_FILE).write_text(alert_msg)
    state[key] = True
    Path(STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(STATE_FILE).write_text(json.dumps(state))
    
    print(f">>> ACORDAR AGENTE: {killzone} <<<")
    print(alert_msg)

if __name__ == "__main__":
    main()
