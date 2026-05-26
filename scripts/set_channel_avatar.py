#!/usr/bin/env python3.14
"""Set channel profile photo for Entidade channel."""
import asyncio
from telethon import TelegramClient
from telethon.tl.functions.channels import EditPhotoRequest

async def set_channel_photo():
    client = TelegramClient('/home/roberto/roberto3', 2040, 'b18441a1ff607e10a989891a5462e627')
    await client.start(phone='+5531982125758')
    
    channel = await client.get_entity(-1008781127500)
    uploaded = await client.upload_file('/home/roberto/.hermes/telegram_avatars/hermes_agent.png')
    
    await client(EditPhotoRequest(channel=channel, photo=uploaded))
    print("✅ Foto do canal Entidade definida")
    await client.disconnect()

asyncio.run(set_channel_photo())
