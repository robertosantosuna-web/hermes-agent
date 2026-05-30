#!/usr/bin/env python3
import json, os, sys
from urllib.request import urlopen, Request
from urllib.error import URLError
from pathlib import Path

API_URL = "https://mindcoach-541659260074.us-central1.run.app/api/chat?since=0"
STATE_FILE = os.path.expanduser("~/.hermes/mc_rest_state.json")

try:
    req = Request(API_URL, headers={"User-Agent": "Hermes-MindCoach/1.0"})
    with urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
except Exception as e:
    print("REMOTE:[]")
    sys.exit(0)

msgs = data.get("messages", [])
last_id = 0
if Path(STATE_FILE).exists():
    try:
        last_id = json.loads(Path(STATE_FILE).read_text()).get("last_id", 0)
    except:
        pass

new_user = [m for m in msgs if m.get("from") == "user" and m.get("id", 0) > last_id and not m.get("read")]
print("REMOTE:" + json.dumps(new_user))

new_last_id = data.get("last_id", 0)
Path(STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
Path(STATE_FILE).write_text(json.dumps({"last_id": new_last_id}))
