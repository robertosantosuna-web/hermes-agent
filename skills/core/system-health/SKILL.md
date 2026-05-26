---
name: system-health
description: "Monitoramento de saúde do sistema: recursos (CPU, RAM, disco), processos, logs, integridade de arquivos e alertas preventivos."
version: 1.1.0
author: Roberto Rodrigues
license: MIT
metadata:
  hermes:
    tags: [system, monitoring, health, linux, resources, alerting]
    related_skills: [life-os, model-orchestration]
---

# System Health

Monitoramento proativo da saúde do sistema operacional. Prevenir problemas antes que afetem operação.

## CHECKS RÁPIDOS

### Check Completo (uma linha)
```bash
echo "=== $(date) ===" && echo "UPTIME: $(uptime -p)" && echo "LOAD: $(uptime | awk -F'load average:' '{print $2}')" && echo "CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2+$4"%"}')" && echo "MEM: $(free -h | awk '/^Mem:/ {print $3"/"$2 " (" $3/$2*100 "%" )"}')" && echo "DISK: $(df -h / | awk 'NR==2 {print $3"/"$2 " (" $5")"}')" && echo "HOME: $(df -h /home | awk 'NR==2 {print $3"/"$2 " (" $5")"}')" && echo "DATA: $(df -h /data 2>/dev/null | awk 'NR==2 {print $3"/"$2 " (" $5")"}' || echo 'N/A')" && echo "PROCS: $(ps aux | wc -l)" && echo "NET: $(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v 127.0.0.1 | head -1)"
```

### Métricas Individuais
```bash
# CPU
top -bn1 | head -5

# Memória
free -h

# Disco
df -h

# Processos
ps aux --sort=-%mem | head -10  # top por memória
ps aux --sort=-%cpu | head -10  # top por CPU

# Rede
ss -tuln                          # portas em escuta
ip -4 addr                        # IPs

# Temperatura (se disponível)
sensors
```

## TMPFS / QUOTA CHECK

/tmp pode ser um tmpfs com quota pequena (ex: 3.3G). Instalações grandes (pip com CUDA, transformers, ultralytics) quebram com "Cota da disco excedida" mesmo com disco livre.

Ver `references/tmpfs-quota-workaround.md` para receita completa.

```bash
# Verificar /tmp
df -h /tmp
mount | grep /tmp  # procura 'usrquota'

# Se /tmp tem quota pequena, usar TMPDIR alternativo
mkdir -p ~/tmp
TMPDIR=~/tmp pip install --no-cache-dir <pacotes>
```

## ALERTAS (LIMIARES)

| Métrica | Alerta Amarelo | Alerta Vermelho |
|---------|---------------|-----------------|
| CPU | >80% por 5min | >95% |
| RAM | >80% | >95% |
| Disco / | >80% | >90% |
| Disco /home | >85% | >95% |
| Disco /tmp (tmpfs) | >70% | >85% |
| Disco /data | >80% | >90% |
| Load avg | > núcleos * 1.5 | > núcleos * 3 |
| Swap usado | >500MB | >2GB |
| Quota atingida | — | EDQUOT em qq operação |

## WORKFLOW DE RESPOSTA A ALERTA

1. Identificar processo consumindo recurso
```bash
ps aux --sort=-%cpu | head -5   # CPU
ps aux --sort=-%mem | head -5   # RAM
```

2. Verificar logs relevantes
```bash
journalctl -n 50 --no-pager     # últimos 50 logs do sistema
dmesg | tail -30                # kernel messages
```

3. Decidir ação:
   - Processo zumbi → kill
   - Memory leak → restart serviço
   - Disco cheio → limpar caches, logs, /tmp
   - Swap excessivo → identificar leak, considerar mais RAM

## LVM DISK CHECK (adicionado 24/05/2026)

Sistema tem 2 discos físicos unificados via LVM:
- nvme0n1 (476G) — sistema /
- sda (953G) — data_vg: lv_home (/home, 492G) + lv_data (/data, 445G)

```bash
# Status LVM
sudo vgs data_vg && sudo lvs data_vg
df -h /home /data

# Verificar saúde dos discos físicos
sudo smartctl -H /dev/nvme0n1 2>/dev/null || echo "nvme sem smartctl"
sudo smartctl -H /dev/sda 2>/dev/null || echo "sda sem smartctl"
```

## LIMPEZA PREVENTIVA

### Caches e Temporários
```bash
# Docker (se instalado)
docker system prune -f

# Snap packages
sudo snap list

# Logs grandes
du -sh /var/log/* | sort -rh | head -10

# Arquivos temporários
find /tmp -type f -atime +7 -delete 2>/dev/null
```

### Home Directory
```bash
# Maiores diretórios
du -sh ~/.* ~/* 2>/dev/null | sort -rh | head -15

# Cache pip
pip cache purge 2>/dev/null

# Node modules (verificar projetos)
find ~ -name "node_modules" -type d -prune -exec du -sh {} \; 2>/dev/null | sort -rh | head -5
```

## INTEGRIDADE DE ARQUIVOS

```bash
# Verificar skills
ls -la ~/.hermes/skills/

# Verificar config
hermes config show 2>/dev/null

# Verificar se ferramentas críticas existem
which git curl python3 node
```

## CRON JOB: HEALTH CHECK

### Diário (9h)
```
Ação: executar check completo, comparar com limiares
Alertar se: qualquer métrica em amarelo
Urgente se: qualquer métrica em vermelho
```

## SERVIÇOS SYSTEMD — PROTEÇÃO DE MEMÓRIA

Serviços de longa duração (gateway, bridges, bots) acumulam memória e podem ser mortos pelo OOM killer. Configurar limites no próprio systemd evita que travem o sistema inteiro.

### Configuração no unit file

```ini
[Service]
MemoryMax=2.5G          # systemd mata o serviço ANTES de travar o sistema
MemorySwapMax=3G        # evita swap infinito
OOMScoreAdjust=200      # morre antes de apps essenciais (ajuste: -1000 a 1000)
Restart=always          # volta automaticamente após ser morto
RestartSec=5
```

### Watchdog (cron job)

Criar 2 cron jobs:

1. **Health check frequente** (a cada 10 min): verifica se serviço está rodando e se memória < threshold. Reinicia se necessário.
2. **Reinício diário** (ex: 3h da manhã): restart programado para liberar memória acumulada (memory leak gradual).

```bash
# Script mínimo de health check
MEM=$(systemctl --user status hermes-gateway.service 2>&1 | grep -oP 'Memory: \K[0-9.]+(?=[A-Z])')
if [ -z "$MEM" ]; then
  systemctl --user restart hermes-gateway.service
elif (( $(echo "$MEM > 2.3" | bc -l) )); then
  systemctl --user restart hermes-gateway.service
fi
```

### Diagnóstico de crash

```bash
# Ver se foi OOM killer
dmesg | grep -i 'out of memory\|oom_reaper' | tail -5

# Ver detalhes do serviço
systemctl --user status <serviço>.service

# Histórico de restarts
journalctl --user -u <serviço>.service --since "1 day ago" | grep -E 'Started|Stopped|Failed|Killed'
```

## LOGS OPERACIONAIS

### Localização
```bash
~/.hermes/logs/         # Logs do Hermes Agent
journalctl --user       # Logs do systemd (usuário)
/var/log/syslog         # Logs do sistema
```

### Comandos Úteis
```bash
# Últimos erros
journalctl -p err -n 20 --no-pager

# Logs desde boot
journalctl -b

# Seguir logs em tempo real
journalctl -f
```

## References

- **[disk-quota-workaround.md](references/disk-quota-workaround.md)** — `/tmp` tmpfs quota fix for pip installs
- **[gateway-protection-setup.md](references/gateway-protection-setup.md)** — systemd MemoryMax + watchdog cron jobs for gateway crash prevention

## ANTI-PADRÕES

- NÃO ignorar alerta de disco cheio — trava sistema
- NÃO matar processo sem saber o que é
- NÃO rodar `rm -rf` sem dupla verificação
- NÃO deixar swap >50% sem investigar
- NÃO acumular arquivos em /tmp
