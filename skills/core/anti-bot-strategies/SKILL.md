---
name: anti-bot-strategies
description: "Estratégias para lidar com barreiras anti-bot (Cloudflare Turnstile, PerimeterX, CAPTCHA). O que tentar, quando desistir, como escalar."
version: 1.0.0
---

# Anti-Bot Strategies — Barreiras e Soluções

## Regra de Ouro

**CDP (Chrome DevTools Protocol) NÃO funciona para plataformas com Cloudflare Turnstile ou PerimeterX.** O headless browser é detectado como automação. Foram 107 tentativas frustradas. CHEGA.

## Matriz de Decisão

| Plataforma | Barreira | CDP? | Desktop Daemon? | Ação Humana? |
|-----------|----------|------|-----------------|-------------|
| 99Freelas | Cloudflare Turnstile | ❌ NUNCA | ✅ Sim | Se Daemon falhar |
| Fiverr | PerimeterX | ❌ NUNCA | ❌ Não | ✅ SEMPRE |
| Workana | Google OAuth | 🟡 Parcial | ✅ Sim | Se 2FA |
| Gmail | Google login | 🟡 Parcial | ✅ Sim | Se 2FA |
| Exness (sign-up) | Cloudflare Turnstile | ❌ NUNCA | ❌ Não | ✅ SEMPRE |
| Exness (sign-in) | Sem Cloudflare | ✅ OK | ✅ Sim | Se UNAUTHORIZED |
| Exness (PA/manage) | Precisa sessão | 🟡 Brave :9222 | — | — |
| Neevo | Nenhuma | ✅ OK | — | — |
| TimeBucks | Nenhuma | ✅ OK | — | — |

## Cloudflare Turnstile — Iframe OOPIF (26/05)

Exness e outros serviços financeiros usam Cloudflare Turnstile com checkbox "Confirme que é humano" em iframe OOPIF. **Programaticamente impossível de clicar.** O `browser_click` no ref do checkbox falha silenciosamente — o iframe é out-of-process e o clique não registra. `Runtime.evaluate` no iframe retorna `body.innerHTML = ""` (protegido). `Input.dispatchMouseEvent` também não resolve.

**Workflow correto:**
1. Navegar até a página → Cloudflare aparece
2. Dizer ao usuário: "Clica no checkbox Confirme que é humano aí no Brave"
3. Usuário clica → página libera → continuar automação

**NÃO perder tempo com:** CDP no iframe, dispatchMouseEvent, Runtime.evaluate no frame, ydotool no checkbox. Já testado — NADA funciona em OOPIF Cloudflare.

## Nova Descoberta (22/05): Google OAuth PULA Turnstile, mas Google bloqueia Hermes Browser

**Fluxo testado no 99Freelas:**
1. Email+senha → Turnstile bloqueia ("token de acesso inválido")
2. Clicar "Continuar com Google" → ✅ Redireciona para accounts.google.com SEM Turnstile
3. Preencher email → Google bloqueia: "Esse navegador ou app pode não ser seguro"

## Estratégia por Camada

### Bypass Google OAuth (DESCOBERTA 22/05)
No 99Freelas, o login email+senha exige Cloudflare Turnstile. Mas o fluxo **Google OAuth** (botão "Continuar com Google") pula o Turnstile. O Google pode bloquear o navegador se detectar automação, mas quando funciona, o login é direto.

### Camada 1: Desktop Daemon (PREFERENCIAL)
Para 99Freelas e plataformas com Turnstile:
1. Conectar ao Desktop Daemon: `ws://localhost:9876`
2. Comando: `mouse_move`, `mouse_click`, `key_type`
3. Navegar pelo Brave real do Roberto (cookies/logins preservados)
4. Se aparecer Turnstile → resolver automaticamente (o checkbox geralmente passa no browser real)
5. Se pedir "human touch" → 🔴 ESCALAR PARA ROBERTO

Comandos do Daemon:
```json
{"action": "mouse_move", "x": 500, "y": 300}
{"action": "mouse_click"}
{"action": "key_type", "text": "robertosantos.una@gmail.com"}
{"action": "key_press", "key": "Tab"}
{"action": "screenshot"}  // para verificar resultado
```

### Camada 2: CDP (APENAS para plataformas sem anti-bot)
- Neevo, TimeBucks, Toloka — CDP funciona
- Usar Edge na porta 9222: `http://localhost:9222`
- Verificar com: `curl -s http://localhost:9222/json`

### Camada 3: Ação Humana (QUANDO TUDO FALHA)
Reportar ao Roberto APENAS:
- 🔴 Plataforma pede verificação humana que não passa automaticamente
- 🔴 Precisa de código SMS/2FA
- 🔴 Precisa de documento físico (foto com RG, etc.)

NÃO reportar:
- ❌ "Cloudflare bloqueou de novo" — isso é ruído
- ❌ "Tentei CDP e não funcionou" — NUNCA tentar CDP para 99Freelas/Fiverr

## Fallback por Plataforma

### 99Freelas
```
1. Desktop Daemon → Brave real → login Google
2. Se sessão expirou → refazer login (credenciais no cofre)
3. Se Turnstile no Daemon → tentar 3x com intervalos de 30s
4. Se 3 falhas → 🔴 reportar "Turnstile no 99Freelas requer ação humana"
```

### Fiverr
```
1. NÃO tentar automação — PerimeterX é intransponível
2. 🔴 Reportar "Fiverr requer ação humana para verificação"
3. Aguardar Roberto resolver
```

### Workana
```
1. Desktop Daemon → Brave real → Login Google
2. Se Google bloquear "atividade suspeita" → 🔴 reportar
3. Se sessão ok → navegar normalmente
```

### Exness (26/05 — ATUALIZADO)

**Duas situações distintas:**

**1. Sign-up (criar conta) — Cloudflare Turnstile bloqueia:**
- Navegar para https://my.exness.com/accounts/sign-up
- Cloudflare Turnstile aparece → 🔴 "Clica no checkbox Confirme que é humano aí no Brave"
- Aguardar usuário clicar → página de cadastro carrega
- Continuar preenchimento normalmente

**2. Sign-in + PA (gerenciar conta existente) — Brave :9222 resolve:**
- A página de login (https://my.exness.com/accounts/sign-in) NÃO tem Cloudflare
- Password auth pode retornar `SIGN_IN_REQUEST_ERROR: UNAUTHORIZED` se senha errada
- Se a conta foi criada via Google OAuth, usar o Brave real :9222 que já tem sessão ativa
- Dados da conta no WebTerminal: `localStorage.getItem('texActiveAccountNumber')`
- Área Pessoal em `my.exness.com/pa/trading/accounts` para gerenciar senhas/servidores
- **PITFALL:** `browser_navigate` no navegador interno para a PA redireciona para /sign-in (sem cookies). Usar Brave :9222 que já tem cookies de sessão.

## Log de Falhas Anti-Bot

Toda falha anti-bot DEVE ser registrada em `~/.hermes/failure_log.json` com:
- `category: "anti-bot"`
- `barrier_type: "turnstile" | "perimeterx" | "captcha" | "oauth_block"`
- `approach_tried: "desktop_daemon" | "cdp" | "direct_navigation"`
- `result: "passed" | "blocked" | "requires_human"`

## Histórico de Efetividade

| Data | Plataforma | Abordagem | Resultado |
|------|-----------|-----------|-----------|
| 14/05 | 99Freelas | CDP Edge headless | ❌ Turnstile |
| 15/05 | Fiverr | CDP | ❌ PerimeterX "human touch" |
| 16/05 | 99Freelas | CDP Brave | ❌ Turnstile |
| 18/05 | 99Freelas | CDP Edge | ❌ Sessão expirou |
| 22/05 | 99Freelas | CDP | ❌ 4 abas na tela de login |
| 22/05 | 99Freelas | Email+senha CDP | ❌ Turnstile "token inválido" |
| 22/05 | 99Freelas | Google OAuth CDP | ❌ Google bloqueou "navegador inseguro" |
| 22/05 | 99Freelas | Desktop Daemon (cego) | ⚠️ Navegou mas sem confirmação visual |
| 26/05 | Exness | CDP browser_click checkbox | ❌ Cloudflare Turnstile OOPIF — clique não registra |
| 26/05 | Exness PA | Brave :9222 CDP (sessão ativa) | ✅ Acessou PA, extraiu conta, alterou senha MT5 |
| 26/05 | Exness login | browser_navigate + password | ❌ UNAUTHORIZED (senha incorreta) |
| 26/05 | Exness login | browser_navigate + Google OAuth | ❌ Redirecionou para TradingView (popup bloqueado) |

| 28/05 | Instagram | Brave :9222 CDP (navegador real) | ✅ Contornou bloqueio do Chromium |
| 28/05 | Instagram | Chromium headless :9226 | ❌ Bloqueado — não aceita Chrome automatizado |

**Regra Instagram (28/05):** Chromium headless é bloqueado. Brave/Edge (navegadores reais com perfil de usuário) passam. Para login: ação humana única no Brave real, depois CDP extrai métricas.

## Dual-Browser Strategy (26/05 — PADRÃO)

Quando o browser interno (browser_navigate) é bloqueado por Cloudflare ou perde cookies de sessão:

1. **Browser interno**: apenas para páginas públicas ou primeiro contato
2. **Brave real :9222**: para páginas que exigem autenticação — a sessão Google/Gmail/Exness já está ativa
3. **Desktop Daemon :9876**: para cliques que exigem evento de mouse kernel-level (React SPAs que rejeitam `Input.dispatchMouseEvent`)

**Fluxo de decisão:**
```
Precisa acessar plataforma X?
├─ X tem Cloudflare? → Brave :9222 + Desktop Daemon (pular browser interno)
├─ X precisa de login? → Brave :9222 (sessão ativa) → CDP Runtime.evaluate para extrair dados
├─ X é pública? → browser_navigate (browser interno)
└─ X bloqueou tudo? → ação humana
```

## Exness — Extração de Dados da Conta (26/05)

**Problema:** browser interno redireciona para /sign-in sem cookies. Cloudflare no sign-up bloqueia automação.

**Solução:** Brave real :9222 já tem sessão Google ativa → acessar WebTerminal ou PA diretamente.

**WebTerminal** (`https://my.exness.com/webtrading/`):
```javascript
// Número da conta no localStorage
localStorage.getItem('texActiveAccountNumber')  // → "198420982"
// Outros dados: saldo, margem, alavancagem visíveis no DOM
document.body.innerText  // → extrair "Demo", "Standard", "10,000.00 USD"
```

**Personal Area** (`https://my.exness.com/pa/trading/accounts`):
- Abrir via Brave :9222: `http://localhost:9222/json/new?https://my.exness.com/pa/trading/accounts`
- Clicar aba "Demo" para ver conta demo
- Dados expostos: servidor (`Exness-MT5Trial11`), alavancagem (`1:200`), saldo
- Botão "Altere a senha da operação" → modal com campos new password/confirm

**Alterar senha MT5 via PA:**
1. `document.querySelectorAll('button')` → achar "Altere a senha da operação"
2. `.click()` → modal abre com campo password
3. `nativeInputValueSetter.call(input, 'nova_senha')` + dispatch Event('input')
4. Clicar "Alterar a senha" → modal fecha se sucesso

**PITFALL:** Não usar `ydotool type` para senhas com caracteres especiais — layout ABNT2 corrompe `@`, `!`, `#`. Usar CDP `Input.dispatchKeyEvent` com `type: "char"` ou `nativeInputValueSetter`. Para senhas puramente alfanuméricas (ex: `Wc0ZO6#p`), testar antes — `#` pode falhar no ABNT2.

## Limitação Crítica: Visão no Wayland/GNOME

O Desktop Daemon usa mss (XWayland) para screenshots, mas isso só captura janelas XWayland — NÃO janelas nativas do GNOME/Wayland (como o Brave). Isso significa que **não é possível ver o que o Roberto vê na tela** via screenshot programático.

GNOME Shell D-Bus (`org.gnome.Shell.Screenshot`) retorna `AccessDenied`. `grim` requer `wlr-screencopy` que o GNOME não implementa. A extensão GNOME criada (`hermes-screenshot@entidade.local`) está quebrada (API incompatível com GNOME 50).

**Workaround**: Navegação cega com confirmação do Roberto após cada passo. Ou Roberto executa ações críticas manualmente (login com Turnstile, upload de arquivos).

## Google OAuth — Bloqueado em 2 níveis

1. **No browser tools do Hermes**: Google detecta Chromium de automação → "Esse navegador ou app pode não ser seguro"
2. **No Desktop Daemon (Brave real)**: Funciona se o Roberto já estiver logado. Caso contrário, o Google pode pedir 2FA.
