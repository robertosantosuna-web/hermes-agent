---
name: telegram-autonomy
description: "Autonomia total no Telegram: leitura, resposta, monitoramento de grupos, triagem de mensagens, envio de arquivos e alertas proativos via Telethon."
version: 1.1.0
author: Roberto Rodrigues
license: MIT
metadata:
  hermes:
    tags: [telegram, autonomy, messaging, telethon, monitoring]
    related_skills: [life-os, executive-communication, dashboard, email-autonomy]
---

# Telegram Autonomy

Conta: @Roberto_R_Santos (ID 845735429, +5531982125758)
Sessão: ~/roberto3.session (persistente)

## INICIALIZAÇÃO

```python
from telethon import TelegramClient

# api_id e api_hash do Telegram oficial (funcionam para login)
client = TelegramClient('roberto3', 2040, 'b18441a1ff607e10a989891a5462e627')

# IMPORTANTE: número com código do país (+55) e DDD
await client.start(phone='+5531982125758')
```

### Formato do telefone
- SEMPRE usar formato internacional: `+<código_país><DDD><número>`
- Brasil: `+55XX9XXXXXXXX`
- NUNCA usar número sem prefixo internacional (Telegram rejeita)

### Sessão persistente
- Arquivo: `~/roberto3.session` (criado automaticamente)
- Após primeiro login (com código), reconexões são instantâneas
- NÃO requer código novamente enquanto a sessão for válida
- Se pedir código de novo, usar `code_callback=lambda: input('Código: ')`

## LER MENSAGENS

```python
# Não lidas
unread = await client.get_dialogs()
for d in unread:
    if d.unread_count:
        print(f'🔴 {d.name}: {d.unread_count}')

# Últimas mensagens de uma conversa
messages = await client.get_messages('@username', limit=20)

# Mensagens de grupos
messages = await client.get_messages(-1001234567890, limit=10)
```

## ENVIAR MENSAGENS

```python
# Para usuário
await client.send_message('@username', 'Mensagem')

# Para grupo
await client.send_message(-1001234567890, 'Mensagem')

# Com arquivo
await client.send_file('@username', '/path/arquivo.pdf')
```

## MONITORAMENTO

```python
# Verificar menções em grupos
async def check_mentions():
    dialogs = await client.get_dialogs()
    for d in dialogs:
        if d.unread_count and d.is_group:
            msgs = await client.get_messages(d.id, limit=d.unread_count)
            for m in msgs:
                if '@Roberto_R_Santos' in (m.text or ''):
                    print(f'🔔 Menção em {d.name}: {m.text[:100]}')
```

## TRIAGEM AUTÔNOMA

### Classificação
```python
def classify_chat(chat_name, message_text):
    name_lower = chat_name.lower()
    
    # Monitoramento/sistema
    if any(k in name_lower for k in ['entidade', 'gateway', 'monitor', 'alert']):
        return 'SISTEMA'
    
    # Clientes/negócios
    if any(k in name_lower for k in ['cliente', 'projeto', 'freela', 'job']):
        return 'NEGOCIO'
    
    # Oportunidades
    if any(k in (message_text or '').lower() for k in ['freela', 'projeto', 'orçamento', 'vaga']):
        return 'OPORTUNIDADE'
    
    # Pessoal
    return 'PESSOAL'
```

## CRON JOB

```bash
# Monitorar Telegram a cada 1h
cronjob create \
  --name "Telegram Monitor" \
  --schedule "0 * * * *" \
  --skills "telegram-autonomy" \
  --prompt "Check Telegram for unread messages. Classify by priority. Alert on SYSTEM/OPPORTUNITY messages."
```

## LISTA DE CONVERSAS ATIVAS

Monitorar:
- "Entidade" → gateway/monitoramento
- "Promotom" → ofertas/oportunidades  
- "Sala de Debriefing" → coordenação
- "Arquivos pessoais" → documentos

## CANAL "ENTIDADE" — CLI DE BACKUP

A conversa "Entidade" (ID 8781127500) funciona como interface de linha de comando
quando as ferramentas de browser/display estão bloqueadas.

### Uso como CLI
- Roberto envia comandos por esta conversa
- A ENTIDADE lê via `get_messages(8781127500, limit=5)` e processa
- Usar para comandos quando o CLI normal não está responsivo

### Uso como armazenamento de dados
Quando Cloudflare/PerimeterX bloqueiam scraping de plataformas (99Freelas, Fiverr),
dados críticos JÁ estão no histórico do canal. Buscar com:
```python
msgs = await client.get_messages(8781127500, limit=100, search='99freelas')
```

O histórico contém: dashboards anteriores, propostas enviadas, status de projetos,
valores, prazos, e relatórios de execução. Recuperar daqui em vez de tentar
scraping bloqueado.

### Uso como log de execução
Enviar relatórios de status periodicamente para manter o registro fora
do contexto da conversa principal. O canal serve como arquivo persistente
de decisões e resultados.

## ANTI-PADRÕES

- NÃO enviar mensagens em massa (spam)
- NÃO responder sem antes classificar
- NÃO usar para conteúdo ilegal (ToS)
- NÃO compartilhar o arquivo .session

## LIMPEZA & AUDITORIA

Ver **[references/telegram-cleanup.md](references/telegram-cleanup.md)** — deep audit, critérios de exclusão, pitfalls de delete_dialog vs LeaveChannel.

## CDP BROWSER AUTOMATION (Telegram Web K)

Quando Telethon não está disponível ou é necessário interagir com o Telegram via browser
(ex: criar bots no @BotFather, ler chats via CDP), usar Telegram Web K no Brave via CDP.

Ver **[references/telegram-web-cdp.md](references/telegram-web-cdp.md)** — CDP connection, Input.dispatchKeyEvent typing, bot creation, pitfall de DOM vs CDP input.

Bot do cérebro: **@HermesEntidadeBot** (token em `.env`, daemon `hermes-brain-telegram.service`).
Responde IMEDIATAMENTE via processamento inline do `_brain_process()`.

## FOTO DE PERFIL

### Conta própria (usuário)
```python
from telethon.tl.functions.photos import UploadProfilePhotoRequest

uploaded = await client.upload_file('/path/avatar.png')
await client(UploadProfilePhotoRequest(file=uploaded))
```

### Bot (@HermesEntidadeBot)
Bots NÃO podem alterar a própria foto via API. Usar @BotFather via Telethon:

```python
botfather = await client.get_entity('@BotFather')
photo = await client.upload_file('/path/brain_avatar.png')

await client.send_message(botfather, '/setuserpic')
await asyncio.sleep(2)
await client.send_message(botfather, '@HermesEntidadeBot')
await asyncio.sleep(2)
await client.send_file(botfather, photo)
await asyncio.sleep(3)

msgs = await client.get_messages(botfather, limit=3)
# Esperado: "Success! Profile photo updated."
```

### Geração de avatares
Script: `~/.hermes/scripts/gen_avatars.py` — gera PNG 512x512 com Pillow.
Necessita `/usr/bin/python3.14` (não está no venv do Hermes; Pillow via sistema).

PITFALL: Telethon usa Python 3.14 (`/usr/bin/python3.14`), não o python3 do venv.
Sessão deve usar caminho absoluto: `TelegramClient('/home/roberto/roberto3', ...)`.

## EXTRAÇÃO DE VOZ

Ver **[references/voice-extraction.md](references/voice-extraction.md)** — script de extração de mensagens de voz próprias (msg.voice + msg.out) para datasets de voice cloning, conversão OGG→WAV.
