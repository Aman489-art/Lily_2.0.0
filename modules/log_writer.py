# modules/log_writer.py

import os
import json
from datetime import datetime

def log_conversation(user_input, response, sentiment):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user_input,
        "lily_response": response,
        "sentiment": sentiment
    }

    log_path = "logs/conversation_log.json"
    if not os.path.exists("logs"):
        os.makedirs("logs")

    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(log_entry)
    with open(log_path, "w") as f:
        json.dump(data[-100:], f, indent=4)  # Keep last 100 interactions
