# Trailing Stop v2 — Revisão Multi-IA (28/05/2026)

## Contexto

Após implementar o trailing stop aprimorado (v1), os 4 especialistas IA foram consultados:
- **Gemini** (Google)
- **DeepSeek** 
- **ChatGPT** (OpenAI)
- **Grok** (xAI)

Extraídos via CDP WebSocket (`ws://localhost:9225`) das abas abertas no Edge.

## Convergência (todos concordaram)

### 1. CAP na aceleração — CRÍTICO
A aceleração 1.3x faz proteção passar de 100% após 8R → stop inválido (acima do preço no long).
```python
TRAIL_ACCEL_CAP = 0.95  # Stop NUNCA trava >95% do lucro
protect_pct = min(0.95, base_pct * accel)
```

### 2. Breakeven com buffer
SL exato no entry pode sair negativo (spread + slippage). Buffer:
```python
atr_buffer = max(spread * 1.5, ATR * 0.1)
breakeven_sl = entry + atr_buffer  # long
```

### 3. Aceleração por ativo
XAUUSD é mais volátil → aceleração menor:
```python
ACCEL_BY_ASSET = {
    'XAUUSD': 1.15,  # Ouro = menos agressivo
    'EURUSD': 1.30,
    'USDJPY': 1.25,
    'GBPJPY': 1.20,
    'EURJPY': 1.20,
    'default': 1.25,
}
```

## Resultado Final (v2)

### Parâmetros
```python
BREAKEVEN_TRIGGER_RR = 1.0
BREAKEVEN_BUFFER_SPREAD = 1.5
BREAKEVEN_BUFFER_ATR = 0.1
ATR_TRAIL_MULTIPLIER = 0.5
TRAIL_ACCEL_CAP = 0.95

LOCK_STEPS = [
    (1.0, 0.25),   # 1R → trava 25%
    (2.0, 0.40),   # 2R → trava 40%
    (3.0, 0.55),   # 3R → trava 55%
    (5.0, 0.70),   # 5R → trava 70%
    (8.0, 0.82),   # 8R → trava 82%
    (12.0, 0.90),  # 12R → trava 90%
]
```

### Efeito da aceleração por ativo

| RR | Base | EURUSD (1.30x) | XAUUSD (1.15x) | Cap |
|----|------|----------------|----------------|-----|
| 1R | 25% | 32.5% | 28.8% | — |
| 2R | 40% | 52.0% | 46.0% | — |
| 3R | 55% | 71.5% | 63.3% | — |
| 5R | 70% | 91.0% | 80.5% | — |
| 8R | 82% | 95.0% (cap) | 94.3% | ✅ |
| 12R | 90% | 95.0% (cap) | 95.0% (cap) | ✅ |

### Função get_atr()
Usa yfinance M15, subprocess isolado. Lida com MultiIndex columns do yfinance.
```python
def get_atr(symbol, tf='M15', periods=14):
    # Mapeia símbolos MT5 → Yahoo Finance
    # Ex: EURUSD → EURUSD=X, XAUUSD → GC=F
    # ATENÇÃO: auto_adjust=False gera MultiIndex columns
```

ATRs típicos (M15, 28/05/2026):
- EURUSD: 0.00024 (2.4 pips)
- GBPUSD: 0.00029 (2.9 pips)  
- USDJPY: 0.0485 (4.85 pips)
- XAUUSD: 6.99 pontos

### Checklist de validação (DeepSeek)
- [ ] Range lateral forte — breakeven tira cedo? Desejável?
- [ ] Gap noturno — trailing pré-gap vs pós-gap?
- [ ] Spike de volatilidade — se ATR dobra em 1 min, stop ajusta?
- [ ] Múltiplas posições escalonadas — cada entry tem seu breakeven?

## Padrão: Consulta Multi-IA via CDP

Técnica reutilizável para code review:
1. Abrir 4 abas (Gemini, DeepSeek, ChatGPT, Grok) com o mesmo prompt
2. Extrair respostas via CDP WebSocket: `ws://localhost:9225/devtools/page/{target_id}`
3. Enviar `Runtime.evaluate` com `document.body.innerText`
4. Encontrar convergência entre as respostas
5. Aplicar correções que TODOS concordam

Código de extração:
```python
import json, asyncio
from websockets import connect

async def extract(url):
    async with connect(url) as ws:
        msg = json.dumps({"id":1,"method":"Runtime.evaluate",
            "params":{"expression":"document.body.innerText","returnByValue":True}})
        await ws.send(msg)
        resp = await asyncio.wait_for(ws.recv(), timeout=8)
        return json.loads(resp)
```
