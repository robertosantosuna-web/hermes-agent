# Email Health Scanning via IMAP

## Why imaplib, not himalaya

`himalaya envelope list` retorna `feature not available` com backend IMAP (Gmail).
O backend IMAP do himalaya não implementa envelope listing — só operações básicas de fetch.

**Solução: Python `imaplib` direto.** Mais rápido, zero dependências, controle total.

## Connection

```python
import imaplib
mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
mail.login("robertosantos.una@gmail.com", "exnlrvfswckioces")
mail.select("INBOX")
```

## Search emails from last 24h

```python
from datetime import datetime, timedelta
since_date = (datetime.now() - timedelta(hours=24)).strftime("%d-%b-%Y")
status, msg_ids = mail.search(None, f'(SINCE "{since_date}")')
```

Formato de data: `DD-Mon-YYYY` em inglês (ex: `24-May-2026`).

## Fetch headers only (economiza banda)

```python
status, msg_data = mail.fetch(eid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])")
```

`BODY.PEEK` não marca como lida. Só puxa FROM e SUBJECT.

## Decode headers

Headers IMAP podem vir encoded: `=?UTF-8?B?VGVzdGU=?=` ou `=?ISO-8859-1?Q?Teste?=`.

```python
from email.header import decode_header
def decode_email_header(header):
    parts = decode_header(header)
    decoded = ""
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded += part.decode(charset or "utf-8", errors="replace")
        else:
            decoded += part
    return decoded
```

## Keywords

Health-related keywords organized by language (PT + EN) and category:
- **Senders**: huawei health, google fit, strava, smartfit, gympass, wellhub, etc.
- **Topics**: sono/sleep, passos/steps, batimentos/heart rate, peso/weight, água/water, etc.
- **Medical**: consulta/appointment, exame/lab results, receita/prescription, farmácia/pharmacy

See `mindcoach_health_collector.py` for the full keyword lists (`HEALTH_EMAIL_SENDERS`, `HEALTH_EMAIL_KEYWORDS`).

## Performance

- 50 emails scanned in ~2-5 seconds
- Headers-only fetch: ~2KB per email
- No marking as read (BODY.PEEK)
- Can run every 15 min without hitting Gmail rate limits
