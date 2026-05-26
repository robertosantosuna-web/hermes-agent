# Yahoo Finance Ban + TradingView CDP Migration — 25/05/2026

## Contexto
Usuário explicitamente proibiu Yahoo Finance após detectar que scripts ainda o usavam como fonte de dados. Correção aplicada em todos os scripts ativos.

## Scripts Migrados

| Script | Antes | Depois |
|--------|-------|--------|
| `forex_bot.py` | `yahoo query1.finance.yahoo.com` | `forex_quote.py` (TradingView CDP) |
| `forex_bot_real.py` | `import yfinance as yf` | `from tv_data import fetch_ohlcv` |
| `brain_gateway.py` | Yahoo Finance API cotação | MT5 IC Markets Bid/Ask |

## Novos Scripts

### `forex_quote.py`
```bash
python3 forex_quote.py EURUSD
# → {"symbol": "EURUSD", "bid": 1.16434, "ask": 1.16436, ...}
```
Usa `brain_browser.py --navigate + --title` para extrair cotação do título da página TradingView.

### `tv_data.py`
```python
from tv_data import fetch_ohlcv
df = fetch_ohlcv('EURUSD=X', period='5d', interval='15m')
# → pandas DataFrame com colunas Open, High, Low, Close
```
Drop-in replacement para `yf.Ticker().history()`. Constrói histórico de cotações via cache local (`forex/tv_quote_cache.json`).

## CDP Browser

### Portas
- `9222`: Brave REAL (IPv4) — usuário navega aqui. NÃO usar para automação.
- `9223`: Brain headless (IPv6-only `[::1]:9223`) — systemd, sempre online. Usar para automação.
- `9224`: Edge (WhatsApp Web)

### brain_browser.py
```bash
# Status
python3 brain_browser.py --status

# Navegar + título (cotação)
python3 brain_browser.py --navigate "https://www.tradingview.com/chart/?symbol=FX:EURUSD" --title --json

# Executar JS
python3 brain_browser.py --eval "document.title" --json
```

## Falhas Comuns

1. **`ConnectionRefusedError` no 9223**: Está usando IPv4 (`localhost:9223`). Usar `[::1]:9223`.
2. **`MetaTrader5` import fail**: Pip package é Windows-only. Não existe no Linux.
3. **Empty OHLCV do TradingView**: A estrutura interna do TradingView é ofuscada. Extrair título é confiável; extrair OHLCV do DOM/JS é frágil. Usar `brain_signal_generator.py` para análise de padrões.
