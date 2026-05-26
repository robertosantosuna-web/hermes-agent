# Telegram Cleanup — Deep Audit & Purge

## Workflow

```python
import asyncio
from telethon import TelegramClient
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.functions.messages import DeleteChatRequest
from datetime import datetime

async def deep_clean():
    client = TelegramClient('/home/roberto/roberto3', 2040, 'b18441a1ff607e10a989891a5462e627')
    await client.start(phone='+5531982125758')
    
    dialogs = await client.get_dialogs(limit=500)  # PEGAR TUDO
    
    KEEP = ['Entidade', 'Telegram', 'SSC - Vídeos', ...]
    
    for d in dialogs:
        name = d.name or ''
        etype = type(d.entity).__name__
        
        if name in KEEP: continue
        
        # Canais: sair (leave)
        if 'Channel' in etype:
            await client.delete_dialog(d.entity)
            await client(LeaveChannelRequest(d.entity))
        
        # Grupos: deletar
        elif 'Chat' in etype:
            await client(DeleteChatRequest(d.entity.id))
        
        # Usuários: deletar conversa
        else:
            await client.delete_dialog(d.entity)
```

## Pitfalls

1. **Limit=50/100 insuficiente** — Telegram pode ter 200+ diálogos. Usar limit=500.
2. **delete_dialog NÃO sai do canal** — precisa de LeaveChannelRequest adicional.
3. **delete_dialog pode falhar silenciosamente** — verificar se diálogo sumiu após deletar.
4. **Canais reaparecem** se houver nova mensagem — sair (leave) é permanente.

## Critérios de exclusão

- Deleted Account ou nome vazio
- Última mensagem do ano anterior ou mais antiga
- Canais sem interação há 3+ meses
- Bots promocionais/comerciais
- Grupos abandonados
