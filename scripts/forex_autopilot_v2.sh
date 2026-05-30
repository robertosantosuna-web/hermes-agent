#!/bin/bash
# Forex AutoPilot v2 — Executa o bot multi-estratégia
# Chamado pelo cron a cada 3 minutos (seg-sex)
cd /home/roberto/.hermes/scripts && /usr/bin/python3 forex_bot_multi.py 2>&1
