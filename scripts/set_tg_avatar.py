#!/usr/bin/env python3
"""Set Telegram profile photos via Telethon."""
import asyncio, sys
from telethon import TelegramClient
from telethon.tl.functions.photos import UploadProfilePhotoRequest

async def set_profile_photo(session_file, phone, photo_path):
    client = TelegramClient(session_file, 2040, 'b18441a1ff607e10a989891a5462e627')
    await client.start(phone=phone)
    
    uploaded = await client.upload_file(photo_path)
    await client(UploadProfilePhotoRequest(file=uploaded))
    print(f"✅ Foto definida: {photo_path}")
    await client.disconnect()

photo = sys.argv[1] if len(sys.argv) > 1 else '/home/roberto/.hermes/telegram_avatars/hermes_agent.png'
asyncio.run(set_profile_photo('roberto3', '+5531982125758', photo))
