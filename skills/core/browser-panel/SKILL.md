---
name: browser-panel
description: "Multi-agent debate panel via browser CDP. NEO opens multiple AI agents (ChatGPT, Claude, Gemini, DeepSeek, Copilot), loads context to make them specialists, orchestrates debate rounds until consensus. Browser automation via Chrome DevTools Protocol on Brave :9222."
---

# Browser Panel — Multi-Agent Debate via CDP

Orquestra múltiplos agentes IA através de um navegador interno (CDP). Cada agente recebe contexto completo → vira especialista → debate com outros → consenso.

## Arquitetura

```
NEO (Ollama local)
  │
  ├── Abre aba ChatGPT   → carrega contexto → especialista
  ├── Abre aba Claude    → carrega contexto → especialista
  ├── Abre aba DeepSeek  → carrega contexto → especialista
  │
  └── Orquestra debate:
      Round 1: cada um analisa o problema
      Round 2-N: debate cruzado (vê respostas dos outros)
      Round final: cada um vota + plano de ação
      → NEO sintetiza consenso
```

## Componentes

### CDP Client (`neo/execution/browser/cdp_client.py`)
WebSocket client para Chrome DevTools Protocol. Multi-tab, navegação, JavaScript eval, screenshots.

```python
from neo.execution.browser.cdp_client import get_browser
client = get_browser()  # conecta em localhost:9222 (Brave)
tabs = client.list_tabs()
tab = client.new_tab("https://chat.openai.com/")
client.evaluate(tab.target_id, "document.title")
```

### AI Connectors (`neo/execution/browser/agents.py`)
Conectores para 5 plataformas IA com selectors CSS mapeados:

| Agent | URL | Input Selector | Login Persistence |
|-------|-----|---------------|-------------------|
| chatgpt | chat.openai.com | #prompt-textarea | Cookies salvas |
| claude | claude.ai | div[contenteditable] | Cookies salvas |
| gemini | gemini.google.com | div[contenteditable] | Cookies salvas |
| deepseek | chat.deepseek.com | #chat-input | Cookies salvas |
| copilot | copilot.microsoft.com | #userInput | Cookies salvas |

### Debate Panel (`neo/execution/browser/panel.py`)
Orquestrador do debate multi-agente:

```python
from neo.execution.browser.panel import DebatePanel

panel = DebatePanel()
result = panel.run_full_debate(
    topic="Otimizar estratégia forex atual",
    agents=["chatgpt", "claude", "deepseek"],
    context_files=["trade_log.json", "DESIGN.md"],
    max_rounds=3
)
# → Resultado: consenso sintetizado com plano de ação
```

## Fluxo do Debate

1. **Load Context** — Carrega trade_log, config, estado MT5, DESIGN.md
2. **Open Agents** — Abre 3+ agentes em abas separadas
3. **Specialize** — Cada agente recebe: "Você é um especialista. Analise o contexto. Responda com 3 pontos críticos."
4. **Round 1** — Pergunta central: "Qual o problema? Quais as 3 ações urgentes?"
5. **Rounds 2-N** — Debate cruzado: cada agente vê respostas dos outros, refina posição
6. **Final Vote** — Cada agente vota com plano de ação e riscos
7. **Synthesize** — NEO combina votos → consenso final

## Consenso Score

Calculado por sobreposição de keywords (Jaccard):
- > 80% → debate encerra (consenso forte)
- 50-80% → continua debatendo
- < 50% → mais rodadas de esclarecimento

## NEO Tools Registradas

| Tool | Função |
|------|--------|
| `browser_delegate(agent, task)` | Envia tarefa para 1 IA |
| `browser_login_status(agent)` | Verifica quem está logado |
| `browser_open_agent(agent)` | Abre agente (precisa login 1x) |
| `panel_debate(topic, agents, rounds)` | Inicia painel de debate completo |
| `panel_status()` | Histórico de painéis anteriores |

## Setup Inicial

1. Garantir Brave aberto com debugging: `brave --remote-debugging-port=9222`
2. **Login manual 1x** em cada plataforma no Brave
3. NEO salva cookies em `~/.hermes/neo/data/browser_sessions/`
4. Sessões reutilizadas automaticamente

## PITFALLS

- **Login manual obrigatório na primeira vez** — Cloudflare/CAPTCHA impedem automação
- **Rate limiting** — Respeitar 3s entre chamadas ao mesmo agente
- **Contenteditable fields** — Telegram/Claude usam contenteditable que requer `Input.dispatchKeyEvent` (char por char), não `el.value = text`
- **Sessões expiram** — Cookies podem expirar. Se `browser_login_status` retornar false, refazer login
- **Múltiplas abas consomem RAM** — Cada aba CDP = ~200MB renderer. Fechar após uso
- **WebSocket efêmero** — Conexões WS são abertas/fechadas por comando. Não manter conexão persistente
