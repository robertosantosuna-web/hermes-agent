# Voice Sourcing — Extração de amostras de voz

Metodologia para coletar amostras de voz do Roberto via Telegram e WhatsApp.

## Telegram (Telethon)

```python
from telethon import TelegramClient

client = TelegramClient('roberto3.session', 2040, 'b18441a1ff607e10a989891a5462e627')
await client.start(phone='+5531982125758')

# Buscar voice notes nas conversas
dialogs = await client.get_dialogs()
for dialog in dialogs:
    messages = await client.get_messages(dialog.id, limit=100)
    for msg in messages:
        if msg.voice and msg.out:  # Apenas voz do Roberto
            await client.download_media(msg, f'voice_dataset/telegram_voice/{msg.id}.ogg')
```

**Resultado (24/05):** 23 amostras, duração total ~87s. Arquivos OGG convertidos para WAV 16kHz mono.

## WhatsApp (Edge CDP)

Acesso via Microsoft Edge com CDP na porta 9224 (systemd `whatsapp-edge.service`).
Perfil persistente em `~/.config/microsoft-edge-whatsapp`.

```bash
# Verificar status
python3 ~/scripts/whatsapp_bridge.py status

# Listar conversas com indicador de áudio
python3 ~/scripts/whatsapp_bridge.py voice
```

**Limitação:** Voice notes do WhatsApp são armazenadas como blobs criptografados.
A extração via CDP requer clicar em cada chat e baixar via elemento `<audio>`.
Alternativa: usar o WhatsApp Desktop snap e acessar LevelDB local.

**Resultado (24/05):** 15 chats com indicadores de áudio detectados.
Extração completa pendente de automação de clique+download.

## Conversão OGG → WAV

```bash
for f in *.ogg; do
    ffmpeg -y -i "$f" -ac 1 -ar 16000 -sample_fmt s16 "${f%.ogg}.wav"
done
```

## Master Reference

Concatenar melhores amostras para criar referência de alta qualidade:

```bash
ffmpeg -y -f concat -safe 0 -i concat_list.txt \
    -ac 1 -ar 16000 -c pcm_s16le roberto_voice_master.wav
```

**Requisitos XTTS v2:** mínimo 6s, ideal 30-90s, WAV mono 16-22kHz, sem ruído.
