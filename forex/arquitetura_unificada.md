# Arquitetura de Unificação — Hermes + RUFLo + TradingView

## 📡 Pipeline de Dados (TradingView como fonte única)

```
TradingView (Pine Script CHoCH+FVG)
    │
    ├─→ Alertas/Webhooks ──→ Webhook Server ──→ MT5 Executor (F9)
    │
    ├─→ Dados OHLCV ──→ neural-trader (Rust Backtest)
    │                        │
    │                        ├─→ LSTM/Transformer (validação)
    │                        ├─→ Risk Analyst (VaR/CVaR)
    │                        └─→ AgentDB (memória)
    │
    └─→ Visualização (Browser CDP)
```

## 🔌 Pontos de Integração

### 1. SINAL → EXECUÇÃO
- Pine Script CHoCH+FVG roda no TradingView
- Alerta/webhook envia sinal (par, direção, entry, SL, TP)
- `mt5_direct.py` recebe e executa F9 no MT5
- **Status:** Pine Script pronto, webhook a configurar

### 2. DADOS → BACKTEST
- Dados OHLCV do TradingView → neural-trader
- Backtest Rust/NAPI (8-19x mais rápido)
- Compara resultado com backtest Pine Script
- **Status:** Precisa bridge TV→neural-trader

### 3. RISCO → PROTEÇÃO
- neural-trader risk-analyst monitora posições
- Circuit breakers: -3% dia, -5% semana, corr > 0.85
- Kelly criterion para sizing
- **Status:** neural-trader a instalar

### 4. MEMÓRIA → APRENDIZADO
- AgentDB armazena padrões de sucesso
- RAG retrieval para reuso de estratégias
- SONA trajectory learning
- **Status:** RUFLo AgentDB a configurar

### 5. ORQUESTRAÇÃO → SWARM
- Agentes especializados: estrategista, risco, mercado
- Swarm coordena múltiplas estratégias em paralelo
- Hermes Agent como orchestrator principal
- **Status:** RUFLo a instalar

## 📋 Plano de Implementação (Fases)

### Fase 1 — Imediato (hoje)
- [x] MT5 OANDA conectado + executor F9
- [x] TradingView 4 pares M15 abertos
- [x] Pine Script CHoCH+FVG carregado
- [ ] Instalar neural-trader + validar backtest
- [ ] Bridge TradingView → neural-trader

### Fase 2 — Curto prazo (2-3 dias)
- [ ] Configurar webhooks TradingView → executor
- [ ] neural-trader risk-analyst ativo
- [ ] AgentDB para memória de trades
- [ ] Validar com conta demo OANDA

### Fase 3 — Médio prazo (1-2 semanas)
- [ ] Swarm multi-agente (estrategista + risco + mercado)
- [ ] LSTM/Transformer para confirmação de sinais
- [ ] Migrar para conta real
- [ ] Contas em XM + Exness como backups

### Fase 4 — Longo prazo
- [ ] Federation: agentes em máquinas separadas
- [ ] Cloud backtesting (Anthropic Managed Agents)
- [ ] Portfolio optimization multi-ativo
