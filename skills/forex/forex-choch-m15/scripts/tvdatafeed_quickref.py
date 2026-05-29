#!/usr/bin/env python3
"""
TvDatafeed — Dados do TradingView sem browser.
Instalar: pip install git+https://github.com/rongardF/tvdatafeed.git

Uso rápido:
  from tvDatafeed import TvDatafeed, Interval
  tv = TvDatafeed()
  df = tv.get_hist(symbol='GBPJPY', exchange='FX', interval=Interval.in_15_minute, n_bars=200)

⚠️ PITFALLS:
  - Colunas são MINÚSCULAS: open, high, low, close (não 'Open', 'High' como yfinance)
  - Modo 'nologin' — dados podem ser limitados, mas funciona sem conta
  - Ouro usa exchange='OANDA', forex usa exchange='FX'
  - Símbolo SEM prefixo: 'GBPJPY', não 'FX:GBPJPY'
  - Intervalos: in_1_minute, in_5_minute, in_15_minute, in_30_minute, in_1_hour, in_4_hour, in_daily
  - MUITO mais dados que Yahoo: 3-6x mais FVGs detectados
