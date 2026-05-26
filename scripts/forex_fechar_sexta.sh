#!/bin/bash
# Fechamento: Sexta-feira 16:00 BRT — fecha todas as ordens abertas
cd /home/roberto/.hermes/scripts
exec /usr/bin/python3 forex_pipeline_v2.py fechar
