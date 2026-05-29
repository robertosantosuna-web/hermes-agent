# Browser CDP — Multi-Agent Orchestration

## Quick Reference

### Iniciar Brave com debug
```bash
pkill -9 brave; sleep 2; brave-browser --remote-debugging-port=9222 --remote-allow-origins='*' &
```

### Verificar conectividade
```bash
curl -s http://localhost:9222/json/version | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('Browser','?'))"
```

## Agentes IA Configurados

| Agente | URL | Login | Status (27/05) |
|--------|-----|-------|----------------|
| chatgpt | chat.openai.com | Google | 🔐 pendente |
| claude | claude.ai | Google | 🔐 pendente |
| gemini | gemini.google.com | Google | 🔐 pendente |
| deepseek | chat.deepseek.com | Google ✅ | ✅ logado (177 cookies) |
| copilot | copilot.microsoft.com | Microsoft | 🔐 pendente |

## Fluxo de Login

1. NEO abre `{agent}.url`
2. Usuário clica "Sign in with Google" (sessão Google já ativa no Brave)
3. NEO detecta que não está mais em página de login
4. NEO salva cookies em `~/.hermes/neo/data/browser_sessions/{agent}_cookies.json`
5. Próximas sessões: NEO carrega cookies → login automático

## CDP WebSocket

- Navegação: `Page.navigate` (WebSocket, não HTTP `/json/navigate`)
- Input: `Input.dispatchKeyEvent` com `type: "char"` para cada caractere
- Avaliação: `Runtime.evaluate` com `returnByValue: true`
- Cookies: `Network.getAllCookies`

### Pitfall: HTTP /json/navigate não funciona em SPAs
Usar sempre WebSocket `Page.navigate` — o endpoint HTTP `/json/navigate` falha silenciosamente com SPAs modernas que usam client-side routing.

### Pitfall: textarea.value + dispatchEvent não funciona
Para campos `textarea` em SPAs React/Vue, usar `Input.dispatchKeyEvent` caractere por caractere. Não usar `el.value = 'texto'` + `dispatchEvent(new Event('input'))`.

### Pitfall: Brave requer --remote-allow-origins='*'
Sem essa flag, conexões WebSocket de `localhost:9222` recebem 403 Forbidden.
