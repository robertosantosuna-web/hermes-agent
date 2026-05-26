# Cron-Based Email Monitoring for Freelance Platforms

## Why: Cloudflare Turnstile blocks browser automation on 99Freelas, Fiverr, and similar platforms. Email (IMAP) is the reliable fallback — it bypasses all anti-bot protection.

## Setup (2026-05-19)

```bash
cronjob create \
  --name "Freelance Opportunity Scanner" \
  --schedule "every 2h" \
  --skills "freelancing-automation,email-autonomy" \
  --prompt "Scan Gmail (robertosantos.una@gmail.com) for new freelancing opportunities from 99Freelas, Freelancer, Workana, and Fiverr from the last 3 hours. For each new project found, report: platform, project title, budget (if any), number of proposals, and whether it's worth bidding (criteria: budget > R$100 OR less than 10 proposals OR urgent deadline). Also check for any new messages from clients on active projects. Send the report to the user."
```

## Supported Platforms via Email

| Platform | Sender pattern | Subject pattern | Reliable? |
|----------|---------------|-----------------|-----------|
| 99Freelas | no-reply@99freelas.com.br | "Novo Projeto: ..." | ✅ Yes |
| 99Freelas | no-reply@99freelas.com.br | "Nova mensagem de ..." | ✅ Yes |
| Fiverr | noreply@fiverr.com | "New brief: ..." | ⚠️ Variable |
| Workana | notificacoes@workana.com | "Novo projeto: ..." | ✅ Yes |
| Freelancer | notifications@freelancer.com | Various | ⚠️ Variable |

## HTML Extraction Pattern

Platform emails are heavy HTML templates. Clean extraction:

```python
import re

def clean_html(html):
    body = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    body = re.sub(r'<head>.*?</head>', '', body, flags=re.DOTALL)
    body = re.sub(r'<[^>]+>', '\n', body)
    body = re.sub(r'\n\s*\n', '\n', body)
    lines = [l.strip() for l in body.split('\n') 
             if l.strip() and len(l.strip()) > 15
             and not any(skip in l.lower() for skip in 
                 ['cancelar', 'visualizar', 'navegador', 'inscrição', 
                  '©', 'direitos', 'newsletter', '99freelas',
                  'whatsapp', 'telegram', 'instagram', 'facebook',
                  'linkedin', 'youtube', 'política', 'privacidade'])]
    return '\n'.join(lines)
```

## Project Worth Bidding — Heuristics

- **Budget > R$100**: Always worth
- **< 10 proposals**: Low competition
- **Urgent deadline** (< 2 days remaining): Fast decision, less competition
- **"Iniciante" level**: Lower barrier
- **AVOID**: Projetos "Exclusivo" (Premium paywall), 50+ propostas (loteria)
