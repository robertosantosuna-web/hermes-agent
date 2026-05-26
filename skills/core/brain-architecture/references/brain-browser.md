# Brain Browser — Navegador Interno do Cérebro

**Date:** 2026-05-23
**Service:** hermes-brain-browser (systemd user)
**CDP:** http://localhost:9223

## Arquitetura

O cérebro tem seu próprio navegador Brave/Chromium rodando 24/7 em modo headless.
Acessível via CDP pelo Hermes Agent E pelos scripts Python do cérebro.

```
hermes-brain-browser.service
  │
  ├── Brave headless (porta 9223)
  │     ├── Hermes Agent: browser_navigate, browser_click, browser_snapshot
  │     └── Brain scripts: brain_browser.py --navigate, --eval, --screenshot
  │
  ├── Cookies: ~/.hermes/browser/tradingview_cookies.json
  │     └── tv_session_restore.py (ExecStartPre + ExecStartPost)
  │
  └── Logs: ~/.hermes/browser/logs/
```

## Comandos do Cérebro

```bash
# Navegar para chart forex
python3 scripts/brain_browser.py --navigate 'https://www.tradingview.com/chart/?symbol=FX:EURUSD' --json

# Extrair dados da página
python3 scripts/brain_browser.py --content

# Screenshot para análise visual
python3 scripts/brain_browser.py --screenshot /tmp/eurusd_m15.png

# Executar JS (ex: pegar preço atual)
python3 scripts/brain_browser.py --eval 'document.querySelector(".price").innerText'
```

## Sites Acessíveis

| Site | CDP | Cloudflare? | Uso |
|------|-----|-------------|-----|
| TradingView | ✅ | Não | Charts forex, Pine Script, ideias |
| ForexFactory | ✅ | Não | Calendário econômico, notícias |
| DailyFX | ✅ | Não | Análise técnica |
| Forexlive | ✅ | Não | Notícias em tempo real |
| BabyPips | ❌ | Sim | — usar Desktop Daemon |
| Investopedia | ❌ | Sim | — usar Desktop Daemon |

## Pitfalls

1. **Cloudflare = bloqueio**: sites com Cloudflare (BabyPips, Investopedia) não funcionam via CDP. Fallback: Desktop Daemon + ydotool no Brave real.
2. **Cookies expiram**: sessão TradingView precisa de refresh periódico. Monitorar via `brain_browser.py --eval 'document.title'` — se retornar "Authentication", refazer login.
3. **Memória**: ~130MB. Se sistema com pouca RAM, considerar `systemctl --user stop` quando não em uso.
