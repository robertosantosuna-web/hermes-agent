# TradingView Scanner API — Descoberta e Documentação

**Data:** 18/05/2026
**Descoberta:** API interna do scanner do TradingView funciona sem autenticação

## Endpoint

```
POST https://scanner.tradingview.com/forex/scan
Content-Type: application/json
```

## Headers necessários

```python
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/148.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Origin': 'https://br.tradingview.com',
    'Referer': 'https://br.tradingview.com/',
})
```

## Payload

```json
{
  "symbols": {"tickers": ["FX:EURUSD", "FX:GBPUSD", "FX:USDJPY", "FX:AUDUSD", "FX:EURGBP", "FX:EURJPY"]},
  "columns": [
    "close", "high", "low", "open", "volume", "change",
    "Recommend.All",
    "RSI", "RSI[1]",
    "MACD.macd", "MACD.signal",
    "SMA20", "SMA50",
    "BB.upper", "BB.lower",
    "ATR", "Volatility.D"
  ]
}
```

## Tickers mapeados

| Par | Ticker TV |
|-----|----------|
| EUR/USD | FX:EURUSD |
| GBP/USD | FX:GBPUSD |
| EUR/GBP | FX:EURGBP |
| USD/JPY | FX:USDJPY |
| AUD/USD | FX:AUDUSD |
| EUR/JPY | FX:EURJPY |

## Resposta (exemplo EUR/USD)

```json
{
  "totalCount": 6,
  "data": [
    {"s": "FX:EURUSD", "d": [1.16377, 1.16451, 1.16083, 1.16179, 75189, 0.11, -0.29, 42.79, 41.09, -0.00013, 0.00133, 1.17105, 1.16466, 1.17902, 1.16307, 0.00626, 0.31701]}
  ]
}
```

Índices no array `d`:
0. close, 1. high, 2. low, 3. open, 4. volume, 5. change%
6. Recommend.All, 7. RSI, 8. RSI[1], 9. MACD, 10. MACD signal
11. SMA20, 12. SMA50, 13. BB.upper, 14. BB.lower, 15. ATR, 16. Volatility.D

## Performance

- 6 pares em 1 chamada
- ~200ms de latência
- Sem rate limit observado
- Dados em tempo real (candle atual)

## Limitações

- Não retorna séries históricas (apenas snapshot do candle atual)
- Não tem endpoints para abrir/fechar ordens (é só dados)
- Para histórico: Yahoo Finance como fallback

## Módulo Python

`~/.hermes/forex/tv_data.py` — wrapper completo com get_live_quotes() e caching de sessão.
