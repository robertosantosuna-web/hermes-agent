#!/usr/bin/env python3
"""
Envia notificação para o app MindCoach via REST API.
Uso: python3 notify_app.py "Título" "Mensagem" [tipo]
"""
import json, sys, urllib.request

URL = "https://mindcoach-541659260074.us-central1.run.app/api/notify"

def notify(titulo, msg, tipo="info", actions=None):
    payload = {"titulo": titulo, "msg": msg, "tipo": tipo}
    if actions:
        payload["actions"] = actions
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
                                  headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())
    except Exception as e:
        return {"ok": False, "error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: notify_app.py <título> <mensagem> [tipo]")
        sys.exit(1)
    titulo = sys.argv[1]
    msg = sys.argv[2]
    tipo = sys.argv[3] if len(sys.argv) > 3 else "info"
    result = notify(titulo, msg, tipo)
    print(json.dumps(result))
