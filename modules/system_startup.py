import datetime
import os
import time
from modules.tts_output import speak

LOG_PATH = "logs/startup_log.txt"
CHANGELOG_PATH = "logs/last_changelog_shown.txt"

def get_time_based_greeting():
    """Get appropriate greeting based on time of day"""
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 18:
        return "Good afternoon"
    elif 18 <= hour < 22:
        return "Good evening"
    else:
        return "You're still up, huh?"

def get_last_run_info():
    """Get timestamp of last run from log file"""
    if os.path.exists(LOG_PATH):
        try:
            with open(LOG_PATH, "r") as f:
                lines = f.readlines()
                if lines:
                    last_entry = lines[-1].strip()
                    last_time_str = last_entry.replace("System started at ", "")
                    last_time = datetime.datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
                    return last_time
        except:
            pass
    return None

def get_time_difference_message(last_time):
    """Generate human-readable message about time since last run"""
    now = datetime.datetime.now()
    delta = now - last_time

    if delta.days > 0:
        return f"It's been {delta.days} day{'s' if delta.days > 1 else ''} since we last talked."
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"It's been {hours} hour{'s' if hours > 1 else ''} since I was last active."
    elif delta.seconds > 300:
        minutes = delta.seconds // 60
        return f"It's been {minutes} minutes since our last session."
    else:
        return None

def log_current_start():
    """Log current startup time"""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(f"System started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    except Exception:
        pass

def show_changelog_once():
    """Show changelog once per day"""
    try:
        today = datetime.date.today().isoformat()
        if os.path.exists(CHANGELOG_PATH):
            with open(CHANGELOG_PATH, 'r') as f:
                last_date = f.read().strip()
                if last_date == today:
                    return

        # Don't print changelog - it's shown in startup sequence now
        with open(CHANGELOG_PATH, 'w') as f:
            f.write(today)
    except Exception:
        pass

def startup_greet():
    """
    Startup greeting - this is called SILENTLY by main.py
    All output is suppressed in main.py's silent_background_init()
    Only speak() calls will be heard
    """
    # Speak the greeting (audio only, no visual output)
    speak("Boot sequence complete.")
    
    # Short pause
    time.sleep(0.3)
    
    # Speak version info
    speak("Lily version 2 is fully online and ready.")
    
    # Short pause
    time.sleep(0.3)
    
    # Time-based greeting
    greeting = get_time_based_greeting()
    speak(f"{greeting} Aman.")
    
    # Short pause
    time.sleep(0.3)
    
    # Time since last run
    last_run = get_last_run_info()
    if last_run:
        time_msg = get_time_difference_message(last_run)
        if time_msg:
            speak(time_msg)
    
    # Show changelog (silent)
    show_changelog_once()
    
    # Log this startup
    log_current_start()