# Conselho de IA — Análise Consolidada (28/05/2026)

4 IAs analisaram a ENTIDADE v3.0: ChatGPT, Gemini, DeepSeek, Grok.

## Síntese por IA

| IA | Foco | Top 3 Sugestões |
|-----|------|-----------------|
| ChatGPT | Engenharia de software | Governança, observabilidade, correção cron |
| Gemini | Resiliência operacional | Trailing stop, fallback SMC, isolamento sensor/execução |
| DeepSeek | ML/AI pesado | A2C, GARCH, ChromaDB, CNN+Transformer |
| Grok | Organização | Bibliotecas, taxonomia, documentação |

## Sugestões Críticas (implementar primeiro)

1. **Trailing stop no servidor da corretora** (Gemini) — protege contra desconexão MT5
2. **Fallback Hard-coded SMC** se Ollama falhar (Gemini) — sistema não fica cego
3. **Isolar Sensor vs Execução** em processos separados (Gemini+ChatGPT)
4. **QoS no Tálamo** — alertas de ameaça passam na frente (Gemini)
5. **Cerebelo veta Amígdala** em horário de notícia (Gemini) — evita stop-loss caçado

## Correção Crítica (ChatGPT)

**CRON bug:** `*/15 * * * 1-5` roda apenas dias 1-5 do mês.
Correto: `*/15 * * * * 1-5` (5 campos + dia da semana = seg-sex).
Afetou Córtex Visual e AutoPilot — corrigido em 28/05.

## Arquitetura Alvo (consenso das 4 IAs)

```
ROBERTO → GOVERNANÇA → TÁLAMO(QoS) → 8 AGENTES → VALIDAÇÃO → EXECUÇÃO → AUDITORIA → OBSERVABILIDADE → APRENDIZADO
```

Ver análise completa em `~/.hermes/brain/council/analise_final.md`