# Brain Browser — Configuração e Pitfalls (25/05/2026)

## Serviço (systemd)

Arquivo: `~/.config/systemd/user/hermes-brain-browser.service`

```ini
[Service]
Type=simple
ExecStartPre=/usr/bin/python3 %h/.hermes/scripts/tv_session_restore.py
ExecStart=/usr/bin/brave-browser \
  --headless=new \
  --remote-debugging-port=9223 \
  --user-data-dir=%h/.hermes/browser/profile \
  --no-first-run --no-default-browser-check --disable-gpu \
  --no-sandbox --window-size=1280,900 --disable-dev-shm-usage \
  --ignore-certificate-errors about:blank
ExecStartPost=/bin/sleep 3 && /usr/bin/python3 %h/.hermes/scripts/tv_session_restore.py
Restart=always
RestartSec=5
Environment=DISPLAY=:99
```

## Pitfalls

### 1. ExecStartPost pode falhar (exit code 1)
Se o browser não carregar a tempo, o `tv_session_restore.py` no Post falha e o systemd dá restart loop.
**Solução**: iniciar o Brave manualmente sem o serviço:
```bash
/usr/bin/brave-browser --headless=new --remote-debugging-port=9223 \
  --user-data-dir=/home/roberto/.hermes/browser/profile \
  --no-first-run --no-sandbox --disable-gpu --window-size=1280,900 \
  --disable-dev-shm-usage --ignore-certificate-errors about:blank &
```

### 2. Porta alterna entre IPv4 e IPv6
- Systemd: tende a escutar em `[::1]:9223` (IPv6)
- Manual: tende a escutar em `127.0.0.1:9223` (IPv4)
- Sempre testar ambos antes de declarar offline

### 3. RAM: cada aba CDP = ~200MB
Abrir abas em loop sem reuso satura a RAM em minutos.
`brain_browser.py` corrigido (25/05) com `navigate(url, reuse=True)`.

### 4. tv_session_restore.py
Restaura cookies do TradingView para manter a sessão logada (Google OAuth).
Cookies salvos em `~/.hermes/browser/tradingview_cookies.json`.
Se falhar, o TradingView não carrega dados — testar com `--title` para ver se mostra preço.

## Verificação rápida

```bash
# Status
python3 ~/.hermes/scripts/brain_browser.py --status

# Teste de cotação (sem abrir abas novas)
python3 ~/.hermes/scripts/forex_quote.py EURUSD
# Deve retornar: {"symbol": "EURUSD", "bid": 1.164XX, ...}
```

## FILE LOCK — Serialização de Chamadas Concorrentes (25/05/2026)

Múltiplos cron jobs chamam `brain_browser.py` simultaneamente. Sem lock, cada chamada concorrente pode criar uma nova aba (se a aba existente estiver ocupada), levando a 80+ abas acumuladas.

### Implementação

No `brain_browser.py`, antes do argparse:

```python
import fcntl

def main():
    lockfile = Path('/tmp/brain_browser.lock')
    lockfile.touch(exist_ok=True)
    lock_fd = open(lockfile, 'w')
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("BUSY: another brain_browser instance is running", file=sys.stderr)
        sys.exit(0)
```

## CLEANUP AUTOMÁTICO DE ABAS (25/05/2026)

No startup de cada chamada, fecha todas as abas extras mantendo apenas 1:

```python
async def cleanup_tabs():
    """Fecha abas extras, mantendo apenas 1 página."""
    tabs = json.loads(urllib.request.urlopen(f"{CDP_URL}/json/list").read())
    page_tabs = [t for t in tabs if t.get('type') == 'page']
    if len(page_tabs) <= 1:
        return len(page_tabs)
    closed = 0
    for t in page_tabs[1:]:
        urllib.request.urlopen(
            urllib.request.Request(f"{CDP_URL}/json/close/{t['id']}"), timeout=3)
        closed += 1
    return closed
```

Chamado em `run()` antes de qualquer operação: `cleaned = await cleanup_tabs()`

## CRON JOBS QUE CAUSAM VAZAMENTO

Estes jobs chamam `brain_browser.py` — manter pausados ou com intervalo ≥ 5min:

| Job | Script | Frequência | Status 25/05 |
|-----|--------|-----------|-------------|
| Brain Weekend Study Scanner | brain_signal_generator.py | */2 min | PAUSADO |
| TV Chart Scanner | tv_chart_scanner.sh | */30 min | PAUSADO |

O lock resolve concorrência, mas jobs muito frequentes ainda geram contenção desnecessária.
