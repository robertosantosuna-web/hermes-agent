#!/bin/bash
# Watchdog do Monitor em Tempo Real — reinicia se cair
pgrep -f forex_realtime_monitor.py > /dev/null 2>&1 && exit 0
cd /home/roberto/.hermes
nohup python3 scripts/forex_realtime_monitor.py >> logs/monitor.log 2>&1 &
echo "$(date -Is) 🔄 Monitor reiniciado (PID $!)"
