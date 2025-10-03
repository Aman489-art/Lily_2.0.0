import threading
import time
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
from modules.tts_output import speak
from modules.voice_input import listen_for_command
import dateparser

TIMERS_FILE = "data/timers.json"
ALARMS_FILE = "data/alarms.json"
REMINDERS_FILE = "data/reminders.json"
EVENTS_FILE = "data/calendar_events.json"

# Global lock for thread safety
data_lock = threading.Lock()

def parse_duration(duration_str):
    total_seconds = 0
    matches = re.findall(r'(\d+)\s*(hour|hours|minute|minutes|second|seconds)', duration_str)
    for value, unit in matches:
        value = int(value)
        if 'hour' in unit:
            total_seconds += value * 3600
        elif 'minute' in unit:
            total_seconds += value * 60
        elif 'second' in unit:
            total_seconds += value
    return timedelta(seconds=total_seconds)

def play_sound():
    # Try different Linux-compatible sound commands
    if os.system("command -v paplay >/dev/null") == 0:
        os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga")
    elif os.system("command -v aplay >/dev/null") == 0:
        os.system("aplay /usr/share/sounds/alsa/Front_Center.wav")
    elif os.system("command -v play >/dev/null") == 0:
        os.system("play -nq -t alsa synth 1 sine 1000")
    else:
        speak("⏰ Time's up! (no sound command found)")

def set_timer(duration_str):

    # Match multiple time units in one string
    matches = re.findall(r'(\d+)\s*(hour|hours|minute|minutes|second|seconds)', duration_str)

    if not matches:
        print("❌ Invalid format. Try something like: '2 hours 10 minutes 30 seconds'")
        return

    total_seconds = 0
    for value, unit in matches:
        value = int(value)
        if 'hour' in unit:
            total_seconds += value * 3600
        elif 'minute' in unit:
            total_seconds += value * 60
        elif 'second' in unit:
            total_seconds += value

    if total_seconds == 0:
        print("❌ Timer duration must be greater than 0.")
        return

    speak(f"⏳ Timer set for {duration_str} ({total_seconds} seconds)...")

    def countdown():
        time.sleep(total_seconds)
        speak("\n⏰ Time's up!")
        play_sound()
        clean_expired_timers()

    threading.Thread(target=countdown).start()

def set_alarm(time_str):
    # Use dateparser to convert natural language to datetime
    alarm_time = dateparser.parse(time_str, settings={'PREFER_DATES_FROM': 'future'})

    if not alarm_time:
        speak("❌ Couldn't understand the time. Try '6 PM', 'tomorrow at 8:30', etc.")
        return

    now = datetime.now()
    seconds_until_alarm = (alarm_time - now).total_seconds()

    if seconds_until_alarm <= 0:
        speak(f"⏰ That time ({alarm_time.strftime('%Y-%m-%d %H:%M:%S')}) is already in the past.")
        return

    speak(f"🔔 Alarm set for {alarm_time.strftime('%Y-%m-%d %I:%M %p')} ({int(seconds_until_alarm)} seconds from now)")

    def wait_and_alert():
        time.sleep(seconds_until_alarm)
        speak("\n⏰ Alarm! It's now", alarm_time.strftime('%I:%M %p'))
        play_sound()
        clean_expired_alarms()

    threading.Thread(target=wait_and_alert).start()

def set_reminder(reminder_str):

    # Pattern: remind me to <task> at <time>
    at_match = re.match(r"remind me to (.+) at (.+)", reminder_str)
    # Pattern: remind me to <task> after <duration>
    after_match = re.match(r"remind me to (.+) after (.+)", reminder_str)

    if at_match:
        task = at_match.group(1).strip()
        time_str = at_match.group(2).strip()

        alarm_time = dateparser.parse(time_str, settings={'PREFER_DATES_FROM': 'future'})
        if not alarm_time:
            print("❌ Couldn't parse the time.")
            return

        now = datetime.now()
        seconds_until = (alarm_time - now).total_seconds()

    elif after_match:
        task = after_match.group(1).strip()
        duration_str = after_match.group(2).strip()

        # Use dateparser to parse duration as future datetime
        future_time = dateparser.parse(f"in {duration_str}")
        if not future_time:
            print("❌ Couldn't parse the duration.")
            return

        now = datetime.now()
        seconds_until = (future_time - now).total_seconds()
    else:
        speak("❌ Invalid format. Try:\n- 'Remind me to drink water at 5:30 PM'\n- 'Remind me to drink water after 15 minutes'")
        return

    if seconds_until <= 0:
        speak("❌ Reminder time is in the past.")
        return

    speak(f"✅ Reminder set: '{task}' in {int(seconds_until)} seconds")

    def remind():
        time.sleep(seconds_until)
        speak(f"\n🔔 Reminder: {task}")
        play_sound()
        clean_expired_reminders()

    threading.Thread(target=remind).start()

"=============== LOGICS FOR CALENDAR EVENTS ============"

def load_events():
    if not os.path.exists(EVENTS_FILE):
        return []
    with open(EVENTS_FILE, "r") as f:
        return json.load(f)

def save_events(events):
    with open(EVENTS_FILE, "w") as f:
        json.dump(events, f, indent=2)

def set_calendar_event(command_str):
    command_str = command_str.lower().strip()

    # Try to extract description and time naturally
    # Expected formats:
    # - set an appointment with doctor at 5:30 p.m. on 26 september
    # - save this date mom's birthday on 4 october

    time_keywords = [' at ', ' on ', ' by ', ' for ']
    time_part = ''
    description = command_str

    # Try to split command based on time indicators
    for keyword in time_keywords:
        if keyword in command_str:
            parts = command_str.split(keyword, 1)
            description = parts[0].replace("set", "").replace("add", "").replace("save", "").replace("this date", "").strip(": ").strip()
            time_part = parts[1].strip()
            break

    if not time_part:
        print("❌ Couldn't extract time part from your command.")
        return

    # Parse the event time using dateparser
    event_time = dateparser.parse(time_part, settings={'PREFER_DATES_FROM': 'future'})

    if not event_time:
        print("❌ Could not parse the event time.")
        return

    # Save the event
    events = load_events()
    events.append({
        "description": description,
        "time": event_time.strftime("%Y-%m-%d %H:%M:%S")
    })
    save_events(events)

    #print(f"✅ Event saved: '{description}' at {event_time.strftime('%Y-%m-%d %I:%M %p')}")
    speak(f"Event saved for {description} on {event_time.strftime('%A, %d %B at %I:%M %p')}")

def list_calendar_events(query=None):
    if not isinstance(query, str) or not query.strip():
        speak("Which date should I check? You can say things like 'today', 'tomorrow', or '12 September'.")
        query = listen_for_command()

    original_query = query
    query = query.lower().strip()

    # Try to extract only the date part
    for keyword in ['for', 'on', 'at']:
        if keyword in query:
            query = query.split(keyword, 1)[1].strip()
            break

    date_obj = dateparser.parse(query, settings={'PREFER_DATES_FROM': 'future'})
    if not date_obj:
        speak("Sorry, I couldn't understand the date you meant.")
        print(f"DEBUG: Failed to parse from query: '{original_query}' → extracted: '{query}'")
        return

    target_date = date_obj.date()

    events = load_events()
    found = False

    for i, event in enumerate(events, start=1):
        event_time = datetime.strptime(event['time'], "%Y-%m-%d %H:%M:%S")
        if event_time.date() == target_date:
            if not found:
                speak(f"Here are your events on {target_date.strftime('%A, %d %B')}:")
                found = True
            speak(f" {i} - {event['description']} at {event_time.strftime('%I:%M %p')}")

    if not found:
        speak(f"You have no events on {target_date.strftime('%A, %d %B')}.")

def delete_calendar_event(index):
    events = load_events()

    if not events:
        speak("📅 There are no calendar events to delete.")
        return

    if 0 <= index - 1 < len(events):
        removed = events.pop(index - 1)
        save_events(events)
        speak(f"🗑️ Calendar event '{removed['description']}' on {removed['time']} deleted.")
    else:
        speak("❌ Invalid event number.")

def list_all_calendar_events():
    events = load_events()
    if not events:
        speak("📅 No calendar events found.")
        return

    speak("Here are all upcoming calendar events:")
    for i, event in enumerate(events, start=1):
        event_time = datetime.strptime(event['time'], "%Y-%m-%d %H:%M:%S")
        speak(f"{i}. {event['description']} on {event_time.strftime('%A, %d %B at %I:%M %p')}")



"================ LOGICS FOR TIMER ====================="

def clean_expired_timers():
    if not os.path.exists(TIMERS_FILE):
        return

    with open(TIMERS_FILE, "r") as f:
        timers = json.load(f)

    now = datetime.now()
    updated = [t for t in timers if datetime.strptime(t["end_time"], "%Y-%m-%d %H:%M:%S") > now]

    if len(updated) != len(timers):
        with open(TIMERS_FILE, "w") as f:
            json.dump(updated, f, indent=2)

def save_timer(duration_str):
    if not os.path.exists(TIMERS_FILE):
        timers = []
    else:
        with open(TIMERS_FILE, "r") as f:
            timers = json.load(f)

    end_time = (datetime.now() + parse_duration(duration_str)).strftime("%Y-%m-%d %H:%M:%S")

    timers.append({"duration": duration_str, "end_time": end_time})
    with open(TIMERS_FILE, "w") as f:
        json.dump(timers, f, indent=2)
    speak("✅ Timer saved.")

def view_timers():
    if not os.path.exists(TIMERS_FILE):
        speak("⏳ No saved timers found.")
        return

    with open(TIMERS_FILE, "r") as f:
        timers = json.load(f)

    if not timers:
        speak("⏳ No saved timers.")
        return

    speak("Here are your saved timers:")
    for i, timer in enumerate(timers, start=1):
        speak(f"{i}. {timer['duration']}")

def delete_timer(index):
    if not os.path.exists(TIMERS_FILE):
        speak("⏳ No timers to delete.")
        return

    with open(TIMERS_FILE, "r") as f:
        timers = json.load(f)

    if 0 <= index - 1 < len(timers):
        removed = timers.pop(index - 1)
        with open(TIMERS_FILE, "w") as f:
            json.dump(timers, f, indent=2)
        speak(f"🗑️ Timer '{removed['duration']}' deleted.")
    else:
        speak("❌ Invalid timer number.")

"================ LOGICS FOR ALARM ====================="
def load_alarms():
    if not os.path.exists(ALARMS_FILE):
        return []
    with open(ALARMS_FILE, "r") as f:
        return json.load(f)

def clean_expired_alarms():
    if not os.path.exists(ALARMS_FILE):
        return

    with open(ALARMS_FILE, "r") as f:
        alarms = json.load(f)

    now = datetime.now()
    updated = [a for a in alarms if dateparser.parse(a["time"]) > now]

    if len(updated) != len(alarms):
        with open(ALARMS_FILE, "w") as f:
            json.dump(updated, f, indent=2)

def save_alarm(time_str):
    if not os.path.exists(ALARMS_FILE):
        alarms = []
    else:
        with open(ALARMS_FILE, "r") as f:
            alarms = json.load(f)

    alarms.append({"time": time_str})
    with open(ALARMS_FILE, "w") as f:
        json.dump(alarms, f, indent=2)
    speak("✅ Alarm saved.")

def view_alarms():
    if not os.path.exists(ALARMS_FILE):
        speak("🔔 No saved alarms found.")
        return

    with open(ALARMS_FILE, "r") as f:
        alarms = json.load(f)

    if not alarms:
        speak("🔔 No saved alarms.")
        return

    speak("Here are your saved alarms:")
    for i, alarm in enumerate(alarms, start=1):
        speak(f"{i}. {alarm['time']}")

def delete_alarm(index):
    if not os.path.exists(ALARMS_FILE):
        speak("🔔 No alarms to delete.")
        return

    with open(ALARMS_FILE, "r") as f:
        alarms = json.load(f)

    if 0 <= index - 1 < len(alarms):
        removed = alarms.pop(index - 1)
        with open(ALARMS_FILE, "w") as f:
            json.dump(alarms, f, indent=2)
        speak(f"🗑️ Alarm '{removed['time']}' deleted.")
    else:
        speak("❌ Invalid alarm number.")

"================ LOGICS FOR REMINDER ====================="

def load_reminders():
    if not os.path.exists(REMINDERS_FILE):
        return []
    with open(REMINDERS_FILE, "r") as f:
        return json.load(f)

def clean_expired_reminders():
    if not os.path.exists(REMINDERS_FILE):
        return

    with open(REMINDERS_FILE, "r") as f:
        reminders = json.load(f)

    now = datetime.now()
    updated = [r for r in reminders if dateparser.parse(r["time"]) > now]

    if len(updated) != len(reminders):
        with open(REMINDERS_FILE, "w") as f:
            json.dump(updated, f, indent=2)

def save_reminder(task, time_str):
    if not os.path.exists(REMINDERS_FILE):
        reminders = []
    else:
        with open(REMINDERS_FILE, "r") as f:
            reminders = json.load(f)

    reminders.append({"task": task, "time": time_str})
    with open(REMINDERS_FILE, "w") as f:
        json.dump(reminders, f, indent=2)
    speak("✅ Reminder saved.")

def view_reminders():
    if not os.path.exists(REMINDERS_FILE):
        speak("🔔 No saved reminders found.")
        return

    with open(REMINDERS_FILE, "r") as f:
        reminders = json.load(f)

    if not reminders:
        speak("🔔 No saved reminders.")
        return

    speak("Here are your saved reminders:")
    for i, rem in enumerate(reminders, start=1):
        speak(f"{i}. {rem['task']} at {rem['time']}")

def delete_reminder(index):
    if not os.path.exists(REMINDERS_FILE):
        speak("🔔 No reminders to delete.")
        return

    with open(REMINDERS_FILE, "r") as f:
        reminders = json.load(f)

    if 0 <= index - 1 < len(reminders):
        removed = reminders.pop(index - 1)
        with open(REMINDERS_FILE, "w") as f:
            json.dump(reminders, f, indent=2)
        speak(f"🗑️ Reminder '{removed['task']}' deleted.")
    else:
        speak("❌ Invalid reminder number.")


