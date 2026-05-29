# TradingView CDP — Limitações e Workarounds (26/05/2026)

## Bar Replay

**Limitação:** Requer conta paga (Pro ou superior). Conta free mostra popup promocional.
**Workaround:** `smc_fractal_detector.py` — mesmo algoritmo do Pine Script, offline, em Python.
Pode testar a metodologia SMC nos dados históricos locais sem depender do TV.

## Pine Editor via CDP

**Limitação:** O editor Pine abre em painel lateral que não é capturado pelo accessibility tree.
Canvas DOM não expõe elementos navegáveis. Não é possível colar código ou interagir programaticamente.
**Workaround:** Usar o site TradingView manualmente OU o script `ict_concepts_luxalgo.pine` 
salvo localmente para referência. O indicador pode ser adicionado manualmente via Interface → Pine Editor → Open → paste.

## Extração de Dados OHLC via CDP

**Limitação confirmada:** Todas as 7 abordagens de extração falharam (ver `references/cdp-ohlc-extraction-investigation.md`):
- `_exposed_chartWidgetCollection` — apenas 2 keys, sem acesso a dados
- `_chartWidgetsDefs[0].chartWidget._dataWindowWidget` — sem renderer de dados
- `exportData()` / `getBars()` — métodos não expostos
- `fetch()` endpoints internos — bloqueado por CORS
- DOM scraping — valores não estão no DOM (canvas-only)
- Context menu "Export chart data" — não dispara com eventos sintéticos

**Workaround:** `tv_data.py v2` híbrido: yfinance (OHLC 400+ candles) + CDP live quote (preço no `<title>`)

## Interação com a UI

**Limitação:** TradingView usa arquitetura canvas pura para o chart. Apenas a toolbar superior 
e a watchlist lateral são HTML navegável. Painéis (Pine Editor, Indicator Search) abrem em 
regiões que o accessibility tree pode ou não capturar dependendo da versão.

## Fonte Alternativa: TradingEconomics Calendar

**Descoberto via Dinei (chat export 04-11/05/2026):** 
- https://tradingeconomics.com/calendar — acessível, HTTP 200, sem Cloudflare
- Investing.com bloqueado por Cloudflare — NÃO usar
- Use `curl` ou `requests` com header User-Agent para extrair dados do calendário

## Referências

- `references/cdp-ohlc-extraction-investigation.md` — investigação completa CDP→OHLC
- `forex/smc_fractal_dinei.md` — metodologia SMC alternativa ao TV replay
- `scripts/smc_fractal_detector.py` — detector Python (substituto do replay)
- `forex/ict_concepts_luxalgo.pine` — indicador Pine Script para uso manual no TV
