# Brain Browser Lock Pattern

## Problema
O `brain_browser.py` é chamado por 7+ scripts diferentes via cron. Quando múltiplas chamadas ocorrem simultaneamente, cada uma tenta usar a aba existente. Se a aba está ocupada (conexão WebSocket ativa), a próxima chamada cria uma nova aba. Em horas, acumulam-se 80+ abas TradingView, consumindo RAM e travando o browser.

## Solução: File Lock + Tab Cleanup

### 1. File Lock no início da main()
```python
import fcntl
from pathlib import Path

lockfile = Path('/tmp/brain_browser.lock')
lockfile.touch(exist_ok=True)
lock_fd = open(lockfile, 'w')
try:
    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    print("BUSY: another brain_browser instance is running", file=sys.stderr)
    sys.exit(0)
```

### 2. Cleanup de abas extras no startup
```python
async def cleanup_tabs():
    """Fecha todas as abas extras, mantendo apenas 1 página."""
    tabs = json.loads(urllib.request.urlopen(f"{CDP_URL}/json/list").read())
    page_tabs = [t for t in tabs if t.get('type') == 'page']
    if len(page_tabs) <= 1:
        return len(page_tabs)
    
    closed = 0
    for t in page_tabs[1:]:
        try:
            urllib.request.urlopen(
                urllib.request.Request(f"{CDP_URL}/json/close/{t['id']}"),
                timeout=3
            )
            closed += 1
        except:
            pass
    return closed
```

### 3. Chamar cleanup antes de qualquer operação
```python
async def run():
    cleaned = await cleanup_tabs()
    if isinstance(cleaned, int) and cleaned > 0:
        print(f"CLEANUP: {cleaned} abas fechadas", file=sys.stderr)
    # ... resto das operações
```

## Cron Jobs Problemáticos
- **Brain Weekend Study Scanner** (`97892173c440`): `brain_signal_generator.py` a cada 2min — **720 chamadas/dia**
- **TV Chart Scanner** (`fb82d93e0783`): `tv_chart_scanner.sh` a cada 30min
- Ambos devem ficar PAUSADOS. Manter apenas scanners em horários espaçados (1-2x/dia).
