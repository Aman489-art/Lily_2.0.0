import os
import json
from datetime import datetime
from modules.emotion_analyser import get_sentiment

HISTORY_FILE = "data/chat_history.json"
os.makedirs("data", exist_ok=True)

def save_to_history(user, assistant):
    mood = get_sentiment(user)
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "lily": assistant,
        "mood": mood
    }

    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except json.JSONDecodeError:
            history = []
    else:
        history = []

    history.append(data)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-50:], f, indent=2)  # Keep only last 50 for speed

def recall_context(last_n=5):
    if not os.path.exists(HISTORY_FILE):
        return ""

    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)

    recent = history[-last_n:]
    safe_lines = []

    for h in recent:
        try:
            # Support both formats
            user = h.get("user") or h.get("user_message")
            assistant = h.get("lily") or h.get("ai_response")
            mood = h.get("mood")
            timestamp = h.get("timestamp", "unknown")

            safe_lines.append(f"[{timestamp}] User: {user} → Lily: {assistant} ({mood})")

        except Exception as e:
            print(f"⚠️ Skipped corrupt history entry: {e}")
            continue

    return "\n".join(safe_lines)



def load_chat_history(date_filter=None, limit=10):
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)
    if date_filter:
        history = [h for h in history if h["timestamp"].startswith(date_filter)]
    return history[-limit:]

def clean_chat_history():
    if not os.path.exists(HISTORY_FILE):
        return
    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)
    clean = []
    for h in history:
        if all(k in h for k in ["timestamp", "user", "lily", "mood"]):
            clean.append(h)
    with open(HISTORY_FILE, "w") as f:
        json.dump(clean, f, indent=2)
    print(f"🧹 Cleaned {len(history) - len(clean)} broken entries from chat history.")

