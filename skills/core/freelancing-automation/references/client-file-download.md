# Client File Exchange Pattern (99Freelas)

## Problem

Clients often send files through the platform's messaging system (Excel, CSV, docs). The email notification only says "Arquivo(s) anexado(s): filename.xlsx" — the actual file content is NOT in the email. The file must be downloaded from the platform's messaging interface.

## Detection

Email subject: "Nova mensagem de [CLIENTE] no projeto [PROJETO]"
Email body contains: "Arquivo(s) anexado(s): [FILENAME]"

Example (Martin, 21/05/2026):
```
Arquivo(s) anexado(s):
Nexus_Lead_Base_Estrategica_Preenchida.xlsx
```

The email contains NO message text — only the file attachment notification.

## Resolution Path

### Option A: Desktop Control (when daemon running)
1. Start desktop daemon: `desktop-control` skill
2. Use ydotool to Alt+Tab to Edge window
3. Ctrl+L → type 99freelas.com.br/messages/inbox/PROJECT_ID
4. Wait for page load (5-6s)
5. Click on the conversation item to activate message panel
6. Find and click the file download link
7. File downloads to ~/Downloads/

### Option B: Manual (fastest)
1. User opens 99Freelas in Edge
2. Clicks on conversation with client
3. Downloads attached file
4. Saves to ~/.hermes/ for agent access
5. Agent analyzes and responds

### Option C: CDP (if Edge running with debug flags)
1. `PUT /json/new?https://www.99freelas.com.br/messages/inbox/PROJECT_ID`
2. Extract DOM to find file link
3. Use `Runtime.evaluate` to trigger download
4. Read file from ~/Downloads/

## Pitfalls

- **File content NOT in email.** Don't waste time parsing email HTML for file data — it's never there.
- **Cloudflare may block CDP.** If Turnstile active, CDP navigation to messaging pages may fail.
- **Message panel hidden.** 99Freelas inbox page shows message LIST, not conversation. Must click on the conversation item to reveal the message panel with attachments.
- **No clipboard access.** Can't use Ctrl+A/Ctrl+C to copy page content — Wayland blocks wl-paste from background. Need screenshot or manual interaction.

## Status: Martin L. — 21/05/2026

- File: Nexus_Lead_Base_Estrategica_Preenchida.xlsx
- Client: Martin Luskacz
- Project: Pesquisa e prospecção B2B de clínicas radiológicas (ID: 752503)
- Status: File not yet downloaded — awaiting user action or desktop daemon screenshot capability
- Priority: HIGH — client is waiting for response
