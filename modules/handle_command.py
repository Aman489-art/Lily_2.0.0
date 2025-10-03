from modules.system_tasks import *
from modules.tts_output import speak 
# Import the functions from your reminder system
from modules.reminder_tasks import (
    set_timer, view_timers, delete_timer, save_timer,
    set_alarm, view_alarms, delete_alarm, save_alarm,
    set_reminder, view_reminders, delete_reminder, save_reminder,
    set_calendar_event, list_calendar_events, list_all_calendar_events, delete_calendar_event
)
from modules.task_manager import *
from modules.error_logger import log_error
from modules.location import *
from modules.weather import *
from modules.phone_control import *
from modules.voice_input import listen_for_command
from modules.file_summarizer import *
import re
from rapidfuzz import process
from datetime import datetime, timedelta
import dateparser
import requests 
import json

def handle_command(query):
    """
    Matches and executes exact user commands. 
    Returns True if a command was executed.
    """
    query = query.strip().lower()

    try:



        if not query:
            return True  # Empty, nothing to process

    # 🎵 MUSIC COMMANDS

        if "play music" in query or "search song" in query:
            handle_music_command()
            return True

    #============== TIMER ==============
        elif "set a timer" in query:
            duration_str = query.replace("set a timer for", "")
            set_timer(duration_str)
            save_timer(duration_str)
            return True

        elif "show my timers" in query or "list timers" in query:
            view_timers()
            return True

        elif "delete timer" in query:
            # Example: "delete timer 2"
            match = re.search(r"delete timer (\d+)", query)
            if match:
                index = int(match.group(1))
                delete_timer(index)
            else:
                speak("Please specify which timer to delete.")
            return True

    #============== ALARM ===============
        elif "set an alarm" in query:
            time_str = query.replace("set an alarm for","")
            set_alarm(time_str)
            save_alarm(time_str)
            return True

        elif "view alarm" in query or "list alarms" in query:
            view_alarms()
            return True

        elif "delete alarm" in query:
            # Example: "delete alarm 1"
            match = re.search(r"delete alarm (\d+)", query)
            if match:
                index = int(match.group(1))
                delete_alarm(index)
            else:
                speak("Please specify which alarm to delete.")
            return True

    #============== REMINDER ==============

        elif "remind me" in query:
            reminder_str = query
            set_reminder(reminder_str)
            # Save reminder
            at_match = re.match(r"remind me to (.+) at (.+)", query)
            after_match = re.match(r"remind me to (.+) after (.+)", query)
            if at_match:
                task = at_match.group(1).strip()
                time_str = at_match.group(2).strip()
                save_reminder(task, time_str)
            elif after_match:
                task = after_match.group(1).strip()
                duration_str = after_match.group(2).strip()
                future_time = dateparser.parse(f"in {duration_str}")
                if future_time:
                    save_reminder(task, future_time.strftime("%Y-%m-%d %H:%M:%S"))
            return True

        elif "show my reminders" in query or "list reminders" in query:
            view_reminders()
            return True

        elif "delete reminder" in query:
            # Example: "delete reminder 3"
            match = re.search(r"delete reminder (\d+)", query)
            if match:
                index = int(match.group(1))
                delete_reminder(index)
            else:
                speak("Please specify which reminder to delete.")
            return True

    #=============== CALENDAR =============

        elif "set an appointment" in query or "set an event" in query or "save this date" in query or "add calendar" in query:
            set_calendar_event(query)
            return True

        elif "show my events" in query or "list calendar" in query or "what's on my calendar" in query:
            list_calendar_events(query)
            return True 

        elif "show all calendar events" in query or "list all calendar events" in query:
            list_all_calendar_events()
            return True

        elif "delete calendar event" in query:
            # Example: "delete calendar event 2"
            match = re.search(r"delete calendar event (\d+)", query)
            if match:
                index = int(match.group(1))
                delete_calendar_event(index)
            else:
                speak("Please specify which calendar event to delete.")
            return True


    #LOCATION

        elif "my location" in query:
            get_location_summary()

    #WEATHER 

        elif "weather" in query:
            get_weather_report()

    #CALL

        elif "call" in query:
            result = call_contact_interactive(query)
            speak(result)
            return True

        elif "search" in query:
            name = query.replace('search', '').strip()
            contact = search_contact_by_name(name)

            if contact:
                numbers = contact.get("number") or contact.get("numbers") or []
                if isinstance(numbers, str):
                    numbers = [numbers]

                result = f"Found {contact.get('name', 'Unknown')}: " + ", ".join(numbers)
            else:
                result = f"Couldn't find any contact named {name}."

            speak(result)
            return True

    #PDF_SUMMARISER

        elif "summarise this file" in query:
            summarize_selected_file()
            return True

    #WIKIPEDIA

        elif "wikipedia" in query:
            query = query.replace("wikipedia", '')
            wiki_search(query)
            return True

    #NEWS

        elif "news" in query:
            news()
            return True

    #notification
        elif "notifications" in query or "show my notifications" in query:
            from modules.notifications import get_phone_notifications
            notifs = get_phone_notifications()
            speak(notifs)
            return True

    #task manager 

    # ============ TASK MANAGER / TO-DO ============

        elif "add task" in query or "new task" in query:
            # Example: "add task buy groceries for tomorrow"
            match = re.search(r"add task (.+?) for (.+)", query)
            if match:
                description = match.group(1).strip()
                date_str = match.group(2).strip()
            else:
                description = query.replace("add task", "").strip()
                date_str = None
            add_task(description, date_str)
            return True

        elif "show my tasks" in query or "view task" in query:
            view_tasks()
            return True

        elif "delete task" in query:
            # Example: "delete task 2"
            match = re.search(r"delete task (\d+)", query)
            if match:
                index = int(match.group(1)) - 1
                delete_task(index)
            else:
                speak("Please specify the task number to delete.")
            return True

    except Exception as e:
        log_error(e, context="Handle Command", extra=f"Query: {query}")
        speak("Something went wrong while processing your request.")


# Mapping of common commands to their core phrases
available_commands = {
    "play music": ["play music", "search song", "play songs"],
    "set timer": ["set a timer", "start timer"],
    "show timers": ["show my timers", "list timers"],
    "delete timer": ["delete timer"],
    "set alarm": ["set an alarm"],
    "view alarms": ["view alarm", "list alarms"],
    "delete alarm": ["delete alarm"],
    "set reminder": ["remind me", "set a reminder"],
    "show reminders": ["show my reminders", "list reminders"],
    "delete reminder": ["delete reminder"],
    "set calendar": ["set an appointment", "set an event", "save this date", "add calendar"],
    "show calendar": ["show my events", "list calendar", "what's on my calendar"],
    "show all calendar": ["show all calendar events", "list all calendar events"],
    "delete calendar": ["delete calendar event"],
    "location": ["my location"],
    "weather": ["weather"],
    "call": ["call"],
    "search contact": ["search"],
    "summarize file": ["summarise this file"],
    "wikipedia": ["wikipedia"],
    "news": ["news"],
    "notifications": ["notifications", "show my notifications"],
    "add task": ["add task", "new task"],
    "view tasks": ["show my tasks", "view task"],
    "delete task": ["delete task"]
}


def get_all_phrases():
    """Flatten command aliases into a searchable list"""
    all_phrases = []
    for aliases in available_commands.values():
        all_phrases.extend(aliases)
    return all_phrases


def fuzzy_handle_command(query, confidence_threshold=80):
    """
    If no command matches directly, use fuzzy matching to suggest or run.
    Returns True if a close match was found and passed to `handle_command()`.
    """
    if not query:
        return False

    all_phrases = get_all_phrases()
    best_match, score, _ = process.extractOne(query.lower(), all_phrases)

    if score >= confidence_threshold:
        speak(f"Did you mean: {best_match}?")
        return handle_command(best_match)

    return False
