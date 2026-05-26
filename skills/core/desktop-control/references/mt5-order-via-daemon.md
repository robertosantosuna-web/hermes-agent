# MT5 Order Execution via Desktop Daemon (ATUALIZADO 25/05/2026)

## ⚠️ CRÍTICO: Daemon v3 usa KEYCODES NUMÉRICOS

O daemon v3 converte nomes → keycodes internamente (81 entradas mapeadas). O ydotool subjacente
só aceita keycodes numéricos (ex: 67=F9, 28=Enter, 15=Tab, 56=Alt, 48=B, 30=A).

**Keycodes essenciais para MT5:**
| Keycode | Nome | Função |
|---------|------|--------|
| 67 | f9 | New Order |
| 28 | enter | Confirmar |
| 15 | tab | Navegar campos |
| 1 | escape | Fechar |
| 56+48 | alt+b | Buy |
| 56+31 | alt+s | Sell |
| 29+30 | ctrl+a | Selecionar tudo |
| 29+20 | ctrl+t | Terminal |

## 🔍 VISÃO: xdotool no DISPLAY=:0 vê janelas XWayland

MT5 Wine cria janelas XWayland — visíveis via xdotool. NÃO usar GNOME overview (não indexa Wine).

Ações do daemon para visão:
```python
# Listar todas as janelas XWayland visíveis
await call("windows")  
# → [{id, name, position, size}, ...]

# Janela ativa
await call("active")
# → {id, name}

# Focar janela por ID
await call("focus", {"wid": 10486700})

# Encontrar e focar MT5 especificamente
await call("find_mt5")
# → {id, name, position, size} + focused: true
```

## ⚠️ CRÍTICO: F9 só funciona em janela de CHART

O F9 (New Order) só abre a janela de ordem quando uma **janela de chart** está focada.
NÃO funciona no terminal principal do MT5 (título com número da conta).

**Sequência correta:**
1. Encontrar janela de chart via `windows` (nome contém par ex: "USDJPY, US Dollar...")
2. Focar com `focus` + clicar dentro com `click`
3. F9
4. Preencher símbolo, volume, SL, TP
5. Alt+B ou Alt+S

## Fluxo completo validado

```python
async def place_order(symbol, direction, volume, sl, tp):
    import websockets, asyncio, json, re
    async with websockets.connect('ws://localhost:9876', max_size=50*1024*1024) as ws:
        async def call(action, params=None, delay=0):
            msg = {"action": action, "id": 0}
            if params: msg["params"] = params
            await ws.send(json.dumps(msg))
            r = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            if delay: await asyncio.sleep(delay)
            return r

        # 1. Fechar janelas de ordem existentes
        r = await call("windows")
        for w in r['data']:
            if 'ordem:' in w['name'].lower():
                await call("focus", {"wid": w['id']}, delay=0.3)
                await call("key", {"key": "escape"}, delay=0.5)

        # 2. Encontrar janela de CHART (qualquer par serve)
        r = await call("windows")
        charts = [w for w in r['data'] 
                  if any(p in w['name'].lower() for p in ['usd','eur','gbp']) 
                  and 'ordem' not in w['name'].lower()]
        if not charts:
            return {'error': 'Nenhuma janela de chart encontrada'}
        
        chart = charts[0]
        pos = chart['position']
        nums = re.findall(r'\d+', pos)
        cx, cy = int(nums[0]) + 400, int(nums[1]) + 300  # Centro do chart

        # 3. Focar + clicar no chart
        await call("focus", {"wid": chart['id']}, delay=0.3)
        await call("mousemove", {"x": cx, "y": cy}, delay=0.1)
        await call("click", {"x": cx, "y": cy, "button": 0}, delay=0.5)

        # 4. F9 → preencher ordem
        await call("key", {"key": "f9"}, delay=2)
        await call("key", {"key": "ctrl+a"}, delay=0.1)
        await call("type", {"text": symbol}, delay=0.5)
        await call("key", {"key": "enter"}, delay=0.5)
        await call("key", {"key": "tab"}, delay=0.1)
        await call("key", {"key": "tab"}, delay=0.1)
        await call("key", {"key": "ctrl+a"}, delay=0.05)
        await call("type", {"text": str(volume)}, delay=0.2)
        await call("key", {"key": "tab"}, delay=0.1)
        await call("key", {"key": "tab"}, delay=0.1)
        await call("key", {"key": "ctrl+a"}, delay=0.05)
        await call("type", {"text": f'{sl:.5f}'}, delay=0.2)
        await call("key", {"key": "tab"}, delay=0.1)
        await call("key", {"key": "ctrl+a"}, delay=0.05)
        await call("type", {"text": f'{tp:.5f}'}, delay=0.3)
        
        key = "alt+b" if direction.upper() in ('BUY', 'LONG') else "alt+s"
        await call("key", {"key": key}, delay=1.5)
        await call("key", {"key": "escape"}, delay=0.5)
        
        # 5. Verificar se janela de ordem apareceu
        r = await call("windows")
        order_wins = [w for w in r['data'] 
                      if 'ordem:' in w['name'].lower() and symbol.upper() in w['name'].upper()]
        
        return {
            'status': 'sent',
            'verified': len(order_wins) > 0,
            'chart_used': chart['name'][:50]
        }
```

## Pitfalls (NOVOS — 25/05)

| Pitfall | Causa | Solução |
|---------|-------|---------|
| F9 não abre ordem | Terminal principal focado, não chart | Focar janela de chart primeiro |
| GNOME overview não acha MT5 | Wine Wayland não indexado | Usar `windows` action (xdotool) |
| ydotool "key F9" falha | ydotool só aceita keycodes (67) | Daemon v3 converte nome→keycode |
| Parâmetros no nível raiz falham | Daemon espera `params` sub-objeto | `{"action":"key","params":{"key":"f9"}}` |
| Screenshot mss tela preta | GNOME Wayland não expõe ao XWayland | Usar xdotool `windows` para "ver" |

## O que NÃO funciona

| Abordagem | Motivo |
|-----------|--------|
| `xdotool` com `DISPLAY=:99` | Xvfb morto, MT5 no Wayland |
| `ydotool` direto sem env vars | Falta XDG_RUNTIME_DIR, WAYLAND_DISPLAY |
| GNOME overview busca | Wine Wayland não indexado |
| `wtype` | GNOME sem virtual-keyboard-v1 |
| F9 no terminal MT5 principal | Precisa estar na janela de chart |
