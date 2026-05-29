# TradingView OHLC Extraction via CDP (29/05/2026)

Extrai dados de velas diretamente do gráfico TradingView via WebSocket CDP no Brave :9222.

## Script
`/home/roberto/tv_ohlc_extractor.py`

## Comando
```bash
python3 /home/roberto/tv_ohlc_extractor.py --symbol 'FX:EURUSD' --interval 1
python3 /home/roberto/tv_ohlc_extractor.py --symbol 'FX:EURUSD' --interval 1 --output /tmp/eurusd_m1.json
```

## Caminho interno TV
```
_exposed_chartWidgetCollection.activeChartWidget._value._modelWV._value
  .m_model._panes[0].m_mainDataSource.data().m_bars._items[]
```
Bar format: `{index, value: [timestamp, open, high, low, close, volume]}`

## Funcionamento
1. Conecta ao Brave :9222 via WebSocket CDP (`websockets.connect(ws_url)`)
2. Reusa aba TV existente ou cria nova
3. Navega para símbolo + intervalo
4. Extrai OHLCV via `Runtime.evaluate`
5. Output JSON lines (stdout) ou arquivo

## Pitfalls
- Brave :9222 bloqueia comandos de sessão CDP (`Target.attachToTarget`) mas aceita WebSocket direto
- WebSocket connection requer `websockets` package (`pip install websockets`)
- Dados limitados ao que está carregado no gráfico (~500-600 velas para M1)
- Para mais dados, navegar para trás no gráfico e re-extrair
- Não funciona no Chromium headless :9226 (bloqueia WebSocket)
