#!/usr/bin/env python3
"""Atualiza bridge-url no Cloud Run quando túnel Cloudflare muda.

Extrai a URL atual do túnel via journalctl e atualiza o arquivo
de config que o app lê dinamicamente via /bridge-url.
"""

import subprocess, re, sys


def get_tunnel_url():
    """Extrai URL atual do túnel via journalctl."""
    try:
        output = subprocess.check_output(
            ["journalctl", "--user", "-u", "cloudflared-mindcoach",
             "--no-pager", "--since", "5 minutes ago"],
            text=True, timeout=10
        )
        urls = re.findall(r'https://[a-z-]+\.trycloudflare\.com', output)
        if urls:
            return urls[-1]  # última URL = a ativa
    except Exception:
        pass
    return None


def update_config(url: str, config_path: str = '/home/roberto/.hermes/mindcoach-pro/bridge-url'):
    """Escreve a URL do túnel como wss:// no arquivo de config."""
    ws_url = url.replace('https://', 'wss://')
    with open(config_path, 'w') as f:
        f.write(ws_url + '\n')
    print(f"Updated: {ws_url}")
    return True


if __name__ == '__main__':
    url = get_tunnel_url()
    if url:
        update_config(url)
    else:
        print("Tunnel URL not found", file=sys.stderr)
        sys.exit(1)
