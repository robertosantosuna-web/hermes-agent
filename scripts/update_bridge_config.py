#!/usr/bin/env python3
"""Atualiza bridge-url no Cloud Run quando túnel muda."""
import subprocess, re, sys, time

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
    except:
        pass
    return None

def update_config(url):
    ws_url = url.replace('https://', 'wss://')
    config_path = '/home/roberto/.hermes/mindcoach-pro/bridge-url'
    with open(config_path, 'w') as f:
        f.write(ws_url)
    print(f"Updated: {ws_url}")
    return True

if __name__ == '__main__':
    url = get_tunnel_url()
    if url:
        update_config(url)
    else:
        print("Tunnel URL not found", file=sys.stderr)
        sys.exit(1)
