# Yahoo Finance Ban — TradingView CDP Migration (25/05/2026)

## Rule (25/05)

**Yahoo Finance PROIBIDO em todos os scripts forex. Zero exceções.**

Fonte primária: **TradingView CDP** via `brain_browser.py` (porta 9223 IPv6, headless, systemd).

## Scripts corrigidos

| Script | Antes | Depois |
|--------|-------|--------|
| `brain_gateway.py` | `query1.finance.yahoo.com` | MT5 IC Markets (Bid/Ask/Spread) |
| `forex_bot.py` | Yahoo `fetch_m15()` | `forex_quote.py` (TradingView CDP) |
| `forex_bot_real.py` | `import yfinance as yf` | `from tv_data import fetch_ohlcv` |

## New pipeline (zero Yahoo)

```
brain_browser.py (:9223 IPv6 headless)
    ↓  --navigate + --title
forex_quote.py  →  {"bid": 1.1642, "ask": 1.1644, "source": "tradingview"}
    ↓  fetch_ohlcv()
tv_data.py  →  pandas DataFrame (drop-in replacement do yf.Ticker().history())
    ↓
forex_bot.py / forex_bot_real.py
```

## Scripts

| Script | Location | Purpose |
|--------|----------|---------|
| `forex_quote.py` | `~/.hermes/scripts/` | Live quote via TradingView CDP |
| `tv_data.py` | `~/.hermes/scripts/` | Drop-in yfinance replacement (pandas) |
| `brain_browser.py` | `~/.hermes/scripts/` | CDP WebSocket controller (IPv6 9223) |

## CDP Browser quirk

Porta 9223 é **IPv6-only** (`[::1]:9223`). `localhost:9223` falha (IPv4).
Porta 9222 é o Brave real do usuário — evitar para automação.
