# Freelancer.com — Phone Verification Flow

## Context (19/05/2026)

Perfil parcialmente completo. Bloqueio: verificação de telefone pendente.

## Páginas e navegação

### Trust & Verification page
- **Como chegar**: Navegar pela UI: clicar no menu superior "@robertor03" → dropdown aparece → NÃO tem link direto pra settings. 
- **Caminho alternativo**: A página de projeto (qualquer uma) mostra banner "Hi Roberto. Please verify your phone number. Verify via SMS" no topo.
- **Banner "Verify via SMS"**: O botão `id="verifyViaSms"` (BUTTON, ~1440,36) redireciona para a Trust & Verification page.
- **URL que FUNCIONA**: `https://www.freelancer.com/users/settings/` (abre corretamente, sem 404)
- **URL que NÃO funciona**: `/verified`, `/settings/profile`, `/u/robertor03` (retorna 404/OOPS)

### Trust Score
- Score atual: 5/100 (STRENGTH: LOW)
- Email: VERIFIED (5 points)
- Phone: pendente (10 points)
- LinkedIn: pendente (20 points)
- Credit/Debit Card: pendente (45 points)

### Phone verification button
- **Seletor**: `button.ButtonElement.ng-star-inserted` com texto "Verify Phone Number"
- **Posição**: ~(1292, 642)
- **Framework**: Angular (classes `ng-star-inserted`)
- **Evento**: `Input.dispatchMouseEvent` NÃO funciona no botão. JS `.click()` + `dispatchEvent(new Event('click'))` SIM.
- Após clique: modal abre com input `placeholder="Enter phone number"`

### Preencher telefone
- Formato: `+55DDDXXXXXXXXX` (ex: `+5531982125758`)
- Input: `input[placeholder*="phone"]`
- Setter nativo + eventos `input`/`change` funciona.

### Enviar/Send
- Após preencher, procurar botão "Verify" ou "Send" ou "OK" na tela.
- **Status 19/05**: NÃO foi possível confirmar se o SMS foi enviado (script perdeu estado entre chamadas).

## Lições
1. NUNCA tentar `/verified`, `/settings/profile` direto — usar `/users/settings/` como entry point.
2. Botões Angular (`.ng-star-inserted`) respondem a JS `.click()`, não a `Input.dispatchMouseEvent`.
3. Manter todas as etapas em UM script contínuo — estado do modal se perde entre chamadas CDP separadas.
