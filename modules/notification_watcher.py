import subprocess
import json
import os
import time
from dotenv import load_dotenv
from modules.tts_output import speak

load_dotenv()
phone_ssh = os.getenv("SSH_CODE")

import subprocess
import json
import time


# 🧠 Only important package names (you can customize this)
PRIORITY_APPS = {
    "com.whatsapp": "WhatsApp",
    "com.google.android.gm": "Gmail",
    "com.google.android.dialer": "Phone",
    "com.android.mms": "SMS",
    "com.truecaller": "Truecaller",
    "com.instagram.android": "Instagram",
    
}

# 📲 Tracks already spoken notifications
seen_notifications = set()

def get_priority_notifications():
    try:
        cmd = phone_ssh
        output = subprocess.check_output(cmd, shell=True, text=True).strip()
        data = json.loads(output)
        return data if isinstance(data, list) else []
    except:
        return []


def watch_notifications_loop(poll_interval=10):
    print("👀 Watching for priority notifications...\n")
    
    while True:
        notifications = get_priority_notifications()

        for notif in notifications:
            package = notif.get("packageName", "")
            title = notif.get("title", "")
            content = notif.get("content", "")
            
            # Create unique ID
            unique_id = (package + title + content).strip()

            # Skip if already seen or not a priority app
            if unique_id in seen_notifications or package not in PRIORITY_APPS:
                continue

            # 📲 Simple notification
            app_name = PRIORITY_APPS[package]
            print(f"📲 {app_name}: {title} - {content}")
            seen_notifications.add(unique_id)

        time.sleep(poll_interval)

