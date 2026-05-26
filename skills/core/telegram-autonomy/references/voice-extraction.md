# Voice Message Extraction via Telegram

Pattern validated 24/05: 23 voice messages extracted from 13 chats, topped up voice cloning dataset.

## Extraction script template

```python
import asyncio
from pathlib import Path
from telethon import TelegramClient

async def extract_voice_messages(output_dir, limit_per_chat=100, max_total=20):
    client = TelegramClient('roberto3', 2040, 'b18441a1ff607e10a989891a5462e627')
    await client.start(phone='+5531982125758')
    
    total = 0
    for dialog in await client.get_dialogs():
        messages = await client.get_messages(dialog.id, limit=limit_per_chat)
        for msg in messages:
            if msg.voice and msg.out:  # Only self-sent voice notes
                filename = f"roberto_{dialog.name}_{msg.date:%Y%m%d_%H%M%S}_{msg.id}.ogg"
                await client.download_media(msg, str(output_dir / filename))
                total += 1
                if total >= max_total:
                    break
    
    await client.disconnect()
    return total
```

## Key details

- **Session file:** `~/roberto3.session` — persistent, no re-auth needed
- **Voice format:** OGG (Opus codec), variable duration (2s-35s typical)
- **Filter:** `msg.voice and msg.out` isolates Roberto's own voice messages
- **Venom:** `/home/roberto/rvc/venv/bin/python3` (has telethon installed)
- **api_id/hash:** Telegram official test credentials (2040 / b18441a1ff607e10a989891a5462e627)

## Post-extraction

Convert OGG to WAV 16kHz mono for voice cloning tools (XTTS, RVC, Piper):

```bash
for f in *.ogg; do
    ffmpeg -y -i "$f" -ac 1 -ar 16000 -sample_fmt s16 "${f%.ogg}.wav"
done
```
