#!/usr/bin/env python3
"""Wrapper: trade_closer.py close"""
import subprocess, sys
sys.exit(subprocess.run([sys.executable, '/home/roberto/.hermes/scripts/trade_closer.py', 'close']).returncode)
