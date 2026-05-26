# Outlook / Exchange — Setup

## Servidores Microsoft 365 / Office 365

- IMAP: `outlook.office365.com:993` (SSL)
- SMTP: `smtp.office365.com:587` (STARTTLS)
- Web: `https://outlook.office.com/mail/` (OWA)

## Contas Configuradas (25/05/2026)

### GOL (Trabalho — somente leitura)
- Email: `robrsantos@voegol.com.br`
- Modo: read_only via CDP browser
- Acesso: Edge CDP :9222, sessao persistente
- URL: `https://outlook.office.com/mail/`
- NUNCA enviar email por esta conta

### Pessoal
- Email: `robertosantos141@outlook.com`
- Modo: read_write via CDP browser
- Mesma sessao Edge :9222

## Autenticacao — Tres abordagens (ordem de preferencia)

### 1. Browser CDP (funciona sempre, sessao persistente)
Abordagem preferida para contas corporativas com IT restritiva.

- Navegar para `https://outlook.office.com/mail/` no Edge CDP (:9222)
- Login via Microsoft (email + senha + MFA) — requer interacao do usuario na primeira vez
- Sessao persiste entre reinicializacoes (cookies no perfil Edge)
- Leitura de emails via `Runtime.evaluate` + `document.querySelectorAll`
- Limitacao: nao escala para alto volume. Para varredura automatica, usar abordagem 2 ou 3.

### 2. IMAP + App Password (se tenant permitir)
- https://account.microsoft.com/security → App passwords
- Requer MFA ativado
- Se o tenant bloquear app passwords → fallback para abordagem 1 ou 3

### 3. OAuth2 (App Registration)
- Registrar app no Azure AD (entra.microsoft.com)
- Permissions: `Mail.Read` (delegated, user consent)
- Multi-tenant se incluir contas pessoais
- PITFALL: Azure Entra admin center bloqueado para usuarios sem admin role → fallback para abordagem 1

## Leitura via CDP Browser

```python
import json, urllib.request
from websocket import create_connection

# Conectar a aba Outlook
resp = urllib.request.urlopen('http://localhost:9222/json')
pages = json.loads(resp.read())
outlook = next(p for p in pages if 'outlook' in p['url'])
ws = create_connection(outlook['webSocketDebuggerUrl'])
# ... Runtime.evaluate para extrair emails do DOM
```

## Regra de seguranca — conta trabalho
- NUNCA usar SMTP (envio) na conta de trabalho
- Apenas leitura (IMAP ou CDP browser)
- Nao marcar como lida, nao deletar, nao mover
- Nao compartilhar credenciais em logs ou chat
