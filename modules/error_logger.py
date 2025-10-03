import traceback
from datetime import datetime
import os

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "error_log.txt")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

def log_error(error: Exception, context: str = "General", extra: str = ""):
    with open(LOG_FILE, "a") as f:
        f.write("\n" + "=" * 60 + "\n")
        f.write(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"📍 Context: {context}\n")
        if extra:
            f.write(f"📝 Extra: {extra}\n")
        f.write("❌ Error:\n")
        f.write(traceback.format_exc())
        f.write("=" * 60 + "\n")
