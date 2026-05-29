# CDP Account Discovery — Extração de Dados de Conta Forex

**Data:** 2026-05-26
**Validado:** Exness (my.exness.com)
**Aplicável:** Qualquer corretora com WebTerminal/Personal Area web

## Contexto

Quando o browser automatizado é bloqueado por Cloudflare/anti-bot, usar o **Brave real na porta :9222** via CDP para extrair dados de conta (número, servidor, saldo, alavancagem) sem precisar de screenshot ou interação visual.

## Pipeline de Descoberta

### 1. Listar abas e achar sessão autenticada

```python
import json, urllib.request
tabs = json.loads(urllib.request.urlopen('http://localhost:9222/json/list').read())

# Achar abas relevantes
for t in tabs:
    if 'exness' in t.get('url', '').lower():
        print(f"[{t['id']}] {t['title'][:60]}")
```

### 2. WebTerminal → localStorage (mais rápido)

O WebTerminal expõe dados via `localStorage` mesmo sem interação:

```python
# Conectar ao WebSocket da aba
ws_url = tab['webSocketDebuggerUrl']

def cdp(method, params=None):
    ws = websocket.create_connection(ws_url, timeout=10)
    ws.send(json.dumps({"id": 1, "method": method, "params": params or {}}))
    resp = json.loads(ws.recv())
    ws.close()
    return resp

# Chave crítica para Exness
result = cdp("Runtime.evaluate", {
    "expression": "localStorage.getItem('texActiveAccountNumber')",
    "returnByValue": True
})
account = result['result']['result']['value']  # → "198420982"
```

**Mapeamento de chaves localStorage (Exness):**

| Chave | Conteúdo | Exemplo |
|-------|----------|---------|
| `texActiveAccountNumber` | Número da conta | `"198420982"` |
| `texDataLayer` | JSON com Uid, Country, language | `{"Country":"BR","Uid":"..."}` |
| `trading.active_broker` | Broker ativo | `"Broker"` |

### 3. Personal Area → DOM (dados completos)

Se precisar de servidor MT5, alavancagem, saldo:

```python
# Abrir PA em nova aba
req = urllib.request.Request(
    'http://localhost:9222/json/new?https://my.exness.com/pa/trading/accounts',
    method='PUT')
tab = json.loads(urllib.request.urlopen(req).read())

# Aguardar carregamento (2-3s)
time.sleep(3)

# Extrair DOM
text = cdp("Runtime.evaluate", {
    "expression": "document.body.innerText",
    "returnByValue": True
})['result']['result']['value']

# Parsear dados de conta
# Exemplo de saída:
# Demo
# MT5
# Standard
# # 198420982
# Standard
# 10,000.00 USD
# ...
# Servidor
# Exness-MT5Trial11
```

### 4. Interagir com componentes React (trocas de senha, abas)

Para clicar em abas (Real/Demo) ou botões em React/MUI:

```python
# Padrão: buscar elemento por texto e clicar via Runtime.evaluate
cdp("Runtime.evaluate", {
    "expression": """
    (() => {
        const els = document.querySelectorAll('button');
        for (const el of els) {
            if (el.textContent.trim() === 'Demo' && el.offsetHeight > 0) {
                el.click();
                return 'clicked Demo tab';
            }
        }
        return 'not found';
    })()
    """,
    "returnByValue": True
})
```

Para formulários React (ex: alterar senha), usar o `nativeInputValueSetter`:

```python
# Preencher campo password em React
cdp("Runtime.evaluate", {
    "expression": """
    (() => {
        const pwInput = document.querySelector('input[type="password"]');
        if (pwInput) {
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value').set;
            nativeInputValueSetter.call(pwInput, 'NewPass123!');
            pwInput.dispatchEvent(new Event('input', { bubbles: true }));
            pwInput.dispatchEvent(new Event('change', { bubbles: true }));
            return 'done';
        }
        return 'no input';
    })()
    """,
    "returnByValue": True
})
```

## Caso Real: Descoberta Exness (26/05/2026)

1. **WebTerminal** já aberto no Brave real → `texActiveAccountNumber` = `"198420982"`
2. Abrir PA → DOM mostrava senha a alterar, não o servidor
3. Clicar aba "Demo" via `Runtime.evaluate` → expandiu card com servidor `Exness-MT5Trial11`
4. Clicar "Altere a senha da operação" → modal MUI → preencher nova senha → sucesso
5. Dados finais: conta 198420982, servidor Exness-MT5Trial11, $10k, 1:200

## Pitfalls

- **Cloudflare no browser interno:** NUNCA tentar `browser_navigate` em sites com Cloudflare. Usar SEMPRE Brave real :9222
- **OOPIF invisível:** iframes Cloudflare retornam `body.innerHTML = ""` — inacessíveis via CDP
- **React ignora `.value =`:** usar `nativeInputValueSetter` + `dispatchEvent('input')` + `dispatchEvent('change')`
- **Navegação via `window.location.href` quebra WebSocket:** abrir SEMPRE nova aba via `json/new?<url>`
- **Senhas no DOM:** nunca logar valores de senha — apenas confirmar que campos foram preenchidos
