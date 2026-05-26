# Forex Pipeline — Produção (18/05/2026)

## Fonte de dados primária: TradingView Scanner API
- URL: `https://scanner.tradingview.com/forex/scan`
- **Não requer login.** Headers: User-Agent Chrome 148, Origin tradingview.com
- Retorna por chamada: OHLCV + RSI, MACD, SMA20, SMA50, BB.upper/lower, ATR, Volatility, Recommend.All
- 6 pares simultâneos em ~200ms. Timeframes: 1, 5, 15, 60, 240, 1D
- Módulo: `~/.hermes/forex/tv_data.py` → `get_live_quotes(['EUR/USD', ...])`

## 3 Picos de volume
| Pico | Horário BRT | Pares | Volume |
|------|------------|-------|--------|
| London Open | 05:00 | EUR/USD, GBP/USD, EUR/GBP | ~30% |
| NY Overlap ⭐ | 10:00 | EUR/USD, GBP/USD, USD/JPY | ~50% |
| Asian Open | 21:00 | USD/JPY, AUD/USD, EUR/JPY | ~17% |

## Calendário de blackout (restrições reais de corretoras)
| Importância | Bloqueio | Exemplos |
|------------|----------|----------|
| ★★★ RED | 15 min antes / 5 min depois | NFP, FOMC, CPI, ECB, BOE |
| ★★ ORANGE | 10 min antes / 3 min depois | Jobless Claims, ISM, GDP, Retail |
| ★ YELLOW | 5 min antes / 2 min depois | Speeches, auctions |

Módulo: `~/.hermes/forex/forex_calendar.py` → `should_block_trading(pico, pairs)`

Janelas diárias fixas (GMT → BRT = -3h):
- 12:30 GMT (09:30 BRT): US MAIN data ★★★ → blackout 09:15-09:35
- 14:00 GMT (11:00 BRT): US secondary ★★
- 18:00 GMT (15:00 BRT): FOMC window ★★★

## Cron jobs (7 ativos)
```
04:55 🔍 Análise London   → 05:00 🚀 Execução London  (seg-sex)
09:55 🔍 Análise NY        → 10:00 🚀 Execução NY      (seg-sex)
20:55 🔍 Análise Asia      → 21:00 🚀 Execução Asia    (seg-sex)
16:00 🔒 Fechar ordens     (sexta-feira)
```

## Regras de trading
1. **Day trade**: abre e fecha no mesmo dia (ordens_abertas.json)
2. **Notícias**: bloqueia -5min antes de ★★★ até +5min depois
3. **Sexta-feira**: não abre após 13:00 BRT, fecha tudo 16:00 BRT
4. **Fim de semana**: não opera
5. **Alavancagem 50x**: risco 1% por trade, relação 1:3 (busca 3x o risco)

## Pipeline (forex_pipeline_v2.py)
- `analise --pico ny` → busca TradingView, analisa RSI/MACD/SMA, salva JSON
- `executar --pico ny` → lê JSON, confirma com dados frescos, abre ordens simuladas
- `status` → ordens abertas, próximas janelas de notícias, últimos trades
- `fechar` → fecha todas as ordens abertas

## OANDA (conta demo pendente)
- API REST v20, `oandapyV20` instalado e testado
- Config: `~/.hermes/forex/oanda_config.json` (token + account_id)
- Cliente pronto: `~/.hermes/forex/oanda_client.py` (status, quote, trade, close_all)
- Registro: formulário React em hub.oanda.com/apply/demo — requer preenchimento manual
- Conta demo gratuita com dados reais. Prática: api-fxpractice.oanda.com

## Virtual Desktop
- `~/.hermes/scripts/virtual_desktop.py` — teclado + mouse virtual
- Backends: pynput ✅, pyautogui ✅, ydotool ✅, wtype ✅
- Wayland bloqueia screenshots. Mouse/teclado via pynput funcionam.
- Comandos: move, click, type, key, hotkey, open_url, run

## Pitfalls
- Google OAuth bloqueia browser automatizado (confirmado)
- Yahoo Finance yfinance retorna arrays numpy → usar `float(x)` ou API direta
- TradingView symbol search precisa de headers de browser real (session + Origin)
- OANDA formulário React não avança em browser headless
