#!/usr/bin/env python3
"""
MindCoach Chat Monitor — checks Cloud Run /api/chat for new user messages.
Auto-resets state on detected inconsistency (redeploy wiped chat data).
Outputs NEW_USER_MESSAGES JSON if any user messages found, else NO_NEW_MESSAGES.
"""
import json, os, sys, urllib.request

CHAT_URL = os.environ.get("MINDCOACH_URL", "https://mindcoach-541659260074.us-central1.run.app") + "/api/chat"
STATE_FILE = os.path.expanduser("~/.hermes/mindcoach_chat_state.json")

def get_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {"last_id": 0}

def save_state(last_id):
    with open(STATE_FILE, "w") as f:
        json.dump({"last_id": last_id}, f)

def fetch(since=0):
    try:
        req = urllib.request.Request(f"{CHAT_URL}?since={since}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"ERROR_FETCH:{e}", file=sys.stderr)
        return None

def post(text, reply_to=None):
    """Post assistant response to chat API."""
    try:
        data = json.dumps({"from": "assistant", "text": text, "reply_to": reply_to}).encode()
        req = urllib.request.Request(CHAT_URL, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"ERROR_POST:{e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    state = get_state()
    data = fetch(since=state["last_id"])
    
    if not data:
        print("OFFLINE")
        sys.exit(1)
    
    api_last_id = data.get("last_id", 0)
    msgs = data.get("messages", [])
    
    # Auto-fix: if state.last_id > api_last_id, data was wiped (redeploy)
    # Reset to 0 and re-fetch to avoid silently missing messages
    if state["last_id"] > api_last_id:
        state["last_id"] = 0
        save_state(0)
        data = fetch(since=0)
        if data:
            msgs = data.get("messages", [])
    
    user_msgs = [m for m in msgs if m["from"] == "user"]
    
    if not user_msgs:
        print("NO_NEW_MESSAGES")
    else:
        print(f"NEW_USER_MESSAGES:{json.dumps(user_msgs)}")
        max_id = max(m["id"] for m in msgs)
        save_state(max_id)
