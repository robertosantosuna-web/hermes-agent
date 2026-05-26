# Ubuntu Hardware Control — Reference for Cortex System

Machine: Acer Nitro 5 | CPU: AMD Ryzen 7 4800H | GPU: NVIDIA GTX 1650 4GB | OS: Ubuntu 26.04 Wayland

## Commands that work (no sudo)
```bash
sensors                           # CPU/GPU temps (k10temp, amdgpu, nvme, iwlwifi)
nvidia-smi                        # GPU status (requires reboot after driver mismatch)
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```

## Commands requiring sudo NOPASSWD
```bash
# CPU governor
echo schedutil | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# CPU boost
echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost   # disable
echo 1 | sudo tee /sys/devices/system/cpu/cpufreq/boost   # enable

# Swappiness
sudo sysctl vm.swappiness=20

# CPU max freq (limit to 2GHz)
echo 2000000 | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq
```

## NVIDIA driver mismatch fix
DKMS version: 595.71.05 | Kernel module: 595.58.03
**Fix:** Reboot. The DKMS module rebuilds on boot.
Post-reboot: `nvidia-smi` works, `nvidia-settings` for fan control.

## Known limitations
- **GPU fan control:** NOT exposed on Optimus laptops. BIOS/EC manages cooling.
- **CPU fan control:** ACPI-managed, no direct interface. `acer_wmi` has `cycle_gaming_thermal_profile=Y`.
- **Wayland screenshots:** GNOME blocks D-Bus portal. Workaround: Xvfb :99 for Wine apps.
- **Python venv:** Hermes venv uses Python 3.11. Cortex modules use `/usr/bin/python3` (3.14) which has all packages.
