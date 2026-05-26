# Gateway Protection — Receita Completa

Configuração aplicada ao `hermes-gateway.service` em 25/05/2026 após crash por OOM (2.4G RAM + 3.3G swap em 12h).

## 1. systemd unit — Memory limits

Adicionar ao `[Service]`:

```ini
MemoryMax=2.5G
MemorySwapMax=3G
OOMScoreAdjust=200
```

Já existente (manter):
```ini
Restart=always
RestartSec=5
```

Recarregar:
```bash
systemctl --user daemon-reload
systemctl --user restart hermes-gateway.service
```

## 2. Watchdog cron job (10 min)

Criar via Hermes:
```
cronjob action='create'
  schedule='*/10 * * * *'
  repeat=8640
  enabled_toolsets=['terminal']
  deliver='origin'
  prompt='Check if hermes-gateway service is running... restart if >2.3GB or offline'
```

## 3. Daily restart cron job (3h)

```
cronjob action='create'
  schedule='0 3 * * *'
  repeat=365
  enabled_toolsets=['terminal']
  deliver='origin'
  prompt='Restart hermes-gateway.service to clear accumulated memory'
```

## 4. Diagnóstico pós-crash

```bash
# Confirmar OOM
dmesg | grep -i 'out of memory\|oom_reaper' | tail -10

# Ver histórico
journalctl --user -u hermes-gateway.service --since "1 day ago" | grep -E 'Started|Stopped|Failed|Killed|Memory'

# Status atual
systemctl --user status hermes-gateway.service
```

## IDs de cron jobs ativos

- Watchdog: `8fbe686d2715` (a cada 10 min, reinicia se >2.3GB ou offline)
- Daily restart: `64a76639d4d2` (3h da manhã, anti-leak)
