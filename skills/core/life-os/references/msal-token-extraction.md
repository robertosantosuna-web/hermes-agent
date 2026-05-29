# MSAL Token Extraction via CDP

## Técnica (26/05/2026)

Extrair token de acesso Microsoft do localStorage do Brave/Edge para usar APIs Microsoft sem OAuth flow.

## Passo a passo

1. Conectar ao browser via CDP (ex: Brave :9222)
2. Listar abas: `curl http://localhost:9222/json`
3. Conectar via WebSocket ao target do Outlook
4. Executar no console:

```javascript
// Encontrar chaves MSAL com access token
for (let i = 0; i < localStorage.length; i++) {
  let k = localStorage.key(i);
  if (k.includes('accesstoken') && k.includes('outlook')) {
    let val = JSON.parse(localStorage.getItem(k));
    console.log(val.secret); // O token JWT
  }
}
```

5. Usar o token com a **Outlook REST API** (NÃO Microsoft Graph):

```python
# Outlook REST API — funciona com token de escopo outlook.office.com
url = "https://outlook.office.com/api/v2.0/me/messages?$search=\"termo\"&$top=3"
headers = {"Authorization": f"Bearer {token}"}
```

## Pitfalls

- O token MSAL tem escopo `outlook.office.com` — **não funciona com Microsoft Graph API** (`graph.microsoft.com`). O Graph retorna "JWT is not well formed".
- O token expira em ~24h (verificar campo `expiresOn`).
- Funciona para Outlook REST API v2.0: emails, calendário, contatos.
