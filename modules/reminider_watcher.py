import time
from datetime import datetime
from modules.tts_output import speak
from modules.reminder_tasks import (
    load_reminders, load_alarms, load_events, clean_expired_reminders,
    clean_expired_alarms, clean_expired_timers
)
from modules.task_manager import load_tasks
import json
import os

# Set to avoid duplicate notifications
reminder_shown = set()
task_shown = set()
alarm_shown = set()
timer_shown = set()
event_shown = set()
def safe_parse_datetime(dt_str):
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%I:%M %p",
        "%H:%M",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(dt_str.strip(), fmt)
        except ValueError:
            continue
    return None

def format_time(dt):
    return dt.strftime("%Y-%m-%d %H:%M")

def check_reminders_loop():
    while True:
        try:
            now = datetime.now()
            current_time_str = format_time(now)

            # ✅ Check Reminders
            reminders = load_reminders()
            for r in reminders:
                r_time = r.get("time")
                task = r.get("task")
                if r_time and format_time(safe_parse_datetime(r_time)) == current_time_str:
                    uid = f"{task}_{r_time}"
                    if uid not in reminder_shown:
                        speak(f"⏰ Reminder: {task}")
                        reminder_shown.add(uid)

            # ✅ Check Tasks
            tasks = load_tasks()
            for t in tasks:
                t_due = t.get("due") or t.get("date")  # support both "due" and "date"
                t_desc = t.get("description")
                if t_due:
                    try:
                        due_dt = safe_parse_datetime(t_due)
                    except ValueError:
                        due_dt = safe_parse_datetime(t_due)
                    if format_time(due_dt) == current_time_str:
                        uid = f"{t_desc}_{t_due}"
                        if uid not in task_shown:
                            speak(f"📝 Task Due: {t_desc}")
                            task_shown.add(uid)


            # ✅ Check Alarms
            alarms = load_alarms()
            for a in alarms:
                a_time = a.get("time")
                if a_time and format_time(safe_parse_datetime(a_time)) == current_time_str:
                    uid = f"alarm_{a_time}"
                    if uid not in alarm_shown:
                        speak(f"🔔 Alarm ringing for {a_time}")
                        alarm_shown.add(uid)

            # ✅ Check Timers
            timers_file = "data/timers.json"
            if os.path.exists(timers_file):
                with open(timers_file, "r") as f:
                    timers = json.load(f)
                for timer in timers:
                    end_time = timer.get("end_time")
                    if end_time and format_time(safe_parse_datetime(end_time)) == current_time_str:
                        uid = f"timer_{end_time}"
                        if uid not in timer_shown:
                            speak(f"⏳ Timer done for {timer['duration']}")
                            timer_shown.add(uid)

            # ✅ Check Calendar Events
            events = load_events()
            for e in events:
                e_time = e.get("time")
                e_desc = e.get("description")
                if e_time and format_time(safe_parse_datetime(e_time)) == current_time_str:
                    uid = f"{e_desc}_{e_time}"
                    if uid not in event_shown:
                        speak(f"📅 Upcoming event: {e_desc}")
                        event_shown.add(uid)

            # Clean expired
            clean_expired_reminders()
            clean_expired_alarms()
            clean_expired_timers()

            time.sleep(30)  # Loop every 30 seconds

        except Exception as e:
            from modules.error_logger import log_error
            log_error(e, context="Reminder Watcher")
            time.sleep(60)
