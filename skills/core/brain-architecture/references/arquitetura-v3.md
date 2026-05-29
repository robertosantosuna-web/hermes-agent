# ENTIDADE v3.0 — Arquitetura Cerebral
## Conselho de IA: 28/05/2026

## Arquitetura Consolidada

14 agentes em produção rodando via 16 cron jobs.
Tálamo unificado substituindo 8 bridges JSON.

### Estrutura

```
~/.hermes/brain/
├── thalamus.py          # Canal único (8 bridges → 1)
├── amygdala.py          # Detector de ameaças (5min)
├── lobo_frontal.py      # Planejador (30min)
├── cortex_visual.py     # Análise forex multi-confluência SMC (15min seg-sex)
├── autopilot.py         # Gestão de posições (3min seg-sex)
├── area_broca.py        # Comunicação (30min)
├── hippocampus.py       # Memória/padrões (6h)
├── n_accumbens.py       # Reforço/pesos (4h)
├── cerebellum.py        # Validação (on-demand)
├── meta_observer.py     # Auto-observação (15min)
├── motor_local.py       # Leitura MT5 (1min)
├── sona_lite.py         # Aprendizado contínuo
├── gateway_guard.py     # Proteção (10min)
├── ollama_keepalive.py  # Mantém Ollama (5min)
├── working_memory.py    # Memória de trabalho persistente
├── attention_manager.py # Fila de prioridade
└── mt5_history_extractor.py  # Extrai histórico MT5 via EA bridge
```

### Conselho de Especialistas IA

Documentado em `~/.hermes/brain/council/prompts.md`:
6 prompts prontos para consultar Gemini, GPT-5, Grok, Claude, Codex, Copilot.

### Bibliotecas Instaladas

- smartmoneyconcepts: FVG, OB, Liquidity, BOS/CHoCH, SMT
- backtesting.py: Backtest interativo
- quantstats: Sharpe, drawdown, métricas
- mplfinance: Gráficos candles
- yfinance: Dados mercado

### Pitfalls Conhecidos

1. **CRON**: `*/15 * * * 1-5` está ERRADO. O quarto campo são dias do mês. Correto: `*/15 * * * * 1-5`
2. **MT5 Bridge**: Lê `hermes_resp.json` via Wine em `~/.wine/.../Common/Files/`
3. **DPI Wine**: Ajustar `LogPixels=0x60` (96) em `~/.wine/user.reg` para 100% scaling

### Referências

- Plano completo: `~/.hermes/plans/entidade-v3-consciencia-expandida.md`
- Análise do conselho: `~/.hermes/brain/council/analise_final.md`
- Relatório de erros: `~/.hermes/forex/ERROR_ANALYSIS.md`
- Backtest report: `~/.hermes/forex/BACKTEST_REPORT.md`