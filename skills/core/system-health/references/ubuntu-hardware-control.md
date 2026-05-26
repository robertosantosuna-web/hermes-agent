# Ubuntu Hardware Control — Diagnóstico e Limitações

> Máquina: Acer Nitro 5 | CPU: AMD Ryzen 7 4800H | GPU: NVIDIA GTX 1650 | Ubuntu 26.04

## Estado Atual

### CPU
- Governor: `performance` (todos os 16 cores) — trocar para `schedutil`
- Boost: ATIVO — desativar reduz temperatura ~15°C
- Driver: `acpi-cpufreq` | Governors disponíveis: conservative, ondemand, userspace, powersave, performance, schedutil
- Temperatura: 52-71°C via k10temp

### NVIDIA GPU
- Driver mismatch: módulo 595.58.03 ≠ DKMS 595.71.05 → **precisa reboot**
- nvidia-smi / nvidia-settings quebrados até corrigir
- Fan control indisponível até driver funcionar

### Fans
- 22 cooling devices, maioria "Processor" (throttling, não fan)
- acer_wmi carregado com `cycle_gaming_thermal_profile=Y`
- Sem controle direto de velocidade — apenas perfis ACPI

### Memória
- 6.6 GB total, swappiness reduzido 60→20 ✅
- Swap: 7.3 GB (37% usado)

### Sensores
- lm-sensors instalado mas sem sensores detectados (ACPI-managed laptop)
- Disponíveis: k10temp (CPU), amdgpu (GPU edge), nvme (SSD), iwlwifi (WiFi)

## Otimizações Aplicadas
- [x] Swappiness 60→20
- [ ] CPU governor → schedutil (requer sudo NOPASSWD)
- [ ] CPU boost off (requer sudo NOPASSWD)
- [ ] NVIDIA driver reload (requer reboot)

## Comandos de Controle

```bash
# CPU Governor
echo schedutil | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# CPU Boost off
echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost

# Limitar frequência (2.0 GHz)
echo 2000000 | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq

# GPU Fan (após reboot)
nvidia-settings -a '[gpu:0]/GPUFanControlState=1' -a '[fan:0]/GPUTargetFanSpeed=60'
```

## Configuração sudo NOPASSWD Recomendada

Arquivo `/etc/sudoers.d/hermes-agent`:
```
roberto ALL=(ALL) NOPASSWD: /usr/bin/tee /sys/devices/system/cpu/*
roberto ALL=(ALL) NOPASSWD: /usr/sbin/sysctl vm.*
roberto ALL=(ALL) NOPASSWD: /usr/bin/nvidia-smi
roberto ALL=(ALL) NOPASSWD: /usr/bin/nvidia-settings
```
