# 99Freelas Message Extraction — CDP via Real Desktop Brave

# Extração de Conversas do 99Freelas via CDP — Brave Real (:9222)

> Última validação: 24/05/2026 — Projeto Martin L. (16525119)

## Regra de Ouro: SEMPRE verificar no site, NUNCA confiar só em email/memória

O email do 99Freelas TRUNCA mensagens (ex: "Gostei da organização... gostaria de evoluir gradualmente a estrutura ..."). A mensagem COMPLETA só está no site. Quando o usuário disser "tem resposta do Martin", NÃO liste o que você lembra ou o que viu no email — ABRA o 99Freelas e extraia a conversa completa.

## Dois Bravos, Duas Portas

| Porta | Tipo | Cloudflare | Usar para |
|-------|------|------------|-----------|
| **9222** | Desktop real Wayland | ✅ Bypassa | 99Freelas, TradingView logado |
| 9223 | Headless | ❌ Bloqueado | Sites sem Cloudflare |

**SEMPRE usar porta 9222 para 99Freelas.** A sessão tem cookies reais do Roberto (Google OAuth, 99Freelas logado).
- Valid session cookies (Google OAuth, 99Freelas login, TradingView)
- Wayland display for visual rendering
- Persistent profile at `$HOME/.config/BraveSoftware/Brave-Browser`

## Extracting 99Freelas Messages

### 1. Connect to the right port

```bash
# Check available tabs
curl -s http://localhost:9222/json/list | python3 -m json.tool
```

### 2. Find the 99Freelas tab

The inbox tab URL pattern: `https://www.99freelas.com.br/messages/inbox/<ID>`

### 3. Extract conversation via CDP WebSocket

```python
import asyncio, json, websockets

TAB_ID = '<target-id-from-json-list>'
WS_URL = f'ws://localhost:9222/devtools/page/{TAB_ID}'

async def extract():
    async with websockets.connect(WS_URL) as ws:
        # Enable Runtime
        await ws.send(json.dumps({
            'id': 1, 'method': 'Runtime.enable'
        }))
        await ws.recv()
        
        # Extract all page text
        await ws.send(json.dumps({
            'id': 2, 'method': 'Runtime.evaluate',
            'params': {
                'expression': 'document.body.innerText',
                'returnByValue': True
            }
        }))
        resp = json.loads(await ws.recv())
        text = resp['result']['result']['value']
        return text

asyncio.run(extract())
```

### 4. Click on a conversation

The inbox page loads a LIST view — the conversation panel only activates after clicking a conversation item:

```javascript
// Find and click the conversation container (not just the name text)
const all = document.querySelectorAll('*');
for (const el of all) {
    if (el.children.length === 0 && el.textContent.includes('CLIENT_NAME')) {
        // Walk up to find the clickable container (usually an <a> tag)
        let parent = el.parentElement;
        for (let i = 0; i < 5; i++) {
            if (parent && parent.tagName === 'A') {
                parent.click();
                return 'Clicked: ' + parent.href;
            }
            parent = parent.parentElement;
        }
    }
}
```

### Pitfalls

- **InnerText truncation**: The sidebar preview truncates messages. Always use `document.body.innerText` for full content.
- **SPA navigation**: After clicking a conversation, wait 2-3 seconds for React to render the chat panel.
- **Page errors**: The page may show "Ocorreu um erro inesperado" — this doesn't affect the already-rendered message content in the DOM.
- **The textarea at bottom** ("Pressionar Enter para Enviar") indicates the chat is active and ready for input.
