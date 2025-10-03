import subprocess
import json
import os
from dotenv import load_dotenv

load_dotenv()
phone_ssh = os.getenv("SSH_CODE")  # Your usual SSH string

def get_phone_notifications():
    try:
        cmd = f"{phone_ssh} termux-notification-list"
        output = subprocess.check_output(cmd, shell=True, text=True).strip()

        data = json.loads(output)
        if not data:
            return "📭 No active notifications right now."

        message = "📱 Here are your phone notifications:\n"
        for notif_id, notif in data.items():
            app = notif.get("package_name", "Unknown App")
            title = notif.get("title", "No Title")
            content = notif.get("content", "No Content")
            message += f"- {title} ({app}): {content}\n"

        return message.strip()

    except json.JSONDecodeError:
        return "⚠️ Couldn't read notifications. Maybe the phone sent bad data."
    except Exception as e:
        return f"⚠️ Failed to fetch notifications: {e}"
