# Arquitetura da ENTIDADE — v2.6 (27/05/2026)

## Camadas Operacionais

```
NÍVEL 0: ROBERTO (autoridade suprema)
│
├── NÍVEL 1: CÓRTEX DUAL (decisor estratégico)
│   ├── Lobo Esquerdo: Hermes (DeepSeek V4)
│   │   Análise, decisão, comunicação, orquestração
│   └── Lobo Direito: Codex (GPT-5.5)
│       Código, backtest, scripts, implementação
│   Ponte: cortex_bridge.py → cortex_sync.json
│
├── NÍVEL 2: AGENTE NEURAL (executor autônomo) ← NOVO v1.0
│   Processo systemd independente
│   Ollama llama3.2:3b (zero API cost)
│   Loop contínuo 15s, pipeline de tarefas
│   Memória própria, bridge JSON com Hermes
│   Local: ~/.hermes/neural/agent.py
│
├── NÍVEL 3: CÉREBRO BI-NEURAL (scripts cron)
│   Executive, Cerebellum (mantidos por segurança)
│   Demais módulos → migrando para Agente Neural
│
└── NÍVEL 4: REDE NEURAL TRIPLA
    NN-Brain, NN-Agent, NN-Shared (526 neurônios)
    Feed-forward diário, backprop por trades
```

## Princípios

- **Hermes delega, Neural executa** — reduz tokens do Hermes
- **Neural é subordinado ao Córtex Dual** — não decide estratégia
- **Neural tem autonomia operacional** — health checks, monitoramento, tarefas repetitivas
- **Comunicação via bridge JSON** — inbox/outbox assíncrono
- **Zero API cost no Neural** — Ollama local, sem créditos
