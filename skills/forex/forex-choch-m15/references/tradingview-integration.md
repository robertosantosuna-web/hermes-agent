# TradingView Integration — 23/05/2026

TradingView substituiu Yahoo Finance como fonte primária de dados para análise visual de charts forex.

## Login

- **Método:** Google OAuth (robertosantos.una@gmail.com)
- **Navegador:** Brave CDP headless (systemd: hermes-brain-browser, porta 9223)
- **Cookies:** Salvos em `~/.hermes/browser/tradingview_cookies.json`
- **Restore:** `scripts/tv_session_restore.py` roda no systemd ExecStartPre+Post

## Ferramentas

| Ferramenta | Script | Função |
|-----------|--------|--------|
| Chart Analyzer | `scripts/tv_chart_analyzer.py` | Navegar pairs, screenshots, Bar Replay, OHLC |
| Chart Scanner | `scripts/tv_chart_scanner.sh` | Cron */30 min seg-sex — screenshots automáticos 5 pares M15 |
| Session Restore | `scripts/tv_session_restore.py` | Injeta cookies de sessão no boot do navegador |

## Uso

```bash
# Set chart and screenshot
python3 scripts/tv_chart_analyzer.py --pair EURUSD --tf M15 --screenshot

# Bar Replay simulation
python3 scripts/tv_chart_analyzer.py --pair USDJPY --tf M15 --replay '2026-05-20' --replay-steps 30 --screenshot

# Get current price
python3 scripts/tv_chart_analyzer.py --pair GBPUSD --price

# Status
python3 scripts/tv_chart_analyzer.py --status
```

## Bar Replay

- Inicia com Alt+R
- Avança/retrocede com setas direita/esquerda
- Shift+seta = salto rápido
- Screenshot a cada N candles para análise visual

## Limitações

- Sites com Cloudflare (BabyPips, Investopedia) bloqueiam o CDP — usar Desktop Daemon + Brave real
- Yahoo Finance mantido como fallback para backtest quantitativo massivo (API rápida, sem Cloudflare)
