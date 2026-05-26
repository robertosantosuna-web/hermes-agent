# Brain Calendar Monitor

## Overview
Script `brain_calendar_monitor.py` — extrai agenda do Google Calendar e WhatsApp sem OAuth.
Zero tokens (no_agent). Roda 06:00 e 16:00 via cron.

## Technique: Google Calendar via CDP Session (No OAuth)
Google Calendar is accessible without OAuth by using the existing browser CDP session:
1. Port 9222 (Brave) has an active Google login session
2. Navigate to `https://calendar.google.com/calendar/u/0/r/week` via CDP Page.navigate
3. Extract events from DOM using TreeWalker over the main content area
4. Parse Portuguese date format: "tarefa: Nome, Não concluída, D de mês de AAAA, HHam"

No Google Cloud Console OAuth client needed. No client_secret.json. No token refresh.
Just reuse the existing browser session that's already logged into Google.

## Pitfall: websocket-client
The script requires `websocket-client` package. It must run under system Python (`/usr/bin/python3`)
which has websocket-client installed, not the venv Python. Shebang: `#!/usr/bin/python3`.

## Pitfall: time module
The scan_gcalendar function uses `time.sleep()` but the original imports didn't include `time`.
Import: `import time` at module level.

## Parsing Format
Google Calendar renders tasks in Portuguese:
```
tarefa: Check-in Biológico: Água e Proteína (Acordar), Não concluída, 24 de maio de 2026, 10am
```
Regex: `(?:tarefa|evento):\s*(.+?),\s*(?:Não concluída|Concluída)?,?\s*(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4}),?\s*(\d{1,2})(?:am|pm)?`

## Cron Jobs
- `56b2f5d980cb` — 06:00 BRT daily
- `e4352927a5f6` — 16:00 BRT daily

## Output
- `~/.hermes/brain/agenda.json` — structured 7-day agenda
- Knowledge Bridge alert — if appointments found today

## Integration
- NN-Brain: neuron `Google_Calendar_CDP_10_Tasks_Semana` + synapse to `Agenda_Diaria`
- Unified Pillar: social_check.py references calendar data
- WhatsApp: scan_whatsapp() extracts dates from messages
