#!/usr/bin/env python3
"""Envia resposta de chat do Hermes Agent para o MindCoach App via WebSocket bridge."""
import asyncio, json, sys

async def send_response(texto):
    import websockets
    uri = "ws://127.0.0.1:9877"
    async with websockets.connect(uri) as ws:
        cmd = {"type": "chat_response", "texto": texto}
        await ws.send(json.dumps(cmd))
        print(f"[chat→app] {texto[:80]}")

if __name__ == '__main__':
    texto = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read().strip()
    if texto:
        asyncio.run(send_response(texto))
