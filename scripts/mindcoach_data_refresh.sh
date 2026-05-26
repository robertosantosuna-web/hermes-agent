#!/bin/bash
# Rebuild data.json and refresh bridge
bash ~/.hermes/mindcoach-pro/build_data.sh
# Notify bridge to reload data
python3 -c "
import asyncio, json, websockets
async def refresh():
    async with websockets.connect('ws://127.0.0.1:9877') as ws:
        await ws.send(json.dumps({'type': 'refresh_data'}))
        print('data refreshed')
asyncio.run(refresh())
" 2>/dev/null || echo "bridge offline"
