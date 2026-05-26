# Pipeline Dual Agente+Cérebro — Configuração (23/05/2026)

## Arquitetura

```
┌─────────────────────────────────────────────────┐
│                   CÉREBRO                         │
│  (no_agent — zero tokens — scripts Python)       │
│                                                   │
│  brain_signal_generator.py                        │
│    → Yahoo Finance M15 (USDJPY, EURUSD, GBPUSD)   │
│    → Detecta CHoCH + FVG (gap ≥ 5 pips)           │
│    → Salva em signals_pending.json                │
│                                                   │
│  brain_study_session.py                           │
│    → Coleta material (RSS, YouTube, BabyPips)     │
│    → Backtest parâmetros                          │
│    → Detecta padrões de estrutura                 │
│    → Escreve descobertas na Knowledge Bridge      │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│         signals_pending.json                     │
│  [                                                 │
│    {"pair":"USDJPY","type":"BULLISH",              │
│     "fvg_pips":7.2,"entry_zone":"159.00-159.10"}  │
│  ]                                                 │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│                   AGENTE                          │
│  (com tokens — validação inteligente)             │
│                                                   │
│  1. Lê signals_pending.json                       │
│  2. Navega no TradingView (browser tools)          │
│  3. Valida visualmente o setup                    │
│  4. Confronta com análise própria (Yahoo Finance) │
│  5. Decide: EXECUTAR ou REJEITAR                   │
│  6. Executa → mt5_order_executor.py (ydotool)     │
│  7. Registra no agent_context.json                 │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│            MT5 IC Markets Demo                    │
│  (DISPLAY=:0 — desktop real do Roberto)           │
│                                                   │
│  mt5_order_executor.py:                           │
│    → ydotool key F9 (New Order)                    │
│    → type símbolo + Tab + volume + SL + TP        │
│    → Alt+B (Buy) ou Alt+S (Sell)                  │
│    → Enter (confirmar)                             │
└─────────────────────────────────────────────────┘
```

## Arquivos de Estado

| Arquivo | Dono | Conteúdo |
|---------|------|----------|
| `agent_context.json` | Agente | Tarefas ativas, decisões, fase atual |
| `brain_context.json` | Cérebro | Módulos ativos, status forex, modo estudo |
| `signals_pending.json` | Ambos | Fila de sinais pendentes de validação |
| `knowledge_bridge.json` | Ambos | Descobertas e conhecimento compartilhado |
| `mt5_execution_log.json` | Agente | Log de ordens executadas no MT5 |

## Regras de Separação

- Agente NUNCA escreve no `brain_context.json`
- Cérebro NUNCA escreve no `agent_context.json`
- `knowledge_bridge.json` e `signals_pending.json` são compartilhados (ambos escrevem)
- Consulta cruzada via `bridge_context.py` é apenas LEITURA

## Fluxo de Decisão do Agente

```
1. Ler signals_pending.json
2. Para cada sinal:
   a. Abrir TradingView (browser) no par+timeframe
   b. Verificar se FVG realmente existe (gap visual)
   c. Verificar se CHoCH é legítimo (quebra de estrutura clara)
   d. Verificar horário (UTC 6-7 ou 15-16)
   e. Se válido → mt5_order_executor.py
   f. Se inválido → mover para "rejected" no signals_pending.json
3. Escrever descobertas na knowledge_bridge.json
```

## Comandos Úteis

```bash
# Ver pipeline state
cat ~/.hermes/forex/signals_pending.json | python3 -m json.tool

# Ver knowledge bridge
python3 ~/.hermes/scripts/knowledge_bridge.py read

# Ver contexto cruzado
python3 ~/.hermes/scripts/bridge_context.py cross

# Executar ordem manual
python3 ~/.hermes/scripts/mt5_order_executor.py BUY USDJPY 0.01 --sl 159.00 --tp 159.45

# Rodar scanner manualmente
python3 ~/.hermes/scripts/brain_signal_generator.py
```
