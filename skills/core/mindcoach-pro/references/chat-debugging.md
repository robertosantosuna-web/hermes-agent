# Chat Debug — Diagnóstico de mensagens que não chegam

## Fluxo normal (esperado)

1. Celular → WebSocket → Cloudflare Tunnel → Bridge (:9877) → inbox (`mindcoach_chat_inbox.json`)
2. Hermes → `mindcoach_control.py chat` → Bridge → WebSocket → Celular

## Procedimento de diagnóstico (25/05)

Quando o celular mostra "vivo" (WebSocket conectado) mas mensagens NÃO chegam ao inbox:

### 1. Ativar debug log na bridge
O bridge tem hook de debug em `process_message`:
```python
with open(Path.home() / '.hermes' / 'bridge_debug.log', 'a') as f:
    f.write(f"[{datetime.now().isoformat()}] RAW: {message[:300]}\n")
```
Reiniciar bridge: `systemctl --user restart mindcoach-bridge.service`

### 2. Testar túnel do servidor
```bash
python3 -c "
import asyncio, websockets, json
async def test():
    async with websockets.connect('wss://<tunnel>.trycloudflare.com') as ws:
        await ws.send(json.dumps({'type':'chat_message','texto':'TESTE','timestamp':0}))
        print(await asyncio.wait_for(ws.recv(), timeout=5))
asyncio.run(test())
"
```

### 3. Checar Cloudflare Tunnel URL
O bridge-url serve o último túnel conhecido. Se o cloudflared reiniciou, a URL MUDOU.
```bash
curl -s https://mindcoach-541659260074.us-central1.run.app/bridge-url
```
Comparar com o túnel ativo:
```bash
journalctl --user -u cloudflared-mindcoach.service --since "2h ago" | grep trycloudflare | tail -1
```
Se diferente, atualizar `~/.hermes/mindcoach-pro/bridge-url` e redeployar.

### 4. Forçar reload no celular
Service Worker pode segurar versão antiga do `websocket.js` sem o handler de `chat_message`.
- Fechar aba e reabrir
- Ou acessar URL com param: `?v=5`
- Ou usar endpoint local: `http://192.168.2.8:9878`

### 5. Verificar conexões ativas
```bash
ss -tnp | grep -E '9877|cloudflared'
```
Se bridge não tem conexões TCP, o túnel está quebrado ou o app não conectou.

## Estado conhecido (não resolvido)

- WebSocket mostra "vivo" (conexão estabelecida)
- Bridge debug log NÃO recebe `chat_message`
- Mensagem nunca chega ao inbox
- Hipótese: `send-to-hermes` event não está disparando, ou `socket.send()` falha silenciosa no mobile Chrome
