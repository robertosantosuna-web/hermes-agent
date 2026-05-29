# NEO CLI Tool — `neo` command

Desktop CLI para falar com a ENTIDADE diretamente do terminal.

**Instalação:** `/usr/local/bin/neo` (symlink → `~/.hermes/scripts/neo`)
**Requer:** NEO agent rodando (`systemctl --user status neo-agent`)

## Comandos

```bash
neo status            # Status rápido + últimos logs
neo check             # Ping/pong — teste de vida (timeout 20s)
neo "sua pergunta"    # Conversa com dados reais injetados (timeout 90s)
echo "msg" | neo      # Via stdin também funciona
```

## Como funciona

1. `neo` escreve mensagem no `~/.hermes/neural/bridge_outbox.json` como:
   ```json
   {"direction": "hermes->neural", "type": "task", "content": "...", "source": "cli"}
   ```
2. Consciousness Loop verifica bridge a cada ciclo (~15s)
3. NEO processa via Ollama local
4. Resposta salva em `~/.hermes/neo/data/last_response.json`
5. `neo` faz polling (a cada 2s) até receber resposta ou timeout

## Timeouts

- `neo check`: 20s (ping/pong rápido)
- `neo <msg>`: 90s (considera 15s loop + 15s Ollama + margem)
- Sinal de progresso: pontos `.` a cada 2s de espera

## Data Injection

O consciousness loop detecta palavras-chave na pergunta e injeta dados reais:
- "status", "ecossistema", "cron", "job" → health check completo
- "forex", "trade", "bot", "posição", "saldo" → status forex
- "telegram", "mensagem", "canal" → status Telegram

Isso compensa o modelo pequeno (llama3.2:3b) que não faz tool-use confiável.
