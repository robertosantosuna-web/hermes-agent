# AutoPilot v12 — Multi-Agente + Self-Learning (29/05/2026)

## Propósito
Bot totalmente autônomo. Pipeline: Multi-TF Bias → 5 Agentes votam → Entrada M1 → RR 3:1 → 2R/3R.
Sem NENHUMA intervenção humana. 7 pares × 2 modos (KZ + 24h), seg-sex.

**Backtest validado:** 110 trades, 62% WR, +162R, PF 4.86 em 21 dias.

## Arquitetura Multi-Agente

### 5 Agentes (em `multi_agent.py`):
- **PERFIL**: perfil do par por sessão (Asia/London/NY) — evita operar par em sessão ruim
- **SESSÃO**: Ásia como preditora de London (range contraído → breakout, expandido → continuação)
- **ESTRUTURA**: CRT + Order Block + Swing Points (peso 1.5x)
- **PADRÃO**: FVG com scoring premium/discount (gap mínimo 2p, zona correta, first touch)
- **CONFLUÊNCIA**: maioria decide, confiança mínima 30%

### Self-Learning (`self_learning.py`):
- Pesos dos agentes ajustados por resultado real
- Agentes que acertam ganham peso, quem erra perde
- Histórico salvo em `forex/agent_learning.json`

## Pipeline
1. `get_multi_tf_bias(sym)` — viés diário (W/D/H4 PDH/PDL)
2. `MULTI_AGENT.analyze(pair, highs, lows, closes, bias, pip)` — 5 agentes votam
3. Se decisão ≠ NEUTRAL → entrada M1 com FVG do agente Padrão
4. SL = 2× ATR(14) no M1, clamp 10-30p (forex) / 300p (XAU)
5. RR 3:1 fixo (nunca reduzir!)
6. Monitor 2R/3R: 2R breakeven, 3R trail

## REGRAS RÍGIDAS
- **RR 3:1 SEMPRE** — Roberto recusou RR 2:1 explicitamente
- **Validar antes de aplicar** — `validate_before_apply.py` testa em backtest 5 dias antes de ativar mudanças
- **CRT é filtro de qualidade, não substituto** — soma ao bias, não substitui
- **CDP TradingView para M1** — `fetch_ohlcv` usa CDP como fonte primária, yfinance é fallback

## Fonte de Dados M1
- **Primário**: CDP TradingView via Brave :9222 (`tv_ohlc_extractor.py`)
- **Fallback**: yfinance (limite 7 dias)
- CDP extrai 544 velas M1 reais sem erro de escala
- yfinance retorna colunas minúsculas (h/l/c) para 1d — `get_multi_tf_bias` normaliza via col_map
