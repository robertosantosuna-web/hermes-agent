#!/usr/bin/env python3
"""Extract Telegram dialog data for behavioral analysis - v2."""
import asyncio, json, os, sys
from datetime import datetime
from pathlib import Path
from telethon import TelegramClient

HOME = Path.home()
API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'
OUTPUT = HOME / '.hermes' / 'data' / 'social' / 'telegram_dialogs.json'

async def main():
    sessions = [
        HOME / "roberto.session",
        HOME / "roberto2.session",
        HOME / "roberto3.session"
    ]
    
    output = {'success': False, 'dialogs': [], 'error': None}
    
    for sess_path in sessions:
        if not sess_path.exists():
            continue
        
        try:
            client = TelegramClient(str(sess_path), API_ID, API_HASH)
            await client.connect()
            
            if not await client.is_user_authorized():
                await client.disconnect()
                continue
            
            me = await client.get_me()
            output['user'] = {
                'first_name': me.first_name or '',
                'last_name': me.last_name or '',
                'username': me.username or '',
                'phone': me.phone or ''
            }
            print(f"✅ Conectado como {me.first_name} (@{me.username})", file=sys.stderr)
            
            # Get dialogs
            dialogs = await client.get_dialogs(limit=200)
            output['total_dialogs'] = len(dialogs)
            
            total_unread = 0
            for d in dialogs:
                total_unread += d.unread_count
                msg = d.message
                
                entry = {
                    'name': d.name or 'Unknown',
                    'unread': d.unread_count,
                    'is_group': d.is_group,
                    'is_channel': d.is_channel,
                    'is_user': d.is_user,
                    'pinned': d.pinned,
                    'archived': d.archived,
                }
                
                if msg:
                    entry['last_msg'] = (msg.message or '')[:200]
                    entry['last_date'] = msg.date.isoformat() if msg.date else None
                    entry['outgoing'] = msg.out
                
                output['dialogs'].append(entry)
            
            output['total_unread'] = total_unread
            output['success'] = True
            
            # Print summary
            print(f"\n📊 {len(dialogs)} conversas, {total_unread} nao lidas", file=sys.stderr)
            
            # Categories
            from collections import Counter
            cats = Counter()
            family_names = ['pai', 'mãe', 'mae', 'tia', 'tio', 'vó', 'irma', 'primo', 'filho']
            
            for d in dialogs:
                name_lower = d.name.lower() if d.name else ''
                if d.is_channel:
                    cats['canal'] += 1
                elif d.is_group:
                    cats['grupo'] += 1
                elif any(f in name_lower for f in family_names):
                    cats['familia'] += 1
                else:
                    cats['social'] += 1
            
            print("Categorias:", dict(cats), file=sys.stderr)
            
            # Top unread
            print("\n🔝 TOP 10 nao lidas:", file=sys.stderr)
            sorted_d = sorted(dialogs, key=lambda d: d.unread_count, reverse=True)[:10]
            for d in sorted_d:
                tag = "📢" if d.is_channel else ("👥" if d.is_group else "👤")
                print(f"  {tag} {d.name[:45]:45s} {d.unread_count:>6}", file=sys.stderr)
            
            await client.disconnect()
            break
            
        except Exception as e:
            output['error'] = f"{sess_path.name}: {e}"
            try:
                await client.disconnect()
            except:
                pass
            continue
    
    # Save
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, 'w') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Salvo: {OUTPUT}", file=sys.stderr)
    print(json.dumps(output, ensure_ascii=False))

asyncio.run(main())
