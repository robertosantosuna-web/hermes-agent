# TradingView Scanner API — Acesso gratuito a dados forex em tempo real

## Descoberta (18/05/2026)

O TradingView expõe uma API interna de scanner (`scanner.tradingview.com/forex/scan`) que retorna dados OHLCV + indicadores técnicos sem autenticação.

## Endpoint

```
POST https://scanner.tradingview.com/forex/scan
Content-Type: application/json
```

### Payload mínimo
```json
{
  "symbols": {"tickers": ["FX:EURUSD", "FX:GBPUSD", "FX:USDJPY"]},
  "columns": ["close", "high", "low", "open", "volume", "change"]
}
```

### Response
```json
{
  "totalCount": 3,
  "data": [
    {"s": "FX:EURUSD", "d": [1.16382, 1.16451, 1.16083, 1.16179, 75135, 0.11]},
    ...
  ]
}
```
O array `d` corresponde à ordem das `columns` no request.

## Mapeamento de pares → tickers

| Par | Ticker TradingView |
|-----|-------------------|
| EUR/USD | FX:EURUSD |
| GBP/USD | FX:GBPUSD |
| USD/JPY | FX:USDJPY |
| AUD/USD | FX:AUDUSD |
| EUR/GBP | FX:EURGBP |
| EUR/JPY | FX:EURJPY |

## Colunas disponíveis (testadas e funcionando)

```
close, high, low, open, volume, change,
Recommend.All,
RSI, RSI[1],
MACD.macd, MACD.signal,
SMA20, SMA50,
BB.upper, BB.lower,
ATR, Volatility.D
```

- **Recommend.All**: -1 (venda forte) a +1 (compra forte)
- **RSI[1]**: valor do RSI no candle anterior
- **ATR**: Average True Range (14 períodos, D1)

## Headers obrigatórios

```python
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/148.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Origin': 'https://br.tradingview.com',
    'Referer': 'https://br.tradingview.com/',
}
```
**SEM Origin/Referer → 403 Forbidden.**

## Filtro de timeframe
```json
{"filter": [{"left": "timeframe", "operation": "equal", "right": "15"}]}
```
Timeframes: `1`, `5`, `15`, `60`, `240`, `1D` — todos ok.

## Vantagens sobre Yahoo Finance

| Critério | TradingView Scanner | Yahoo Finance |
|----------|-------------------|---------------|
| Indicadores | RSI, MACD, SMA, BB, ATR, Recommend | Nenhum |
| Múltiplos pares | 6+ em 1 chamada | 1 por chamada |
| Timeframes | M1 a D1 | Apenas D1 |
| Latência | ~200ms | ~500ms |

## Pitfalls

- API interna/não documentada — pode mudar sem aviso
- Sessão requests.Session() com headers persistentes reduz latência
- Dados históricos limitados (snapshot atual). Para séries longas: Yahoo Finance
