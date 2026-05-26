# Pipeline Scripts — Maio 2026

## Scripts ativos

### forex_bot_real.py
Bot principal. CHoCH+FVG M15 com execução real no MT5. Zero tokens.
- Dados: Yahoo Finance (provisório, migrar para TradingView)
- Dedup: verifica `trade_log.json` antes de abrir — 1 trade por par+direção por dia
- Notificação: silencioso sem trade. Com trade: `⚡ N trade(s) | PAIR DIR WR=X%`
- Cron: `21f7caf29606` — `*/15 4-17 * * 2-4`, deliver `origin`

### mt5_direct.py
Executor de ordens no MT5 via xdotool (F9 + Alt+B/S).
- `place_choch_order(pair, direction, entry, fvg, atr)` — ordem CHoCH+FVG
- `close_all()` — fecha todas as posições (Ctrl+T + menu)
- `focus_mt5()` — windowfocus (Xvfb não tem WM, windowactivate falha)

### trade_tracker.py
Registra trades em `~/.hermes/forex/trade_log.json`.
- `record_trade(direction, pair, entry, sl, tp)` — registra entrada
- `daily_summary()` — WR + P&L do dia

### trade_closer.py
Fecha trades no log monitorando saldo MT5.
- `close_trades_by_balance()` — compara saldo atual com inicial, distribui P&L
- `health_check()` — verifica se terminal64.exe está vivo
- `get_mt5_balance()` — OCR do terminal MT5 (ruidoso, preferir xdotool Ctrl+C)
- Cron: `5e12477198e4` — `*/10 * * * 2-4`, deliver `local`

### vision_engine.py
Motor de captura + OCR.
- Backends: Xvfb (MT5), grim (Wayland wlr), browser (CDP)
- `mt5` — captura Xvfb :99 + OCR
- `mt5_account` — captura região inferior (saldo)
- Pitfall: GNOME Wayland bloqueia screenshots não-interativos

### forex_daily_review.py
Relatório diário 18h. Só emite se teve trade no dia.
- Cron: `c79a771c95a0` — `0 18 * * 2-4`, deliver `origin`

### forex_choch_m15.py
Simulação golden hours. Roda em silêncio (local).
- Cron: `74f1169e6e66` — `0 7,10,14,16 * * 2-4`, deliver `local`

## Infraestrutura

### Cron jobs forex (todos no-agent, zero tokens)

| Job | ID | Script | Schedule | Deliver |
|-----|-----|--------|----------|---------|
| 🤖 Trading REAL | 21f7caf29606 | forex_bot_real.py | */15 4-17 Ter-Qui | origin |
| 📊 Golden Hours | 74f1169e6e66 | forex_choch_m15.py | 07,10,14,16 Ter-Qui | local |
| 💰 Trade Closer | 5e12477198e4 | trade_closer.py | */10 Ter-Qui | local |
| 🩺 MT5 Health | 8f3e0f2d4f3e | trade_closer.py health | */30 Ter-Qui | local |
| 📊 Daily Review | c79a771c95a0 | forex_daily_review.py | 18:00 Ter-Qui | origin |
| 🔒 Fechar Ordens | de69bd5aa118 | forex_fechar_sexta.sh | 16:00 Sex | origin |

## MT5 OANDA Demo
- Conta: 1715539800, Server: OANDA_Global-Demo-1
- Senha: wc0ZO6#p
- Wine + Xvfb :99 (1280x720)
- VNC: `x11vnc -forever -shared -nopw -display :99` → `vncviewer localhost:5900`

## PITFALLS

### Dedup cross-run
O mesmo sinal CHoCH pode persistir por múltiplos candles M15. Sem verificação, o bot reabre o mesmo trade a cada tick. Solução: `forex_bot_real.py` verifica `trade_log.json` e pula par+direção já tradados no dia.

### P&L tracking
`trade_tracker.py` registra entrada mas não fecha. `trade_closer.py` monitora saldo MT5 a cada 10min e fecha trades quando detecta mudança. Daily review consome `trade_log.json`.

### OCR não confiável
Saída típica do MT5: "2- - +". Para dados financeiros, preferir xdotool (Ctrl+C no Trade Terminal) ou F9+Tab para navegar campos. OCR serve para confirmação visual (menu, janela aberta).

### Yahoo Finance → TradingView
Usuário determinou TV como fonte única (17:38 20/05). Migração pendente. Yahoo Finance é provisório — detecta padrões CHoCH+FVG mas não tem a precisão do TV.
