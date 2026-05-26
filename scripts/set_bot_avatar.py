#!/usr/bin/env python3.14
"""Set bot profile photo via @BotFather using Telethon."""
import asyncio, sys, os, time
from telethon import TelegramClient

async def set_bot_photo():
    client = TelegramClient('/home/roberto/roberto3', 2040, 'b18441a1ff607e10a989891a5462e627')
    await client.start(phone='+5531982125758')
    
    # Upload photo
    photo_path = '/home/roberto/.hermes/telegram_avatars/hermes_brain.png'
    uploaded = await client.upload_file(photo_path)
    
    # Send /setuserpic to BotFather
    botfather = await client.get_entity('@BotFather')
    
    # Step 1: send /setuserpic
    await client.send_message(botfather, '/setuserpic')
    await asyncio.sleep(2)
    
    # Step 2: send bot username
    await client.send_message(botfather, '@HermesEntidadeBot')
    await asyncio.sleep(2)
    
    # Step 3: send the photo
    await client.send_file(botfather, uploaded)
    await asyncio.sleep(3)
    
    # Read BotFather response
    msgs = await client.get_messages(botfather, limit=3)
    for m in msgs[:3]:
        print(f"[BotFather] {m.text[:120] if m.text else '(media)'}")
    
    print("✅ Foto do cérebro enviada para BotFather")
    await client.disconnect()

asyncio.run(set_bot_photo())
